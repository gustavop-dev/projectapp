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
    include_portada=None,
    include_subportada=None,
    include_contraportada=None,
):
    """Build a mock Document with the attributes used by DocumentPdfService."""
    doc = MagicMock()
    doc.id = 1
    doc.title = title
    doc.client_name = client_name
    doc.cover_type = cover_type
    doc.language = language
    doc.created_at = datetime.datetime(2025, 6, 15, 10, 0, 0)

    # Derive boolean flags from cover_type when not explicitly provided
    if include_portada is None:
        doc.include_portada = cover_type == 'proposal'
    else:
        doc.include_portada = include_portada
    if include_subportada is None:
        doc.include_subportada = cover_type != 'none'
    else:
        doc.include_subportada = include_subportada
    if include_contraportada is None:
        doc.include_contraportada = cover_type != 'none'
    else:
        doc.include_contraportada = include_contraportada

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

def test_with_subportada_produces_longer_pdf_than_without():
    blocks = [{'type': 'paragraph', 'text': 'Cover test'}]
    doc_with = _make_document(blocks=blocks, include_subportada=True, include_portada=False, include_contraportada=False)
    doc_without = _make_document(blocks=blocks, include_subportada=False, include_portada=False, include_contraportada=False)

    result_with = DocumentPdfService.generate(doc_with)
    result_without = DocumentPdfService.generate(doc_without)

    # subportada adds an extra title page so the PDF should be larger
    assert len(result_with) > len(result_without)


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


# -- TOC block -----------------------------------------------------------

def test_toc_block_renders_valid_pdf():
    blocks = [
        {'type': 'toc'},
        {'type': 'section_header', 'index': '01', 'title': 'Introducción'},
        {'type': 'paragraph', 'text': 'Texto de intro.'},
        {'type': 'section_header', 'index': '02', 'title': 'Análisis'},
        {'type': 'paragraph', 'text': 'Texto de análisis.'},
    ]
    doc = _make_document(blocks=blocks, include_subportada=False, include_portada=False, include_contraportada=False)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)
    assert result[:5] == b'%PDF-'


def test_toc_with_subportada_renders_valid_pdf():
    blocks = [
        {'type': 'toc'},
        {'type': 'section_header', 'index': '01', 'title': 'Capítulo Uno'},
        {'type': 'paragraph', 'text': 'Contenido del capítulo.'},
    ]
    doc = _make_document(blocks=blocks, include_subportada=True, include_portada=False, include_contraportada=False)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)
    assert result[:5] == b'%PDF-'


def test_document_without_toc_block_is_unaffected():
    blocks = [
        {'type': 'section_header', 'index': '01', 'title': 'Sin Índice'},
        {'type': 'paragraph', 'text': 'Documento sin bloque [TOC].'},
    ]
    doc = _make_document(blocks=blocks, include_subportada=False, include_portada=False, include_contraportada=False)

    result = DocumentPdfService.generate(doc)

    assert isinstance(result, bytes)
    assert result[:5] == b'%PDF-'


def test_toc_produces_larger_pdf_than_same_doc_without_toc():
    content_blocks = [
        {'type': 'section_header', 'index': '01', 'title': 'Sección A'},
        {'type': 'paragraph', 'text': 'Texto A.'},
        {'type': 'section_header', 'index': '02', 'title': 'Sección B'},
        {'type': 'paragraph', 'text': 'Texto B.'},
    ]
    doc_with_toc = _make_document(
        blocks=[{'type': 'toc'}] + content_blocks,
        include_subportada=False, include_portada=False, include_contraportada=False,
    )
    doc_without_toc = _make_document(
        blocks=content_blocks,
        include_subportada=False, include_portada=False, include_contraportada=False,
    )

    result_with = DocumentPdfService.generate(doc_with_toc)
    result_without = DocumentPdfService.generate(doc_without_toc)

    assert len(result_with) > len(result_without)
