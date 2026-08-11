"""Tests for content/services/document_archive_service.py.

The interesting behaviour is the cascade *memory*: archiving a folder drags its
content along, but items that were already archived on their own keep that mark
and stay archived when the folder is restored.
"""
import pytest
from django.utils import timezone

from content.models import Document, DocumentFolder
from content.services import document_archive_service as svc

pytestmark = pytest.mark.django_db


@pytest.fixture
def folder(db):
    return DocumentFolder.objects.create(name='Contratos')


@pytest.fixture
def make_doc(db):
    def _make(title, folder=None):
        return Document.objects.create(title=title, folder=folder)

    return _make


class TestArchiveDocument:
    def test_sets_flag_and_timestamp(self, make_doc):
        doc = make_doc('Acta')

        assert svc.archive_document(doc) is True

        doc.refresh_from_db()
        assert doc.is_archived is True
        assert doc.archived_at is not None
        assert doc.archived_via_folder_id is None

    def test_is_a_noop_when_already_archived(self, make_doc):
        doc = make_doc('Acta')
        svc.archive_document(doc)
        original = Document.objects.get(pk=doc.pk).archived_at

        assert svc.archive_document(doc) is False
        assert Document.objects.get(pk=doc.pk).archived_at == original


class TestUnarchiveDocument:
    def test_clears_flag_timestamp_and_provenance(self, folder, make_doc):
        doc = make_doc('Acta', folder=folder)
        svc.archive_folder(folder)
        doc.refresh_from_db()
        assert doc.archived_via_folder_id == folder.pk

        assert svc.unarchive_document(doc) is True

        doc.refresh_from_db()
        assert doc.is_archived is False
        assert doc.archived_at is None
        assert doc.archived_via_folder_id is None

    def test_returns_to_root_when_its_folder_was_deleted(self, folder, make_doc):
        doc = make_doc('Acta', folder=folder)
        svc.archive_document(doc)
        # El guard 409 impide borrar carpetas con contenido, así que primero
        # se saca el documento; el FK es SET_NULL.
        Document.objects.filter(pk=doc.pk).update(folder=None)
        folder.delete()

        svc.unarchive_document(Document.objects.get(pk=doc.pk))

        doc.refresh_from_db()
        assert doc.is_archived is False
        assert doc.folder_id is None


class TestArchiveFolder:
    def test_archives_the_folder_its_documents_and_subfolders(self, folder, make_doc):
        child = DocumentFolder.objects.create(name='2024', parent=folder)
        top_doc = make_doc('Marco', folder=folder)
        nested_doc = make_doc('Anexo', folder=child)

        counts = svc.archive_folder(folder)

        folder.refresh_from_db()
        child.refresh_from_db()
        top_doc.refresh_from_db()
        nested_doc.refresh_from_db()
        assert folder.is_archived is True
        assert child.is_archived is True
        assert top_doc.is_archived is True
        assert nested_doc.is_archived is True
        assert counts == {'folders': 1, 'documents': 2}

    def test_stamps_cascaded_items_with_the_causing_folder(self, folder, make_doc):
        child = DocumentFolder.objects.create(name='2024', parent=folder)
        doc = make_doc('Marco', folder=folder)

        svc.archive_folder(folder)

        assert Document.objects.get(pk=doc.pk).archived_via_folder_id == folder.pk
        assert DocumentFolder.objects.get(pk=child.pk).archived_via_folder_id == folder.pk
        # La carpeta archivada a mano nunca lleva procedencia.
        assert DocumentFolder.objects.get(pk=folder.pk).archived_via_folder_id is None

    def test_leaves_individually_archived_documents_untouched(self, folder, make_doc):
        loose = make_doc('Viejo', folder=folder)
        svc.archive_document(loose)
        original = Document.objects.get(pk=loose.pk).archived_at

        counts = svc.archive_folder(folder)

        loose.refresh_from_db()
        assert loose.archived_via_folder_id is None
        assert loose.archived_at == original
        assert counts['documents'] == 0

    def test_is_idempotent_and_preserves_the_original_archived_at(self, folder, make_doc):
        make_doc('Marco', folder=folder)
        svc.archive_folder(folder)
        original = DocumentFolder.objects.get(pk=folder.pk).archived_at

        counts = svc.archive_folder(DocumentFolder.objects.get(pk=folder.pk))

        assert counts == {'folders': 0, 'documents': 0}
        assert DocumentFolder.objects.get(pk=folder.pk).archived_at == original

    def test_sweeps_content_added_into_an_already_archived_folder(self, folder, make_doc):
        svc.archive_folder(folder)
        latecomer = make_doc('Nuevo', folder=folder)

        counts = svc.archive_folder(DocumentFolder.objects.get(pk=folder.pk))

        latecomer.refresh_from_db()
        assert latecomer.is_archived is True
        assert counts['documents'] == 1

    def test_nested_manual_archive_keeps_its_own_subtree(self, folder, make_doc):
        child = DocumentFolder.objects.create(name='2024', parent=folder)
        grandchild_doc = make_doc('Anexo', folder=child)
        svc.archive_folder(child)

        svc.archive_folder(folder)

        # El subárbol de `child` sigue apuntando a `child`, no a `folder`.
        assert DocumentFolder.objects.get(pk=child.pk).archived_via_folder_id is None
        assert Document.objects.get(pk=grandchild_doc.pk).archived_via_folder_id == child.pk


class TestUnarchiveFolder:
    def test_restores_the_folder_and_everything_it_dragged(self, folder, make_doc):
        child = DocumentFolder.objects.create(name='2024', parent=folder)
        doc = make_doc('Marco', folder=folder)
        nested = make_doc('Anexo', folder=child)
        svc.archive_folder(folder)

        counts = svc.unarchive_folder(DocumentFolder.objects.get(pk=folder.pk))

        folder.refresh_from_db()
        child.refresh_from_db()
        doc.refresh_from_db()
        nested.refresh_from_db()
        assert folder.is_archived is False
        assert folder.archived_at is None
        assert child.is_archived is False
        assert doc.is_archived is False
        assert nested.is_archived is False
        assert counts == {'folders': 1, 'documents': 2}

    def test_keeps_individually_archived_documents_archived(self, folder, make_doc):
        dragged = make_doc('Nuevo', folder=folder)
        loose = make_doc('Viejo', folder=folder)
        svc.archive_document(loose)
        svc.archive_folder(folder)

        svc.unarchive_folder(DocumentFolder.objects.get(pk=folder.pk))

        dragged.refresh_from_db()
        loose.refresh_from_db()
        assert dragged.is_archived is False
        assert loose.is_archived is True, 'lo archivado a mano debe quedarse archivado'

    def test_does_not_restore_the_subtree_of_a_nested_manual_archive(self, folder, make_doc):
        child = DocumentFolder.objects.create(name='2024', parent=folder)
        nested = make_doc('Anexo', folder=child)
        svc.archive_folder(child)
        svc.archive_folder(folder)

        svc.unarchive_folder(DocumentFolder.objects.get(pk=folder.pk))

        child.refresh_from_db()
        nested.refresh_from_db()
        assert child.is_archived is True
        assert nested.is_archived is True

    def test_restores_a_document_moved_to_another_folder_while_archived(self, folder, make_doc):
        other = DocumentFolder.objects.create(name='Otra')
        doc = make_doc('Marco', folder=folder)
        svc.archive_folder(folder)
        Document.objects.filter(pk=doc.pk).update(folder=other)

        svc.unarchive_folder(DocumentFolder.objects.get(pk=folder.pk))

        doc.refresh_from_db()
        assert doc.is_archived is False
        assert doc.folder_id == other.pk

    def test_raises_when_the_parent_folder_is_still_archived(self, folder):
        child = DocumentFolder.objects.create(name='2024', parent=folder)
        svc.archive_folder(folder)

        with pytest.raises(svc.DocumentArchiveError):
            svc.unarchive_folder(DocumentFolder.objects.get(pk=child.pk))

    def test_allows_restoring_a_child_whose_parent_is_active(self, folder):
        child = DocumentFolder.objects.create(name='2024', parent=folder)
        svc.archive_folder(child)

        svc.unarchive_folder(DocumentFolder.objects.get(pk=child.pk))

        child.refresh_from_db()
        assert child.is_archived is False


class TestArchivedAtOrdering:
    def test_archived_at_is_shared_across_one_cascade(self, folder, make_doc):
        make_doc('A', folder=folder)
        make_doc('B', folder=folder)
        before = timezone.now()

        svc.archive_folder(folder)

        stamps = set(
            Document.objects.filter(folder=folder).values_list('archived_at', flat=True)
        )
        assert len(stamps) == 1
        assert stamps.pop() >= before
