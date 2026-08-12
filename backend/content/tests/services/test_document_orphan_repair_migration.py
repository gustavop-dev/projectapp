"""Tests for migration 0186 — reparación de elementos activos inalcanzables.

La migración recorre el árbol con modelos históricos, así que se la invoca
directamente (el módulo empieza con dígitos y necesita `importlib`).
"""
import importlib
from types import SimpleNamespace

import pytest
from django.apps import apps

from content.models import Document, DocumentFolder

pytestmark = pytest.mark.django_db

migration_module = importlib.import_module(
    'content.migrations.0186_repair_active_rows_under_archived_folders',
)


def _run():
    migration_module.repair_unreachable_rows(
        apps, SimpleNamespace(connection=SimpleNamespace(alias='default')),
    )


def _archive(*rows):
    """Marca filas como archivadas sin pasar por el servicio (estado histórico)."""
    for row in rows:
        type(row).objects.filter(pk=row.pk).update(is_archived=True)


def test_reopens_the_folder_of_an_active_document():
    folder = DocumentFolder.objects.create(name='temp')
    doc = Document.objects.create(title='requirements_mapping', folder=folder)
    _archive(folder)

    _run()

    folder.refresh_from_db()
    doc.refresh_from_db()
    assert folder.is_archived is False
    assert doc.folder_id == folder.pk


def test_reopens_every_level_of_the_chain():
    root = DocumentFolder.objects.create(name='Clientes')
    mid = DocumentFolder.objects.create(name='2026', parent=root)
    leaf = DocumentFolder.objects.create(name='Actas', parent=mid)
    Document.objects.create(title='Acta', folder=leaf)
    _archive(root, mid, leaf)

    _run()

    assert not DocumentFolder.objects.filter(is_archived=True).exists()


def test_leaves_the_rest_of_the_chain_content_archived():
    folder = DocumentFolder.objects.create(name='temp')
    Document.objects.create(title='Rescatado', folder=folder)
    sibling = Document.objects.create(title='Archivado', folder=folder)
    sibling_folder = DocumentFolder.objects.create(name='Sub', parent=folder)
    _archive(folder, sibling, sibling_folder)

    _run()

    sibling.refresh_from_db()
    sibling_folder.refresh_from_db()
    assert sibling.is_archived is True
    assert sibling_folder.is_archived is True


def test_reopens_the_chain_of_an_active_subfolder():
    root = DocumentFolder.objects.create(name='Clientes')
    child = DocumentFolder.objects.create(name='2026', parent=root)
    _archive(root)

    _run()

    root.refresh_from_db()
    child.refresh_from_db()
    assert root.is_archived is False
    assert child.is_archived is False


def test_does_nothing_when_every_active_row_is_reachable():
    folder = DocumentFolder.objects.create(name='Contratos')
    archived = Document.objects.create(title='Viejo', folder=folder)
    _archive(archived)

    _run()

    folder.refresh_from_db()
    archived.refresh_from_db()
    assert folder.is_archived is False
    assert archived.is_archived is True, 'un archivado suelto no se toca'


def test_is_idempotent():
    folder = DocumentFolder.objects.create(name='temp')
    Document.objects.create(title='Acta', folder=folder)
    _archive(folder)

    _run()
    _run()

    folder.refresh_from_db()
    assert folder.is_archived is False


def test_survives_a_cycle_without_detaching_anything():
    first = DocumentFolder.objects.create(name='A')
    second = DocumentFolder.objects.create(name='B', parent=first)
    Document.objects.create(title='Acta', folder=second)
    DocumentFolder.objects.filter(pk=first.pk).update(parent=second)
    _archive(first, second)

    _run()

    first.refresh_from_db()
    second.refresh_from_db()
    # Desatendida, la migración desarchiva lo que encuentra y deja la topología
    # intacta: re-parentar filas en silencio sería peor que el ciclo.
    assert first.is_archived is False
    assert second.is_archived is False
    assert second.parent_id == first.pk
