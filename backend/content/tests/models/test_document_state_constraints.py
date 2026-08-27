"""Database constraints for the shared document/project state catalog."""

import pytest
from django.db import IntegrityError, transaction

from content.models import DocumentState, DocumentStateGroup


pytestmark = pytest.mark.django_db


def _group(catalog, name):
    return DocumentStateGroup.objects.create(
        catalog=catalog,
        name=name,
        selection_mode=DocumentStateGroup.SelectionMode.ADDITIVE,
    )


def test_duplicate_system_key_in_one_catalog_is_rejected():
    group = _group(DocumentStateGroup.Catalog.DOCUMENTS, 'Ciclo de soporte')
    DocumentState.objects.create(
        name='Pendiente de soporte',
        group=group,
        system_key='support_pending',
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DocumentState.objects.create(
                name='Soporte pendiente duplicado',
                group=group,
                system_key='support_pending',
            )


def test_same_system_key_in_different_catalogs_is_allowed():
    documents = _group(
        DocumentStateGroup.Catalog.DOCUMENTS,
        'Ciclo documental',
    )
    projects = _group(
        DocumentStateGroup.Catalog.PROJECTS,
        'Ciclo de proyectos',
    )
    document_state = DocumentState.objects.create(
        name='En espera documental',
        group=documents,
        system_key='waiting',
    )
    project_state = DocumentState.objects.create(
        name='En espera de proyecto',
        group=projects,
        system_key='waiting',
    )

    assert document_state.catalog != project_state.catalog


def test_multiple_null_system_keys_in_one_catalog_are_allowed():
    group = _group(DocumentStateGroup.Catalog.DOCUMENTS, 'Estados personalizados')
    first = DocumentState.objects.create(name='Esperando firma', group=group)
    second = DocumentState.objects.create(name='Esperando pago', group=group)

    assert first.system_key is None
    assert second.system_key is None


def test_system_key_constraint_does_not_use_a_condition():
    constraint = next(
        item
        for item in DocumentState._meta.constraints
        if item.name == 'unique_state_system_key_per_catalog'
    )

    assert constraint.condition is None
