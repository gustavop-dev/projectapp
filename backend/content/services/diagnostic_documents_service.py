"""Service for sending diagnostic attachments by email.

Mirrors ``ProposalEmailService.send_documents_to_client`` without the
contract/commercial/technical PDF generation (diagnostics rely on the
existing `send-initial`/`send-final` transitions for the core docs).
Only ``DiagnosticAttachment`` rows are attached here.
"""

from __future__ import annotations

import logging
import mimetypes

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from accounts.services.proposal_client_service import build_client_display_name
from content.models import DiagnosticAttachment, WebAppDiagnostic
from content.services.diagnostic_email_service import DiagnosticEmailService
from content.services.proposal_email_service import (
    ProposalEmailService,
    _is_unsendable_client_email,
)

logger = logging.getLogger(__name__)

TEMPLATE_KEY = DiagnosticEmailService.TEMPLATE_DOCUMENTS


def send_attachments_to_client(
    diagnostic: WebAppDiagnostic,
    attachment_ids: list,
    subject: str = '',
    greeting: str = '',
    body: str = '',
    footer: str = '',
    document_descriptions: list | None = None,
) -> tuple[bool, str | None]:
    """Attach the requested DiagnosticAttachments to an email and send it.

    Returns ``(ok, error_message)``. ``error_message`` is None on success or
    a user-facing error string on failure.
    """
    recipient = (diagnostic.client.user.email or '').strip()
    if _is_unsendable_client_email(recipient):
        return False, 'No hay email del cliente configurado.'

    attachments_list = list(
        DiagnosticAttachment.objects.filter(
            diagnostic=diagnostic, pk__in=attachment_ids or [],
        )
    )
    files_payload = []
    for att in attachments_list:
        if not att.file:
            continue
        mime = mimetypes.guess_type(att.file.name)[0] or 'application/octet-stream'
        with att.file.open('rb') as fh:
            files_payload.append((
                att.file.name.rsplit('/', 1)[-1],
                fh.read(),
                mime,
            ))

    if not files_payload:
        return False, 'No se pudieron adjuntar los documentos seleccionados.'

    client_name = build_client_display_name(diagnostic.client)
    context = {
        'client_name': client_name,
        'title': diagnostic.title,
        'greeting': greeting or f'Hola {client_name}',
        'body': body or '',
        'footer': footer or '',
        'document_descriptions': document_descriptions or [],
    }
    email_subject = subject or (
        f'📎 {client_name}, te compartimos documentos '
        f'de tu diagnóstico — Project App'
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL',
                         'team@projectapp.co')

    log_metadata = {
        'diagnostic_uuid': str(diagnostic.uuid),
        'attached_doc_ids': [att.id for att in attachments_list],
    }

    try:
        html_body = render_to_string(
            'emails/proposal_documents_sent.html', context,
        )
        text_body = render_to_string(
            'emails/proposal_documents_sent.txt', context,
        )
        email = EmailMultiAlternatives(
            subject=email_subject,
            body=text_body,
            from_email=from_email,
            to=[recipient],
        )
        email.attach_alternative(html_body, 'text/html')
        for filename, data, mime_type in files_payload:
            email.attach(filename, data, mime_type)
        email.send(fail_silently=False)
    except Exception as exc:
        ProposalEmailService._log_email(
            TEMPLATE_KEY, recipient, subject=email_subject, status='failed',
            error_message=str(exc)[:1000], metadata=log_metadata,
        )
        logger.exception('Failed sending diagnostic documents for %s',
                         diagnostic.uuid)
        return False, 'Error al enviar el correo. Intenta de nuevo.'

    ProposalEmailService._log_email(
        TEMPLATE_KEY, recipient, subject=email_subject, status='sent',
        metadata=log_metadata,
    )
    logger.info('Sent %d attachments for diagnostic %s to %s',
                len(files_payload), diagnostic.uuid, recipient)
    return True, None
