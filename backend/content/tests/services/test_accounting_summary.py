"""Aggregation tests for accounting_service (dashboard, pocket, ads)."""
from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from content.models import (
    AdsSpendRecord,
    CardBalanceSnapshot,
    CreditCard,
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

    def test_partner_totals_company_card_is_full_company_ledger(
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
        # The company card is the company ledger itself, not the residue.
        assert partners['company']['liquid'] == Decimal('100.00')
        assert partners['company']['expenses'] == Decimal('20.00')
        assert partners['company']['net'] == Decimal('80.00')

    def test_pocket_draw_counts_against_company_utility(
        self, superuser, make_income,
    ):
        # A pocket egreso attributed to a partner is a company draw: it
        # must reduce liquid_utility and the partner's participation —
        # never land on his personal ledger (that would drain the pocket
        # while the utility stays intact).
        from unittest.mock import patch

        from content.models import AccountingChangeLog
        from content.serializers.accounting import (
            PocketMovementCreateUpdateSerializer,
        )

        make_income(kind='liquid', total_amount=Decimal('1000.00'))
        serializer = PocketMovementCreateUpdateSerializer(data={
            'concept': 'Gasolina', 'movement_date': '2026-07-17',
            'direction': 'out', 'amount': '200.00', 'ledger': 'gustavo',
        })
        assert serializer.is_valid(), serializer.errors
        with patch.object(accounting_service, '_notify'):
            accounting_service.create_record(
                AccountingChangeLog.EntityType.POCKET, serializer, superuser,
            )

        summary = accounting_service.dashboard_summary(2026)
        assert summary['expenses_total'] == Decimal('200.00')
        assert summary['liquid_utility'] == Decimal('800.00')
        assert summary['partners']['gustavo']['expenses'] == Decimal('200.00')
        assert summary['partners']['gustavo']['personal']['expenses'] == (
            Decimal('0')
        )
        assert accounting_service.pocket_balance() == Decimal('-200.00')

    def test_personal_records_excluded_from_company_totals(
        self, make_income, make_expense,
    ):
        make_income(
            kind='liquid',
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('50.00'),
            carlos_amount=Decimal('50.00'),
        )
        make_income(
            kind='liquid',
            ledger=IncomeRecord.Ledger.GUSTAVO,
            total_amount=Decimal('40.00'),
            gustavo_amount=Decimal('40.00'),
            carlos_amount=Decimal('0.00'),
        )
        make_expense(
            ledger=IncomeRecord.Ledger.CARLOS,
            total_amount=Decimal('15.00'),
            gustavo_amount=Decimal('0.00'),
            carlos_amount=Decimal('15.00'),
        )
        summary = accounting_service.dashboard_summary(2026)
        assert summary['liquid_total'] == Decimal('100.00')
        assert summary['expenses_total'] == Decimal('0')
        assert summary['liquid_utility'] == Decimal('100.00')
        march = summary['monthly'][2]
        assert march['liquid'] == Decimal('100.00')
        assert march['expenses'] == Decimal('0')
        assert summary['partners']['company']['net'] == Decimal('100.00')

    def test_partner_net_combines_participation_and_personal(
        self, make_income, make_expense,
    ):
        make_income(
            kind='liquid',
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('50.00'),
            carlos_amount=Decimal('50.00'),
        )
        make_income(
            kind='liquid',
            ledger=IncomeRecord.Ledger.GUSTAVO,
            total_amount=Decimal('40.00'),
            gustavo_amount=Decimal('40.00'),
            carlos_amount=Decimal('0.00'),
        )
        make_expense(
            ledger=IncomeRecord.Ledger.GUSTAVO,
            total_amount=Decimal('25.00'),
            gustavo_amount=Decimal('25.00'),
            carlos_amount=Decimal('0.00'),
        )
        make_expense(
            total_amount=Decimal('10.00'),
            gustavo_amount=Decimal('5.00'),
            carlos_amount=Decimal('5.00'),
        )
        partners = accounting_service.partner_totals(2026)
        gustavo = partners['gustavo']
        assert gustavo['liquid'] == Decimal('90.00')
        assert gustavo['expenses'] == Decimal('30.00')
        assert gustavo['net'] == Decimal('60.00')
        assert gustavo['participation']['liquid'] == Decimal('50.00')
        assert gustavo['personal']['liquid'] == Decimal('40.00')
        assert gustavo['personal']['expenses'] == Decimal('25.00')
        carlos = partners['carlos']
        assert carlos['net'] == Decimal('45.00')
        assert carlos['personal']['liquid'] == Decimal('0')


@pytest.mark.django_db
@freeze_time('2026-07-13 12:00:00')
class TestExpectedCurrentMonth:
    def test_sums_only_company_expected_income_of_the_current_month(
        self, make_income,
    ):
        make_income(
            kind='expected',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('600.00'),
        )
        make_income(
            kind='expected',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('400.00'),
        )
        # Liquid, another month and a personal ledger must not count.
        make_income(
            kind='liquid',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('900.00'),
        )
        make_income(
            kind='expected',
            period_date=date(2026, 6, 1),
            total_amount=Decimal('700.00'),
        )
        make_income(
            kind='expected',
            period_date=date(2026, 7, 1),
            ledger=IncomeRecord.Ledger.GUSTAVO,
            total_amount=Decimal('50.00'),
            gustavo_amount=Decimal('50.00'),
            carlos_amount=Decimal('0.00'),
        )

        current = accounting_service.expected_current_month()
        assert current['period'] == '2026-07'
        assert current['label'] == 'Julio 2026'
        assert current['total'] == Decimal('1000.00')

    def test_ignores_the_dashboard_year_selector(self, make_income):
        make_income(
            kind='expected',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('1000.00'),
        )
        summary = accounting_service.dashboard_summary(2025)
        assert summary['year'] == 2025
        assert summary['expected_total'] == Decimal('0')
        assert summary['expected_current_month']['total'] == Decimal('1000.00')
        assert summary['expected_current_month']['period'] == '2026-07'

    def test_no_expected_income_this_month_is_zero(self, make_income):
        make_income(
            kind='expected',
            period_date=date(2026, 6, 1),
            total_amount=Decimal('700.00'),
        )
        assert accounting_service.expected_current_month()['total'] == Decimal('0')

    def test_fully_paid_expected_income_no_longer_counts_as_pending(
        self, make_income,
    ):
        expected = make_income(
            kind='expected',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('1000.00'),
        )
        make_income(
            kind='liquid',
            period_date=date(2026, 9, 1),
            total_amount=Decimal('1000.00'),
            expected_income=expected,
        )
        assert accounting_service.expected_current_month()['total'] == Decimal('0')

    def test_partially_paid_expected_income_counts_only_the_remainder(
        self, make_income,
    ):
        expected = make_income(
            kind='expected',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('1000.00'),
        )
        make_income(
            kind='liquid',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('400.00'),
            expected_income=expected,
        )
        assert accounting_service.expected_current_month()['total'] == Decimal(
            '600.00',
        )

    def test_overpaid_record_clamps_to_zero_without_eating_a_pending_sibling(
        self, make_income,
    ):
        """Per-row clamping: a naive Sum(total - paid) would report 200.00."""
        overpaid = make_income(
            kind='expected',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('100.00'),
        )
        make_income(
            kind='liquid',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('900.00'),
            expected_income=overpaid,
        )
        make_income(
            kind='expected',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('1000.00'),
        )
        assert accounting_service.expected_current_month()['total'] == Decimal(
            '1000.00',
        )

    def test_a_lost_child_does_not_count_as_payment(self, make_income):
        expected = make_income(
            kind='expected',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('1000.00'),
        )
        make_income(
            kind='lost',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('1000.00'),
            expected_income=expected,
        )
        assert accounting_service.expected_current_month()['total'] == Decimal(
            '1000.00',
        )

    def test_paid_income_leaves_the_projection_totals_untouched(
        self, make_income,
    ):
        """Only the current-month card nets out payments.

        `expected_total`, `difference` and the monthly breakdown keep the
        full projection — that is what makes expected-vs-liquid meaningful.
        """
        expected = make_income(
            kind='expected',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('1000.00'),
        )
        make_income(
            kind='liquid',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('1000.00'),
            expected_income=expected,
        )
        summary = accounting_service.dashboard_summary(2026)
        assert summary['expected_total'] == Decimal('1000.00')
        assert summary['liquid_total'] == Decimal('1000.00')
        assert summary['difference'] == Decimal('0')
        july = summary['monthly'][6]
        assert july['expected'] == Decimal('1000.00')
        assert summary['expected_current_month']['total'] == Decimal('0')

    def test_lost_income_stays_out_of_every_dashboard_total(self, make_income):
        make_income(
            kind='lost',
            period_date=date(2026, 7, 1),
            total_amount=Decimal('460000.00'),
        )
        summary = accounting_service.dashboard_summary(2026)
        assert summary['expected_total'] == Decimal('0')
        assert summary['liquid_total'] == Decimal('0')
        assert summary['expected_utility'] == Decimal('0')
        assert summary['liquid_utility'] == Decimal('0')
        assert summary['monthly'][6]['expected'] == Decimal('0')


@pytest.mark.django_db
class TestCardDebtTotal:
    @pytest.fixture(autouse=True)
    def empty_catalog(self):
        """Migration 0158 seeds 'T.C 0064'; each test declares its own cupo."""
        CreditCard.objects.all().delete()

    def test_sums_latest_snapshot_per_card_and_uses_active_catalog_cupo(self):
        CreditCard.objects.create(
            name='T.C 0064', credit_limit=Decimal('8000000.00'), is_active=True,
        )
        CreditCard.objects.create(
            name='T.C 9999', credit_limit=Decimal('2000000.00'), is_active=True,
        )
        CreditCard.objects.create(
            name='T.C Vieja', credit_limit=Decimal('5000000.00'), is_active=False,
        )
        # Older snapshot for the same card must be ignored.
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
        CardBalanceSnapshot.objects.create(
            snapshot_date=date(2026, 7, 2), card_name='T.C 9999',
            available_amount=Decimal('1150000.00'),
            debt_amount=Decimal('850000.00'),
        )

        debt = accounting_service.card_debt_total()
        assert debt['total'] == Decimal('5000954.00')
        assert debt['card_count'] == 2
        # The inactive card's cupo is out: 8.000.000 + 2.000.000.
        assert debt['credit_limit_total'] == Decimal('10000000.00')
        assert debt['utilization_pct'] == 50.0

    def test_utilization_is_none_without_an_active_catalog(self):
        CardBalanceSnapshot.objects.create(
            snapshot_date=date(2026, 7, 1), card_name='T.C Suelta',
            available_amount=Decimal('0.00'),
            debt_amount=Decimal('300000.00'),
        )
        debt = accounting_service.card_debt_total()
        assert debt['total'] == Decimal('300000.00')
        assert debt['card_count'] == 1
        assert debt['utilization_pct'] is None

    def test_no_snapshots_is_zero_debt(self):
        CreditCard.objects.create(
            name='T.C 0064', credit_limit=Decimal('8000000.00'), is_active=True,
        )
        debt = accounting_service.card_debt_total()
        assert debt['total'] == Decimal('0')
        assert debt['card_count'] == 0
        assert debt['utilization_pct'] == 0.0


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
