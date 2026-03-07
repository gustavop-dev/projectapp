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
        Send an urgency/reminder email at day 15.

        If proposal.discount_percent > 0, sends the discount-focused template.
        Otherwise, sends a simpler reminder without discount info.

        Args:
            proposal: BusinessProposal instance with client_email set.

        Returns:
            bool: True if the email was sent successfully.
        """
        if not proposal.client_email:
            return False

        has_discount = (
            proposal.discount_percent and proposal.discount_percent > 0
        )

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'days_remaining': proposal.days_remaining,
            'expires_at': proposal.expires_at,
            'total_investment': proposal.total_investment,
            'currency': proposal.currency,
            'title': proposal.title,
        }

        if has_discount:
            from decimal import Decimal
            discount_factor = (
                Decimal(100 - proposal.discount_percent) / Decimal(100)
            )
            discounted = proposal.total_investment * discount_factor
            context.update({
                'discounted_investment': discounted,
                'discount_percent': proposal.discount_percent,
            })
            html_template = 'emails/proposal_urgency.html'
            txt_template = 'emails/proposal_urgency.txt'
            subject = (
                f'🔥 {proposal.client_name}, tu propuesta expira pronto — '
                f'{proposal.discount_percent}% de descuento si accedes hoy'
            )
        else:
            html_template = 'emails/proposal_urgency_no_discount.html'
            txt_template = 'emails/proposal_urgency_no_discount.txt'
            subject = (
                f'⏰ {proposal.client_name}, tu propuesta expira pronto — '
                f'Project App'
            )

        try:
            html_content = render_to_string(html_template, context)
            text_content = render_to_string(txt_template, context)

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
                'Sent urgency email for proposal %s to %s (discount=%s)',
                proposal.uuid, proposal.client_email, has_discount,
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

    @classmethod
    def send_first_view_notification(cls, proposal):
        """
        Send notification email to team@projectapp.co when a client
        opens a proposal for the first time. This is the ideal moment
        for the sales team to do follow-up.
        """
        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'total_investment': proposal.total_investment,
            'currency': proposal.currency,
            'proposal_uuid': str(proposal.uuid),
            'viewed_at': proposal.first_viewed_at or timezone.now(),
            'client_email': proposal.client_email or '',
        }

        try:
            html_content = render_to_string(
                'emails/proposal_first_view_notification.html', context
            )
            text_content = render_to_string(
                'emails/proposal_first_view_notification.txt', context
            )

            subject = (
                f'\U0001f441 [OPENED] Propuesta: {proposal.title} — '
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
                'Sent first-view notification for proposal %s',
                proposal.uuid,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send first-view notification for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_comment_notification(cls, proposal, comment):
        """
        Send notification email to team@projectapp.co when a client
        submits a negotiation comment ("Tengo comentarios antes de decidir").
        This is a high-intent signal — client is not rejecting, just negotiating.
        """
        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'total_investment': proposal.total_investment,
            'currency': proposal.currency,
            'comment': comment,
            'proposal_uuid': str(proposal.uuid),
        }

        try:
            html_content = render_to_string(
                'emails/proposal_comment_notification.html', context
            )
            text_content = render_to_string(
                'emails/proposal_comment_notification.txt', context
            )

            subject = (
                f'[COMENTARIO] Propuesta: {proposal.title} — '
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
                'Sent comment notification for proposal %s',
                proposal.uuid,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send comment notification for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_rejection_reengagement(cls, proposal):
        """
        Send a personalized re-engagement email to the client 48h after
        rejecting due to budget concerns. Invites them to explore a
        reduced scope or payment flexibility.
        """
        if not proposal.client_email:
            return False

        from decimal import Decimal
        has_discount = bool(proposal.discount_percent and proposal.discount_percent > 0)
        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'total_investment': proposal.total_investment,
            'currency': proposal.currency,
        }
        if has_discount:
            discount_factor = (
                Decimal(100 - proposal.discount_percent) / Decimal(100)
            )
            context['discounted_investment'] = proposal.total_investment * discount_factor
            context['discount_percent'] = proposal.discount_percent

        try:
            html_content = render_to_string(
                'emails/proposal_reengagement.html', context
            )
            text_content = render_to_string(
                'emails/proposal_reengagement.txt', context
            )

            subject = (
                f'{proposal.client_name}, ¿podemos encontrar una solución '
                f'que se ajuste a tu presupuesto?'
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
                'Sent rejection re-engagement email for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send re-engagement email for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_revisit_alert(cls, proposal, visit_count, top_section='', top_section_time=0):
        """
        Send a smart follow-up alert to team@projectapp.co when a client
        shows strong engagement signals (multiple revisits or high time on
        key sections like Investment).
        """
        top_section_display = top_section or 'N/A'
        top_time_display = f'{int(top_section_time // 60)}m {int(top_section_time % 60)}s'

        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'total_investment': proposal.total_investment,
            'currency': proposal.currency,
            'visit_count': visit_count,
            'top_section': top_section_display,
            'top_section_time': top_time_display,
            'proposal_uuid': str(proposal.uuid),
        }

        try:
            html_content = render_to_string(
                'emails/proposal_revisit_alert.html', context
            )
            text_content = render_to_string(
                'emails/proposal_revisit_alert.txt', context
            )

            subject = (
                f'\U0001f525 [HOT LEAD] {proposal.client_name} revisó la propuesta '
                f'{visit_count} veces'
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

            proposal.revisit_alert_sent_at = timezone.now()
            proposal.save(update_fields=['revisit_alert_sent_at'])

            logger.info(
                'Sent revisit alert for proposal %s (visits=%d)',
                proposal.uuid, visit_count,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send revisit alert for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_abandonment_followup(cls, proposal):
        """
        Send a follow-up email when the client viewed the proposal but
        never reached the investment section, suggesting a call to discuss.
        """
        if not proposal.client_email:
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'title': proposal.title,
        }

        try:
            html_content = render_to_string(
                'emails/proposal_abandonment_followup.html', context
            )
            text_content = render_to_string(
                'emails/proposal_abandonment_followup.txt', context
            )

            subject = (
                f'📋 {proposal.client_name}, ¿te quedaron dudas sobre '
                f'la propuesta? — Project App'
            )

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[proposal.client_email],
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            proposal.abandonment_email_sent_at = timezone.now()
            proposal.save(update_fields=['abandonment_email_sent_at'])

            logger.info(
                'Sent abandonment followup for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send abandonment followup for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_investment_interest_followup(cls, proposal, time_on_investment=0):
        """
        Send a follow-up email when the client spent significant time
        on the investment section, offering to discuss payment options.
        """
        if not proposal.client_email:
            return False

        time_display = f'{int(time_on_investment // 60)}m {int(time_on_investment % 60)}s'

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'title': proposal.title,
            'total_investment': proposal.total_investment,
            'currency': proposal.currency,
            'time_on_investment': time_display,
        }

        try:
            html_content = render_to_string(
                'emails/proposal_investment_interest_followup.html', context
            )
            text_content = render_to_string(
                'emails/proposal_investment_interest_followup.txt', context
            )

            subject = (
                f'💰 {proposal.client_name}, hablemos sobre opciones '
                f'de inversión — Project App'
            )

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[proposal.client_email],
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            proposal.investment_interest_email_sent_at = timezone.now()
            proposal.save(update_fields=['investment_interest_email_sent_at'])

            logger.info(
                'Sent investment interest followup for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send investment interest followup for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_share_notification(cls, proposal, share_link):
        """
        Notify the sales team when a client shares the proposal
        with another person (multi-stakeholder signal).
        """
        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'shared_by_name': share_link.shared_by_name,
            'shared_by_email': share_link.shared_by_email,
            'proposal_uuid': str(proposal.uuid),
        }

        try:
            html_content = render_to_string(
                'emails/proposal_share_notification.html', context
            )
            text_content = render_to_string(
                'emails/proposal_share_notification.txt', context
            )

            subject = (
                f'🔗 [SHARED] {proposal.client_name} compartió la propuesta '
                f'"{proposal.title}"'
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
                'Sent share notification for proposal %s (shared by %s)',
                proposal.uuid, share_link.shared_by_name,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send share notification for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_scheduled_followup(cls, proposal):
        """
        Send a scheduled follow-up email to a client who previously
        rejected the proposal with "Not the right time".
        """
        if not proposal.client_email:
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'title': proposal.title,
        }

        try:
            html_content = render_to_string(
                'emails/proposal_scheduled_followup.html', context
            )
            text_content = render_to_string(
                'emails/proposal_scheduled_followup.txt', context
            )

            subject = (
                f'👋 {proposal.client_name}, ¿es buen momento para '
                f'retomar tu proyecto? — Project App'
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
                'Sent scheduled followup for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send scheduled followup for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_stakeholder_detected_notification(cls, proposal, known_ips_count):
        """
        Notify the sales team when the proposal is accessed from a new
        IP address, suggesting a secondary decision-maker is reviewing it.
        """
        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'total_investment': proposal.total_investment,
            'currency': proposal.currency,
            'proposal_uuid': str(proposal.uuid),
            'known_ips_count': known_ips_count,
        }

        try:
            html_content = render_to_string(
                'emails/proposal_stakeholder_detected.html', context
            )
            text_content = render_to_string(
                'emails/proposal_stakeholder_detected.txt', context
            )

            subject = (
                f'\U0001f465 [NUEVO LECTOR] Propuesta: {proposal.title} — '
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
                'Sent stakeholder detection notification for proposal %s',
                proposal.uuid,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send stakeholder notification for proposal %s',
                proposal.uuid,
            )
            return False
