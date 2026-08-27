"""Regression coverage for the seventh project state and catalog help copy."""

from importlib import import_module
from types import SimpleNamespace

import pytest
from django.apps import apps
from django.db import connection

from content.models import DocumentState, DocumentStateGroup


pytestmark = pytest.mark.django_db
migration = import_module('content.migrations.0218_project_state_help')


def run_data_migration():
    migration.add_project_state_help(
        apps,
        SimpleNamespace(connection=connection),
    )


def project_states():
    return DocumentState.objects.filter(
        catalog=DocumentStateGroup.Catalog.PROJECTS,
    )


def test_data_migration_seeds_evolving_after_active():
    project_states().filter(system_key='evolving').delete()
    active = project_states().get(system_key='active')

    run_data_migration()

    evolving = project_states().get(system_key='evolving')
    assert evolving.name == 'En evolución'
    assert evolving.order == active.order + 1
    assert evolving.operational_effect == 'operating'
    assert evolving.description.startswith('Está en producción')


def test_data_migration_preserves_existing_help_copy():
    active = project_states().get(system_key='active')
    active.description = 'Definición adaptada por el equipo.'
    active.save(update_fields=('description',))

    run_data_migration()

    active.refresh_from_db()
    assert active.description == 'Definición adaptada por el equipo.'


def test_data_migration_fills_custom_state_help_from_its_effect():
    group = DocumentStateGroup.objects.get(
        catalog=DocumentStateGroup.Catalog.PROJECTS,
        selection_mode=DocumentStateGroup.SelectionMode.EXCLUSIVE,
    )
    custom = DocumentState.objects.create(
        name='En observación',
        description='',
        color=DocumentState.Color.YELLOW,
        group=group,
        operational_effect=DocumentState.OperationalEffect.PAUSED,
    )

    run_data_migration()

    custom.refresh_from_db()
    assert custom.description == (
        'El trabajo del proyecto está detenido temporalmente.'
    )
