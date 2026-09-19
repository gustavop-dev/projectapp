from datetime import timedelta

from django.utils import timezone
from huey import crontab
from huey.contrib.djhuey import periodic_task

from .models import Delivery, Report

CLEANUP_BATCH_SIZE = 500
MAX_CLEANUP_BATCHES = 4


def delete_in_batches(queryset):
    """Bound each transaction and the work done in one periodic invocation."""
    for _ in range(MAX_CLEANUP_BATCHES):
        ids = list(queryset.order_by('pk').values_list('pk', flat=True)[:CLEANUP_BATCH_SIZE])
        if not ids:
            break
        queryset.filter(pk__in=ids).delete()


@periodic_task(crontab(hour='5', minute='45'))
def cleanup_monitoring_reports():
    cutoff = timezone.now() - timedelta(days=90)
    delete_in_batches(Report.objects.filter(observed_at__lt=cutoff))
    # Keep receipts for cases and reports: historical retries stay idempotent.
    delete_in_batches(Delivery.objects.filter(kind='heartbeat', received_at__lt=cutoff))
