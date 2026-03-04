import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


class ProposalEmailService:
    """
    Service for sending proposal-related emails to clients.
    Uses Django's EmailMultiAlternatives for HTML + text fallback.
    """

    FROM_EMAIL = None  # Resolved at runtime from settings

    @classmethod
    def _get_from_email(cls):
        """Return the configured sender email address."""
        return cls.FROM_EMAIL or getattr(
            settings, 'DEFAULT_FROM_EMAIL', 'team@projectapp.co'
        )

    @classmethod
    def send_reminder(cls, proposal):
        """
        Send a reminder email about a pending proposal.

        Renders HTML and plain-text templates with proposal context,
        sends via EmailMultiAlternatives, and records reminder_sent_at.

        Args:
            proposal: BusinessProposal instance with client_email set.

        Returns:
            bool: True if the email was sent successfully.
        """
        if not proposal.client_email:
            logger.warning(
                'Cannot send reminder for proposal %s: no client_email',
                proposal.uuid,
            )
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'days_remaining': proposal.days_remaining,
            'expires_at': proposal.expires_at,
            'total_investment': proposal.total_investment,
            'currency': proposal.currency,
            'title': proposal.title,
        }

        try:
            html_content = render_to_string(
                'emails/proposal_reminder.html', context
            )
            text_content = render_to_string(
                'emails/proposal_reminder.txt', context
            )

            subject = (
                f'📋 {proposal.client_name}, tu propuesta te espera — '
                f'Project App'
            )

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[proposal.client_email],
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            proposal.reminder_sent_at = timezone.now()
            proposal.save(update_fields=['reminder_sent_at'])

            logger.info(
                'Sent reminder email for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send reminder email for proposal %s',
                proposal.uuid,
            )
            return False
