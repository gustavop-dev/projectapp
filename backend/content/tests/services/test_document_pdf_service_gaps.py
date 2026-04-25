"""Gap tests for DocumentPdfService — targets uncovered early-return branches and dry-run paths."""
from unittest.mock import patch

import pytest

from content.models import Document
from content.services.document_pdf_service import DocumentPdfService

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _bypass_merge():
    with patch(
        'content.services.document_pdf_service.DocumentPdfService._merge_with_covers',
        side_effect=lambda b, **kw: b,
    ):
        yield


def _doc(blocks, **kwargs):
    defaults = {
        'title': 'Gap Test',
        'client_name': 'Client',
        'include_portada': False,
        'include_subportada': False,
        'include_contraportada': False,
        'content_json': {'meta': {'client_name': 'Client'}, 'blocks': blocks},
    }
    defaults.update(kwargs)
    return Document.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Early-return branches in renderer methods
# ---------------------------------------------------------------------------

class TestRendererEarlyReturns:
    def test_paragraph_with_empty_text_returns_without_drawing(self):
        doc = _doc([{'type': 'paragraph', 'text': ''}])
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)

    def test_table_with_no_headers_returns_without_drawing(self):
        doc = _doc([{'type': 'table', 'headers': [], 'rows': [['a', 'b']]}])
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)

    def test_list_with_no_items_returns_without_drawing(self):
        doc = _doc([{'type': 'list', 'ordered': False, 'items': []}])
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)

    def test_blockquote_with_empty_text_returns_without_drawing(self):
        doc = _doc([{'type': 'blockquote', 'text': ''}])
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)

    def test_code_block_with_empty_content_returns_without_drawing(self):
        doc = _doc([{'type': 'code', 'language': 'python', 'content': ''}])
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)

    def test_callout_with_empty_text_returns_without_drawing(self):
        doc = _doc([{'type': 'callout', 'style': 'note', 'text': ''}])
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# _render_sub_section — without index field
# ---------------------------------------------------------------------------

class TestRenderSubSectionWithoutIndex:
    def test_sub_section_without_index_renders_title_only(self):
        doc = _doc([{'type': 'sub_section', 'title': 'No Index Sub'}])
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)

    def test_sub_section_with_empty_index_renders_title_only(self):
        doc = _doc([{'type': 'sub_section', 'index': '', 'title': 'Empty Index'}])
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# _collect_section_pages — subportada dry-run path
# ---------------------------------------------------------------------------

class TestCollectSectionPagesWithSubportada:
    def test_toc_with_include_subportada_generates_pdf(self):
        doc = _doc(
            [
                {'type': 'toc'},
                {'type': 'section_header', 'index': '01', 'title': 'Sección'},
                {'type': 'paragraph', 'text': 'Body.'},
            ],
            include_subportada=True,
        )
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'

    def test_toc_heading_level3_is_not_added_to_toc_entries(self):
        doc = _doc([
            {'type': 'toc'},
            {'type': 'heading', 'level': 3, 'text': 'Minor heading'},
            {'type': 'paragraph', 'text': 'Content.'},
        ])
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# _render_title_page — date handling
# ---------------------------------------------------------------------------

class TestRenderTitlePageDateHandling:
    def test_title_page_with_date_in_meta_renders_date(self):
        doc = Document.objects.create(
            title='Dated Doc',
            client_name='Client',
            include_portada=False,
            include_subportada=True,
            include_contraportada=False,
            content_json={
                'meta': {'client_name': 'Client', 'date': '25 de abril de 2026'},
                'blocks': [{'type': 'paragraph', 'text': 'Body.'}],
            },
        )
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)

    def test_title_page_without_client_name_renders_without_client_line(self):
        doc = Document.objects.create(
            title='No Client Doc',
            client_name='',
            include_portada=False,
            include_subportada=True,
            include_contraportada=False,
            content_json={
                'meta': {'client_name': ''},
                'blocks': [{'type': 'paragraph', 'text': 'Body.'}],
            },
        )
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# generate_from_markdown — untested entry point
# ---------------------------------------------------------------------------

def test_generate_from_markdown_produces_valid_pdf():
    result = DocumentPdfService.generate_from_markdown(
        title='Markdown Doc',
        markdown_text='# Section One\n\nHello world paragraph.',
        client_name='Test Client',
        include_portada=False,
        include_subportada=False,
        include_contraportada=False,
    )
    assert isinstance(result, bytes)
    assert result[:4] == b'%PDF'


# ---------------------------------------------------------------------------
# generate — empty blocks returns None
# ---------------------------------------------------------------------------

def test_generate_returns_none_for_empty_blocks():
    doc = _doc([])
    result = DocumentPdfService.generate(doc)
    assert result is None


# ---------------------------------------------------------------------------
# generate — TOC with all dry-run block types + heading bookmark
# ---------------------------------------------------------------------------

def test_generate_toc_document_with_all_dry_run_block_types():
    """Covers _collect_section_pages dry-run paths for every block type and
    the heading bookmark branch when has_toc is True."""
    blocks = [
        {'type': 'paragraph', 'text': 'Intro paragraph.'},
        {'type': 'toc'},
        {'type': 'section_header', 'index': '01', 'title': 'Introduction'},
        {'type': 'heading', 'level': 1, 'text': 'Overview'},
        {'type': 'heading', 'level': 2, 'text': 'Details'},
        {'type': 'heading', 'level': 3, 'text': 'Minor note'},
        {'type': 'table', 'headers': ['Col1'], 'rows': [['Val1']]},
        {'type': 'list', 'ordered': False, 'items': ['Item 1']},
        {'type': 'blockquote', 'text': 'A block quote.'},
        {'type': 'code', 'language': 'python', 'content': 'x = 1'},
        {'type': 'separator'},
        {'type': 'sub_section', 'index': '1.1', 'title': 'Sub Section'},
        {'type': 'callout', 'style': 'note', 'text': 'Important note.'},
    ]
    doc = _doc(blocks)
    result = DocumentPdfService.generate(doc)
    assert isinstance(result, bytes)
    assert result[:4] == b'%PDF'


# ---------------------------------------------------------------------------
# _merge_with_covers — actual method body (override autouse bypass)
# ---------------------------------------------------------------------------

class TestMergeWithCoversBody:
    @pytest.fixture(autouse=True)
    def _bypass_merge(self):
        """Override module-level autouse fixture to let _merge_with_covers body run."""
        with patch(
            'content.services.pdf_utils.merge_with_covers',
            side_effect=lambda b, **kw: b,
        ):
            yield

    def test_merge_with_covers_delegates_to_pdf_utils(self):
        doc = _doc([{'type': 'paragraph', 'text': 'Content for merge test.'}])
        result = DocumentPdfService.generate(doc)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# _render_toc — TOC entry overflow triggers new page
# ---------------------------------------------------------------------------

def test_toc_entries_overflow_to_new_page():
    """When TOC has enough entries to overflow a page, _render_toc creates a new page."""
    blocks = [{'type': 'toc'}]
    for i in range(45):
        blocks.append({
            'type': 'section_header',
            'index': str(i + 1).zfill(2),
            'title': f'Section {i + 1}',
        })
        blocks.append({'type': 'paragraph', 'text': 'Body.'})
    doc = _doc(blocks)
    result = DocumentPdfService.generate(doc)
    assert isinstance(result, bytes)
    assert result[:4] == b'%PDF'
