"""API tests for hosting/pocket/recurring/ads/card-snapshot/dashboard."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import HostingRecord, PocketMovement, RecurringPayment
from content.services import accounting_service


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


@pytest.mark.django_db
class TestHostingEndpoints:
    def test_create_defaults_payment_per_cycle(self, super_client):
        response = super_client.post(
            '/api/accounting/hostings/create/',
            {
                'client_name': 'German - Kore',
                'domain_url': 'https://korehealths.com/',
                'monthly_value': '91667.00',
                'payment_modality': 'semiannual',
            },
            format='json',
        )
        assert response.status_code == 201, response.data
        assert response.data['payment_per_cycle'] == '550002.00'

    def test_list_meta_reports_active_monthly_income(self, super_client):
        HostingRecord.objects.create(
            client_name='A', monthly_value=Decimal('100.00'), is_active=True,
        )
        HostingRecord.objects.create(
            client_name='B', monthly_value=Decimal('50.00'), is_active=False,
        )
        response = super_client.get('/api/accounting/hostings/')
        assert response.data['meta']['active_count'] == 1
        assert response.data['meta']['monthly_income'] == '100.00'

    def test_meta_reports_expiring_soon_and_total_paid(self, super_client):
        from datetime import timedelta

        from content.utils import today_bogota

        today = today_bogota()
        HostingRecord.objects.create(
            client_name='Pronto', monthly_value=Decimal('10.00'),
            is_active=True, valid_to=today + timedelta(days=15),
            total_paid=Decimal('600.00'),
        )
        HostingRecord.objects.create(
            client_name='Lejano', monthly_value=Decimal('10.00'),
            is_active=True, valid_to=today + timedelta(days=90),
            total_paid=Decimal('400.00'),
        )
        HostingRecord.objects.create(
            client_name='Inactivo', monthly_value=Decimal('10.00'),
            is_active=False, valid_to=today + timedelta(days=5),
        )
        response = super_client.get('/api/accounting/hostings/')
        meta = response.data['meta']
        assert meta['expiring_soon_count'] == 1
        assert meta['total_paid'] == '1000.00'

    def test_filter_by_modality(self, super_client):
        HostingRecord.objects.create(
            client_name='Anual', monthly_value=Decimal('10.00'),
            payment_modality='annual',
        )
        HostingRecord.objects.create(
            client_name='Mensual', monthly_value=Decimal('10.00'),
            payment_modality='monthly',
        )
        response = super_client.get(
            '/api/accounting/hostings/?payment_modality=annual',
        )
        assert [r['client_name'] for r in response.data['results']] == ['Anual']


@pytest.mark.django_db
class TestPocketEndpoints:
    def test_list_meta_reports_balance(self, super_client):
        PocketMovement.objects.create(
            concept='In', movement_date=date(2026, 4, 1),
            direction='in', amount=Decimal('100.00'),
        )
        PocketMovement.objects.create(
            concept='Out', movement_date=date(2026, 4, 2),
            direction='out', amount=Decimal('40.00'),
        )
        response = super_client.get('/api/accounting/pocket/')
        assert response.data['meta']['balance'] == '60.00'

    def test_manual_movement_crud(self, super_client):
        create = super_client.post(
            '/api/accounting/pocket/create/',
            {
                'concept': 'Trans. Gustavo',
                'movement_date': '2026-05-09',
                'direction': 'out',
                'amount': '200000.00',
            },
            format='json',
        )
        assert create.status_code == 201, create.data
        movement_id = create.data['id']

        delete = super_client.delete(
            f'/api/accounting/pocket/{movement_id}/delete/',
        )
        assert delete.status_code == 204

    def test_linked_movement_edit_mirrors_into_income(self, super_client):
        income = super_client.post(
            '/api/accounting/incomes/create/',
            {
                'concept': 'Vastago (Fase 1)',
                'kind': 'liquid',
                'destination': 'pocket',
                'period_date': '2026-04',
                'total_amount': '2123000.00',
            },
            format='json',
        )
        movement_id = income.data['pocket_movement']
        assert movement_id is not None

        update = super_client.patch(
            f'/api/accounting/pocket/{movement_id}/update/',
            {'amount': '1500000.00'},
            format='json',
        )
        assert update.status_code == 200, update.data
        linked = super_client.get(
            f'/api/accounting/incomes/{income.data["id"]}/',
        )
        assert linked.data['total_amount'] == '1500000.00'

        locked = super_client.patch(
            f'/api/accounting/pocket/{movement_id}/update/',
            {'direction': 'out'},
            format='json',
        )
        assert locked.status_code == 400
        assert locked.data['code'] == 'linked_direction_locked'

        delete = super_client.delete(
            f'/api/accounting/pocket/{movement_id}/delete/',
        )
        assert delete.status_code == 204
        gone = super_client.get(
            f'/api/accounting/incomes/{income.data["id"]}/',
        )
        assert gone.status_code == 404


@pytest.mark.django_db
class TestRecurringEndpoints:
    def test_meta_reports_monthly_cop_total(self, super_client):
        RecurringPayment.objects.create(
            name='Claude Code 20x', price=Decimal('200.00'), currency='USD',
            cop_equivalent=Decimal('800000.00'), frequency='monthly',
        )
        RecurringPayment.objects.create(
            name='NameCheap', price=Decimal('10.98'), currency='USD',
            cop_equivalent=Decimal('43920.00'), frequency='annual',
        )
        response = super_client.get('/api/accounting/recurring/')
        assert response.data['meta']['monthly_cop_total'] == '803660.00'

    def test_meta_reports_usd_totals_from_settings_rate(self, super_client):
        from content.models import AccountingSettings

        config = AccountingSettings.load()
        config.usd_exchange_rate = Decimal('4000.00')
        config.save()
        RecurringPayment.objects.create(
            name='Claude Code 20x', price=Decimal('200.00'), currency='USD',
            cop_equivalent=Decimal('800000.00'), frequency='monthly',
        )
        RecurringPayment.objects.create(
            name='Hosting COP', price=Decimal('400000.00'), currency='COP',
            cop_equivalent=Decimal('400000.00'), frequency='monthly',
        )
        response = super_client.get('/api/accounting/recurring/')
        meta = response.data['meta']
        # (800000 + 400000) / 4000 = 300 USD
        assert meta['monthly_usd_total'] == '300.00'
        assert meta['usd_native_total'] == '200.00'
        assert meta['usd_exchange_rate'] == '4000.00'

    def test_filter_by_frequency_and_method(self, super_client):
        RecurringPayment.objects.create(
            name='Efectivo mensual', price=Decimal('400000.00'),
            payment_method='cash', frequency='monthly',
        )
        RecurringPayment.objects.create(
            name='TC anual', price=Decimal('43920.00'),
            payment_method='credit_card', frequency='annual',
        )
        response = super_client.get(
            '/api/accounting/recurring/?frequency=monthly&payment_method=cash',
        )
        assert [r['name'] for r in response.data['results']] == [
            'Efectivo mensual',
        ]


@pytest.mark.django_db
class TestAdsEndpoints:
    def test_list_includes_running_accumulated(self, super_client):
        for day, amount in (
            ('2026-01-25', '143820.00'),
            ('2026-01-17', '146103.00'),
        ):
            response = super_client.post(
                '/api/accounting/ads/create/',
                {'spend_date': day, 'amount': amount, 'origin_card': 'T.C 0655'},
                format='json',
            )
            assert response.status_code == 201, response.data

        response = super_client.get('/api/accounting/ads/')
        rows = response.data['results']
        assert rows[0]['spend_date'] == '2026-01-17'
        assert rows[0]['accumulated'] == '146103.00'
        assert rows[1]['accumulated'] == '289923.00'


@pytest.mark.django_db
class TestCardSnapshotAndDashboard:
    def test_card_snapshot_crud(self, super_client):
        create = super_client.post(
            '/api/accounting/card-snapshots/create/',
            {
                'snapshot_date': '2026-07-01',
                'card_name': 'T.C 0064',
                'available_amount': '3849046.00',
                'debt_amount': '4150954.00',
            },
            format='json',
        )
        assert create.status_code == 201, create.data

        listing = super_client.get(
            '/api/accounting/card-snapshots/?card_name=T.C 0064',
        )
        assert len(listing.data['results']) == 1

    def test_dashboard_payload_shape(self, super_client, make_income):
        make_income(kind='expected', total_amount=Decimal('1500.00'))
        make_income(kind='liquid', total_amount=Decimal('900.00'))
        response = super_client.get('/api/accounting/dashboard/?year=2026')
        assert response.status_code == 200
        data = response.data
        assert data['expected_total'] == Decimal('1500.00')
        assert data['liquid_total'] == Decimal('900.00')
        assert len(data['monthly']) == 12
        assert set(data['partners'].keys()) == {'gustavo', 'carlos', 'company'}
        assert 'pocket_balance' in data
        assert 'hostings' in data

    def test_dashboard_rejects_invalid_year(self, super_client):
        response = super_client.get('/api/accounting/dashboard/?year=abc')
        assert response.status_code == 400


@pytest.mark.django_db
class TestCreditCardCatalogEndpoints:
    PAYLOAD = {
        'name': 'T.C Nueva',
        'credit_limit': '5000000.00',
        'statements_since': '2026-06',
    }

    def test_create_update_and_list(self, super_client):
        create = super_client.post(
            '/api/accounting/credit-cards/create/', self.PAYLOAD, format='json',
        )
        assert create.status_code == 201, create.data
        assert create.data['statements_since'] == '2026-06-01'

        update = super_client.patch(
            f"/api/accounting/credit-cards/{create.data['id']}/update/",
            {'credit_limit': '9000000.00'},
            format='json',
        )
        assert update.status_code == 200
        assert update.data['credit_limit'] == '9000000.00'

        listing = super_client.get('/api/accounting/credit-cards/')
        names = [row['name'] for row in listing.data['results']]
        assert 'T.C Nueva' in names

    def test_delete_blocked_when_referenced(self, super_client):
        from content.models import CardBalanceSnapshot, CreditCard

        card = CreditCard.objects.create(
            name='T.C Referenciada', credit_limit=Decimal('1000000.00'),
        )
        CardBalanceSnapshot.objects.create(
            snapshot_date=date(2026, 7, 1),
            card_name=card.name,
            available_amount=Decimal('500000.00'),
            debt_amount=Decimal('500000.00'),
        )
        response = super_client.delete(
            f'/api/accounting/credit-cards/{card.id}/delete/',
        )
        assert response.status_code == 400
        assert response.data['code'] == 'credit_card_referenced'
        assert CreditCard.objects.filter(pk=card.pk).exists()

    def test_delete_unreferenced_card(self, super_client):
        from content.models import CreditCard

        card = CreditCard.objects.create(
            name='T.C Sin Uso', credit_limit=Decimal('1000000.00'),
        )
        response = super_client.delete(
            f'/api/accounting/credit-cards/{card.id}/delete/',
        )
        assert response.status_code == 204
        assert not CreditCard.objects.filter(pk=card.pk).exists()
