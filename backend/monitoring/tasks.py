from datetime import timedelta

from django.utils import timezone
from huey import crontab
from huey.contrib.djhuey import periodic_task

from .models import Delivery, Report


@periodic_task(crontab(hour='5', minute='45'))
def cleanup_monitoring_reports():
    cutoff = timezone.now() - timedelta(days=90)
    Report.objects.filter(observed_at__lt=cutoff).delete()
    # Keep receipts for cases and reports: historical retries stay idempotent.
    Delivery.objects.filter(kind='heartbeat', received_at__lt=cutoff).delete()
