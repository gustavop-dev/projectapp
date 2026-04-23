"""
Service for generating professional PDF business proposals
using ReportLab.

Each enabled section is rendered on portrait-A4 pages with the
Project App brand palette (esmerald / lemon / bone) and Ubuntu
typography.  Long sections flow across multiple pages automatically.

Shared PDF utilities (fonts, colours, drawing helpers) live in
``pdf_utils.py`` and are re-exported here for backward compatibility.
"""

import io
import logging
import math
import os
import re
import tempfile
import textwrap
from pathlib import Path

from django.conf import settings
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from content.services.proposal_service import normalize_hosting_plan
from content.services.pdf_utils import (  # noqa: F401 — re-exported
    _register_fonts,
    _font,
    # Brand colours
    ESMERALD,
    ESMERALD_DARK,
    ESMERALD_LIGHT,
    GREEN_LIGHT,
    LEMON,
    BONE,
    WINDOW_BLACK,
    GRAY_700,
    GRAY_500,
    GRAY_300,
    GRAY_200,
    WHITE,
    ESMERALD_80,
    # Cover paths
    COVER_PDF,
    BACK_COVER_PDF,
    # Page dimensions
    PAGE_W,
    PAGE_H,
    MARGIN_L,
    MARGIN_R,
    MARGIN_T,
    MARGIN_B,
    CONTENT_W,
    TEXT_AREA_W,
    SIDEBAR_X,
    SIDEBAR_W,
    # Text utilities
    _strip_emoji,
    _format_cop,
    _clean_url_display,
    _replace_urls_with_placeholders,
    _draw_line_with_links,
    _safe,
    # Pagination helpers
    _new_page,
    _check_y,
    # Drawing helpers
    _draw_header_bar,
    _draw_footer,
    _draw_section_header,
    _draw_paragraphs,
    _estimate_text_height,
    _draw_bullet_list,
    _sidebar_box_height,
    _draw_sidebar_box,
    _draw_subtitle,
    _draw_pill,
    _draw_banner_box,
    _apply_toc_links,
    _draw_toc_page,
    format_date_es,
    # Markdown helpers
    _parse_markdown_lines,
    _clean_inline_bold,
)

logger = logging.getLogger(__name__)


def _filter_calculator_groups(groups, sel_ids):
    """Filter out calculator-module groups that were not selected.

    Non-calculator groups always pass through. Calculator modules
    (``is_calculator_module=True``) are only kept when their ID appears
    in *sel_ids*.  When *sel_ids* is ``None`` (no selection provided),
    **all** calculator modules are excluded.
    """
    return [
        g for g in groups
        if not _safe(g, 'is_calculator_module')
        or (sel_ids is not None and f"module-{_safe(g, 'id')}" in sel_ids)
    ]


def default_selected_modules_from_content(proposal):
    """Resolve default selected module IDs for a PDF render.

    Priority:
    1. ``BusinessProposal.selected_modules`` when non-empty — this mirrors
       what the frontend does at ``pages/proposal/[uuid]/index.vue``
       (``effectiveSelectedModuleIdsForTechnical``) and covers both client
       confirmations via the calculator modal and admin-driven edits to
       that field. Legacy payloads may store bare group ids, so we run
       them through the shared normalizer to restore the canonical
       ``module-<id>`` / ``group-<id>`` form the renderer expects.
    2. Derive from the current ``content_json``
       (``additionalModules[*].selected`` + ``default_selected``) so admin
       toggles in the editor still propagate to the PDF when the DB field
       is empty.

    Returns a list of module IDs ready to be passed as ``selected_modules``
    to :meth:`ProposalPdfService.generate`.
    """
    from content.services.proposal_service import normalize_selected_module_ids

    sections = list(proposal.sections.all())
    fr = next(
        (s for s in sections if s.section_type == 'functional_requirements'),
        None,
    )
    fr_content = fr.content_json if fr else None

    persisted = getattr(proposal, 'selected_modules', None)
    if persisted:
        return normalize_selected_module_ids(persisted, fr_content)

    selected = []

    inv = next((s for s in sections if s.section_type == 'investment'), None)
    if inv and inv.content_json:
        for mod in inv.content_json.get('modules') or []:
            mid = mod.get('id') if isinstance(mod, dict) else None
            if mid:
                selected.append(mid)

    if fr_content:
        groups = list(fr_content.get('groups') or []) + list(fr_content.get('additionalModules') or [])
        for grp in groups:
            if not isinstance(grp, dict):
                continue
            if grp.get('is_visible') is False:
                continue
            is_calc = grp.get('is_calculator_module') is True
            default_sel = grp.get('selected')
            if default_sel is None:
                default_sel = grp.get('default_selected')
            if default_sel is None:
                default_sel = not is_calc
            if not default_sel:
                continue
            gid = grp.get('id')
            if not gid:
                continue
            selected.append(f'module-{gid}' if is_calc else f'group-{gid}')

    return selected


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
        sb_h = _sidebar_box_height(highlights)
        text_h = _estimate_text_height(paragraphs, TEXT_AREA_W)
        need = max(sb_h, text_h) + 20
        has_room = (content_top - MARGIN_B) > need
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
        sb_h = _sidebar_box_height(issues)
        paragraphs = _safe(data, 'paragraphs', [])
        para_h = _estimate_text_height(paragraphs, TEXT_AREA_W)
        opp = _safe(data, 'opportunity')
        opp_title = _safe(data, 'opportunityTitle')
        full_left_h = para_h
        if opp:
            full_left_h += 30 + _estimate_text_height([opp], TEXT_AREA_W)
        avail = content_top - MARGIN_B

        # Tier 1: full two-column (paragraphs + opportunity alongside sidebar)
        full_need = max(sb_h, full_left_h) + 20
        # Tier 2: partial two-column (paragraphs alongside sidebar,
        #         opportunity rendered below at full width)
        partial_need = max(sb_h, para_h) + 20

        if avail > full_need:
            text_w = TEXT_AREA_W
            y = _draw_paragraphs(c, y, paragraphs, max_width=text_w, ps=ps)
            if opp:
                y -= 6
                y = _draw_subtitle(c, y, opp_title or 'La oportunidad', ps=ps)
                y = _draw_paragraphs(c, y, [opp], max_width=text_w, ps=ps)
            sb = _draw_sidebar_box(c, content_top, issues_title, issues)
            y = min(y, sb - 8)
        elif avail > partial_need:
            text_w = TEXT_AREA_W
            y = _draw_paragraphs(c, y, paragraphs, max_width=text_w, ps=ps)
            sb = _draw_sidebar_box(c, content_top, issues_title, issues)
            y = min(y, sb - 8)
            if opp:
                y -= 6
                y = _draw_subtitle(c, y, opp_title or 'La oportunidad', ps=ps)
                y = _draw_paragraphs(c, y, [opp], ps=ps)
        else:
            # Tier 3: linear fallback — everything full-width
            y = _draw_paragraphs(c, y, paragraphs, ps=ps)
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

    # Render paragraphs + objective first (full width or left column)
    paragraphs = _safe(data, 'paragraphs', [])
    obj_title = _safe(data, 'objectiveTitle')
    obj = _safe(data, 'objective')

    if focus_items:
        # Always render inline (full-width) to avoid whitespace gaps
        y = _draw_paragraphs(c, y, paragraphs, ps=ps)
        if obj:
            y -= 6
            y = _draw_subtitle(c, y, obj_title or 'Objetivo', ps=ps)
            y = _draw_paragraphs(c, y, [obj], ps=ps)
        y -= 10
        # Focus items as a full-width branded box below paragraphs
        if ps:
            y = _check_y(c, y, ps, need=60)
        y = _draw_subtitle(c, y, focus_title, ps=ps)
        y = _draw_bullet_list(c, y, focus_items, ps=ps)
    else:
        y = _draw_paragraphs(c, y, paragraphs, ps=ps)
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
        sb_h = _sidebar_box_height(includes)
        paragraphs = _safe(data, 'paragraphs', [])
        para_h = _estimate_text_height(paragraphs, TEXT_AREA_W)
        closing = _safe(data, 'closing')
        full_left_h = para_h
        if closing:
            full_left_h += _estimate_text_height([closing], TEXT_AREA_W)
        avail = content_top - MARGIN_B

        # Tier 1: full two-column (paragraphs + closing alongside sidebar)
        full_need = max(sb_h, full_left_h) + 20
        # Tier 2: partial two-column (paragraphs alongside sidebar,
        #         closing rendered below at full width)
        partial_need = max(sb_h, para_h) + 20

        if avail > full_need:
            y = _draw_paragraphs(c, y, paragraphs,
                                 max_width=TEXT_AREA_W, ps=ps)
            if closing:
                y -= 6
                y = _draw_paragraphs(c, y, [closing], max_width=TEXT_AREA_W,
                                     ps=ps)
            sb = _draw_sidebar_box(c, content_top, inc_title, includes)
            y = min(y, sb - 8)
        elif avail > partial_need:
            y = _draw_paragraphs(c, y, paragraphs,
                                 max_width=TEXT_AREA_W, ps=ps)
            sb = _draw_sidebar_box(c, content_top, inc_title, includes)
            y = min(y, sb - 8)
            if closing:
                y -= 6
                y = _draw_paragraphs(c, y, [closing], ps=ps)
        else:
            # Tier 3: linear fallback — everything full-width
            y = _draw_paragraphs(c, y, paragraphs, ps=ps)
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
    all_groups = [g for g in list(groups) + list(additional) if _safe(g, 'is_visible', True) is not False]

    # Hide groups rendered in the dedicated value-added section.
    hidden_ids = ps.get('_value_added_ids', set()) if ps else set()
    if hidden_ids:
        all_groups = [g for g in all_groups if _safe(g, 'id') not in hidden_ids]

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

    # Filter out calculator-module groups not selected
    sel_ids = ps.get('selected_modules') if ps else None
    all_groups = _filter_calculator_groups(all_groups, sel_ids)

    # Overview cards (2-column grid) — paginated with dynamic height
    col_w = (CONTENT_W - 16) / 2
    inner_w = col_w - 20  # 10pt padding each side
    title_chars = int(inner_w / 6.0)  # bold 10pt ≈ 6pt per char
    desc_chars = int(inner_w / 5.0)   # regular 8pt ≈ 5pt per char
    row_y = y
    idx = 0
    while idx < len(all_groups):
        # Pre-compute card data and heights for this row (up to 2 cards)
        row_cards = []
        for col in range(2):
            ci = idx + col
            if ci >= len(all_groups):
                break
            grp = all_groups[ci]
            grp_title = _strip_emoji(_safe(grp, 'title'))
            t_lines = textwrap.wrap(grp_title, width=title_chars) or [grp_title]
            t_lines = t_lines[:2]  # max 2 title lines
            desc = _safe(grp, 'description')
            d_lines = textwrap.wrap(_strip_emoji(str(desc)), width=desc_chars)[:2] if desc else []
            # Filter items (same logic as before)
            grp_items = _safe(grp, 'items', [])
            if sel_ids is not None and grp_items:
                grp_key = (_safe(grp, 'id') or _safe(grp, 'title') or '')
                kept = []
                for it in grp_items:
                    is_req = _safe(it, 'is_required')
                    if is_req is True:
                        kept.append(it)
                    else:
                        configurable = _safe(it, 'price') or is_req is False
                        if not configurable:
                            kept.append(it)
                        else:
                            fr_id = re.sub(r'\s+', '-', f'fr-{grp_key}-{_safe(it, "name") or ""}').lower()
                            if fr_id in sel_ids:
                                kept.append(it)
                grp_items = kept
            # Card height: top pad + title lines + gap + desc lines + bottom pad
            ch = 10 + (len(t_lines) * 13) + 4 + (len(d_lines) * 11) + 6
            ch = max(ch, 44)  # minimum height
            row_cards.append({
                'grp': grp, 'title_lines': t_lines, 'desc_lines': d_lines,
                'items': grp_items, 'height': ch,
            })

        if not row_cards:
            break

        row_h = max(rc['height'] for rc in row_cards)

        # Page break check
        if ps:
            row_y = _check_y(c, row_y, ps, need=row_h + 10)
        elif row_y < MARGIN_B + row_h + 10:
            break

        # Draw cards in this row
        for col, rc in enumerate(row_cards):
            card_x = MARGIN_L + col * (col_w + 16)
            card_y = row_y

            c.setFillColor(ESMERALD_LIGHT)
            c.roundRect(card_x, card_y - row_h + 6, col_w, row_h, 5, fill=1, stroke=0)
            # Left accent bar
            c.setFillColor(LEMON)
            c.roundRect(card_x, card_y - row_h + 6, 3, row_h, 1, fill=1, stroke=0)

            # Title (wrapped)
            c.setFont(_font('bold'), 10)
            c.setFillColor(ESMERALD)
            for ti, tl in enumerate(rc['title_lines']):
                c.drawString(card_x + 10, card_y - 10 - (ti * 13), tl)

            # Item count pill (after last title line)
            if rc['items']:
                last_ti = len(rc['title_lines']) - 1
                last_line = rc['title_lines'][last_ti]
                tw = c.stringWidth(last_line, _font('bold'), 10)
                pill_y = card_y - 10 - (last_ti * 13)
                _draw_pill(c, card_x + 10 + tw + 6, pill_y,
                           str(len(rc['items'])),
                           bg_color=BONE, text_color=ESMERALD, font_size=6,
                           padding_h=5, padding_v=2)

            # Description
            if rc['desc_lines']:
                c.setFont(_font('regular'), 8)
                c.setFillColor(ESMERALD_80)
                desc_y = card_y - 10 - (len(rc['title_lines']) * 13) - 4
                for dl in rc['desc_lines']:
                    c.drawString(card_x + 10, desc_y, dl)
                    desc_y -= 11

        idx += len(row_cards)
        row_y -= (row_h + 12)

    # Store groups for generate() to render detail sub-sections
    if ps is not None:
        ps['_func_req_groups'] = all_groups

    return row_y - 8


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

    # Render items as a full-width table — one row per requirement
    if not items:
        return y

    # Table column widths
    num_col_w = 28
    name_col_w = int((CONTENT_W - num_col_w) * 0.36)
    desc_col_w = CONTENT_W - num_col_w - name_col_w

    # Approximate chars that fit per column
    name_chars = int(name_col_w / 5.0) - 1
    desc_chars = int(desc_col_w / 4.5) - 1

    row_y = y

    # ── Table header ──────────────────────────────────────────
    hdr_h = 22
    if ps:
        row_y = _check_y(c, row_y, ps, need=hdr_h + 32)
    hdr_bottom = row_y - hdr_h
    c.setFillColor(ESMERALD_DARK)
    c.rect(MARGIN_L, hdr_bottom, CONTENT_W, hdr_h, fill=1, stroke=0)
    # Offset +2 aligns the optical midline of the glyphs with the rect's
    # vertical center (without it, the text sits low because the descender
    # makes the geometric baseline fall below the cap-height midpoint).
    hdr_text_y = hdr_bottom + (hdr_h - 8) / 2 + 2
    c.setFont(_font('bold'), 8)
    c.setFillColor(WHITE)
    c.drawCentredString(MARGIN_L + num_col_w / 2, hdr_text_y, '#')
    c.drawString(MARGIN_L + num_col_w + 6, hdr_text_y, 'Requerimiento')
    c.drawString(MARGIN_L + num_col_w + name_col_w + 6, hdr_text_y, 'Descripción')
    row_y = hdr_bottom

    # ── Item rows ─────────────────────────────────────────────
    for idx, item in enumerate(items):
        name = _strip_emoji(_safe(item, 'name') or '')
        item_desc = _strip_emoji(_safe(item, 'description') or '')
        name_lines = textwrap.wrap(name, width=name_chars) or [name]
        desc_lines = textwrap.wrap(item_desc, width=desc_chars) if item_desc else []

        line_h = 11
        n_lines = max(len(name_lines), len(desc_lines) if desc_lines else 1)
        row_h = n_lines * line_h + 14
        row_h = max(row_h, 28)

        # Page break check
        if ps:
            row_y = _check_y(c, row_y, ps, need=row_h)

        row_bottom = row_y - row_h

        # Row background (alternating)
        c.setFillColor(ESMERALD_LIGHT if idx % 2 == 0 else WHITE)
        c.rect(MARGIN_L, row_bottom, CONTENT_W, row_h, fill=1, stroke=0)

        # LEMON left accent bar
        c.setFillColor(LEMON)
        c.rect(MARGIN_L, row_bottom, 3, row_h, fill=1, stroke=0)

        # Row number (vertically centred)
        c.setFont(_font('bold'), 8)
        c.setFillColor(ESMERALD_80)
        c.drawCentredString(
            MARGIN_L + num_col_w / 2,
            row_bottom + (row_h - 8) / 2,
            str(idx + 1).zfill(2),
        )

        # Item name (top-aligned, bold)
        text_y = row_y - 9
        c.setFont(_font('bold'), 9)
        c.setFillColor(ESMERALD)
        for nl in name_lines:
            c.drawString(MARGIN_L + num_col_w + 6, text_y, nl)
            text_y -= line_h

        # Item description (top-aligned, regular)
        if desc_lines:
            text_y = row_y - 9
            c.setFont(_font('regular'), 8)
            c.setFillColor(ESMERALD_80)
            for dl in desc_lines:
                c.drawString(MARGIN_L + num_col_w + name_col_w + 6, text_y, dl)
                text_y -= line_h

        row_y = row_bottom

    return row_y - 4


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
        # Duration badge — width adapts to content, capped at CONTENT_W
        total_str = _strip_emoji(total)
        label_str = 'Duración Total Estimada'
        value_w = c.stringWidth(total_str, _font('bold'), 11)
        label_w = c.stringWidth(label_str, _font('regular'), 8)
        badge_w = min(CONTENT_W, max(200, math.ceil(max(value_w, label_w)) + 40))
        badge_h = 36

        # Truncate value text if it would overflow badge's inner width
        inner_w = badge_w - 24  # 12px left padding + 12px right guard
        if value_w > inner_w:
            stripped = total_str.rstrip()
            lo, hi = 0, len(stripped)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if c.stringWidth(stripped[:mid] + '...', _font('bold'), 11) <= inner_w:
                    lo = mid
                else:
                    hi = mid - 1
            total_str = stripped[:lo] + '...'
        # Truncate label too if it overflows
        if label_w > inner_w:
            lbl_stripped = label_str.rstrip()
            lo, hi = 0, len(lbl_stripped)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if c.stringWidth(lbl_stripped[:mid] + '...', _font('regular'), 8) <= inner_w:
                    lo = mid
                else:
                    hi = mid - 1
            label_str = lbl_stripped[:lo] + '...'

        c.setFillColor(BONE)
        c.roundRect(MARGIN_L, y - badge_h + 4, badge_w, badge_h,
                    4, fill=1, stroke=0)
        c.setFont(_font('regular'), 8)
        c.setFillColor(GRAY_500)
        c.drawString(MARGIN_L + 12, y - 8, label_str)
        c.setFont(_font('bold'), 11)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L + 12, y - 23, total_str)
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
    # BusinessProposal fields are the source of truth; content_json is the
    # stale mirror (matches frontend override in pages/proposal/[uuid]/index.vue).
    _model_total = getattr(_proposal, 'total_investment', None)
    total = (_format_cop(int(_model_total))
             if _model_total else _safe(data, 'totalInvestment'))
    currency = (getattr(_proposal, 'currency', None)
                or _safe(data, 'currency'))
    options = _safe(data, 'paymentOptions', [])

    # ── Pre-calculate adjusted total (needed for payment options too) ──
    selected_ids = ps.get('selected_modules') if ps else None
    adjusted = None
    base_num = int(re.sub(r'[^\d]', '', str(total)) or '0') if total else 0
    display_total = total or ''
    if total and selected_ids is not None:
        all_mods = _safe(data, 'modules', [])
        fr_items = ps.get('_fr_items', []) if ps else []
        calc_items = ps.get('_calc_module_items', []) if ps else []
        deselected_sum = sum(
            _safe(m, 'price', 0) for m in all_mods
            if _safe(m, 'id') not in selected_ids
        ) + sum(
            it.get('price', 0) for it in fr_items
            if it.get('id') not in selected_ids
        )
        added_sum = sum(
            it.get('price', 0) for it in calc_items
            if it.get('id') in selected_ids and it.get('price')
        )
        adjusted = base_num - deselected_sum + added_sum
        display_total = _format_cop(adjusted)

    # Intro text — full width, brief
    if intro:
        y = _draw_paragraphs(c, y, [intro], ps=ps)
        y -= 10

    # ── Layout: Formas de Pago + Incluye ──
    col_gap = 20
    left_w = CONTENT_W * 0.58
    right_w = CONTENT_W - left_w - col_gap
    right_x = MARGIN_L + left_w + col_gap

    # Pre-calculate heights to decide two-column vs linear layout
    left_need = 20 + len(options) * 22 if options else 0
    items_text = []
    if included:
        items_text = [
            f'{_strip_emoji(_safe(it, "title"))} \u2014 '
            f'{_strip_emoji(_safe(it, "description"))}'
            for it in included
        ]
    right_need = _sidebar_box_height(items_text, sidebar_w=right_w) if items_text else 0
    total_need = max(left_need, right_need)
    use_two_col = (y - MARGIN_B) > total_need + 30

    if use_two_col:
        # ── Two-column layout ──
        columns_top = y

        # LEFT COLUMN: Formas de Pago
        left_y = columns_top
        if options:
            c.setFont(_font('bold'), 12)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, left_y, 'Formas de Pago')
            left_y -= 20

            for opt in options:
                label = _strip_emoji(_safe(opt, 'label'))
                desc = _strip_emoji(_safe(opt, 'description'))

                c.setFillColor(ESMERALD_LIGHT)
                c.roundRect(MARGIN_L, left_y - 6, left_w, 18, 4,
                            fill=1, stroke=0)
                c.setFont(_font('regular'), 8)
                c.setFillColor(ESMERALD_80)
                c.drawString(MARGIN_L + 8, left_y - 2, label)
                pill_desc = desc
                if adjusted is not None and base_num > 0 and desc:
                    desc_num = int(re.sub(r'[^\d]', '', str(desc)) or '0')
                    if desc_num > 0:
                        ratio = adjusted / base_num
                        new_amount = round(desc_num * ratio)
                        pill_desc = re.sub(
                            r'[\$]?[\d.,]+',
                            _format_cop(new_amount).lstrip('$'),
                            _strip_emoji(desc),
                            count=1,
                        )
                        if not pill_desc.startswith('$'):
                            pill_desc = '$' + pill_desc
                if pill_desc:
                    _draw_pill(c, MARGIN_L + left_w - 80, left_y - 2, pill_desc,
                               bg_color=ESMERALD, text_color=WHITE, font_size=7)
                left_y -= 22

        # RIGHT COLUMN: Incluye
        right_bottom = columns_top
        if items_text:
            right_bottom = _draw_sidebar_box(c, columns_top, 'Incluye', items_text,
                                              sidebar_x=right_x, sidebar_w=right_w)

        y = min(left_y, right_bottom) - 12
    else:
        # ── Linear layout (paginated) ──
        if options:
            if ps:
                y = _check_y(c, y, ps, need=40)
            c.setFont(_font('bold'), 12)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, 'Formas de Pago')
            y -= 20

            for opt in options:
                if ps:
                    y = _check_y(c, y, ps, need=24)
                label = _strip_emoji(_safe(opt, 'label'))
                desc = _strip_emoji(_safe(opt, 'description'))

                c.setFillColor(ESMERALD_LIGHT)
                c.roundRect(MARGIN_L, y - 6, CONTENT_W, 18, 4,
                            fill=1, stroke=0)
                c.setFont(_font('regular'), 8)
                c.setFillColor(ESMERALD_80)
                c.drawString(MARGIN_L + 8, y - 2, label)
                pill_desc = desc
                if adjusted is not None and base_num > 0 and desc:
                    desc_num = int(re.sub(r'[^\d]', '', str(desc)) or '0')
                    if desc_num > 0:
                        ratio = adjusted / base_num
                        new_amount = round(desc_num * ratio)
                        pill_desc = re.sub(
                            r'[\$]?[\d.,]+',
                            _format_cop(new_amount).lstrip('$'),
                            _strip_emoji(desc),
                            count=1,
                        )
                        if not pill_desc.startswith('$'):
                            pill_desc = '$' + pill_desc
                if pill_desc:
                    _draw_pill(c, MARGIN_L + CONTENT_W - 80, y - 2, pill_desc,
                               bg_color=ESMERALD, text_color=WHITE, font_size=7)
                y -= 22

        if items_text:
            y -= 10
            if ps:
                y = _check_y(c, y, ps, need=right_need + 10)
            y = _draw_sidebar_box(c, y, 'Incluye', items_text,
                                   sidebar_x=MARGIN_L, sidebar_w=CONTENT_W)
            y -= 8

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
        label = f'Inversi\u00f3n Total: {display_total}'
        if currency:
            label = f'{label}  {currency}'
        c.drawCentredString(MARGIN_L + box_w / 2, box_y + 7, label)
        y = box_y - 8

    # ── Adjusted duration (when modules are deselected) ─────────
    if selected_ids is not None and ps:
        base_weeks = ps.get('base_weeks', 0)
        if base_weeks > 0:
            all_mods = _safe(data, 'modules', [])
            fr_items = ps.get('_fr_items', []) if ps else []
            deselected = [
                m for m in all_mods
                if _safe(m, 'id') not in selected_ids
            ] + [
                it for it in fr_items
                if it.get('id') not in selected_ids
            ]
            reduction = 0
            views_removed = 0
            features_removed = 0
            for m in deselected:
                src = _safe(m, '_source') or m.get('_source', '')
                gid = _safe(m, 'groupId') or m.get('groupId', '')
                if src == 'investment' or gid.startswith('integration_'):
                    reduction += 1
                elif gid == 'views':
                    views_removed += 1
                elif gid == 'features':
                    features_removed += 1
            reduction += views_removed // 3
            reduction += features_removed // 3
            adjusted_weeks = max(1, base_weeks - reduction)
            if adjusted_weeks != base_weeks:
                if ps:
                    y = _check_y(c, y, ps, need=20)
                c.setFont(_font('regular'), 9)
                c.setFillColor(GRAY_500)
                duration_text = (
                    f'Duraci\u00f3n estimada: {adjusted_weeks} semanas'
                    f' (reducido de {base_weeks})'
                )
                c.drawCentredString(
                    MARGIN_L + CONTENT_W / 2, y, duration_text
                )
                y -= 16

    # ── AI scope note (when AI module selected) ───────────────────
    if ps:
        calc_items = ps.get('_calc_module_items', [])
        sel_check = ps.get('selected_modules')
        for ci in calc_items:
            if ci.get('is_invite') and (
                sel_check is None or ci.get('id') in sel_check
            ):
                y = _check_y(c, y, ps, need=30)
                lang = (_proposal.language or 'es') if _proposal else 'es'
                ai_note = (
                    'Nota: El alcance y costos del módulo de IA se definirán '
                    'en una llamada personalizada. Este módulo no tiene costo '
                    'adicional asignado hasta acordar el alcance.'
                ) if lang == 'es' else (
                    'Note: The scope and costs of the AI module will be defined '
                    'in a personalized call. This module has no additional cost '
                    'assigned until the scope is agreed upon.'
                )
                c.setFont(_font('regular'), 8)
                c.setFillColor(GRAY_500)
                note_lines = textwrap.wrap(ai_note, width=90)
                for nl in note_lines:
                    c.drawString(MARGIN_L, y, nl)
                    y -= 11
                y -= 4
                break

    # ── Interactive Modules (if present) ──────────────────────────
    modules = _safe(data, 'modules', [])
    selected_ids = ps.get('selected_modules') if ps else None
    # Only show selected modules (or all if no filter)
    visible_modules = [
        mod for mod in modules
        if selected_ids is None or _safe(mod, 'id') in (selected_ids or [])
    ]
    if visible_modules:
        y -= 14
        if ps:
            y = _check_y(c, y, ps, need=60)
        c.setFont(_font('bold'), 12)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, 'Módulos del Proyecto')
        y -= 18
        for mod in visible_modules:
            mod_name = _strip_emoji(_safe(mod, 'name'))
            mod_price = _safe(mod, 'price', 0)
            if ps:
                y = _check_y(c, y, ps, need=20)
            c.setFillColor(ESMERALD_LIGHT)
            c.roundRect(MARGIN_L, y - 6, CONTENT_W, 18, 4, fill=1, stroke=0)
            c.setFont(_font('regular'), 8)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L + 8, y - 2, f'✓  {mod_name}')
            if mod_price:
                price_str = _format_cop(mod_price)
                c.setFont(_font('bold'), 8)
                c.drawRightString(MARGIN_L + CONTENT_W - 8, y - 2, price_str)
            y -= 22

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

        # Specs grid — 2 columns of pill-style badges (2-line: label + value)
        specs = [s for s in _safe(hosting, 'specs', [])
                 if _safe(s, 'label') or _safe(s, 'value')]
        if specs:
            spec_col_w = (CONTENT_W - 14) / 2
            spec_row_h = 38
            for si, spec in enumerate(specs):
                col = si % 2
                if col == 0 and ps:
                    y = _check_y(c, y, ps, need=spec_row_h + 4)
                sx = MARGIN_L + col * (spec_col_w + 14)
                # Badge background
                c.setFillColor(ESMERALD_LIGHT)
                c.roundRect(sx, y - 18, spec_col_w, spec_row_h, 5,
                            fill=1, stroke=0)
                # Label (bold) — top line
                spec_label = _strip_emoji(_safe(spec, 'label'))
                label_y = y - 18 + spec_row_h - 12
                c.setFont(_font('bold'), 8)
                c.setFillColor(ESMERALD)
                c.drawString(sx + 8, label_y, spec_label)
                # Value (regular) — second line below label
                spec_value = _strip_emoji(_safe(spec, 'value'))
                value_y = label_y - 13
                c.setFont(_font('regular'), 7.5)
                c.setFillColor(ESMERALD_80)
                c.drawString(sx + 8, value_y, spec_value)
                # Move down after every 2nd column
                if col == 1 or si == len(specs) - 1:
                    y -= spec_row_h + 4
            y -= 2

        # Billing tiers — 3 frequency options side by side.
        normalized_hosting = normalize_hosting_plan(_proposal, hosting)
        h_percent = normalized_hosting.get('hostingPercent', 0) or 0
        billing_tiers = normalized_hosting.get('billingTiers', [])
        # Hosting is a percentage of the SAME "Inversión Total" the client
        # sees above — the effective total (base + admin-pre-selected
        # additional modules, or the client's adjusted selection). Keeps
        # parity with the public frontend (Investment.vue
        # ``hostingAnnualAmount``) and the admin preview in the General tab.
        basis = adjusted if adjusted is not None else base_num
        annual_hosting = round(basis * h_percent / 100) if h_percent and basis else 0

        if billing_tiers and annual_hosting > 0:
            if ps:
                y = _check_y(c, y, ps, need=56)
            num_tiers = len(billing_tiers)
            tier_gap = 10
            tier_col_w = (CONTENT_W - tier_gap * (num_tiers - 1)) / num_tiers
            tier_h = 48
            tier_y = y - tier_h + 6

            monthly_base = round(annual_hosting / 12)

            for ti, tier in enumerate(billing_tiers):
                tx = MARGIN_L + ti * (tier_col_w + tier_gap)
                discount = _safe(tier, 'discountPercent', 0)
                months = _safe(tier, 'months', 1) or 1
                label = _strip_emoji(_safe(tier, 'label', ''))
                badge = _strip_emoji(_safe(tier, 'badge', ''))
                monthly_discounted = round(monthly_base * (100 - discount) / 100)
                period_total = monthly_discounted * months

                # First tier (best price) gets esmerald bg
                if ti == 0:
                    c.setFillColor(ESMERALD)
                    c.roundRect(tx, tier_y, tier_col_w, tier_h, 5,
                                fill=1, stroke=0)
                    label_color = colors.HexColor('#A7F3D0')
                    price_color = WHITE
                    sub_color = colors.HexColor('#A7F3D0')
                else:
                    c.setFillColor(ESMERALD_LIGHT)
                    c.roundRect(tx, tier_y, tier_col_w, tier_h, 5,
                                fill=1, stroke=0)
                    label_color = GREEN_LIGHT
                    price_color = ESMERALD
                    sub_color = ESMERALD_80

                # Badge (top-right corner)
                if badge:
                    c.setFont(_font('medium'), 6)
                    badge_w = c.stringWidth(badge, _font('medium'), 6) + 8
                    badge_x = tx + tier_col_w - badge_w - 4
                    badge_y = tier_y + tier_h - 12
                    c.setFillColor(LEMON)
                    c.roundRect(badge_x, badge_y, badge_w, 10, 3,
                                fill=1, stroke=0)
                    c.setFont(_font('medium'), 6)
                    c.setFillColor(ESMERALD)
                    c.drawString(badge_x + 4, badge_y + 2, badge)

                # Label
                c.setFont(_font('medium'), 7)
                c.setFillColor(label_color)
                c.drawString(tx + 10, tier_y + tier_h - 12, label)

                # Price per month
                c.setFont(_font('bold'), 11)
                c.setFillColor(price_color)
                price_str = _format_cop(monthly_discounted) + ' /mes'
                c.drawString(tx + 10, tier_y + tier_h - 26, price_str)

                # Period total
                c.setFont(_font('regular'), 7)
                c.setFillColor(sub_color)
                sub_str = f'{_format_cop(period_total)} cada {months} mes{"es" if months > 1 else ""}'
                c.drawString(tx + 10, tier_y + 5, sub_str)

            y = tier_y - 6
        else:
            # Legacy fallback: monthlyPrice / annualPrice
            m_price = _safe(hosting, 'monthlyPrice')
            a_price = _safe(hosting, 'annualPrice')
            if m_price or a_price:
                if ps:
                    y = _check_y(c, y, ps, need=40)
                price_col_w = (CONTENT_W - 14) / 2
                price_h = 34
                price_y = y - price_h + 6
                p_label_y = price_y + price_h - 11
                p_price_y = price_y + 5
                if m_price:
                    c.setFillColor(ESMERALD)
                    c.roundRect(MARGIN_L, price_y, price_col_w, price_h, 5,
                                fill=1, stroke=0)
                    c.setFont(_font('medium'), 7)
                    c.setFillColor(colors.HexColor('#A7F3D0'))
                    c.drawString(MARGIN_L + 10, p_label_y,
                                 _strip_emoji(_safe(hosting, 'monthlyLabel', 'por mes')))
                    c.setFont(_font('bold'), 11)
                    c.setFillColor(WHITE)
                    c.drawString(MARGIN_L + 10, p_price_y,
                                 _strip_emoji(str(m_price)))
                if a_price:
                    ax = MARGIN_L + price_col_w + 14
                    c.setFillColor(BONE)
                    c.roundRect(ax, price_y, price_col_w, price_h, 5,
                                fill=1, stroke=0)
                    c.setFont(_font('medium'), 7)
                    c.setFillColor(GRAY_500)
                    c.drawString(ax + 10, p_label_y,
                                 _strip_emoji(_safe(hosting, 'annualLabel', 'pago anual')))
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
            text_block_h = len(cov_lines) * 12
            ty = box_y + box_h - (box_h - text_block_h) / 2 - 10
            for cl in cov_lines:
                c.drawString(MARGIN_L + 10, ty, cl)
                ty -= 12
            y = box_y - 6

        # Renewal note — SMLMV formula text
        renewal = _safe(hosting, 'renewalNote')
        if renewal:
            # Normalise legacy 5% formula to current 6%
            renewal = str(renewal).replace('5%', '6%').replace(
                '$65,000', '$78.000').replace(
                '$65.000', '$78.000').replace(
                '$745,000', '$758.000').replace(
                '$745.000', '$758.000')
        if not renewal and h_title:
            renewal = (
                'Renovaciones a partir del segundo año: el costo se ajusta anualmente '
                'con base en el SMLMV (Salario Mínimo Legal Mensual Vigente) del año '
                'de renovación, aplicando la siguiente fórmula:\n\n'
                'Costo de renovación = Costo del año anterior + '
                '(6% \u00d7 SMLMV del año de renovación)\n\n'
                'Por ejemplo, si el SMLMV del año de renovación fuera $1.300.000 COP, '
                'el incremento sería de $78.000 COP, llevando el costo a $758.000 COP '
                'para ese año.'
            )
        if renewal:
            y -= 6
            if ps:
                y = _check_y(c, y, ps, need=80)
            c.setFont(_font('bold'), 8)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, 'Renovaciones')
            y -= 14
            # Split on double-newlines to preserve paragraph breaks
            renewal_paras = [
                p.strip() for p in str(renewal).split('\n\n') if p.strip()
            ]
            y = _draw_paragraphs(c, y, renewal_paras, font_size=8,
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


def _render_value_added_modules(c, data, _proposal, ps=None, y=None):
    """Render the "Incluido sin costo adicional" section as cards.

    Mirrors frontend/components/BusinessProposal/ValueAddedModules.vue:
    resolves each module_id against the functional_requirements catalog
    (ps['_value_added_catalog']) and renders one tinted card per module
    with title, top-right "Sin costo adicional" pill, justification
    (primary) and optional description (secondary). Each card's full
    height is pre-computed so it never splits across a page break.
    """
    if y is None:
        y = PAGE_H - MARGIN_T
    y = _draw_section_header(c, y, _safe(data, 'index'), _safe(data, 'title'))
    y -= 12

    intro = _safe(data, 'intro')
    if intro:
        y = _draw_paragraphs(c, y, [intro], ps=ps)
        y -= 8

    catalog = ps.get('_value_added_catalog', {}) if ps else {}
    module_ids = _safe(data, 'module_ids', []) or []
    justifications = _safe(data, 'justifications', {}) or {}

    card_pad_x = 14
    card_pad_y = 12
    icon_size = 22
    icon_gap = 10
    title_font_size = 11
    just_font_size = 9
    just_leading = 13
    desc_font_size = 8
    desc_leading = 11
    pill_font_size = 7
    pill_text = 'Sin costo adicional'

    pill_w = (c.stringWidth(pill_text, _font('medium'), pill_font_size)
              + 8 * 2)  # padding_h*2 in _draw_pill
    content_area_w = CONTENT_W - card_pad_x * 2 - icon_size - icon_gap
    title_max_w = content_area_w - pill_w - 8  # gap before pill
    title_chars = max(int(title_max_w / (title_font_size * 0.55)), 10)

    for mid in module_ids:
        module = catalog.get(mid)
        if not module:
            continue
        title = _strip_emoji(_safe(module, 'title')) or 'Módulo'
        description = _strip_emoji(_safe(module, 'description'))
        justification = (justifications.get(mid)
                         if isinstance(justifications, dict) else None)

        title_lines = textwrap.wrap(title, width=title_chars)[:2] or [title]
        just_h = (_estimate_text_height(
                      [justification], max_width=content_area_w,
                      font_size=just_font_size, leading=just_leading)
                  if justification else 0)
        desc_h = (_estimate_text_height(
                      [description], max_width=content_area_w,
                      font_size=desc_font_size, leading=desc_leading)
                  if description else 0)
        card_h = (
            card_pad_y
            + len(title_lines) * 14
            + (6 + just_h if justification else 0)
            + (4 + desc_h if description else 0)
            + card_pad_y
        )

        if ps:
            y = _check_y(c, y, ps, need=card_h + 14)

        card_top = y
        card_bottom = y - card_h
        c.setFillColor(ESMERALD_LIGHT)
        c.roundRect(MARGIN_L, card_bottom, CONTENT_W, card_h, 8,
                    fill=1, stroke=0)

        # Decorative icon square — emoji glyphs don't render in Ubuntu,
        # so we fall back to the title's first letter.
        icon_x = MARGIN_L + card_pad_x
        icon_y = card_top - card_pad_y - icon_size
        c.setFillColor(BONE)
        c.roundRect(icon_x, icon_y, icon_size, icon_size, 5,
                    fill=1, stroke=0)
        c.setFillColor(ESMERALD)
        c.setFont(_font('bold'), 11)
        c.drawCentredString(icon_x + icon_size / 2,
                            icon_y + icon_size / 2 - 3.5,
                            title[:1].upper() if title else '•')

        # Right-aligned pill guarantees no overlap with long titles.
        pill_x = MARGIN_L + CONTENT_W - card_pad_x - pill_w
        pill_baseline_y = card_top - card_pad_y - 10
        _draw_pill(c, pill_x, pill_baseline_y, pill_text,
                   bg_color=LEMON, text_color=ESMERALD,
                   font_size=pill_font_size)

        text_x = icon_x + icon_size + icon_gap
        title_y = card_top - card_pad_y - 10
        c.setFont(_font('bold'), title_font_size)
        c.setFillColor(ESMERALD)
        for line in title_lines:
            c.drawString(text_x, title_y, line)
            title_y -= 14

        next_y = title_y - 2

        if justification:
            next_y -= 4
            next_y = _draw_paragraphs(
                c, next_y, [str(justification)],
                max_width=content_area_w,
                font_size=just_font_size, leading=just_leading,
                color=ESMERALD, x=text_x,
            )

        if description:
            next_y -= 2
            next_y = _draw_paragraphs(
                c, next_y, [str(description)],
                max_width=content_area_w,
                font_size=desc_font_size, leading=desc_leading,
                color=ESMERALD_80, x=text_x,
                font_name=_font('italic'),
            )

        y = card_bottom - 12

    footer_note = _safe(data, 'footer_note')
    if footer_note:
        footer_h = _estimate_text_height(
            [str(footer_note)], max_width=CONTENT_W - 24,
            font_size=9, leading=12,
        )
        if ps:
            y = _check_y(c, y, ps, need=footer_h + 32)
        y -= 4
        y = _draw_banner_box(
            c, MARGIN_L, y, CONTENT_W, str(footer_note),
            bg_color=BONE, text_color=ESMERALD,
            font_size=9, icon_text='✓', ps=ps,
        )

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
    validity = _safe(data, 'validityMessage') or _safe(
        data, 'validityPeriod',
        'Esta propuesta tiene una vigencia de 30 d\u00edas '
        'calendario a partir de su fecha de env\u00edo.',
    )
    # Replace hardcoded days with actual remaining days from expires_at
    if validity and hasattr(proposal, 'expires_at') and proposal.expires_at:
        from django.utils import timezone as _tz
        _now = _tz.now()
        _remaining = max((proposal.expires_at - _now).days, 0)
        import re as _re
        validity = _re.sub(
            r'\d+\s*(d\u00edas|days|d\u00eda|day)',
            f'{_remaining} d\u00edas' if _remaining != 1 else '1 d\u00eda',
            str(validity),
            count=1,
        )
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
    'value_added_modules': _render_value_added_modules,
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
    def generate(cls, proposal, selected_modules=None):
        """
        Build a multi-page portrait-A4 PDF from the proposal's
        enabled sections and return the raw bytes.

        Sections flow continuously — each section starts where the
        previous one ended.  The greeting/cover page is the only
        section that always gets its own page.

        Args:
            proposal: BusinessProposal instance with related sections.
            selected_modules: Optional list of module IDs for dynamic pricing.

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
            # PDF metadata: creation date
            from django.utils import timezone as _tz
            _created = proposal.created_at or _tz.now()
            c.setSubject(
                f'Propuesta de negocio — {proposal.client_name} — '
                f'{_created.strftime("%Y-%m-%d")}'
            )

            ps = {
                'num': 3,
                'client': proposal.client_name,
                'selected_modules': selected_modules,
            }

            # Single pass over sections to build every ps.* derived from them:
            # FR configurable items (for total), calculator modules (additive
            # pricing), value-added IDs + catalog, and the investment total.
            _fr_items = []
            _calc_module_items = []
            _value_added_ids = set()
            _value_added_catalog = {}
            # Trust the model field for the base investment used to price
            # calculator modules (percent-of-base). ``content_json`` mirrors
            # this value but can drift — matches the override applied in
            # ``_render_investment`` and the public frontend view.
            _model_total = getattr(proposal, 'total_investment', None) or 0
            _base_num = int(_model_total)
            needs_selection_data = selected_modules is not None

            for _sec in sections:
                _cj = _sec.content_json or {}
                if _sec.section_type == 'value_added_modules':
                    _value_added_ids.update(_cj.get('module_ids') or [])
                elif _sec.section_type == 'functional_requirements':
                    for _grp in list(_cj.get('groups') or []) + list(_cj.get('additionalModules') or []):
                        _gid = _safe(_grp, 'id')
                        if _gid and _gid not in _value_added_catalog:
                            _value_added_catalog[_gid] = _grp
                        if not needs_selection_data:
                            continue
                        _gkey = _gid or _safe(_grp, 'title') or ''
                        for _it in _safe(_grp, 'items', []):
                            _iname = _safe(_it, 'name') or ''
                            _fid = re.sub(r'\s+', '-', f'fr-{_gkey}-{_iname}').lower()
                            _fprice = _safe(_it, 'price', 0)
                            if _fprice or _safe(_it, 'is_required') is False:
                                _fr_items.append({'id': _fid, 'price': _fprice})
                        if _safe(_grp, 'is_calculator_module'):
                            _pp_raw = _safe(_grp, 'price_percent')
                            try:
                                _pp = float(_pp_raw) if _pp_raw not in (None, '') else None
                            except (TypeError, ValueError):
                                _pp = None
                            _calc_module_items.append({
                                'id': f'module-{_gid or ""}',
                                'group_id': _gid or '',
                                'price_percent': _pp,
                                'price': 0,
                                'is_invite': bool(_safe(_grp, 'is_invite')),
                            })

            for _ci in _calc_module_items:
                if _ci['price_percent'] is not None:
                    _ci['price'] = round(_base_num * _ci['price_percent'] / 100)

            ps['_fr_items'] = _fr_items
            ps['_calc_module_items'] = _calc_module_items
            ps['_value_added_ids'] = _value_added_ids
            ps['_value_added_catalog'] = _value_added_catalog

            # Extract base_weeks from timeline section for dynamic duration
            base_weeks = 0
            if selected_modules is not None:
                for _sec in sections:
                    if _sec.section_type == 'timeline':
                        _td = (_sec.content_json or {}).get('totalDuration', '')
                        _wm = re.search(r'(\d+)\s*(?:semana|week)', str(_td), re.IGNORECASE)
                        if _wm:
                            base_weeks = int(_wm.group(1))
                        break
            ps['base_weeks'] = base_weeks

            # ── Pass A: Content canvas (pages 3+) ────────────────────
            # Pages 1 = greeting, 2 = TOC; content starts at page 3.
            date_str = format_date_es(_created)

            _draw_header_bar(c)
            y = PAGE_H - MARGIN_T
            first_content = True
            toc_entries = []

            for sec in sections:
                stype = sec.section_type
                if stype in ('technical_document', 'greeting'):
                    continue
                data = sec.content_json or {}

                if 'title' not in data or not data['title']:
                    data['title'] = sec.title
                if not data.get('index'):
                    data['index'] = str(sec.order + 1).zfill(2)

                is_paste = (
                    data.get('_editMode') == 'paste'
                    and data.get('rawText')
                )
                renderer = SECTION_RENDERERS.get(stype)

                if first_content:
                    first_content = False
                else:
                    y -= 28
                    y = _check_y(c, y, ps, need=80)

                # Record TOC entry at the page where this section starts
                toc_entries.append((data['index'], data['title'], ps['num']))

                if is_paste:
                    y = _render_raw_text(c, data, proposal, ps=ps,
                                         y=y) or y
                elif renderer:
                    y = renderer(c, data, proposal, ps=ps, y=y) or y

                    # Functional requirements: per-group details
                    func_groups = ps.pop('_func_req_groups', None)
                    parent_idx = data.get('index', '')
                    sel_ids = ps.get('selected_modules')
                    if stype == 'functional_requirements' and func_groups:
                        # Filter out hidden groups and calculator-module groups not selected
                        func_groups = [g for g in func_groups if _safe(g, 'is_visible', True) is not False]
                        func_groups = _filter_calculator_groups(func_groups, sel_ids)
                        for gi, grp in enumerate(func_groups):
                            grp_paste = (
                                _safe(grp, '_editMode') == 'paste'
                                and _safe(grp, 'rawText')
                            )
                            items = _safe(grp, 'items', [])
                            # Filter out deselected configurable FR items only
                            if sel_ids is not None and items:
                                grp_key = (_safe(grp, 'id') or _safe(grp, 'title') or '')
                                filtered = []
                                for it in items:
                                    is_req = _safe(it, 'is_required')
                                    if is_req is True:
                                        filtered.append(it)
                                    else:
                                        configurable = _safe(it, 'price') or is_req is False
                                        if not configurable:
                                            filtered.append(it)
                                        else:
                                            it_name = _safe(it, 'name') or ''
                                            fr_id = re.sub(r'\s+', '-', f'fr-{grp_key}-{it_name}').lower()
                                            if fr_id in sel_ids:
                                                filtered.append(it)
                                items = filtered
                                grp = dict(grp, items=items)
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

            # Creation date line at the bottom of the last content page
            y -= 30
            y = _check_y(c, y, ps, need=20)
            c.setFont(_font('regular'), 8)
            c.setFillColor(GRAY_500)
            c.drawCentredString(
                PAGE_W / 2, y,
                f'Fecha de creaci\u00f3n de la propuesta: {date_str}',
            )
            _draw_footer(c, ps['num'], client_name=ps['client'])
            c.save()
            content_bytes = buf.getvalue()
            buf.close()

            # ── Pass B: Greeting + TOC (pages 1-2) ───────────────────
            buf_prefix = io.BytesIO()
            c_prefix = canvas.Canvas(buf_prefix, pagesize=A4)
            c_prefix.setTitle(f'Propuesta \u2014 {proposal.client_name}')
            c_prefix.setAuthor('Project App')
            ps_prefix = {'num': 1, 'client': proposal.client_name}

            greeting_sec = next(
                (s for s in sections if s.section_type == 'greeting'), None
            )
            if greeting_sec:
                g_data = greeting_sec.content_json or {}
                if 'title' not in g_data or not g_data['title']:
                    g_data['title'] = greeting_sec.title
                is_paste_g = (
                    g_data.get('_editMode') == 'paste'
                    and g_data.get('rawText')
                )
                _draw_header_bar(c_prefix)
                if is_paste_g:
                    _render_raw_text(c_prefix, g_data, proposal, ps=ps_prefix)
                else:
                    renderer_g = SECTION_RENDERERS.get('greeting')
                    if renderer_g:
                        renderer_g(c_prefix, g_data, proposal, ps=ps_prefix)
                _draw_footer(c_prefix, ps_prefix['num'],
                             client_name=ps_prefix['client'])
                c_prefix.showPage()
                ps_prefix['num'] += 1

            link_areas = []
            _draw_toc_page(c_prefix, toc_entries, ps_prefix, link_areas=link_areas)
            c_prefix.save()
            prefix_bytes = buf_prefix.getvalue()
            buf_prefix.close()

            pdf_bytes = cls._merge_with_covers(content_bytes, prepend_bytes=prefix_bytes)

            cover_offset = 1 if COVER_PDF.exists() else 0
            pdf_bytes = _apply_toc_links(pdf_bytes, link_areas, cover_offset)

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
    def _merge_with_covers(content_bytes, prepend_bytes=None):
        """Merge static Portada + content + Contraportada.

        Delegates to the shared ``merge_with_covers`` in pdf_utils.
        """
        from content.services.pdf_utils import merge_with_covers
        return merge_with_covers(content_bytes, prepend_bytes=prepend_bytes)

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
