"""Create + issue a cuenta de cobro linked to an income (panel modal flow).

Every modal-created cuenta requires an income (expected or liquid) and a
platform client. The customer snapshot defaults come from the client's
profile — NIT preferred over cédula — overlaid with the form's editable
overrides; the per-client PA-{CODE}-{NNN} series numbers the document.
"""
from decimal import Decimal

from django.db import transaction

from accounts.models import UserProfile
from content.models import (
    Document,
    DocumentCollectionAccount,
    DocumentItem,
    IncomeRecord,
)
from content.services.collection_account_numbering import allocate_client_number
from content.services.collection_account_service import (
    CollectionAccountError,
    get_default_issuer,
    issue_collection_account,
    seed_default_payment_methods,
)
from content.services.document_type_utils import (
    get_collection_account_document_type,
)

PAYMENT_TERM_DAYS = 8


def customer_snapshot_defaults(profile):
    """Editable snapshot prefill from the client profile (NIT over cédula)."""
    user = profile.user
    full_name = f'{user.first_name} {user.last_name}'.strip()
    if profile.nit:
        identification, identification_type = profile.nit, 'NIT'
    elif profile.cedula:
        identification, identification_type = profile.cedula, 'CC'
    else:
        identification, identification_type = '', ''
    return {
        'name': profile.company_name or full_name or (user.email or ''),
        'email': user.email or '',
        'identification': identification,
        'identification_type': identification_type,
        'contact_name': full_name,
        'address': '',
    }


def _resolve_customer(profile, overrides):
    customer = customer_snapshot_defaults(profile)
    for key, value in (overrides or {}).items():
        if value is not None:
            customer[key] = value
    email = (customer.get('email') or '').strip()
    if not email or email.endswith(UserProfile.PLACEHOLDER_EMAIL_DOMAIN):
        raise CollectionAccountError(
            'El cliente no tiene un email real configurado. Actualízalo en '
            'el módulo de clientes o escríbelo en el formulario.',
        )
    customer['email'] = email
    return customer


@transaction.atomic
def create_income_collection_account(data, *, acting_user=None):
    """Draft + issue in one transaction. Returns the issued Document."""
    issuer = get_default_issuer()

    profile = (
        UserProfile.objects.select_related('user')
        .filter(pk=data['client_profile_id'])
        .first()
    )
    if profile is None:
        raise CollectionAccountError('El cliente seleccionado no existe.')
    client = profile.user

    # Row lock: serializes concurrent creates over the same income, making
    # the one-non-cancelled-cuenta guard race-safe (MySQL cannot express it
    # as a conditional unique constraint).
    income = (
        IncomeRecord.objects.select_for_update()
        .filter(pk=data['income_record_id'])
        .first()
    )
    if income is None:
        raise CollectionAccountError('El ingreso seleccionado no existe.')
    if income.kind == IncomeRecord.Kind.LOST:
        raise CollectionAccountError(
            'No se puede generar una cuenta de cobro sobre un ingreso perdido.',
        )
    if income.collection_documents.exclude(
        commercial_status=Document.CommercialStatus.CANCELLED,
    ).exists():
        raise CollectionAccountError(
            'Este ingreso ya tiene una cuenta de cobro. Anúlala para '
            'generar otra.',
        )

    customer = _resolve_customer(profile, data.get('customer'))
    billing_concept = (
        (data.get('billing_concept') or '').strip() or income.concept
    )

    document = Document.objects.create(
        title=f'Cuenta de cobro — {billing_concept}',
        document_type=get_collection_account_document_type(),
        commercial_status=Document.CommercialStatus.DRAFT,
        client_user=client,
        income_record=income,
        client_name=customer['name'],
        currency=(data.get('currency') or 'COP').upper(),
        city=data.get('city') or '',
        notes=data.get('notes') or '',
        created_by=acting_user,
        updated_by=acting_user,
    )
    due_date = data.get('due_date')
    if due_date:
        term_type = DocumentCollectionAccount.PaymentTermType.FIXED_DATE
        term_days = None
        document.due_date = due_date
        document.save(update_fields=['due_date'])
    else:
        term_type = DocumentCollectionAccount.PaymentTermType.DAYS_AFTER_ISSUE
        term_days = data.get('payment_term_days') or PAYMENT_TERM_DAYS
    DocumentCollectionAccount.objects.create(
        document=document,
        billing_concept=billing_concept,
        payment_term_type=term_type,
        payment_term_days=term_days,
        observations=data.get('observations') or '',
    )
    for position, item in enumerate(data['items'], start=1):
        quantity = item.get('quantity') or Decimal('1')
        unit_price = item['unit_price']
        DocumentItem.objects.create(
            document=document,
            position=position,
            item_type=DocumentItem.ItemType.SERVICE,
            description=(item.get('description') or '').strip() or billing_concept,
            quantity=quantity,
            unit_price=unit_price,
            line_total=quantity * unit_price,
            period_start=item.get('period_start'),
            period_end=item.get('period_end'),
            reference_type='income_record',
            reference_id=income.pk,
        )
    seed_default_payment_methods(document, issuer)

    manual_number = (data.get('public_number') or '').strip() or None
    issue_collection_account(
        document,
        issuer=issuer,
        acting_user=acting_user,
        customer=customer,
        number_allocator=lambda: allocate_client_number(
            profile, issuer, manual_number=manual_number,
        ),
    )
    # Re-read: creating the extension above primed the reverse one-to-one
    # cache on `document` with the pre-issue row (empty customer snapshot);
    # issue_collection_account saved a different instance.
    return (
        Document.objects.select_related('collection_account')
        .prefetch_related('items', 'payment_methods')
        .get(pk=document.pk)
    )
