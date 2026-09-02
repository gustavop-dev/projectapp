from importlib import import_module

import pytest
from django.apps import apps

from content.models import AccountingChangeLog


pytestmark = pytest.mark.django_db
migration = import_module(
    'content.migrations.0237_accounting_change_movement_direction',
)


def make_pocket_log(action, changes):
    return AccountingChangeLog.objects.create(
        entity_type=AccountingChangeLog.EntityType.POCKET,
        object_id=1,
        object_repr='Movimiento histórico',
        action=action,
        changes=changes,
    )


def test_backfill_uses_new_direction_for_created_log():
    log = make_pocket_log(
        AccountingChangeLog.Action.CREATED,
        [{
            'field': 'direction',
            'label': 'Tipo',
            'old': '',
            'new': 'Egreso',
        }],
    )

    migration.backfill_pocket_movement_direction(apps, None)

    log.refresh_from_db()
    assert log.movement_direction == AccountingChangeLog.MovementDirection.OUT


def test_backfill_uses_old_direction_for_deleted_log():
    log = make_pocket_log(
        AccountingChangeLog.Action.DELETED,
        [{
            'field': 'direction',
            'label': 'Tipo',
            'old': 'Ingreso',
            'new': '',
        }],
    )

    migration.backfill_pocket_movement_direction(apps, None)

    log.refresh_from_db()
    assert log.movement_direction == AccountingChangeLog.MovementDirection.IN


def test_backfill_leaves_unrecoverable_update_unclassified():
    log = make_pocket_log(
        AccountingChangeLog.Action.UPDATED,
        [{
            'field': 'concept',
            'label': 'Concepto',
            'old': 'Antes',
            'new': 'Después',
        }],
    )

    migration.backfill_pocket_movement_direction(apps, None)

    log.refresh_from_db()
    assert log.movement_direction is None
