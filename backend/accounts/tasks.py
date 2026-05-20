"""
Automatic recurring billing tasks for hosting subscriptions.

auto_charge_due_subscriptions runs daily and charges every open payment past
its due date using the subscription's stored Wompi payment source. Failed
charges are retried a fixed number of times before the subscription is
suspended and the client + admins are notified.
"""

import logging

from huey import crontab
from huey.contrib.djhuey import periodic_task

logger = logging.getLogger(__name__)

MAX_CHARGE_ATTEMPTS = 3
RETRY_INTERVAL_DAYS = 2


@periodic_task(crontab(hour='6', minute='0'))
def auto_charge_due_subscriptions():
    """
    Daily: charge open payments whose billing period has expired, using each
    subscription's stored card. Reschedules retries on failure and suspends
    the subscription once the attempt limit is exhausted.
    """
    from datetime import timedelta

    from django.db.models import Q
    from django.utils import timezone

    from accounts.models import HostingSubscription, Payment, PaymentHistory
    from accounts.views import _charge_payment_with_source

    today = timezone.now().date()

    due = Payment.objects.select_related('subscription__project__client').filter(
        status__in=[Payment.STATUS_PENDING, Payment.STATUS_OVERDUE, Payment.STATUS_FAILED],
        is_archived=False,
        due_date__lte=today,
        charge_attempts__lt=MAX_CHARGE_ATTEMPTS,
        subscription__status=HostingSubscription.STATUS_ACTIVE,
    ).filter(
        Q(next_retry_at__isnull=True) | Q(next_retry_at__lte=today),
    ).exclude(
        subscription__wompi_payment_source_id='',
    )

    charged = 0
    failed = 0
    for payment in due:
        payment.charge_attempts += 1
        try:
            _charge_payment_with_source(payment, PaymentHistory.SOURCE_SYSTEM)
        except Exception as e:
            logger.error('Auto-charge error for payment %s: %s', payment.id, e)
            payment.status = Payment.STATUS_FAILED
            payment.last_charge_error = str(e)[:300]

        if payment.status in (Payment.STATUS_PAID, Payment.STATUS_PROCESSING):
            payment.next_retry_at = None
            payment.save(update_fields=['charge_attempts', 'next_retry_at'])
            charged += 1
            continue

        failed += 1
        if payment.charge_attempts >= MAX_CHARGE_ATTEMPTS:
            payment.next_retry_at = None
            payment.save(update_fields=[
                'charge_attempts', 'next_retry_at', 'status', 'last_charge_error',
            ])
            _suspend_subscription_on_failure(payment)
        else:
            payment.next_retry_at = today + timedelta(days=RETRY_INTERVAL_DAYS)
            payment.save(update_fields=[
                'charge_attempts', 'next_retry_at', 'status', 'last_charge_error',
            ])
            _notify_charge_retry(payment)

    logger.info('auto_charge_due_subscriptions: %s charged, %s failed', charged, failed)
    return {'charged': charged, 'failed': failed}


def _suspend_subscription_on_failure(payment):
    """Suspend the subscription after the charge attempt limit is exhausted."""
    from accounts.models import HostingSubscription, Notification
    from accounts.services.notifications import notify, notify_project_admins

    sub = payment.subscription
    sub.status = HostingSubscription.STATUS_SUSPENDED
    sub.save(update_fields=['status', 'updated_at'])

    project = sub.project
    try:
        notify(
            user=project.client,
            type=Notification.TYPE_GENERAL,
            title='Suscripción suspendida',
            message=(
                f'No pudimos cobrar el hosting de "{project.name}" después de '
                f'{payment.charge_attempts} intentos. Tu suscripción quedó suspendida; '
                f'actualiza tu tarjeta para reactivarla.'
            ),
            project=project,
            related_object_type='payment',
            related_object_id=payment.id,
        )
        notify_project_admins(
            project, Notification.TYPE_GENERAL,
            f'Suscripción suspendida: {project.name}',
            message=(
                f'El cobro automático del hosting de "{project.name}" falló '
                f'{payment.charge_attempts} veces. La suscripción quedó suspendida.'
            ),
            related_object_type='payment', related_object_id=payment.id,
        )
    except Exception:
        logger.warning('Failed to send suspension notifications for payment %s', payment.id)


def _notify_charge_retry(payment):
    """Tell the client an automatic charge failed and when it will be retried."""
    from accounts.models import Notification
    from accounts.services.notifications import notify

    project = payment.subscription.project
    try:
        notify(
            user=project.client,
            type=Notification.TYPE_GENERAL,
            title='Cobro de hosting fallido',
            message=(
                f'No pudimos cobrar el hosting de "{project.name}". '
                f'Reintentaremos el {payment.next_retry_at}. '
                f'Verifica que tu tarjeta tenga fondos o actualízala.'
            ),
            project=project,
            related_object_type='payment',
            related_object_id=payment.id,
        )
    except Exception:
        logger.warning('Failed to send retry notification for payment %s', payment.id)
