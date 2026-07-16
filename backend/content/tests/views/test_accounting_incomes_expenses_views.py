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


@pytest.mark.django_db
class TestIncomeExpenseMeta:
    def test_income_meta_totals_and_top(self, super_client, make_income):
        from content.utils import today_bogota

        today = today_bogota()
        month_start = today.replace(day=1)
        make_income(
            kind=IncomeRecord.Kind.EXPECTED, period_date=month_start,
            total_amount=Decimal('2000.00'),
            gustavo_amount=Decimal('1000.00'), carlos_amount=Decimal('1000.00'),
        )
        make_income(
            concept='Entrega grande', kind=IncomeRecord.Kind.LIQUID,
            period_date=month_start, total_amount=Decimal('1500.00'),
            gustavo_amount=Decimal('750.00'), carlos_amount=Decimal('750.00'),
        )
        response = super_client.get('/api/accounting/incomes/')
        meta = response.data['meta']
        assert meta['expected_total'] == '2000.00'
        assert meta['liquid_total'] == '1500.00'
        assert meta['received_pct'] == 75
        assert meta['current_month_liquid'] == '1500.00'
        assert meta['top_income']['concept'] == 'Entrega grande'

    def test_income_meta_empty_year(self, super_client):
        response = super_client.get('/api/accounting/incomes/')
        meta = response.data['meta']
        assert meta['received_pct'] is None
        assert meta['top_income'] is None

    def test_income_meta_reports_lost_total_without_touching_the_rest(
        self, super_client, make_income,
    ):
        from content.utils import today_bogota

        month_start = today_bogota().replace(day=1)
        make_income(
            kind=IncomeRecord.Kind.EXPECTED, period_date=month_start,
            total_amount=Decimal('2000.00'),
        )
        make_income(
            concept='Entrega grande', kind=IncomeRecord.Kind.LIQUID,
            period_date=month_start, total_amount=Decimal('1000.00'),
        )
        make_income(
            concept='Catherine Ruiz Candles', kind=IncomeRecord.Kind.LOST,
            period_date=month_start, total_amount=Decimal('460000.00'),
        )
        meta = super_client.get('/api/accounting/incomes/').data['meta']
        assert meta['lost_total'] == '460000.00'
        assert meta['expected_total'] == '2000.00'
        assert meta['liquid_total'] == '1000.00'
        assert meta['received_pct'] == 50
        assert meta['top_income']['concept'] == 'Entrega grande'

    def test_meta_counts_an_expected_once_when_it_has_two_liquid_children(
        self, super_client, make_income,
    ):
        """Regression: the paid_amount annotation must not multiply rows.

        A Sum() over the reverse FK would join one row per child and report
        expected_total as 4000.00 here.
        """
        from content.utils import today_bogota

        month_start = today_bogota().replace(day=1)
        expected = make_income(
            kind=IncomeRecord.Kind.EXPECTED, period_date=month_start,
            total_amount=Decimal('2000.00'),
        )
        for amount in ('500.00', '300.00'):
            make_income(
                concept='Abono', kind=IncomeRecord.Kind.LIQUID,
                period_date=month_start, total_amount=Decimal(amount),
                expected_income=expected,
            )
        meta = super_client.get('/api/accounting/incomes/').data['meta']
        assert meta['expected_total'] == '2000.00'
        assert meta['liquid_total'] == '800.00'


@pytest.mark.django_db
class TestIncomePaymentState:
    def test_expected_row_reports_paid_pending_and_status(
        self, super_client, make_income,
    ):
        expected = make_income(
            kind=IncomeRecord.Kind.EXPECTED,
            total_amount=Decimal('1000.00'),
        )
        make_income(
            kind=IncomeRecord.Kind.LIQUID, total_amount=Decimal('400.00'),
            expected_income=expected,
        )
        rows = super_client.get('/api/accounting/incomes/').data['results']
        row = next(r for r in rows if r['id'] == expected.id)
        assert row['paid_amount'] == '400.00'
        assert row['pending_amount'] == '600.00'
        assert row['payment_status'] == 'partial'
        assert row['payment_status_label'] == 'Parcial'

    def test_liquid_and_lost_rows_carry_no_payment_state(
        self, super_client, make_income,
    ):
        make_income(kind=IncomeRecord.Kind.LIQUID)
        make_income(kind=IncomeRecord.Kind.LOST)
        rows = super_client.get('/api/accounting/incomes/').data['results']
        for row in rows:
            assert row['paid_amount'] is None
            assert row['pending_amount'] is None
            assert row['payment_status'] is None
            assert row['payment_status_label'] is None

    def test_single_record_endpoint_computes_state_without_the_annotation(
        self, super_client, make_income,
    ):
        """retrieve/create/update serialize a bare instance, not the list qs."""
        expected = make_income(
            kind=IncomeRecord.Kind.EXPECTED, total_amount=Decimal('1000.00'),
        )
        make_income(
            kind=IncomeRecord.Kind.LIQUID, total_amount=Decimal('1000.00'),
            expected_income=expected,
        )
        row = super_client.get(f'/api/accounting/incomes/{expected.id}/').data
        assert row['paid_amount'] == '1000.00'
        assert row['pending_amount'] == '0.00'
        assert row['payment_status'] == 'paid'

    def test_a_lost_child_is_not_counted_as_payment(
        self, super_client, make_income,
    ):
        expected = make_income(
            kind=IncomeRecord.Kind.EXPECTED, total_amount=Decimal('1000.00'),
        )
        make_income(
            kind=IncomeRecord.Kind.LOST, total_amount=Decimal('1000.00'),
            expected_income=expected,
        )
        row = super_client.get(f'/api/accounting/incomes/{expected.id}/').data
        assert row['paid_amount'] == '0.00'
        assert row['payment_status'] == 'pending'

    def test_overpaid_row_is_paid_and_never_reports_negative_pending(
        self, super_client, make_income,
    ):
        expected = make_income(
            kind=IncomeRecord.Kind.EXPECTED, total_amount=Decimal('100.00'),
        )
        make_income(
            kind=IncomeRecord.Kind.LIQUID, total_amount=Decimal('900.00'),
            expected_income=expected,
        )
        row = super_client.get(f'/api/accounting/incomes/{expected.id}/').data
        assert row['payment_status'] == 'paid'
        assert row['pending_amount'] == '0.00'

    def test_liquidating_creates_a_linked_liquid_row_and_keeps_the_expected(
        self, super_client, make_income,
    ):
        expected = make_income(
            kind=IncomeRecord.Kind.EXPECTED, period_date=date(2026, 8, 1),
            total_amount=Decimal('1000.00'),
        )
        response = super_client.post(
            '/api/accounting/incomes/create/',
            income_payload(
                kind='liquid', period_date='2026-11',
                total_amount='700.00', expected_income=expected.id,
            ),
            format='json',
        )
        assert response.status_code == 201
        liquid = IncomeRecord.objects.get(id=response.data['id'])
        assert liquid.expected_income_id == expected.id
        assert liquid.period_date == date(2026, 11, 1)
        assert liquid.pocket_movement is None
        expected.refresh_from_db()
        assert expected.kind == IncomeRecord.Kind.EXPECTED
        assert expected.total_amount == Decimal('1000.00')

    def test_expense_meta_totals_split_and_top(self, super_client):
        from content.utils import today_bogota

        today = today_bogota()
        month_start = today.replace(day=1)
        for concept, category, amount in (
            ('Figma', 'business', '300.00'),
            ('Almuerzo', 'personal', '700.00'),
        ):
            ExpenseRecord.objects.create(
                concept=concept, category=category,
                period_date=month_start, total_amount=Decimal(amount),
            )
        response = super_client.get('/api/accounting/expenses/')
        meta = response.data['meta']
        assert meta['year_total'] == '1000.00'
        assert meta['current_month_total'] == '1000.00'
        assert meta['business_total'] == '300.00'
        assert meta['personal_total'] == '700.00'
        assert meta['top_expense']['concept'] == 'Almuerzo'

    def test_expense_meta_alert_triggers_at_150_pct(self, super_client):
        from content.utils import today_bogota

        today = today_bogota()
        if today.month == 1:
            pytest.skip('sin meses previos en enero')
        prior = today.replace(month=today.month - 1, day=1)
        ExpenseRecord.objects.create(
            concept='Mes previo', period_date=prior,
            total_amount=Decimal('100.00'),
        )
        ExpenseRecord.objects.create(
            concept='Mes actual', period_date=today.replace(day=1),
            total_amount=Decimal('150.00'),
        )
        response = super_client.get('/api/accounting/expenses/')
        assert response.data['meta']['current_month_alert'] is True

    def test_expense_meta_alert_off_below_threshold(self, super_client):
        from content.utils import today_bogota

        today = today_bogota()
        if today.month == 1:
            pytest.skip('sin meses previos en enero')
        prior = today.replace(month=today.month - 1, day=1)
        ExpenseRecord.objects.create(
            concept='Mes previo', period_date=prior,
            total_amount=Decimal('100.00'),
        )
        ExpenseRecord.objects.create(
            concept='Mes actual', period_date=today.replace(day=1),
            total_amount=Decimal('149.00'),
        )
        response = super_client.get('/api/accounting/expenses/')
        assert response.data['meta']['current_month_alert'] is False
