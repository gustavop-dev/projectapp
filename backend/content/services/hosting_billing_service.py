"""Cuenta de cobro (collection account) flow for accounting hostings.

The panel action "Enviar cuenta de cobro" on a HostingRecord:
1. Creates a draft Document + DocumentCollectionAccount for the next
   billing period (valid_to → valid_to + modality months).
2. Issues it (public number, payer/customer snapshots — the customer
   comes from the hosting's client fields, not a platform user).
3. Emails the client the branded message with the PDF attached.
4. Stamps `billing_requested_at` on the hosting, silencing the expiry
   notice cadence until the next renewal (hosting_expiry_service).

The document stays issued even when the email fails: the admin re-sends
it from the Cobros tab.
"""
import logging

from django.db.models import F
from django.utils import timezone

from content.models import (
    Document,
    DocumentCollectionAccount,
    DocumentItem,
    HostingRecord,
)
from content.services.collection_account_email_service import (
    TEMPLATE_KEY,
    send_collection_account_email,
)
from content.services.collection_account_service import (
    CollectionAccountError,
    get_default_issuer,
    issue_collection_account,
    seed_default_payment_methods,
)
from content.services.document_type_utils import (
    get_collection_account_document_type,
)
from content.utils import add_months, today_bogota

__all__ = [
    'HostingBillingError',
    'TEMPLATE_KEY',
    'create_hosting_collection_account',
    'next_billing_period',
    'resend_collection_account_email',
    'send_hosting_collection_account',
]

logger = logging.getLogger(__name__)

PAYMENT_TERM_DAYS = 8


class HostingBillingError(Exception):
    """Invalid state or input for the hosting cuenta de cobro flow."""


def next_billing_period(hosting):
    """(from, to) of the period being billed: valid_to plus one modality."""
    months = HostingRecord.MODALITY_MONTHS.get(hosting.payment_modality, 1)
    period_from = hosting.valid_to or today_bogota()
    return period_from, add_months(period_from, months)


def _default_issuer():
    try:
        return get_default_issuer()
    except CollectionAccountError as exc:
        raise HostingBillingError(str(exc)) from exc


def create_hosting_collection_account(hosting, *, acting_user=None):
    """Draft Document + extension + line item + default payment methods."""
    period_from, period_to = next_billing_period(hosting)
    label = hosting.domain_url or hosting.client_name
    document = Document.objects.create(
        title=f'Cuenta de cobro — hosting {label}',
        document_type=get_collection_account_document_type(),
        commercial_status=Document.CommercialStatus.DRAFT,
        hosting_record=hosting,
        currency='COP',
        created_by=acting_user,
        updated_by=acting_user,
    )
    DocumentCollectionAccount.objects.create(
        document=document,
        billing_concept=f'Servicio de hosting {label}',
        payment_term_type=DocumentCollectionAccount.PaymentTermType.DAYS_AFTER_ISSUE,
        payment_term_days=PAYMENT_TERM_DAYS,
    )
    DocumentItem.objects.create(
        document=document,
        position=1,
        item_type=DocumentItem.ItemType.HOSTING,
        description=(
            f'Servicio de hosting {label} — período '
            f'{period_from:%d/%m/%Y} a {period_to:%d/%m/%Y}'
        ),
        quantity=1,
        unit_price=hosting.payment_per_cycle,
        line_total=hosting.payment_per_cycle,
        period_start=period_from,
        period_end=period_to,
        reference_type='hosting_record',
        reference_id=hosting.pk,
    )
    seed_default_payment_methods(document, _default_issuer())
    return document


def send_hosting_collection_account(hosting, *, acting_user=None):
    """Create + issue + email the cuenta de cobro. Returns
    {'document': Document, 'email_sent': bool}."""
    if not hosting.client_email:
        raise HostingBillingError(
            'El hosting no tiene email de cliente configurado.',
        )
    if not hosting.payment_per_cycle or hosting.payment_per_cycle <= 0:
        raise HostingBillingError(
            'El hosting no tiene un pago por ciclo configurado.',
        )
    already_billed = (
        hosting.billing_requested_at is not None
        and hosting.collection_documents.exclude(
            commercial_status=Document.CommercialStatus.CANCELLED,
        ).exists()
    )
    if already_billed:
        raise HostingBillingError(
            'Ya se envió la cuenta de cobro de este período; '
            'usa "Reenviar" en el tab Cuentas de cobro.',
        )

    issuer = _default_issuer()
    document = create_hosting_collection_account(hosting, acting_user=acting_user)
    try:
        issue_collection_account(
            document,
            issuer=issuer,
            acting_user=acting_user,
            customer={
                'name': hosting.client_name,
                'email': hosting.client_email,
                'identification': hosting.client_identification,
                'contact_name': hosting.client_contact_name,
            },
        )
    except CollectionAccountError as exc:
        raise HostingBillingError(str(exc)) from exc

    # Re-read: the in-memory document may cache the pre-issue extension
    # (empty customer snapshot) via the reverse one-to-one descriptor.
    document = (
        Document.objects.select_related('collection_account')
        .prefetch_related('items', 'payment_methods')
        .get(pk=document.pk)
    )
    email_sent = _send_client_email(document, hosting=hosting)

    # Silence the expiry cadence for this period even if the email failed:
    # the document is issued and can be re-sent from Cobros.
    HostingRecord.objects.filter(pk=hosting.pk).update(
        billing_requested_at=timezone.now(),
        expiry_notice_target=F('valid_to'),
    )
    return {'document': document, 'email_sent': email_sent}


def resend_collection_account_email(document, *, acting_user=None):
    """Re-send the client email of an issued/paid collection account."""
    extension = getattr(document, 'collection_account', None)
    if extension is None or not extension.customer_email:
        raise HostingBillingError(
            'La cuenta de cobro no tiene un email de cliente.',
        )
    if document.commercial_status not in (
        Document.CommercialStatus.ISSUED,
        Document.CommercialStatus.PAID,
    ):
        raise HostingBillingError(
            'Solo se pueden reenviar cuentas de cobro emitidas.',
        )
    return _send_client_email(document, resend=True)


def _send_client_email(document, *, hosting=None, resend=False):
    """Delegation seam: existing tests patch this name to intercept sends."""
    return send_collection_account_email(
        document, hosting=hosting, resend=resend,
    )
