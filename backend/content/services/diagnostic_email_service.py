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
        return cls._send(diagnostic, 'diagnostic_initial_sent', subject)

    @classmethod
    def send_final_to_client(cls, diagnostic: WebAppDiagnostic) -> bool:
        name = build_client_display_name(diagnostic.client)
        subject = f'📊 {name}, tu diagnóstico está listo — Project App'
        return cls._send(diagnostic, 'diagnostic_final_sent', subject)
