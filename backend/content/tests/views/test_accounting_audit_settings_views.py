"""API tests for the accounting change log and settings endpoints."""
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import AccountingChangeLog, RecurringPayment
from content.services import accounting_service


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


def seed_logs(count, **overrides):
    for index in range(count):
        defaults = {
            'entity_type': 'income',
            'object_id': index + 1,
            'object_repr': f'Ingreso {index + 1}',
            'action': 'created',
        }
        defaults.update(overrides)
        AccountingChangeLog.objects.create(**defaults)


@pytest.mark.django_db
class TestChangeLogEndpoint:
    def test_paginates_20_per_page(self, super_client):
        seed_logs(25)
        page_one = super_client.get('/api/accounting/change-logs/')
        assert page_one.data['count'] == 25
        assert page_one.data['num_pages'] == 2
        assert len(page_one.data['results']) == 20

        page_two = super_client.get('/api/accounting/change-logs/?page=2')
        assert len(page_two.data['results']) == 5
        assert page_two.data['page'] == 2

    def test_filters_by_entity_and_action(self, super_client):
        seed_logs(2, entity_type='income', action='created')
        seed_logs(1, entity_type='expense', action='deleted')
        response = super_client.get(
            '/api/accounting/change-logs/?entity_type=expense&action=deleted',
        )
        assert response.data['count'] == 1
        assert response.data['results'][0]['entity_type_label'] == 'Gasto'

    def test_filters_by_object_id(self, super_client):
        seed_logs(3)
        response = super_client.get(
            '/api/accounting/change-logs/?object_id=2',
        )
        assert response.data['count'] == 1

    def test_filters_by_actor_and_date_range(self, super_client):
        seed_logs(2)
        seed_logs(1, actor_username='gustavo', object_repr='Fila de Gustavo')
        response = super_client.get(
            '/api/accounting/change-logs/'
            '?actor=gus&date_from=2020-01-01&date_to=2030-01-01',
        )
        assert response.data['count'] == 1
        assert response.data['results'][0]['object_repr'] == 'Fila de Gustavo'

    def test_invalid_date_filter_returns_400(self, super_client):
        seed_logs(1)
        response = super_client.get(
            '/api/accounting/change-logs/?date_from=notadate',
        )
        assert response.status_code == 400

    def test_invalid_page_param_defaults_to_the_first_page(self, super_client):
        seed_logs(3)
        response = super_client.get('/api/accounting/change-logs/?page=abc')
        assert response.data['page'] == 1

    def test_requires_superuser(self, admin_client):
        assert admin_client.get(
            '/api/accounting/change-logs/',
        ).status_code == 403


@pytest.mark.django_db
class TestSettingsEndpoints:
    def test_get_returns_singleton_defaults(self, super_client):
        response = super_client.get('/api/accounting/settings/')
        assert response.status_code == 200
        assert response.data['notifications_enabled'] is True

    def test_recipients_are_not_part_of_the_settings_payload(self, super_client):
        """They live in their own catalog; two writable copies would drift."""
        response = super_client.get('/api/accounting/settings/')

        assert 'notification_recipients' not in response.data

    def test_update_frequency_and_audit_it(self, super_client):
        """PATCH persists the change and writes a settings audit row."""
        response = super_client.patch(
            '/api/accounting/settings/update/',
            {'overdue_reminder_frequency': 'weekly'},
            format='json',
        )
        assert response.status_code == 200, response.data
        assert response.data['overdue_reminder_frequency'] == 'weekly'
        log = AccountingChangeLog.objects.get(entity_type='settings')
        assert log.action == 'updated'
        assert log.changes[0]['field'] == 'overdue_reminder_frequency'

    def test_update_rejects_invalid_frequency(self, super_client):
        response = super_client.patch(
            '/api/accounting/settings/update/',
            {'overdue_reminder_frequency': 'cada-rato'},
            format='json',
        )
        assert response.status_code == 400

    def test_toggle_notifications_enabled(self, super_client):
        response = super_client.patch(
            '/api/accounting/settings/update/',
            {'notifications_enabled': False},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['notifications_enabled'] is False

    def test_usd_exchange_rate_defaults_to_4000(self, super_client):
        response = super_client.get('/api/accounting/settings/')
        assert response.data['usd_exchange_rate'] == '4000.00'

    def test_usd_exchange_rate_roundtrip_and_min(self, super_client):
        """The USD rate persists on PATCH and rejects values below 1."""
        response = super_client.patch(
            '/api/accounting/settings/update/',
            {'usd_exchange_rate': '4350.50'},
            format='json',
        )
        assert response.status_code == 200, response.data
        assert response.data['usd_exchange_rate'] == '4350.50'

        rejected = super_client.patch(
            '/api/accounting/settings/update/',
            {'usd_exchange_rate': '0.50'},
            format='json',
        )
        assert rejected.status_code == 400

    def test_usd_rate_update_resynchronizes_recurring_equivalents(
        self, super_client,
    ):
        payment = RecurringPayment.objects.create(
            name='Chat-GPT', price='200.00', currency='USD',
        )

        response = super_client.patch(
            '/api/accounting/settings/update/',
            {'usd_exchange_rate': '4350.50'},
            format='json',
        )

        payment.refresh_from_db()
        assert response.status_code == 200
        assert payment.cop_equivalent == Decimal('870100.00')

    def test_usd_rate_update_leaves_cop_recurring_at_its_price(
        self, super_client,
    ):
        payment = RecurringPayment.objects.create(
            name='Netflix', price='39800.00', currency='COP',
        )

        super_client.patch(
            '/api/accounting/settings/update/',
            {'usd_exchange_rate': '4350.50'},
            format='json',
        )

        payment.refresh_from_db()
        assert payment.cop_equivalent == Decimal('39800.00')

    def test_income_view_mode_defaults_to_grouped(self, super_client):
        response = super_client.get('/api/accounting/settings/')
        assert response.data['income_default_view_mode'] == 'grouped'

    def test_income_view_mode_roundtrip_and_audit(self, super_client):
        """PATCH persists the landing mode and audits it with its label."""
        response = super_client.patch(
            '/api/accounting/settings/update/',
            {'income_default_view_mode': 'classic'},
            format='json',
        )
        assert response.status_code == 200, response.data
        assert response.data['income_default_view_mode'] == 'classic'
        log = AccountingChangeLog.objects.get(entity_type='settings')
        assert log.changes[0]['field'] == 'income_default_view_mode'
        assert log.changes[0]['old'] == 'Agrupado'
        assert log.changes[0]['new'] == 'Clásico'

    def test_income_view_mode_rejects_unknown_value(self, super_client):
        response = super_client.patch(
            '/api/accounting/settings/update/',
            {'income_default_view_mode': 'kanban'},
            format='json',
        )
        assert response.status_code == 400
