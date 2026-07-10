"""Hosting expiry notices for the accounting module.

Business rule: active hostings with a `valid_to` (vigencia) alert the
internal recipients 15 days before expiry, again when crossing 7 days,
and then every 5 days (continuing past expiry) until the cuenta de cobro
is sent to the client (`billing_requested_at`, set by
hosting_billing_service) or the hosting is deactivated.

Cadence state lives on each HostingRecord. `expiry_notice_target`
snapshots the valid_to the cadence is armed against: any change of
valid_to (renewal or correction) re-arms the cadence automatically on
the next daily run.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import F, Q
from django.template.loader import render_to_string

from content.utils import today_bogota

logger = logging.getLogger(__name__)

TEMPLATE_KEY = 'hosting_expiry_notice'
FIRST_NOTICE_DAYS = 15
SECOND_NOTICE_DAYS = 7
REPEAT_EVERY_DAYS = 5


def run_hosting_expiry_notices(today=None):
    """Send due expiry notices. Returns the number of hostings notified.

    Never raises: per-record failures are logged and skipped.
    """
    from content.models import AccountingSettings, HostingRecord

    today = today or today_bogota()
    config = AccountingSettings.load()
    if not (config.notifications_enabled and config.hosting_expiry_reminder_enabled):
        return 0

    # Re-arm renewed/corrected records first (even those far from expiry).
    HostingRecord.objects.filter(
        Q(expiry_notice_target__isnull=False) & ~Q(expiry_notice_target=F('valid_to')),
    ).update(
        expiry_notice_target=F('valid_to'),
        expiry_notice_last_sent_at=None,
        expiry_notice_count=0,
        billing_requested_at=None,
    )

    recipients = [r for r in (config.notification_recipients or []) if r]

    sent = 0
    candidates = HostingRecord.objects.filter(
        is_active=True,
        valid_to__isnull=False,
        billing_requested_at__isnull=True,
    )
    for record in candidates:
        if not _is_due(record, today):
            continue
        if not recipients:
            # Do not update state: retry daily until recipients exist.
            logger.warning(
                'Hosting expiry notice due (%s) but no recipients configured.',
                record.client_name,
            )
            continue
        if _send_notice(record, today, recipients):
            sent += 1
    return sent


def _is_due(record, today):
    days_left = (record.valid_to - today).days
    if days_left > FIRST_NOTICE_DAYS:
        return False
    last_sent = record.expiry_notice_last_sent_at
    if last_sent is None:
        return True
    if days_left > SECOND_NOTICE_DAYS:
        # Between 15 and 7 days there is a single notice, no repeats.
        return False
    days_left_at_last_sent = (record.valid_to - last_sent).days
    if days_left_at_last_sent > SECOND_NOTICE_DAYS:
        # Crossing the 7-day threshold triggers the second notice.
        return True
    return (today - last_sent).days >= REPEAT_EVERY_DAYS


def _send_notice(record, today, recipients):
    from content.models import EmailLog, HostingRecord

    days_left = (record.valid_to - today).days
    notice_number = record.expiry_notice_count + 1
    base_url = getattr(settings, 'FRONTEND_BASE_URL', '').rstrip('/')
    context = {
        'record': record,
        'days_left': days_left,
        'is_expired': days_left < 0,
        'days_expired': abs(days_left),
        'notice_number': notice_number,
        'modality_label': record.get_payment_modality_display(),
        'panel_url': f'{base_url}/panel/accounting/hostings',
    }
    label = record.client_name or record.domain_url
    if days_left < 0:
        subject = f'[Contabilidad] Hosting de {label} vencido hace {abs(days_left)} días'
    else:
        subject = f'[Contabilidad] Hosting de {label} vence en {days_left} días'
    if notice_number > 1:
        subject += f' (aviso #{notice_number})'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'team@projectapp.co')
    metadata = {
        'hosting_id': record.pk,
        'valid_to': record.valid_to.isoformat(),
        'days_left': days_left,
        'notice_number': notice_number,
    }

    try:
        text_body = render_to_string('emails/hosting_expiry_notice.txt', context)
        html_body = render_to_string('emails/hosting_expiry_notice.html', context)
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
            'Failed to send hosting expiry notice for %s: %s', record.pk, exc,
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

    # System state, not a user change: update directly (no audit trail).
    HostingRecord.objects.filter(pk=record.pk).update(
        expiry_notice_target=record.valid_to,
        expiry_notice_last_sent_at=today,
        expiry_notice_count=F('expiry_notice_count') + 1,
    )
    logger.info(
        'Sent hosting expiry notice #%s for %s (%s days left)',
        notice_number, record.client_name, days_left,
    )
    return True
