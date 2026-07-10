"""Income/Expense ↔ Pocket movement synchronization tests."""
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import AccountingChangeLog, PocketMovement
from content.serializers.accounting import (
    ExpenseRecordCreateUpdateSerializer,
    IncomeRecordCreateUpdateSerializer,
)
from content.services import accounting_service

EntityType = AccountingChangeLog.EntityType


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


@pytest.mark.django_db
class TestIncomePocketSync:
    def test_liquid_pocket_income_creates_in_movement(self, superuser):
        income = create_pocket_income(superuser)
        movement = income.pocket_movement
        assert movement is not None
        assert movement.direction == PocketMovement.Direction.IN
        assert movement.amount == Decimal('2123000.00')
        assert movement.movement_date == income.period_date
        assert movement.concept == f'Ingreso: {income.concept}'
        assert movement.is_auto_managed is True

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
            action=AccountingChangeLog.Action.CREATED,
        ).exists()


@pytest.mark.django_db
class TestExpensePocketSync:
    def test_expense_creates_no_movement(self, superuser):
        # Expenses draw from money already in the pocket (team flow);
        # pocket OUT movements are registered manually, never auto-synced.
        data = {
            'concept': 'Figma',
            'period_date': '2026-02',
            'total_amount': '80000.00',
        }
        with patch.object(accounting_service, '_notify'):
            accounting_service.create_record(
                EntityType.EXPENSE,
                make_serializer(ExpenseRecordCreateUpdateSerializer, data),
                superuser,
            )
        assert PocketMovement.objects.count() == 0
