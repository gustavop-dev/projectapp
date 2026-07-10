"""Tests for content.services.email_markdown.

Covers normalize_sections (dual payload shapes) and markdown_to_email_html
(escaping, inline formats, link scheme whitelist, block rendering).
"""
import pytest

from content.services.email_markdown import (
    markdown_to_email_html,
    normalize_sections,
)


# ── normalize_sections ────────────────────────────────────────────────────────

class TestNormalizeSections:
    def test_accepts_legacy_plain_strings(self):
        assert normalize_sections(['hola', 'mundo']) == [
            {'text': 'hola', 'markdown': False},
            {'text': 'mundo', 'markdown': False},
        ]

    def test_accepts_dict_shape_and_coerces_markdown_to_bool(self):
        result = normalize_sections([
            {'text': '**a**', 'markdown': True},
            {'text': 'b', 'markdown': 'yes'},
            {'text': 'c'},
        ])
        assert result == [
            {'text': '**a**', 'markdown': True},
            {'text': 'b', 'markdown': True},
            {'text': 'c', 'markdown': False},
        ]

    def test_mixed_shapes_filters_empties_and_garbage(self):
        result = normalize_sections([
            'plano', '   ', {'text': '  '}, {'text': 'md', 'markdown': True},
            42, None, {'markdown': True}, ['nested'],
        ])
        assert result == [
            {'text': 'plano', 'markdown': False},
            {'text': 'md', 'markdown': True},
        ]

    def test_non_list_input_returns_empty(self):
        assert normalize_sections('not a list') == []
        assert normalize_sections(None) == []
        assert normalize_sections({'text': 'x'}) == []


# ── markdown_to_email_html — safety ──────────────────────────────────────────

class TestMarkdownToEmailHtmlSafety:
    def test_escapes_raw_html(self):
        html = markdown_to_email_html('<script>alert(1)</script>')
        assert '<script' not in html
        assert '&lt;script&gt;' in html

    def test_https_and_mailto_links_allowed(self):
        html = markdown_to_email_html(
            '[web](https://projectapp.co) y [correo](mailto:team@projectapp.co)',
        )
        assert '<a href="https://projectapp.co"' in html
        assert '<a href="mailto:team@projectapp.co"' in html

    def test_javascript_and_data_schemes_stay_literal_text(self):
        html = markdown_to_email_html('[x](javascript:alert(1)) y [y](data:text/html,z)')
        assert '<a ' not in html
        assert 'javascript:alert(1)' in html

    def test_code_fence_content_is_escaped_and_untransformed(self):
        html = markdown_to_email_html('```\n**no bold** <b>tag</b>\n```')
        assert '<pre style=' in html
        assert '<strong' not in html
        assert '&lt;b&gt;tag&lt;/b&gt;' in html


# ── markdown_to_email_html — rendering ───────────────────────────────────────

class TestMarkdownToEmailHtmlRendering:
    def test_bold_italic_and_inline_code(self):
        html = markdown_to_email_html('Hola **negrita** con *cursiva* y `codigo`.')
        assert '<strong style="font-weight:500;">negrita</strong>' in html
        assert '<em>cursiva</em>' in html
        assert '>codigo</code>' in html

    def test_inline_code_is_protected_from_inline_transforms(self):
        html = markdown_to_email_html('usa `**esto**` literal')
        assert '**esto**' in html
        assert '<strong' not in html

    def test_headings_map_to_styled_levels(self):
        html = markdown_to_email_html('# Uno\n\n## Dos\n\n### Tres')
        assert 'font-size:22px' in html
        assert 'font-size:19px' in html
        assert html.count('font-weight:700') >= 1

    def test_nested_unordered_list(self):
        html = markdown_to_email_html('- padre\n  - hijo\n- otro')
        assert html.count('<ul') == 2
        assert '<li' in html and 'hijo' in html

    def test_ordered_list(self):
        html = markdown_to_email_html('1. primero\n2. segundo')
        assert '<ol' in html and 'segundo' in html

    def test_blockquote_and_separator(self):
        html = markdown_to_email_html('> cita importante\n\n---')
        assert 'border-left:3px solid #F0FF3D' in html
        assert 'height:1px;background:#ece8db' in html

    def test_table_renders_headers_and_rows(self):
        html = markdown_to_email_html('| A | B |\n| --- | --- |\n| 1 | 2 |')
        assert '<table' in html and '<th' in html and '<td' in html

    def test_paragraphs_use_branded_body_style(self):
        html = markdown_to_email_html('texto simple')
        assert 'font-size:16px;line-height:26px;color:#001713' in html

    def test_empty_input_returns_empty_string(self):
        assert markdown_to_email_html('') == ''
        assert markdown_to_email_html(None) == ''
