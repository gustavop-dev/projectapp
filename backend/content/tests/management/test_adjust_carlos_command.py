"""Tests for the one-off adjust_carlos_opening_balance command."""
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from content.management.commands.adjust_carlos_opening_balance import (
    CONCEPT,
    DEFAULT_SOURCE_REF,
)
from content.models import ExpenseRecord, IncomeRecord, PocketMovement
from content.services import accounting_service
from content.utils import today_bogota


def _seed(carlos_liquid='1000000.00', pocket_in='1000000.00'):
    """Company liquid income split to Carlos + a manual pocket IN movement."""
    period = today_bogota().replace(day=1)
    IncomeRecord.objects.create(
        concept='Proyecto X - Entrega',
        kind=IncomeRecord.Kind.LIQUID,
        period_date=period,
        total_amount=Decimal(carlos_liquid) * 2,
        gustavo_amount=Decimal(carlos_liquid),
        carlos_amount=Decimal(carlos_liquid),
    )
    PocketMovement.objects.create(
        concept='Fondo inicial',
        movement_date=period,
        direction=PocketMovement.Direction.IN,
        amount=Decimal(pocket_in),
    )


def _run(*args):
    out = StringIO()
    call_command('adjust_carlos_opening_balance', *args, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
class TestAdjustCarlosCommand:
    def test_dry_run_writes_nothing(self):
        _seed()
        output = _run('--dry-run')
        assert 'Dry-run' in output
        assert not ExpenseRecord.objects.exists()

    def test_apply_leaves_carlos_at_half_the_pocket(self):
        _seed()  # carlos net 1,000,000 / pocket 1,000,000 -> target 500,000
        _run()
        expense = ExpenseRecord.objects.get()
        assert expense.concept == CONCEPT
        assert expense.ledger == 'carlos'
        assert expense.category == ExpenseRecord.Category.PERSONAL
        assert expense.total_amount == Decimal('500000.00')
        assert expense.carlos_amount == Decimal('500000.00')
        assert expense.source_ref == DEFAULT_SOURCE_REF

    def test_apply_updates_partner_net_and_reports_the_target(self):
        _seed()
        output = _run()
        summary = accounting_service.dashboard_summary(today_bogota().year)
        assert summary['partners']['carlos']['net'] == Decimal('500000.00')
        assert 'mitad del bolsillo' in output

    def test_rerun_aborts_via_source_ref(self):
        _seed()
        _run()
        with pytest.raises(CommandError, match='source_ref'):
            _run()
        assert ExpenseRecord.objects.count() == 1

    def test_adjustment_expense_never_touches_the_pocket(self):
        _seed()
        _run()
        assert PocketMovement.objects.count() == 1  # only the seeded IN

    def test_aborts_when_net_already_at_or_below_target(self):
        # Carlos net 100,000 vs pocket 1,000,000 -> target 500,000: no-op.
        _seed(carlos_liquid='100000.00')
        with pytest.raises(CommandError, match='menor o igual'):
            _run()
        assert not ExpenseRecord.objects.exists()
