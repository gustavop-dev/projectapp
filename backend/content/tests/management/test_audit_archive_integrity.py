"""Tests del comando audit_archive_integrity — auditoría re-ejecutable del
invariante de archivado (la versión repetible de la migración 0186)."""
import io

import pytest
from django.core.management import call_command

from content.models import Document, DocumentFolder

pytestmark = pytest.mark.django_db


def _run(*args):
    out = io.StringIO()
    call_command('audit_archive_integrity', *args, stdout=out)
    return out.getvalue()


def _archive(*rows):
    """Marca filas como archivadas sin pasar por el servicio (estado tóxico)."""
    for row in rows:
        type(row).objects.filter(pk=row.pk).update(is_archived=True)


def test_reports_a_lost_document_without_touching_data():
    folder = DocumentFolder.objects.create(name='temp')
    doc = Document.objects.create(title='requirements_mapping', folder=folder)
    _archive(folder)

    output = _run()

    assert 'DOCUMENTOS PERDIDOS' in output
    assert 'requirements_mapping' in output
    folder.refresh_from_db()
    assert folder.is_archived is True, 'el dry-run no escribe nada'


def test_repair_reopens_the_full_ancestor_chain():
    root = DocumentFolder.objects.create(name='Clientes')
    mid = DocumentFolder.objects.create(name='2026', parent=root)
    leaf = DocumentFolder.objects.create(name='Actas', parent=mid)
    doc = Document.objects.create(title='Acta', folder=leaf)
    _archive(root, mid, leaf)

    output = _run('--repair')

    assert 'Reparado: 3 carpeta(s)' in output
    assert not DocumentFolder.objects.filter(is_archived=True).exists()
    doc.refresh_from_db()
    assert doc.folder_id == leaf.pk, 'nunca se re-parenta'


def test_repair_leaves_siblings_archived():
    folder = DocumentFolder.objects.create(name='temp')
    Document.objects.create(title='Rescatado', folder=folder)
    sibling = Document.objects.create(title='Archivado a propósito', folder=folder)
    sibling_folder = DocumentFolder.objects.create(name='Sub', parent=folder)
    _archive(folder, sibling, sibling_folder)

    _run('--repair')

    folder.refresh_from_db()
    sibling.refresh_from_db()
    sibling_folder.refresh_from_db()
    assert folder.is_archived is False
    assert sibling.is_archived is True, 'solo la cadena, como 0186'
    assert sibling_folder.is_archived is True


def test_clean_tree_reports_no_violations():
    folder = DocumentFolder.objects.create(name='Contratos')
    archived = Document.objects.create(title='Viejo', folder=folder)
    _archive(archived)

    output = _run()

    assert 'Invariante OK' in output
    archived.refresh_from_db()
    assert archived.is_archived is True, 'un archivado suelto no es violación'


def test_repair_is_idempotent():
    folder = DocumentFolder.objects.create(name='temp')
    Document.objects.create(title='Acta', folder=folder)
    _archive(folder)

    _run('--repair')
    output = _run('--repair')

    assert 'Nada que reparar' in output
    folder.refresh_from_db()
    assert folder.is_archived is False


def test_reports_a_cycle_without_detaching():
    first = DocumentFolder.objects.create(name='A')
    second = DocumentFolder.objects.create(name='B', parent=first)
    DocumentFolder.objects.filter(pk=first.pk).update(parent=second)
    _archive(first, second)

    output = _run('--repair')

    assert 'CICLO en parent' in output
    assert 'punto muerto' in output
    first.refresh_from_db()
    second.refresh_from_db()
    # Sin contenido activo adentro no hay nada que reabrir, y la topología
    # queda intacta: el comando jamás re-parenta.
    assert first.is_archived is True
    assert second.is_archived is True
    assert first.parent_id == second.pk


def test_reports_active_rows_claiming_cascade_provenance():
    cause = DocumentFolder.objects.create(name='Causante')
    doc = Document.objects.create(title='Editado a mano')
    Document.objects.filter(pk=doc.pk).update(archived_via_folder=cause)

    output = _run('--repair')

    assert 'PROCEDENCIA ANÓMALA' in output
    assert 'Editado a mano' in output
    doc.refresh_from_db()
    # Se reporta pero no se toca: limpiar procedencia no es parte de la
    # política de reparación.
    assert doc.archived_via_folder_id == cause.pk
