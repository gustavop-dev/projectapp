"""Tests for DocumentPdfService.generate() — Phase 3C coverage.

All tests use a real in-memory Document fixture to call generate() and
assert observable outputs (bytes, PDF header).  No external I/O is
mocked beyond the cover-page PDFs (which require disk files and are
not present in the test environment).
"""
from unittest.mock import patch

import pytest

from content.models import Document

pytestmark = pytest.mark.django_db


# -- Fixtures -----------------------------------------------------------------

def _document(**kwargs):
    """Create a minimal Document with sensible defaults."""
    defaults = {
        'title': 'Test Document',
        'client_name': 'Test Client',
        'include_portada': False,
        'include_subportada': False,
        'include_contraportada': False,
    }
    defaults.update(kwargs)
    return Document.objects.create(**defaults)


def _with_blocks(blocks):
    """Return a content_json dict with the given blocks list."""
    return {'meta': {'client_name': 'Client'}, 'blocks': blocks}


# -- generate() basic ---------------------------------------------------------

class TestDocumentPdfServiceGenerate:
    @pytest.fixture(autouse=True)
    def _bypass_merge(self):
        with patch(
            'content.services.document_pdf_service.DocumentPdfService._merge_with_covers',
            side_effect=lambda b, **kw: b,
        ):
            yield

    def test_generate_returns_pdf_bytes_for_simple_paragraph(self):
        """generate() returns PDF bytes when document has paragraph blocks."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'paragraph', 'text': 'Hello world.'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'

    def test_generate_returns_none_when_no_blocks(self):
        """generate() returns None when content_json has no blocks."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json={'blocks': []})
        result = DocumentPdfService.generate(doc)

        assert result is None

    def test_generate_returns_none_when_content_json_empty(self):
        """generate() returns None when content_json is an empty dict."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json={})
        result = DocumentPdfService.generate(doc)

        assert result is None


    def test_generate_renders_heading_block(self):
        """generate() handles heading blocks of all levels without error."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'heading', 'level': 1, 'text': 'Title'},
            {'type': 'heading', 'level': 2, 'text': 'Subtitle'},
            {'type': 'heading', 'level': 3, 'text': 'Minor'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_renders_list_block_unordered(self):
        """generate() renders unordered list blocks without error."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'list', 'ordered': False, 'items': [
                {'text': 'Item A', 'children': []},
                {'text': 'Item B', 'children': []},
            ]},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_renders_list_block_ordered(self):
        """generate() renders ordered list blocks without error."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'list', 'ordered': True, 'items': [
                {'text': 'First', 'children': []},
                {'text': 'Second', 'children': []},
            ]},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_renders_table_block(self):
        """generate() renders table blocks without error."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'table', 'headers': ['Col A', 'Col B'],
             'rows': [['val1', 'val2'], ['val3', 'val4']]},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_renders_code_block(self):
        """generate() renders fenced code blocks without error."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'code', 'language': 'python', 'content': 'print("hello")'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_renders_blockquote_block(self):
        """generate() renders blockquote blocks without error."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'blockquote', 'text': 'This is a quote.'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_renders_separator_block(self):
        """generate() renders separator blocks without error."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'paragraph', 'text': 'Before separator.'},
            {'type': 'separator'},
            {'type': 'paragraph', 'text': 'After separator.'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_renders_callout_note_block(self):
        """generate() renders callout note blocks without error."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'callout', 'style': 'note', 'text': 'Important information.'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_renders_section_header_block(self):
        """generate() renders section_header blocks without error."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'section_header', 'index': '01', 'title': 'Introducción'},
            {'type': 'paragraph', 'text': 'Section content.'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_renders_sub_section_block(self):
        """generate() renders sub_section blocks without error."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'sub_section', 'index': '1.1', 'title': 'Detalle'},
            {'type': 'paragraph', 'text': 'Sub-section content.'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_skips_unknown_block_types_gracefully(self):
        """generate() skips unknown block types without raising an exception."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'totally_unknown_block', 'data': 'ignored'},
            {'type': 'paragraph', 'text': 'Still renders.'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_with_include_subportada_renders_title_page(self):
        """generate() renders a title page when include_subportada=True."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(
            include_subportada=True,
            content_json=_with_blocks([
                {'type': 'paragraph', 'text': 'Document content.'},
            ]),
        )
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'


    def test_generate_with_toc_block_renders_table_of_contents(self):
        """generate() renders a TOC page when blocks include a [toc] block."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'toc'},
            {'type': 'section_header', 'index': '01', 'title': 'Sección Uno'},
            {'type': 'paragraph', 'text': 'Content of section one.'},
            {'type': 'section_header', 'index': '02', 'title': 'Sección Dos'},
            {'type': 'paragraph', 'text': 'Content of section two.'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'


    def test_generate_returns_none_on_unexpected_exception(self):
        """generate() returns None when an unexpected exception is raised."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'paragraph', 'text': 'Some text.'},
        ]))
        with patch(
            'content.services.document_pdf_service.DocumentPdfService._merge_with_covers',
            side_effect=RuntimeError('unexpected'),
        ):
            result = DocumentPdfService.generate(doc)

        assert result is None


    def test_generate_toc_not_first_block_flushes_previous_page(self):
        """generate() flushes the current page before the TOC when toc is not the first block."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'paragraph', 'text': 'Intro paragraph before TOC.'},
            {'type': 'toc'},
            {'type': 'section_header', 'index': '01', 'title': 'Section'},
            {'type': 'paragraph', 'text': 'Body.'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'


    def test_generate_toc_with_heading_blocks_creates_toc_entries(self):
        """generate() creates TOC entries for h1/h2 headings when TOC is present."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'toc'},
            {'type': 'heading', 'level': 1, 'text': 'Chapter One'},
            {'type': 'paragraph', 'text': 'Chapter content.'},
            {'type': 'heading', 'level': 2, 'text': 'Sub Chapter'},
            {'type': 'paragraph', 'text': 'Sub content.'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_title_page_with_subtitle_in_meta(self):
        """generate() renders the subtitle label on the title page when meta has subtitle."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(
            include_subportada=True,
            content_json={
                'meta': {'client_name': 'Client', 'subtitle': 'Technical Specification'},
                'blocks': [{'type': 'paragraph', 'text': 'Content.'}],
            },
        )
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


    def test_generate_renders_mixed_block_types(self):
        """generate() renders all block types in a single document without error."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'heading', 'level': 1, 'text': 'Title'},
            {'type': 'paragraph', 'text': 'A paragraph.'},
            {'type': 'list', 'ordered': False, 'items': [
                {'text': 'Item', 'children': []},
            ]},
            {'type': 'table', 'headers': ['A'], 'rows': [['1']]},
            {'type': 'code', 'language': 'text', 'content': 'code here'},
            {'type': 'blockquote', 'text': 'A quote.'},
            {'type': 'callout', 'style': 'warning', 'text': 'Caution.'},
            {'type': 'separator'},
            {'type': 'section_header', 'index': '01', 'title': 'Sec'},
            {'type': 'sub_section', 'index': '1.1', 'title': 'Sub'},
        ]))
        result = DocumentPdfService.generate(doc)

        assert isinstance(result, bytes)


# ── generate_from_markdown() ──────────────────────────────────────────────

class TestDocumentPdfServiceGenerateFromMarkdown:
    @pytest.fixture(autouse=True)
    def _bypass_merge(self):
        with patch(
            'content.services.document_pdf_service.DocumentPdfService._merge_with_covers',
            side_effect=lambda b, **kw: b,
        ):
            yield

    def test_generate_from_markdown_returns_pdf_bytes(self):
        """generate_from_markdown() returns PDF bytes for a valid markdown string."""
        from content.services.document_pdf_service import DocumentPdfService

        result = DocumentPdfService.generate_from_markdown(
            markdown_text='# Title\n\nThis is a paragraph.',
            client_name='Test Client',
            title='Test Doc',
        )

        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'

    def test_generate_from_markdown_with_empty_string_returns_none(self):
        """generate_from_markdown() returns None for an empty string."""
        from content.services.document_pdf_service import DocumentPdfService

        result = DocumentPdfService.generate_from_markdown(
            markdown_text='',
            client_name='C',
            title='T',
        )

        assert result is None

    def test_generate_returns_none_on_unexpected_exception(self):
        """generate() returns None when an unhandled exception occurs."""
        from content.services.document_pdf_service import DocumentPdfService

        doc = _document(content_json=_with_blocks([
            {'type': 'paragraph', 'text': 'Hello.'},
        ]))

        with patch(
            'content.services.document_pdf_service._register_fonts',
            side_effect=RuntimeError('font error'),
        ):
            result = DocumentPdfService.generate(doc)

        assert result is None
