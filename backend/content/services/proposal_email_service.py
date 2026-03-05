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

    @classmethod
    def send_urgency_email(cls, proposal):
        """
        Send an urgency email with discount offer 2 days before expiry.

        Only sends if proposal.discount_percent > 0.

        Args:
            proposal: BusinessProposal instance with client_email set.

        Returns:
            bool: True if the email was sent successfully.
        """
        if not proposal.client_email:
            return False

        if not proposal.discount_percent or proposal.discount_percent <= 0:
            return False

        from decimal import Decimal
        discount_factor = Decimal(100 - proposal.discount_percent) / Decimal(100)
        discounted = proposal.total_investment * discount_factor

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'days_remaining': proposal.days_remaining,
            'expires_at': proposal.expires_at,
            'total_investment': proposal.total_investment,
            'discounted_investment': discounted,
            'discount_percent': proposal.discount_percent,
            'currency': proposal.currency,
            'title': proposal.title,
        }

        try:
            html_content = render_to_string(
                'emails/proposal_urgency.html', context
            )
            text_content = render_to_string(
                'emails/proposal_urgency.txt', context
            )

            subject = (
                f'🔥 {proposal.client_name}, tu propuesta expira pronto — '
                f'{proposal.discount_percent}% de descuento si accedes hoy'
            )

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[proposal.client_email],
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            proposal.urgency_email_sent_at = timezone.now()
            proposal.save(update_fields=['urgency_email_sent_at'])

            logger.info(
                'Sent urgency email for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send urgency email for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_response_notification(cls, proposal, action):
        """
        Send notification email to team@projectapp.co when a client
        accepts or rejects a proposal.
        """
        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'total_investment': proposal.total_investment,
            'currency': proposal.currency,
            'action': action,
            'action_label': 'ACEPTADA' if action == 'accepted' else 'RECHAZADA',
            'proposal_uuid': str(proposal.uuid),
            'rejection_reason': getattr(proposal, 'rejection_reason', ''),
            'rejection_comment': getattr(proposal, 'rejection_comment', ''),
        }

        try:
            html_content = render_to_string(
                'emails/proposal_response_notification.html', context
            )
            text_content = render_to_string(
                'emails/proposal_response_notification.txt', context
            )

            action_tag = 'ACCEPTED' if action == 'accepted' else 'REJECTED'
            subject = (
                f'[{action_tag}] Propuesta: {proposal.title} — '
                f'{proposal.client_name}'
            )

            notification_email = getattr(
                settings, 'NOTIFICATION_EMAIL', 'team@projectapp.co'
            )

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[notification_email],
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            logger.info(
                'Sent %s notification for proposal %s',
                action, proposal.uuid,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send %s notification for proposal %s',
                action, proposal.uuid,
            )
            return False

    @classmethod
    def send_acceptance_confirmation(cls, proposal):
        """
        Send acceptance confirmation email to the client with a link
        to view/download their proposal. Attaches a PDF of the proposal
        when generation succeeds.
        """
        if not proposal.client_email:
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'title': proposal.title,
            'total_investment': proposal.total_investment,
            'currency': proposal.currency,
        }

        try:
            html_content = render_to_string(
                'emails/proposal_accepted_client.html', context
            )
            text_content = render_to_string(
                'emails/proposal_accepted_client.txt', context
            )

            subject = (
                f'✅ {proposal.client_name}, tu propuesta ha sido aceptada — '
                f'Project App'
            )

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[proposal.client_email],
            )
            email.attach_alternative(html_content, 'text/html')

            # Attach proposal PDF if generation succeeds
            try:
                from content.services.proposal_pdf_service import (
                    ProposalPdfService,
                )
                pdf_bytes = ProposalPdfService.generate(proposal)
                if pdf_bytes:
                    filename = f'Propuesta_{proposal.client_name}.pdf'
                    email.attach(filename, pdf_bytes, 'application/pdf')
                    logger.info(
                        'Attached PDF (%d bytes) to acceptance email for %s',
                        len(pdf_bytes), proposal.uuid,
                    )
            except Exception:
                logger.warning(
                    'PDF generation failed for proposal %s, '
                    'sending email without attachment',
                    proposal.uuid,
                    exc_info=True,
                )

            email.send(fail_silently=False)

            logger.info(
                'Sent acceptance confirmation for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send acceptance confirmation for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_rejection_thank_you(cls, proposal):
        """
        Send a thank-you email to the client when they reject a proposal.
        Includes an inspirational message inviting future collaboration.
        """
        if not proposal.client_email:
            return False

        context = {
            'client_name': proposal.client_name,
            'title': proposal.title,
        }

        try:
            html_content = render_to_string(
                'emails/proposal_rejected_client.html', context
            )
            text_content = render_to_string(
                'emails/proposal_rejected_client.txt', context
            )

            subject = (
                f'Gracias por tu tiempo, {proposal.client_name} — '
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

            logger.info(
                'Sent rejection thank-you for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send rejection thank-you for proposal %s',
                proposal.uuid,
            )
            return False
