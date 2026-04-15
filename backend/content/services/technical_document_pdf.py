"""
Technical-only PDF (ReportLab canvas) for proposal technical_document section.

Commercial proposal PDF excludes this section; ?doc=technical uses this module.
"""

import io
import logging
import textwrap

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.services.pdf_utils import (
    BONE,
    CONTENT_W,
    COVER_PDF,
    COVER_TECHNICAL_PDF,
    ESMERALD,
    ESMERALD_80,
    ESMERALD_DARK,
    ESMERALD_LIGHT,
    GRAY_500,
    LEMON,
    MARGIN_L,
    MARGIN_T,
    PAGE_H,
    PAGE_W,
    WHITE,
    _apply_toc_links,
    _check_y,
    _draw_bullet_list,
    _draw_decorative_title_page,
    _draw_footer,
    _draw_header_bar,
    _draw_paragraphs,
    _draw_pill,
    _draw_section_header,
    _draw_separator,
    _draw_subtitle,
    _draw_table,
    _draw_toc_page,
    _font,
    _register_fonts,
    _safe,
    _strip_emoji,
    format_date_es,
    merge_with_covers,
)

logger = logging.getLogger(__name__)


def _nonempty_str(v):
    return isinstance(v, str) and v.strip()


def _row_any(row, keys):
    if not row or not isinstance(row, dict):
        return False
    return any(_nonempty_str(row.get(k)) for k in keys)


def generate_technical_document_pdf(proposal, selected_modules=None):
    """
    Build a PDF from the enabled technical_document section only.
    Returns bytes or None if section missing/disabled or on error.

    selected_modules: optional list of module/group ids (module-*, group-*).
    None means no filtering (show all linked requirements). Empty list filters
    to base-scope requirements only.
    """
    from content.services.technical_document_filter import (
        filter_technical_document_by_module_selection,
    )
    from content.services.proposal_module_links import (
        build_proposal_module_link_catalog,
        normalize_technical_document_module_links,
    )

    sec = (
        proposal.sections.filter(is_enabled=True, section_type='technical_document').first()
    )
    if not sec:
        return None
    data = sec.content_json if isinstance(sec.content_json, dict) else {}
    section_payloads = [
        {
            'section_type': section.section_type,
            'content_json': section.content_json if isinstance(section.content_json, dict) else {},
        }
        for section in proposal.sections.all()
    ]
    data = normalize_technical_document_module_links(data, section_payloads)
    link_catalog = build_proposal_module_link_catalog(section_payloads)
    data = filter_technical_document_by_module_selection(
        data,
        selected_modules,
        always_included_ids=link_catalog['always_included_ids'],
    )

    try:
        _register_fonts()
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setTitle(f'Detalle t\u00e9cnico \u2014 {proposal.client_name}')
        c.setAuthor('Project App')

        from django.utils import timezone as _tz

        _created = proposal.created_at or _tz.now()
        date_str = format_date_es(_created)

        # ── Pass A: Content pages (ps.num starts at 3) ───────
        # Page 1 = title page, page 2 = TOC; content begins at page 3.
        ps = {'num': 3, 'client': proposal.client_name}

        _draw_header_bar(c)
        y = PAGE_H - MARGIN_T
        section_i = 0
        toc_entries = []

        def next_section(title_es):
            nonlocal y, section_i
            section_i += 1
            idx = str(section_i).zfill(2)
            y -= 24
            y = _check_y(c, y, ps, need=90)
            section_page = ps['num']
            y = _draw_section_header(c, y, idx, title_es, ps=ps)
            toc_entries.append((idx, title_es, section_page))
            return y

        # ── 1. Propósito ──────────────────────────────────────
        purpose = data.get('purpose') or ''
        if _nonempty_str(purpose):
            y = next_section('Prop\u00f3sito')
            y = _draw_paragraphs(c, y, [purpose.strip()], ps=ps)

        # ── 2. Stack tecnológico ──────────────────────────────
        stack = data.get('stack') or []
        stack_rows = [
            r for r in stack
            if isinstance(r, dict) and _row_any(r, ('layer', 'technology', 'rationale'))
        ]
        if stack_rows:
            y = next_section('Stack tecnol\u00f3gico')
            headers = ['Capa', 'Tecnolog\u00eda', 'Justificaci\u00f3n']
            rows = [
                [
                    _safe(r, 'layer') or '\u2014',
                    _safe(r, 'technology') or '\u2014',
                    _safe(r, 'rationale') or '',
                ]
                for r in stack_rows
            ]
            y = _draw_table(c, y, headers, rows, ps=ps)

        # ── 3. Arquitectura ───────────────────────────────────
        arch = data.get('architecture') if isinstance(data.get('architecture'), dict) else {}
        arch_text = (arch.get('summary') or '').strip()
        arch_note = (arch.get('diagramNote') or '').strip()
        patterns = [p for p in (arch.get('patterns') or []) if isinstance(p, dict) and _row_any(
            p, ('component', 'pattern', 'description')
        )]
        if arch_text or arch_note or patterns:
            y = next_section('Arquitectura')
            if arch_text:
                y = _draw_paragraphs(c, y, [arch_text], ps=ps)
            if patterns:
                y -= 8
                headers = ['Componente', 'Patr\u00f3n', 'Descripci\u00f3n']
                rows = [
                    [
                        _safe(p, 'component') or '\u2014',
                        _safe(p, 'pattern') or '\u2014',
                        _safe(p, 'description') or '',
                    ]
                    for p in patterns
                ]
                y = _draw_table(c, y, headers, rows, ps=ps)
            if arch_note:
                y -= 8
                y = _draw_paragraphs(c, y, [f'Nota: {arch_note}'], ps=ps)

        # ── 4. Modelo de datos ────────────────────────────────
        dm = data.get('dataModel') if isinstance(data.get('dataModel'), dict) else {}
        dm_sum = (dm.get('summary') or '').strip()
        dm_rel = (dm.get('relationships') or '').strip()
        entities = [
            e for e in (dm.get('entities') or [])
            if isinstance(e, dict) and _row_any(e, ('name', 'description', 'keyFields'))
        ]
        if dm_sum or dm_rel or entities:
            y = next_section('Modelo de datos')
            if dm_sum:
                y = _draw_paragraphs(c, y, [dm_sum], ps=ps)
            if entities:
                y -= 8
                headers = ['Entidad', 'Descripci\u00f3n', 'Campos clave']
                rows = [
                    [
                        _safe(e, 'name') or '\u2014',
                        _safe(e, 'description') or '',
                        _safe(e, 'keyFields') or '',
                    ]
                    for e in entities
                ]
                y = _draw_table(c, y, headers, rows, ps=ps)
            if dm_rel:
                y -= 8
                y = _draw_subtitle(c, y, 'Relaciones', ps=ps)
                y = _draw_paragraphs(c, y, [dm_rel], ps=ps)

        # ── 5. Preparación para el crecimiento ────────────────
        gr = data.get('growthReadiness') if isinstance(data.get('growthReadiness'), dict) else {}
        gr_sum = (gr.get('summary') or '').strip()
        gr_strat = [
            r for r in (gr.get('strategies') or [])
            if isinstance(r, dict) and _row_any(r, ('dimension', 'preparation', 'evolution'))
        ]
        if gr_sum or gr_strat:
            y = next_section('Preparaci\u00f3n para el crecimiento')
            if gr_sum:
                y = _draw_paragraphs(c, y, [gr_sum], ps=ps)
            if gr_strat:
                y -= 8
                headers = ['Dimensi\u00f3n', 'Preparaci\u00f3n', 'Evoluci\u00f3n']
                rows = [
                    [
                        _safe(r, 'dimension') or '\u2014',
                        _safe(r, 'preparation') or '',
                        _safe(r, 'evolution') or '',
                    ]
                    for r in gr_strat
                ]
                y = _draw_table(c, y, headers, rows, ps=ps)

        # ── 6. Módulos del producto ───────────────────────────
        epics = [e for e in (data.get('epics') or []) if isinstance(e, dict)]
        epic_blocks = []
        for ep in epics:
            reqs = [
                q for q in (ep.get('requirements') or [])
                if isinstance(q, dict) and _row_any(
                    q, ('title', 'description', 'configuration', 'usageFlow', 'flowKey')
                )
            ]
            if _nonempty_str(ep.get('title')) or _nonempty_str(ep.get('description')) or reqs:
                epic_blocks.append((ep, reqs))
        if epic_blocks:
            y = next_section('M\u00f3dulos del producto')
            for ei, (ep, reqs) in enumerate(epic_blocks):
                if ei > 0:
                    y = _draw_separator(c, y, ps=ps)

                head = _safe(ep, 'title') or _safe(ep, 'epicKey') or 'M\u00f3dulo'
                y = _draw_subtitle(c, y, _strip_emoji(head)[:80], ps=ps)

                desc = (_safe(ep, 'description') or '').strip()
                if desc:
                    y = _draw_paragraphs(c, y, [desc], ps=ps)

                # ── Requirements table — one row per requirement ──────
                if reqs:
                    num_col_w = 28
                    name_col_w = int((CONTENT_W - num_col_w) * 0.36)
                    desc_col_w = CONTENT_W - num_col_w - name_col_w
                    name_chars = int(name_col_w / 5.0) - 1
                    desc_chars = int(desc_col_w / 4.5) - 1

                    # Table header
                    hdr_h = 22
                    y = _check_y(c, y, ps, need=hdr_h + 32)
                    hdr_bottom = y - hdr_h
                    c.setFillColor(ESMERALD_DARK)
                    c.rect(MARGIN_L, hdr_bottom, CONTENT_W, hdr_h, fill=1, stroke=0)
                    hdr_text_y = hdr_bottom + (hdr_h - 8) / 2
                    c.setFont(_font('bold'), 8)
                    c.setFillColor(WHITE)
                    c.drawCentredString(MARGIN_L + num_col_w / 2, hdr_text_y, '#')
                    c.drawString(MARGIN_L + num_col_w + 6, hdr_text_y, 'Requerimiento')
                    c.drawString(MARGIN_L + num_col_w + name_col_w + 6, hdr_text_y, 'Descripción')
                    y = hdr_bottom

                    for qi, q in enumerate(reqs):
                        pr = _safe(q, 'priority') or ''
                        qt = _strip_emoji(_safe(q, 'title') or 'Requerimiento')
                        q_desc = (_safe(q, 'description') or '').strip()
                        q_conf = (_safe(q, 'configuration') or '').strip()
                        q_flow = (_safe(q, 'usageFlow') or '').strip()

                        name_lines = textwrap.wrap(qt, width=name_chars) or [qt]
                        all_desc_lines = []  # list of (text, bold_prefix | None)
                        if q_desc:
                            for line in textwrap.wrap(q_desc, width=desc_chars) or [q_desc]:
                                all_desc_lines.append((line, None))
                        if q_conf:
                            conf_lines = textwrap.wrap(f'Config: {q_conf}', width=desc_chars) or [f'Config: {q_conf}']
                            for i, line in enumerate(conf_lines):
                                all_desc_lines.append((line, 'Config:' if i == 0 else None))
                        if q_flow:
                            flow_lines = textwrap.wrap(f'Flujo: {q_flow}', width=desc_chars) or [f'Flujo: {q_flow}']
                            for i, line in enumerate(flow_lines):
                                all_desc_lines.append((line, 'Flujo:' if i == 0 else None))

                        line_h = 11
                        n_lines = max(len(name_lines), len(all_desc_lines) if all_desc_lines else 1)
                        row_h = n_lines * line_h + 14
                        row_h = max(row_h, 28)

                        y = _check_y(c, y, ps, need=row_h)
                        row_bottom = y - row_h

                        # Row background (alternating)
                        c.setFillColor(ESMERALD_LIGHT if qi % 2 == 0 else WHITE)
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
                            str(qi + 1).zfill(2),
                        )

                        # Requirement title (top-aligned, bold)
                        text_y = y - 9
                        c.setFont(_font('bold'), 9)
                        c.setFillColor(ESMERALD)
                        for nl in name_lines:
                            c.drawString(MARGIN_L + num_col_w + 6, text_y, nl)
                            text_y -= line_h
                        if pr:
                            _draw_pill(
                                c, MARGIN_L + num_col_w + 6, text_y + 2, pr,
                                bg_color=BONE, text_color=ESMERALD,
                                font_size=6, padding_h=4, padding_v=2,
                            )

                        # Description + config + flow (top-aligned; config/flujo prefix bold only)
                        if all_desc_lines:
                            text_y = y - 9
                            c.setFillColor(ESMERALD_80)
                            dx = MARGIN_L + num_col_w + name_col_w + 6
                            for dl, bold_prefix in all_desc_lines:
                                if bold_prefix and dl.startswith(bold_prefix):
                                    c.setFont(_font('bold'), 8)
                                    c.setFillColor(ESMERALD_80)
                                    c.drawString(dx, text_y, bold_prefix)
                                    prefix_w = c.stringWidth(bold_prefix, _font('bold'), 8)
                                    remainder = dl[len(bold_prefix):]
                                    if remainder:
                                        c.setFont(_font('regular'), 8)
                                        c.drawString(dx + prefix_w, text_y, remainder)
                                else:
                                    c.setFont(_font('regular'), 8)
                                    c.setFillColor(ESMERALD_80)
                                    c.drawString(dx, text_y, dl)
                                text_y -= line_h

                        y = row_bottom
                    y -= 8

        # ── 7. API ────────────────────────────────────────────
        api_sum = (data.get('apiSummary') or '').strip()
        api_dom = [
            d for d in (data.get('apiDomains') or [])
            if isinstance(d, dict) and _row_any(d, ('domain', 'summary'))
        ]
        if api_sum or api_dom:
            y = next_section('API')
            if api_sum:
                y = _draw_paragraphs(c, y, [api_sum], ps=ps)
            if api_dom:
                y -= 8
                headers = ['Dominio', 'Descripci\u00f3n']
                rows = [
                    [_safe(d, 'domain') or '\u2014', _safe(d, 'summary') or '']
                    for d in api_dom
                ]
                y = _draw_table(c, y, headers, rows, ps=ps)

        # ── 8. Integraciones ──────────────────────────────────
        integ = data.get('integrations') if isinstance(data.get('integrations'), dict) else {}
        notes = (integ.get('notes') or '').strip()
        inc = [
            r for r in (integ.get('included') or [])
            if isinstance(r, dict) and _row_any(
                r, ('service', 'provider', 'connection', 'dataExchange', 'accountOwner')
            )
        ]
        exc = [
            r for r in (integ.get('excluded') or [])
            if isinstance(r, dict) and _row_any(r, ('service', 'reason', 'availability'))
        ]
        if inc or exc or notes:
            y = next_section('Integraciones')
            if inc:
                y = _draw_subtitle(c, y, 'Incluidas', ps=ps)
                headers = ['Servicio', 'Proveedor', 'Conexi\u00f3n']
                rows = [
                    [
                        _safe(r, 'service') or '\u2014',
                        _safe(r, 'provider') or '',
                        _safe(r, 'connection') or '',
                    ]
                    for r in inc
                ]
                y = _draw_table(c, y, headers, rows, ps=ps)
            if exc:
                y -= 8
                y = _draw_subtitle(c, y, 'Excluidas', ps=ps)
                headers = ['Servicio', 'Raz\u00f3n']
                rows = [
                    [_safe(r, 'service') or '\u2014', _safe(r, 'reason') or '']
                    for r in exc
                ]
                y = _draw_table(c, y, headers, rows, ps=ps)
            if notes:
                y -= 8
                bullets = [b.strip() for b in notes.splitlines() if b.strip()]
                if bullets:
                    y = _draw_bullet_list(c, y, bullets, ps=ps)

        # ── 9. Ambientes ──────────────────────────────────────
        env_note = (data.get('environmentsNote') or '').strip()
        envs = [
            r for r in (data.get('environments') or [])
            if isinstance(r, dict) and _row_any(
                r, ('name', 'purpose', 'url', 'database', 'whoAccesses')
            )
        ]
        if env_note or envs:
            y = next_section('Ambientes')
            if env_note:
                y = _draw_paragraphs(c, y, [env_note], ps=ps)
            if envs:
                y -= 8
                headers = ['Nombre', 'Prop\u00f3sito', 'URL']
                rows = [
                    [
                        _safe(r, 'name') or '\u2014',
                        _safe(r, 'purpose') or '',
                        _safe(r, 'url') or '',
                    ]
                    for r in envs
                ]
                y = _draw_table(c, y, headers, rows, ps=ps)

        # ── 10. Seguridad ─────────────────────────────────────
        sec_rows = [
            r for r in (data.get('security') or [])
            if isinstance(r, dict) and _row_any(r, ('aspect', 'implementation'))
        ]
        if sec_rows:
            y = next_section('Seguridad')
            headers = ['Aspecto', 'Implementaci\u00f3n']
            rows = [
                [_safe(r, 'aspect') or '\u2014', _safe(r, 'implementation') or '']
                for r in sec_rows
            ]
            y = _draw_table(c, y, headers, rows, ps=ps)

        # ── 11. Rendimiento ───────────────────────────────────
        pq = data.get('performanceQuality') if isinstance(data.get('performanceQuality'), dict) else {}
        metrics = [
            m for m in (pq.get('metrics') or [])
            if isinstance(m, dict) and _row_any(m, ('metric', 'target', 'howMeasured'))
        ]
        practices = [
            p for p in (pq.get('practices') or [])
            if isinstance(p, dict) and _row_any(p, ('strategy', 'description'))
        ]
        if metrics or practices:
            y = next_section('Rendimiento')
            if metrics:
                headers = ['M\u00e9trica', 'Objetivo', 'Medici\u00f3n']
                rows = [
                    [
                        _safe(m, 'metric') or '\u2014',
                        _safe(m, 'target') or '',
                        _safe(m, 'howMeasured') or '',
                    ]
                    for m in metrics
                ]
                y = _draw_table(c, y, headers, rows, ps=ps)
            if practices:
                y -= 8
                y = _draw_subtitle(c, y, 'Pr\u00e1cticas', ps=ps)
                headers = ['Estrategia', 'Descripci\u00f3n']
                rows = [
                    [_safe(p, 'strategy') or '\u2014', _safe(p, 'description') or '']
                    for p in practices
                ]
                y = _draw_table(c, y, headers, rows, ps=ps)

        # ── 12. Backups ───────────────────────────────────────
        bk = (data.get('backupsNote') or '').strip()
        if bk:
            y = next_section('Backups')
            y = _draw_paragraphs(c, y, [bk], ps=ps)

        # ── 13. Calidad ───────────────────────────────────────
        qual = data.get('quality') if isinstance(data.get('quality'), dict) else {}
        dims = [
            x for x in (qual.get('dimensions') or [])
            if isinstance(x, dict) and _row_any(x, ('dimension', 'evaluates', 'standard'))
        ]
        tests = [
            x for x in (qual.get('testTypes') or [])
            if isinstance(x, dict) and _row_any(x, ('type', 'validates', 'tool', 'whenRun'))
        ]
        cf = (qual.get('criticalFlowsNote') or '').strip()
        if dims or tests or cf:
            y = next_section('Calidad')
            if dims:
                headers = ['Dimensi\u00f3n', 'Eval\u00faa', 'Est\u00e1ndar']
                rows = [
                    [
                        _safe(x, 'dimension') or '\u2014',
                        _safe(x, 'evaluates') or '',
                        _safe(x, 'standard') or '',
                    ]
                    for x in dims
                ]
                y = _draw_table(c, y, headers, rows, ps=ps)
            if tests:
                y -= 8
                y = _draw_subtitle(c, y, 'Tipos de prueba', ps=ps)
                headers = ['Tipo', 'Valida', 'Herramienta']
                rows = [
                    [
                        _safe(x, 'type') or '\u2014',
                        _safe(x, 'validates') or '',
                        _safe(x, 'tool') or '',
                    ]
                    for x in tests
                ]
                y = _draw_table(c, y, headers, rows, ps=ps)
            if cf:
                y -= 8
                y = _draw_subtitle(c, y, 'Flujos cr\u00edticos', ps=ps)
                y = _draw_paragraphs(c, y, [cf], ps=ps)

        # ── 14. Decisiones ────────────────────────────────────
        decisions = [
            r for r in (data.get('decisions') or [])
            if isinstance(r, dict) and _row_any(r, ('decision', 'alternative', 'reason'))
        ]
        if decisions:
            y = next_section('Decisiones')
            headers = ['Decisi\u00f3n', 'Alternativa', 'Raz\u00f3n']
            rows = [
                [
                    _safe(r, 'decision') or '\u2014',
                    _safe(r, 'alternative') or '',
                    _safe(r, 'reason') or '',
                ]
                for r in decisions
            ]
            y = _draw_table(c, y, headers, rows, ps=ps)

        # ── Footer note ──────────────────────────────────────
        y -= 20
        y = _check_y(c, y, ps, need=24)
        c.setFont(_font('regular'), 8)
        c.setFillColor(GRAY_500)
        c.drawCentredString(
            PAGE_W / 2,
            y,
            f'Fecha de creaci\u00f3n del documento: {date_str}',
        )
        y -= 16
        c.drawCentredString(
            PAGE_W / 2,
            y,
            'Condiciones de soporte seg\u00fan propuesta comercial.',
        )

        _draw_footer(c, ps['num'], client_name=ps['client'])
        c.save()
        content_bytes = buf.getvalue()
        buf.close()

        # ── Pass B: Title page + TOC (pages 1-2) ─────────────
        buf2 = io.BytesIO()
        c2 = canvas.Canvas(buf2, pagesize=A4)
        ps2 = {'num': 1, 'client': proposal.client_name}
        _draw_decorative_title_page(
            c2,
            'DETALLE T\u00c9CNICO',
            proposal.client_name or 'Cliente',
            date_str,
            ps2,
        )
        link_areas = []
        _draw_toc_page(c2, toc_entries, ps2, link_areas=link_areas)
        c2.save()
        prefix_bytes = buf2.getvalue()
        buf2.close()

        final_pdf = merge_with_covers(
            content_bytes,
            cover_path=COVER_TECHNICAL_PDF,
            prepend_bytes=prefix_bytes,
        )

        cover_offset = 1 if (COVER_TECHNICAL_PDF.exists() or COVER_PDF.exists()) else 0
        return _apply_toc_links(final_pdf, link_areas, cover_offset)
    except Exception:
        logger.exception('Technical PDF failed for proposal %s', proposal.uuid)
        return None
