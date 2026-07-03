"""Weekly card-debt reminder for the accounting module.

Business rule: every Friday the partners must register the week's
CardBalanceSnapshot. A daily Huey task (9:00 Bogotá) calls
`run_card_reminder`; if the current cycle's Friday has no snapshot with
`snapshot_date >= friday`, an email goes out, then re-alerts every 2
days until the snapshot is registered. A new Friday opens a new cycle.

A snapshot dated in the future also counts for the current cycle — it
is assumed intentional (registered ahead of time).
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from content.utils import today_bogota

logger = logging.getLogger(__name__)

TEMPLATE_KEY = 'accounting_card_reminder'
REALERT_EVERY_DAYS = 2


def cycle_friday(today):
    """Most recent Friday <= today (weekday: Monday=0 ... Friday=4)."""
    return today - timedelta(days=(today.weekday() - 4) % 7)


def run_card_reminder(today=None):
    """Send the card-debt reminder if this cycle still lacks a snapshot.

    Returns True when an email was sent. Never raises.
    """
    from content.models import AccountingSettings, CardBalanceSnapshot, EmailLog
    from content.services.accounting_service import latest_card_snapshots

    today = today or today_bogota()
    config = AccountingSettings.load()
    if not (config.notifications_enabled and config.card_reminder_enabled):
        return False

    friday = cycle_friday(today)
    if CardBalanceSnapshot.objects.filter(snapshot_date__gte=friday).exists():
        return False

    same_cycle = config.card_reminder_cycle_start == friday
    if (
        same_cycle
        and config.card_reminder_last_sent_at
        and (today - config.card_reminder_last_sent_at).days < REALERT_EVERY_DAYS
    ):
        return False

    recipients = [r for r in (config.notification_recipients or []) if r]
    if not recipients:
        # Do not mark the cycle as notified: retry daily until there are
        # recipients to alert.
        logger.warning(
            'Card-debt reminder due (cycle %s) but no recipients configured.',
            friday,
        )
        return False

    base_url = getattr(settings, 'FRONTEND_BASE_URL', '').rstrip('/')
    reminder_number = (today - friday).days // REALERT_EVERY_DAYS + 1
    context = {
        'reminder_number': reminder_number,
        'is_first': reminder_number == 1,
        'cycle_friday': friday,
        'days_since': (today - friday).days,
        'snapshots': latest_card_snapshots(),
        'panel_url': f'{base_url}/panel/accounting/cards',
    }
    subject = '[Contabilidad] Recordatorio: registra la deuda de tarjetas'
    if reminder_number > 1:
        subject += f' (recordatorio #{reminder_number})'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'team@projectapp.co')
    metadata = {
        'cycle_friday': friday.isoformat(),
        'reminder_number': reminder_number,
    }

    try:
        text_body = render_to_string(
            'emails/accounting_card_reminder.txt', context,
        )
        html_body = render_to_string(
            'emails/accounting_card_reminder.html', context,
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
        logger.warning('Failed to send card-debt reminder: %s', exc)
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

    # System state, not a user change: update directly (no audit trail).
    AccountingSettings.objects.filter(pk=1).update(
        card_reminder_cycle_start=friday,
        card_reminder_last_sent_at=today,
    )
    logger.info(
        'Sent card-debt reminder #%s (cycle %s) to %s',
        reminder_number, friday, ', '.join(recipients),
    )
    return True
