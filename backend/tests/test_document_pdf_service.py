"""
Tests for DocumentPdfService.generate() in content/services/document_pdf_service.py.

Uses a mock Document object to avoid database access.
Each test verifies ONE specific behaviour following the AAA pattern.
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from content.services.document_pdf_service import DocumentPdfService


def _make_document(
    blocks=None,
    meta=None,
    title='Test Document',
    client_name='Acme Corp',
    cover_type='generic',
    language='es',
):
    """Build a mock Document with the attributes used by DocumentPdfService."""
    doc = MagicMock()
    doc.id = 1
    doc.title = title
    doc.client_name = client_name
    doc.cover_type = cover_type
    doc.language = language
    doc.created_at = datetime.datetime(2025, 6, 15, 10, 0, 0)

    content_json = {}
    if meta is not None:
        content_json['meta'] = meta
    if blocks is not None:
        content_json['blocks'] = blocks
    doc.content_json = content_json

    return doc


# -- Basic contract -----------------------------------------------------------

def test_returns_none_when_document_has_no_blocks():
    doc = _make_document(blocks=[])

    result = DocumentPdfService.generate(doc)

    assert result is None


def test_returns_none_when_content_json_is_empty():
    doc = _make_document()
    doc.content_json = {}

    result = DocumentPdfService.generate(doc)

    assert result is None


def test_returns_bytes_when_document_has_valid_blocks():
    doc = _make_document(blocks=[{'type': 'paragraph', 'text': 'Hello world'}])

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)
    assert len(result) > 0


def test_generated_pdf_starts_with_pdf_magic_bytes():
    doc = _make_document(blocks=[{'type': 'paragraph', 'text': 'Check magic'}])

    result = DocumentPdfService.generate(doc)

    assert result[:5] == b'%PDF-'


# -- Individual block types ---------------------------------------------------

def test_handles_heading_blocks():
    blocks = [{'type': 'heading', 'level': 1, 'text': 'Main Heading'}]
    doc = _make_document(blocks=blocks)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)
    assert len(result) > 0


def test_handles_paragraph_blocks():
    blocks = [{'type': 'paragraph', 'text': 'A paragraph of text.'}]
    doc = _make_document(blocks=blocks)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)


def test_handles_table_blocks():
    blocks = [{
        'type': 'table',
        'headers': ['Col A', 'Col B'],
        'rows': [['val1', 'val2']],
    }]
    doc = _make_document(blocks=blocks)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)


def test_handles_unordered_list_blocks():
    blocks = [{'type': 'list', 'ordered': False, 'items': ['one', 'two']}]
    doc = _make_document(blocks=blocks)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)


def test_handles_ordered_list_blocks():
    blocks = [{'type': 'list', 'ordered': True, 'items': ['first', 'second']}]
    doc = _make_document(blocks=blocks)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)


def test_handles_blockquote_blocks():
    blocks = [{'type': 'blockquote', 'text': 'A wise quote'}]
    doc = _make_document(blocks=blocks)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)


def test_handles_code_blocks():
    blocks = [{'type': 'code', 'language': 'python', 'content': 'x = 1'}]
    doc = _make_document(blocks=blocks)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)


def test_handles_separator_blocks():
    blocks = [{'type': 'separator'}]
    doc = _make_document(blocks=blocks)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)


def test_handles_section_header_blocks():
    blocks = [{'type': 'section_header', 'index': '01', 'title': 'Intro'}]
    doc = _make_document(blocks=blocks)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)


def test_handles_sub_section_blocks():
    blocks = [{'type': 'sub_section', 'index': '1.1', 'title': 'Details'}]
    doc = _make_document(blocks=blocks)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)


# -- Cover type behaviour ------------------------------------------------------

def test_generic_cover_type_produces_longer_pdf():
    blocks = [{'type': 'paragraph', 'text': 'Cover test'}]
    doc_generic = _make_document(blocks=blocks, cover_type='generic')
    doc_none = _make_document(blocks=blocks, cover_type='none')

    result_generic = DocumentPdfService.generate(doc_generic)
    result_none = DocumentPdfService.generate(doc_none)

    # generic includes a title page so the PDF should be larger
    assert len(result_generic) > len(result_none)


def test_none_cover_type_skips_title_page():
    blocks = [{'type': 'paragraph', 'text': 'No cover'}]
    doc = _make_document(
        blocks=blocks,
        meta={'cover_type': 'none'},
        cover_type='none',
    )

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)
    assert result[:5] == b'%PDF-'


# -- Combined blocks ----------------------------------------------------------

def test_handles_document_with_all_block_types_combined():
    blocks = [
        {'type': 'section_header', 'index': '01', 'title': 'Section'},
        {'type': 'heading', 'level': 2, 'text': 'Heading Two'},
        {'type': 'sub_section', 'index': '1.1', 'title': 'Sub'},
        {'type': 'paragraph', 'text': 'Some paragraph text.'},
        {'type': 'list', 'ordered': False, 'items': ['a', 'b']},
        {'type': 'list', 'ordered': True, 'items': ['1', '2']},
        {'type': 'table', 'headers': ['H1', 'H2'], 'rows': [['r1', 'r2']]},
        {'type': 'blockquote', 'text': 'Quote here'},
        {'type': 'code', 'language': 'js', 'content': 'console.log(1)'},
        {'type': 'separator'},
    ]
    doc = _make_document(blocks=blocks)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)
    assert len(result) > 100


# -- New block types (callout + nested list) ----------------------------------

def test_callout_block_renders_without_error():
    blocks = [
        {'type': 'callout', 'style': 'warning', 'text': 'This is a **warning** callout.'},
    ]
    doc = _make_document(blocks=blocks, cover_type='none')

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)
    assert result[:5] == b'%PDF-'


def test_all_callout_styles_render_without_error():
    blocks = [
        {'type': 'callout', 'style': style, 'text': f'Callout text for {style}.'}
        for style in ('note', 'tip', 'important', 'warning', 'caution')
    ]
    doc = _make_document(blocks=blocks, cover_type='none')

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)


def test_nested_list_block_renders_without_error():
    blocks = [
        {'type': 'list', 'ordered': False, 'items': [
            {'text': 'Parent item A', 'children': ['Child 1', 'Child 2']},
            {'text': 'Parent item B', 'children': []},
        ]},
    ]
    doc = _make_document(blocks=blocks, cover_type='none')

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)
    assert result[:5] == b'%PDF-'


def test_inline_formatting_in_paragraph_renders_without_error():
    blocks = [
        {'type': 'paragraph', 'text': (
            'Text with *italic*, **bold**, ***bold-italic***, '
            '`inline_code`, ~~strikethrough~~, and [a link](https://example.com).'
        )},
    ]
    doc = _make_document(blocks=blocks, cover_type='none')

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)
