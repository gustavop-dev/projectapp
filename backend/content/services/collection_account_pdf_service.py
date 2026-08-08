"""
Generate a branded PDF for collection account documents from relational data.

The page is cut to its content instead of forcing an A4 sheet: we bill three
concepts (development, diagnostics, hosting), never by units and never with
itemised taxes, so an A4 cuenta de cobro was half empty. Width is fixed at A5
(148mm) and the height comes from measuring the content — see `generate`.
"""
import io
import logging

from reportlab.lib.pagesizes import A5
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from content.services.collection_account_service import is_collection_account
from content.services.pdf_utils import (
    ESMERALD,
    GRAY_700,
    _draw_footer,
    _draw_header_bar,
    _font,
    _format_cop,
    _register_fonts,
    amount_in_words_es,
    format_date_es,
)

logger = logging.getLogger(__name__)

_IDENT_LABELS = {'NIT': 'NIT', 'CC': 'C.C.'}

# ── Page geometry ────────────────────────────────────────────
# Local on purpose: PAGE_W/PAGE_H in pdf_utils are shared by every other
# generator (proposals, contracts, technical docs) and must stay A4.
PAGE_W = A5[0]                      # 419.5pt ≈ 148mm
MARGIN_X = 36                       # 48 suited 595pt of width, not 420
MARGIN_TOP = 44
MARGIN_BOTTOM = 40
CONTENT_W = PAGE_W - 2 * MARGIN_X   # ≈ 348pt

# Measuring canvas: never saved, so ReportLab does not care that this is far
# beyond the format's real limit. It only has to be taller than any content.
_PROBE_H = 200_000
# A PDF page cannot exceed 14400pt a side. Past that we fall back to paging.
_MAX_PAGE_H = 14400

_AMOUNT_COL_W = 70                  # room for "$1.490.000" at 8pt


def _ident_line(id_type, number):
    """'NIT 901234567' / 'C.C. 12345678' / bare number when untyped."""
    if not number:
        return ''
    label = _IDENT_LABELS.get((id_type or '').upper(), id_type or '')
    return f'{label} {number}'.strip()


def _wrap(text, style, size, width):
    """Split *text* into lines that fit *width*, measured in the real font.

    Replaces the old fixed character truncation, which silently dropped text
    and was calibrated for A4's wider column.
    """
    return simpleSplit(str(text or ''), _font(style), size, width)


class CollectionAccountPdfService:
    """Build PDF bytes from a Document with collection_account extension."""

    @classmethod
    def generate(cls, document):
        if not is_collection_account(document):
            logger.warning('Document %s is not a collection account', document.id)
            return None
        ext = getattr(document, 'collection_account', None)
        if ext is None:
            logger.warning('Document %s has no collection_account row', document.id)
            return None

        try:
            _register_fonts()

            # Two passes. The layout is a chain of relative `y` decrements, so
            # the height it consumes does not depend on where it starts — draw
            # it once on a throwaway tall canvas to measure, then for real on a
            # page cut to exactly that. Nothing from the first pass is kept.
            probe = canvas.Canvas(io.BytesIO(), pagesize=(PAGE_W, _PROBE_H))
            content_h = _PROBE_H - cls._draw(probe, document, ext, _PROBE_H)
            page_h = min(_MAX_PAGE_H, content_h + MARGIN_BOTTOM)

            # The page was cut to fit, so paging is off for the real pass:
            # `ensure_space` reserves a rounded-up estimate and would break a
            # phantom second page on the last line. It stays on only when the
            # content did not fit the format's maximum page height.
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=(PAGE_W, page_h))
            cls._draw(c, document, ext, page_h, paginate=page_h >= _MAX_PAGE_H)
            c.save()
            out = buf.getvalue()
            buf.close()
            return out
        except Exception:
            logger.exception('Collection account PDF failed for document %s', document.id)
            return None

    @classmethod
    def _draw(cls, c, document, ext, page_h, paginate=True):
        """Render the whole document; return the `y` where the content ended.

        Called twice by `generate` — once to measure, once for real.
        """
        page_num = 1
        y = page_h - MARGIN_TOP
        right_x = PAGE_W - MARGIN_X

        def footer():
            _draw_footer(
                c, page_num, client_name=ext.customer_name or '',
                page_w=PAGE_W, margin_x=MARGIN_X, margin_b=MARGIN_BOTTOM,
            )

        def ensure_space(need):
            """Page break valve. Off on a page cut to content — it only fires
            for a document too tall for the PDF format itself."""
            nonlocal y, page_num
            if not paginate or y - need >= MARGIN_BOTTOM:
                return
            footer()
            c.showPage()
            page_num += 1
            _draw_header_bar(c, page_w=PAGE_W, page_h=page_h)
            y = page_h - MARGIN_TOP

        def paragraph(text, style, size, color, leading, width=CONTENT_W):
            """Draw wrapped text at the left margin."""
            nonlocal y
            c.setFont(_font(style), size)
            c.setFillColor(color)
            for chunk in _wrap(text, style, size, width):
                ensure_space(leading + 4)
                c.drawString(MARGIN_X, y, chunk)
                y -= leading

        _draw_header_bar(c, page_w=PAGE_W, page_h=page_h)

        c.setFont(_font('bold'), 16)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_X, y, 'Cuenta de cobro')
        y -= 20
        c.setFont(_font('regular'), 10)
        c.setFillColor(GRAY_700)
        c.drawString(MARGIN_X, y, document.public_number or f'#{document.id}')
        y -= 24

        # The stored title is "Cuenta de cobro — <concepto>", so printing it
        # whole repeats the heading right under itself. The concepto alone is
        # the part that carries information.
        paragraph(
            ext.billing_concept or document.title,
            'medium', 11, ESMERALD, 14,
        )
        y -= 8

        def field(label, value):
            nonlocal y
            ensure_space(34)
            c.setFont(_font('bold'), 9)
            c.setFillColor(GRAY_700)
            c.drawString(MARGIN_X, y, label)
            y -= 12
            paragraph(value, 'regular', 9, GRAY_700, 12)
            y -= 6

        if document.issue_date:
            field('Fecha de emisión', format_date_es(document.issue_date))
        if document.due_date:
            field('Fecha de vencimiento', format_date_es(document.due_date))
        if document.city:
            field('Ciudad', document.city)

        def party(label, values):
            """A party block. The heading was LEMON (#F0FF3D), a colour meant
            for the dark header bar — about 1.2:1 against white, so it read as
            blank. Brand green instead."""
            nonlocal y
            y -= 8
            ensure_space(52)
            c.setFont(_font('bold'), 10)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_X, y, label)
            y -= 14
            for value in values:
                if value:
                    paragraph(value, 'regular', 9, GRAY_700, 12)
            y -= 8

        # "Pagador" printed the issuer's own data (see _fill_payer_from_issuer);
        # the party who pays is the client, below.
        party('Emisor', (
            ext.payer_name,
            _ident_line(ext.payer_identification_type, ext.payer_identification),
            ext.payer_address,
            ext.payer_phone,
            ext.payer_email,
        ))
        party('Cliente', (
            ext.customer_name,
            _ident_line(
                ext.customer_identification_type, ext.customer_identification,
            ),
            ext.customer_contact_name,
            ext.customer_email,
            ext.customer_address,
        ))

        y -= 2
        ensure_space(60)
        c.setFont(_font('bold'), 10)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_X, y, 'Detalle')
        y -= 16

        # No "Cant." column: nothing here is billed by units.
        c.setFont(_font('bold'), 8)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_X, y, 'Descripción')
        c.drawRightString(right_x, y, 'Total')
        y -= 10
        c.setStrokeColor(GRAY_700)
        c.setLineWidth(0.4)
        c.line(MARGIN_X, y, right_x, y)
        y -= 12

        desc_w = CONTENT_W - _AMOUNT_COL_W - 10
        for item in document.items.all().order_by('position', 'id'):
            chunks = _wrap(item.description, 'regular', 8, desc_w) or ['']
            ensure_space(11 * len(chunks) + 6)
            amount = _format_cop(item.line_total)
            for index, chunk in enumerate(chunks):
                c.setFont(_font('regular'), 8)
                c.setFillColor(GRAY_700)
                c.drawString(MARGIN_X, y, chunk)
                if index == 0:
                    c.drawRightString(right_x, y, amount)
                y -= 11
            y -= 3

        # Only the Total: nothing carries itemised tax, so Subtotal always
        # repeated this same figure.
        y -= 9
        ensure_space(34)
        c.setFont(_font('bold'), 10)
        c.setFillColor(ESMERALD)
        c.drawRightString(
            right_x, y,
            f'Total ({document.currency}): {_format_cop(document.total)}',
        )
        y -= 16

        words = amount_in_words_es(document.total)
        if words:
            paragraph(f'Son: {words}', 'regular', 8, GRAY_700, 11)
        y -= 10

        pms = list(document.payment_methods.all())
        if pms:
            ensure_space(38)
            c.setFont(_font('bold'), 10)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_X, y, 'Formas de pago')
            y -= 16
            for pm in pms:
                block = ' | '.join(
                    filter(
                        None,
                        [
                            pm.get_payment_method_type_display(),
                            pm.bank_name,
                            pm.account_number,
                            pm.payment_instructions or '',
                        ],
                    ),
                )
                paragraph(block, 'regular', 8, GRAY_700, 11)
                y -= 3

        footer()
        return y
