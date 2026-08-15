"""Periodic statement reminder for the accounting module.

Business rule: once a month closes, each active catalog card (with
``statements_since`` set) must have that month's statement PROCESSED and
its bank PDF attached. A daily Huey task (9:05 Bogotá, right after the
card-debt reminder) calls `run_statement_reminder`; while anything is
pending, an email goes out every REALERT_EVERY_DAYS days.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from content.services import email_log_service
from content.services.notification_recipient_service import (
    active_recipient_emails,
)
from content.utils import today_bogota

logger = logging.getLogger(__name__)

TEMPLATE_KEY = 'accounting_statement_reminder'
REALERT_EVERY_DAYS = 8


def previous_month(today):
    """First day of the month before `today`."""
    first = today.replace(day=1)
    return (
        first.replace(year=first.year - 1, month=12)
        if first.month == 1
        else first.replace(month=first.month - 1)
    )


def pending_statements(today):
    """Cards whose previous-month statement is missing, draft or PDF-less.

    Returns [{'card_name', 'card_id', 'statement_id', 'period', 'reason'}]
    limited to active catalog cards with statements available since before
    the target month. The ids are what the send log links the reminder to;
    `statement_id` is None when the statement was never registered.
    """
    from content.models import CreditCard, CreditCardStatement

    target = previous_month(today)
    Status = CreditCardStatement.Status
    statements = {
        s.card_name: s
        for s in CreditCardStatement.objects.filter(period_date=target)
    }
    pending = []
    cards = CreditCard.objects.filter(
        is_active=True, statements_since__isnull=False,
        statements_since__lte=target,
    )
    for card in cards:
        statement = statements.get(card.name)
        if statement is None:
            reason = 'Sin extracto registrado'
        elif statement.status != Status.PROCESSED:
            reason = 'Extracto en borrador (sin procesar)'
        elif not statement.pdf_file:
            reason = 'Falta adjuntar el PDF del extracto'
        else:
            continue
        pending.append({
            'card_name': card.name,
            'card_id': card.pk,
            'statement_id': statement.pk if statement else None,
            'period': target,
            'reason': reason,
        })
    return pending


def run_statement_reminder(today=None):
    """Send the statement reminder if the previous month is incomplete.

    Returns True when an email was sent. Never raises.
    """
    from content.models import AccountingSettings, EmailLog

    today = today or today_bogota()
    config = AccountingSettings.load()
    if not (config.notifications_enabled and config.statement_reminder_enabled):
        return False

    if (
        config.statement_reminder_last_sent_at
        and (today - config.statement_reminder_last_sent_at).days
        < REALERT_EVERY_DAYS
    ):
        return False

    pending = pending_statements(today)
    if not pending:
        return False

    recipients = active_recipient_emails()
    if not recipients:
        # Do not mark as notified: retry daily until there are recipients.
        logger.warning(
            'Statement reminder due (%s pending) but no recipients configured.',
            len(pending),
        )
        return False

    from content.serializers.accounting import month_label

    base_url = getattr(settings, 'FRONTEND_BASE_URL', '').rstrip('/')
    context = {
        'pending': [
            {**item, 'period_label': month_label(item['period'])}
            for item in pending
        ],
        'period_label': month_label(pending[0]['period']),
        'panel_url': f'{base_url}/panel/accounting/statements',
    }
    subject = '[Contabilidad] Recordatorio: extracto de tarjeta pendiente'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'team@projectapp.co')
    metadata = {
        'period': pending[0]['period'].isoformat(),
        'pending': [
            {'card_name': item['card_name'], 'reason': item['reason']}
            for item in pending
        ],
    }
    targets = [
        ('credit_card', item['card_id'], item['card_name'])
        for item in pending
    ] + [
        ('statement', item['statement_id'], item['card_name'])
        for item in pending if item['statement_id']
    ]
    text_body = html_body = ''

    try:
        text_body = render_to_string(
            'emails/accounting_statement_reminder.txt', context,
        )
        html_body = render_to_string(
            'emails/accounting_statement_reminder.html', context,
        )
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=recipients,
        )
        email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=False)
    except Exception as exc:
        logger.warning('Failed to send statement reminder: %s', exc)
        email_log_service.record_send(
            template_key=TEMPLATE_KEY,
            recipients=recipients,
            subject=subject,
            status=EmailLog.Status.FAILED,
            error_message=str(exc),
            metadata=metadata,
            targets=targets,
            html_body=html_body,
            text_body=text_body,
        )
        return False

    email_log_service.record_send(
        template_key=TEMPLATE_KEY,
        recipients=recipients,
        subject=subject,
        status=EmailLog.Status.SENT,
        metadata=metadata,
        targets=targets,
        html_body=html_body,
        text_body=text_body,
    )

    # System state, not a user change: update directly (no audit trail).
    AccountingSettings.objects.filter(pk=1).update(
        statement_reminder_last_sent_at=today,
    )
    logger.info(
        'Sent statement reminder (%s pending) to %s',
        len(pending), ', '.join(recipients),
    )
    return True
