"""
Generate a contract PDF from a markdown template or custom markdown text.

Two modes:
- **default**: Loads the ContractTemplate from the database, substitutes
  {placeholders} with values from ``proposal.contract_params``, parses
  the resulting markdown into blocks, and renders a branded PDF.
- **custom**: Uses the raw markdown stored in
  ``proposal.contract_params['custom_contract_markdown']`` as-is (no
  placeholder substitution).

Both modes share the same markdown → blocks → ReportLab rendering pipeline.
"""

import io
import logging

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.services.markdown_parser import markdown_to_blocks
from content.services.pdf_utils import (
    ESMERALD,
    ESMERALD_80,
    GRAY_500,
    GRAY_300,
    LEMON,
    MARGIN_L,
    MARGIN_T,
    PAGE_H,
    PAGE_W,
    CONTENT_W,
    _check_y,
    _draw_footer,
    _draw_header_bar,
    _draw_paragraphs,
    _draw_separator,
    _draw_table,
    _draw_blockquote,
    _draw_code_block,
    _font,
    _register_fonts,
    _strip_emoji,
)

logger = logging.getLogger(__name__)

# Placeholder default values when a param is missing
_PLACEHOLDER_BLANK = '_______________'


def _build_params(raw_params: dict) -> dict:
    """Build a substitution dict with sensible defaults for missing values."""
    return {
        'contractor_full_name': raw_params.get('contractor_full_name', _PLACEHOLDER_BLANK),
        'contractor_cedula': raw_params.get('contractor_cedula', _PLACEHOLDER_BLANK),
        'contractor_email': raw_params.get('contractor_email', _PLACEHOLDER_BLANK),
        'bank_name': raw_params.get('bank_name', _PLACEHOLDER_BLANK),
        'bank_account_type': raw_params.get('bank_account_type', 'Ahorros'),
        'bank_account_number': raw_params.get('bank_account_number', _PLACEHOLDER_BLANK),
        'contract_city': raw_params.get('contract_city', 'Medellín'),
        'client_full_name': raw_params.get('client_full_name', _PLACEHOLDER_BLANK),
        'client_cedula': raw_params.get('client_cedula', _PLACEHOLDER_BLANK),
        'client_email': raw_params.get('client_email', _PLACEHOLDER_BLANK),
        'contract_date': raw_params.get('contract_date', ''),
    }


def _substitute_placeholders(markdown_text: str, params: dict) -> str:
    """Replace {placeholders} in the markdown template with param values."""
    try:
        return markdown_text.format(**params)
    except KeyError as exc:
        logger.warning('Unknown placeholder %s in contract template; falling back to per-key substitution', exc)
        result = markdown_text
        for key, value in params.items():
            result = result.replace('{' + key + '}', str(value))
        return result


def _get_contract_markdown(raw_params: dict, params: dict) -> str:
    """Return the final markdown text for the contract PDF."""
    source = raw_params.get('contract_source', 'default')

    if source == 'custom':
        return raw_params.get('custom_contract_markdown', '')

    # Default: load template from DB and substitute placeholders
    from content.models import ContractTemplate
    template = ContractTemplate.get_default()
    if not template:
        logger.error('No default ContractTemplate found in DB')
        return ''

    return _substitute_placeholders(template.content_markdown, params)


# ---------------------------------------------------------------------------
# Block rendering — reuses pdf_utils primitives
# ---------------------------------------------------------------------------

def _render_block(c, y, block, ps):
    """Render a single markdown block on the canvas. Returns the new y position."""
    block_type = block.get('type', '')

    if block_type == 'heading':
        level = block.get('level', 2)
        text = _strip_emoji(block.get('text', ''))
        if level == 1:
            y = _check_y(c, y, ps, need=50)
            c.setFont(_font('bold'), 14)
            c.setFillColor(ESMERALD)
        elif level == 2:
            y = _check_y(c, y, ps, need=40)
            y -= 16
            c.setFont(_font('bold'), 12)
            c.setFillColor(ESMERALD)
        else:
            y = _check_y(c, y, ps, need=30)
            y -= 8
            c.setFont(_font('bold'), 10)
            c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, text)
        y -= 18

    elif block_type == 'paragraph':
        text = block.get('text', '')
        y = _check_y(c, y, ps, need=30)
        y = _draw_paragraphs(
            c, y, [text], ps=ps,
            color=ESMERALD_80, font_size=9, leading=13,
        )
        y -= 4

    elif block_type == 'list':
        items = block.get('items', [])
        ordered = block.get('ordered', False)
        y = _check_y(c, y, ps, need=30)
        texts = []
        for i, item in enumerate(items):
            txt = item.get('text', item) if isinstance(item, dict) else str(item)
            if ordered and not txt[0:3].replace('.', '').replace(')', '').strip().isdigit():
                txt = f'{i + 1}. {txt}'
            texts.append(txt)
        y = _draw_paragraphs(
            c, y, texts, ps=ps,
            color=ESMERALD_80, font_size=9, leading=13,
            x=MARGIN_L + 12,
            max_width=CONTENT_W - 12,
        )
        y -= 4

    elif block_type == 'separator':
        y = _draw_separator(c, y, ps)

    elif block_type == 'blockquote':
        text = block.get('text', '')
        y = _check_y(c, y, ps, need=30)
        y = _draw_blockquote(c, y, text, ps)

    elif block_type == 'code':
        text = block.get('text', '')
        y = _check_y(c, y, ps, need=40)
        y = _draw_code_block(c, y, text, ps)

    elif block_type == 'table':
        y = _check_y(c, y, ps, need=50)
        headers = block.get('headers', [])
        rows = block.get('rows', [])
        y = _draw_table(c, y, headers, rows, ps)

    return y


def _draw_title_page(c, y, params, ps):
    """Draw the contract title section on the first page."""
    c.setFont(_font('light'), 22)
    c.setFillColor(ESMERALD)
    c.drawString(MARGIN_L, y, 'CONTRATO DE PRESTACION')
    y -= 28
    c.drawString(MARGIN_L, y, 'DE SERVICIOS')
    y -= 36

    # Accent line
    c.setStrokeColor(LEMON)
    c.setLineWidth(2)
    c.line(MARGIN_L, y + 6, MARGIN_L + 80, y + 6)
    y -= 18

    # Party header
    c.setFont(_font('bold'), 10)
    c.setFillColor(ESMERALD)
    c.drawString(MARGIN_L, y, f'ENTRE: {params.get("client_full_name", "")} (EL CONTRATANTE)')
    y -= 16
    c.drawString(MARGIN_L, y, f'Y: {params.get("contractor_full_name", "")} (EL CONTRATISTA)')
    y -= 24

    contract_date = params.get('contract_date', '')
    if contract_date:
        c.setFont(_font('regular'), 9)
        c.setFillColor(GRAY_500)
        c.drawString(MARGIN_L, y, f'Fecha: {contract_date}')
        y -= 20

    return y


def _draw_signature_block(c, y, params, ps):
    """Draw the signature block at the bottom of the contract."""
    y = _check_y(c, y, ps, need=160)
    y -= 20

    c.setFont(_font('bold'), 11)
    c.setFillColor(ESMERALD)
    c.drawString(MARGIN_L, y, 'EN CONSTANCIA DE LO ANTERIOR,')
    y -= 14
    c.setFont(_font('regular'), 9)
    c.setFillColor(ESMERALD_80)
    c.drawString(
        MARGIN_L, y,
        'las partes firman el presente contrato en dos (2) ejemplares del mismo tenor.',
    )
    y -= 40

    col1_x = MARGIN_L
    col2_x = MARGIN_L + CONTENT_W / 2 + 10
    sig_width = CONTENT_W / 2 - 20

    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.6)
    c.line(col1_x, y, col1_x + sig_width, y)
    c.line(col2_x, y, col2_x + sig_width, y)
    y -= 14

    c.setFont(_font('bold'), 9)
    c.setFillColor(ESMERALD)
    c.drawString(col1_x, y, 'EL CONTRATANTE')
    c.drawString(col2_x, y, 'EL CONTRATISTA')
    y -= 14

    c.setFont(_font('regular'), 8)
    c.setFillColor(ESMERALD_80)
    c.drawString(col1_x, y, params.get('client_full_name', ''))
    c.drawString(col2_x, y, params.get('contractor_full_name', ''))
    y -= 12
    c.drawString(col1_x, y, f'C.C. {params.get("client_cedula", "")}')
    c.drawString(col2_x, y, f'C.C. {params.get("contractor_cedula", "")}')

    return y


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_contract_pdf(proposal) -> bytes | None:
    """Generate a contract PDF and return raw bytes, or None on failure."""
    try:
        raw_params = getattr(proposal, 'contract_params', None) or {}
        source = raw_params.get('contract_source', 'default')
        params = _build_params(raw_params)

        markdown_text = _get_contract_markdown(raw_params, params)
        if not markdown_text:
            logger.warning('Empty contract markdown for proposal %s', getattr(proposal, 'pk', '?'))
            return None

        blocks = markdown_to_blocks(markdown_text)

        _register_fonts()
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        ps = {'num': 1, 'client': params.get('client_full_name', '')}

        _draw_header_bar(c)
        y = PAGE_H - MARGIN_T

        # Title page (only for default contracts with param data)
        if source != 'custom':
            y = _draw_title_page(c, y, params, ps)

        # Render markdown blocks
        for block in blocks:
            block_type = block.get('type', '')
            if block_type in ('heading', 'section_header'):
                y -= 12
            y = _render_block(c, y, block, ps)

        # Signature block (only for default contracts)
        if source != 'custom':
            _draw_signature_block(c, y, params, ps)

        _draw_footer(c, ps['num'], client_name=ps['client'])
        c.save()
        return buf.getvalue()

    except Exception:
        logger.exception('Failed to generate contract PDF for proposal %s', getattr(proposal, 'pk', '?'))
        return None
