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

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import F
from django.template.loader import render_to_string
from django.utils import timezone

from content.models import (
    Document,
    DocumentCollectionAccount,
    DocumentItem,
    DocumentPaymentMethod,
    EmailLog,
    HostingRecord,
    IssuerProfile,
)
from content.services.collection_account_pdf_service import (
    CollectionAccountPdfService,
)
from content.services.collection_account_service import (
    CollectionAccountError,
    issue_collection_account,
)
from content.services.document_type_utils import (
    get_collection_account_document_type,
)
from content.utils import add_months, format_cop_email, today_bogota

logger = logging.getLogger(__name__)

TEMPLATE_KEY = 'collection_account_sent'
PAYMENT_TERM_DAYS = 8


class HostingBillingError(Exception):
    """Invalid state or input for the hosting cuenta de cobro flow."""


def next_billing_period(hosting):
    """(from, to) of the period being billed: valid_to plus one modality."""
    months = HostingRecord.MODALITY_MONTHS.get(hosting.payment_modality, 1)
    period_from = hosting.valid_to or today_bogota()
    return period_from, add_months(period_from, months)


def _default_issuer():
    issuer = IssuerProfile.objects.order_by('pk').first()
    if issuer is None:
        raise HostingBillingError(
            'No hay un perfil emisor (IssuerProfile) configurado.',
        )
    return issuer


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
    issuer = _default_issuer()
    for position, method in enumerate(issuer.default_payment_methods or []):
        DocumentPaymentMethod.objects.create(
            document=document,
            payment_method_type=method.get('payment_method_type', 'bank_transfer'),
            bank_name=method.get('bank_name', ''),
            account_type=method.get('account_type', ''),
            account_number=method.get('account_number', ''),
            account_holder_name=method.get('account_holder_name', ''),
            account_holder_identification=method.get(
                'account_holder_identification', '',
            ),
            payment_instructions=method.get('payment_instructions', ''),
            is_primary=position == 0,
        )
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
            'usa "Reenviar" en el tab Cobros.',
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
    """Branded client email with the PDF attached. Returns True on success."""
    from content.services.proposal_email_service import _build_design_context

    extension = document.collection_account
    recipient = extension.customer_email
    if not recipient:
        logger.warning(
            'Collection account %s has no customer email; not sent.',
            document.pk,
        )
        return False
    total = format_cop_email(document.total)
    due = f'{document.due_date:%d/%m/%Y}' if document.due_date else ''
    item = document.items.first()
    period = ''
    if item and item.period_start and item.period_end:
        period = f'{item.period_start:%d/%m/%Y} a {item.period_end:%d/%m/%Y}'

    sections = [
        (
            f'Te compartimos la cuenta de cobro {document.public_number} por '
            f'{extension.billing_concept or document.title}.'
        ),
    ]
    if period:
        sections.append(f'Período facturado: {period}.')
    sections.append(
        f'Valor a pagar: {total} COP'
        + (f' · Fecha límite de pago: {due}.' if due else '.')
    )
    methods = list(document.payment_methods.all())
    if methods:
        lines = []
        for method in methods:
            parts = [method.get_payment_method_type_display()]
            if method.bank_name:
                parts.append(method.bank_name)
            if method.account_number:
                parts.append(f'cuenta {method.account_number}')
            lines.append(' · '.join(parts))
        sections.append('Formas de pago:\n' + '\n'.join(f'— {line}' for line in lines))
    sections.append(
        'Adjuntamos el PDF con el detalle completo. Cualquier duda, '
        'responde este correo y con gusto te ayudamos.'
    )

    subject = f'Cuenta de cobro {document.public_number} — ProjectApp'
    greeting = f'Hola {extension.customer_contact_name or extension.customer_name}'
    context = {
        'subject': subject,
        'greeting': greeting,
        'sections': sections,
        'footer': '',
        'attachment_names': [f'{document.public_number}.pdf'],
    }
    context.update(_build_design_context())
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'team@projectapp.co')
    metadata = {
        'document_id': document.pk,
        'public_number': document.public_number,
        'hosting_id': hosting.pk if hosting else document.hosting_record_id,
        'resend': resend,
    }

    try:
        pdf_bytes = CollectionAccountPdfService.generate(document)
        html_body = render_to_string('emails/branded_email.html', context)
        text_body = render_to_string('emails/branded_email.txt', context)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[recipient],
        )
        email.attach_alternative(html_body, 'text/html')
        email.attach(f'{document.public_number}.pdf', pdf_bytes, 'application/pdf')
        email.send(fail_silently=False)
    except Exception as exc:
        logger.warning(
            'Failed to send collection account %s to %s: %s',
            document.pk, recipient, exc,
        )
        EmailLog.objects.create(
            template_key=TEMPLATE_KEY,
            recipient=recipient,
            subject=subject,
            status=EmailLog.Status.FAILED,
            error_message=str(exc),
            metadata=metadata,
        )
        return False

    EmailLog.objects.create(
        template_key=TEMPLATE_KEY,
        recipient=recipient,
        subject=subject,
        status=EmailLog.Status.SENT,
        metadata=metadata,
    )
    logger.info(
        'Sent collection account %s to %s', document.public_number, recipient,
    )
    return True
