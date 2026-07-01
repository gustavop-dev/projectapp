"""Aggregation tests for accounting_service (dashboard, pocket, ads)."""
from datetime import date
from decimal import Decimal

import pytest

from content.models import (
    AdsSpendRecord,
    CardBalanceSnapshot,
    HostingRecord,
    IncomeRecord,
    PocketMovement,
    RecurringPayment,
)
from content.services import accounting_service


def movement(concept, day, direction, amount):
    return PocketMovement.objects.create(
        concept=concept,
        movement_date=day,
        direction=direction,
        amount=Decimal(amount),
    )


@pytest.mark.django_db
class TestPocketBalance:
    def test_balance_is_inflow_minus_outflow(self):
        movement('Ingreso A', date(2026, 4, 29), 'in', '2123000.00')
        movement('Gasto B', date(2026, 5, 6), 'out', '2272000.00')
        movement('Ingreso C', date(2026, 5, 7), 'in', '1592250.00')
        assert accounting_service.pocket_balance() == Decimal('1443250.00')

    def test_balance_respects_as_of_date(self):
        movement('Ingreso A', date(2026, 4, 29), 'in', '100.00')
        movement('Gasto B', date(2026, 5, 6), 'out', '40.00')
        assert accounting_service.pocket_balance(
            as_of=date(2026, 4, 30),
        ) == Decimal('100.00')


@pytest.mark.django_db
class TestDashboardSummary:
    def test_totals_difference_and_utilities(self, make_income, make_expense):
        make_income(kind='expected', total_amount=Decimal('1000.00'))
        make_income(kind='expected', total_amount=Decimal('500.00'))
        make_income(kind='liquid', total_amount=Decimal('900.00'))
        make_expense(total_amount=Decimal('300.00'))

        summary = accounting_service.dashboard_summary(2026)
        assert summary['expected_total'] == Decimal('1500.00')
        assert summary['liquid_total'] == Decimal('900.00')
        assert summary['difference'] == Decimal('-600.00')
        assert summary['expenses_total'] == Decimal('300.00')
        assert summary['expected_utility'] == Decimal('1200.00')
        assert summary['liquid_utility'] == Decimal('600.00')

    def test_other_years_are_excluded(self, make_income):
        make_income(
            kind='expected',
            period_date=date(2025, 12, 1),
            total_amount=Decimal('999.00'),
        )
        summary = accounting_service.dashboard_summary(2026)
        assert summary['expected_total'] == Decimal('0')

    def test_hostings_meta_counts_active_only(self):
        HostingRecord.objects.create(
            client_name='A', monthly_value=Decimal('100.00'),
            total_paid=Decimal('50.00'), is_active=True,
        )
        HostingRecord.objects.create(
            client_name='B', monthly_value=Decimal('200.00'),
            total_paid=Decimal('70.00'), is_active=False,
        )
        summary = accounting_service.dashboard_summary(2026)
        assert summary['hostings']['active_count'] == 1
        assert summary['hostings']['monthly_income'] == Decimal('100.00')
        assert summary['hostings']['total_paid'] == Decimal('120.00')


@pytest.mark.django_db
class TestMonthlyAndPartners:
    def test_monthly_breakdown_buckets_by_month(
        self, make_income, make_expense,
    ):
        make_income(
            kind='expected',
            period_date=date(2026, 3, 1),
            total_amount=Decimal('600.00'),
        )
        make_income(
            kind='expected',
            period_date=date(2026, 3, 1),
            total_amount=Decimal('400.00'),
        )
        make_income(
            kind='liquid',
            period_date=date(2026, 3, 1),
            total_amount=Decimal('800.00'),
        )
        make_expense(
            period_date=date(2026, 3, 1), total_amount=Decimal('300.00'),
        )
        breakdown = accounting_service.monthly_breakdown(2026)
        assert len(breakdown) == 12
        march = breakdown[2]
        assert march['period'] == '2026-03'
        assert march['label'] == 'Marzo 2026'
        assert march['expected'] == Decimal('1000.00')
        assert march['liquid'] == Decimal('800.00')
        assert march['expenses'] == Decimal('300.00')
        assert march['utility'] == Decimal('500.00')

    def test_partner_totals_include_company_share(
        self, make_income, make_expense,
    ):
        make_income(
            kind='liquid',
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('30.00'),
            carlos_amount=Decimal('30.00'),
        )
        make_expense(
            total_amount=Decimal('20.00'),
            gustavo_amount=Decimal('10.00'),
            carlos_amount=Decimal('10.00'),
        )
        partners = accounting_service.partner_totals(2026)
        assert partners['gustavo']['liquid'] == Decimal('30.00')
        assert partners['gustavo']['net'] == Decimal('20.00')
        assert partners['company']['liquid'] == Decimal('40.00')
        assert partners['company']['expenses'] == Decimal('0.00')


@pytest.mark.django_db
class TestAdsAndCards:
    def test_ads_running_accumulated_is_chronological(self):
        AdsSpendRecord.objects.create(
            spend_date=date(2026, 1, 25), amount=Decimal('143820.00'),
        )
        AdsSpendRecord.objects.create(
            spend_date=date(2026, 1, 17), amount=Decimal('146103.00'),
        )
        records = accounting_service.ads_with_accumulated(
            AdsSpendRecord.objects.all(),
        )
        assert records[0].spend_date == date(2026, 1, 17)
        assert records[0].accumulated == Decimal('146103.00')
        assert records[1].accumulated == Decimal('289923.00')

    def test_latest_card_snapshot_per_card(self):
        CardBalanceSnapshot.objects.create(
            snapshot_date=date(2026, 6, 17), card_name='T.C 0064',
            available_amount=Decimal('413226.00'),
            debt_amount=Decimal('7586774.00'),
        )
        CardBalanceSnapshot.objects.create(
            snapshot_date=date(2026, 7, 1), card_name='T.C 0064',
            available_amount=Decimal('3849046.00'),
            debt_amount=Decimal('4150954.00'),
        )
        snapshots = accounting_service.latest_card_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0]['snapshot_date'] == date(2026, 7, 1)
        assert snapshots[0]['available_amount'] == Decimal('3849046.00')

    def test_recurring_monthly_cost_ignores_inactive(self):
        RecurringPayment.objects.create(
            name='Claude Code 20x', price=Decimal('200.00'),
            currency='USD', cop_equivalent=Decimal('800000.00'),
            frequency='monthly', is_active=True,
        )
        RecurringPayment.objects.create(
            name='Figma', price=Decimal('40000.00'),
            cop_equivalent=Decimal('40000.00'),
            frequency='monthly', is_active=False,
        )
        assert accounting_service.recurring_monthly_cost() == Decimal('800000.00')
