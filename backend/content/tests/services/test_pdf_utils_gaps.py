"""Tests covering missing branches in pdf_utils.py.

Targets:
- _tokenize_inline: italic_star, italic_under, strike, code, md_link non-http, full_url, bare_domain
- _draw_line_with_links: code token, strike token, link with URL, italic/bold_italic tokens
- _estimate_text_height: default max_width, empty para
- _draw_table: empty headers guard
- _draw_blockquote: empty text guard
- _draw_callout_box: empty text → wrapped_lines fallback
- _draw_code_block: empty content, very long block pagination path
- merge_with_covers: all-false fast-path
- _draw_decorative_title_page: long client name wrap, with date_str
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
# _tokenize_inline — additional token types
# ===========================================================================

class TestTokenizeInlineAdditional:
    def test_parses_italic_star_token(self):
        """*text* produces an italic token."""
        from content.services.pdf_utils import _tokenize_inline

        tokens = _tokenize_inline('Hello *world* end')

        italic = [t for t in tokens if t['type'] == 'italic']
        assert len(italic) == 1
        assert italic[0]['text'] == 'world'

    def test_parses_italic_underscore_token(self):
        """_text_ produces an italic token."""
        from content.services.pdf_utils import _tokenize_inline

        tokens = _tokenize_inline('Hello _world_ end')

        italic = [t for t in tokens if t['type'] == 'italic']
        assert len(italic) == 1
        assert italic[0]['text'] == 'world'

    def test_parses_strike_token(self):
        """~~text~~ produces a strike token."""
        from content.services.pdf_utils import _tokenize_inline

        tokens = _tokenize_inline('Old ~~deleted~~ text')

        strike = [t for t in tokens if t['type'] == 'strike']
        assert len(strike) == 1
        assert strike[0]['text'] == 'deleted'

    def test_parses_inline_code_token(self):
        """`code` produces a code token."""
        from content.services.pdf_utils import _tokenize_inline

        tokens = _tokenize_inline('Call `func()` here')

        code = [t for t in tokens if t['type'] == 'code']
        assert len(code) == 1
        assert code[0]['text'] == 'func()'

    def test_parses_md_link_with_non_http_url(self):
        """[text](domain.com) normalises URL to https://."""
        from content.services.pdf_utils import _tokenize_inline

        tokens = _tokenize_inline('[Project](projectapp.co)')

        links = [t for t in tokens if t['type'] == 'link']
        assert len(links) == 1
        assert links[0]['url'].startswith('https://')

    def test_parses_full_url(self):
        """Bare https URL becomes a link token."""
        from content.services.pdf_utils import _tokenize_inline

        tokens = _tokenize_inline('Visit https://example.com for more.')

        links = [t for t in tokens if t['type'] == 'link']
        assert len(links) == 1
        assert links[0]['url'] == 'https://example.com'

    def test_parses_bare_domain(self):
        """projectapp.co (bare domain) becomes a link token."""
        from content.services.pdf_utils import _tokenize_inline

        tokens = _tokenize_inline('See projectapp.co for info.')

        links = [t for t in tokens if t['type'] == 'link']
        assert len(links) == 1
        assert 'projectapp.co' in links[0]['url']


# ===========================================================================
# _draw_line_with_links — additional token rendering
# ===========================================================================

class TestDrawLineWithLinksTokens:
    def test_renders_inline_code_token(self):
        """A line with `code` renders the code pill without error."""
        from content.services.pdf_utils import ESMERALD_80, _draw_line_with_links

        c, buf = _make_canvas()
        _draw_line_with_links(
            c, x=48, y=700,
            line='Call `get_data()` here',
            font_name='Helvetica', font_size=10, text_color=ESMERALD_80,
        )
        c.save()

        assert buf.getvalue()

    def test_renders_strike_token_in_justify_mode(self):
        """~~strikethrough~~ in justify mode draws strikethrough line."""
        from content.services.pdf_utils import ESMERALD_80, _draw_line_with_links

        c, buf = _make_canvas()
        _draw_line_with_links(
            c, x=48, y=700,
            line='Old ~~deleted item~~ text here for testing',
            font_name='Helvetica', font_size=10, text_color=ESMERALD_80,
            justify=True, max_width=400,
        )
        c.save()

        assert buf.getvalue()

    def test_renders_strike_token_without_justify(self):
        """~~strike~~ in normal mode renders without error."""
        from content.services.pdf_utils import ESMERALD_80, _draw_line_with_links

        c, buf = _make_canvas()
        _draw_line_with_links(
            c, x=48, y=700,
            line='Old ~~deleted~~ word',
            font_name='Helvetica', font_size=10, text_color=ESMERALD_80,
        )
        c.save()

        assert buf.getvalue()

    def test_renders_link_token_draws_underline_and_annotation(self):
        """[text](url) token draws underline and link annotation."""
        from content.services.pdf_utils import ESMERALD_80, _draw_line_with_links

        c, buf = _make_canvas()
        _draw_line_with_links(
            c, x=48, y=700,
            line='See [Project App](https://projectapp.co) for more.',
            font_name='Helvetica', font_size=10, text_color=ESMERALD_80,
        )
        c.save()

        assert buf.getvalue()

    def test_renders_with_custom_link_color(self):
        """Providing link_color directly takes the not-None branch."""
        from reportlab.lib import colors

        from content.services.pdf_utils import ESMERALD_80, _draw_line_with_links

        c, buf = _make_canvas()
        _draw_line_with_links(
            c, x=48, y=700,
            line='See https://example.com here.',
            font_name='Helvetica', font_size=10, text_color=ESMERALD_80,
            link_color=colors.blue,
        )
        c.save()

        assert buf.getvalue()

    def test_renders_italic_and_bold_italic_tokens(self):
        """*italic* and ***bold-italic*** tokens render without error."""
        from content.services.pdf_utils import ESMERALD_80, _draw_line_with_links

        c, buf = _make_canvas()
        _draw_line_with_links(
            c, x=48, y=700,
            line='A *italic* and ***bold-italic*** token here.',
            font_name='Helvetica', font_size=10, text_color=ESMERALD_80,
        )
        c.save()

        assert buf.getvalue()


# ===========================================================================
# _estimate_text_height
# ===========================================================================

class TestEstimateTextHeight:
    def test_uses_default_content_width_when_max_width_is_none(self):
        """Calling with max_width=None defaults to CONTENT_W."""
        from content.services.pdf_utils import _estimate_text_height

        result = _estimate_text_height(['Some paragraph text.'], max_width=None)

        assert result > 0

    def test_skips_empty_paragraphs_in_list(self):
        """Empty strings in paragraph list are skipped without error."""
        from content.services.pdf_utils import _estimate_text_height

        result = _estimate_text_height(['', 'Real paragraph.', ''])

        assert result > 0


# ===========================================================================
# _draw_table — empty headers guard
# ===========================================================================

class TestDrawTableGuard:
    def test_returns_y_unchanged_when_headers_empty(self):
        """_draw_table returns y immediately when no headers given."""
        from content.services.pdf_utils import _draw_table

        c, _ = _make_canvas()
        y = _draw_table(c, y=700, headers=[], rows=[['a', 'b']])

        assert y == 700


# ===========================================================================
# _draw_blockquote — empty text guard
# ===========================================================================

class TestDrawBlockquoteEmpty:
    def test_returns_y_unchanged_when_text_is_empty(self):
        """_draw_blockquote returns y unchanged when text is empty."""
        from content.services.pdf_utils import _draw_blockquote

        c, _ = _make_canvas()
        y = _draw_blockquote(c, y=700, text='')

        assert y == 700


# ===========================================================================
# _draw_callout_box — empty text path
# ===========================================================================

class TestDrawCalloutBoxEmptyText:
    def test_empty_text_falls_back_to_blank_line(self):
        """_draw_callout_box with empty text uses [''] fallback."""
        from content.services.pdf_utils import _draw_callout_box

        c, buf = _make_canvas()
        new_y = _draw_callout_box(c, y=700, text='', style='note')
        c.save()

        assert isinstance(new_y, (int, float))
        assert buf.getvalue()


# ===========================================================================
# _draw_code_block
# ===========================================================================

class TestDrawCodeBlock:
    def test_returns_y_unchanged_when_content_is_empty(self):
        """_draw_code_block returns y immediately when content is empty."""
        from content.services.pdf_utils import _draw_code_block

        c, _ = _make_canvas()
        y = _draw_code_block(c, y=700, content='')

        assert y == 700

    def test_very_large_block_renders_line_by_line(self):
        """A code block taller than page height falls back to per-line rendering."""
        from content.services.pdf_utils import _draw_code_block

        c, buf = _make_canvas()
        # Generate enough lines to exceed PAGE_H (~841) - MARGINS (~96) = ~745pts
        # Each line is 11pts; 80 lines = 880pts > page usable area
        large_code = '\n'.join([f'line_{i:03d} = "value {i}"' for i in range(80)])
        ps = _make_ps()
        new_y = _draw_code_block(c, y=700, content=large_code, ps=ps)
        c.save()

        assert isinstance(new_y, (int, float))
        assert buf.getvalue()


# ===========================================================================
# merge_with_covers — no-op fast path
# ===========================================================================

class TestMergeWithCoversNoop:
    def test_returns_content_bytes_unchanged_when_no_covers_requested(self):
        """When include_portada=False, include_contraportada=False, and no prepend,
        returns content_bytes as-is without merging."""
        from content.services.pdf_utils import merge_with_covers

        content = b'%PDF-1.4 minimal'

        result = merge_with_covers(
            content,
            include_portada=False,
            include_contraportada=False,
            prepend_bytes=None,
        )

        assert result == content


# ===========================================================================
# _draw_decorative_title_page — long name and date_str
# ===========================================================================

class TestDecorativeTitlePage:
    def test_long_client_name_is_wrapped_across_lines(self):
        """A client name longer than 22 chars is wrapped with drawCentredString."""
        from content.services.pdf_utils import _draw_decorative_title_page

        c, buf = _make_canvas()
        ps = _make_ps()
        _draw_decorative_title_page(
            c,
            document_label='Propuesta Técnica',
            client_name='Empresa de Tecnología Avanzada S.A.S.',  # >22 chars
            date_str='',
            ps=ps,
        )
        c.save()

        assert buf.getvalue()
        assert ps['num'] == 2  # page was advanced

    def test_date_str_is_rendered_below_divider(self):
        """When date_str is provided it is drawn below the divider line."""
        from content.services.pdf_utils import _draw_decorative_title_page

        c, buf = _make_canvas()
        ps = _make_ps()
        _draw_decorative_title_page(
            c,
            document_label='Documento Técnico',
            client_name='Client X',
            date_str='3 de abril de 2026',
            ps=ps,
        )
        c.save()

        assert buf.getvalue()
