"""API tests for the accounting descriptive-stats endpoint."""
from datetime import date
from decimal import Decimal

import pytest

from content.models import IncomeRecord, Ledger


@pytest.mark.django_db
class TestAccountingStatsEndpoint:
    def test_staff_non_superuser_is_forbidden(self, admin_client):
        response = admin_client.get('/api/accounting/stats/')
        assert response.status_code == 403

    def test_rejects_invalid_year(self, super_client):
        response = super_client.get('/api/accounting/stats/?year=abc')
        assert response.status_code == 400

    def test_empty_year_returns_zeroed_payload(self, super_client):
        response = super_client.get('/api/accounting/stats/?year=2031')
        assert response.status_code == 200
        assert response.data['year'] == 2031
        assert response.data['income']['liquid'] == {
            'count': 0, 'total': Decimal('0'), 'avg': Decimal('0'),
            'min': Decimal('0'), 'max': Decimal('0'),
        }
        assert response.data['income']['top_concepts'] == []
        assert response.data['expenses']['by_category'] == []

    def test_liquid_describe_excludes_personal_and_other_kinds(
        self, super_client, make_income,
    ):
        make_income(kind=IncomeRecord.Kind.LIQUID, concept='A',
                    period_date=date(2026, 2, 1),
                    total_amount=Decimal('100000.00'))
        make_income(kind=IncomeRecord.Kind.LIQUID, concept='B',
                    period_date=date(2026, 5, 1),
                    total_amount=Decimal('300000.00'))
        # Excluded: personal ledger, expected kind, other year.
        make_income(kind=IncomeRecord.Kind.LIQUID, concept='C',
                    period_date=date(2026, 5, 1), ledger=Ledger.GUSTAVO,
                    total_amount=Decimal('900000.00'),
                    gustavo_amount=Decimal('900000.00'),
                    carlos_amount=Decimal('0.00'))
        make_income(kind=IncomeRecord.Kind.EXPECTED, concept='D',
                    period_date=date(2026, 5, 1),
                    total_amount=Decimal('700000.00'))
        make_income(kind=IncomeRecord.Kind.LIQUID, concept='E',
                    period_date=date(2025, 5, 1),
                    total_amount=Decimal('50000.00'))

        response = super_client.get('/api/accounting/stats/?year=2026')
        liquid = response.data['income']['liquid']
        assert liquid['count'] == 2
        assert liquid['total'] == Decimal('400000.00')
        assert liquid['avg'] == Decimal('200000.00')
        assert liquid['min'] == Decimal('100000.00')
        assert liquid['max'] == Decimal('300000.00')
        assert response.data['income']['expected']['total'] == Decimal('700000.00')

    def test_lost_total_only_counts_lost_records(self, super_client, make_income):
        make_income(kind=IncomeRecord.Kind.LOST, concept='Perdido',
                    period_date=date(2026, 4, 1),
                    total_amount=Decimal('250000.00'))
        make_income(kind=IncomeRecord.Kind.LIQUID, concept='Cobrado',
                    period_date=date(2026, 4, 1),
                    total_amount=Decimal('100000.00'))

        response = super_client.get('/api/accounting/stats/?year=2026')
        assert response.data['income']['lost_total'] == Decimal('250000.00')

    def test_top_concepts_ranked_by_summed_total_and_capped(
        self, super_client, make_income,
    ):
        for index in range(9):
            make_income(kind=IncomeRecord.Kind.LIQUID, concept=f'Cliente {index}',
                        period_date=date(2026, 3, 1),
                        total_amount=Decimal(f'{(index + 1) * 10000}.00'))
        # Two rows of the same concept must group above single big rows.
        make_income(kind=IncomeRecord.Kind.LIQUID, concept='Cliente 0',
                    period_date=date(2026, 6, 1),
                    total_amount=Decimal('200000.00'))

        response = super_client.get('/api/accounting/stats/?year=2026')
        top = response.data['income']['top_concepts']
        assert len(top) == 8
        assert top[0]['concept'] == 'Cliente 0'
        assert top[0]['total'] == Decimal('210000.00')
        assert top[0]['count'] == 2
        totals = [row['total'] for row in top]
        assert totals == sorted(totals, reverse=True)

    def test_expenses_by_category_splits_business_and_personal(
        self, super_client, make_expense,
    ):
        from content.models import ExpenseRecord

        make_expense(category=ExpenseRecord.Category.BUSINESS,
                     period_date=date(2026, 1, 1),
                     total_amount=Decimal('120000.00'))
        make_expense(category=ExpenseRecord.Category.PERSONAL,
                     period_date=date(2026, 1, 1),
                     total_amount=Decimal('30000.00'))
        make_expense(category=ExpenseRecord.Category.BUSINESS,
                     period_date=date(2026, 2, 1),
                     total_amount=Decimal('80000.00'))

        response = super_client.get('/api/accounting/stats/?year=2026')
        by_category = response.data['expenses']['by_category']
        assert [row['category'] for row in by_category] == ['business', 'personal']
        assert by_category[0]['label'] == 'Negocio'
        assert by_category[0]['total'] == Decimal('200000.00')
        assert by_category[0]['count'] == 2
        assert by_category[1]['total'] == Decimal('30000.00')
        summary = response.data['expenses']['summary']
        assert summary['count'] == 3
        assert summary['total'] == Decimal('230000.00')
