"""Ported documents deltas tested against the canonical #99 layout engine.

Covers only the four additive deltas re-applied on top of PR #99's
``pdf_utils`` engine:

  1. theme threading through the shared drawers (theme=None keeps the
     professional/legacy look, which equals the historical constants),
  2. multi-level nested bullet lists (also backward-compatible with the
     plain-string items proposals pass),
  3. content-proportional table column widths (``_table_col_widths``),
  4. long code-line wrapping (``_wrap_code_line``).

It deliberately does NOT test the dropped measured-wrapping engine
(``_layout_inline`` / ``_draw_fragments_line``) — those are gone.
"""
import io

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

from content.services import pdf_utils as u
from content.services.pdf_theme import FRIENDLY_THEME, PROFESSIONAL_THEME

pytestmark = pytest.mark.django_db


def _canvas():
    u._register_fonts()
    buf = io.BytesIO()
    return rl_canvas.Canvas(buf, pagesize=A4), buf


class TestThemeThreading:
    def test_resolve_theme_defaults_professional(self):
        assert u._resolve_theme(None) is PROFESSIONAL_THEME
        assert u._resolve_theme(FRIENDLY_THEME) is FRIENDLY_THEME

    def test_drawers_accept_theme_kwarg_and_render(self):
        c, buf = _canvas()
        y = u.PAGE_H - u.MARGIN_T
        for theme in (None, PROFESSIONAL_THEME, FRIENDLY_THEME):
            u._draw_header_bar(c, theme=theme)
            y = u._draw_section_header(c, y, '01', 'Titulo de seccion',
                                       theme=theme)
            y = u._draw_paragraphs(c, y, ['Un parrafo con projectapp.co'],
                                   ps=None, link_color=None)
            y = u._draw_blockquote(c, y, 'Una **cita** de prueba', theme=theme)
            y = u._draw_code_block(c, y, 'print("hola")', theme=theme)
            y = u._draw_separator(c, y, theme=theme)
            y = u._draw_table(c, y, ['A', 'B'], [['1', '2'], ['3', '4']],
                              theme=theme)
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'

    def test_professional_default_header_and_section_colors_match_legacy(self):
        # The whole point of theme=None: proposals render byte-identical.
        t = PROFESSIONAL_THEME
        assert t.header_bar_color == u.ESMERALD
        assert t.header_dot_color == u.LEMON
        assert t.section_index_color == u.GREEN_LIGHT
        assert t.section_title_color == u.ESMERALD
        assert t.section_rule_color == u.LEMON

    def test_professional_default_table_colors_match_legacy(self):
        t = PROFESSIONAL_THEME
        assert t.table_header_bg == u.ESMERALD
        assert t.table_header_text == u.WHITE
        assert t.table_stripe_bg == u.ESMERALD_LIGHT
        assert t.table_row_bg == u.WHITE
        assert t.table_body_text == u.ESMERALD_80
        assert t.table_border_color == u.GRAY_300

    def test_professional_default_quote_code_and_rule_colors_match_legacy(self):
        t = PROFESSIONAL_THEME
        assert t.quote_bg == u.BONE
        assert t.quote_accent == u.LEMON
        assert t.quote_text == u.ESMERALD
        assert t.code_bg == u.GRAY_200
        assert t.code_border == u.GRAY_300
        assert t.code_text == u.ESMERALD_80
        assert t.rule_color == u.GRAY_300


class TestNestedLists:
    def test_three_level_nesting_renders(self):
        c, buf = _canvas()
        items = [
            {'text': 'nivel uno', 'children': [
                {'text': 'nivel dos', 'children': [
                    {'text': 'nivel tres', 'children': []},
                ]},
            ]},
            {'text': 'otro nivel uno', 'children': []},
        ]
        start = u.PAGE_H - u.MARGIN_T
        y = u._draw_bullet_list(
            c, start, items,
            ps={'num': 1, 'client': '', 'total': None})
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'
        assert y < start  # advanced down the page

    def test_legacy_dict_with_string_children_render(self):
        c, buf = _canvas()
        items = [{'text': 'padre', 'children': ['hijo a', 'hijo b']}]
        u._draw_bullet_list(c, u.PAGE_H - u.MARGIN_T, items)
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'

    def test_legacy_plain_string_items_render(self):
        # Proposals pass flat string bullets; they must keep working.
        c, buf = _canvas()
        u._draw_bullet_list(c, u.PAGE_H - u.MARGIN_T, ['uno', 'dos', 'tres'])
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'

    def test_numbered_nested_list_renders(self):
        c, buf = _canvas()
        items = [{'text': 'primero', 'children': [
            {'text': 'sub', 'children': []}]}]
        u._draw_bullet_list(c, u.PAGE_H - u.MARGIN_T, items, numbered=True)
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'

    def test_normalize_accepts_all_shapes(self):
        assert u._normalize_list_item('x') == {'text': 'x', 'children': []}
        nested = u._normalize_list_item(
            {'text': 'p', 'children': ['a', {'text': 'b', 'children': []}]})
        assert nested['text'] == 'p'
        assert nested['children'][0] == {'text': 'a', 'children': []}
        assert nested['children'][1]['text'] == 'b'
        assert nested['children'][1]['children'] == []


class TestTableColWidths:
    def test_wide_column_gets_more_than_narrow(self):
        headers = ['ID', 'Descripcion larga que necesita mucho espacio']
        rows = [['1', 'x' * 120], ['2', 'y' * 100]]
        widths = u._table_col_widths(headers, rows, u.CONTENT_W, 6)
        assert len(widths) == 2
        assert widths[1] > widths[0]

    def test_widths_sum_to_max_width(self):
        headers = ['A', 'B', 'C']
        rows = [['aa', 'bbbb', 'c'], ['a', 'bb', 'cccccc']]
        widths = u._table_col_widths(headers, rows, u.CONTENT_W, 6)
        assert abs(sum(widths) - u.CONTENT_W) < 1.0

    def test_many_narrow_columns_still_positive_and_sum(self):
        headers = [f'C{i}' for i in range(12)]
        rows = [['x'] * 12]
        widths = u._table_col_widths(headers, rows, u.CONTENT_W, 6)
        assert len(widths) == 12
        assert all(w > 0 for w in widths)
        assert abs(sum(widths) - u.CONTENT_W) < 1.0

    def test_empty_headers_returns_empty(self):
        assert u._table_col_widths([], [], u.CONTENT_W, 6) == []


class TestWrapCodeLine:
    def test_short_line_unchanged(self):
        assert u._wrap_code_line('short line', 8, 400) == ['short line']

    def test_long_line_wraps_within_width(self):
        line = 'def funcion(' + 'a' * 200 + '):'
        max_w = 200
        pieces = u._wrap_code_line(line, 8, max_w)
        assert len(pieces) > 1
        for p in pieces:
            assert u._string_width_mixed(p, 'Courier', 8) <= max_w + 0.5

    def test_content_preserved_after_wrap(self):
        line = 'x' * 300
        pieces = u._wrap_code_line(line, 8, 150)
        reconstructed = ''.join(p.lstrip() for p in pieces)
        assert reconstructed == line
