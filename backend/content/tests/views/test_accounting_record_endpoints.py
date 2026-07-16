"""API tests for the thin per-entity record endpoints and hosting cycles.

Exercises the retrieve/update/delete wrappers that delegate to
``_retrieve_record`` / ``_update_record`` / ``_delete_record``, the hosting
payment-cycle endpoints, and two list-filter branches without direct coverage.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import (
    AdsSpendRecord,
    CardBalanceSnapshot,
    CreditCard,
    ExpenseRecord,
    HostingRecord,
    PocketMovement,
    RecurringPayment,
)
from content.services import accounting_service


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


def make_expense(**overrides):
    defaults = {
        'concept': 'Hosting Hetzner',
        'period_date': date(2026, 3, 1),
        'total_amount': Decimal('100.00'),
        'gustavo_amount': Decimal('50.00'),
        'carlos_amount': Decimal('50.00'),
    }
    defaults.update(overrides)
    return ExpenseRecord.objects.create(**defaults)


def make_hosting(**overrides):
    defaults = {'client_name': 'Kore', 'monthly_value': Decimal('90000.00')}
    defaults.update(overrides)
    return HostingRecord.objects.create(**defaults)


def make_pocket(**overrides):
    defaults = {
        'concept': 'Abono bolsillo',
        'movement_date': date(2026, 3, 10),
        'direction': PocketMovement.Direction.IN,
        'amount': Decimal('80000.00'),
    }
    defaults.update(overrides)
    return PocketMovement.objects.create(**defaults)


def make_recurring(**overrides):
    defaults = {
        'name': 'Figma',
        'price': Decimal('40000.00'),
        'cop_equivalent': Decimal('40000.00'),
        'frequency': 'monthly',
    }
    defaults.update(overrides)
    return RecurringPayment.objects.create(**defaults)


def make_ads(**overrides):
    defaults = {'spend_date': date(2026, 3, 5), 'amount': Decimal('150000.00')}
    defaults.update(overrides)
    return AdsSpendRecord.objects.create(**defaults)


def make_snapshot(**overrides):
    defaults = {
        'snapshot_date': date(2026, 3, 13),
        'card_name': 'T.C 0064',
        'available_amount': Decimal('1000000.00'),
        'debt_amount': Decimal('400000.00'),
    }
    defaults.update(overrides)
    return CardBalanceSnapshot.objects.create(**defaults)


RETRIEVE_CASES = [
    ('expenses', make_expense, 'concept', 'Hosting Hetzner'),
    ('hostings', make_hosting, 'client_name', 'Kore'),
    ('pocket', make_pocket, 'concept', 'Abono bolsillo'),
    ('recurring', make_recurring, 'name', 'Figma'),
    ('ads', make_ads, 'amount', '150000.00'),
    ('card-snapshots', make_snapshot, 'card_name', 'T.C 0064'),
]

UPDATE_CASES = [
    ('hostings', make_hosting, {'monthly_value': '120000.00'},
     'monthly_value', '120000.00'),
    ('recurring', make_recurring, {'name': 'Notion'}, 'name', 'Notion'),
    ('ads', make_ads, {'amount': '99000.00'}, 'amount', '99000.00'),
]

DELETE_CASES = [
    ('hostings', make_hosting, HostingRecord),
    ('ads', make_ads, AdsSpendRecord),
    ('card-snapshots', make_snapshot, CardBalanceSnapshot),
]


@pytest.mark.django_db
class TestRecordRetrieveEndpoints:
    @pytest.mark.parametrize(
        'path,factory,field,expected',
        RETRIEVE_CASES,
        ids=[case[0] for case in RETRIEVE_CASES],
    )
    def test_retrieve_returns_the_record(
        self, super_client, path, factory, field, expected,
    ):
        record = factory()
        response = super_client.get(f'/api/accounting/{path}/{record.pk}/')
        assert response.status_code == 200
        assert response.data[field] == expected


@pytest.mark.django_db
class TestRecordUpdateEndpoints:
    @pytest.mark.parametrize(
        'path,factory,payload,field,expected',
        UPDATE_CASES,
        ids=[case[0] for case in UPDATE_CASES],
    )
    def test_update_applies_the_patch(
        self, super_client, path, factory, payload, field, expected,
    ):
        record = factory()
        response = super_client.patch(
            f'/api/accounting/{path}/{record.pk}/update/',
            payload,
            format='json',
        )
        assert response.status_code == 200, response.data
        assert response.data[field] == expected


@pytest.mark.django_db
class TestRecordDeleteEndpoints:
    @pytest.mark.parametrize(
        'path,factory,model',
        DELETE_CASES,
        ids=[case[0] for case in DELETE_CASES],
    )
    def test_delete_removes_the_row(self, super_client, path, factory, model):
        record = factory()
        response = super_client.delete(
            f'/api/accounting/{path}/{record.pk}/delete/',
        )
        assert response.status_code == 204
        assert model.objects.count() == 0


@pytest.mark.django_db
class TestHostingCycleEndpoints:
    def test_create_registers_a_cycle_payment(self, super_client):
        hosting = make_hosting()
        response = super_client.post(
            f'/api/accounting/hostings/{hosting.pk}/cycles/create/',
            {'amount': '90000.00', 'paid_at': '2026-03-01'},
            format='json',
        )
        assert response.status_code == 201, response.data
        assert response.data['hosting']['id'] == hosting.pk
        assert hosting.cycles.count() == 1

    def test_create_rejects_an_inverted_period(self, super_client):
        hosting = make_hosting()
        response = super_client.post(
            f'/api/accounting/hostings/{hosting.pk}/cycles/create/',
            {
                'amount': '90000.00',
                'period_from': '2026-03-01',
                'period_to': '2026-02-01',
            },
            format='json',
        )
        assert response.status_code == 400
        assert hosting.cycles.count() == 0

    def test_list_returns_registered_cycles(self, super_client):
        hosting = make_hosting()
        super_client.post(
            f'/api/accounting/hostings/{hosting.pk}/cycles/create/',
            {'amount': '90000.00', 'paid_at': '2026-03-01'},
            format='json',
        )
        response = super_client.get(
            f'/api/accounting/hostings/{hosting.pk}/cycles/',
        )
        assert response.status_code == 200
        assert len(response.data['results']) == 1

    def test_delete_removes_the_cycle(self, super_client):
        hosting = make_hosting()
        super_client.post(
            f'/api/accounting/hostings/{hosting.pk}/cycles/create/',
            {'amount': '90000.00', 'paid_at': '2026-03-01'},
            format='json',
        )
        cycle = hosting.cycles.first()
        response = super_client.delete(
            f'/api/accounting/hostings/{hosting.pk}/cycles/'
            f'{cycle.pk}/delete/',
        )
        assert response.status_code == 204
        assert hosting.cycles.count() == 0


@pytest.mark.django_db
class TestListFilterBranches:
    def test_invalid_year_returns_400(self, super_client):
        response = super_client.get('/api/accounting/incomes/?year=abc')
        assert response.status_code == 400
        assert 'year' in str(response.data)

    def test_partner_projectapp_filters_unassigned_remainder(
        self, super_client,
    ):
        """partner=projectapp keeps only rows whose split leaves a remainder."""
        make_expense(
            concept='Con remanente',
            gustavo_amount=Decimal('30.00'),
            carlos_amount=Decimal('30.00'),
        )
        make_expense(concept='Repartido completo')
        response = super_client.get(
            '/api/accounting/expenses/?partner=projectapp',
        )
        assert response.status_code == 200
        concepts = [row['concept'] for row in response.data['results']]
        assert concepts == ['Con remanente']

    def test_invalid_amount_min_returns_400(self, super_client):
        response = super_client.get('/api/accounting/expenses/?amount_min=abc')
        assert response.status_code == 400
        assert 'amount_min' in str(response.data)

    def test_year_filter_limits_the_results(self, super_client):
        make_expense(concept='Este año')
        make_expense(concept='Año pasado', period_date=date(2025, 3, 1))
        response = super_client.get('/api/accounting/expenses/?year=2026')
        concepts = [row['concept'] for row in response.data['results']]
        assert concepts == ['Este año']

    def test_multi_value_category_filters_as_or(self, super_client):
        make_expense(concept='Negocio')
        make_expense(concept='Personal', category='personal')
        response = super_client.get(
            '/api/accounting/expenses/?category=business,personal',
        )
        assert len(response.data['results']) == 2

    def test_bool_filter_keeps_only_active_recurring(self, super_client):
        make_recurring(name='Activa')
        make_recurring(name='Inactiva', is_active=False)
        response = super_client.get('/api/accounting/recurring/?is_active=true')
        names = [row['name'] for row in response.data['results']]
        assert names == ['Activa']

    def test_partner_carlos_filters_by_his_amount(self, super_client):
        make_expense(
            concept='De Carlos',
            gustavo_amount=Decimal('0.00'),
            carlos_amount=Decimal('100.00'),
        )
        make_expense(
            concept='De Gustavo',
            gustavo_amount=Decimal('100.00'),
            carlos_amount=Decimal('0.00'),
        )
        response = super_client.get('/api/accounting/expenses/?partner=carlos')
        concepts = [row['concept'] for row in response.data['results']]
        assert concepts == ['De Carlos']

    def test_pocket_meta_balance_respects_date_to(self, super_client):
        make_pocket(amount=Decimal('100.00'), movement_date=date(2026, 2, 10))
        make_pocket(amount=Decimal('50.00'), movement_date=date(2026, 5, 10))
        response = super_client.get('/api/accounting/pocket/?date_to=2026-03-31')
        assert response.data['meta']['balance'] == '100.00'


@pytest.mark.django_db
class TestRecurringAndCatalogEndpoints:
    def test_create_recurring_payment_returns_201(self, super_client):
        response = super_client.post(
            '/api/accounting/recurring/create/',
            {'name': 'Notion', 'price': '30000.00'},
            format='json',
        )
        assert response.status_code == 201, response.data
        assert response.data['name'] == 'Notion'

    def test_delete_recurring_payment_removes_the_row(self, super_client):
        record = make_recurring()
        response = super_client.delete(
            f'/api/accounting/recurring/{record.pk}/delete/',
        )
        assert response.status_code == 204
        assert RecurringPayment.objects.count() == 0

    def test_retrieve_credit_card_returns_the_record(self, super_client):
        card = CreditCard.objects.create(
            name='T.C QA Cycle', credit_limit=Decimal('10000000.00'),
        )
        response = super_client.get(f'/api/accounting/credit-cards/{card.pk}/')
        assert response.status_code == 200
        assert response.data['name'] == 'T.C QA Cycle'

    def test_update_card_snapshot_applies_the_patch(self, super_client):
        record = make_snapshot()
        response = super_client.patch(
            f'/api/accounting/card-snapshots/{record.pk}/update/',
            {'available_amount': '900000.00'},
            format='json',
        )
        assert response.status_code == 200, response.data
        assert response.data['available_amount'] == '900000.00'

    def test_update_with_an_invalid_payload_returns_400(self, super_client):
        record = make_hosting()
        response = super_client.patch(
            f'/api/accounting/hostings/{record.pk}/update/',
            {'monthly_value': 'abc'},
            format='json',
        )
        assert response.status_code == 400
