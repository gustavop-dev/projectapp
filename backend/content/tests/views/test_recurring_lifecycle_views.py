"""Focused API coverage for recurring-payment lifecycle row actions."""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core import mail

from content.models import AccountingChangeLog, RecurringCategory, RecurringPayment
from content.services import accounting_service
from content.utils import today_bogota


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mute_accounting_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


def make_recurring(**overrides):
    fields = {
        'name': 'Figma equipo',
        'price': Decimal('270000.00'),
        'currency': RecurringPayment.Currency.COP,
        'payment_method': RecurringPayment.PaymentMethod.CREDIT_CARD,
        'frequency': RecurringPayment.Frequency.QUARTERLY,
        'billing_day': 17,
        'cycle_anchor_date': date(2026, 1, 17),
        'cost_type': RecurringPayment.CostType.VARIABLE,
        'notes': 'Contrato anterior',
    }
    fields.update(overrides)
    return RecurringPayment.objects.create(**fields)


class TestDuplicateDraft:
    def test_returns_a_create_prefill_without_writing(self, super_client):
        category = RecurringCategory.objects.create(name='Diseño')
        payment = make_recurring(category=category)

        response = super_client.get(
            f'/api/accounting/recurring/{payment.pk}/duplicate-draft/',
        )

        assert response.status_code == 200
        assert RecurringPayment.objects.count() == 1
        expected_prefill = {
            'name': 'Figma equipo',
            'price': '270000.00',
            'currency': RecurringPayment.Currency.COP,
            'payment_method': RecurringPayment.PaymentMethod.CREDIT_CARD,
            'frequency': RecurringPayment.Frequency.QUARTERLY,
            'billing_day': 17,
            'category': category.pk,
            'cost_type': RecurringPayment.CostType.VARIABLE,
            'notes': '',
            'is_active': True,
        }
        assert {
            field: response.data[field] for field in expected_prefill
        } == expected_prefill
        assert {
            'reminder_count', 'reminder_last_sent_at', 'is_archived',
        }.isdisjoint(response.data)

    def test_recalculates_the_reference_from_the_next_occurrence(self, super_client):
        payment = make_recurring(cycle_anchor_date=date(2025, 1, 31))
        fixed_today = date(2026, 8, 27)

        with patch(
            'content.services.accounting_recurring_service.today_bogota',
            return_value=fixed_today,
        ):
            response = super_client.get(
                f'/api/accounting/recurring/{payment.pk}/duplicate-draft/',
            )

        assert response.data['cycle_anchor_date'] == '2026-10-31'

    def test_requires_an_anchor_when_the_original_has_no_schedule(self, super_client):
        payment = make_recurring(cycle_anchor_date=None)

        response = super_client.get(
            f'/api/accounting/recurring/{payment.pk}/duplicate-draft/',
        )

        assert response.data['cycle_anchor_date'] is None
        assert response.data['schedule_requires_anchor'] is True


class TestArchiveScope:
    def test_current_scope_excludes_archived_rows(self, super_client):
        make_recurring(name='Vigente')
        make_recurring(name='Archivado', is_active=False, is_archived=True)

        response = super_client.get('/api/accounting/recurring/')

        assert [row['name'] for row in response.data['results']] == ['Vigente']

    def test_archived_scope_has_zero_budget_total(self, super_client):
        make_recurring(is_active=False, is_archived=True)

        response = super_client.get(
            '/api/accounting/recurring/?archive_scope=archived',
        )

        assert response.data['meta']['monthly_cop_total'] == '0.00'

    def test_inactive_rows_stay_out_of_the_current_budget(self, super_client):
        make_recurring(
            name='Activo', price=Decimal('300000.00'),
            frequency=RecurringPayment.Frequency.MONTHLY,
            is_active=True,
        )
        make_recurring(
            name='Pausado', price=Decimal('900000.00'),
            frequency=RecurringPayment.Frequency.MONTHLY,
            is_active=False,
        )

        response = super_client.get('/api/accounting/recurring/')

        assert response.data['meta']['monthly_cop_total'] == '300000.00'

    def test_export_respects_the_archived_scope(self, super_client):
        make_recurring(name='Vigente')
        make_recurring(name='Cancelado', is_active=False, is_archived=True)

        response = super_client.get(
            '/api/accounting/export/?section=recurring&archive_scope=archived',
        )

        content = response.content.decode('utf-8-sig')
        assert 'Cancelado' in content
        assert 'Vigente' not in content


class TestSingleLifecycle:
    def test_archiving_deactivates_and_audits(self, super_client):
        payment = make_recurring(
            is_active=True,
            reminder_target_date=date(2026, 10, 17),
            reminder_last_sent_at=date(2026, 10, 2),
        )

        response = super_client.post(
            f'/api/accounting/recurring/{payment.pk}/archive/', {}, format='json',
        )

        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.is_archived is True
        assert payment.is_active is False
        assert payment.reminder_target_date == date(2026, 10, 17)
        assert payment.reminder_last_sent_at == date(2026, 10, 2)
        assert AccountingChangeLog.objects.filter(
            entity_type=AccountingChangeLog.EntityType.RECURRING,
            object_id=payment.pk,
        ).exists()

    def test_restoring_keeps_the_payment_inactive(self, super_client):
        payment = make_recurring(is_active=False, is_archived=True)

        response = super_client.post(
            f'/api/accounting/recurring/{payment.pk}/restore/', {}, format='json',
        )

        assert response.status_code == 200
        assert response.data['is_archived'] is False
        assert response.data['is_active'] is False

    def test_archived_payment_cannot_be_activated(self, super_client):
        payment = make_recurring(is_active=False, is_archived=True)

        response = super_client.post(
            f'/api/accounting/recurring/{payment.pk}/state/',
            {'is_active': True},
            format='json',
        )

        assert response.status_code == 409
        assert response.data['code'] == 'recurring_archived'

    def test_current_payment_cannot_be_hard_deleted(self, super_client):
        payment = make_recurring()

        response = super_client.delete(
            f'/api/accounting/recurring/{payment.pk}/delete/',
        )

        assert response.status_code == 409
        assert RecurringPayment.objects.filter(pk=payment.pk).exists()

    def test_archived_payment_can_be_hard_deleted(self, super_client):
        payment = make_recurring(is_active=False, is_archived=True)

        response = super_client.delete(
            f'/api/accounting/recurring/{payment.pk}/delete/',
        )

        assert response.status_code == 204
        assert not RecurringPayment.objects.filter(pk=payment.pk).exists()


class TestReminderMute:
    def test_mutes_until_a_future_date_without_email(self, super_client):
        payment = make_recurring()
        resume = today_bogota() + timedelta(days=30)

        response = super_client.post(
            f'/api/accounting/recurring/{payment.pk}/reminders/mute/',
            {'muted': True, 'until': resume.isoformat()},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['reminders_effectively_muted'] is True
        assert mail.outbox == []

    def test_archived_payment_rejects_mute_changes(self, super_client):
        payment = make_recurring(is_active=False, is_archived=True)

        response = super_client.post(
            f'/api/accounting/recurring/{payment.pk}/reminders/mute/',
            {'muted': True},
            format='json',
        )

        assert response.status_code == 409


class TestBulkLifecycle:
    @pytest.mark.parametrize(
        ('action', 'expected_active', 'expected_archived'),
        [
            ('activate', True, False),
            ('deactivate', False, False),
            ('archive', False, True),
        ],
    )
    def test_applies_the_requested_action_atomically(
        self, super_client, action, expected_active, expected_archived,
    ):
        payment = make_recurring(is_active=action != 'activate')

        response = super_client.post(
            '/api/accounting/recurring/bulk-action/',
            {'recurring_ids': [payment.pk], 'action': action},
            format='json',
        )

        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.is_active is expected_active
        assert payment.is_archived is expected_archived

    def test_missing_row_rolls_back_the_complete_selection(self, super_client):
        payment = make_recurring(is_active=True)

        response = super_client.post(
            '/api/accounting/recurring/bulk-action/',
            {'recurring_ids': [payment.pk, 999999], 'action': 'deactivate'},
            format='json',
        )

        assert response.status_code == 409
        payment.refresh_from_db()
        assert payment.is_active is True

    def test_archived_conflict_rolls_back_activation(self, super_client):
        current = make_recurring(name='Pausado', is_active=False)
        archived = make_recurring(
            name='Archivado', is_active=False, is_archived=True,
        )

        response = super_client.post(
            '/api/accounting/recurring/bulk-action/',
            {'recurring_ids': [current.pk, archived.pk], 'action': 'activate'},
            format='json',
        )

        assert response.status_code == 409
        current.refresh_from_db()
        assert current.is_active is False
