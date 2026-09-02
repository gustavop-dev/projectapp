from datetime import date
from decimal import Decimal

import pytest
from django.template.loader import render_to_string
from django.utils import timezone

from content.models import AccountingChangeLog, PocketMovement
from content.serializers.accounting import (
    AccountingChangeLogSerializer,
    PocketMovementCreateUpdateSerializer,
)
from content.services import accounting_service
from content.services.accounting_email_service import (
    NOTIFICATION_TONE_INCOME,
    NOTIFICATION_TONE_NEUTRAL,
    NOTIFICATION_TONE_OUTFLOW,
    build_accounting_change_context,
    resolve_accounting_notification_tone,
)


EntityType = AccountingChangeLog.EntityType
Action = AccountingChangeLog.Action


def make_change_log(
    entity_type,
    *,
    action=Action.CREATED,
    movement_direction=None,
    changes=None,
):
    return AccountingChangeLog(
        entity_type=entity_type,
        object_id=1,
        object_repr='Registro contable',
        action=action,
        movement_direction=movement_direction,
        changes=changes or [],
        actor_username='super_test',
        created_at=timezone.now(),
    )


@pytest.mark.parametrize(
    ('entity_type', 'expected_tone'),
    [
        (EntityType.INCOME, NOTIFICATION_TONE_INCOME),
        (EntityType.EXPENSE, NOTIFICATION_TONE_OUTFLOW),
        (EntityType.RECURRING, NOTIFICATION_TONE_OUTFLOW),
        (EntityType.ADS, NOTIFICATION_TONE_OUTFLOW),
        (EntityType.CARD_SNAPSHOT, NOTIFICATION_TONE_OUTFLOW),
        (EntityType.STATEMENT, NOTIFICATION_TONE_OUTFLOW),
        (EntityType.STATEMENT_TX, NOTIFICATION_TONE_OUTFLOW),
        (EntityType.HOSTING, NOTIFICATION_TONE_NEUTRAL),
        (EntityType.CREDIT_CARD, NOTIFICATION_TONE_NEUTRAL),
    ],
)
def test_entity_type_resolves_financial_tone(entity_type, expected_tone):
    log = make_change_log(entity_type)

    assert resolve_accounting_notification_tone(log) == expected_tone


@pytest.mark.parametrize(
    ('direction', 'expected_tone'),
    [
        (
            AccountingChangeLog.MovementDirection.IN,
            NOTIFICATION_TONE_INCOME,
        ),
        (
            AccountingChangeLog.MovementDirection.OUT,
            NOTIFICATION_TONE_OUTFLOW,
        ),
        (None, NOTIFICATION_TONE_NEUTRAL),
    ],
)
def test_pocket_direction_resolves_financial_tone(direction, expected_tone):
    log = make_change_log(EntityType.POCKET, movement_direction=direction)

    assert resolve_accounting_notification_tone(log) == expected_tone


def test_direction_snapshot_stays_out_of_change_log_payload():
    log = make_change_log(
        EntityType.POCKET,
        movement_direction=AccountingChangeLog.MovementDirection.OUT,
    )

    assert 'movement_direction' not in AccountingChangeLogSerializer(log).data


@pytest.mark.django_db
def test_complete_pocket_diff_recovers_direction_snapshot():
    log = accounting_service.log_accounting_change(
        entity_type=EntityType.POCKET,
        object_id=1,
        object_repr='Compra de equipo',
        action=Action.CREATED,
        changes=[{
            'field': 'direction',
            'label': 'Tipo',
            'old': '',
            'new': 'Egreso',
        }],
    )

    assert log.movement_direction == AccountingChangeLog.MovementDirection.OUT


@pytest.mark.django_db
def test_pocket_update_persists_unchanged_direction(superuser):
    movement = PocketMovement.objects.create(
        concept='Compra de equipo',
        movement_date=date(2026, 9, 2),
        direction=PocketMovement.Direction.OUT,
        amount=Decimal('200000.00'),
    )
    serializer = PocketMovementCreateUpdateSerializer(
        movement,
        data={'concept': 'Compra de portátil'},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors

    accounting_service.update_record(
        EntityType.POCKET,
        movement,
        serializer,
        superuser,
        notify=False,
    )

    log = AccountingChangeLog.objects.get(
        entity_type=EntityType.POCKET,
        object_id=movement.pk,
        action=Action.UPDATED,
    )
    assert log.movement_direction == AccountingChangeLog.MovementDirection.OUT


def test_created_expense_uses_outflow_accent():
    log = make_change_log(
        EntityType.EXPENSE,
        changes=[{
            'field': 'total_amount',
            'label': 'Monto total',
            'old': '',
            'new': '$200.000',
        }],
    )

    html = render_to_string(
        'emails/accounting_change.html',
        build_accounting_change_context(log),
    )

    assert 'background-color:#b45309;' in html
    assert 'color:#b45309;">$200.000' in html


def test_updated_income_preserves_old_value_accent():
    log = make_change_log(
        EntityType.INCOME,
        action=Action.UPDATED,
        changes=[{
            'field': 'total_amount',
            'label': 'Monto total',
            'old': '$100.000',
            'new': '$200.000',
        }],
    )

    html = render_to_string(
        'emails/accounting_change.html',
        build_accounting_change_context(log),
    )

    assert 'background-color:#15803d;' in html
    assert 'color:#b91c1c;">$100.000' in html
    assert 'color:#15803d;">$200.000' in html


def test_deleted_outflow_uses_outflow_header_accent():
    log = make_change_log(
        EntityType.POCKET,
        action=Action.DELETED,
        movement_direction=AccountingChangeLog.MovementDirection.OUT,
        changes=[{
            'field': 'amount',
            'label': 'Valor',
            'old': '$200.000',
            'new': '',
        }],
    )

    html = render_to_string(
        'emails/accounting_change.html',
        build_accounting_change_context(log),
    )

    assert 'background-color:#b45309;' in html
    assert 'color:#b91c1c;">$200.000' in html
    assert 'Valor nuevo' not in html
