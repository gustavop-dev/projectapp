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
    ESMERALD,
    GRAY_500,
    MARGIN_L,
    MARGIN_T,
    PAGE_H,
    PAGE_W,
    _check_y,
    _draw_footer,
    _draw_header_bar,
    _draw_paragraphs,
    _draw_section_header,
    _font,
    _register_fonts,
    _safe,
    _strip_emoji,
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

    sec = (
        proposal.sections.filter(is_enabled=True, section_type='technical_document').first()
    )
    if not sec:
        return None
    data = sec.content_json if isinstance(sec.content_json, dict) else {}
    data = filter_technical_document_by_module_selection(data, selected_modules)

    try:
        _register_fonts()
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setTitle(f'Detalle técnico — {proposal.client_name}')
        c.setAuthor('Project App')

        ps = {'num': 1, 'client': proposal.client_name}
        _draw_header_bar(c)
        y = PAGE_H - MARGIN_T

        # Title block
        c.setFont(_font('light'), 28)
        c.setFillColor(ESMERALD)
        title = _strip_emoji(f'Detalle técnico — {proposal.client_name or "Cliente"}')
        for line in textwrap.wrap(title, width=36) or [title]:
            y = _check_y(c, y, ps, need=36)
            c.drawString(MARGIN_L, y, line)
            y -= 32
        y -= 10
        c.setFont(_font('regular'), 9)
        c.setFillColor(GRAY_500)
        from django.utils import timezone as _tz

        _created = proposal.created_at or _tz.now()
        c.drawString(MARGIN_L, y, _created.strftime('%Y-%m-%d'))
        y -= 40

        section_i = 0

        def next_section(title_es):
            nonlocal y, section_i
            section_i += 1
            y -= 24
            y = _check_y(c, y, ps, need=90)
            y = _draw_section_header(c, y, str(section_i), title_es, ps=ps)
            return y

        purpose = data.get('purpose') or ''
        if _nonempty_str(purpose):
            y = next_section('Propósito')
            y = _draw_paragraphs(c, y, [purpose.strip()], ps=ps)

        stack = data.get('stack') or []
        stack_rows = [
            r for r in stack
            if isinstance(r, dict) and _row_any(r, ('layer', 'technology', 'rationale'))
        ]
        if stack_rows:
            y = next_section('Stack tecnológico')
            for r in stack_rows:
                layer = _safe(r, 'layer') or '—'
                tech = _safe(r, 'technology') or '—'
                why = _safe(r, 'rationale') or ''
                block = f'{layer} | {tech}' + (f' — {why}' if why else '')
                y = _check_y(c, y, ps, need=40)
                y = _draw_paragraphs(c, y, [block], ps=ps)

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
            for p in patterns:
                line = ' | '.join(
                    filter(None, [
                        _safe(p, 'component'),
                        _safe(p, 'pattern'),
                        _safe(p, 'description'),
                    ])
                )
                y = _draw_paragraphs(c, y, [line], ps=ps)
            if arch_note:
                y = _draw_paragraphs(c, y, [f'Nota: {arch_note}'], ps=ps)

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
            if dm_rel:
                y = _draw_paragraphs(c, y, [dm_rel], ps=ps)
            for e in entities:
                line = ' | '.join(
                    filter(None, [
                        _safe(e, 'name'),
                        _safe(e, 'description'),
                        _safe(e, 'keyFields'),
                    ])
                )
                y = _draw_paragraphs(c, y, [line], ps=ps)

        gr = data.get('growthReadiness') if isinstance(data.get('growthReadiness'), dict) else {}
        gr_sum = (gr.get('summary') or '').strip()
        gr_strat = [
            r for r in (gr.get('strategies') or [])
            if isinstance(r, dict) and _row_any(r, ('dimension', 'preparation', 'evolution'))
        ]
        if gr_sum or gr_strat:
            y = next_section('Preparación para el crecimiento')
            if gr_sum:
                y = _draw_paragraphs(c, y, [gr_sum], ps=ps)
            for r in gr_strat:
                line = ' | '.join(
                    filter(
                        None,
                        [
                            _safe(r, 'dimension'),
                            _safe(r, 'preparation'),
                            _safe(r, 'evolution'),
                        ],
                    )
                )
                y = _draw_paragraphs(c, y, [line], ps=ps)

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
            y = next_section('Módulos del producto')
            for ep, reqs in epic_blocks:
                head = _safe(ep, 'title') or _safe(ep, 'epicKey') or 'Módulo'
                y = _check_y(c, y, ps, need=28)
                c.setFont(_font('bold'), 11)
                c.setFillColor(ESMERALD)
                c.drawString(MARGIN_L, y, _strip_emoji(head)[:80])
                y -= 18
                desc = (_safe(ep, 'description') or '').strip()
                if desc:
                    c.setFont(_font('regular'), 10)
                    c.setFillColor(GRAY_500)
                    y = _draw_paragraphs(c, y, [desc], ps=ps)
                for q in reqs:
                    pr = _safe(q, 'priority') or ''
                    pr_suffix = f' [{pr}]' if pr else ''
                    qt = (_safe(q, 'title') or 'Requerimiento') + pr_suffix
                    y = _check_y(c, y, ps, need=50)
                    c.setFont(_font('bold'), 10)
                    c.setFillColor(ESMERALD)
                    c.drawString(MARGIN_L, y, _strip_emoji(qt)[:90])
                    y -= 16
                    c.setFont(_font('regular'), 9)
                    c.setFillColor(GRAY_500)
                    for key, label in (
                        ('description', ''),
                        ('configuration', 'Config: '),
                        ('usageFlow', 'Flujo: '),
                    ):
                        txt = (_safe(q, key) or '').strip()
                        if txt:
                            y = _draw_paragraphs(c, y, [f'{label}{txt}'], ps=ps)
                y -= 8

        api_sum = (data.get('apiSummary') or '').strip()
        api_dom = [
            d for d in (data.get('apiDomains') or [])
            if isinstance(d, dict) and _row_any(d, ('domain', 'summary'))
        ]
        if api_sum or api_dom:
            y = next_section('API')
            if api_sum:
                y = _draw_paragraphs(c, y, [api_sum], ps=ps)
            for d in api_dom:
                line = f"{_safe(d, 'domain')}: {_safe(d, 'summary')}"
                y = _draw_paragraphs(c, y, [line], ps=ps)

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
            for r in inc:
                line = ' | '.join(
                    filter(None, [
                        _safe(r, 'service'),
                        _safe(r, 'provider'),
                        _safe(r, 'connection'),
                    ])
                )
                y = _draw_paragraphs(c, y, [line], ps=ps)
            for r in exc:
                line = f"{_safe(r, 'service')}: {_safe(r, 'reason')}"
                y = _draw_paragraphs(c, y, [line], ps=ps)
            if notes:
                for bullet in notes.splitlines():
                    b = bullet.strip()
                    if b:
                        y = _draw_paragraphs(c, y, [f'• {b}'], ps=ps)

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
            for r in envs:
                line = ' | '.join(
                    filter(
                        None,
                        [
                            _safe(r, 'name'),
                            _safe(r, 'purpose'),
                            _safe(r, 'url'),
                        ],
                    )
                )
                y = _draw_paragraphs(c, y, [line], ps=ps)

        sec_rows = [
            r for r in (data.get('security') or [])
            if isinstance(r, dict) and _row_any(r, ('aspect', 'implementation'))
        ]
        if sec_rows:
            y = next_section('Seguridad')
            for r in sec_rows:
                line = f"{_safe(r, 'aspect')}: {_safe(r, 'implementation')}"
                y = _draw_paragraphs(c, y, [line], ps=ps)

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
            for m in metrics:
                line = ' | '.join(
                    filter(
                        None,
                        [
                            _safe(m, 'metric'),
                            _safe(m, 'target'),
                            _safe(m, 'howMeasured'),
                        ],
                    )
                )
                y = _draw_paragraphs(c, y, [line], ps=ps)
            for p in practices:
                line = f"{_safe(p, 'strategy')}: {_safe(p, 'description')}"
                y = _draw_paragraphs(c, y, [line], ps=ps)

        bk = (data.get('backupsNote') or '').strip()
        if bk:
            y = next_section('Backups')
            y = _draw_paragraphs(c, y, [bk], ps=ps)

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
            for x in dims:
                line = ' | '.join(
                    filter(
                        None,
                        [
                            _safe(x, 'dimension'),
                            _safe(x, 'evaluates'),
                            _safe(x, 'standard'),
                        ],
                    )
                )
                y = _draw_paragraphs(c, y, [line], ps=ps)
            for x in tests:
                line = ' | '.join(
                    filter(
                        None,
                        [
                            _safe(x, 'type'),
                            _safe(x, 'validates'),
                            _safe(x, 'tool'),
                        ],
                    )
                )
                y = _draw_paragraphs(c, y, [line], ps=ps)
            if cf:
                y = _draw_paragraphs(c, y, [cf], ps=ps)

        decisions = [
            r for r in (data.get('decisions') or [])
            if isinstance(r, dict) and _row_any(r, ('decision', 'alternative', 'reason'))
        ]
        if decisions:
            y = next_section('Decisiones')
            for r in decisions:
                line = ' | '.join(
                    filter(
                        None,
                        [
                            _safe(r, 'decision'),
                            _safe(r, 'alternative'),
                            _safe(r, 'reason'),
                        ],
                    )
                )
                y = _draw_paragraphs(c, y, [line], ps=ps)

        y -= 20
        y = _check_y(c, y, ps, need=24)
        c.setFont(_font('regular'), 8)
        c.setFillColor(GRAY_500)
        c.drawString(
            MARGIN_L,
            y,
            'Condiciones de soporte según propuesta comercial.',
        )

        _draw_footer(c, ps['num'], client_name=ps['client'])
        c.save()
        out = buf.getvalue()
        buf.close()
        return out
    except Exception:
        logger.exception('Technical PDF failed for proposal %s', proposal.uuid)
        return None
