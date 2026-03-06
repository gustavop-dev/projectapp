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
    _draw_footer(c, ps['num'], ps['total'], ps['client'])
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


def _draw_footer(c, page_num, total_pages, client_name=''):
    """Draw a discrete footer with page number and branding."""
    footer_y = MARGIN_B - 14
    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.4)
    c.line(MARGIN_L, footer_y, PAGE_W - MARGIN_R, footer_y)
    c.setFont(_font('regular'), 7)
    c.setFillColor(GRAY_500)
    c.drawString(MARGIN_L, footer_y - 11, 'Project App  |  projectapp.co')
    c.setFont(_font('regular'), 7)
    c.setFillColor(GREEN_LIGHT)
    c.drawRightString(
        PAGE_W - MARGIN_R, footer_y - 11,
        f'{page_num} / {total_pages}',
    )


def _draw_section_header(c, y, index_str, title, ps=None):
    """Draw section index + title and return the new y position."""
    if index_str:
        c.setFont(_font('light'), 11)
        c.setFillColor(GREEN_LIGHT)
        c.drawString(MARGIN_L, y, str(index_str).zfill(2))
        y -= 8
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


def _render_executive_summary(c, data, _proposal, ps=None):
    """Render executive summary with paragraphs + sidebar highlights."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    paragraphs = _safe(data, 'paragraphs', [])
    highlights = _safe(data, 'highlights', [])
    hl_title = _safe(data, 'highlightsTitle', 'Aspectos Clave')

    if highlights:
        y = _draw_paragraphs(c, y, paragraphs, max_width=TEXT_AREA_W, ps=ps)
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 50, hl_title, highlights)
    else:
        y = _draw_paragraphs(c, y, paragraphs, ps=ps)


def _render_context_diagnostic(c, data, _proposal, ps=None):
    """Render context & diagnostic section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    issues = _safe(data, 'issues', [])
    issues_title = _safe(data, 'issuesTitle', 'Problemas Identificados')

    text_w = TEXT_AREA_W if issues else None
    y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []),
                         max_width=text_w, ps=ps)

    # Opportunity block
    opp_title = _safe(data, 'opportunityTitle')
    opp = _safe(data, 'opportunity')
    if opp:
        y -= 6
        y = _draw_subtitle(c, y, opp_title or 'La oportunidad', ps=ps)
        y = _draw_paragraphs(c, y, [opp], max_width=text_w, ps=ps)

    if issues:
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 50, issues_title, issues)


def _render_conversion_strategy(c, data, _proposal, ps=None):
    """Render conversion strategy section."""
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


def _render_design_ux(c, data, _proposal, ps=None):
    """Render design & UX section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    focus_items = _safe(data, 'focusItems', [])
    focus_title = _safe(data, 'focusTitle', 'Enfoque')
    text_w = TEXT_AREA_W if focus_items else None

    y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []),
                         max_width=text_w, ps=ps)

    obj_title = _safe(data, 'objectiveTitle')
    obj = _safe(data, 'objective')
    if obj:
        y -= 6
        y = _draw_subtitle(c, y, obj_title or 'Objetivo', ps=ps)
        y = _draw_paragraphs(c, y, [obj], max_width=text_w, ps=ps)

    if focus_items:
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 50, focus_title, focus_items)


def _render_creative_support(c, data, _proposal, ps=None):
    """Render creative support section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    includes = _safe(data, 'includes', [])
    inc_title = _safe(data, 'includesTitle', 'Incluye')
    text_w = TEXT_AREA_W if includes else None

    y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []),
                         max_width=text_w, ps=ps)

    closing = _safe(data, 'closing')
    if closing:
        y -= 6
        y = _draw_paragraphs(c, y, [closing], max_width=text_w, ps=ps)

    if includes:
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 50, inc_title, includes)


def _render_development_stages(c, data, _proposal, ps=None):
    """Render development stages as a vertical timeline."""
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
        y -= 15

        if desc:
            c.setFont(_font('regular'), 9)
            c.setFillColor(ESMERALD_80)
            d_lines = textwrap.wrap(_strip_emoji(str(desc)), width=70)
            for dl in d_lines:
                c.drawString(tx, y, dl)
                y -= 13
        y -= 12


def _render_functional_requirements(c, data, proposal, ps=None):
    """Render functional requirements overview page."""
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
    for idx, grp in enumerate(all_groups):
        col = idx % 2
        row = idx // 2
        card_x = MARGIN_L + col * (col_w + 16)
        card_y = y - row * 62

        if card_y < MARGIN_B + 30:
            break

        c.setFillColor(ESMERALD_LIGHT)
        c.roundRect(card_x, card_y - 44, col_w, 50, 5, fill=1, stroke=0)

        c.setFont(_font('bold'), 10)
        c.setFillColor(ESMERALD)
        c.drawString(card_x + 8, card_y - 10,
                     _strip_emoji(_safe(grp, 'title')))

        desc = _safe(grp, 'description')
        if desc:
            c.setFont(_font('regular'), 8)
            c.setFillColor(ESMERALD_80)
            d_lines = textwrap.wrap(_strip_emoji(str(desc)), width=chars)
            dy = card_y - 24
            for dl in d_lines[:2]:
                c.drawString(card_x + 8, dy, dl)
                dy -= 11

    return all_groups


def _render_requirement_group_page(c, grp, ps=None):
    """Render a single requirement group on its own page."""
    y = PAGE_H - MARGIN_T

    c.setFont(_font('light'), 20)
    c.setFillColor(ESMERALD)
    c.drawString(MARGIN_L, y, _strip_emoji(_safe(grp, 'title')))
    y -= 28

    desc = _safe(grp, 'description')
    if desc:
        y = _draw_paragraphs(c, y, [desc], ps=ps)
        y -= 8

    items = _safe(grp, 'items', [])
    for item in items:
        if ps:
            y = _check_y(c, y, ps, need=30)
        elif y < MARGIN_B + 30:
            break
        name = _safe(item, 'name')
        item_desc = _safe(item, 'description')

        c.setFont(_font('bold'), 10)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L + 4, y, f'\u2022  {_strip_emoji(name)}')
        y -= 14

        if item_desc:
            c.setFont(_font('regular'), 9)
            c.setFillColor(ESMERALD_80)
            i_lines = textwrap.wrap(_strip_emoji(str(item_desc)), width=80)
            for il in i_lines:
                if ps:
                    y = _check_y(c, y, ps)
                elif y < MARGIN_B + 20:
                    break
                c.drawString(MARGIN_L + 20, y, il)
                y -= 13
        y -= 5


def _render_timeline(c, data, _proposal, ps=None):
    """Render timeline section with phases."""
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
            c.setFont(_font('regular'), 8)
            c.setFillColor(GREEN_LIGHT)
            c.drawRightString(PAGE_W - MARGIN_R, y, _strip_emoji(dur))
        y -= 15

        desc = _safe(phase, 'description')
        if desc:
            c.setFont(_font('regular'), 9)
            c.setFillColor(ESMERALD_80)
            d_lines = textwrap.wrap(_strip_emoji(str(desc)), width=75)
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
            c.setFont(_font('bold'), 8)
            c.setFillColor(ESMERALD)
            c.drawString(tx, y, f'Hito: {_strip_emoji(milestone)}')
            y -= 12

        y -= 6


def _render_investment(c, data, _proposal, ps=None):
    """Render investment section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    intro = _safe(data, 'introText')
    if intro:
        y = _draw_paragraphs(c, y, [intro], ps=ps)
        y -= 6

    # Total investment highlight box
    total = _safe(data, 'totalInvestment')
    currency = _safe(data, 'currency')
    if total:
        box_h = 54
        box_w = CONTENT_W
        box_y = y - box_h
        c.setFillColor(ESMERALD)
        c.roundRect(MARGIN_L, box_y, box_w, box_h, 8, fill=1, stroke=0)
        c.setFont(_font('bold'), 26)
        c.setFillColor(WHITE)
        c.drawCentredString(MARGIN_L + box_w / 2, box_y + 26, total)
        if currency:
            c.setFont(_font('regular'), 10)
            c.setFillColor(LEMON)
            c.drawCentredString(MARGIN_L + box_w / 2, box_y + 8, currency)
        y = box_y - 14

    # Payment options
    options = _safe(data, 'paymentOptions', [])
    if options:
        y -= 4
        y = _draw_subtitle(c, y, 'Formas de Pago', ps=ps)
        for opt in options:
            if ps:
                y = _check_y(c, y, ps)
            elif y < MARGIN_B + 20:
                break
            label = _safe(opt, 'label')
            desc = _safe(opt, 'description')
            c.setFont(_font('regular'), 9)
            c.setFillColor(ESMERALD_80)
            c.drawString(MARGIN_L + 8, y,
                         f'\u2022  {_strip_emoji(label)}')
            c.setFont(_font('bold'), 9)
            c.drawRightString(PAGE_W - MARGIN_R, y, _strip_emoji(desc))
            y -= 15

    # Hosting plan
    hosting = _safe(data, 'hostingPlan', {})
    h_title = _safe(hosting, 'title')
    if h_title:
        y -= 8
        y = _draw_subtitle(c, y, h_title, ps=ps)
        h_desc = _safe(hosting, 'description')
        if h_desc:
            y = _draw_paragraphs(c, y, [h_desc], font_size=9,
                                 leading=13, ps=ps)

    # What's included sidebar
    included = _safe(data, 'whatsIncluded', [])
    if included:
        items_text = [
            f'{_strip_emoji(_safe(it, "title"))} \u2014 '
            f'{_strip_emoji(_safe(it, "description"))}'
            for it in included
        ]
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 50, 'Incluye', items_text)

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


def _render_final_note(c, data, _proposal, ps=None):
    """Render final note section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

    message = _safe(data, 'message')
    if message:
        y = _draw_paragraphs(c, y, [message], ps=ps)

    personal = _safe(data, 'personalNote')
    if personal:
        y -= 6
        c.setFont(_font('italic'), 10)
        c.setFillColor(GREEN_LIGHT)
        p_lines = textwrap.wrap(_strip_emoji(str(personal)), width=70)
        for pl in p_lines:
            if ps:
                y = _check_y(c, y, ps)
            c.setFont(_font('italic'), 10)
            c.setFillColor(GREEN_LIGHT)
            c.drawString(MARGIN_L, y, pl)
            y -= 14

    # Signature
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

    # Commitment badges in sidebar
    badges = _safe(data, 'commitmentBadges', [])
    if badges:
        items = [
            f'{_strip_emoji(_safe(b, "title"))} \u2014 '
            f'{_strip_emoji(_safe(b, "description"))}'
            for b in badges
        ]
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 50, 'Compromisos', items)


def _render_next_steps(c, data, _proposal, ps=None):
    """Render next steps section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 8

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
            s_lines = textwrap.wrap(_strip_emoji(str(step_desc)), width=70)
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
        cta_lines = textwrap.wrap(_strip_emoji(str(cta)), width=55)
        for cl in cta_lines:
            if ps:
                y = _check_y(c, y, ps)
            c.setFont(_font('bold'), 12)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, cl)
            y -= 16

    # Contact methods sidebar
    contacts = _safe(data, 'contactMethods', [])
    if contacts:
        items = [
            f'{_strip_emoji(_safe(ct, "title"))}: '
            f'{_strip_emoji(_safe(ct, "value"))}'
            for ct in contacts
        ]
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 50, 'Contacto', items)


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


def _render_raw_text(c, data, _proposal, ps=None):
    """Render a paste-mode section with parsed markdown content."""
    y = PAGE_H - MARGIN_T
    index_str = _safe(data, 'index')
    title = _safe(data, 'title', 'Sección')
    y = _draw_section_header(c, y, index_str, title)
    y -= 8

    raw = _safe(data, 'rawText')
    if not raw:
        return

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

            # Estimate total pages (auto-pagination may add more)
            extra_pages = 0
            for sec in sections:
                if sec.section_type == 'functional_requirements':
                    data = sec.content_json or {}
                    groups = list(data.get('groups', []))
                    groups += list(data.get('additionalModules', []))
                    db_groups = proposal.requirement_groups.count()
                    extra_pages += len(groups) + db_groups

            total_pages = len(sections) + extra_pages

            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            c.setTitle(f'Propuesta \u2014 {proposal.client_name}')
            c.setAuthor('Project App')

            ps = {
                'num': 0,
                'total': total_pages,
                'client': proposal.client_name,
            }

            for sec in sections:
                stype = sec.section_type
                data = sec.content_json or {}

                if 'title' not in data or not data['title']:
                    data['title'] = sec.title

                # Decide rendering mode: paste-mode wins over form
                is_paste = (
                    data.get('_editMode') == 'paste'
                    and data.get('rawText')
                )
                renderer = SECTION_RENDERERS.get(stype)

                if is_paste:
                    # Paste-mode: render raw markdown regardless of type
                    ps['num'] += 1
                    _draw_header_bar(c)
                    _render_raw_text(c, data, proposal, ps=ps)
                    _draw_footer(
                        c, ps['num'], ps['total'], proposal.client_name,
                    )
                    c.showPage()
                elif renderer:
                    ps['num'] += 1
                    _draw_header_bar(c)
                    result = renderer(c, data, proposal, ps=ps)
                    _draw_footer(
                        c, ps['num'], ps['total'], proposal.client_name,
                    )
                    c.showPage()

                    # Functional requirements: per-group detail pages
                    if stype == 'functional_requirements' and isinstance(
                        result, list
                    ):
                        for grp in result:
                            grp_paste = (
                                _safe(grp, '_editMode') == 'paste'
                                and _safe(grp, 'rawText')
                            )
                            items = _safe(grp, 'items', [])
                            if not items and not grp_paste:
                                continue
                            ps['num'] += 1
                            _draw_header_bar(c)
                            if grp_paste:
                                _render_raw_text(
                                    c,
                                    {'title': _safe(grp, 'title'),
                                     'rawText': _safe(grp, 'rawText')},
                                    proposal, ps=ps,
                                )
                            else:
                                _render_requirement_group_page(
                                    c, grp, ps=ps,
                                )
                            _draw_footer(
                                c, ps['num'], ps['total'],
                                proposal.client_name,
                            )
                            c.showPage()
                elif data.get('rawText'):
                    # Unknown section type with rawText fallback
                    ps['num'] += 1
                    _draw_header_bar(c)
                    _render_raw_text(c, data, proposal, ps=ps)
                    _draw_footer(
                        c, ps['num'], ps['total'], proposal.client_name,
                    )
                    c.showPage()

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
