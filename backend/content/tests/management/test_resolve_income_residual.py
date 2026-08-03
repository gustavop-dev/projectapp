"""Tests for the resolve_income_residual command.

The scenario it exists for: an old partial collection (before the settlement
flow) left a gateway-fee-sized residual that will never arrive.
"""
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from content.models import ExpenseRecord, IncomeRecord

pytestmark = pytest.mark.django_db


def make_partial(total='86400.00', paid='81546.00'):
    income = IncomeRecord.objects.create(
        concept='Jimmy & Daniel - Hosting, Junio',
        kind=IncomeRecord.Kind.EXPECTED,
        period_date='2026-06-01',
        total_amount=Decimal(total),
        gustavo_amount=Decimal(total) / 2,
        carlos_amount=Decimal(total) / 2,
    )
    if Decimal(paid) > 0:
        IncomeRecord.objects.create(
            concept='Abono previo',
            kind=IncomeRecord.Kind.LIQUID,
            period_date='2026-06-15',
            total_amount=Decimal(paid),
            gustavo_amount=Decimal(paid) / 2,
            carlos_amount=Decimal(paid) / 2,
            expected_income=income,
        )
    return income


def run(*args):
    out = StringIO()
    call_command('resolve_income_residual', *args, stdout=out)
    return out.getvalue()


class TestResolveIncomeResidual:
    def test_dry_run_writes_nothing(self):
        income = make_partial()

        output = run('--income-id', str(income.pk))

        assert 'Dry-run' in output
        assert 'Pendiente:      4854.00' in output
        assert not ExpenseRecord.objects.exists()
        income.refresh_from_db()
        assert income.total_amount == Decimal('86400.00')

    def test_apply_books_the_pending_as_a_deduction_and_closes_the_income(self):
        income = make_partial()

        run('--income-id', str(income.pk), '--apply')

        expense = ExpenseRecord.objects.get()
        assert expense.deduction_type == ExpenseRecord.DeductionType.GATEWAY_FEE
        assert expense.total_amount == Decimal('4854.00')
        assert expense.concept == (
            'Comisión plataforma de pago — Jimmy & Daniel - Hosting, Junio'
        )
        assert expense.pocket_movement_id is None
        assert expense.source_ref == f'income:{income.pk}:settlement'
        assert expense.source_income_id == income.pk
        income.refresh_from_db()
        # Parent stays gross; the fee credits the difference → status paid.
        assert income.total_amount == Decimal('86400.00')
        # No liquid child was invented for the zero received.
        assert income.liquid_records.count() == 1

    def test_rerun_is_a_noop_once_settled(self):
        income = make_partial()
        run('--income-id', str(income.pk), '--apply')

        output = run('--income-id', str(income.pk), '--apply')

        assert 'nada que resolver' in output
        assert ExpenseRecord.objects.count() == 1

    def test_defaults_the_period_to_the_parent_month_and_accepts_an_override(
        self,
    ):
        june = make_partial()
        run('--income-id', str(june.pk), '--apply')
        assert str(ExpenseRecord.objects.get().period_date) == '2026-06-01'

        ExpenseRecord.objects.all().delete()
        july = IncomeRecord.objects.create(
            concept='Jimmy & Daniel - Hosting, Julio',
            kind=IncomeRecord.Kind.EXPECTED,
            period_date='2026-07-01',
            total_amount=Decimal('4854.00'),
            gustavo_amount=Decimal('2427.00'),
            carlos_amount=Decimal('2427.00'),
        )
        run('--income-id', str(july.pk), '--period', '2026-08', '--apply')
        assert str(ExpenseRecord.objects.get().period_date) == '2026-08-01'

    def test_rejects_a_non_expected_income(self):
        liquid = IncomeRecord.objects.create(
            concept='Pago suelto',
            kind=IncomeRecord.Kind.LIQUID,
            period_date='2026-06-01',
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('50.00'),
            carlos_amount=Decimal('50.00'),
        )

        with pytest.raises(CommandError, match='ingreso esperado'):
            run('--income-id', str(liquid.pk))
