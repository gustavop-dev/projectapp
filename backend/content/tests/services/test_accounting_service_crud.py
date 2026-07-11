"""CRUD + audit pipeline tests for accounting_service."""
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.api_errors import ProposalActionError
from content.models import AccountingChangeLog, IncomeRecord
from content.serializers.accounting import (
    IncomeRecordCreateUpdateSerializer,
    PocketMovementCreateUpdateSerializer,
)
from content.services import accounting_service

EntityType = AccountingChangeLog.EntityType
Action = AccountingChangeLog.Action


def valid_serializer(data, instance=None):
    serializer = IncomeRecordCreateUpdateSerializer(
        instance=instance, data=data, partial=instance is not None,
    )
    assert serializer.is_valid(), serializer.errors
    return serializer


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
class TestCreateRecord:
    def test_creates_logs_and_sets_created_by(self, superuser):
        with patch.object(accounting_service, '_notify') as notify:
            income = accounting_service.create_record(
                EntityType.INCOME,
                valid_serializer(income_payload()),
                superuser,
            )
        assert income.created_by == superuser
        log = AccountingChangeLog.objects.get(
            entity_type=EntityType.INCOME, object_id=income.pk,
        )
        assert log.action == Action.CREATED
        assert log.actor == superuser
        assert log.actor_username == superuser.username
        assert any(c['field'] == 'total_amount' for c in log.changes)
        notify.assert_called_once_with(log)

    def test_create_survives_notification_failure(self, superuser):
        with patch(
            'content.tasks.send_accounting_change_email',
            side_effect=RuntimeError('queue down'),
        ):
            income = accounting_service.create_record(
                EntityType.INCOME,
                valid_serializer(income_payload()),
                superuser,
            )
        assert IncomeRecord.objects.filter(pk=income.pk).exists()


@pytest.mark.django_db
class TestUpdateRecord:
    def test_logs_only_changed_fields(self, superuser, make_income):
        income = make_income(total_amount=Decimal('1000000.00'))
        serializer = valid_serializer(
            {'total_amount': '1200000.00'}, instance=income,
        )
        with patch.object(accounting_service, '_notify') as notify:
            accounting_service.update_record(
                EntityType.INCOME, income, serializer, superuser,
            )
        log = AccountingChangeLog.objects.filter(action=Action.UPDATED).get()
        assert len(log.changes) == 1
        change = log.changes[0]
        assert change['field'] == 'total_amount'
        # Money fields are audited with COP formatting (shared helper).
        assert change['old'] == "$1'000.000"
        assert change['new'] == "$1'200.000"
        notify.assert_called_once()

    def test_noop_update_writes_no_log_and_no_email(
        self, superuser, make_income,
    ):
        income = make_income()
        serializer = valid_serializer(
            {'concept': income.concept}, instance=income,
        )
        with patch.object(accounting_service, '_notify') as notify:
            accounting_service.update_record(
                EntityType.INCOME, income, serializer, superuser,
            )
        assert not AccountingChangeLog.objects.filter(
            action=Action.UPDATED,
        ).exists()
        notify.assert_not_called()


@pytest.mark.django_db
class TestDeleteRecord:
    def test_deletes_and_logs_repr_with_old_values(
        self, superuser, make_income,
    ):
        income = make_income(concept='Universidad Nacional')
        income_pk = income.pk
        with patch.object(accounting_service, '_notify') as notify:
            accounting_service.delete_record(
                EntityType.INCOME, income, superuser,
            )
        assert not IncomeRecord.objects.filter(pk=income_pk).exists()
        log = AccountingChangeLog.objects.filter(action=Action.DELETED).get()
        assert log.object_repr == 'Universidad Nacional'
        assert log.object_id == income_pk
        assert any(
            c['field'] == 'concept' and c['old'] == 'Universidad Nacional'
            for c in log.changes
        )
        notify.assert_called_once()


@pytest.mark.django_db
class TestLinkedMovementEditing:
    def _linked_movement(self, superuser):
        income = accounting_service.create_record(
            EntityType.INCOME,
            valid_serializer(income_payload(
                kind='liquid', destination='pocket',
            )),
            superuser,
        )
        return income.pocket_movement

    def test_linked_movement_update_mirrors_into_income(self, superuser):
        movement = self._linked_movement(superuser)
        serializer = PocketMovementCreateUpdateSerializer(
            instance=movement, data={'amount': '999000.00'}, partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        with patch.object(accounting_service, '_notify'):
            accounting_service.update_record(
                EntityType.POCKET, movement, serializer, superuser,
            )
        income = movement.income_record
        income.refresh_from_db()
        assert income.total_amount == Decimal('999000.00')

    def test_linked_movement_direction_change_is_rejected(self, superuser):
        movement = self._linked_movement(superuser)
        serializer = PocketMovementCreateUpdateSerializer(
            instance=movement, data={'direction': 'out'}, partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        with pytest.raises(ProposalActionError) as exc_info:
            accounting_service.update_record(
                EntityType.POCKET, movement, serializer, superuser,
            )
        assert exc_info.value.code == 'linked_direction_locked'

    def test_linked_movement_delete_cascades_to_income(self, superuser):
        movement = self._linked_movement(superuser)
        income_pk = movement.income_record.pk
        with patch.object(accounting_service, '_notify'):
            accounting_service.delete_record(
                EntityType.POCKET, movement, superuser,
            )
        assert not IncomeRecord.objects.filter(pk=income_pk).exists()
