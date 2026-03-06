"""
Service for generating professional PDF business proposals
using ReportLab.

Each enabled section is rendered on portrait-A4 pages with the
Project App brand palette (esmerald / lemon / bone) and Ubuntu
typography.  Long sections flow across multiple pages automatically.
"""

import io
import logging
import os
import re
import tempfile
import textwrap
from pathlib import Path

from django.conf import settings
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

# ── Register Ubuntu fonts ────────────────────────────────────
_FONTS_DIR = (
    Path(settings.BASE_DIR).parent / 'frontend' / 'assets' / 'fonts'
)
_FONT_MAP = {
    'Ubuntu': 'Ubuntu-Regular.ttf',
    'Ubuntu-Bold': 'Ubuntu-Bold.ttf',
    'Ubuntu-Light': 'Ubuntu-Light.ttf',
    'Ubuntu-Medium': 'Ubuntu-Medium.ttf',
    'Ubuntu-Italic': 'Ubuntu-Italic.ttf',
    'Ubuntu-BoldItalic': 'Ubuntu-BoldItalic.ttf',
    'Ubuntu-LightItalic': 'Ubuntu-LightItalic.ttf',
    'Ubuntu-MediumItalic': 'Ubuntu-MediumItalic.ttf',
}
_fonts_registered = False


def _register_fonts():
    """Register Ubuntu TTF fonts once (falls back to Helvetica if missing)."""
    global _fonts_registered
    if _fonts_registered:
        return
    for name, filename in _FONT_MAP.items():
        path = _FONTS_DIR / filename
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(path)))
            except Exception:
                logger.debug('Could not register font %s', name)
    _fonts_registered = True


# Font helpers – fall back to Helvetica if Ubuntu is not available
def _font(style='regular'):
    """Return the best available font name for *style*."""
    mapping = {
        'regular': ('Ubuntu', 'Helvetica'),
        'bold': ('Ubuntu-Bold', 'Helvetica-Bold'),
        'light': ('Ubuntu-Light', 'Helvetica'),
        'medium': ('Ubuntu-Medium', 'Helvetica'),
        'italic': ('Ubuntu-Italic', 'Helvetica-Oblique'),
        'bolditalic': ('Ubuntu-BoldItalic', 'Helvetica-BoldOblique'),
        'lightitalic': ('Ubuntu-LightItalic', 'Helvetica-Oblique'),
    }
    primary, fallback = mapping.get(style, ('Ubuntu', 'Helvetica'))
    try:
        pdfmetrics.getFont(primary)
        return primary
    except KeyError:
        return fallback


# ── Brand colours (match frontend tailwind.config.js) ────────
ESMERALD = colors.HexColor('#002921')
ESMERALD_DARK = colors.HexColor('#001713')
ESMERALD_LIGHT = colors.HexColor('#E6EFEF')
GREEN_LIGHT = colors.HexColor('#809490')
LEMON = colors.HexColor('#F0FF3D')
BONE = colors.HexColor('#FAF3E0')
WINDOW_BLACK = colors.HexColor('#191919')
GRAY_700 = colors.HexColor('#374151')
GRAY_500 = colors.HexColor('#6B7280')
GRAY_300 = colors.HexColor('#D1D5DB')
GRAY_200 = colors.HexColor('#E5E7EB')
WHITE = colors.white

# Derived colours
ESMERALD_80 = colors.HexColor('#335550')  # esmerald at ~80% mixed with white

# ── Cover / back-cover PDF paths ─────────────────────────────
COVER_PDF = Path(settings.MEDIA_ROOT) / 'front_page' / 'Portada_ProjectApp.pdf'
BACK_COVER_PDF = (
    Path(settings.MEDIA_ROOT) / 'front_page' / 'Contraportada_ProjectApp.pdf'
)

# ── Page dimensions (portrait A4) ────────────────────────────
PAGE_W, PAGE_H = A4  # ≈595 × 842 pt
MARGIN_L = 48
MARGIN_R = 48
MARGIN_T = 56
MARGIN_B = 48
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R
TEXT_AREA_W = CONTENT_W * 0.60
SIDEBAR_X = MARGIN_L + TEXT_AREA_W + 20
SIDEBAR_W = CONTENT_W - TEXT_AREA_W - 20


# ─────────────────────────────────────────────────────────────
# Emoji / symbol stripping
# ─────────────────────────────────────────────────────────────

_EMOJI_RE = re.compile(
    '['
    '\U0001F000-\U0001FFFF'
    '\U00002600-\U000027BF'
    '\U00002300-\U000023FF'
    '\U0000FE00-\U0000FE0F'
    '\U0000200D'
    '\U000020E3'
    '\U00002B50-\U00002B55'
    '\U000025A0-\U000025FF'
    '\U00002702-\U000027B0'
    '\U0000231A-\U0000231B'
    '\U000023E9-\U000023F3'
    '\U000023F8-\U000023FA'
    '\U0000200B'
    '\U0000FFFD'
    ']+',
)


def _strip_emoji(text):
    """Remove emoji/symbol characters that the fonts cannot render."""
    if not text:
        return text
    return _EMOJI_RE.sub('', str(text)).strip()


def _safe(data, key, default=''):
    """Safely get a key from a dict, returning default if missing."""
    if not isinstance(data, dict):
        return default
    return data.get(key, default) or default


# ─────────────────────────────────────────────────────────────
# Auto-pagination helpers
# ─────────────────────────────────────────────────────────────

def _new_page(c, ps):
    """Emit current page and start a new one with header bar + footer."""
    _draw_footer(c, ps['num'], ps.get('total'), ps['client'])
    c.showPage()
    ps['num'] += 1
    _draw_header_bar(c)
    return PAGE_H - MARGIN_T


def _check_y(c, y, ps, need=20):
    """If y is too low, start a new page and return fresh y."""
    if y < MARGIN_B + need:
        y = _new_page(c, ps)
    return y


# ─────────────────────────────────────────────────────────────
# Drawing helpers
# ─────────────────────────────────────────────────────────────

def _draw_header_bar(c):
    """Draw a thin accent bar at the top of the page."""
    c.setFillColor(ESMERALD)
    c.rect(0, PAGE_H - 6, PAGE_W, 6, fill=1, stroke=0)
    # Lemon accent dot
    c.setFillColor(LEMON)
    c.circle(PAGE_W - 30, PAGE_H - 3, 3, fill=1, stroke=0)


def _draw_green_bar(c):
    """Alias kept for backward compatibility."""
    _draw_header_bar(c)


def _draw_footer(c, page_num, total_pages=None, client_name=''):
    """Draw a discrete footer with page number and branding."""
    footer_y = MARGIN_B - 14
    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.4)
    c.line(MARGIN_L, footer_y, PAGE_W - MARGIN_R, footer_y)
    c.setFont(_font('regular'), 7)
    c.setFillColor(GRAY_500)
    c.drawString(MARGIN_L, footer_y - 11, 'Project App  |  projectapp.co')
    if client_name:
        c.drawCentredString(PAGE_W / 2, footer_y - 11, client_name)
    c.setFillColor(GREEN_LIGHT)
    page_label = (
        f'{page_num} / {total_pages}' if total_pages
        else f'P\u00e1gina {page_num}'
    )
    c.drawRightString(PAGE_W - MARGIN_R, footer_y - 11, page_label)


def _draw_section_header(c, y, index_str, title, ps=None):
    """Draw section index + title and return the new y position."""
    if index_str:
        c.setFont(_font('light'), 11)
        c.setFillColor(GREEN_LIGHT)
        c.drawString(MARGIN_L, y, str(index_str).zfill(2))
        y -= 22
    c.setFont(_font('light'), 24)
    c.setFillColor(ESMERALD)
    max_chars = 38
    clean_title = _strip_emoji(title)
    if len(clean_title) > max_chars:
        lines = textwrap.wrap(clean_title, width=max_chars)
        for line in lines:
            c.drawString(MARGIN_L, y, line)
            y -= 30
    else:
        c.drawString(MARGIN_L, y, clean_title)
        y -= 30
    # Thin accent line
    c.setStrokeColor(LEMON)
    c.setLineWidth(2)
    c.line(MARGIN_L, y + 6, MARGIN_L + 60, y + 6)
    y -= 18
    return y


def _draw_paragraphs(c, y, paragraphs, max_width=None, font_size=10,
                      leading=15, color=ESMERALD_80, ps=None, x=None):
    """Draw a list of paragraph strings and return the new y."""
    if max_width is None:
        max_width = CONTENT_W
    if x is None:
        x = MARGIN_L
    chars_per_line = int(max_width / (font_size * 0.48))
    c.setFont(_font('regular'), font_size)
    c.setFillColor(color)
    for para in (paragraphs or []):
        if not para:
            continue
        lines = textwrap.wrap(_strip_emoji(str(para)), width=chars_per_line)
        # Prevent orphan: if >1 line and only 1 fits, start new page
        if ps and len(lines) > 1 and y < MARGIN_B + leading * 2:
            y = _new_page(c, ps)
        for line in lines:
            if ps:
                y = _check_y(c, y, ps)
                c.setFont(_font('regular'), font_size)
                c.setFillColor(color)
            elif y < MARGIN_B + 20:
                return y
            c.drawString(x, y, line)
            y -= leading
        y -= 5
    return y


def _draw_bullet_list(c, y, items, x=None, max_width=None,
                       font_size=9, leading=13, color=ESMERALD_80,
                       bullet='\u2022', ps=None):
    """Draw a bulleted list and return the new y."""
    if max_width is None:
        max_width = CONTENT_W
    if x is None:
        x = MARGIN_L
    chars_per_line = int(max_width / (font_size * 0.48))
    c.setFont(_font('regular'), font_size)
    c.setFillColor(color)
    for item in (items or []):
        text = _strip_emoji(str(item))
        lines = textwrap.wrap(text, width=chars_per_line - 4)
        # Prevent orphan: keep at least 2 lines together
        if ps and len(lines) > 1 and y < MARGIN_B + leading * 2:
            y = _new_page(c, ps)
        for i, line in enumerate(lines):
            if ps:
                y = _check_y(c, y, ps)
                c.setFont(_font('regular'), font_size)
                c.setFillColor(color)
            elif y < MARGIN_B + 20:
                return y
            prefix = f'  {bullet}  ' if i == 0 else '      '
            c.drawString(x, y, f'{prefix}{line}')
            y -= leading
        y -= 2
    return y


def _draw_sidebar_box(c, y_start, title, items, sidebar_x=None,
                       sidebar_w=None):
    """Draw a branded sidebar box with a title and bullet items."""
    sx = sidebar_x or SIDEBAR_X
    sw = sidebar_w or SIDEBAR_W
    line_h = 13
    header_h = 22
    items_h = sum(
        max(1, len(textwrap.wrap(str(it), width=int(sw / 5.2)))) * line_h + 2
        for it in (items or [])
    )
    box_h = header_h + items_h + 14
    box_y = y_start - box_h

    c.setFillColor(ESMERALD_LIGHT)
    c.roundRect(sx, box_y, sw, box_h, 6, fill=1, stroke=0)

    inner_y = y_start - 16
    c.setFont(_font('bold'), 10)
    c.setFillColor(ESMERALD)
    c.drawString(sx + 10, inner_y, _strip_emoji(str(title)))
    inner_y -= 16

    c.setFont(_font('regular'), 9)
    c.setFillColor(ESMERALD_80)
    chars = int(sw / 5.2)
    for item in (items or []):
        text = _strip_emoji(str(item))
        lines = textwrap.wrap(text, width=chars)
        for j, line in enumerate(lines):
            prefix = '\u2022  ' if j == 0 else '    '
            c.drawString(sx + 10, inner_y, f'{prefix}{line}')
            inner_y -= line_h
        inner_y -= 2

    return box_y


def _draw_subtitle(c, y, text, color=ESMERALD, ps=None):
    """Draw a bold subtitle and return the new y."""
    if ps:
        y = _check_y(c, y, ps, need=24)
    c.setFont(_font('bold'), 12)
    c.setFillColor(color)
    c.drawString(MARGIN_L, y, _strip_emoji(str(text)))
    return y - 18


def _draw_pill(c, x, y, text, bg_color=ESMERALD_LIGHT, text_color=ESMERALD,
               font_size=7, padding_h=8, padding_v=3):
    """Draw a rounded pill/badge and return (right_x, pill_y_bottom).

    The pill is vertically centred on *y* so that it aligns nicely next to
    text drawn at the same y coordinate.
    """
    text = _strip_emoji(str(text))
    c.setFont(_font('medium'), font_size)
    tw = c.stringWidth(text, _font('medium'), font_size)
    pill_w = tw + padding_h * 2
    pill_h = font_size + padding_v * 2
    pill_y = y - padding_v + 1
    c.setFillColor(bg_color)
    c.roundRect(x, pill_y, pill_w, pill_h, pill_h / 2, fill=1, stroke=0)
    c.setFont(_font('medium'), font_size)
    c.setFillColor(text_color)
    c.drawString(x + padding_h, y, text)
    return x + pill_w, pill_y


def _draw_banner_box(c, x, y, width, text, bg_color=BONE,
                     text_color=ESMERALD, font_size=9, icon_text='',
                     ps=None):
    """Draw a full-width banner box with optional icon prefix. Returns new y."""
    if ps:
        y = _check_y(c, y, ps, need=36)
    text = _strip_emoji(str(text))
    box_h = 28
    box_y = y - box_h + 8
    c.setFillColor(bg_color)
    c.roundRect(x, box_y, width, box_h, 6, fill=1, stroke=0)
    inner_x = x + 12
    if icon_text:
        c.setFont(_font('bold'), font_size)
        c.setFillColor(text_color)
        c.drawString(inner_x, box_y + 9, icon_text)
        inner_x += c.stringWidth(icon_text, _font('bold'), font_size) + 6
    c.setFont(_font('regular'), font_size)
    c.setFillColor(text_color)
    c.drawString(inner_x, box_y + 9, text)
    return box_y - 6


# ─────────────────────────────────────────────────────────────
# Section renderers
# ─────────────────────────────────────────────────────────────

def _render_greeting(c, data, proposal, ps=None):
    """Render the greeting/title page."""
    # Subtle decorative circle top-right
    c.saveState()
    c.setFillColor(ESMERALD_LIGHT)
    c.circle(PAGE_W - 40, PAGE_H - 40, 140, fill=1, stroke=0)
    c.restoreState()

    # Small accent circle bottom-left
    c.saveState()
    c.setFillColor(BONE)
    c.circle(50, 60, 70, fill=1, stroke=0)
    c.restoreState()

    mid_y = PAGE_H / 2 + 80

    # "Propuesta de Desarrollo Web," label
    c.setFont(_font('light'), 14)
    c.setFillColor(GREEN_LIGHT)
    c.drawCentredString(PAGE_W / 2, mid_y + 60,
                        'PROPUESTA DE DESARROLLO WEB')

    # Client name — large, centred
    name = _safe(data, 'clientName', proposal.client_name)
    c.setFont(_font('light'), 36)
    c.setFillColor(ESMERALD)
    if len(name) > 22:
        lines = textwrap.wrap(name, width=22)
        ny = mid_y + 10
        for line in lines:
            c.drawCentredString(PAGE_W / 2, ny, line)
            ny -= 44
    else:
        c.drawCentredString(PAGE_W / 2, mid_y + 10, name)

    # Decorative divider line with lemon accent
    line_y = mid_y - 40
    c.setStrokeColor(LEMON)
    c.setLineWidth(2)
    c.line(PAGE_W / 2 - 60, line_y, PAGE_W / 2 + 60, line_y)
    c.setFillColor(LEMON)
    c.circle(PAGE_W / 2 - 60, line_y, 2.5, fill=1, stroke=0)
    c.circle(PAGE_W / 2 + 60, line_y, 2.5, fill=1, stroke=0)

    # Quote
    quote = _safe(data, 'inspirationalQuote')
    if quote:
        c.setFont(_font('italic'), 11)
        c.setFillColor(GREEN_LIGHT)
        q_lines = textwrap.wrap(f'"{_strip_emoji(quote)}"', width=56)
        qy = line_y - 30
        for ql in q_lines:
            c.drawCentredString(PAGE_W / 2, qy, ql)
            qy -= 16

    # Bottom branding
    c.setFont(_font('regular'), 8)
    c.setFillColor(GRAY_500)
    c.drawCentredString(PAGE_W / 2, MARGIN_B + 10,
                        'Project App  |  projectapp.co')


def _render_executive_summary(c, data, _proposal, ps=None, y=None):
    """Render executive summary with paragraphs + sidebar highlights."""
    if y is None:
        y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    paragraphs = _safe(data, 'paragraphs', [])
    highlights = _safe(data, 'highlights', [])
    hl_title = _safe(data, 'highlightsTitle', 'Aspectos Clave')
    content_top = y

    if highlights:
        has_room = (content_top - MARGIN_B) > 200
        if has_room:
            y = _draw_paragraphs(c, y, paragraphs, max_width=TEXT_AREA_W, ps=ps)
            sb = _draw_sidebar_box(c, content_top, hl_title, highlights)
            y = min(y, sb - 8)
        else:
            y = _draw_paragraphs(c, y, paragraphs, ps=ps)
            y -= 6
            y = _draw_subtitle(c, y, hl_title, ps=ps)
            y = _draw_bullet_list(c, y, highlights, ps=ps)
    else:
        y = _draw_paragraphs(c, y, paragraphs, ps=ps)
    return y


def _render_context_diagnostic(c, data, _proposal, ps=None, y=None):
    """Render context & diagnostic section."""
    if y is None:
        y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    issues = _safe(data, 'issues', [])
    issues_title = _safe(data, 'issuesTitle', 'Problemas Identificados')
    content_top = y

    if issues:
        has_room = (content_top - MARGIN_B) > 200
        if has_room:
            text_w = TEXT_AREA_W
            y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []),
                                 max_width=text_w, ps=ps)
            opp_title = _safe(data, 'opportunityTitle')
            opp = _safe(data, 'opportunity')
            if opp:
                y -= 6
                y = _draw_subtitle(c, y, opp_title or 'La oportunidad', ps=ps)
                y = _draw_paragraphs(c, y, [opp], max_width=text_w, ps=ps)
            sb = _draw_sidebar_box(c, content_top, issues_title, issues)
            y = min(y, sb - 8)
        else:
            y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []), ps=ps)
            opp_title = _safe(data, 'opportunityTitle')
            opp = _safe(data, 'opportunity')
            if opp:
                y -= 6
                y = _draw_subtitle(c, y, opp_title or 'La oportunidad', ps=ps)
                y = _draw_paragraphs(c, y, [opp], ps=ps)
            y -= 6
            y = _draw_subtitle(c, y, issues_title, ps=ps)
            y = _draw_bullet_list(c, y, issues, ps=ps)
    else:
        y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []), ps=ps)
        opp_title = _safe(data, 'opportunityTitle')
        opp = _safe(data, 'opportunity')
        if opp:
            y -= 6
            y = _draw_subtitle(c, y, opp_title or 'La oportunidad', ps=ps)
            y = _draw_paragraphs(c, y, [opp], ps=ps)
    return y


def _render_conversion_strategy(c, data, _proposal, ps=None, y=None):
    """Render conversion strategy section."""
    if y is None:
        y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    intro = _safe(data, 'intro')
    if intro:
        y = _draw_paragraphs(c, y, [intro], ps=ps)
        y -= 4

    steps = _safe(data, 'steps', [])
    for step in steps:
        if ps:
            y = _check_y(c, y, ps, need=40)
        elif y < MARGIN_B + 40:
            break
        title = _safe(step, 'title')
        if title:
            y = _draw_subtitle(c, y, title, ps=ps)
        bullets = _safe(step, 'bullets', [])
        if bullets:
            y = _draw_bullet_list(c, y, bullets, ps=ps)
        y -= 4

    # Result sidebar or inline
    result_title = _safe(data, 'resultTitle')
    result = _safe(data, 'result')
    if result:
        y -= 6
        if result_title:
            y = _draw_subtitle(c, y, result_title, ps=ps)
        y = _draw_paragraphs(c, y, [result], ps=ps)
    return y


def _render_design_ux(c, data, _proposal, ps=None, y=None):
    """Render design & UX section."""
    if y is None:
        y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    focus_items = _safe(data, 'focusItems', [])
    focus_title = _safe(data, 'focusTitle', 'Enfoque')
    content_top = y

    if focus_items:
        has_room = (content_top - MARGIN_B) > 200
        if has_room:
            y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []),
                                 max_width=TEXT_AREA_W, ps=ps)
            obj_title = _safe(data, 'objectiveTitle')
            obj = _safe(data, 'objective')
            if obj:
                y -= 6
                y = _draw_subtitle(c, y, obj_title or 'Objetivo', ps=ps)
                y = _draw_paragraphs(c, y, [obj], max_width=TEXT_AREA_W, ps=ps)
            sb = _draw_sidebar_box(c, content_top, focus_title, focus_items)
            y = min(y, sb - 8)
        else:
            y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []), ps=ps)
            obj_title = _safe(data, 'objectiveTitle')
            obj = _safe(data, 'objective')
            if obj:
                y -= 6
                y = _draw_subtitle(c, y, obj_title or 'Objetivo', ps=ps)
                y = _draw_paragraphs(c, y, [obj], ps=ps)
            y -= 6
            y = _draw_subtitle(c, y, focus_title, ps=ps)
            y = _draw_bullet_list(c, y, focus_items, ps=ps)
    else:
        y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []), ps=ps)
        obj_title = _safe(data, 'objectiveTitle')
        obj = _safe(data, 'objective')
        if obj:
            y -= 6
            y = _draw_subtitle(c, y, obj_title or 'Objetivo', ps=ps)
            y = _draw_paragraphs(c, y, [obj], ps=ps)
    return y


def _render_creative_support(c, data, _proposal, ps=None, y=None):
    """Render creative support section."""
    if y is None:
        y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    includes = _safe(data, 'includes', [])
    inc_title = _safe(data, 'includesTitle', 'Incluye')
    content_top = y

    if includes:
        has_room = (content_top - MARGIN_B) > 200
        if has_room:
            y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []),
                                 max_width=TEXT_AREA_W, ps=ps)
            closing = _safe(data, 'closing')
            if closing:
                y -= 6
                y = _draw_paragraphs(c, y, [closing], max_width=TEXT_AREA_W,
                                     ps=ps)
            sb = _draw_sidebar_box(c, content_top, inc_title, includes)
            y = min(y, sb - 8)
        else:
            y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []), ps=ps)
            closing = _safe(data, 'closing')
            if closing:
                y -= 6
                y = _draw_paragraphs(c, y, [closing], ps=ps)
            y -= 6
            y = _draw_subtitle(c, y, inc_title, ps=ps)
            y = _draw_bullet_list(c, y, includes, ps=ps)
    else:
        y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []), ps=ps)
        closing = _safe(data, 'closing')
        if closing:
            y -= 6
            y = _draw_paragraphs(c, y, [closing], ps=ps)
    return y


def _render_development_stages(c, data, _proposal, ps=None, y=None):
    """Render development stages as a vertical timeline."""
    if y is None:
        y = PAGE_H - MARGIN_T
    index_str = _safe(data, 'index')
    title = _safe(data, 'title', 'Etapas de Desarrollo')
    y = _draw_section_header(c, y, index_str, title)
    y -= 8

    stages = _safe(data, 'stages', [])
    for i, stage in enumerate(stages):
        if ps:
            y = _check_y(c, y, ps, need=50)
        elif y < MARGIN_B + 50:
            break
        stage_title = _safe(stage, 'title')
        desc = _safe(stage, 'description')
        is_current = _safe(stage, 'current', False)

        circle_x = MARGIN_L + 14
        circle_y = y - 4
        if is_current:
            c.setFillColor(LEMON)
        else:
            c.setFillColor(ESMERALD)
        c.circle(circle_x, circle_y, 11, fill=1, stroke=0)
        c.setFillColor(ESMERALD if is_current else WHITE)
        c.setFont(_font('bold'), 9)
        c.drawCentredString(circle_x, circle_y - 3, str(i + 1))

        if i < len(stages) - 1:
            c.setStrokeColor(GRAY_200)
            c.setLineWidth(1)
            c.line(circle_x, circle_y - 13, circle_x, circle_y - 44)

        tx = MARGIN_L + 36
        c.setFont(_font('bold'), 11)
        c.setFillColor(ESMERALD)
        c.drawString(tx, y, _strip_emoji(stage_title))
        # "Etapa actual" pill for the current stage
        if is_current:
            title_w = c.stringWidth(_strip_emoji(stage_title),
                                    _font('bold'), 11)
            _draw_pill(c, tx + title_w + 8, y + 1, 'Etapa actual',
                       bg_color=LEMON, text_color=ESMERALD)
        y -= 15

        if desc:
            c.setFont(_font('regular'), 9)
            c.setFillColor(ESMERALD_80)
            stage_chars = int((PAGE_W - MARGIN_R - tx) / (9 * 0.48))
            d_lines = textwrap.wrap(_strip_emoji(str(desc)), width=stage_chars)
            for dl in d_lines:
                c.drawString(tx, y, dl)
                y -= 13
        y -= 12
    return y


def _render_functional_requirements(c, data, proposal, ps=None, y=None):
    """Render functional requirements overview page."""
    if y is None:
        y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    intro = _safe(data, 'intro')
    if intro:
        y = _draw_paragraphs(c, y, [intro], ps=ps)
        y -= 6

    groups = _safe(data, 'groups', [])
    additional = _safe(data, 'additionalModules', [])
    all_groups = list(groups) + list(additional)

    db_groups = list(proposal.requirement_groups.all().order_by('order'))
    for grp in db_groups:
        all_groups.append({
            'title': grp.title,
            'description': grp.description,
            'items': [
                {'name': item.name, 'description': item.description,
                 'icon': item.icon}
                for item in grp.items.all().order_by('order')
            ],
        })

    # Overview cards (2-column grid)
    col_w = (CONTENT_W - 16) / 2
    chars = int(col_w / 5.0)
    last_card_bottom = y
    for idx, grp in enumerate(all_groups):
        col = idx % 2
        row = idx // 2
        card_x = MARGIN_L + col * (col_w + 16)
        card_y = y - row * 62

        if card_y < MARGIN_B + 30:
            break

        c.setFillColor(ESMERALD_LIGHT)
        c.roundRect(card_x, card_y - 44, col_w, 50, 5, fill=1, stroke=0)
        # Left accent bar
        c.setFillColor(LEMON)
        c.roundRect(card_x, card_y - 44, 3, 50, 1, fill=1, stroke=0)

        grp_title = _strip_emoji(_safe(grp, 'title'))
        c.setFont(_font('bold'), 10)
        c.setFillColor(ESMERALD)
        c.drawString(card_x + 10, card_y - 10, grp_title)

        # Item count pill
        grp_items = _safe(grp, 'items', [])
        if grp_items:
            tw = c.stringWidth(grp_title, _font('bold'), 10)
            _draw_pill(c, card_x + 10 + tw + 6, card_y - 10,
                       str(len(grp_items)),
                       bg_color=BONE, text_color=ESMERALD, font_size=6,
                       padding_h=5, padding_v=2)

        desc = _safe(grp, 'description')
        if desc:
            c.setFont(_font('regular'), 8)
            c.setFillColor(ESMERALD_80)
            d_lines = textwrap.wrap(_strip_emoji(str(desc)), width=chars)
            dy = card_y - 24
            for dl in d_lines[:2]:
                c.drawString(card_x + 10, dy, dl)
                dy -= 11
        last_card_bottom = min(last_card_bottom, card_y - 44)

    # Store groups for generate() to render detail sub-sections
    if ps is not None:
        ps['_func_req_groups'] = all_groups

    return last_card_bottom - 8


def _render_requirement_group_page(c, grp, ps=None, y=None,
                                    sub_index=''):
    """Render a single requirement group detail with cards layout."""
    if y is None:
        y = PAGE_H - MARGIN_T

    # Sub-index numeral (e.g. "07.1")
    if sub_index:
        c.setFont(_font('light'), 11)
        c.setFillColor(GREEN_LIGHT)
        c.drawString(MARGIN_L, y, str(sub_index))
        y -= 22

    # Group title
    title_text = _strip_emoji(_safe(grp, 'title'))
    c.setFont(_font('light'), 20)
    c.setFillColor(ESMERALD)
    c.drawString(MARGIN_L, y, title_text)

    # Item count pill next to title
    items = _safe(grp, 'items', [])
    if items:
        title_w = c.stringWidth(title_text, _font('light'), 20)
        pill_label = f'{len(items)} elemento{"s" if len(items) != 1 else ""}'
        _draw_pill(c, MARGIN_L + title_w + 12, y + 2, pill_label,
                   bg_color=BONE, text_color=ESMERALD)
    y -= 28

    # Thin accent line
    c.setStrokeColor(LEMON)
    c.setLineWidth(2)
    c.line(MARGIN_L, y + 6, MARGIN_L + 40, y + 6)
    y -= 12

    desc = _safe(grp, 'description')
    if desc:
        y = _draw_paragraphs(c, y, [desc], ps=ps)
        y -= 6

    # Render items as 2-column cards
    if not items:
        return y

    col_gap = 12
    row_gap = 14
    card_w = (CONTENT_W - col_gap) / 2
    card_chars = int(card_w / (8 * 0.48)) - 4

    def _card_height(itm):
        d = _strip_emoji(_safe(itm, 'description'))
        dl = textwrap.wrap(d, width=card_chars) if d else []
        return 14 + 14 + len(dl) * 11 + 10

    # Process items in pairs (rows)
    row_y = y
    idx = 0
    while idx < len(items):
        left_item = items[idx]
        right_item = items[idx + 1] if idx + 1 < len(items) else None

        left_h = _card_height(left_item)
        right_h = _card_height(right_item) if right_item else 0
        max_h = max(left_h, right_h)

        # Page check once per row
        if ps:
            row_y = _check_y(c, row_y, ps, need=max_h + 10)
        y = row_y

        for ci, item in enumerate(
            [left_item, right_item] if right_item else [left_item]
        ):
            name = _strip_emoji(_safe(item, 'name'))
            item_desc = _strip_emoji(_safe(item, 'description'))
            desc_lines = (
                textwrap.wrap(item_desc, width=card_chars)
                if item_desc else []
            )
            card_h = 14 + 14 + len(desc_lines) * 11 + 10

            card_x = MARGIN_L + ci * (card_w + col_gap)

            # Card background
            c.setFillColor(ESMERALD_LIGHT)
            c.roundRect(card_x, row_y - card_h + 8, card_w, card_h,
                        6, fill=1, stroke=0)

            # Subtle left accent bar
            c.setFillColor(LEMON)
            c.roundRect(card_x, row_y - card_h + 8, 3, card_h, 1,
                        fill=1, stroke=0)

            # Item name
            inner_x = card_x + 12
            text_y = row_y - 6
            c.setFont(_font('bold'), 9)
            c.setFillColor(ESMERALD)
            c.drawString(inner_x, text_y, name)
            text_y -= 14

            # Item description
            if desc_lines:
                c.setFont(_font('regular'), 8)
                c.setFillColor(ESMERALD_80)
                for dl in desc_lines:
                    c.drawString(inner_x, text_y, dl)
                    text_y -= 11

        row_y = row_y - max_h - row_gap + 8
        y = row_y
        idx += 2 if right_item else 1

    return y


def _render_timeline(c, data, _proposal, ps=None, y=None):
    """Render timeline section with phases."""
    if y is None:
        y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    intro = _safe(data, 'introText')
    if intro:
        y = _draw_paragraphs(c, y, [intro], ps=ps)

    total = _safe(data, 'totalDuration')
    if total:
        # Duration badge
        badge_w = 200
        badge_h = 28
        c.setFillColor(BONE)
        c.roundRect(MARGIN_L, y - badge_h + 4, badge_w, badge_h,
                    4, fill=1, stroke=0)
        c.setFont(_font('regular'), 8)
        c.setFillColor(GRAY_500)
        c.drawString(MARGIN_L + 10, y - 6, 'Duración Total Estimada')
        c.setFont(_font('bold'), 11)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L + 10, y - 19, _strip_emoji(total))
        y -= badge_h + 12

    phases = _safe(data, 'phases', [])
    for i, phase in enumerate(phases):
        if ps:
            y = _check_y(c, y, ps, need=50)
        elif y < MARGIN_B + 50:
            break

        cx = MARGIN_L + 12
        cy = y - 2
        c.setFillColor(ESMERALD)
        c.circle(cx, cy, 9, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(_font('bold'), 8)
        c.drawCentredString(cx, cy - 3, str(i + 1))

        tx = MARGIN_L + 30
        c.setFont(_font('bold'), 11)
        c.setFillColor(ESMERALD)
        c.drawString(tx, y, _strip_emoji(_safe(phase, 'title')))

        dur = _safe(phase, 'duration')
        if dur:
            _draw_pill(c, PAGE_W - MARGIN_R - 80, y + 1,
                       _strip_emoji(dur),
                       bg_color=ESMERALD_LIGHT, text_color=ESMERALD)
        y -= 15

        desc = _safe(phase, 'description')
        if desc:
            c.setFont(_font('regular'), 9)
            c.setFillColor(ESMERALD_80)
            phase_chars = int((PAGE_W - MARGIN_R - tx) / (9 * 0.48))
            d_lines = textwrap.wrap(_strip_emoji(str(desc)), width=phase_chars)
            for dl in d_lines:
                c.drawString(tx, y, dl)
                y -= 12

        tasks = _safe(phase, 'tasks', [])
        if tasks:
            y = _draw_bullet_list(
                c, y, tasks, x=tx, font_size=8, leading=11,
                max_width=CONTENT_W - 40, ps=ps,
            )

        milestone = _safe(phase, 'milestone')
        if milestone:
            _draw_pill(c, tx, y, f'Hito: {_strip_emoji(milestone)}',
                       bg_color=BONE, text_color=ESMERALD, font_size=7)
            y -= 16

        y -= 6
    return y


def _render_investment(c, data, _proposal, ps=None, y=None):
    """Render investment section with two-column layout.

    Left column:  Formas de Pago (payment options).
    Right column: Incluye (what's included).
    Below both:   Compact Inversión Total line.
    """
    if y is None:
        y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    intro = _safe(data, 'introText')
    included = _safe(data, 'whatsIncluded', [])
    total = _safe(data, 'totalInvestment')
    currency = _safe(data, 'currency')
    options = _safe(data, 'paymentOptions', [])

    # Intro text — full width, brief
    if intro:
        y = _draw_paragraphs(c, y, [intro], ps=ps)
        y -= 10

    # ── Two-column area: Formas de Pago (left) | Incluye (right) ──
    col_gap = 20
    left_w = CONTENT_W * 0.58
    right_w = CONTENT_W - left_w - col_gap
    right_x = MARGIN_L + left_w + col_gap
    columns_top = y

    # ── LEFT COLUMN: Formas de Pago ──────────────────────────────
    left_y = columns_top
    if options:
        c.setFont(_font('bold'), 12)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, left_y, 'Formas de Pago')
        left_y -= 20

        for opt in options:
            label = _strip_emoji(_safe(opt, 'label'))
            desc = _strip_emoji(_safe(opt, 'description'))

            # Row background
            c.setFillColor(ESMERALD_LIGHT)
            c.roundRect(MARGIN_L, left_y - 6, left_w, 18, 4,
                        fill=1, stroke=0)
            c.setFont(_font('regular'), 8)
            c.setFillColor(ESMERALD_80)
            c.drawString(MARGIN_L + 8, left_y - 2, label)
            # Amount pill on right edge of column
            if desc:
                _draw_pill(c, MARGIN_L + left_w - 80, left_y - 2, desc,
                           bg_color=ESMERALD, text_color=WHITE, font_size=7)
            left_y -= 22

    # ── RIGHT COLUMN: Incluye ────────────────────────────────────
    right_y = columns_top
    if included:
        items_text = [
            f'{_strip_emoji(_safe(it, "title"))} \u2014 '
            f'{_strip_emoji(_safe(it, "description"))}'
            for it in included
        ]
        _draw_sidebar_box(c, columns_top, 'Incluye', items_text,
                          sidebar_x=right_x, sidebar_w=right_w)

    # Advance y past whichever column is taller
    y = min(left_y, columns_top) - 22

    # ── Compact Inversión Total ──────────────────────────────────
    if total:
        if ps:
            y = _check_y(c, y, ps, need=28)
        box_h = 24
        box_w = CONTENT_W
        box_y = y - box_h
        c.setFillColor(ESMERALD)
        c.roundRect(MARGIN_L, box_y, box_w, box_h, 5, fill=1, stroke=0)
        c.setFont(_font('bold'), 11)
        c.setFillColor(WHITE)
        label = f'Inversi\u00f3n Total: {total}'
        if currency:
            label = f'{label}  {currency}'
        c.drawCentredString(MARGIN_L + box_w / 2, box_y + 7, label)
        y = box_y - 8

    # ── Hosting plan (detailed specs + pricing) ───────────────────
    hosting = _safe(data, 'hostingPlan', {})
    h_title = _safe(hosting, 'title')
    if h_title:
        y -= 14
        if ps:
            y = _check_y(c, y, ps, need=120)
        # Title
        c.setFont(_font('bold'), 12)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, _strip_emoji(str(h_title)))
        y -= 16
        # Description
        h_desc = _safe(hosting, 'description')
        if h_desc:
            y = _draw_paragraphs(c, y, [h_desc], font_size=9,
                                 leading=13, ps=ps)
            y -= 6

        # Specs grid — 2 columns of pill-style badges
        specs = [s for s in _safe(hosting, 'specs', [])
                 if _safe(s, 'label') or _safe(s, 'value')]
        if specs:
            spec_col_w = (CONTENT_W - 14) / 2
            spec_row_h = 28
            for si, spec in enumerate(specs):
                col = si % 2
                if col == 0 and ps:
                    y = _check_y(c, y, ps, need=spec_row_h + 4)
                sx = MARGIN_L + col * (spec_col_w + 14)
                # Badge background
                c.setFillColor(ESMERALD_LIGHT)
                c.roundRect(sx, y - 18, spec_col_w, spec_row_h, 5,
                            fill=1, stroke=0)
                # Vertical centre of badge
                badge_mid_y = y - 18 + spec_row_h / 2
                text_y = badge_mid_y - 3  # baseline offset
                # Label (bold)
                spec_label = _strip_emoji(_safe(spec, 'label'))
                c.setFont(_font('bold'), 8)
                c.setFillColor(ESMERALD)
                c.drawString(sx + 8, text_y, spec_label)
                # Value (regular, right-aligned in badge)
                spec_value = _strip_emoji(_safe(spec, 'value'))
                c.setFont(_font('regular'), 7.5)
                c.setFillColor(ESMERALD_80)
                c.drawRightString(sx + spec_col_w - 8, text_y, spec_value)
                # Move down after every 2nd column
                if col == 1 or si == len(specs) - 1:
                    y -= spec_row_h + 4
            y -= 2

        # Pricing row — monthly + annual side by side
        m_price = _safe(hosting, 'monthlyPrice')
        a_price = _safe(hosting, 'annualPrice')
        if m_price or a_price:
            if ps:
                y = _check_y(c, y, ps, need=40)
            price_col_w = (CONTENT_W - 14) / 2
            price_h = 34
            price_y = y - price_h + 6
            # Vertically centred text positions for price boxes
            p_label_y = price_y + price_h - 11   # top line
            p_price_y = price_y + 5               # bottom line
            if m_price:
                # Monthly — emerald bg, white text
                c.setFillColor(ESMERALD)
                c.roundRect(MARGIN_L, price_y, price_col_w, price_h, 5,
                            fill=1, stroke=0)
                c.setFont(_font('medium'), 7)
                c.setFillColor(colors.HexColor('#A7F3D0'))
                m_label = _strip_emoji(
                    _safe(hosting, 'monthlyLabel', 'por mes'))
                c.drawString(MARGIN_L + 10, p_label_y, m_label)
                c.setFont(_font('bold'), 11)
                c.setFillColor(WHITE)
                c.drawString(MARGIN_L + 10, p_price_y,
                             _strip_emoji(str(m_price)))
            if a_price:
                # Annual — bone bg, esmerald text
                ax = MARGIN_L + price_col_w + 14
                c.setFillColor(BONE)
                c.roundRect(ax, price_y, price_col_w, price_h, 5,
                            fill=1, stroke=0)
                c.setFont(_font('medium'), 7)
                c.setFillColor(GRAY_500)
                a_label = _strip_emoji(
                    _safe(hosting, 'annualLabel', 'pago anual'))
                c.drawString(ax + 10, p_label_y, a_label)
                c.setFont(_font('bold'), 11)
                c.setFillColor(ESMERALD)
                c.drawString(ax + 10, p_price_y,
                             _strip_emoji(str(a_price)))
            y = price_y - 6

        # Coverage note — pill-style block describing the 3 hosting components
        coverage = _safe(hosting, 'coverageNote')
        if coverage:
            y -= 8
            if ps:
                y = _check_y(c, y, ps, need=50)
            # Draw a light background box
            cov_lines = textwrap.wrap(
                _strip_emoji(str(coverage)), width=int(CONTENT_W / (8 * 0.48))
            )
            box_h = len(cov_lines) * 12 + 16
            box_y = y - box_h + 6
            c.setFillColor(ESMERALD_LIGHT)
            c.roundRect(MARGIN_L, box_y, CONTENT_W, box_h, 5,
                        fill=1, stroke=0)
            c.setFont(_font('medium'), 7.5)
            c.setFillColor(ESMERALD)
            ty = y
            for cl in cov_lines:
                c.drawString(MARGIN_L + 10, ty, cl)
                ty -= 12
            y = box_y - 6

        # Renewal note — SMLMV formula text
        renewal = _safe(hosting, 'renewalNote')
        if renewal:
            y -= 6
            if ps:
                y = _check_y(c, y, ps, need=60)
            c.setFont(_font('bold'), 8)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, 'Renovaciones')
            y -= 14
            y = _draw_paragraphs(c, y, [renewal], font_size=8,
                                 leading=11, ps=ps)

    # Value reasons
    reasons = _safe(data, 'valueReasons', [])
    if reasons:
        y -= 8
        y = _draw_subtitle(c, y, '\u00bfPor qu\u00e9 esta inversi\u00f3n?',
                           ps=ps)
        normalized = [
            r if isinstance(r, str)
            else _safe(r, 'description', _safe(r, 'title'))
            for r in reasons
        ]
        y = _draw_bullet_list(c, y, normalized, font_size=9, ps=ps)
    return y


def _render_final_note(c, data, proposal, ps=None, y=None):
    """Render final note section."""
    if y is None:
        y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    badges = _safe(data, 'commitmentBadges', [])

    message = _safe(data, 'message')
    if message:
        y = _draw_paragraphs(c, y, [message], ps=ps)

    personal = _safe(data, 'personalNote')
    if personal:
        y -= 6
        chars = int(CONTENT_W / (10 * 0.48))
        c.setFont(_font('italic'), 10)
        c.setFillColor(GREEN_LIGHT)
        p_lines = textwrap.wrap(_strip_emoji(str(personal)), width=chars)
        for pl in p_lines:
            if ps:
                y = _check_y(c, y, ps)
            c.setFont(_font('italic'), 10)
            c.setFillColor(GREEN_LIGHT)
            c.drawString(MARGIN_L, y, pl)
            y -= 14

    # Validity period — eye-catching banner
    validity = _safe(data, 'validityPeriod',
                     'Esta propuesta tiene una vigencia de 30 d\u00edas '
                     'calendario a partir de su fecha de env\u00edo.')
    if validity:
        y -= 12
        y = _draw_banner_box(c, MARGIN_L, y, CONTENT_W,
                             _strip_emoji(str(validity)),
                             bg_color=BONE, text_color=ESMERALD,
                             icon_text='Vigencia:', ps=ps)

    # Client name
    client_name = getattr(proposal, 'client_name', '')
    if client_name:
        y -= 6
        if ps:
            y = _check_y(c, y, ps, need=20)
        c.setFont(_font('regular'), 8)
        c.setFillColor(GRAY_500)
        c.drawString(MARGIN_L, y,
                     f'Propuesta elaborada para: {client_name}')
        y -= 14

    # Signature
    if ps:
        y = _check_y(c, y, ps, need=60)
    y -= 16
    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.4)
    c.line(MARGIN_L, y, MARGIN_L + 180, y)
    y -= 16
    team = _safe(data, 'teamName')
    role = _safe(data, 'teamRole')
    email = _safe(data, 'contactEmail')
    if team:
        c.setFont(_font('bold'), 12)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, team)
        y -= 15
    if role:
        c.setFont(_font('regular'), 9)
        c.setFillColor(GRAY_500)
        c.drawString(MARGIN_L, y, role)
        y -= 13
    if email:
        c.setFont(_font('regular'), 9)
        c.setFillColor(GRAY_500)
        c.drawString(MARGIN_L, y, email)
        y -= 13

    # Commitment badges as inline pills
    if badges:
        y -= 10
        if ps:
            y = _check_y(c, y, ps, need=40)
        c.setFont(_font('bold'), 10)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, 'Compromisos')
        y -= 18
        pill_x = MARGIN_L
        for b in badges:
            b_title = _strip_emoji(_safe(b, 'title'))
            if not b_title:
                continue
            c.setFont(_font('medium'), 7)
            tw = c.stringWidth(b_title, _font('medium'), 7) + 16
            # Wrap to next row if pill overflows
            if pill_x + tw > PAGE_W - MARGIN_R:
                pill_x = MARGIN_L
                y -= 18
                if ps:
                    y = _check_y(c, y, ps)
            _draw_pill(c, pill_x, y, b_title,
                       bg_color=ESMERALD_LIGHT, text_color=ESMERALD)
            pill_x += tw + 6
        y -= 14
    return y


def _render_next_steps(c, data, _proposal, ps=None, y=None):
    """Render next steps section."""
    if y is None:
        y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    contacts = _safe(data, 'contactMethods', [])

    intro = _safe(data, 'introMessage')
    if intro:
        y = _draw_paragraphs(c, y, [intro], ps=ps)
        y -= 6

    steps = _safe(data, 'steps', [])
    for i, step in enumerate(steps):
        if ps:
            y = _check_y(c, y, ps, need=30)
        elif y < MARGIN_B + 30:
            break
        step_title = _safe(step, 'title')
        step_desc = _safe(step, 'description')

        c.setFont(_font('bold'), 11)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, f'{i + 1}.  {_strip_emoji(step_title)}')
        y -= 15

        if step_desc:
            c.setFont(_font('regular'), 9)
            c.setFillColor(ESMERALD_80)
            desc_w = CONTENT_W - 18  # account for x offset
            desc_chars = int(desc_w / (9 * 0.48))
            s_lines = textwrap.wrap(_strip_emoji(str(step_desc)), width=desc_chars)
            for sl in s_lines:
                if ps:
                    y = _check_y(c, y, ps)
                    c.setFont(_font('regular'), 9)
                    c.setFillColor(ESMERALD_80)
                c.drawString(MARGIN_L + 18, y, sl)
                y -= 13
        y -= 5

    # CTA message
    cta = _safe(data, 'ctaMessage')
    if cta:
        y -= 8
        c.setFont(_font('bold'), 12)
        c.setFillColor(ESMERALD)
        cta_chars = int(CONTENT_W / (12 * 0.48))
        cta_lines = textwrap.wrap(_strip_emoji(str(cta)), width=cta_chars)
        for cl in cta_lines:
            if ps:
                y = _check_y(c, y, ps)
            c.setFont(_font('bold'), 12)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, cl)
            y -= 16

    # Contact methods as pills
    if contacts:
        y -= 10
        if ps:
            y = _check_y(c, y, ps, need=40)
        c.setFont(_font('bold'), 10)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, 'Contacto')
        y -= 18
        for ct in contacts:
            ct_title = _strip_emoji(_safe(ct, 'title'))
            ct_value = _strip_emoji(_safe(ct, 'value'))
            if not ct_title:
                continue
            if ps:
                y = _check_y(c, y, ps, need=18)
            # Title pill + value text
            pr, _ = _draw_pill(c, MARGIN_L, y, ct_title,
                               bg_color=ESMERALD, text_color=WHITE,
                               font_size=7)
            c.setFont(_font('regular'), 9)
            c.setFillColor(ESMERALD_80)
            c.drawString(pr + 8, y, ct_value)
            y -= 18
    return y


def _parse_markdown_lines(raw):
    """Parse raw markdown text into a list of (type, text) tuples.

    Supported types: 'h1', 'h2', 'h3', 'h4', 'bullet', 'numbered',
    'bold_line', 'paragraph', 'blank'.
    Inline **bold** markers are stripped into clean text.
    """
    if not raw:
        return []
    result = []
    for line in raw.split('\n'):
        stripped = line.strip()
        if not stripped:
            result.append(('blank', ''))
            continue
        # Headings
        if stripped.startswith('#### '):
            result.append(('h4', stripped[5:].strip()))
        elif stripped.startswith('### '):
            result.append(('h3', stripped[4:].strip()))
        elif stripped.startswith('## '):
            result.append(('h2', stripped[3:].strip()))
        elif stripped.startswith('# '):
            result.append(('h1', stripped[2:].strip()))
        # Bullet list
        elif stripped.startswith('- ') or stripped.startswith('* '):
            result.append(('bullet', stripped[2:].strip()))
        # Numbered list (e.g. "1. ", "2. ")
        elif len(stripped) > 2 and stripped[0].isdigit() and '. ' in stripped[:5]:
            idx = stripped.index('. ')
            result.append(('numbered', stripped[idx + 2:].strip()))
        # Line that is entirely bold  **text**
        elif stripped.startswith('**') and stripped.endswith('**') and len(stripped) > 4:
            result.append(('bold_line', stripped[2:-2].strip()))
        else:
            result.append(('paragraph', stripped))
    return result


def _clean_inline_bold(text):
    """Strip **bold** markers from inline text for PDF rendering."""
    return re.sub(r'\*\*(.+?)\*\*', r'\1', text)


def _render_raw_text(c, data, _proposal, ps=None, y=None):
    """Render a paste-mode section with parsed markdown content."""
    if y is None:
        y = PAGE_H - MARGIN_T
    index_str = _safe(data, 'index')
    title = _safe(data, 'title', 'Sección')
    y = _draw_section_header(c, y, index_str, title)
    y -= 8

    raw = _safe(data, 'rawText')
    if not raw:
        return y

    tokens = _parse_markdown_lines(raw)
    for kind, text in tokens:
        text = _strip_emoji(_clean_inline_bold(text))

        if kind == 'blank':
            y -= 6
            continue

        if kind == 'h1':
            if ps:
                y = _check_y(c, y, ps, need=30)
            y -= 4
            c.setFont(_font('bold'), 16)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, text)
            y -= 22
        elif kind == 'h2':
            if ps:
                y = _check_y(c, y, ps, need=26)
            y -= 4
            c.setFont(_font('bold'), 13)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, text)
            y -= 19
        elif kind in ('h3', 'h4'):
            if ps:
                y = _check_y(c, y, ps, need=22)
            y -= 2
            c.setFont(_font('bold'), 11)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, text)
            y -= 16
        elif kind == 'bold_line':
            if ps:
                y = _check_y(c, y, ps, need=18)
            c.setFont(_font('bold'), 10)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, text)
            y -= 15
        elif kind == 'bullet':
            y = _draw_bullet_list(c, y, [text], ps=ps)
        elif kind == 'numbered':
            y = _draw_bullet_list(c, y, [text], ps=ps)
        else:  # paragraph
            y = _draw_paragraphs(c, y, [text], ps=ps)
    return y


# Map section_type → renderer
SECTION_RENDERERS = {
    'greeting': _render_greeting,
    'executive_summary': _render_executive_summary,
    'context_diagnostic': _render_context_diagnostic,
    'conversion_strategy': _render_conversion_strategy,
    'design_ux': _render_design_ux,
    'creative_support': _render_creative_support,
    'development_stages': _render_development_stages,
    'functional_requirements': _render_functional_requirements,
    'timeline': _render_timeline,
    'investment': _render_investment,
    'final_note': _render_final_note,
    'next_steps': _render_next_steps,
}


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

class ProposalPdfService:
    """
    Generate a professional PDF of a business proposal using ReportLab.

    Usage:
        pdf_bytes = ProposalPdfService.generate(proposal)
    """

    @classmethod
    def generate(cls, proposal):
        """
        Build a multi-page portrait-A4 PDF from the proposal's
        enabled sections and return the raw bytes.

        Sections flow continuously — each section starts where the
        previous one ended.  The greeting/cover page is the only
        section that always gets its own page.

        Args:
            proposal: BusinessProposal instance with related sections.

        Returns:
            bytes: The PDF content, or None on failure.
        """
        try:
            _register_fonts()

            sections = list(
                proposal.sections
                .filter(is_enabled=True)
                .order_by('order')
            )

            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            c.setTitle(f'Propuesta \u2014 {proposal.client_name}')
            c.setAuthor('Project App')

            ps = {
                'num': 1,
                'client': proposal.client_name,
            }

            # Start first page
            _draw_header_bar(c)
            y = PAGE_H - MARGIN_T
            page_started = True
            first_content = True  # track whether we need greeting's own page

            for sec in sections:
                stype = sec.section_type
                data = sec.content_json or {}

                if 'title' not in data or not data['title']:
                    data['title'] = sec.title
                if not data.get('index'):
                    data['index'] = str(sec.order + 1).zfill(2)

                # Decide rendering mode: paste-mode wins over form
                is_paste = (
                    data.get('_editMode') == 'paste'
                    and data.get('rawText')
                )
                renderer = SECTION_RENDERERS.get(stype)

                # ── Greeting gets its own full page ──────────────
                if stype == 'greeting':
                    if not first_content:
                        # finish current page and start fresh
                        _draw_footer(c, ps['num'], client_name=ps['client'])
                        c.showPage()
                        ps['num'] += 1
                        _draw_header_bar(c)
                    first_content = False
                    if is_paste:
                        _render_raw_text(c, data, proposal, ps=ps)
                    elif renderer:
                        renderer(c, data, proposal, ps=ps)
                    _draw_footer(c, ps['num'], client_name=ps['client'])
                    c.showPage()
                    ps['num'] += 1
                    _draw_header_bar(c)
                    y = PAGE_H - MARGIN_T
                    page_started = True
                    continue

                # ── All other sections flow continuously ─────────
                if first_content:
                    first_content = False
                else:
                    # Section separator space
                    y -= 28
                    # Need room for header (~80pt); if not, new page
                    y = _check_y(c, y, ps, need=80)

                if is_paste:
                    y = _render_raw_text(c, data, proposal, ps=ps,
                                         y=y) or y
                elif renderer:
                    y = renderer(c, data, proposal, ps=ps, y=y) or y

                    # Functional requirements: per-group details
                    func_groups = ps.pop('_func_req_groups', None)
                    parent_idx = data.get('index', '')
                    if stype == 'functional_requirements' and func_groups:
                        for gi, grp in enumerate(func_groups):
                            grp_paste = (
                                _safe(grp, '_editMode') == 'paste'
                                and _safe(grp, 'rawText')
                            )
                            items = _safe(grp, 'items', [])
                            if not items and not grp_paste:
                                continue
                            sub_idx = (
                                f'{parent_idx}.{gi + 1}'
                                if parent_idx else str(gi + 1)
                            )
                            y -= 28
                            y = _check_y(c, y, ps, need=80)
                            if grp_paste:
                                y = _render_raw_text(
                                    c,
                                    {'title': _safe(grp, 'title'),
                                     'index': sub_idx,
                                     'rawText': _safe(grp, 'rawText')},
                                    proposal, ps=ps, y=y,
                                ) or y
                            else:
                                y = _render_requirement_group_page(
                                    c, grp, ps=ps, y=y,
                                    sub_index=sub_idx,
                                ) or y
                elif data.get('rawText'):
                    y = _render_raw_text(c, data, proposal, ps=ps,
                                         y=y) or y

            # Finalize last page
            if page_started:
                _draw_footer(c, ps['num'], client_name=ps['client'])

            c.save()
            content_bytes = buf.getvalue()
            buf.close()

            pdf_bytes = cls._merge_with_covers(content_bytes)

            logger.info(
                'Generated PDF for proposal %s (%d bytes, %d pages)',
                proposal.uuid, len(pdf_bytes), ps['num'],
            )
            return pdf_bytes

        except Exception:
            logger.exception(
                'Failed to generate PDF for proposal %s', proposal.uuid,
            )
            return None

    @staticmethod
    def _merge_with_covers(content_bytes):
        """
        Merge static cover (Portada) and back cover (Contraportada)
        PDFs with the generated proposal content.

        Returns the merged PDF bytes, or the original content_bytes
        if cover files are not found.
        """
        writer = PdfWriter()

        if COVER_PDF.exists():
            try:
                cover_reader = PdfReader(str(COVER_PDF))
                for page in cover_reader.pages:
                    writer.add_page(page)
            except Exception:
                logger.warning('Could not read cover PDF: %s', COVER_PDF)

        content_reader = PdfReader(io.BytesIO(content_bytes))
        for page in content_reader.pages:
            writer.add_page(page)

        if BACK_COVER_PDF.exists():
            try:
                back_reader = PdfReader(str(BACK_COVER_PDF))
                for page in back_reader.pages:
                    writer.add_page(page)
            except Exception:
                logger.warning(
                    'Could not read back cover PDF: %s', BACK_COVER_PDF,
                )

        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()

    @classmethod
    def generate_to_file(cls, proposal, output_path=None):
        """
        Generate PDF and save to a file. Returns the file path or None.

        Args:
            proposal: BusinessProposal instance.
            output_path: Optional path. If None, uses a temp file.

        Returns:
            str: Path to the generated PDF file, or None on failure.
        """
        pdf_bytes = cls.generate(proposal)
        if not pdf_bytes:
            return None

        if output_path is None:
            media_temp = Path(settings.MEDIA_ROOT) / 'temp'
            media_temp.mkdir(parents=True, exist_ok=True)
            fd, output_path = tempfile.mkstemp(
                suffix='.pdf',
                prefix=f'proposal_{proposal.uuid}_',
                dir=str(media_temp),
            )
            os.close(fd)

        output_path = str(output_path)
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

        logger.info('Saved PDF to %s', output_path)
        return output_path
