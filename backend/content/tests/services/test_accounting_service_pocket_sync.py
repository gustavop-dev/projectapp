"""Income/Expense ↔ Pocket movement synchronization tests."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.api_errors import ProposalActionError
from content.models import (
    AccountingChangeLog,
    ExpenseRecord,
    IncomeRecord,
    PocketMovement,
)
from content.serializers.accounting import (
    ExpenseRecordCreateUpdateSerializer,
    IncomeRecordCreateUpdateSerializer,
    PocketMovementCreateUpdateSerializer,
)
from content.services import accounting_service

EntityType = AccountingChangeLog.EntityType
Action = AccountingChangeLog.Action


def make_serializer(cls, data, instance=None):
    serializer = cls(
        instance=instance, data=data, partial=instance is not None,
    )
    assert serializer.is_valid(), serializer.errors
    return serializer


def create_pocket_income(user, **overrides):
    data = {
        'concept': 'Vastago (Fase 1) - Inicio 40%',
        'kind': 'liquid',
        'destination': 'pocket',
        'period_date': '2026-04',
        'total_amount': '2123000.00',
    }
    data.update(overrides)
    with patch.object(accounting_service, '_notify'):
        return accounting_service.create_record(
            EntityType.INCOME,
            make_serializer(IncomeRecordCreateUpdateSerializer, data),
            user,
        )


def create_expense(user, **overrides):
    data = {
        'concept': 'Figma',
        'period_date': '2026-02',
        'total_amount': '80000.00',
    }
    data.update(overrides)
    with patch.object(accounting_service, '_notify'):
        return accounting_service.create_record(
            EntityType.EXPENSE,
            make_serializer(ExpenseRecordCreateUpdateSerializer, data),
            user,
        )


def create_movement(user, **overrides):
    data = {
        'concept': 'Pago dominio',
        'movement_date': '2026-04-17',
        'direction': 'out',
        'amount': '150000.00',
    }
    data.update(overrides)
    with patch.object(accounting_service, '_notify'):
        return accounting_service.create_record(
            EntityType.POCKET,
            make_serializer(PocketMovementCreateUpdateSerializer, data),
            user,
        )


def update_movement(user, movement, **data):
    serializer = make_serializer(
        PocketMovementCreateUpdateSerializer, data, instance=movement,
    )
    with patch.object(accounting_service, '_notify'):
        return accounting_service.update_record(
            EntityType.POCKET, movement, serializer, user,
        )


@pytest.mark.django_db
class TestIncomePocketSync:
    def test_liquid_pocket_income_creates_in_movement(self, superuser):
        income = create_pocket_income(superuser)
        movement = income.pocket_movement
        assert movement is not None
        assert movement.direction == PocketMovement.Direction.IN
        assert movement.amount == Decimal('2123000.00')
        assert movement.movement_date == income.period_date
        assert movement.concept == income.concept
        assert movement.is_auto_managed is True

    def test_income_creates_exactly_one_movement(self, superuser):
        create_pocket_income(superuser)
        assert PocketMovement.objects.count() == 1

    def test_amount_change_mirrors_into_movement(self, superuser):
        income = create_pocket_income(superuser)
        serializer = make_serializer(
            IncomeRecordCreateUpdateSerializer,
            {'total_amount': '2500000.00'},
            instance=income,
        )
        with patch.object(accounting_service, '_notify'):
            accounting_service.update_record(
                EntityType.INCOME, income, serializer, superuser,
            )
        income.pocket_movement.refresh_from_db()
        assert income.pocket_movement.amount == Decimal('2500000.00')

    def test_destination_flip_removes_movement(self, superuser):
        income = create_pocket_income(superuser)
        movement_pk = income.pocket_movement.pk
        serializer = make_serializer(
            IncomeRecordCreateUpdateSerializer,
            {'destination': 'partners'},
            instance=income,
        )
        with patch.object(accounting_service, '_notify'):
            accounting_service.update_record(
                EntityType.INCOME, income, serializer, superuser,
            )
        income.refresh_from_db()
        assert income.pocket_movement is None
        assert not PocketMovement.objects.filter(pk=movement_pk).exists()

    def test_writing_off_a_pocket_income_removes_its_movement(self, superuser):
        """kind=lost drops `wants_movement`, so the pocket side must unlink.

        The destination has to move back to partners in the same PATCH:
        pocket is liquid-only, which is exactly what the edit modal enforces.
        """
        income = create_pocket_income(superuser)
        movement_pk = income.pocket_movement.pk
        serializer = make_serializer(
            IncomeRecordCreateUpdateSerializer,
            {'kind': 'lost', 'destination': 'partners'},
            instance=income,
        )
        with patch.object(accounting_service, '_notify'):
            accounting_service.update_record(
                EntityType.INCOME, income, serializer, superuser,
            )
        income.refresh_from_db()
        assert income.kind == IncomeRecord.Kind.LOST
        assert income.pocket_movement is None
        assert not PocketMovement.objects.filter(pk=movement_pk).exists()

    def test_liquidating_an_expected_creates_no_movement_for_partners(
        self, superuser,
    ):
        expected = IncomeRecord.objects.create(
            concept='Kore - Inicio 40%',
            kind=IncomeRecord.Kind.EXPECTED,
            period_date=date(2026, 8, 1),
            total_amount=Decimal('1000000.00'),
        )
        serializer = make_serializer(
            IncomeRecordCreateUpdateSerializer,
            {
                'concept': 'Kore - Inicio 40%',
                'kind': 'liquid',
                'destination': 'partners',
                'period_date': '2026-11',
                'total_amount': '700000.00',
                'expected_income': expected.pk,
            },
        )
        with patch.object(accounting_service, '_notify'):
            liquid = accounting_service.create_record(
                EntityType.INCOME, serializer, superuser,
            )
        assert liquid.expected_income_id == expected.pk
        assert liquid.pocket_movement is None
        assert not PocketMovement.objects.exists()

    def test_income_delete_removes_linked_movement(self, superuser):
        income = create_pocket_income(superuser)
        movement_pk = income.pocket_movement.pk
        with patch.object(accounting_service, '_notify'):
            accounting_service.delete_record(
                EntityType.INCOME, income, superuser,
            )
        assert not PocketMovement.objects.filter(pk=movement_pk).exists()

    def test_auto_movement_lifecycle_is_audited(self, superuser):
        income = create_pocket_income(superuser)
        movement_pk = income.pocket_movement.pk
        assert AccountingChangeLog.objects.filter(
            entity_type=EntityType.POCKET,
            object_id=movement_pk,
            action=Action.CREATED,
        ).exists()


@pytest.mark.django_db
class TestExpensePocketSync:
    def test_expense_create_creates_linked_out_movement(self, superuser):
        expense = create_expense(superuser)
        movement = expense.pocket_movement
        assert movement is not None
        assert movement.direction == PocketMovement.Direction.OUT
        assert movement.amount == Decimal('80000.00')
        assert movement.concept == expense.concept
        assert movement.source_ref == f'expense:{expense.pk}'
        assert AccountingChangeLog.objects.filter(
            entity_type=EntityType.POCKET,
            object_id=movement.pk,
            action=Action.CREATED,
        ).exists()

    def test_historical_expense_update_creates_no_movement(
        self, superuser, make_expense,
    ):
        expense = make_expense()
        serializer = make_serializer(
            ExpenseRecordCreateUpdateSerializer,
            {'concept': 'Gasto histórico editado'},
            instance=expense,
        )
        with patch.object(accounting_service, '_notify'):
            accounting_service.update_record(
                EntityType.EXPENSE, expense, serializer, superuser,
            )
        assert PocketMovement.objects.count() == 0

    def test_unchecked_register_flag_skips_movement(self, superuser):
        expense = create_expense(superuser, register_in_pocket=False)
        assert expense.pocket_movement is None
        assert PocketMovement.objects.count() == 0

    def test_unchecking_flag_on_linked_expense_removes_movement(
        self, superuser,
    ):
        expense = create_expense(superuser)
        movement_pk = expense.pocket_movement.pk
        serializer = make_serializer(
            ExpenseRecordCreateUpdateSerializer,
            {'register_in_pocket': False},
            instance=expense,
        )
        with patch.object(accounting_service, '_notify'):
            accounting_service.update_record(
                EntityType.EXPENSE, expense, serializer, superuser,
            )
        expense.refresh_from_db()
        assert expense.pocket_movement is None
        assert not PocketMovement.objects.filter(pk=movement_pk).exists()

    def test_checking_flag_on_historical_expense_creates_movement(
        self, superuser, make_expense,
    ):
        expense = make_expense()
        serializer = make_serializer(
            ExpenseRecordCreateUpdateSerializer,
            {'register_in_pocket': True},
            instance=expense,
        )
        with patch.object(accounting_service, '_notify'):
            accounting_service.update_record(
                EntityType.EXPENSE, expense, serializer, superuser,
            )
        expense.refresh_from_db()
        movement = expense.pocket_movement
        assert movement is not None
        assert movement.direction == PocketMovement.Direction.OUT
        assert movement.amount == expense.total_amount

    def test_linked_expense_edit_mirrors_and_preserves_day(self, superuser):
        expense = create_expense(superuser)
        movement = expense.pocket_movement
        movement.movement_date = date(2026, 2, 17)
        movement.save(update_fields=['movement_date'])
        serializer = make_serializer(
            ExpenseRecordCreateUpdateSerializer,
            {'concept': 'Figma anual', 'total_amount': '95000.00',
             'period_date': '2026-02'},
            instance=expense,
        )
        with patch.object(accounting_service, '_notify'):
            accounting_service.update_record(
                EntityType.EXPENSE, expense, serializer, superuser,
            )
        movement.refresh_from_db()
        assert movement.concept == 'Figma anual'
        assert movement.amount == Decimal('95000.00')
        # Same-month period edits keep the day chosen on the pocket side.
        assert movement.movement_date == date(2026, 2, 17)

    def test_linked_expense_period_month_change_moves_movement(
        self, superuser,
    ):
        expense = create_expense(superuser)
        serializer = make_serializer(
            ExpenseRecordCreateUpdateSerializer,
            {'period_date': '2026-05'},
            instance=expense,
        )
        with patch.object(accounting_service, '_notify'):
            accounting_service.update_record(
                EntityType.EXPENSE, expense, serializer, superuser,
            )
        expense.pocket_movement.refresh_from_db()
        assert expense.pocket_movement.movement_date == date(2026, 5, 1)

    def test_expense_delete_removes_linked_movement(self, superuser):
        expense = create_expense(superuser)
        movement_pk = expense.pocket_movement.pk
        with patch.object(accounting_service, '_notify'):
            accounting_service.delete_record(
                EntityType.EXPENSE, expense, superuser,
            )
        assert not PocketMovement.objects.filter(pk=movement_pk).exists()


@pytest.mark.django_db
class TestPocketToRecordSync:
    def test_pocket_in_creates_liquid_pocket_income_with_half_split(
        self, superuser,
    ):
        movement = create_movement(
            superuser, direction='in', concept='Anticipo cliente',
            amount='1000000.00',
        )
        income = movement.income_record
        assert income is not None
        assert income.kind == IncomeRecord.Kind.LIQUID
        assert income.destination == IncomeRecord.Destination.POCKET
        assert income.period_date == date(2026, 4, 1)
        assert income.concept == 'Anticipo cliente'
        assert income.gustavo_amount == Decimal('500000.00')
        assert income.carlos_amount == Decimal('500000.00')
        assert income.source_ref == f'pocket:{movement.pk}'
        # Regression: the mirrored income must not spawn a second movement.
        assert PocketMovement.objects.count() == 1

    def test_pocket_in_with_personal_ledger_is_invalid(self):
        serializer = PocketMovementCreateUpdateSerializer(data={
            'concept': 'Anticipo', 'movement_date': '2026-04-17',
            'direction': 'in', 'amount': '100000.00', 'ledger': 'gustavo',
        })
        assert not serializer.is_valid()

    def test_pocket_out_with_gustavo_ledger_creates_personal_expense(
        self, superuser,
    ):
        movement = create_movement(superuser, ledger='gustavo')
        expense = movement.expense_record
        assert expense is not None
        assert expense.ledger == 'gustavo'
        assert expense.category == ExpenseRecord.Category.PERSONAL
        assert expense.gustavo_amount == Decimal('150000.00')
        assert expense.carlos_amount == Decimal('0')

    def test_pocket_out_default_ledger_creates_business_expense(
        self, superuser,
    ):
        movement = create_movement(superuser)
        expense = movement.expense_record
        assert expense.ledger == 'company'
        assert expense.category == ExpenseRecord.Category.BUSINESS
        assert expense.gustavo_amount == Decimal('75000.00')
        assert expense.carlos_amount == Decimal('75000.00')

    def test_pocket_edit_mirrors_into_record(self, superuser):
        movement = create_movement(superuser)
        update_movement(
            superuser, movement,
            concept='Pago dominio .co', amount='200000.00',
            movement_date='2026-04-20',
        )
        expense = movement.expense_record
        expense.refresh_from_db()
        assert expense.concept == 'Pago dominio .co'
        assert expense.total_amount == Decimal('200000.00')
        assert expense.gustavo_amount == Decimal('100000.00')
        # Same month: period stays normalized to day 1.
        assert expense.period_date == date(2026, 4, 1)

    def test_pocket_ledger_edit_resets_split(self, superuser):
        movement = create_movement(superuser)
        update_movement(superuser, movement, ledger='carlos')
        expense = movement.expense_record
        expense.refresh_from_db()
        assert expense.ledger == 'carlos'
        assert expense.gustavo_amount == Decimal('0')
        assert expense.carlos_amount == Decimal('150000.00')

    def test_pocket_direction_change_on_linked_is_rejected(self, superuser):
        movement = create_movement(superuser)
        serializer = make_serializer(
            PocketMovementCreateUpdateSerializer,
            {'direction': 'in'}, instance=movement,
        )
        with pytest.raises(ProposalActionError) as exc_info:
            accounting_service.update_record(
                EntityType.POCKET, movement, serializer, superuser,
            )
        assert exc_info.value.code == 'linked_direction_locked'

    def test_unlinked_movement_direction_flip_is_allowed(self, superuser):
        movement = PocketMovement.objects.create(
            concept='Ajuste histórico', movement_date=date(2026, 1, 10),
            direction=PocketMovement.Direction.OUT,
            amount=Decimal('50000.00'),
        )
        update_movement(superuser, movement, direction='in')
        movement.refresh_from_db()
        assert movement.direction == PocketMovement.Direction.IN
        # Historical movements never gain a mirror retroactively.
        assert movement.linked_record is None

    def test_pocket_delete_cascades_to_record_with_audit(self, superuser):
        movement = create_movement(superuser)
        expense_pk = movement.expense_record.pk
        with patch.object(accounting_service, '_notify') as notify:
            accounting_service.delete_record(
                EntityType.POCKET, movement, superuser,
            )
        assert not ExpenseRecord.objects.filter(pk=expense_pk).exists()
        assert AccountingChangeLog.objects.filter(
            entity_type=EntityType.EXPENSE,
            object_id=expense_pk,
            action=Action.DELETED,
        ).exists()
        assert AccountingChangeLog.objects.filter(
            entity_type=EntityType.POCKET,
            action=Action.DELETED,
        ).exists()
        notify.assert_called_once()
