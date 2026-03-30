"""
Service for generating branded PDF documents from structured JSON blocks
using the shared PDF utilities (ReportLab).

Reuses the Project App brand palette, fonts, header/footer, and cover
pages from the proposal PDF system.
"""

import io
import logging
import textwrap

from django.utils import timezone as _tz
from django.utils.text import slugify
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.services.pdf_utils import (
    _register_fonts, _font,
    ESMERALD, ESMERALD_DARK, ESMERALD_LIGHT, GREEN_LIGHT, LEMON, BONE,
    GRAY_500, GRAY_300, WHITE, ESMERALD_80,
    COVER_PDF, BACK_COVER_PDF,
    PAGE_W, PAGE_H, MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B, CONTENT_W,
    _strip_emoji, _replace_urls_with_placeholders,
    _draw_line_with_links,
    _new_page, _check_y,
    _draw_header_bar, _draw_footer,
    _draw_section_header, _draw_paragraphs, _draw_bullet_list,
    _draw_subtitle, _draw_banner_box,
    _draw_table, _draw_blockquote, _draw_code_block, _draw_separator,
    _draw_callout_box,
)

logger = logging.getLogger(__name__)


class DocumentPdfService:
    """Generate a branded PDF from a Document model instance."""

    @classmethod
    def generate(cls, document):
        """Generate PDF bytes from a Document instance.

        Args:
            document: Document model instance with content_json populated.

        Returns:
            bytes: PDF content, or None on failure.
        """
        try:
            _register_fonts()

            content_json = document.content_json or {}
            meta = content_json.get('meta', {})
            blocks = content_json.get('blocks', [])

            if not blocks:
                logger.warning('Document %s has no blocks to render', document.id)
                return None

            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)

            ps = {
                'num': 1,
                'client': meta.get('client_name', document.client_name or ''),
                'total': None,
            }

            cover_type = meta.get('cover_type', document.cover_type or 'generic')

            # Start first page
            _draw_header_bar(c)
            y = PAGE_H - MARGIN_T

            # Render title page if cover_type is 'generic'
            if cover_type == 'generic':
                y = cls._render_title_page(c, document, meta, ps)
                # Start new page for content
                _draw_footer(c, ps['num'], client_name=ps['client'])
                c.showPage()
                ps['num'] += 1
                _draw_header_bar(c)
                y = PAGE_H - MARGIN_T

            # Render blocks
            first_block = True
            for block in blocks:
                block_type = block.get('type', '')

                if not first_block and block_type in ('section_header', 'heading'):
                    y -= 28
                    y = _check_y(c, y, ps, need=80)
                elif not first_block:
                    y -= 6

                first_block = False

                if block_type == 'heading':
                    y = cls._render_heading(c, y, block, ps)
                elif block_type == 'paragraph':
                    y = cls._render_paragraph(c, y, block, ps)
                elif block_type == 'table':
                    y = cls._render_table(c, y, block, ps)
                elif block_type == 'list':
                    y = cls._render_list(c, y, block, ps)
                elif block_type == 'blockquote':
                    y = cls._render_blockquote(c, y, block, ps)
                elif block_type == 'code':
                    y = cls._render_code(c, y, block, ps)
                elif block_type == 'separator':
                    y = cls._render_separator(c, y, block, ps)
                elif block_type == 'section_header':
                    y = cls._render_section_header(c, y, block, ps)
                elif block_type == 'sub_section':
                    y = cls._render_sub_section(c, y, block, ps)
                elif block_type == 'callout':
                    y = cls._render_callout(c, y, block, ps)

            # Finalize last page
            _draw_footer(c, ps['num'], client_name=ps['client'])
            c.save()

            content_bytes = buf.getvalue()
            buf.close()

            # Merge with covers
            pdf_bytes = cls._merge_with_covers(content_bytes, cover_type)

            logger.info(
                'Generated document PDF for "%s" (%d bytes, %d pages)',
                document.title, len(pdf_bytes), ps['num'],
            )
            return pdf_bytes

        except Exception:
            logger.exception(
                'Failed to generate PDF for document %s', document.id,
            )
            return None

    @classmethod
    def _render_title_page(cls, c, document, meta, ps):
        """Render a branded title page with decorative elements."""
        # Decorative circle top-right
        c.saveState()
        c.setFillColor(ESMERALD_LIGHT)
        c.circle(PAGE_W - 40, PAGE_H - 40, 140, fill=1, stroke=0)
        c.restoreState()

        # Small accent circle bottom-left
        c.saveState()
        c.setFillColor(BONE)
        c.circle(60, 80, 70, fill=1, stroke=0)
        c.restoreState()

        # Title
        title = _strip_emoji(meta.get('title', document.title or 'Documento'))
        y = PAGE_H / 2 + 60

        # Subtitle label (above title)
        subtitle = meta.get('subtitle', '')
        if subtitle:
            c.setFont(_font('light'), 14)
            c.setFillColor(GREEN_LIGHT)
            c.drawCentredString(PAGE_W / 2, y + 30, _strip_emoji(subtitle))

        # Main title
        c.setFont(_font('light'), 36)
        c.setFillColor(ESMERALD)
        title_lines = textwrap.wrap(title, width=24)
        for line in title_lines:
            c.drawCentredString(PAGE_W / 2, y, line)
            y -= 44

        # Lemon divider
        y -= 10
        div_w = 60
        c.setStrokeColor(LEMON)
        c.setLineWidth(2)
        c.line(PAGE_W / 2 - div_w / 2, y, PAGE_W / 2 + div_w / 2, y)
        c.setFillColor(LEMON)
        c.circle(PAGE_W / 2 - div_w / 2 - 3, y, 3, fill=1, stroke=0)
        c.circle(PAGE_W / 2 + div_w / 2 + 3, y, 3, fill=1, stroke=0)

        # Client name
        client = meta.get('client_name', document.client_name or '')
        if client:
            y -= 30
            c.setFont(_font('regular'), 14)
            c.setFillColor(ESMERALD)
            c.drawCentredString(PAGE_W / 2, y, _strip_emoji(client))

        # Date
        date_str = meta.get('date', '')
        if not date_str and document.created_at:
            _MONTHS_ES = {
                1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
                5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
                9: 'septiembre', 10: 'octubre', 11: 'noviembre',
                12: 'diciembre',
            }
            dt = document.created_at
            date_str = f'{dt.day} de {_MONTHS_ES.get(dt.month, "")} de {dt.year}'
        if date_str:
            c.setFont(_font('regular'), 9)
            c.setFillColor(GRAY_500)
            c.drawCentredString(PAGE_W / 2, MARGIN_B + 40, date_str)

        return y

    # -- Block renderers -------------------------------------------

    @staticmethod
    def _render_heading(c, y, block, ps):
        """Render h1/h2/h3 headings."""
        level = block.get('level', 1)
        text = _strip_emoji(block.get('text', ''))

        if level == 1:
            font_size, font_style = 20, 'light'
            y = _check_y(c, y, ps, need=40)
        elif level == 2:
            font_size, font_style = 16, 'bold'
            y = _check_y(c, y, ps, need=30)
        else:
            font_size, font_style = 13, 'bold'
            y = _check_y(c, y, ps, need=24)

        c.setFont(_font(font_style), font_size)
        c.setFillColor(ESMERALD)

        max_chars = int(CONTENT_W / (font_size * 0.5))
        lines = textwrap.wrap(text, width=max_chars) or [text]
        for line in lines:
            c.drawString(MARGIN_L, y, line)
            y -= font_size + 6

        if level <= 2:
            # Accent line for h1/h2
            c.setStrokeColor(LEMON)
            c.setLineWidth(2)
            c.line(MARGIN_L, y + 4, MARGIN_L + 60, y + 4)
            y -= 12

        return y

    @staticmethod
    def _render_paragraph(c, y, block, ps):
        """Render a paragraph."""
        text = block.get('text', '')
        if not text:
            return y
        y = _draw_paragraphs(c, y, [text], max_width=CONTENT_W, ps=ps)
        return y

    @staticmethod
    def _render_table(c, y, block, ps):
        """Render a table."""
        headers = block.get('headers', [])
        rows = block.get('rows', [])
        if not headers:
            return y
        return _draw_table(c, y, headers, rows, ps=ps)

    @staticmethod
    def _render_list(c, y, block, ps):
        """Render ordered or unordered list."""
        items = block.get('items', [])
        ordered = block.get('ordered', False)
        if not items:
            return y
        return _draw_bullet_list(c, y, items, max_width=CONTENT_W, ps=ps,
                                  numbered=ordered)

    @staticmethod
    def _render_blockquote(c, y, block, ps):
        """Render a blockquote."""
        text = block.get('text', '')
        if not text:
            return y
        return _draw_blockquote(c, y, text, ps=ps)

    @staticmethod
    def _render_code(c, y, block, ps):
        """Render a code block."""
        content = block.get('content', '')
        language = block.get('language', 'text')
        if not content:
            return y
        return _draw_code_block(c, y, content, ps=ps, language=language)

    @staticmethod
    def _render_separator(c, y, block, ps):
        """Render a horizontal separator."""
        return _draw_separator(c, y, ps=ps)

    @staticmethod
    def _render_section_header(c, y, block, ps):
        """Render a numbered section header."""
        index = block.get('index', '')
        title = block.get('title', '')
        return _draw_section_header(c, y, index, title, ps=ps)

    @staticmethod
    def _render_sub_section(c, y, block, ps):
        """Render a sub-section header."""
        index = block.get('index', '')
        title = block.get('title', '')

        y = _check_y(c, y, ps, need=24)

        # Draw index in lighter color
        if index:
            c.setFont(_font('medium'), 9)
            c.setFillColor(GREEN_LIGHT)
            c.drawString(MARGIN_L, y, index)
            y -= 4

        # Draw title
        y = _draw_subtitle(c, y, title, ps=ps)
        return y

    @staticmethod
    def _render_callout(c, y, block, ps):
        """Render a GitHub-style callout box (note/tip/warning/caution/important)."""
        style = block.get('style', 'note')
        text  = block.get('text', '')
        if not text:
            return y
        return _draw_callout_box(c, y, text, style=style, ps=ps)

    @classmethod
    def _merge_with_covers(cls, content_bytes, cover_type='generic'):
        """Merge content with cover PDFs based on cover_type."""
        writer = PdfWriter()

        # Front cover (only for 'proposal' type)
        if cover_type == 'proposal' and COVER_PDF.exists():
            try:
                cover_reader = PdfReader(str(COVER_PDF))
                for page in cover_reader.pages:
                    page.scale_to(PAGE_W, PAGE_H)
                    writer.add_page(page)
            except Exception:
                logger.warning('Could not read cover PDF: %s', COVER_PDF)

        # Content pages
        content_reader = PdfReader(io.BytesIO(content_bytes))
        for page in content_reader.pages:
            writer.add_page(page)

        # Back cover (for 'generic' and 'proposal')
        if cover_type in ('generic', 'proposal') and BACK_COVER_PDF.exists():
            try:
                back_reader = PdfReader(str(BACK_COVER_PDF))
                for page in back_reader.pages:
                    page.scale_to(PAGE_W, PAGE_H)
                    writer.add_page(page)
            except Exception:
                logger.warning('Could not read back cover PDF: %s', BACK_COVER_PDF)

        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()
