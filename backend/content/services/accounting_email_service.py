"""Email notifications for accounting module changes.

Every create/update/delete on an accounting record produces one email to
the recipients configured in AccountingSettings (Gustavo's and Carlos's
inboxes). Best-effort: never raises; every attempt is recorded in EmailLog.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

TEMPLATE_KEY = 'accounting_change'

# Panel subview per entity, used for the email CTA link.
_PANEL_PATHS = {
    'income': '/panel/accounting/incomes',
    'expense': '/panel/accounting/expenses',
    'hosting': '/panel/accounting/hostings',
    'pocket': '/panel/accounting/pocket',
    'recurring': '/panel/accounting/recurring',
    'ads': '/panel/accounting/ads',
    'card_snapshot': '/panel/accounting',
    'settings': '/panel/accounting/settings',
}


def build_accounting_change_context(change_log):
    """Build the template context for an accounting-change email."""
    base_url = getattr(settings, 'FRONTEND_BASE_URL', '').rstrip('/')
    path = _PANEL_PATHS.get(change_log.entity_type, '/panel/accounting')
    return {
        'action': change_log.action,
        'action_label': change_log.get_action_display(),
        'entity_label': change_log.get_entity_type_display(),
        'object_repr': change_log.object_repr,
        'actor_name': change_log.actor_username or 'Sistema',
        'changes': change_log.changes,
        'is_created': change_log.action == 'created',
        'is_updated': change_log.action == 'updated',
        'is_deleted': change_log.action == 'deleted',
        'occurred_at': change_log.created_at,
        'panel_url': f'{base_url}{path}',
        'history_url': f'{base_url}/panel/accounting/history',
    }


def send_accounting_change_email(change_log_id):
    """
    Render and send the change notification to the configured recipients.
    Returns True if the email was sent, False otherwise. Never raises.
    """
    from content.models import AccountingChangeLog, AccountingSettings, EmailLog

    try:
        change_log = AccountingChangeLog.objects.get(id=change_log_id)
    except AccountingChangeLog.DoesNotExist:
        logger.warning(
            'AccountingChangeLog %s not found for notification email',
            change_log_id,
        )
        return False

    config = AccountingSettings.load()
    if not config.notifications_enabled:
        logger.info(
            'Accounting notifications disabled; skipping change_log %s',
            change_log_id,
        )
        return False

    recipients = [r for r in (config.notification_recipients or []) if r]
    if not recipients:
        logger.warning(
            'No accounting notification recipients configured; '
            'skipping change_log %s',
            change_log_id,
        )
        return False

    context = build_accounting_change_context(change_log)
    subject = (
        f'[Contabilidad] {context["entity_label"]} '
        f'{context["action_label"].lower()}: {context["object_repr"]}'
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'team@projectapp.co')
    metadata = {
        'change_log_id': change_log.id,
        'entity_type': change_log.entity_type,
        'action': change_log.action,
    }

    try:
        text_body = render_to_string('emails/accounting_change.txt', context)
        html_body = render_to_string('emails/accounting_change.html', context)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=recipients,
        )
        email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=False)
    except Exception as exc:
        logger.warning(
            'Failed to send accounting change email for change_log %s: %s',
            change_log_id, exc,
        )
        for recipient in recipients:
            EmailLog.objects.create(
                template_key=TEMPLATE_KEY,
                recipient=recipient,
                subject=subject,
                status=EmailLog.Status.FAILED,
                error_message=str(exc),
                metadata=metadata,
            )
        return False

    for recipient in recipients:
        EmailLog.objects.create(
            template_key=TEMPLATE_KEY,
            recipient=recipient,
            subject=subject,
            status=EmailLog.Status.SENT,
            metadata=metadata,
        )
    logger.info(
        'Sent accounting change email (change_log %s) to %s',
        change_log_id, ', '.join(recipients),
    )
    return True
