"""Second batch of pdf_utils gap tests.

Targets remaining missing branches after test_pdf_utils_gaps.py:
- _draw_paragraphs: ps + multi-line + low y → new page
- _draw_bullet_list: nested children + y near bottom (no ps)
- _draw_table: ps-triggered pagination during rows
- _draw_callout_box: body text pagination with ps
- _draw_code_block: large block rendered without ps
- merge_with_covers: include_portada=False, include_contraportada=True
- _draw_toc_page: long title leaves no room for dot-leaders
"""
import io

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _make_canvas():
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    return c, buf


def _make_ps(num=1):
    return {'num': num, 'client': 'Test Client', 'total': None}


@pytest.fixture(autouse=True)
def register_fonts():
    from content.services.pdf_utils import _register_fonts
    _register_fonts()


# ===========================================================================
# _draw_paragraphs — pagination triggered (ps + multi-line + low y)
# ===========================================================================

class TestDrawParagraphsPagination:
    def test_triggers_new_page_when_y_near_bottom_with_ps(self):
        """Multi-line paragraph at very low y with ps triggers _new_page."""
        from content.services.pdf_utils import MARGIN_B, _draw_paragraphs

        c, buf = _make_canvas()
        ps = _make_ps()
        # y < MARGIN_B + leading*2 → 48+30 = 78; use y=70
        # Use a very narrow max_width so the paragraph wraps to > 1 line
        long_para = (
            'Este es un párrafo suficientemente largo para que necesite '
            'envolverse en varias líneas cuando el ancho disponible es reducido.'
        )
        new_y = _draw_paragraphs(
            c, y=MARGIN_B + 20, paragraphs=[long_para],
            max_width=120, ps=ps,
        )
        c.save()

        assert isinstance(new_y, (int, float))
        assert buf.getvalue()


# ===========================================================================
# _draw_bullet_list — nested children y-guard without ps
# ===========================================================================

class TestDrawBulletListNestedChildrenLowY:
    def test_nested_children_returns_early_when_y_near_bottom_no_ps(self):
        """When y is very low and ps is None, returns early while rendering children."""
        from content.services.pdf_utils import MARGIN_B, _draw_bullet_list

        c, _ = _make_canvas()
        items = [
            {'text': 'Parent item', 'children': ['Child A', 'Child B', 'Child C']},
        ]
        # y < MARGIN_B + 20 = 68; use a value that triggers after entering children
        y = _draw_bullet_list(c, y=MARGIN_B + 18, items=items, ps=None)
        c.save()

        assert isinstance(y, (int, float))


# ===========================================================================
# _draw_table — ps-triggered pagination within rows
# ===========================================================================

class TestDrawTablePagination:
    def test_new_page_inserted_when_row_does_not_fit(self):
        """When a data row doesn't fit and ps is provided, _new_page is called."""
        from content.services.pdf_utils import MARGIN_B, _draw_table

        c, buf = _make_canvas()
        ps = _make_ps()
        # Position y near bottom so first data row triggers pagination
        rows = [['Alice', 'Admin'], ['Bob', 'Client'], ['Carol', 'Manager']]
        new_y = _draw_table(
            c,
            y=MARGIN_B + 25,
            headers=['Name', 'Role'],
            rows=rows,
            ps=ps,
        )
        c.save()

        assert isinstance(new_y, (int, float))
        assert buf.getvalue()


# ===========================================================================
# _draw_callout_box — pagination in body text with ps
# ===========================================================================

class TestDrawCalloutBoxPagination:
    def test_pagination_triggered_in_body_text_with_ps(self):
        """A callout box near the page bottom with ps triggers page break in body."""
        from content.services.pdf_utils import MARGIN_B, _draw_callout_box

        c, buf = _make_canvas()
        ps = _make_ps()
        # Long multi-line callout placed very near the bottom
        long_text = ' '.join([f'sentence {i}' for i in range(30)])
        new_y = _draw_callout_box(
            c, y=MARGIN_B + 60, text=long_text, style='note', ps=ps,
        )
        c.save()

        assert isinstance(new_y, (int, float))
        assert buf.getvalue()


# ===========================================================================
# _draw_code_block — large block rendered WITHOUT ps
# ===========================================================================

class TestDrawCodeBlockLargeNops:
    def test_large_code_block_renders_per_line_without_ps(self):
        """A code block taller than a page renders line-by-line with ps=None."""
        from content.services.pdf_utils import _draw_code_block

        c, buf = _make_canvas()
        # 80 lines at 11pts = 880pts > usable page ~746pts
        large_code = '\n'.join([f'line_{i:03d} = "value {i}"' for i in range(80)])
        new_y = _draw_code_block(c, y=700, content=large_code, ps=None)
        c.save()

        assert isinstance(new_y, (int, float))
        assert buf.getvalue()


# ===========================================================================
# merge_with_covers — include_portada=False, include_contraportada=True
# ===========================================================================

class TestMergeWithCoversBackOnly:
    def test_back_cover_requested_but_file_does_not_exist(self):
        """include_portada=False, include_contraportada=True with missing cover file
        still returns valid PDF bytes."""
        from unittest.mock import patch, PropertyMock
        from pathlib import Path

        from content.services.pdf_utils import merge_with_covers

        # Build a minimal real PDF to merge
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.drawString(50, 700, 'Content page')
        c.save()
        content_bytes = buf.getvalue()

        # Patch BACK_COVER_PDF.exists() to return False so the back-cover
        # branch is exercised but no actual file I/O fails
        with patch(
            'content.services.pdf_utils.BACK_COVER_PDF',
            new_callable=lambda: type(
                'FakePath', (), {
                    'exists': lambda self: False,
                    '__str__': lambda self: '/fake/back.pdf',
                }
            )(),
        ):
            result = merge_with_covers(
                content_bytes,
                include_portada=False,
                include_contraportada=True,
                prepend_bytes=None,
            )

        assert isinstance(result, bytes)
        assert len(result) > 0


# ===========================================================================
# _draw_toc_page — long title leaves no room for dot-leaders
# ===========================================================================

class TestDrawTocPageNoDots:
    def test_very_long_title_has_no_dot_leaders(self):
        """A title so long it leaves no room for dots renders without error."""
        from content.services.pdf_utils import _draw_toc_page

        c, buf = _make_canvas()
        ps = _make_ps(num=2)
        # Title wider than available space → num_dots == 0 → dots skipped
        long_title = 'A' * 70  # way longer than available space
        entries = [(1, long_title, 3)]
        link_areas = []

        _draw_toc_page(c, entries, ps, link_areas=link_areas)
        c.save()

        assert buf.getvalue()
        assert ps['num'] == 3


# ===========================================================================
# _draw_paragraphs — explicit x takes the x-is-not-None branch (625->627)
# ===========================================================================

class TestDrawParagraphsExplicitX:
    def test_explicit_x_skips_x_default_branch(self):
        """Passing x explicitly takes the 'x is not None' branch."""
        from content.services.pdf_utils import MARGIN_L, _draw_paragraphs

        c, buf = _make_canvas()
        new_y = _draw_paragraphs(
            c, y=700, paragraphs=['Some text here.'],
            x=MARGIN_L + 20,
        )
        c.save()

        assert new_y < 700


# ===========================================================================
# _draw_table — explicit max_width (927->930) + low-y pagination (987-988)
# ===========================================================================

class TestDrawTableMaxWidthAndPagination:
    def test_explicit_max_width_takes_not_none_branch(self):
        """Passing max_width skips the 'is None' assignment."""
        from content.services.pdf_utils import _draw_table

        c, buf = _make_canvas()
        new_y = _draw_table(
            c, y=700,
            headers=['Name', 'Role'],
            rows=[['Alice', 'Admin']],
            max_width=400,
        )
        c.save()

        assert new_y < 700

    def test_row_pagination_triggers_when_y_very_low(self):
        """Row that doesn't fit with ps triggers new page during data rows.

        y must be >= MARGIN_B+40 so the initial _check_y(need=40) doesn't fire,
        but after the header row (height ~20) the first data row's y - row_h
        falls below MARGIN_B+20, triggering lines 987-988.
        """
        from content.services.pdf_utils import MARGIN_B, _draw_table

        c, buf = _make_canvas()
        ps = _make_ps()
        # MARGIN_B=48. Header height ≈ 20. Row height ≈ 20.
        # y=100: check_y(need=40) passes (100 >= 88), header draws → y=80,
        # row 1: 80-20=60 < MARGIN_B+20=68 → _new_page fires (987-988).
        new_y = _draw_table(
            c,
            y=MARGIN_B + 52,
            headers=['Name', 'Role'],
            rows=[['Alice', 'Admin'], ['Bob', 'Client']],
            ps=ps,
        )
        c.save()

        assert isinstance(new_y, (int, float))


# ===========================================================================
# _draw_bullet_list — nested children y-guard WITH ps (line 720)
# AND nested children y-guard without ps (line 722)
# ===========================================================================

class TestDrawBulletListNestedChildrenYGuards:
    def test_nested_children_with_ps_hits_check_y(self):
        """Nested children with ps triggers _check_y (line 720)."""
        from content.services.pdf_utils import _draw_bullet_list

        c, buf = _make_canvas()
        ps = _make_ps()
        items = [
            {'text': 'Parent item', 'children': ['Child A', 'Child B']},
        ]
        # Generous y — the check_y inside children loops will be called
        new_y = _draw_bullet_list(c, y=600, items=items, ps=ps)
        c.save()

        assert isinstance(new_y, (int, float))

    def test_nested_children_without_ps_returns_when_y_too_low(self):
        """y just above guard for parent but drops below guard in children (line 722)."""
        from content.services.pdf_utils import MARGIN_B, _draw_bullet_list

        c, _ = _make_canvas()
        items = [
            {'text': 'Parent item', 'children': ['Child A', 'Child B', 'Child C']},
        ]
        # y=MARGIN_B+34: parent draws one line (y→MARGIN_B+21→MARGIN_B+19 after -2),
        # then children hit y < MARGIN_B+20 → return early
        new_y = _draw_bullet_list(
            c, y=MARGIN_B + 34, items=items, ps=None,
        )
        c.save()

        assert isinstance(new_y, (int, float))


# ===========================================================================
# _draw_callout_box — pagination in body text (1128-1132) with correct setup
# ===========================================================================

class TestDrawCalloutBoxBodyPagination:
    def test_body_text_triggers_page_break_when_y_drops_below_margin(self):
        """Callout box body text that drops below margin triggers page break."""
        from content.services.pdf_utils import MARGIN_B, _draw_callout_box

        c, buf = _make_canvas()
        ps = _make_ps()
        # Place y so that the callout renders near the bottom; enough lines to
        # force body_y < MARGIN_B + leading inside the loop
        many_lines = ' '.join([f'word{i}' for i in range(40)])
        new_y = _draw_callout_box(
            c, y=MARGIN_B + 80, text=many_lines, style='important', ps=ps,
        )
        c.save()

        assert isinstance(new_y, (int, float))
        assert buf.getvalue()
