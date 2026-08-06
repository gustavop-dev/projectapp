"""Client email for a cuenta de cobro, split in build vs send.

``build_collection_account_email`` renders subject + bodies with zero side
effects — the preview endpoint reuses it, so what the operator previews is
by construction what ``send_collection_account_email`` sends (same sections,
same branded shell, same PDF service on the send side).
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from content.models import EmailLog
from content.services.collection_account_pdf_service import (
    CollectionAccountPdfService,
)
from content.utils import format_cop_email

logger = logging.getLogger(__name__)

TEMPLATE_KEY = 'collection_account_sent'


def build_collection_account_email(document, *, resend=False):
    """Subject + rendered bodies for the client email. No side effects."""
    extension = document.collection_account
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
        f'Valor a pagar: ${total} COP'
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
        sections.append(
            'Formas de pago:\n' + '\n'.join(f'— {line}' for line in lines)
        )
    sections.append(
        'Adjuntamos el PDF con el detalle completo. Cualquier duda, '
        'responde este correo y con gusto te ayudamos.'
    )

    subject = f'Cuenta de cobro {document.public_number} — ProjectApp'
    greeting = (
        f'Hola {extension.customer_contact_name or extension.customer_name}'
    )
    attachment_name = f'{document.public_number}.pdf'
    context = {
        'subject': subject,
        'greeting': greeting,
        'sections': sections,
        'footer': '',
        'attachment_names': [attachment_name],
    }
    from content.services.proposal_email_service import _build_design_context

    context.update(_build_design_context())
    return {
        'subject': subject,
        'greeting': greeting,
        'sections': sections,
        'html_body': render_to_string('emails/branded_email.html', context),
        'text_body': render_to_string('emails/branded_email.txt', context),
        'attachment_name': attachment_name,
    }


def send_collection_account_email(document, *, hosting=None, resend=False):
    """Build + send the client email with the PDF attached. True on success."""
    extension = document.collection_account
    recipient = extension.customer_email
    if not recipient:
        logger.warning(
            'Collection account %s has no customer email; not sent.',
            document.pk,
        )
        return False

    email_parts = build_collection_account_email(document, resend=resend)
    subject = email_parts['subject']
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'team@projectapp.co')
    metadata = {
        'document_id': document.pk,
        'public_number': document.public_number,
        'hosting_id': hosting.pk if hosting else document.hosting_record_id,
        'income_record_id': document.income_record_id,
        'resend': resend,
    }

    try:
        pdf_bytes = CollectionAccountPdfService.generate(document)
        email = EmailMultiAlternatives(
            subject=subject,
            body=email_parts['text_body'],
            from_email=from_email,
            to=[recipient],
        )
        email.attach_alternative(email_parts['html_body'], 'text/html')
        email.attach(
            email_parts['attachment_name'], pdf_bytes, 'application/pdf',
        )
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
