"""
Service for generating professional PDF business proposals
using ReportLab.

Each enabled section is rendered on its own landscape-A4 page with
an emerald/green colour scheme that mirrors the frontend design.
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
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

# ── Brand colours (match frontend Tailwind palette) ──────────
ESMERALD = colors.HexColor('#064E3B')
ESMERALD_80 = colors.HexColor('#37705C')
GREEN_LIGHT = colors.HexColor('#10B981')
GREEN_BG = colors.HexColor('#ECFDF5')
GREEN_DARK = colors.HexColor('#065F46')
GRAY_700 = colors.HexColor('#374151')
GRAY_500 = colors.HexColor('#6B7280')
GRAY_200 = colors.HexColor('#E5E7EB')
WHITE = colors.white

# ── Cover / back-cover PDF paths ─────────────────────────────
COVER_PDF = Path(settings.MEDIA_ROOT) / 'front_page' / 'Portada_ProjectApp.pdf'
BACK_COVER_PDF = (
    Path(settings.MEDIA_ROOT) / 'front_page' / 'Contraportada_ProjectApp.pdf'
)

# ── Page dimensions (landscape A4) ───────────────────────────
PAGE_W, PAGE_H = landscape(A4)  # ≈841 × 595 pt
MARGIN_L = 50
MARGIN_R = 50
MARGIN_T = 50
MARGIN_B = 40
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R
TEXT_AREA_W = CONTENT_W * 0.58
SIDEBAR_X = MARGIN_L + TEXT_AREA_W + 30
SIDEBAR_W = CONTENT_W - TEXT_AREA_W - 30


# ─────────────────────────────────────────────────────────────
# Drawing helpers
# ─────────────────────────────────────────────────────────────

def _draw_green_bar(c):
    """Draw a green accent bar at the top of the page."""
    c.setFillColor(ESMERALD)
    c.rect(0, PAGE_H - 8, PAGE_W, 8, fill=1, stroke=0)
    # Thin highlight line below
    c.setFillColor(GREEN_LIGHT)
    c.rect(0, PAGE_H - 10, PAGE_W, 2, fill=1, stroke=0)


def _draw_footer(c, page_num, total_pages, client_name=''):
    """Draw a discrete footer with a separator line, page number, and client name."""
    footer_y = MARGIN_B - 10
    c.setStrokeColor(GRAY_200)
    c.setLineWidth(0.5)
    c.line(MARGIN_L, footer_y, PAGE_W - MARGIN_R, footer_y)
    c.setFont('Helvetica', 8)
    c.setFillColor(GRAY_500)
    c.drawString(MARGIN_L, footer_y - 12, client_name)
    c.drawRightString(
        PAGE_W - MARGIN_R, footer_y - 12,
        f'{page_num} / {total_pages}',
    )
    # Small green dot before page number
    c.setFillColor(GREEN_LIGHT)
    c.circle(PAGE_W - MARGIN_R - 42, footer_y - 8, 2, fill=1, stroke=0)


def _draw_section_header(c, y, index_str, title):
    """Draw section index + title and return the new y position."""
    if index_str:
        # Section number in a small green circle
        c.setFillColor(GREEN_LIGHT)
        c.circle(MARGIN_L + 10, y + 4, 11, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 9)
        c.setFillColor(WHITE)
        c.drawCentredString(MARGIN_L + 10, y + 1, str(index_str))
        y -= 20
    c.setFont('Helvetica-Bold', 26)
    c.setFillColor(ESMERALD)
    # Wrap long titles
    max_chars = 42
    clean_title = _strip_emoji(title)
    if len(clean_title) > max_chars:
        lines = textwrap.wrap(clean_title, width=max_chars)
        for line in lines:
            c.drawString(MARGIN_L, y, line)
            y -= 32
    else:
        c.drawString(MARGIN_L, y, clean_title)
        y -= 32
    # Accent line under title
    c.setStrokeColor(GREEN_LIGHT)
    c.setLineWidth(2)
    c.line(MARGIN_L, y + 6, MARGIN_L + 80, y + 6)
    y -= 16
    return y


def _draw_paragraphs(c, y, paragraphs, max_width=None, font_size=11,
                      leading=16, color=ESMERALD_80):
    """Draw a list of paragraph strings and return the new y."""
    if max_width is None:
        max_width = TEXT_AREA_W
    chars_per_line = int(max_width / (font_size * 0.52))
    c.setFont('Helvetica', font_size)
    c.setFillColor(color)
    for para in (paragraphs or []):
        if not para:
            continue
        lines = textwrap.wrap(_strip_emoji(str(para)), width=chars_per_line)
        for line in lines:
            if y < MARGIN_B + 20:
                return y
            c.drawString(MARGIN_L, y, line)
            y -= leading
        y -= 6  # extra spacing between paragraphs
    return y


def _draw_bullet_list(c, y, items, x=MARGIN_L, max_width=None,
                       font_size=10, leading=14, color=ESMERALD_80,
                       bullet='•'):
    """Draw a bulleted list and return the new y."""
    if max_width is None:
        max_width = TEXT_AREA_W
    chars_per_line = int(max_width / (font_size * 0.52))
    c.setFont('Helvetica', font_size)
    c.setFillColor(color)
    for item in (items or []):
        text = _strip_emoji(str(item))
        lines = textwrap.wrap(text, width=chars_per_line - 4)
        for i, line in enumerate(lines):
            if y < MARGIN_B + 20:
                return y
            prefix = f'  {bullet}  ' if i == 0 else '      '
            c.drawString(x, y, f'{prefix}{line}')
            y -= leading
        y -= 2
    return y


def _draw_sidebar_box(c, y_start, title, items, sidebar_x=None,
                       sidebar_w=None):
    """Draw a light-green sidebar box with a title and bullet items."""
    sx = sidebar_x or SIDEBAR_X
    sw = sidebar_w or SIDEBAR_W
    # Estimate height
    line_h = 14
    header_h = 24
    items_h = sum(
        max(1, len(textwrap.wrap(str(it), width=int(sw / 5.5)))) * line_h + 2
        for it in (items or [])
    )
    box_h = header_h + items_h + 16
    box_y = y_start - box_h

    # Background
    c.setFillColor(GREEN_BG)
    c.roundRect(sx, box_y, sw, box_h, 8, fill=1, stroke=0)

    # Title
    inner_y = y_start - 18
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(ESMERALD)
    c.drawString(sx + 12, inner_y, str(title))
    inner_y -= 18

    # Items
    c.setFont('Helvetica', 10)
    c.setFillColor(ESMERALD_80)
    chars = int(sw / 5.5)
    for item in (items or []):
        text = _strip_emoji(str(item))
        lines = textwrap.wrap(text, width=chars)
        for j, line in enumerate(lines):
            prefix = '•  ' if j == 0 else '    '
            c.drawString(sx + 12, inner_y, f'{prefix}{line}')
            inner_y -= line_h
        inner_y -= 2

    return box_y


def _draw_subtitle(c, y, text, color=ESMERALD):
    """Draw a bold subtitle and return the new y."""
    c.setFont('Helvetica-Bold', 13)
    c.setFillColor(color)
    c.drawString(MARGIN_L, y, _strip_emoji(str(text)))
    return y - 20


# Regex to strip emoji and symbols that Helvetica cannot render.
# Covers: Emoticons, Symbols, Dingbats, Variation Selectors,
# Supplemental Symbols, Misc Technical, Transport, Flags, etc.
_EMOJI_RE = re.compile(
    '['
    '\U0001F000-\U0001FFFF'   # All Supplementary Multilingual Plane emojis
    '\U00002600-\U000027BF'   # Misc Symbols + Dingbats
    '\U00002300-\U000023FF'   # Misc Technical
    '\U0000FE00-\U0000FE0F'   # Variation Selectors
    '\U0000200D'               # Zero Width Joiner
    '\U000020E3'               # Combining Enclosing Keycap
    '\U00002B50-\U00002B55'   # Stars, circles
    '\U000025A0-\U000025FF'   # Geometric Shapes
    '\U00002702-\U000027B0'   # Dingbats
    '\U0000231A-\U0000231B'   # Watch, Hourglass
    '\U000023E9-\U000023F3'   # Media controls
    '\U000023F8-\U000023FA'   # Media controls 2
    '\U0000200B'               # Zero Width Space
    '\U0000FFFD'               # Replacement Character
    ']+',
)


def _strip_emoji(text):
    """Remove emoji/symbol characters that Helvetica cannot render."""
    if not text:
        return text
    return _EMOJI_RE.sub('', str(text)).strip()


def _safe(data, key, default=''):
    """Safely get a key from a dict, returning default if missing."""
    if not isinstance(data, dict):
        return default
    return data.get(key, default) or default


# ─────────────────────────────────────────────────────────────
# Section renderers
# ─────────────────────────────────────────────────────────────

def _render_greeting(c, data, proposal):
    """Render the greeting/cover page."""
    # Large decorative circle in top-right corner (subtle branding)
    c.saveState()
    c.setFillColor(GREEN_BG)
    c.circle(PAGE_W - 80, PAGE_H - 60, 180, fill=1, stroke=0)
    c.restoreState()

    # Small accent circle bottom-left
    c.saveState()
    c.setFillColor(GREEN_BG)
    c.circle(60, 50, 90, fill=1, stroke=0)
    c.restoreState()

    # Centre content vertically
    mid_y = PAGE_H / 2 + 50

    # "Propuesta para" label
    c.setFont('Helvetica', 13)
    c.setFillColor(GREEN_LIGHT)
    c.drawCentredString(PAGE_W / 2, mid_y + 70, 'PROPUESTA COMERCIAL PARA')

    # Client name
    name = _safe(data, 'clientName', proposal.client_name)
    c.setFont('Helvetica-Bold', 40)
    c.setFillColor(ESMERALD)
    if len(name) > 28:
        lines = textwrap.wrap(name, width=28)
        ny = mid_y + 25
        for line in lines:
            c.drawCentredString(PAGE_W / 2, ny, line)
            ny -= 48
    else:
        c.drawCentredString(PAGE_W / 2, mid_y + 15, name)

    # Decorative line with green dot accents
    line_y = mid_y - 30
    c.setStrokeColor(GREEN_LIGHT)
    c.setLineWidth(2)
    c.line(PAGE_W / 2 - 80, line_y, PAGE_W / 2 + 80, line_y)
    c.setFillColor(GREEN_LIGHT)
    c.circle(PAGE_W / 2 - 80, line_y, 3, fill=1, stroke=0)
    c.circle(PAGE_W / 2 + 80, line_y, 3, fill=1, stroke=0)

    # Quote
    quote = _safe(data, 'inspirationalQuote')
    if quote:
        c.setFont('Helvetica-Oblique', 12)
        c.setFillColor(ESMERALD_80)
        q_lines = textwrap.wrap(f'"{_strip_emoji(quote)}"', width=72)
        qy = line_y - 30
        for ql in q_lines:
            c.drawCentredString(PAGE_W / 2, qy, ql)
            qy -= 17

    # Bottom branding
    c.setFont('Helvetica', 9)
    c.setFillColor(GRAY_500)
    c.drawCentredString(PAGE_W / 2, MARGIN_B, 'Project App  |  projectapp.co')


def _render_executive_summary(c, data, _proposal):
    """Render executive summary with paragraphs + sidebar highlights."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 10
    y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []))

    # Sidebar highlights
    highlights = _safe(data, 'highlights', [])
    hl_title = _safe(data, 'highlightsTitle', 'Aspectos Clave')
    if highlights:
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 48, hl_title, highlights)


def _render_context_diagnostic(c, data, _proposal):
    """Render context & diagnostic section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 10
    y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []))

    # Opportunity text
    opp_title = _safe(data, 'opportunityTitle')
    opp = _safe(data, 'opportunity')
    if opp:
        y -= 6
        y = _draw_subtitle(c, y, opp_title or 'Oportunidad')
        y = _draw_paragraphs(c, y, [opp])

    # Issues sidebar
    issues = _safe(data, 'issues', [])
    issues_title = _safe(data, 'issuesTitle', 'Problemáticas Identificadas')
    if issues:
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 48, issues_title, issues)


def _render_conversion_strategy(c, data, _proposal):
    """Render conversion strategy section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 10

    intro = _safe(data, 'intro')
    if intro:
        y = _draw_paragraphs(c, y, [intro])
        y -= 6

    steps = _safe(data, 'steps', [])
    for step in steps:
        if y < MARGIN_B + 60:
            break
        title = _safe(step, 'title')
        if title:
            y = _draw_subtitle(c, y, title)
        bullets = _safe(step, 'bullets', [])
        if bullets:
            y = _draw_bullet_list(c, y, bullets)
        y -= 4

    # Result
    result_title = _safe(data, 'resultTitle')
    result = _safe(data, 'result')
    if result:
        y -= 6
        if result_title:
            y = _draw_subtitle(c, y, result_title)
        y = _draw_paragraphs(c, y, [result])


def _render_design_ux(c, data, _proposal):
    """Render design & UX section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 10
    y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []))

    # Objective
    obj_title = _safe(data, 'objectiveTitle')
    obj = _safe(data, 'objective')
    if obj:
        y -= 6
        y = _draw_subtitle(c, y, obj_title or 'Objetivo')
        y = _draw_paragraphs(c, y, [obj])

    # Focus items sidebar
    focus_items = _safe(data, 'focusItems', [])
    focus_title = _safe(data, 'focusTitle', 'Enfoque')
    if focus_items:
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 48, focus_title, focus_items)


def _render_creative_support(c, data, _proposal):
    """Render creative support section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 10
    y = _draw_paragraphs(c, y, _safe(data, 'paragraphs', []))

    # Closing
    closing = _safe(data, 'closing')
    if closing:
        y -= 6
        y = _draw_paragraphs(c, y, [closing])

    # Includes sidebar
    includes = _safe(data, 'includes', [])
    inc_title = _safe(data, 'includesTitle', 'Incluye')
    if includes:
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 48, inc_title, includes)


def _render_development_stages(c, data, _proposal):
    """Render development stages as a vertical timeline."""
    y = PAGE_H - MARGIN_T
    index_str = _safe(data, 'index')
    title = _safe(data, 'title', 'Etapas de Desarrollo')
    y = _draw_section_header(c, y, index_str, title)
    y -= 10

    stages = _safe(data, 'stages', [])
    for i, stage in enumerate(stages):
        if y < MARGIN_B + 60:
            break
        stage_title = _safe(stage, 'title')
        desc = _safe(stage, 'description')
        is_current = _safe(stage, 'current', False)

        # Stage number circle
        circle_x = MARGIN_L + 16
        circle_y = y - 4
        if is_current:
            c.setFillColor(GREEN_LIGHT)
        else:
            c.setFillColor(ESMERALD)
        c.circle(circle_x, circle_y, 12, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 10)
        c.drawCentredString(circle_x, circle_y - 4, str(i + 1))

        # Connector line
        if i < len(stages) - 1:
            c.setStrokeColor(GRAY_200)
            c.setLineWidth(1)
            c.line(circle_x, circle_y - 14, circle_x, circle_y - 50)

        # Title + description
        tx = MARGIN_L + 40
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(ESMERALD if not is_current else GREEN_DARK)
        c.drawString(tx, y, _strip_emoji(stage_title))
        y -= 16

        if desc:
            c.setFont('Helvetica', 10)
            c.setFillColor(ESMERALD_80)
            d_lines = textwrap.wrap(_strip_emoji(str(desc)), width=80)
            for dl in d_lines:
                c.drawString(tx, y, dl)
                y -= 14
        y -= 14


def _render_functional_requirements(c, data, proposal):
    """Render functional requirements overview page."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 10

    intro = _safe(data, 'intro')
    if intro:
        y = _draw_paragraphs(c, y, [intro])
        y -= 6

    # Gather groups from content_json + DB requirement_groups
    groups = _safe(data, 'groups', [])
    additional = _safe(data, 'additionalModules', [])
    all_groups = list(groups) + list(additional)

    # Also include DB-level requirement groups
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

    # Draw overview cards (2-column grid)
    col_w = (CONTENT_W - 20) / 2
    chars = int(col_w / 5.8)
    for idx, grp in enumerate(all_groups):
        col = idx % 2
        row = idx // 2
        card_x = MARGIN_L + col * (col_w + 20)
        card_y = y - row * 70

        if card_y < MARGIN_B + 30:
            break

        # Card background
        c.setFillColor(GREEN_BG)
        c.roundRect(card_x, card_y - 50, col_w, 55, 6, fill=1, stroke=0)

        # Title
        c.setFont('Helvetica-Bold', 11)
        c.setFillColor(ESMERALD)
        c.drawString(card_x + 10, card_y - 12, _strip_emoji(_safe(grp, 'title')))

        # Description
        desc = _safe(grp, 'description')
        if desc:
            c.setFont('Helvetica', 9)
            c.setFillColor(ESMERALD_80)
            d_lines = textwrap.wrap(_strip_emoji(str(desc)), width=chars)
            dy = card_y - 28
            for dl in d_lines[:2]:
                c.drawString(card_x + 10, dy, dl)
                dy -= 12

    return all_groups


def _render_requirement_group_page(c, grp):
    """Render a single requirement group on its own page."""
    y = PAGE_H - MARGIN_T

    # Group title
    c.setFont('Helvetica', 22)
    c.setFillColor(ESMERALD)
    c.drawString(MARGIN_L, y, _strip_emoji(_safe(grp, 'title')))
    y -= 30

    # Group description
    desc = _safe(grp, 'description')
    if desc:
        y = _draw_paragraphs(c, y, [desc], font_size=11, leading=16)
        y -= 10

    # Items
    items = _safe(grp, 'items', [])
    for item in items:
        if y < MARGIN_B + 40:
            break
        name = _safe(item, 'name')
        item_desc = _safe(item, 'description')

        c.setFont('Helvetica-Bold', 11)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L + 4, y, f'>  {_strip_emoji(name)}')
        y -= 16

        if item_desc:
            c.setFont('Helvetica', 10)
            c.setFillColor(ESMERALD_80)
            i_lines = textwrap.wrap(_strip_emoji(str(item_desc)), width=90)
            for il in i_lines:
                if y < MARGIN_B + 20:
                    break
                c.drawString(MARGIN_L + 24, y, il)
                y -= 14
        y -= 6


def _render_timeline(c, data, _proposal):
    """Render timeline section with phases."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 10

    intro = _safe(data, 'introText')
    if intro:
        y = _draw_paragraphs(c, y, [intro])

    total = _safe(data, 'totalDuration')
    if total:
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, f'Duración Total: {total}')
        y -= 24

    phases = _safe(data, 'phases', [])
    for i, phase in enumerate(phases):
        if y < MARGIN_B + 60:
            break

        # Phase number circle
        cx = MARGIN_L + 14
        cy = y - 2
        c.setFillColor(GREEN_LIGHT)
        c.circle(cx, cy, 10, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(cx, cy - 3, str(i + 1))

        # Phase title + duration
        tx = MARGIN_L + 34
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(ESMERALD)
        c.drawString(tx, y, _strip_emoji(_safe(phase, 'title')))

        dur = _safe(phase, 'duration')
        if dur:
            c.setFont('Helvetica', 9)
            c.setFillColor(GRAY_500)
            c.drawString(tx + 250, y, _strip_emoji(dur))
        y -= 16

        # Description
        desc = _safe(phase, 'description')
        if desc:
            c.setFont('Helvetica', 10)
            c.setFillColor(ESMERALD_80)
            d_lines = textwrap.wrap(_strip_emoji(str(desc)), width=90)
            for dl in d_lines:
                c.drawString(tx, y, dl)
                y -= 13

        # Tasks as bullets
        tasks = _safe(phase, 'tasks', [])
        if tasks:
            y = _draw_bullet_list(
                c, y, tasks, x=tx, font_size=9, leading=12,
                max_width=CONTENT_W - 50,
            )

        # Milestone
        milestone = _safe(phase, 'milestone')
        if milestone:
            c.setFont('Helvetica-Bold', 9)
            c.setFillColor(GREEN_DARK)
            c.drawString(tx, y, f'Hito: {_strip_emoji(milestone)}')
            y -= 14

        y -= 8


def _render_investment(c, data, _proposal):
    """Render investment section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 10

    intro = _safe(data, 'introText')
    if intro:
        y = _draw_paragraphs(c, y, [intro])
        y -= 6

    # Total investment highlight box
    total = _safe(data, 'totalInvestment')
    currency = _safe(data, 'currency')
    if total:
        box_h = 60
        box_y = y - box_h
        c.setFillColor(GREEN_DARK)
        c.roundRect(MARGIN_L, box_y, TEXT_AREA_W, box_h, 10, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 28)
        c.setFillColor(WHITE)
        c.drawCentredString(MARGIN_L + TEXT_AREA_W / 2, box_y + 28, total)
        if currency:
            c.setFont('Helvetica', 11)
            c.drawCentredString(
                MARGIN_L + TEXT_AREA_W / 2, box_y + 10, currency,
            )
        y = box_y - 16

    # What's included
    included = _safe(data, 'whatsIncluded', [])
    if included:
        items_text = [
            f'{_strip_emoji(_safe(it, "title"))} — '
            f'{_strip_emoji(_safe(it, "description"))}'
            for it in included
        ]
        _draw_sidebar_box(
            c, PAGE_H - MARGIN_T - 48, 'Incluye', items_text,
        )

    # Payment options
    options = _safe(data, 'paymentOptions', [])
    if options:
        y -= 6
        y = _draw_subtitle(c, y, 'Formas de Pago')
        for opt in options:
            if y < MARGIN_B + 20:
                break
            label = _safe(opt, 'label')
            desc = _safe(opt, 'description')
            c.setFont('Helvetica', 10)
            c.setFillColor(ESMERALD_80)
            c.drawString(MARGIN_L + 10, y, f'•  {_strip_emoji(label)}')
            c.setFont('Helvetica-Bold', 10)
            c.drawRightString(MARGIN_L + TEXT_AREA_W, y, _strip_emoji(desc))
            y -= 16

    # Hosting plan
    hosting = _safe(data, 'hostingPlan', {})
    h_title = _safe(hosting, 'title')
    if h_title:
        y -= 10
        y = _draw_subtitle(c, y, h_title)
        h_desc = _safe(hosting, 'description')
        if h_desc:
            y = _draw_paragraphs(c, y, [h_desc], font_size=10, leading=14)

    # Value reasons
    reasons = _safe(data, 'valueReasons', [])
    if reasons:
        y -= 10
        y = _draw_subtitle(c, y, '¿Por Qué Esta Inversión Vale la Pena?')
        normalized = [
            r if isinstance(r, str) else _safe(r, 'description', _safe(r, 'title'))
            for r in reasons
        ]
        y = _draw_bullet_list(c, y, normalized, font_size=10)


def _render_final_note(c, data, _proposal):
    """Render final note section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 10

    message = _safe(data, 'message')
    if message:
        y = _draw_paragraphs(c, y, [message])

    personal = _safe(data, 'personalNote')
    if personal:
        y -= 4
        c.setFont('Helvetica-Oblique', 11)
        c.setFillColor(GRAY_500)
        p_lines = textwrap.wrap(_strip_emoji(str(personal)), width=80)
        for pl in p_lines:
            c.drawString(MARGIN_L, y, pl)
            y -= 15

    # Signature
    y -= 20
    c.setStrokeColor(GRAY_200)
    c.setLineWidth(0.5)
    c.line(MARGIN_L, y, MARGIN_L + 200, y)
    y -= 18
    team = _safe(data, 'teamName')
    role = _safe(data, 'teamRole')
    email = _safe(data, 'contactEmail')
    if team:
        c.setFont('Helvetica-Bold', 13)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, team)
        y -= 16
    if role:
        c.setFont('Helvetica', 10)
        c.setFillColor(GRAY_500)
        c.drawString(MARGIN_L, y, role)
        y -= 14
    if email:
        c.setFont('Helvetica', 10)
        c.setFillColor(GRAY_500)
        c.drawString(MARGIN_L, y, email)
        y -= 14

    # Commitment badges in sidebar
    badges = _safe(data, 'commitmentBadges', [])
    if badges:
        items = [
            f'{_strip_emoji(_safe(b, "title"))} — '
            f'{_strip_emoji(_safe(b, "description"))}'
            for b in badges
        ]
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 48, 'Compromisos', items)


def _render_next_steps(c, data, _proposal):
    """Render next steps section."""
    y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 10

    intro = _safe(data, 'introMessage')
    if intro:
        y = _draw_paragraphs(c, y, [intro])
        y -= 6

    # Steps
    steps = _safe(data, 'steps', [])
    for i, step in enumerate(steps):
        if y < MARGIN_B + 60:
            break
        step_title = _safe(step, 'title')
        step_desc = _safe(step, 'description')

        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, f'{i + 1}.  {step_title}')
        y -= 16

        if step_desc:
            c.setFont('Helvetica', 10)
            c.setFillColor(ESMERALD_80)
            s_lines = textwrap.wrap(str(step_desc), width=80)
            for sl in s_lines:
                c.drawString(MARGIN_L + 20, y, sl)
                y -= 14
        y -= 6

    # CTA message
    cta = _safe(data, 'ctaMessage')
    if cta:
        y -= 10
        c.setFont('Helvetica-Bold', 13)
        c.setFillColor(GREEN_DARK)
        cta_lines = textwrap.wrap(str(cta), width=70)
        for cl in cta_lines:
            c.drawString(MARGIN_L, y, cl)
            y -= 18

    # Contact methods sidebar
    contacts = _safe(data, 'contactMethods', [])
    if contacts:
        items = [
            f'{_strip_emoji(_safe(ct, "title"))}: '
            f'{_strip_emoji(_safe(ct, "value"))}'
            for ct in contacts
        ]
        _draw_sidebar_box(c, PAGE_H - MARGIN_T - 48, 'Contacto', items)


def _render_raw_text(c, data, _proposal):
    """Render a paste-mode section with raw text."""
    y = PAGE_H - MARGIN_T
    index_str = _safe(data, 'index')
    title = _safe(data, 'title', 'Sección')
    y = _draw_section_header(c, y, index_str, title)
    y -= 10

    raw = _safe(data, 'rawText')
    if raw:
        y = _draw_paragraphs(
            c, y, [raw], max_width=CONTENT_W, font_size=10, leading=14,
        )


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
        Build a multi-page landscape-A4 PDF from the proposal's
        enabled sections and return the raw bytes.

        Args:
            proposal: BusinessProposal instance with related sections.

        Returns:
            bytes: The PDF content, or None on failure.
        """
        try:
            sections = list(
                proposal.sections
                .filter(is_enabled=True)
                .order_by('order')
            )

            # Pre-calculate total pages (some sections add extra pages)
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
            c = canvas.Canvas(buf, pagesize=landscape(A4))
            c.setTitle(f'Propuesta — {proposal.client_name}')
            c.setAuthor('Project App')

            page_num = 0

            for sec in sections:
                stype = sec.section_type
                data = sec.content_json or {}

                # Use section model title as fallback
                if 'title' not in data or not data['title']:
                    data['title'] = sec.title

                renderer = SECTION_RENDERERS.get(stype)

                if renderer:
                    page_num += 1
                    _draw_green_bar(c)
                    result = renderer(c, data, proposal)
                    _draw_footer(
                        c, page_num, total_pages, proposal.client_name,
                    )
                    c.showPage()

                    # Functional requirements: add per-group detail pages
                    if stype == 'functional_requirements' and isinstance(
                        result, list
                    ):
                        for grp in result:
                            items = _safe(grp, 'items', [])
                            if not items:
                                continue
                            page_num += 1
                            _draw_green_bar(c)
                            _render_requirement_group_page(c, grp)
                            _draw_footer(
                                c, page_num, total_pages,
                                proposal.client_name,
                            )
                            c.showPage()
                elif data.get('rawText'):
                    # Paste-mode section
                    page_num += 1
                    _draw_green_bar(c)
                    _render_raw_text(c, data, proposal)
                    _draw_footer(
                        c, page_num, total_pages, proposal.client_name,
                    )
                    c.showPage()

            c.save()
            content_bytes = buf.getvalue()
            buf.close()

            # Merge: cover + content + back cover
            pdf_bytes = cls._merge_with_covers(content_bytes)

            logger.info(
                'Generated PDF for proposal %s (%d bytes, %d pages)',
                proposal.uuid, len(pdf_bytes), page_num,
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

        # 1. Cover page (Portada)
        if COVER_PDF.exists():
            try:
                cover_reader = PdfReader(str(COVER_PDF))
                for page in cover_reader.pages:
                    writer.add_page(page)
            except Exception:
                logger.warning('Could not read cover PDF: %s', COVER_PDF)

        # 2. Generated content
        content_reader = PdfReader(io.BytesIO(content_bytes))
        for page in content_reader.pages:
            writer.add_page(page)

        # 3. Back cover (Contraportada)
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
