"""Tests for the hosting expiry cadence (15/7 days, then every 5).

The cadence is unchanged; its delivery moved into the daily payment calendar,
so these drive `run_payment_calendar` and assert on the hosting state. Keeping
them pointed at the real entry point is the guarantee that absorbing the
notices into the digest did not quietly drop them.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core import mail

from accounts.models import Project
from content.models import (
    AccountingSettings,
    EmailLog,
    HostingRecord,
    NotificationRecipient,
)
from content.services.accounting_payment_calendar_service import (
    TEMPLATE_KEY,
    run_payment_calendar,
)

pytestmark = pytest.mark.django_db

TODAY = date(2026, 7, 10)
User = get_user_model()


@pytest.fixture(autouse=True)
def _recipients(settings):
    settings.MAILERS = {
        'default': {
            'BACKEND': 'django.core.mail.backends.locmem.EmailBackend',
        },
    }
    # Migration 0191 seeds two production inboxes into every test database.
    NotificationRecipient.objects.all().delete()
    NotificationRecipient.objects.create(email='team@projectapp.co')
    config = AccountingSettings.load()
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
        assert run_payment_calendar(TODAY) == 1
        record.refresh_from_db()
        assert record.expiry_notice_count == 1
        assert record.expiry_notice_last_sent_at == TODAY
        assert record.expiry_notice_target == record.valid_to
        assert sent_count() == 1

    def test_not_due_beyond_15_days(self):
        make_hosting(days_left=16)
        assert run_payment_calendar(TODAY) == 0

    def test_catch_up_first_notice_inside_window(self):
        make_hosting(days_left=3)
        assert run_payment_calendar(TODAY) == 1

    def test_no_repeat_between_15_and_7_days(self):
        record = make_hosting(days_left=15)
        run_payment_calendar(TODAY)
        # 5 days later there are 10 days left: still silent.
        record.refresh_from_db()
        assert run_payment_calendar(TODAY + timedelta(days=5)) == 0

    def test_second_notice_when_crossing_7_days(self):
        record = make_hosting(days_left=15)
        run_payment_calendar(TODAY)
        assert run_payment_calendar(TODAY + timedelta(days=8)) == 1
        record.refresh_from_db()
        assert record.expiry_notice_count == 2

    def test_repeats_every_5_days_after_7_day_notice(self):
        make_hosting(days_left=7)
        run_payment_calendar(TODAY)
        assert run_payment_calendar(TODAY + timedelta(days=4)) == 0
        assert run_payment_calendar(TODAY + timedelta(days=5)) == 1

    def test_continues_past_expiry(self):
        record = make_hosting(days_left=-3)
        assert run_payment_calendar(TODAY) == 1
        assert run_payment_calendar(TODAY + timedelta(days=5)) == 1
        record.refresh_from_db()
        assert record.expiry_notice_count == 2

    def test_same_day_rerun_is_idempotent(self):
        make_hosting(days_left=15)
        run_payment_calendar(TODAY)
        assert run_payment_calendar(TODAY) == 0
        assert sent_count() == 1


class TestStopsAndRearm:
    def test_billing_requested_silences(self):
        make_hosting(days_left=5, billing_requested_at=None)
        HostingRecord.objects.update(
            billing_requested_at=TODAY - timedelta(days=1),
        )
        assert run_payment_calendar(TODAY) == 0

    def test_renewal_rearms_and_clears_billing_request(self):
        record = make_hosting(days_left=5)
        run_payment_calendar(TODAY)
        record.refresh_from_db()
        # Renewal: valid_to moves 6 months; billing was requested meanwhile.
        HostingRecord.objects.filter(pk=record.pk).update(
            valid_to=record.valid_to + timedelta(days=180),
            billing_requested_at=TODAY,
        )
        assert run_payment_calendar(TODAY + timedelta(days=1)) == 0
        record.refresh_from_db()
        assert record.expiry_notice_count == 0
        assert record.expiry_notice_last_sent_at is None
        assert record.billing_requested_at is None
        assert record.expiry_notice_target == record.valid_to

    def test_inactive_and_null_valid_to_are_skipped(self):
        make_hosting(days_left=5, is_active=False)
        make_hosting(days_left=5, valid_to=None, client_name='Sin vigencia')
        assert run_payment_calendar(TODAY) == 0

    def test_legacy_unclassified_project_is_skipped(self):
        client = User.objects.create_user(
            username='legacy-hosting@example.com',
            email='legacy-hosting@example.com',
        )
        project = Project.objects.create(name='Hosting histórico', client=client)
        Project.objects.filter(pk=project.pk).update(
            status=Project.STATUS_ARCHIVED,
            current_state=None,
            state_review_required=True,
        )
        make_hosting(days_left=5, project=project)

        assert run_payment_calendar(TODAY) == 0

    def test_disabled_flag_gates_the_hosting_section(self):
        make_hosting(days_left=5)
        config = AccountingSettings.load()
        config.hosting_expiry_reminder_enabled = False
        config.save()
        assert run_payment_calendar(TODAY) == 0

    def test_no_recipients_retries_without_state_update(self):
        record = make_hosting(days_left=5)
        NotificationRecipient.objects.all().delete()
        assert run_payment_calendar(TODAY) == 0
        record.refresh_from_db()
        assert record.expiry_notice_count == 0
        assert record.expiry_notice_last_sent_at is None


class TestDigestContent:
    def test_email_log_names_the_hosting(self):
        record = make_hosting(days_left=7)
        run_payment_calendar(TODAY)
        log = EmailLog.objects.get(template_key=TEMPLATE_KEY)
        assert log.metadata['counts']['hostings'] == 1
        entry = log.metadata['hostings'][0]
        assert entry['id'] == record.pk
        assert entry['days_left'] == 7
        assert entry['notice_number'] == 1

    def test_body_formats_money_and_the_expiry_date(self):
        make_hosting(days_left=15)
        assert run_payment_calendar(TODAY) == 1
        body = mail.outbox[0].body
        assert '$550.002' in body
        assert 'Sáb, 25 jul 2026' in body
        assert '550002.00' not in body

    def test_subject_counts_what_is_coming(self):
        make_hosting(days_left=15)
        run_payment_calendar(TODAY)
        assert mail.outbox[0].subject == (
            '[Contabilidad] Calendario de cobros y pagos: 1 próximo'
        )
