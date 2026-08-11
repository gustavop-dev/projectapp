"""API tests for silencing an expected income's payment-calendar notices."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail

from content.models import AccountingChangeLog, IncomeRecord
from content.utils import today_bogota

pytestmark = pytest.mark.django_db


def make_expected(**overrides):
    fields = {
        'concept': 'Kore - Hosting julio',
        'kind': IncomeRecord.Kind.EXPECTED,
        'period_date': date(2026, 7, 1),
        'total_amount': Decimal('1000000.00'),
    }
    fields.update(overrides)
    return IncomeRecord.objects.create(**fields)


def url(record):
    return f'/api/accounting/incomes/{record.pk}/mute/'


class TestMuting:
    def test_mutes_indefinitely(self, super_client):
        record = make_expected()
        response = super_client.post(url(record), {'muted': True}, format='json')
        assert response.status_code == 200
        assert response.data['reminders_muted'] is True
        assert response.data['reminders_muted_until'] is None
        record.refresh_from_db()
        assert record.reminders_muted is True

    def test_mutes_until_a_date(self, super_client):
        record = make_expected()
        resume = today_bogota() + timedelta(days=50)
        response = super_client.post(
            url(record), {'muted': True, 'until': resume.isoformat()}, format='json',
        )
        assert response.status_code == 200
        record.refresh_from_db()
        assert record.reminders_muted_until == resume

    def test_unmuting_clears_the_resume_date(self, super_client):
        record = make_expected(
            reminders_muted=True,
            reminders_muted_until=today_bogota() + timedelta(days=10),
        )
        response = super_client.post(url(record), {'muted': False}, format='json')
        assert response.status_code == 200
        record.refresh_from_db()
        assert record.reminders_muted is False
        assert record.reminders_muted_until is None


class TestValidation:
    def test_a_resume_date_of_today_is_rejected(self, super_client):
        record = make_expected()
        response = super_client.post(
            url(record),
            {'muted': True, 'until': today_bogota().isoformat()},
            format='json',
        )
        assert response.status_code == 400
        assert 'until' in response.data

    def test_only_an_expected_income_can_be_muted(self, super_client):
        record = make_expected(kind=IncomeRecord.Kind.LIQUID)
        response = super_client.post(url(record), {'muted': True}, format='json')
        assert response.status_code == 400

    def test_a_missing_income_is_a_404(self, super_client):
        response = super_client.post(
            '/api/accounting/incomes/999999/mute/', {'muted': True}, format='json',
        )
        assert response.status_code == 404

    def test_a_staff_non_superuser_is_rejected(self, admin_client):
        record = make_expected()
        response = admin_client.post(url(record), {'muted': True}, format='json')
        assert response.status_code == 403

    def test_the_generic_update_endpoint_cannot_mute(self, super_client):
        # The mute fields are read-only on the write serializer on purpose:
        # that path notifies, and silencing a receivable must never email.
        record = make_expected()
        super_client.patch(
            f'/api/accounting/incomes/{record.pk}/update/',
            {'reminders_muted': True},
            format='json',
        )
        record.refresh_from_db()
        assert record.reminders_muted is False


class TestAuditedButQuiet:
    def test_muting_is_recorded_in_the_change_log(self, super_client):
        record = make_expected()
        super_client.post(url(record), {'muted': True}, format='json')
        log = AccountingChangeLog.objects.filter(
            entity_type=AccountingChangeLog.EntityType.INCOME,
            object_id=record.pk,
        ).latest('created_at')
        labels = {change['label']: change for change in log.changes}
        assert labels['Avisos silenciados']['new'] == 'Sí'

    def test_muting_sends_no_email(self, super_client):
        # The whole point of the calendar is less noise: silencing one income
        # must not generate a notification of its own.
        record = make_expected()
        super_client.post(url(record), {'muted': True}, format='json')
        assert mail.outbox == []
