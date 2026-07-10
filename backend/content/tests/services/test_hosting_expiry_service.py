"""Tests for the hosting expiry notice cadence (15/7 days, then every 5)."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from content.models import AccountingSettings, EmailLog, HostingRecord
from content.services.hosting_expiry_service import (
    TEMPLATE_KEY,
    run_hosting_expiry_notices,
)

pytestmark = pytest.mark.django_db

TODAY = date(2026, 7, 10)


@pytest.fixture(autouse=True)
def _recipients(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    config = AccountingSettings.load()
    config.notification_recipients = ['team@projectapp.co']
    config.save()
    return config


def make_hosting(days_left=15, **overrides):
    defaults = {
        'client_name': 'German - Kore',
        'domain_url': 'https://korehealths.com/',
        'monthly_value': Decimal('91667.00'),
        'payment_modality': 'semiannual',
        'payment_per_cycle': Decimal('550002.00'),
        'valid_from': TODAY - timedelta(days=180),
        'valid_to': TODAY + timedelta(days=days_left),
        'is_active': True,
    }
    defaults.update(overrides)
    return HostingRecord.objects.create(**defaults)


def sent_count():
    return EmailLog.objects.filter(
        template_key=TEMPLATE_KEY, status=EmailLog.Status.SENT,
    ).count()


class TestCadence:
    def test_first_notice_at_15_days(self):
        record = make_hosting(days_left=15)
        assert run_hosting_expiry_notices(TODAY) == 1
        record.refresh_from_db()
        assert record.expiry_notice_count == 1
        assert record.expiry_notice_last_sent_at == TODAY
        assert record.expiry_notice_target == record.valid_to
        assert sent_count() == 1

    def test_not_due_beyond_15_days(self):
        make_hosting(days_left=16)
        assert run_hosting_expiry_notices(TODAY) == 0

    def test_catch_up_first_notice_inside_window(self):
        make_hosting(days_left=3)
        assert run_hosting_expiry_notices(TODAY) == 1

    def test_no_repeat_between_15_and_7_days(self):
        record = make_hosting(days_left=15)
        run_hosting_expiry_notices(TODAY)
        # 5 days later there are 10 days left: still silent.
        record.refresh_from_db()
        assert run_hosting_expiry_notices(TODAY + timedelta(days=5)) == 0

    def test_second_notice_when_crossing_7_days(self):
        record = make_hosting(days_left=15)
        run_hosting_expiry_notices(TODAY)
        assert run_hosting_expiry_notices(TODAY + timedelta(days=8)) == 1
        record.refresh_from_db()
        assert record.expiry_notice_count == 2

    def test_repeats_every_5_days_after_7_day_notice(self):
        make_hosting(days_left=7)
        run_hosting_expiry_notices(TODAY)
        assert run_hosting_expiry_notices(TODAY + timedelta(days=4)) == 0
        assert run_hosting_expiry_notices(TODAY + timedelta(days=5)) == 1

    def test_continues_past_expiry(self):
        record = make_hosting(days_left=-3)
        assert run_hosting_expiry_notices(TODAY) == 1
        assert run_hosting_expiry_notices(TODAY + timedelta(days=5)) == 1
        record.refresh_from_db()
        assert record.expiry_notice_count == 2

    def test_same_day_rerun_is_idempotent(self):
        make_hosting(days_left=15)
        run_hosting_expiry_notices(TODAY)
        assert run_hosting_expiry_notices(TODAY) == 0
        assert sent_count() == 1


class TestStopsAndRearm:
    def test_billing_requested_silences(self):
        make_hosting(days_left=5, billing_requested_at=None)
        HostingRecord.objects.update(
            billing_requested_at=TODAY - timedelta(days=1),
        )
        assert run_hosting_expiry_notices(TODAY) == 0

    def test_renewal_rearms_and_clears_billing_request(self):
        record = make_hosting(days_left=5)
        run_hosting_expiry_notices(TODAY)
        record.refresh_from_db()
        # Renewal: valid_to moves 6 months; billing was requested meanwhile.
        HostingRecord.objects.filter(pk=record.pk).update(
            valid_to=record.valid_to + timedelta(days=180),
            billing_requested_at=TODAY,
        )
        assert run_hosting_expiry_notices(TODAY + timedelta(days=1)) == 0
        record.refresh_from_db()
        assert record.expiry_notice_count == 0
        assert record.expiry_notice_last_sent_at is None
        assert record.billing_requested_at is None
        assert record.expiry_notice_target == record.valid_to

    def test_inactive_and_null_valid_to_are_skipped(self):
        make_hosting(days_left=5, is_active=False)
        make_hosting(days_left=5, valid_to=None, client_name='Sin vigencia')
        assert run_hosting_expiry_notices(TODAY) == 0

    def test_disabled_flag_gates_everything(self):
        make_hosting(days_left=5)
        config = AccountingSettings.load()
        config.hosting_expiry_reminder_enabled = False
        config.save()
        assert run_hosting_expiry_notices(TODAY) == 0

    def test_no_recipients_retries_without_state_update(self):
        record = make_hosting(days_left=5)
        config = AccountingSettings.load()
        config.notification_recipients = []
        config.save()
        assert run_hosting_expiry_notices(TODAY) == 0
        record.refresh_from_db()
        assert record.expiry_notice_count == 0
        assert record.expiry_notice_last_sent_at is None

    def test_email_log_metadata(self):
        record = make_hosting(days_left=7)
        run_hosting_expiry_notices(TODAY)
        log = EmailLog.objects.get(template_key=TEMPLATE_KEY)
        assert log.metadata['hosting_id'] == record.pk
        assert log.metadata['days_left'] == 7
        assert log.metadata['notice_number'] == 1
