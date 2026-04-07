"""Tests for pdf_utils: TOC drawing helpers and justification."""
import io
from unittest.mock import MagicMock, patch

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

pytestmark = pytest.mark.django_db


def _make_canvas():
    """Return a ReportLab canvas writing to an in-memory buffer."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    return c, buf


def _make_ps(num=1, client='Test Client'):
    return {'num': num, 'client': client}


# ── _draw_toc_page ────────────────────────────────────────────

class TestDrawTocPage:
    def test_advances_page_number(self):
        """_draw_toc_page increments ps['num'] by exactly 1."""
        from content.services.pdf_utils import _draw_toc_page, _register_fonts
        _register_fonts()
        c, _ = _make_canvas()
        ps = _make_ps(num=2)
        entries = [('01', 'Introducción', 3), ('02', 'Propuesta', 4)]

        _draw_toc_page(c, entries, ps)

        assert ps['num'] == 3

    def test_populates_link_areas_for_each_entry(self):
        """Each TOC entry appends one item to link_areas."""
        from content.services.pdf_utils import _draw_toc_page, _register_fonts
        _register_fonts()
        c, _ = _make_canvas()
        ps = _make_ps(num=2)
        entries = [
            ('01', 'Sección A', 3),
            ('02', 'Sección B', 5),
            ('03', 'Sección C', 7),
        ]
        link_areas = []

        _draw_toc_page(c, entries, ps, link_areas=link_areas)

        assert len(link_areas) == 3

    def test_empty_entries_does_not_raise(self):
        """_draw_toc_page with no entries runs without error."""
        from content.services.pdf_utils import _draw_toc_page, _register_fonts
        _register_fonts()
        c, _ = _make_canvas()
        ps = _make_ps(num=1)

        _draw_toc_page(c, [], ps)

        assert ps['num'] == 2  # page was advanced despite no entries

    def test_entries_without_page_num_do_not_produce_link_areas(self):
        """Entries where page_num is None are drawn but not linked."""
        from content.services.pdf_utils import _draw_toc_page, _register_fonts
        _register_fonts()
        c, _ = _make_canvas()
        ps = _make_ps(num=1)
        entries = [('01', 'Unnamed Section', None)]
        link_areas = []

        _draw_toc_page(c, entries, ps, link_areas=link_areas)

        assert link_areas == []


# ── _apply_toc_links ─────────────────────────────────────────

class TestApplyTocLinks:
    def _build_minimal_pdf(self, num_pages=4):
        """Build a minimal multi-page PDF with ReportLab."""
        from content.services.pdf_utils import _register_fonts
        _register_fonts()
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        for i in range(num_pages):
            c.drawString(50, 700, f'Page {i + 1}')
            c.showPage()
        c.save()
        return buf.getvalue()

    def test_returns_bytes_with_valid_link_areas(self):
        """_apply_toc_links returns bytes when given valid link_areas."""
        from content.services.pdf_utils import _apply_toc_links
        pdf = self._build_minimal_pdf(num_pages=4)
        link_areas = [
            ((48, 600, 547, 634), 3),
            ((48, 566, 547, 600), 4),
        ]

        result = _apply_toc_links(pdf, link_areas, cover_offset=1)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_returns_original_bytes_when_link_areas_empty(self):
        """_apply_toc_links returns original bytes unchanged when link_areas is []."""
        from content.services.pdf_utils import _apply_toc_links
        pdf = self._build_minimal_pdf(num_pages=3)

        result = _apply_toc_links(pdf, [], cover_offset=1)

        assert result == pdf

    def test_out_of_range_target_does_not_raise(self):
        """Link areas pointing to non-existent pages are silently skipped."""
        from content.services.pdf_utils import _apply_toc_links
        pdf = self._build_minimal_pdf(num_pages=2)
        # target_idx = section_ps_num + cover_offset - 1 = 99 + 0 - 1 = 98 → out of range
        link_areas = [((48, 600, 547, 634), 99)]

        result = _apply_toc_links(pdf, link_areas, cover_offset=0)

        assert isinstance(result, bytes)


# ── _draw_line_with_links (justify mode) ─────────────────────

class TestDrawLineWithLinksJustify:
    def test_justified_line_does_not_raise(self):
        """_draw_line_with_links with justify=True runs without error."""
        from content.services.pdf_utils import _draw_line_with_links, _register_fonts, ESMERALD_80
        _register_fonts()
        c, buf = _make_canvas()
        c.setFont('Helvetica', 11)

        _draw_line_with_links(
            c, x=48, y=700,
            line='Este es un párrafo de prueba con varias palabras para justificación.',
            font_name='Helvetica', font_size=11,
            text_color=ESMERALD_80,
            justify=True, max_width=499,
        )
        c.save()

        assert buf.getvalue()  # non-empty PDF bytes

    def test_justify_with_single_word_does_not_add_extra_space(self):
        """A single-word token has no space gaps — extra should be 0."""
        from content.services.pdf_utils import _draw_line_with_links, _register_fonts, ESMERALD_80
        _register_fonts()
        c, buf = _make_canvas()
        c.setFont('Helvetica', 11)

        # Single word: no space characters → extra must be 0 (no division error)
        _draw_line_with_links(
            c, x=48, y=700,
            line='Singleword',
            font_name='Helvetica', font_size=11,
            text_color=ESMERALD_80,
            justify=True, max_width=499,
        )
        c.save()

        assert buf.getvalue()

    def test_bold_inline_token_rendered_in_justify_mode(self):
        """Bold **tokens** inside a justified line render without error."""
        from content.services.pdf_utils import _draw_line_with_links, _register_fonts, ESMERALD_80
        _register_fonts()
        c, buf = _make_canvas()
        c.setFont('Helvetica', 11)

        _draw_line_with_links(
            c, x=48, y=700,
            line='Este es **un texto en negrita** dentro de una línea justificada.',
            font_name='Helvetica', font_size=11,
            text_color=ESMERALD_80,
            justify=True, max_width=499,
        )
        c.save()

        assert buf.getvalue()


# ── Utility functions ────────────────────────────────────────

class TestUtilityFunctions:
    def test_format_date_es_returns_spanish_format(self):
        """format_date_es formats a datetime as Spanish text."""
        import datetime
        from content.services.pdf_utils import format_date_es

        dt = datetime.datetime(2026, 4, 3)
        result = format_date_es(dt)

        assert result == '3 de abril de 2026'

    def test_strip_emoji_removes_emoji_characters(self):
        """_strip_emoji removes emoji/symbol characters."""
        from content.services.pdf_utils import _strip_emoji

        result = _strip_emoji('Hello 🚀 World')

        assert 'Hello' in result
        assert '🚀' not in result

    def test_strip_emoji_returns_none_for_empty_input(self):
        """_strip_emoji returns the input unchanged when empty."""
        from content.services.pdf_utils import _strip_emoji

        result = _strip_emoji('')

        assert result == ''

    def test_strip_emoji_converts_bold_html_to_markdown(self):
        """_strip_emoji converts <b>text</b> to **text**."""
        from content.services.pdf_utils import _strip_emoji

        result = _strip_emoji('<b>bold</b>')

        assert '**bold**' in result

    def test_format_cop_formats_with_dots_as_thousands_separator(self):
        """_format_cop formats large numbers with dots."""
        from content.services.pdf_utils import _format_cop

        result = _format_cop(1490000)

        assert result == '$1.490.000'

    def test_format_cop_handles_invalid_value_gracefully(self):
        """_format_cop returns str(value) on conversion failure."""
        from content.services.pdf_utils import _format_cop

        result = _format_cop('not-a-number')

        assert result == 'not-a-number'

    def test_safe_pdf_filename_returns_clean_filename(self):
        """safe_pdf_filename returns a sanitized filename string."""
        from content.services.pdf_utils import safe_pdf_filename

        result = safe_pdf_filename('Propuesta', 'Empresa ABC / Ltd', '2026-04-03')

        assert result.endswith('.pdf')
        assert '/' not in result


# ── Drawing helpers ────────────────────────────────────────

class TestDrawingHelpers:
    def setup_method(self):
        from content.services.pdf_utils import _register_fonts
        _register_fonts()

    def _ps(self):
        return {'num': 1, 'client': 'Test Client', 'total': None}

    def test_draw_footer_does_not_raise(self):
        """_draw_footer renders without error."""
        from content.services.pdf_utils import _draw_footer

        c, buf = _make_canvas()
        _draw_footer(c, 1, total_pages=5, client_name='Test Client')
        c.save()

        assert buf.getvalue()

    def test_draw_footer_without_client_name_does_not_raise(self):
        """_draw_footer renders without client_name."""
        from content.services.pdf_utils import _draw_footer

        c, buf = _make_canvas()
        _draw_footer(c, 3)
        c.save()

        assert buf.getvalue()

    def test_draw_header_bar_does_not_raise(self):
        """_draw_header_bar renders the accent bar without error."""
        from content.services.pdf_utils import _draw_header_bar

        c, buf = _make_canvas()
        _draw_header_bar(c)
        c.save()

        assert buf.getvalue()

    def test_draw_section_header_does_not_raise(self):
        """_draw_section_header renders index + title without error."""
        from content.services.pdf_utils import _draw_section_header

        c, buf = _make_canvas()
        new_y = _draw_section_header(c, y=700, index_str='01', title='Introducción')
        c.save()

        assert new_y < 700
        assert buf.getvalue()

    def test_draw_section_header_with_long_title_wraps(self):
        """Long titles are wrapped across multiple lines."""
        from content.services.pdf_utils import _draw_section_header

        c, buf = _make_canvas()
        long_title = 'Este es un título muy largo que definitivamente supera los 38 caracteres permitidos'
        new_y = _draw_section_header(c, y=700, index_str='02', title=long_title)
        c.save()

        assert new_y < 700

    def test_draw_section_header_without_index_does_not_raise(self):
        """_draw_section_header works with empty index_str."""
        from content.services.pdf_utils import _draw_section_header

        c, buf = _make_canvas()
        _draw_section_header(c, y=700, index_str='', title='Sin índice')
        c.save()

        assert buf.getvalue()

    def test_draw_paragraphs_renders_text(self):
        """_draw_paragraphs draws multi-paragraph text without error."""
        from content.services.pdf_utils import _draw_paragraphs

        c, buf = _make_canvas()
        paragraphs = ['First paragraph of text.', 'Second paragraph here.']
        new_y = _draw_paragraphs(c, y=700, paragraphs=paragraphs)
        c.save()

        assert new_y < 700

    def test_draw_paragraphs_with_justify_renders(self):
        """_draw_paragraphs with justify=True renders justified text."""
        from content.services.pdf_utils import _draw_paragraphs

        c, buf = _make_canvas()
        paragraphs = ['This is a justified paragraph with enough words to span multiple lines.']
        _draw_paragraphs(c, y=700, paragraphs=paragraphs, justify=True)
        c.save()

        assert buf.getvalue()

    def test_draw_bullet_list_with_string_items_renders(self):
        """_draw_bullet_list with plain string items renders without error."""
        from content.services.pdf_utils import _draw_bullet_list

        c, buf = _make_canvas()
        new_y = _draw_bullet_list(c, y=700, items=['Item one', 'Item two', 'Item three'])
        c.save()

        assert new_y < 700

    def test_draw_bullet_list_with_dict_items_renders(self):
        """_draw_bullet_list with dict items (text + children) renders."""
        from content.services.pdf_utils import _draw_bullet_list

        c, buf = _make_canvas()
        items = [
            {'text': 'Main item', 'children': ['Sub item A', 'Sub item B']},
            {'text': 'Another item', 'children': []},
        ]
        _draw_bullet_list(c, y=700, items=items)
        c.save()

        assert buf.getvalue()

    def test_draw_bullet_list_numbered_renders(self):
        """_draw_bullet_list with numbered=True renders numbered list."""
        from content.services.pdf_utils import _draw_bullet_list

        c, buf = _make_canvas()
        _draw_bullet_list(c, y=700, items=['First', 'Second', 'Third'], numbered=True)
        c.save()

        assert buf.getvalue()

    def test_draw_separator_renders(self):
        """_draw_separator draws a horizontal rule without error."""
        from content.services.pdf_utils import _draw_separator

        c, buf = _make_canvas()
        _draw_separator(c, y=700)
        c.save()

        assert buf.getvalue()

    def test_draw_subtitle_renders(self):
        """_draw_subtitle draws a styled subtitle without error."""
        from content.services.pdf_utils import _draw_subtitle

        c, buf = _make_canvas()
        _draw_subtitle(c, y=700, text='Subtítulo de sección')
        c.save()

        assert buf.getvalue()

    def test_draw_blockquote_renders(self):
        """_draw_blockquote draws a quoted block without error."""
        from content.services.pdf_utils import _draw_blockquote

        c, buf = _make_canvas()
        new_y = _draw_blockquote(c, y=700, text='This is a blockquote.')
        c.save()

        assert new_y < 700

    def test_draw_callout_box_note_renders(self):
        """_draw_callout_box with style='note' renders without error."""
        from content.services.pdf_utils import _draw_callout_box

        c, buf = _make_canvas()
        new_y = _draw_callout_box(c, y=700, text='Important note here.', style='note')
        c.save()

        assert new_y < 700

    def test_draw_callout_box_warning_renders(self):
        """_draw_callout_box with style='warning' renders without error."""
        from content.services.pdf_utils import _draw_callout_box

        c, buf = _make_canvas()
        _draw_callout_box(c, y=700, text='Warning message.', style='warning')
        c.save()

        assert buf.getvalue()

    def test_draw_code_block_renders(self):
        """_draw_code_block renders a fenced code block without error."""
        from content.services.pdf_utils import _draw_code_block

        c, buf = _make_canvas()
        new_y = _draw_code_block(c, y=700, content='def hello():\n    print("world")')
        c.save()

        assert new_y < 700

    def test_draw_table_renders_headers_and_rows(self):
        """_draw_table renders a complete table without error."""
        from content.services.pdf_utils import _draw_table

        c, buf = _make_canvas()
        new_y = _draw_table(
            c, y=700,
            headers=['Name', 'Role', 'Status'],
            rows=[['Alice', 'Admin', 'Active'], ['Bob', 'Client', 'Inactive']],
        )
        c.save()

        assert new_y < 700

    def test_draw_banner_box_renders(self):
        """_draw_banner_box renders a text banner without error."""
        from content.services.pdf_utils import _draw_banner_box

        c, buf = _make_canvas()
        _draw_banner_box(c, x=48, y=700, width=499, text='Banner text here')
        c.save()

        assert buf.getvalue()

    def test_draw_pill_renders(self):
        """_draw_pill renders a labeled pill badge without error."""
        from content.services.pdf_utils import _draw_pill

        c, buf = _make_canvas()
        _draw_pill(c, x=48, y=700, text='Status')
        c.save()

        assert buf.getvalue()


# ── _md_wrap bold-span integrity ──────────────────────────────

class TestMdWrap:
    def test_keeps_bold_span_on_same_line(self):
        """A single **bold block** must not be split across lines."""
        from content.services.pdf_utils import _md_wrap

        text = (
            'Arturo, esta propuesta se enfoca en el '
            '**corazón financiero de Circular Bank**: '
            'la wallet digital que convierte cada kilo.'
        )
        lines = _md_wrap(text, 55)

        for i, line in enumerate(lines):
            count = line.count('**')
            assert count % 2 == 0, (
                f'Line {i} has unbalanced ** markers: "{line}"'
            )

    def test_handles_multiple_bold_spans(self):
        """Two **spans** in the same text both stay paired."""
        from content.services.pdf_utils import _md_wrap

        text = (
            'El proceso será **colaborativo**: cada pantalla pasará por '
            '**revisiones conjuntas** para que la experiencia sea clara.'
        )
        lines = _md_wrap(text, 55)

        for i, line in enumerate(lines):
            count = line.count('**')
            assert count % 2 == 0, (
                f'Line {i} has unbalanced ** markers: "{line}"'
            )

    def test_handles_bold_at_end_of_text(self):
        """A **bold span** at the very end of the text stays paired."""
        from content.services.pdf_utils import _md_wrap

        text = (
            'Cada pantalla será una co-creación, donde Arturo validará '
            'que la experiencia refleje la misión de **convertir residuos en valor**.'
        )
        lines = _md_wrap(text, 55)

        for i, line in enumerate(lines):
            count = line.count('**')
            assert count % 2 == 0, (
                f'Line {i} has unbalanced ** markers: "{line}"'
            )

    def test_no_bold_wraps_normally(self):
        """Text without markdown wraps like standard textwrap."""
        import textwrap
        from content.services.pdf_utils import _md_wrap

        text = 'Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.'
        md_lines = _md_wrap(text, 40)
        tw_lines = textwrap.wrap(text, width=40)

        assert md_lines == tw_lines

    def test_empty_input_returns_list(self):
        """Empty string returns a single-element list."""
        from content.services.pdf_utils import _md_wrap

        result = _md_wrap('', 50)

        assert result == ['']


# ── _tokenize_inline ──────────────────────────────────────────

class TestTokenizeInline:
    def test_parses_bold_token(self):
        """**text** produces a bold token."""
        from content.services.pdf_utils import _tokenize_inline

        tokens = _tokenize_inline('Hello **world** end')

        bold_tokens = [t for t in tokens if t['type'] == 'bold']
        assert len(bold_tokens) == 1
        assert bold_tokens[0]['text'] == 'world'

    def test_parses_mixed_tokens(self):
        """Plain + bold + plain produces three tokens in order."""
        from content.services.pdf_utils import _tokenize_inline

        tokens = _tokenize_inline('before **mid** after')

        assert len(tokens) == 3
        assert tokens[0]['type'] == 'text'
        assert tokens[1]['type'] == 'bold'
        assert tokens[2]['type'] == 'text'

    def test_no_markers_returns_single_text(self):
        """Text without markdown markers returns a single text token."""
        from content.services.pdf_utils import _tokenize_inline

        tokens = _tokenize_inline('plain text here')

        assert len(tokens) == 1
        assert tokens[0]['type'] == 'text'
        assert tokens[0]['text'] == 'plain text here'


# ── _clean_inline_bold ────────────────────────────────────────

class TestCleanInlineBold:
    def test_strips_double_stars(self):
        """**bold** markers are removed, leaving inner text."""
        from content.services.pdf_utils import _clean_inline_bold

        assert _clean_inline_bold('Hello **world** end') == 'Hello world end'

    def test_strips_triple_stars(self):
        """***bold-italic*** markers are removed."""
        from content.services.pdf_utils import _clean_inline_bold

        assert _clean_inline_bold('A ***bi*** Z') == 'A bi Z'


# ── Integration: drawing functions with bold markdown ─────────

class TestBoldMarkdownIntegration:
    def setup_method(self):
        from content.services.pdf_utils import _register_fonts
        _register_fonts()

    def test_draw_paragraphs_with_bold_text_renders(self):
        """_draw_paragraphs with **bold** text produces valid PDF without error."""
        from content.services.pdf_utils import _draw_paragraphs

        c, buf = _make_canvas()
        text = (
            'Esta propuesta se enfoca en el **corazón financiero de Circular Bank**: '
            'la wallet digital que convierte cada kilo de residuo gestionado en '
            '**valor visible, trazable y retirable**.'
        )
        new_y = _draw_paragraphs(c, y=700, paragraphs=[text])
        c.save()

        assert new_y < 700
        assert buf.getvalue()

    def test_draw_table_with_bold_cell_renders(self):
        """_draw_table with **bold** in a cell renders without error."""
        from content.services.pdf_utils import _draw_table

        c, buf = _make_canvas()
        new_y = _draw_table(
            c, y=700,
            headers=['Feature', 'Description'],
            rows=[['Wallet', 'El **corazón financiero** del proyecto con integración completa']],
        )
        c.save()

        assert new_y < 700
        assert buf.getvalue()

    def test_draw_blockquote_with_bold_text_renders(self):
        """_draw_blockquote with **bold** text renders without error."""
        from content.services.pdf_utils import _draw_blockquote

        c, buf = _make_canvas()
        new_y = _draw_blockquote(
            c, y=700,
            text='La wallet es el **corazón financiero** de la plataforma.',
        )
        c.save()

        assert new_y < 700
        assert buf.getvalue()
