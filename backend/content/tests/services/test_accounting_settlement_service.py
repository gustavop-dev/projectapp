"""Settling an expected income collected short.

The governing arithmetic (see the service docstring):

    received + deductions + follow_ups + unassigned = pending
    new parent total = old total - deductions - follow_ups
"""
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import AccountingChangeLog, ExpenseRecord, IncomeRecord
from content.services import accounting_service, accounting_settlement_service

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify') as notify:
        yield notify


def make_expected(**overrides):
    fields = {
        'concept': 'Kore - Inicio 40%',
        'kind': IncomeRecord.Kind.EXPECTED,
        'period_date': '2026-07-01',
        'total_amount': Decimal('1000000.00'),
        'gustavo_amount': Decimal('500000.00'),
        'carlos_amount': Decimal('500000.00'),
    }
    fields.update(overrides)
    return IncomeRecord.objects.create(**fields)


def settlement(**overrides):
    data = {
        'concept': 'Kore - Inicio 40%',
        'period_date': '2026-07-15',
        'destination': IncomeRecord.Destination.PARTNERS,
        'total_amount': Decimal('992000.00'),
        'notes': '',
        'deductions': [],
        'expected_incomes': [],
    }
    data.update(overrides)
    return data


def gateway_fee(amount='8000.00'):
    return {
        'type': ExpenseRecord.DeductionType.GATEWAY_FEE,
        'detail': '',
        'amount': Decimal(amount),
    }


class TestNoAllocations:
    """With nothing to allocate the flow must behave exactly like today."""

    def test_leaves_the_parent_untouched(self, superuser):
        income = make_expected()

        result = accounting_settlement_service.settle_expected_income(
            income, settlement(total_amount=Decimal('1000000.00')), superuser,
        )

        income.refresh_from_db()
        assert income.total_amount == Decimal('1000000.00')
        assert result['liquid'].kind == IncomeRecord.Kind.LIQUID
        assert result['liquid'].expected_income_id == income.pk
        assert result['expenses'] == []
        assert result['expected_incomes'] == []

    def test_sends_exactly_one_email(self, superuser, _mute_notifications):
        income = make_expected()

        # 942.000 received + 8.000 fee + 50.000 rescheduled = 1.000.000
        accounting_settlement_service.settle_expected_income(
            income,
            settlement(
                total_amount=Decimal('942000.00'),
                deductions=[gateway_fee()],
                expected_incomes=[{
                    'concept': 'Kore - Saldo',
                    'period_date': '2026-08-01',
                    'amount': Decimal('50000.00'),
                }],
            ),
            superuser,
        )

        # Four records are written but the settlement is one user action.
        assert _mute_notifications.call_count == 1


class TestDeduction:
    def test_closes_the_parent_and_books_the_fee(self, superuser):
        income = make_expected()

        result = accounting_settlement_service.settle_expected_income(
            income, settlement(deductions=[gateway_fee()]), superuser,
        )

        income.refresh_from_db()
        assert income.total_amount == Decimal('992000.00')
        # Nothing left pending: 992.000 received against a 992.000 expected.
        assert income.total_amount == result['liquid'].total_amount

        expense = result['expenses'][0]
        assert expense.deduction_type == ExpenseRecord.DeductionType.GATEWAY_FEE
        assert expense.total_amount == Decimal('8000.00')
        assert expense.concept == 'Comisión plataforma de pago — Kore - Inicio 40%'
        assert expense.source_ref == f'income:{income.pk}:settlement'

    def test_never_touches_the_pocket(self, superuser):
        """That money was discounted before the transfer ever arrived."""
        income = make_expected()

        result = accounting_settlement_service.settle_expected_income(
            income, settlement(deductions=[gateway_fee()]), superuser,
        )

        assert result['expenses'][0].pocket_movement_id is None

    def test_other_uses_the_free_text_as_concept(self, superuser):
        income = make_expected()

        result = accounting_settlement_service.settle_expected_income(
            income,
            settlement(deductions=[{
                'type': ExpenseRecord.DeductionType.OTHER,
                'detail': 'Descuento pactado',
                'amount': Decimal('8000.00'),
            }]),
            superuser,
        )

        assert result['expenses'][0].concept.startswith('Descuento pactado —')

    def test_several_deductions_in_one_settlement(self, superuser):
        """A single payment can carry a fee AND a withholding."""
        income = make_expected()

        result = accounting_settlement_service.settle_expected_income(
            income,
            settlement(
                total_amount=Decimal('900000.00'),
                deductions=[
                    gateway_fee('30000.00'),
                    {
                        'type': ExpenseRecord.DeductionType.WITHHOLDING,
                        'detail': '',
                        'amount': Decimal('70000.00'),
                    },
                ],
            ),
            superuser,
        )

        income.refresh_from_db()
        assert len(result['expenses']) == 2
        assert income.total_amount == Decimal('900000.00')


class TestFollowUpExpectedIncomes:
    def test_reschedules_the_balance_and_shrinks_the_parent(self, superuser):
        income = make_expected()

        result = accounting_settlement_service.settle_expected_income(
            income,
            settlement(
                total_amount=Decimal('900000.00'),
                deductions=[gateway_fee()],
                expected_incomes=[{
                    'concept': 'Kore - Saldo agosto',
                    'period_date': '2026-08',
                    'amount': Decimal('92000.00'),
                }],
            ),
            superuser,
        )

        income.refresh_from_db()
        follow_up = result['expected_incomes'][0]
        assert income.total_amount == Decimal('900000.00')
        assert follow_up.kind == IncomeRecord.Kind.EXPECTED
        assert follow_up.total_amount == Decimal('92000.00')
        assert str(follow_up.period_date) == '2026-08-01'
        # The three slices still add up to the original expected amount.
        assert (
            income.total_amount
            + result['expenses'][0].total_amount
            + follow_up.total_amount
        ) == Decimal('1000000.00')

    def test_inherits_ledger_and_destination(self, superuser):
        income = make_expected(destination=IncomeRecord.Destination.PARTNERS)

        result = accounting_settlement_service.settle_expected_income(
            income,
            settlement(expected_incomes=[{
                'concept': 'Saldo',
                'period_date': '2026-08',
                'amount': Decimal('8000.00'),
            }]),
            superuser,
        )

        follow_up = result['expected_incomes'][0]
        assert follow_up.ledger == income.ledger
        assert follow_up.destination == income.destination

    def test_more_than_one_follow_up(self, superuser):
        income = make_expected()

        result = accounting_settlement_service.settle_expected_income(
            income,
            settlement(
                total_amount=Decimal('500000.00'),
                expected_incomes=[
                    {'concept': 'Cuota 2', 'period_date': '2026-08',
                     'amount': Decimal('250000.00')},
                    {'concept': 'Cuota 3', 'period_date': '2026-09',
                     'amount': Decimal('250000.00')},
                ],
            ),
            superuser,
        )

        income.refresh_from_db()
        assert len(result['expected_incomes']) == 2
        assert income.total_amount == Decimal('500000.00')


class TestPartialAllocation:
    def test_unassigned_balance_stays_pending(self, superuser):
        """Not deciding yet is still allowed — the rest simply stays open."""
        income = make_expected()

        accounting_settlement_service.settle_expected_income(
            income,
            settlement(
                total_amount=Decimal('900000.00'),
                deductions=[gateway_fee()],
            ),
            superuser,
        )

        income.refresh_from_db()
        # Parent drops only by what was moved out (the 8.000 fee).
        assert income.total_amount == Decimal('992000.00')
        # 992.000 expected − 900.000 received = 92.000 still pending.
        assert income.total_amount - Decimal('900000.00') == Decimal('92000.00')

    def test_settling_a_partially_collected_record(self, superuser):
        income = make_expected()
        IncomeRecord.objects.create(
            concept='Abono previo',
            kind=IncomeRecord.Kind.LIQUID,
            period_date='2026-07-05',
            total_amount=Decimal('600000.00'),
            gustavo_amount=Decimal('300000.00'),
            carlos_amount=Decimal('300000.00'),
            expected_income=income,
        )

        accounting_settlement_service.settle_expected_income(
            income,
            settlement(
                total_amount=Decimal('390000.00'),
                deductions=[gateway_fee('10000.00'),],
            ),
            superuser,
        )

        income.refresh_from_db()
        assert income.total_amount == Decimal('990000.00')
        # 600.000 + 390.000 collected against a 990.000 expected → closed.


class TestPartnerSplit:
    def test_follow_up_keeps_the_parent_ratio(self, superuser):
        income = make_expected(
            gustavo_amount=Decimal('600000.00'),
            carlos_amount=Decimal('400000.00'),
        )

        result = accounting_settlement_service.settle_expected_income(
            income,
            settlement(
                total_amount=Decimal('900000.00'),
                expected_incomes=[{
                    'concept': 'Saldo',
                    'period_date': '2026-08',
                    'amount': Decimal('100000.00'),
                }],
            ),
            superuser,
        )

        follow_up = result['expected_incomes'][0]
        assert follow_up.gustavo_amount == Decimal('60000.00')
        assert follow_up.carlos_amount == Decimal('40000.00')

    def test_parent_split_is_rescaled_when_reduced(self, superuser):
        income = make_expected(
            gustavo_amount=Decimal('600000.00'),
            carlos_amount=Decimal('400000.00'),
        )

        accounting_settlement_service.settle_expected_income(
            income,
            settlement(deductions=[gateway_fee()]), superuser,
        )

        income.refresh_from_db()
        assert income.total_amount == Decimal('992000.00')
        assert income.gustavo_amount == Decimal('595200.00')
        assert income.carlos_amount == Decimal('396800.00')

    def test_split_never_exceeds_the_amount_on_odd_cents(self, superuser):
        income = make_expected(
            total_amount=Decimal('1000.00'),
            gustavo_amount=Decimal('333.33'),
            carlos_amount=Decimal('666.67'),
        )

        result = accounting_settlement_service.settle_expected_income(
            income,
            settlement(
                total_amount=Decimal('900.01'),
                expected_incomes=[{
                    'concept': 'Saldo',
                    'period_date': '2026-08',
                    'amount': Decimal('99.99'),
                }],
            ),
            superuser,
        )

        follow_up = result['expected_incomes'][0]
        assert (
            follow_up.gustavo_amount + follow_up.carlos_amount
            <= follow_up.total_amount
        )


class TestValidation:
    def test_rejects_allocations_above_the_pending_balance(self, superuser):
        income = make_expected()

        with pytest.raises(ValueError, match='no puede superar el saldo'):
            accounting_settlement_service.settle_expected_income(
                income,
                settlement(deductions=[gateway_fee('50000.00')]),
                superuser,
            )

    def test_rejects_a_non_expected_record(self, superuser):
        liquid = make_expected(kind=IncomeRecord.Kind.LIQUID)

        with pytest.raises(ValueError, match='ingreso esperado'):
            accounting_settlement_service.settle_expected_income(
                liquid, settlement(), superuser,
            )

    def test_rejects_a_zero_payment(self, superuser):
        income = make_expected()

        with pytest.raises(ValueError, match='mayor a cero'):
            accounting_settlement_service.settle_expected_income(
                income, settlement(total_amount=Decimal('0')), superuser,
            )

    def test_rejects_an_already_paid_record(self, superuser):
        income = make_expected()
        IncomeRecord.objects.create(
            concept='Pago total',
            kind=IncomeRecord.Kind.LIQUID,
            period_date='2026-07-05',
            total_amount=Decimal('1000000.00'),
            gustavo_amount=Decimal('500000.00'),
            carlos_amount=Decimal('500000.00'),
            expected_income=income,
        )

        with pytest.raises(ValueError, match='completamente pagado'):
            accounting_settlement_service.settle_expected_income(
                income, settlement(), superuser,
            )

    def test_nothing_is_written_when_validation_fails(self, superuser):
        income = make_expected()
        before = ExpenseRecord.objects.count()

        with pytest.raises(ValueError):
            accounting_settlement_service.settle_expected_income(
                income,
                settlement(deductions=[gateway_fee('50000.00')]),
                superuser,
            )

        income.refresh_from_db()
        assert ExpenseRecord.objects.count() == before
        assert income.total_amount == Decimal('1000000.00')


class TestAudit:
    def test_every_record_is_audited(self, superuser):
        income = make_expected()

        accounting_settlement_service.settle_expected_income(
            income,
            settlement(
                total_amount=Decimal('900000.00'),
                deductions=[gateway_fee()],
                expected_incomes=[{
                    'concept': 'Saldo',
                    'period_date': '2026-08',
                    'amount': Decimal('92000.00'),
                }],
            ),
            superuser,
        )

        actions = AccountingChangeLog.objects.values_list(
            'entity_type', 'action',
        )
        assert (
            AccountingChangeLog.EntityType.EXPENSE,
            AccountingChangeLog.Action.CREATED,
        ) in actions
        assert (
            AccountingChangeLog.EntityType.INCOME,
            AccountingChangeLog.Action.UPDATED,
        ) in actions


class TestUtilityImpact:
    def test_a_deduction_does_not_move_utility(self, superuser):
        """The money is already absent from the liquid total.

        Subtracting it as an expense too would count the same loss twice.
        """
        income = make_expected()
        accounting_settlement_service.settle_expected_income(
            income, settlement(deductions=[gateway_fee()]), superuser,
        )

        totals = accounting_service.year_totals(2026)

        assert totals['liquid_total'] == Decimal('992000.00')
        assert totals['expenses_total'] == Decimal('0')
        assert totals['deductions_total'] == Decimal('8000.00')
        assert totals['liquid_utility'] == Decimal('992000.00')

    def test_an_ordinary_expense_still_reduces_utility(self, superuser):
        income = make_expected()
        accounting_settlement_service.settle_expected_income(
            income, settlement(deductions=[gateway_fee()]), superuser,
        )
        ExpenseRecord.objects.create(
            concept='Hosting',
            period_date='2026-07-01',
            total_amount=Decimal('100000.00'),
            gustavo_amount=Decimal('50000.00'),
            carlos_amount=Decimal('50000.00'),
        )

        totals = accounting_service.year_totals(2026)

        assert totals['expenses_total'] == Decimal('100000.00')
        assert totals['liquid_utility'] == Decimal('892000.00')
