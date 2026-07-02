"""API tests for accounting income/expense endpoints."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import AccountingChangeLog, ExpenseRecord, IncomeRecord
from content.services import accounting_service


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


def income_payload(**overrides):
    payload = {
        'concept': 'Kore - Inicio 40%',
        'kind': 'expected',
        'period_date': '2026-02',
        'total_amount': '1160000.00',
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestAccountingEndpointAuth:
    def test_staff_non_superuser_gets_403(self, admin_client):
        assert admin_client.get('/api/accounting/incomes/').status_code == 403
        assert admin_client.post(
            '/api/accounting/incomes/create/', income_payload(), format='json',
        ).status_code == 403

    def test_anonymous_is_rejected(self, api_client):
        response = api_client.get('/api/accounting/incomes/')
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestIncomeCrud:
    def test_create_returns_201_with_default_split(self, super_client):
        response = super_client.post(
            '/api/accounting/incomes/create/', income_payload(), format='json',
        )
        assert response.status_code == 201, response.data
        assert response.data['gustavo_amount'] == '580000.00'
        assert response.data['carlos_amount'] == '580000.00'
        assert response.data['period'] == '2026-02'
        assert AccountingChangeLog.objects.filter(
            entity_type='income', action='created',
        ).exists()

    def test_create_with_invalid_split_returns_400(self, super_client):
        response = super_client.post(
            '/api/accounting/incomes/create/',
            income_payload(
                gustavo_amount='700000.00', carlos_amount='700000.00',
            ),
            format='json',
        )
        assert response.status_code == 400

    def test_list_returns_results_and_meta(self, super_client, make_income):
        make_income()
        response = super_client.get('/api/accounting/incomes/')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert 'meta' in response.data

    def test_retrieve_update_delete_flow(self, super_client, make_income):
        income = make_income()
        detail = super_client.get(f'/api/accounting/incomes/{income.pk}/')
        assert detail.status_code == 200

        update = super_client.patch(
            f'/api/accounting/incomes/{income.pk}/update/',
            {'total_amount': '2000000.00', 'gustavo_amount': '1000000.00',
             'carlos_amount': '1000000.00'},
            format='json',
        )
        assert update.status_code == 200
        assert update.data['total_amount'] == '2000000.00'

        delete = super_client.delete(
            f'/api/accounting/incomes/{income.pk}/delete/',
        )
        assert delete.status_code == 204
        assert not IncomeRecord.objects.filter(pk=income.pk).exists()

    def test_update_missing_record_returns_404(self, super_client):
        response = super_client.patch(
            '/api/accounting/incomes/999/update/', {}, format='json',
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestIncomeFilters:
    @pytest.fixture
    def dataset(self, make_income):
        make_income(
            concept='Kore expected', kind='expected',
            period_date=date(2026, 2, 1), total_amount=Decimal('1000.00'),
            gustavo_amount=Decimal('500.00'), carlos_amount=Decimal('500.00'),
        )
        make_income(
            concept='Kore liquid', kind='liquid',
            period_date=date(2026, 3, 1), total_amount=Decimal('900.00'),
            gustavo_amount=Decimal('0.00'), carlos_amount=Decimal('900.00'),
        )
        make_income(
            concept='Vastago pocket', kind='liquid', destination='pocket',
            period_date=date(2026, 4, 1), total_amount=Decimal('2000.00'),
            gustavo_amount=Decimal('0.00'), carlos_amount=Decimal('0.00'),
        )

    def _concepts(self, response):
        return {row['concept'] for row in response.data['results']}

    def test_filter_by_kind(self, super_client, dataset):
        response = super_client.get('/api/accounting/incomes/?kind=expected')
        assert self._concepts(response) == {'Kore expected'}

    def test_filter_by_partner_gustavo(self, super_client, dataset):
        response = super_client.get(
            '/api/accounting/incomes/?partner=gustavo',
        )
        assert self._concepts(response) == {'Kore expected'}

    def test_filter_by_partner_projectapp(self, super_client, dataset):
        response = super_client.get(
            '/api/accounting/incomes/?partner=projectapp',
        )
        assert self._concepts(response) == {'Vastago pocket'}

    def test_filter_by_date_range(self, super_client, dataset):
        response = super_client.get(
            '/api/accounting/incomes/?date_from=2026-03-01&date_to=2026-03-31',
        )
        assert self._concepts(response) == {'Kore liquid'}

    def test_filter_by_amount_range(self, super_client, dataset):
        response = super_client.get(
            '/api/accounting/incomes/?amount_min=950&amount_max=1500',
        )
        assert self._concepts(response) == {'Kore expected'}

    def test_search_by_concept(self, super_client, dataset):
        response = super_client.get('/api/accounting/incomes/?q=vastago')
        assert self._concepts(response) == {'Vastago pocket'}

    def test_invalid_date_returns_spanish_error(self, super_client):
        response = super_client.get(
            '/api/accounting/incomes/?date_from=not-a-date',
        )
        assert response.status_code == 400
        assert 'fecha' in response.data['error']

    def test_invalid_partner_returns_400(self, super_client):
        response = super_client.get('/api/accounting/incomes/?partner=bob')
        assert response.status_code == 400


@pytest.mark.django_db
class TestExpenseCrudAndFilters:
    def test_create_and_filter_by_category(self, super_client):
        for concept, category in (
            ('Claude Code 20x', 'business'),
            ('Aporte Carro Onix', 'personal'),
        ):
            response = super_client.post(
                '/api/accounting/expenses/create/',
                {
                    'concept': concept,
                    'period_date': '2026-01',
                    'category': category,
                    'total_amount': '100.00',
                },
                format='json',
            )
            assert response.status_code == 201, response.data

        response = super_client.get(
            '/api/accounting/expenses/?category=personal',
        )
        assert [r['concept'] for r in response.data['results']] == [
            'Aporte Carro Onix',
        ]

    def test_update_and_delete(self, super_client, make_expense):
        expense = make_expense()
        update = super_client.patch(
            f'/api/accounting/expenses/{expense.pk}/update/',
            {'concept': 'Windsurf Marzo'},
            format='json',
        )
        assert update.status_code == 200
        assert update.data['concept'] == 'Windsurf Marzo'

        delete = super_client.delete(
            f'/api/accounting/expenses/{expense.pk}/delete/',
        )
        assert delete.status_code == 204
        assert not ExpenseRecord.objects.filter(pk=expense.pk).exists()
