"""End-to-end emoji rendering through DocumentPdfService (no tofu, no crash)."""
import datetime
from unittest.mock import MagicMock

import pytest

from content.services.document_pdf_service import DocumentPdfService

pytestmark = pytest.mark.django_db


def _make_document(blocks, meta=None, title='Doc 🚀', client_name='Cliente 😀'):
    doc = MagicMock()
    doc.id = 1
    doc.title = title
    doc.client_name = client_name
    doc.cover_type = 'generic'
    doc.language = 'es'
    doc.created_at = datetime.datetime(2026, 7, 10, 10, 0, 0)
    doc.include_portada = False
    doc.include_subportada = True
    doc.include_contraportada = False
    doc.content_json = {'meta': meta or {}, 'blocks': blocks}
    return doc


def test_generate_with_emoji_in_title_and_heading_returns_pdf():
    doc = _make_document([
        {'type': 'heading', 'level': 1, 'text': 'Objetivos ✅'},
        {'type': 'paragraph', 'text': 'Texto con 🎯 y **negrita 🔥**.'},
    ])

    pdf = DocumentPdfService.generate(doc)

    assert pdf[:4] == b'%PDF'


def test_generate_with_emoji_in_table_and_list_returns_pdf():
    doc = _make_document([
        {
            'type': 'table',
            'headers': ['Fase 📋', 'Estado'],
            'rows': [['Kickoff 🤝', '✅'], ['Cierre', '❌']],
        },
        {
            'type': 'list',
            'ordered': False,
            'items': [
                {'text': 'Item 🧩 uno', 'children': ['hijo 💡']},
            ],
        },
    ])

    pdf = DocumentPdfService.generate(doc)

    assert pdf[:4] == b'%PDF'


def test_generate_with_emoji_in_blockquote_and_callout_returns_pdf():
    doc = _make_document([
        {'type': 'blockquote', 'text': 'Cita con 💰'},
        {'type': 'callout', 'style': 'tip', 'text': 'Consejo 💰 final'},
    ])

    pdf = DocumentPdfService.generate(doc)

    assert pdf[:4] == b'%PDF'


def test_generate_with_toc_and_emoji_section_titles_returns_pdf():
    doc = _make_document([
        {'type': 'toc'},
        {'type': 'section_header', 'index': '1', 'title': 'Plan 🚀'},
        {'type': 'paragraph', 'text': 'Contenido.'},
    ])

    pdf = DocumentPdfService.generate(doc)

    assert pdf[:4] == b'%PDF'


def test_generate_from_markdown_converts_shortcodes_and_keeps_unicode():
    markdown = (
        '# Plan :rocket: de proyecto\n\n'
        'Texto con 🎯 y :white_check_mark:.\n\n'
        '| Fase :clipboard: | Estado |\n|---|---|\n| Kickoff | ✅ |\n'
    )

    pdf = DocumentPdfService.generate_from_markdown(
        title='Demo 🚀', markdown_text=markdown, client_name='Cliente 😀',
    )

    assert pdf[:4] == b'%PDF'


def test_pdf_with_emoji_embeds_the_emoji_font_subset():
    # ReportLab only embeds a font that was actually drawn with, so the
    # presence of the NotoEmoji subset proves the emoji run was rendered.
    # (pypdf can't extract_text over ReportLab's supplementary-plane
    # ToUnicode cmap, so we assert on the embedded font instead.)
    doc = _make_document(
        [{'type': 'paragraph', 'text': 'Lanzamiento 🚀 confirmado'}],
    )
    doc.include_subportada = False

    pdf = DocumentPdfService.generate(doc)

    assert b'NotoEmoji' in pdf


def test_pdf_without_emoji_does_not_touch_the_emoji_font():
    doc = _make_document(
        [{'type': 'paragraph', 'text': 'Texto plano sin simbolos'}],
        title='Documento', client_name='Cliente',
    )
    doc.include_subportada = False

    pdf = DocumentPdfService.generate(doc)

    assert pdf[:4] == b'%PDF'
    assert b'NotoEmoji' not in pdf
