import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from content.utils import format_bogota_date, format_cop_email

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
    def _get_notification_recipients(cls):
        """
        Return internal notification recipients.

        Supports:
        - NOTIFICATION_EMAIL (single email or comma-separated emails)
        - NOTIFICATION_EMAILS (list/tuple/set or comma-separated string)
        """
        recipients = []

        def _append(value):
            if not value:
                return
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    _append(item)
                return
            for part in str(value).split(','):
                email = part.strip()
                if email and email not in recipients:
                    recipients.append(email)

        _append(getattr(settings, 'NOTIFICATION_EMAILS', None))
        _append(getattr(settings, 'NOTIFICATION_EMAIL', None))

        if not recipients:
            recipients.append('team@projectapp.co')

        return recipients

    @classmethod
    def _log_email(cls, template_key, recipient, subject='', proposal=None,
                   status='sent', error_message='', metadata=None):
        """Log an email send attempt to the EmailLog model."""
        try:
            from content.models import EmailLog
            EmailLog.objects.create(
                proposal=proposal,
                template_key=template_key,
                recipient=recipient,
                subject=subject[:500] if subject else '',
                status=status,
                error_message=error_message,
                metadata=metadata or {},
            )
        except Exception:
            logger.exception('Failed to create EmailLog entry')

    @classmethod
    def _is_template_active(cls, template_key):
        """Check if a template is active (not disabled by admin)."""
        from content.models import EmailTemplateConfig
        config = EmailTemplateConfig.objects.filter(
            template_key=template_key,
        ).first()
        if config is None:
            return True
        return config.is_active

    @classmethod
    def _check_cooldown(cls, proposal, cooldown_hours=24):
        """
        Check if enough time has passed since the last automated email.
        If cooldown has passed, update last_automated_email_at and return True.
        Otherwise return False (email should be skipped).
        """
        from datetime import timedelta
        now = timezone.now()
        if (
            proposal.last_automated_email_at
            and (now - proposal.last_automated_email_at) < timedelta(hours=cooldown_hours)
        ):
            logger.info(
                'Skipping automated email for %s: cooldown active (last sent %s)',
                proposal.uuid, proposal.last_automated_email_at,
            )
            return False
        proposal.last_automated_email_at = now
        proposal.save(update_fields=['last_automated_email_at'])
        return True

    @classmethod
    def _resolve_content(cls, template_key, context):
        """
        Resolve editable field values for a template, merging DB overrides
        with registry defaults, then substituting {variable} placeholders
        with actual context values.

        Returns a dict of {field_key: resolved_value}.
        """
        from content.models import EmailTemplateConfig
        from content.services.email_template_registry import (
            resolve_field_values,
            substitute_variables,
        )

        config = EmailTemplateConfig.objects.filter(
            template_key=template_key,
        ).first()
        overrides = config.content_overrides if config else {}
        field_values = resolve_field_values(template_key, overrides)

        resolved = {}
        for key, value in field_values.items():
            resolved[key] = substitute_variables(value, context)
        return resolved

    @classmethod
    def send_proposal_to_client(cls, proposal):
        """
        Send the initial proposal email to the client with a link to view it.

        Args:
            proposal: BusinessProposal instance with client_email set.

        Returns:
            bool: True if the email was sent successfully.
        """
        if not proposal.client_email:
            logger.warning(
                'Cannot send proposal email for %s: no client_email',
                proposal.uuid,
            )
            return False

        if not cls._is_template_active('proposal_sent_client'):
            logger.info('Skipping proposal_sent_client: template disabled')
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'days_remaining': proposal.days_remaining,
            'expires_at': proposal.expires_at,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'title': proposal.title,
        }

        resolved = cls._resolve_content('proposal_sent_client', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_sent_client.html', context
            )
            text_content = render_to_string(
                'emails/proposal_sent_client.txt', context
            )

            subject = resolved.get('subject', (
                f'📋 {proposal.client_name}, tu propuesta está lista — '
                f'Project App'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[proposal.client_email],
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            cls._log_email(
                'proposal_sent_client', proposal.client_email,
                subject=subject, proposal=proposal, status='sent',
            )
            logger.info(
                'Sent proposal email for %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception as exc:
            cls._log_email(
                'proposal_sent_client', proposal.client_email,
                subject='', proposal=proposal, status='failed',
                error_message=str(exc)[:1000],
            )
            logger.exception(
                'Failed to send proposal email for %s',
                proposal.uuid,
            )
            return False

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

        if not cls._is_template_active('proposal_reminder'):
            logger.info('Skipping proposal_reminder: template disabled')
            return False

        if not cls._check_cooldown(proposal):
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'days_remaining': proposal.days_remaining,
            'expires_at': proposal.expires_at,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'title': proposal.title,
        }

        resolved = cls._resolve_content('proposal_reminder', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_reminder.html', context
            )
            text_content = render_to_string(
                'emails/proposal_reminder.txt', context
            )

            subject = resolved.get('subject', (
                f'📋 {proposal.client_name}, tu propuesta te espera — '
                f'Project App'
            ))

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

            cls._log_email(
                'proposal_reminder', proposal.client_email,
                subject=subject, proposal=proposal, status='sent',
            )
            logger.info(
                'Sent reminder email for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception as exc:
            cls._log_email(
                'proposal_reminder', proposal.client_email,
                subject='', proposal=proposal, status='failed',
                error_message=str(exc)[:1000],
            )
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

        template_key = (
            'proposal_urgency' if has_discount
            else 'proposal_urgency_no_discount'
        )

        if not cls._is_template_active(template_key):
            logger.info('Skipping %s: template disabled', template_key)
            return False

        if not cls._check_cooldown(proposal):
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'days_remaining': proposal.days_remaining,
            'expires_at': proposal.expires_at,
            'total_investment': format_cop_email(proposal.total_investment),
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
                'discounted_investment': format_cop_email(discounted),
                'discount_percent': proposal.discount_percent,
            })
            html_template = 'emails/proposal_urgency.html'
            txt_template = 'emails/proposal_urgency.txt'
        else:
            html_template = 'emails/proposal_urgency_no_discount.html'
            txt_template = 'emails/proposal_urgency_no_discount.txt'

        resolved = cls._resolve_content(template_key, context)
        context.update(resolved)
        subject = resolved.get('subject', f'{proposal.client_name}, tu propuesta expira pronto')

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

            cls._log_email(
                template_key, proposal.client_email,
                subject=subject, proposal=proposal, status='sent',
            )
            logger.info(
                'Sent urgency email for proposal %s to %s (discount=%s)',
                proposal.uuid, proposal.client_email, has_discount,
            )
            return True

        except Exception as exc:
            cls._log_email(
                template_key, proposal.client_email,
                subject=subject, proposal=proposal, status='failed',
                error_message=str(exc)[:1000],
            )
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
        if not cls._is_template_active('proposal_response_notification'):
            logger.info('Skipping proposal_response_notification: template disabled')
            return False

        action_tag = (
            'ACCEPTED' if action == 'accepted'
            else 'NEGOTIATING' if action == 'negotiating'
            else 'REJECTED'
        )
        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'action': action,
            'action_label': (
                'ACEPTADA' if action == 'accepted'
                else 'NEGOCIANDO' if action == 'negotiating'
                else 'RECHAZADA'
            ),
            'action_tag': action_tag,
            'proposal_uuid': str(proposal.uuid),
            'rejection_reason': getattr(proposal, 'rejection_reason', ''),
            'rejection_comment': getattr(proposal, 'rejection_comment', ''),
        }

        resolved = cls._resolve_content('proposal_response_notification', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_response_notification.html', context
            )
            text_content = render_to_string(
                'emails/proposal_response_notification.txt', context
            )

            subject = resolved.get('subject', (
                f'[{action_tag}] Propuesta: {proposal.title} — '
                f'{proposal.client_name}'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=cls._get_notification_recipients(),
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

        if not cls._is_template_active('proposal_accepted_client'):
            logger.info('Skipping proposal_accepted_client: template disabled')
            return False

        base = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000').rstrip('/')
        platform_login_url = f'{base}/platform/login'
        dlv = getattr(proposal, 'deliverable', None)
        project_name = ''
        deliverable_title = ''
        if dlv is not None:
            project_name = dlv.project.name if dlv.project_id else ''
            deliverable_title = dlv.title or ''

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'platform_login_url': platform_login_url,
            'project_name': project_name,
            'deliverable_title': deliverable_title,
        }

        resolved = cls._resolve_content('proposal_accepted_client', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_accepted_client.html', context
            )
            text_content = render_to_string(
                'emails/proposal_accepted_client.txt', context
            )

            subject = resolved.get('subject', (
                f'✅ {proposal.client_name}, tu propuesta ha sido aceptada — '
                f'Project App'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[proposal.client_email],
            )
            email.attach_alternative(html_content, 'text/html')

            from django.utils.text import slugify

            safe_client = slugify(proposal.client_name) or 'Cliente'

            # Commercial proposal PDF
            try:
                from content.services.proposal_pdf_service import ProposalPdfService

                pdf_bytes = ProposalPdfService.generate(proposal)
                if pdf_bytes:
                    email.attach(
                        f'Propuesta_comercial_{safe_client}.pdf',
                        pdf_bytes,
                        'application/pdf',
                    )
                    logger.info(
                        'Attached commercial PDF (%d bytes) to acceptance email for %s',
                        len(pdf_bytes), proposal.uuid,
                    )
            except Exception:
                logger.warning(
                    'Commercial PDF generation failed for proposal %s',
                    proposal.uuid,
                    exc_info=True,
                )

            # Technical document PDF
            try:
                from content.services.technical_document_pdf import (
                    generate_technical_document_pdf,
                )

                tech_pdf = generate_technical_document_pdf(proposal)
                if tech_pdf:
                    email.attach(
                        f'Documento_tecnico_{safe_client}.pdf',
                        tech_pdf,
                        'application/pdf',
                    )
            except Exception:
                logger.warning(
                    'Technical PDF attachment failed for proposal %s',
                    proposal.uuid,
                    exc_info=True,
                )

            # Platform onboarding guide PDF
            try:
                from content.services.platform_onboarding_pdf import (
                    generate_platform_onboarding_pdf,
                )

                guide_pdf = generate_platform_onboarding_pdf(
                    client_name=proposal.client_name or '',
                    client_email=proposal.client_email or '',
                    project_name=project_name,
                    deliverable_title=deliverable_title,
                    platform_login_url=platform_login_url,
                )
                if guide_pdf:
                    email.attach(
                        f'Guia_plataforma_{safe_client}.pdf',
                        guide_pdf,
                        'application/pdf',
                    )
            except Exception:
                logger.warning(
                    'Platform guide PDF failed for proposal %s',
                    proposal.uuid,
                    exc_info=True,
                )

            email.send(fail_silently=False)

            cls._log_email(
                'proposal_accepted_client', proposal.client_email,
                subject=subject, proposal=proposal, status='sent',
            )
            logger.info(
                'Sent acceptance confirmation for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception as exc:
            cls._log_email(
                'proposal_accepted_client', proposal.client_email,
                subject=locals().get('subject', ''), proposal=proposal,
                status='failed', error_message=str(exc)[:1000],
            )
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

        if not cls._is_template_active('proposal_rejected_client'):
            logger.info('Skipping proposal_rejected_client: template disabled')
            return False

        context = {
            'client_name': proposal.client_name,
            'title': proposal.title,
        }

        resolved = cls._resolve_content('proposal_rejected_client', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_rejected_client.html', context
            )
            text_content = render_to_string(
                'emails/proposal_rejected_client.txt', context
            )

            subject = resolved.get('subject', (
                f'Gracias por tu tiempo, {proposal.client_name} — '
                f'Project App'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[proposal.client_email],
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            cls._log_email(
                'proposal_rejected_client', proposal.client_email,
                subject=subject, proposal=proposal, status='sent',
            )
            logger.info(
                'Sent rejection thank-you for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception as exc:
            cls._log_email(
                'proposal_rejected_client', proposal.client_email,
                subject=locals().get('subject', ''), proposal=proposal,
                status='failed', error_message=str(exc)[:1000],
            )
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
        if not cls._is_template_active('proposal_first_view_notification'):
            logger.info('Skipping proposal_first_view_notification: template disabled')
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'proposal_uuid': str(proposal.uuid),
            'viewed_at': proposal.first_viewed_at or timezone.now(),
            'client_email': proposal.client_email or '',
        }

        resolved = cls._resolve_content('proposal_first_view_notification', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_first_view_notification.html', context
            )
            text_content = render_to_string(
                'emails/proposal_first_view_notification.txt', context
            )

            subject = resolved.get('subject', (
                f'\U0001f441 [OPENED] Propuesta: {proposal.title} — '
                f'{proposal.client_name}'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=cls._get_notification_recipients(),
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
        if not cls._is_template_active('proposal_comment_notification'):
            logger.info('Skipping proposal_comment_notification: template disabled')
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'comment': comment,
            'proposal_uuid': str(proposal.uuid),
        }

        resolved = cls._resolve_content('proposal_comment_notification', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_comment_notification.html', context
            )
            text_content = render_to_string(
                'emails/proposal_comment_notification.txt', context
            )

            subject = resolved.get('subject', (
                f'[COMENTARIO] Propuesta: {proposal.title} — '
                f'{proposal.client_name}'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=cls._get_notification_recipients(),
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

        if not cls._is_template_active('proposal_reengagement'):
            logger.info('Skipping proposal_reengagement: template disabled')
            return False

        from decimal import Decimal
        has_discount = bool(proposal.discount_percent and proposal.discount_percent > 0)
        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
        }
        if has_discount:
            discount_factor = (
                Decimal(100 - proposal.discount_percent) / Decimal(100)
            )
            context['discounted_investment'] = format_cop_email(
                proposal.total_investment * discount_factor
            )
            context['discount_percent'] = proposal.discount_percent

        resolved = cls._resolve_content('proposal_reengagement', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_reengagement.html', context
            )
            text_content = render_to_string(
                'emails/proposal_reengagement.txt', context
            )

            subject = resolved.get('subject', (
                f'{proposal.client_name}, ¿podemos encontrar una solución '
                f'que se ajuste a tu presupuesto?'
            ))

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
        if not cls._is_template_active('proposal_revisit_alert'):
            logger.info('Skipping proposal_revisit_alert: template disabled')
            return False

        top_section_display = top_section or 'N/A'
        top_time_display = f'{int(top_section_time // 60)}m {int(top_section_time % 60)}s'

        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'visit_count': visit_count,
            'top_section': top_section_display,
            'top_section_time': top_time_display,
            'proposal_uuid': str(proposal.uuid),
        }

        resolved = cls._resolve_content('proposal_revisit_alert', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_revisit_alert.html', context
            )
            text_content = render_to_string(
                'emails/proposal_revisit_alert.txt', context
            )

            subject = resolved.get('subject', (
                f'\U0001f525 [HOT LEAD] {proposal.client_name} revisó la propuesta '
                f'{visit_count} veces'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=cls._get_notification_recipients(),
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

        if not cls._is_template_active('proposal_abandonment_followup'):
            logger.info('Skipping proposal_abandonment_followup: template disabled')
            return False

        if not cls._check_cooldown(proposal):
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'title': proposal.title,
        }

        resolved = cls._resolve_content('proposal_abandonment_followup', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_abandonment_followup.html', context
            )
            text_content = render_to_string(
                'emails/proposal_abandonment_followup.txt', context
            )

            subject = resolved.get('subject', (
                f'📋 {proposal.client_name}, ¿te quedaron dudas sobre '
                f'la propuesta? — Project App'
            ))

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

            cls._log_email(
                'proposal_abandonment_followup', proposal.client_email,
                subject=subject, proposal=proposal, status='sent',
            )
            logger.info(
                'Sent abandonment followup for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception as exc:
            cls._log_email(
                'proposal_abandonment_followup', proposal.client_email,
                subject=locals().get('subject', ''), proposal=proposal,
                status='failed', error_message=str(exc)[:1000],
            )
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

        if not cls._is_template_active('proposal_investment_interest_followup'):
            logger.info('Skipping proposal_investment_interest_followup: template disabled')
            return False

        if not cls._check_cooldown(proposal):
            return False

        time_display = f'{int(time_on_investment // 60)}m {int(time_on_investment % 60)}s'

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'time_on_investment': time_display,
        }

        resolved = cls._resolve_content('proposal_investment_interest_followup', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_investment_interest_followup.html', context
            )
            text_content = render_to_string(
                'emails/proposal_investment_interest_followup.txt', context
            )

            subject = resolved.get('subject', (
                f'💰 {proposal.client_name}, hablemos sobre opciones '
                f'de inversión — Project App'
            ))

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

            cls._log_email(
                'proposal_investment_interest_followup', proposal.client_email,
                subject=subject, proposal=proposal, status='sent',
            )
            logger.info(
                'Sent investment interest followup for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception as exc:
            cls._log_email(
                'proposal_investment_interest_followup', proposal.client_email,
                subject=locals().get('subject', ''), proposal=proposal,
                status='failed', error_message=str(exc)[:1000],
            )
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
        if not cls._is_template_active('proposal_share_notification'):
            logger.info('Skipping proposal_share_notification: template disabled')
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'title': proposal.title,
            'shared_by_name': share_link.shared_by_name,
            'shared_by_email': share_link.shared_by_email,
            'proposal_uuid': str(proposal.uuid),
        }

        resolved = cls._resolve_content('proposal_share_notification', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_share_notification.html', context
            )
            text_content = render_to_string(
                'emails/proposal_share_notification.txt', context
            )

            subject = resolved.get('subject', (
                f'🔗 [SHARED] {proposal.client_name} compartió la propuesta '
                f'"{proposal.title}"'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=cls._get_notification_recipients(),
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

        if not cls._is_template_active('proposal_scheduled_followup'):
            logger.info('Skipping proposal_scheduled_followup: template disabled')
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'title': proposal.title,
        }

        resolved = cls._resolve_content('proposal_scheduled_followup', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_scheduled_followup.html', context
            )
            text_content = render_to_string(
                'emails/proposal_scheduled_followup.txt', context
            )

            subject = resolved.get('subject', (
                f'👋 {proposal.client_name}, ¿es buen momento para '
                f'retomar tu proyecto? — Project App'
            ))

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
        if not cls._is_template_active('proposal_stakeholder_detected'):
            logger.info('Skipping proposal_stakeholder_detected: template disabled')
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'proposal_uuid': str(proposal.uuid),
            'known_ips_count': known_ips_count,
        }

        resolved = cls._resolve_content('proposal_stakeholder_detected', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_stakeholder_detected.html', context
            )
            text_content = render_to_string(
                'emails/proposal_stakeholder_detected.txt', context
            )

            subject = resolved.get('subject', (
                f'\U0001f465 [NUEVO LECTOR] Propuesta: {proposal.title} — '
                f'{proposal.client_name}'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=cls._get_notification_recipients(),
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

    @classmethod
    def send_seller_inactivity_escalation(cls, proposal, days_inactive):
        """
        Send an escalation email to the sales team when a proposal has had
        no seller follow-up for >=5 days after the client viewed it.

        Args:
            proposal: BusinessProposal instance.
            days_inactive: Number of days without seller activity.

        Returns:
            bool: True if the email was sent successfully.
        """
        if not cls._is_template_active('seller_inactivity_escalation'):
            logger.info('Skipping seller_inactivity_escalation: template disabled')
            return False

        frontend_base = getattr(
            settings, 'FRONTEND_BASE_URL', 'http://localhost:3000'
        )
        edit_url = f'{frontend_base}/panel/proposals/{proposal.id}/edit'

        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'days_inactive': days_inactive,
            'edit_url': edit_url,
            'proposal_uuid': str(proposal.uuid),
            'status': proposal.status,
        }

        resolved = cls._resolve_content('seller_inactivity_escalation', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/seller_inactivity_escalation.html', context
            )
            text_content = render_to_string(
                'emails/seller_inactivity_escalation.txt', context
            )

            subject = resolved.get('subject', (
                f'\u26a0\ufe0f Propuesta sin seguimiento: '
                f'{proposal.client_name} — {proposal.title}'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=cls._get_notification_recipients(),
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            logger.info(
                'Sent seller inactivity escalation for proposal %s (%d days)',
                proposal.uuid, days_inactive,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send seller inactivity escalation for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_negotiation_notification(cls, proposal, comment=''):
        """
        Send notification to the sales team when a client wants to
        accept with changes (negotiating status).
        """
        if not cls._is_template_active('proposal_negotiation_notification'):
            logger.info('Skipping proposal_negotiation_notification: template disabled')
            return False

        frontend_base = getattr(
            settings, 'FRONTEND_BASE_URL', 'http://localhost:3000'
        )
        edit_url = f'{frontend_base}/panel/proposals/{proposal.id}/edit'

        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'comment': comment,
            'edit_url': edit_url,
            'proposal_uuid': str(proposal.uuid),
        }

        resolved = cls._resolve_content('proposal_negotiation_notification', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_negotiation_notification.html', context
            )
            text_content = render_to_string(
                'emails/proposal_negotiation_notification.txt', context
            )

            subject = resolved.get('subject', (
                f'🤝 [NEGOCIANDO] {proposal.client_name} quiere '
                f'ajustar la propuesta "{proposal.title}"'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=cls._get_notification_recipients(),
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            logger.info(
                'Sent negotiation notification for proposal %s',
                proposal.uuid,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send negotiation notification for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_negotiation_confirmation(cls, proposal):
        """
        Send confirmation email to the client when they choose
        'accept with changes' (negotiating).
        """
        if not proposal.client_email:
            return False

        if not cls._is_template_active('proposal_negotiation_confirmation'):
            logger.info('Skipping proposal_negotiation_confirmation: template disabled')
            return False

        context = {
            'client_name': proposal.client_name,
            'proposal_url': proposal.public_url,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
        }

        resolved = cls._resolve_content('proposal_negotiation_confirmation', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_negotiation_confirmation.html', context
            )
            text_content = render_to_string(
                'emails/proposal_negotiation_confirmation.txt', context
            )

            subject = resolved.get('subject', (
                f'🤝 {proposal.client_name}, recibimos tu solicitud '
                f'de ajustes — Project App'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[proposal.client_email],
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            cls._log_email(
                'proposal_negotiation_confirmation', proposal.client_email,
                subject=subject, proposal=proposal, status='sent',
            )
            logger.info(
                'Sent negotiation confirmation for proposal %s to %s',
                proposal.uuid, proposal.client_email,
            )
            return True

        except Exception as exc:
            cls._log_email(
                'proposal_negotiation_confirmation', proposal.client_email,
                subject=locals().get('subject', ''), proposal=proposal,
                status='failed', error_message=str(exc)[:1000],
            )
            logger.exception(
                'Failed to send negotiation confirmation for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_post_rejection_revisit_alert(cls, proposal):
        """
        Send immediate alert to the sales team when a rejected client
        revisits the proposal after 7+ days — high-intent reconsideration signal.
        """
        if not cls._is_template_active('post_rejection_revisit_alert'):
            logger.info('Skipping post_rejection_revisit_alert: template disabled')
            return False

        frontend_base = getattr(
            settings, 'FRONTEND_BASE_URL', 'http://localhost:3000'
        )
        edit_url = f'{frontend_base}/panel/proposals/{proposal.id}/edit'

        days_since = 0
        if proposal.responded_at:
            days_since = (timezone.now() - proposal.responded_at).days

        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'edit_url': edit_url,
            'proposal_uuid': str(proposal.uuid),
            'days_since_rejection': days_since,
        }

        resolved = cls._resolve_content('post_rejection_revisit_alert', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/post_rejection_revisit_alert.html', context
            )
            text_content = render_to_string(
                'emails/post_rejection_revisit_alert.txt', context
            )

            subject = resolved.get('subject', (
                f'🔄 [RECONSIDERACIÓN] {proposal.client_name} revisitó la '
                f'propuesta rechazada "{proposal.title}" ({days_since}d después)'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=cls._get_notification_recipients(),
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            logger.info(
                'Sent post-rejection revisit alert for proposal %s (%d days)',
                proposal.uuid, days_since,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send post-rejection revisit alert for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_daily_pipeline_digest(cls, digest_data):
        """
        Send a daily pipeline digest email summarising proposal activity.

        Args:
            digest_data: dict with keys:
                - viewed_yesterday: list of proposal dicts
                - inactive: list of proposal dicts
                - expiring_soon: list of proposal dicts
                - total_active: int
                - date: str
        """
        if not cls._is_template_active('daily_pipeline_digest'):
            logger.info('Skipping daily_pipeline_digest: template disabled')
            return False

        context = digest_data

        resolved = cls._resolve_content('daily_pipeline_digest', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/daily_pipeline_digest.html', context
            )
            text_content = render_to_string(
                'emails/daily_pipeline_digest.txt', context
            )

            subject = resolved.get('subject', (
                f'📊 Pipeline Diario — {digest_data["date"]} — '
                f'{digest_data["total_active"]} propuestas activas'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=cls._get_notification_recipients(),
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            logger.info('Sent daily pipeline digest for %s', digest_data['date'])
            return True

        except Exception:
            logger.exception('Failed to send daily pipeline digest')
            return False

    @classmethod
    def send_post_expiration_visit_alert(cls, proposal):
        """
        Send immediate alert to the sales team when a client opens
        an expired proposal — high-intent signal.
        """
        if not cls._is_template_active('proposal_post_expiration_visit'):
            logger.info('Skipping proposal_post_expiration_visit: template disabled')
            return False

        frontend_base = getattr(
            settings, 'FRONTEND_BASE_URL', 'http://localhost:3000'
        )
        edit_url = f'{frontend_base}/panel/proposals/{proposal.id}/edit'

        context = {
            'client_name': proposal.client_name,
            'proposal_title': proposal.title,
            'title': proposal.title,
            'total_investment': format_cop_email(proposal.total_investment),
            'currency': proposal.currency,
            'edit_url': edit_url,
            'proposal_uuid': str(proposal.uuid),
        }

        resolved = cls._resolve_content('proposal_post_expiration_visit', context)
        context.update(resolved)

        try:
            html_content = render_to_string(
                'emails/proposal_post_expiration_visit.html', context
            )
            text_content = render_to_string(
                'emails/proposal_post_expiration_visit.txt', context
            )

            subject = resolved.get('subject', (
                f'🔥 {proposal.client_name} abrió la propuesta expirada '
                f'"{proposal.title}" — ¡Alto interés!'
            ))

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=cls._get_notification_recipients(),
            )
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)

            logger.info(
                'Sent post-expiration visit alert for proposal %s',
                proposal.uuid,
            )
            return True

        except Exception:
            logger.exception(
                'Failed to send post-expiration visit alert for proposal %s',
                proposal.uuid,
            )
            return False

    @classmethod
    def send_magic_link_email(cls, email, proposals):
        """
        Send a magic link email containing links to the client's proposals.

        Args:
            email: Client email address.
            proposals: List of BusinessProposal instances.
        """
        if not proposals:
            return False

        proposal_links = []
        for p in proposals:
            proposal_links.append({
                'title': p.title,
                'url': p.public_url,
                'status': p.get_status_display(),
                'created_at': format_bogota_date(p.created_at) if p.created_at else '',
            })

        client_name = proposals[0].client_name or ''
        subject = f'Tus propuestas en Project App — {client_name}'

        # Build simple HTML email
        links_html = ''
        for link in proposal_links:
            links_html += (
                f'<tr><td style="padding:12px 16px;border-bottom:1px solid #f0f0f0;">'
                f'<a href="{link["url"]}" style="color:#059669;text-decoration:none;'
                f'font-weight:600;">{link["title"]}</a>'
                f'<br><span style="color:#9ca3af;font-size:12px;">'
                f'{link["status"]} — {link["created_at"]}</span>'
                f'</td></tr>'
            )

        html_content = f"""
        <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                     max-width:560px;margin:0 auto;padding:32px 24px;">
            <h2 style="color:#111827;font-weight:400;margin-bottom:8px;">
                Hola{(' ' + client_name) if client_name else ''},
            </h2>
            <p style="color:#6b7280;line-height:1.6;">
                Solicitaste acceso a tus propuestas. Aquí están los enlaces:
            </p>
            <table style="width:100%;border-collapse:collapse;margin:24px 0;
                          background:#fafafa;border-radius:8px;overflow:hidden;">
                {links_html}
            </table>
            <p style="color:#9ca3af;font-size:13px;margin-top:24px;">
                Si no solicitaste este email, puedes ignorarlo.
            </p>
            <p style="color:#d1d5db;font-size:12px;margin-top:32px;">
                Project App — projectapp.co
            </p>
        </div>
        """

        text_content = (
            f'Hola {client_name},\n\n'
            f'Solicitaste acceso a tus propuestas:\n\n'
            + '\n'.join(
                f'- {l["title"]}: {l["url"]}' for l in proposal_links
            )
            + '\n\nProject App — projectapp.co'
        )

        try:
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[email],
            )
            email_msg.attach_alternative(html_content, 'text/html')
            email_msg.send(fail_silently=False)

            cls._log_email(
                'magic_link', email, subject=subject,
                proposal=proposals[0],
            )

            logger.info('Sent magic link email to %s with %d proposals', email, len(proposals))
            return True

        except Exception:
            cls._log_email(
                'magic_link', email, subject=subject,
                proposal=proposals[0], status='failed',
                error_message='Send failed',
            )
            logger.exception('Failed to send magic link email to %s', email)
            return False

    @classmethod
    def send_documents_to_client(cls, proposal, attachments,
                                  subject=None, greeting=None, body=None,
                                  footer=None, document_descriptions=None):
        """
        Send selected documents to the client as email attachments.

        The admin composes the email content in a modal before sending.
        If content fields are not provided, defaults from the registry are used.

        Args:
            proposal: BusinessProposal instance.
            attachments: list of (filename, pdf_bytes, mime_type) tuples.
            subject: Email subject (pre-resolved by frontend).
            greeting: Greeting text.
            body: Introductory body text.
            footer: Closing text.
            document_descriptions: list of dicts [{'name': str, 'description': str}].

        Returns:
            bool: True if the email was sent successfully.
        """
        if not proposal.client_email:
            logger.warning(
                'Cannot send documents for proposal %s: no client_email',
                proposal.pk,
            )
            return False

        template_key = 'proposal_documents_sent'
        if not cls._is_template_active(template_key):
            logger.info('Skipping %s: template disabled', template_key)
            return False

        # Fall back to registry defaults for any missing fields
        if not subject or not greeting or not body or not footer:
            fallback_context = {
                'client_name': proposal.client_name,
                'title': proposal.title,
            }
            resolved = cls._resolve_content(template_key, fallback_context)
            if not subject:
                subject = resolved.get('subject', (
                    f'\U0001f4ce {proposal.client_name}, te compartimos documentos '
                    f'de tu proyecto \u2014 Project App'
                ))
            if not greeting:
                greeting = resolved.get('greeting', f'Hola {proposal.client_name}')
            if not body:
                body = resolved.get('body', '')
            if not footer:
                footer = resolved.get('footer', '')

        context = {
            'client_name': proposal.client_name,
            'title': proposal.title,
            'greeting': greeting,
            'body': body,
            'footer': footer or '',
            'document_descriptions': document_descriptions or [],
        }

        try:
            html_content = render_to_string(
                'emails/proposal_documents_sent.html', context
            )
            text_content = render_to_string(
                'emails/proposal_documents_sent.txt', context
            )

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[proposal.client_email],
            )
            email.attach_alternative(html_content, 'text/html')

            for filename, data, mime_type in attachments:
                email.attach(filename, data, mime_type)

            email.send(fail_silently=False)

            cls._log_email(
                template_key, proposal.client_email,
                subject=subject, proposal=proposal, status='sent',
            )
            logger.info(
                'Sent %d documents for proposal %s to %s',
                len(attachments), proposal.pk, proposal.client_email,
            )
            return True

        except Exception as exc:
            cls._log_email(
                template_key, proposal.client_email,
                subject='', proposal=proposal, status='failed',
                error_message=str(exc)[:1000],
            )
            logger.exception(
                'Failed to send documents for proposal %s', proposal.pk,
            )
            return False

    # ── User-composed emails (branded & proposal) ───────────────────

    @classmethod
    def _send_composed_email(
        cls, template_key, proposal, recipient_email, subject,
        greeting, sections, footer='', attachments=None,
    ):
        """
        Send a user-composed email with the standard Project App branding.

        Shared implementation for branded emails and proposal emails.
        """
        attachment_names = [a[0] for a in attachments] if attachments else []
        log_metadata = {
            'greeting': greeting,
            'sections': sections,
            'footer': footer,
            'attachment_names': attachment_names,
        }

        try:
            context = {
                'subject': subject,
                'greeting': greeting,
                'sections': sections,
                'footer': footer,
                'attachment_names': attachment_names,
            }

            from content.services.email_template_registry import get_template_entry
            entry = get_template_entry(template_key)
            html_content = render_to_string(entry['html_template'], context)
            text_content = render_to_string(entry['txt_template'], context)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_from_email(),
                to=[recipient_email],
            )
            email.attach_alternative(html_content, 'text/html')

            if attachments:
                for filename, data, mime_type in attachments:
                    email.attach(filename, data, mime_type)

            email.send(fail_silently=False)

            cls._log_email(
                template_key, recipient_email,
                subject=subject, proposal=proposal, status='sent',
                metadata=log_metadata,
            )
            logger.info(
                'Sent %s for proposal %s to %s',
                template_key, proposal.pk if proposal else 'standalone', recipient_email,
            )
            return True

        except Exception as exc:
            cls._log_email(
                template_key, recipient_email,
                subject=subject, proposal=proposal, status='failed',
                error_message=str(exc)[:1000],
                metadata=log_metadata,
            )
            logger.exception(
                'Failed to send %s for proposal %s', template_key, proposal.pk if proposal else 'standalone',
            )
            return False

    @classmethod
    def send_branded_email(
        cls, proposal, recipient_email, subject, greeting,
        sections, footer='', attachments=None,
    ):
        """Send a user-composed branded email (generic, no activity logging)."""
        return cls._send_composed_email(
            'branded_email', proposal, recipient_email, subject,
            greeting, sections, footer, attachments,
        )

    @classmethod
    def send_standalone_branded_email(
        cls, recipient_email, subject, greeting,
        sections, footer='', attachments=None,
    ):
        """Send a standalone branded email not tied to any proposal."""
        return cls._send_composed_email(
            'branded_email', None, recipient_email, subject,
            greeting, sections, footer, attachments,
        )

    @classmethod
    def send_proposal_email(
        cls, proposal, recipient_email, subject, greeting,
        sections, footer='', attachments=None,
    ):
        """Send a proposal-specific email and register it as a proposal activity."""
        sent = cls._send_composed_email(
            'proposal_email', proposal, recipient_email, subject,
            greeting, sections, footer, attachments,
        )
        if sent:
            from content.models import ProposalChangeLog
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type=ProposalChangeLog.ChangeType.EMAIL_SENT,
                actor_type=ProposalChangeLog.ActorType.SELLER,
                description=f'Correo enviado a {recipient_email}: {subject}',
            )
            proposal.last_activity_at = timezone.now()
            proposal.save(update_fields=['last_activity_at'])
        return sent
