"""Tests for the `backfill_document_content_json` management command.

Business rules asserted:
- Documents with markdown but no parsed blocks are repaired
- Dry-run is the default: nothing is written without --apply
- Documents that already have blocks are left untouched
- Documents whose markdown is blank are not targets at all
"""
from io import StringIO

import pytest
from django.core.management import call_command

from content.models import Document, DocumentType
from content.services.document_type_codes import MARKDOWN

pytestmark = pytest.mark.django_db


@pytest.fixture
def md_type(db):
    doc_type, _ = DocumentType.objects.get_or_create(
        code=MARKDOWN, defaults={'name': 'Documento markdown'},
    )
    return doc_type


def _run(*args):
    out = StringIO()
    call_command('backfill_document_content_json', *args, stdout=out)
    return out.getvalue()


class TestBackfillDocumentContentJson:
    def test_apply_rebuilds_blocks_from_markdown(self, md_type):
        doc = Document.objects.create(
            title='Estimate', document_type=md_type,
            content_markdown='# Título\n\nUn párrafo.\n', content_json={},
        )

        _run('--apply')

        doc.refresh_from_db()
        assert [b['type'] for b in doc.content_json['blocks']] == ['heading', 'paragraph']
        assert doc.content_json['meta']['title'] == 'Estimate'

    def test_dry_run_is_the_default_and_writes_nothing(self, md_type):
        doc = Document.objects.create(
            title='Estimate', document_type=md_type,
            content_markdown='# Título\n', content_json={},
        )

        output = _run()

        doc.refresh_from_db()
        assert doc.content_json == {}
        assert '--apply' in output

    def test_documents_with_blocks_are_left_untouched(self, md_type):
        original = {'meta': {}, 'blocks': [{'type': 'paragraph', 'text': 'Ya parseado'}]}
        doc = Document.objects.create(
            title='Intacto', document_type=md_type,
            content_markdown='# Otro contenido\n', content_json=original,
        )

        _run('--apply')

        doc.refresh_from_db()
        assert doc.content_json == original

    def test_blank_markdown_is_not_a_target(self, md_type):
        """Un documento sin contenido real no se toca: no hay nada que derivar."""
        doc = Document.objects.create(
            title='Vacío', document_type=md_type,
            content_markdown='   \n', content_json={},
        )

        _run('--apply')

        doc.refresh_from_db()
        assert doc.content_json == {}
