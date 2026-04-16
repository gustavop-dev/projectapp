"""Email service for the WebAppDiagnostic feature.

Sends two emails:
- ``diagnostic_initial_sent`` — initial scope/severity/categories doc (no pricing).
- ``diagnostic_final_sent`` — full package with pricing + sizing annex.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from accounts.services.proposal_client_service import build_client_display_name
from content.models import WebAppDiagnostic
from content.services.proposal_email_service import (
    ProposalEmailService,
    _is_unsendable_client_email,
)

logger = logging.getLogger(__name__)


class DiagnosticEmailService:

    TEMPLATE_INITIAL = 'diagnostic_initial_sent'
    TEMPLATE_FINAL = 'diagnostic_final_sent'
    TEMPLATE_CUSTOM = 'diagnostic_custom_email'
    TEMPLATE_DOCUMENTS = 'diagnostic_documents_sent'

    @classmethod
    def _send(cls, diagnostic: WebAppDiagnostic, template_key: str,
              subject: str) -> bool:
        recipient = (diagnostic.client.user.email or '').strip()
        if _is_unsendable_client_email(recipient):
            logger.warning(
                'Cannot send %s: no usable client email for diagnostic %s',
                template_key, diagnostic.uuid,
            )
            return False

        context = {
            'client_name': build_client_display_name(diagnostic.client),
            'diagnostic_url': diagnostic.public_url,
            'title': diagnostic.title,
            'investment_amount': diagnostic.investment_amount,
            'currency': diagnostic.currency,
            'duration_label': diagnostic.duration_label,
        }
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'team@projectapp.co')

        try:
            html_body = render_to_string(f'emails/{template_key}.html', context)
            text_body = render_to_string(f'emails/{template_key}.txt', context)
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=from_email,
                to=[recipient],
            )
            email.attach_alternative(html_body, 'text/html')
            email.send(fail_silently=False)
            ProposalEmailService._log_email(
                template_key, recipient, subject=subject, status='sent',
                metadata={'diagnostic_uuid': str(diagnostic.uuid)},
            )
            logger.info('Sent %s to %s for diagnostic %s',
                        template_key, recipient, diagnostic.uuid)
            return True
        except Exception as exc:
            ProposalEmailService._log_email(
                template_key, recipient, subject=subject, status='failed',
                error_message=str(exc)[:1000],
                metadata={'diagnostic_uuid': str(diagnostic.uuid)},
            )
            logger.exception('Failed sending %s for diagnostic %s',
                             template_key, diagnostic.uuid)
            return False

    @classmethod
    def send_initial_to_client(cls, diagnostic: WebAppDiagnostic) -> bool:
        name = build_client_display_name(diagnostic.client)
        subject = f'📋 {name}, propuesta de diagnóstico técnico — Project App'
        return cls._send(diagnostic, cls.TEMPLATE_INITIAL, subject)

    @classmethod
    def send_final_to_client(cls, diagnostic: WebAppDiagnostic) -> bool:
        name = build_client_display_name(diagnostic.client)
        subject = f'📊 {name}, tu diagnóstico está listo — Project App'
        return cls._send(diagnostic, cls.TEMPLATE_FINAL, subject)

    # ── Custom composer (branded-style email) ────────────────────────

    @classmethod
    def get_defaults(cls, diagnostic: WebAppDiagnostic) -> dict:
        """Return suggested field values for the admin email composer."""
        name = build_client_display_name(diagnostic.client)
        return {
            'recipient_email': (diagnostic.client.user.email or '').strip(),
            'subject': f'{name}, seguimiento de tu diagnóstico — Project App',
            'greeting': f'Hola {name}',
            'sections': [''],
            'footer': 'Quedamos atentos a tus comentarios.',
        }

    @classmethod
    def send_custom_email(
        cls,
        diagnostic: WebAppDiagnostic,
        recipient_email: str,
        subject: str,
        greeting: str,
        sections: list,
        footer: str = '',
        attachments: list | None = None,
    ) -> bool:
        """Send a composer-driven follow-up email for a diagnostic.

        Reuses the shared branded-email template and records the send in
        ``EmailLog`` with ``metadata.diagnostic_uuid`` (no ``proposal`` FK).
        """
        attachment_names = [a[0] for a in attachments] if attachments else []
        log_metadata = {
            'diagnostic_uuid': str(diagnostic.uuid),
            'greeting': greeting,
            'sections': sections,
            'footer': footer,
            'attachment_names': attachment_names,
        }
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL',
                             'team@projectapp.co')

        try:
            context = {
                'subject': subject,
                'greeting': greeting,
                'sections': sections,
                'footer': footer,
                'attachment_names': attachment_names,
            }
            html_body = render_to_string('emails/branded_email.html', context)
            text_body = render_to_string('emails/branded_email.txt', context)
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=from_email,
                to=[recipient_email],
            )
            email.attach_alternative(html_body, 'text/html')
            for filename, data, mime_type in (attachments or []):
                email.attach(filename, data, mime_type)
            email.send(fail_silently=False)

            ProposalEmailService._log_email(
                cls.TEMPLATE_CUSTOM, recipient_email,
                subject=subject, status='sent',
                metadata=log_metadata,
            )
            logger.info(
                'Sent %s to %s for diagnostic %s',
                cls.TEMPLATE_CUSTOM, recipient_email, diagnostic.uuid,
            )
            return True
        except Exception as exc:
            ProposalEmailService._log_email(
                cls.TEMPLATE_CUSTOM, recipient_email,
                subject=subject, status='failed',
                error_message=str(exc)[:1000],
                metadata=log_metadata,
            )
            logger.exception(
                'Failed sending %s for diagnostic %s',
                cls.TEMPLATE_CUSTOM, diagnostic.uuid,
            )
            return False

    @classmethod
    def list_emails(cls, diagnostic: WebAppDiagnostic, page: int = 1,
                    page_size: int = 20) -> dict:
        """Return paginated email history filtered by diagnostic uuid."""
        from content.models import EmailLog

        logs = EmailLog.objects.filter(
            proposal__isnull=True,
            metadata__diagnostic_uuid=str(diagnostic.uuid),
        ).order_by('-sent_at')

        total = logs.count()
        page = max(1, int(page or 1))
        offset = (page - 1) * page_size
        results = [
            {
                'id': log.pk,
                'recipient': log.recipient,
                'subject': log.subject,
                'status': log.status,
                'template_key': log.template_key,
                'sent_at': log.sent_at.isoformat(),
                'metadata': log.metadata,
            }
            for log in logs[offset:offset + page_size]
        ]
        return {
            'results': results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'has_next': offset + page_size < total,
        }
