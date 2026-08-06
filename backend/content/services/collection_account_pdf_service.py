"""
Generate a branded PDF for collection account documents from relational data.
"""
import io
import logging
import textwrap

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.services.collection_account_service import is_collection_account
from content.services.pdf_utils import (
    ESMERALD,
    GRAY_500,
    GREEN_LIGHT,
    LEMON,
    MARGIN_B,
    MARGIN_L,
    MARGIN_R,
    MARGIN_T,
    PAGE_H,
    PAGE_W,
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


def _ident_line(id_type, number):
    """'NIT 901234567' / 'C.C. 12345678' / bare number when untyped."""
    if not number:
        return ''
    label = _IDENT_LABELS.get((id_type or '').upper(), id_type or '')
    return f'{label} {number}'.strip()


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
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            page_num = 1
            y = PAGE_H - MARGIN_T

            def ensure_space(need):
                nonlocal y, page_num
                if y - need >= MARGIN_B:
                    return
                _draw_footer(c, page_num, client_name=ext.customer_name or '')
                c.showPage()
                page_num += 1
                _draw_header_bar(c)
                y = PAGE_H - MARGIN_T

            _draw_header_bar(c)

            c.setFont(_font('bold'), 16)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, 'Cuenta de cobro')
            y -= 22
            c.setFont(_font('regular'), 10)
            c.setFillColor(GRAY_500)
            num = document.public_number or f'#{document.id}'
            c.drawString(MARGIN_L, y, num)
            y -= 28

            c.setFont(_font('medium'), 11)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, document.title)
            y -= 20

            def line(label, value):
                nonlocal y
                ensure_space(40)
                c.setFont(_font('bold'), 9)
                c.setFillColor(GREEN_LIGHT)
                c.drawString(MARGIN_L, y, label)
                y -= 12
                c.setFont(_font('regular'), 9)
                c.setFillColor(GRAY_500)
                for chunk in str(value or '').split('\n'):
                    ensure_space(20)
                    c.drawString(MARGIN_L, y, chunk[:120])
                    y -= 12
                y -= 6

            if document.issue_date:
                line('Fecha de emisión', format_date_es(document.issue_date))
            if document.due_date:
                line('Fecha de vencimiento', format_date_es(document.due_date))
            if document.city:
                line('Ciudad', document.city)

            y -= 8
            ensure_space(60)
            c.setFont(_font('bold'), 10)
            c.setFillColor(LEMON)
            c.drawString(MARGIN_L, y, 'Pagador')
            y -= 14
            c.setFont(_font('regular'), 9)
            c.setFillColor(GRAY_500)
            for t in (
                ext.payer_name,
                _ident_line(ext.payer_identification_type, ext.payer_identification),
                ext.payer_address,
                ext.payer_phone,
                ext.payer_email,
            ):
                if t:
                    ensure_space(16)
                    c.drawString(MARGIN_L, y, str(t)[:100])
                    y -= 12
            y -= 8

            ensure_space(60)
            c.setFont(_font('bold'), 10)
            c.setFillColor(LEMON)
            c.drawString(MARGIN_L, y, 'Cliente')
            y -= 14
            c.setFont(_font('regular'), 9)
            c.setFillColor(GRAY_500)
            for t in (
                ext.customer_name,
                _ident_line(
                    ext.customer_identification_type, ext.customer_identification,
                ),
                ext.customer_contact_name,
                ext.customer_email,
                ext.customer_address,
            ):
                if t:
                    ensure_space(16)
                    c.drawString(MARGIN_L, y, str(t)[:100])
                    y -= 12
            y -= 8

            if ext.billing_concept:
                line('Concepto de cobro', ext.billing_concept)

            y -= 10
            ensure_space(80)
            c.setFont(_font('bold'), 10)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, 'Detalle')
            y -= 16

            c.setFont(_font('bold'), 8)
            c.drawString(MARGIN_L, y, 'Descripción')
            c.drawRightString(PAGE_W - MARGIN_R - 80, y, 'Cant.')
            c.drawRightString(PAGE_W - MARGIN_R, y, 'Total')
            y -= 10
            c.line(MARGIN_L, y, PAGE_W - MARGIN_R, y)
            y -= 12

            c.setFont(_font('regular'), 8)
            for item in document.items.all().order_by('position', 'id'):
                ensure_space(20)
                desc = (item.description or '')[:70]
                c.drawString(MARGIN_L, y, desc)
                c.drawRightString(PAGE_W - MARGIN_R - 80, y, str(item.quantity))
                c.drawRightString(
                    PAGE_W - MARGIN_R, y, _format_cop(item.line_total),
                )
                y -= 14

            y -= 12
            ensure_space(50)
            c.setFont(_font('bold'), 9)
            c.drawRightString(
                PAGE_W - MARGIN_R, y,
                f'Subtotal: {_format_cop(document.subtotal)}',
            )
            y -= 12
            c.drawRightString(
                PAGE_W - MARGIN_R, y,
                f'Impuestos: {_format_cop(document.tax_total)}',
            )
            y -= 12
            c.drawRightString(
                PAGE_W - MARGIN_R, y,
                f'Total ({document.currency}): {_format_cop(document.total)}',
            )
            y -= 14

            words = amount_in_words_es(document.total)
            if words:
                c.setFont(_font('regular'), 8)
                c.setFillColor(GRAY_500)
                for chunk in textwrap.wrap(f'Son: {words}', 95):
                    ensure_space(16)
                    c.drawString(MARGIN_L, y, chunk)
                    y -= 11
            y -= 13

            pms = list(document.payment_methods.all())
            if pms:
                ensure_space(40)
                c.setFont(_font('bold'), 10)
                c.setFillColor(ESMERALD)
                c.drawString(MARGIN_L, y, 'Formas de pago')
                y -= 16
                c.setFont(_font('regular'), 8)
                c.setFillColor(GRAY_500)
                for pm in pms:
                    ensure_space(20)
                    block = ' | '.join(
                        filter(
                            None,
                            [
                                pm.get_payment_method_type_display(),
                                pm.bank_name,
                                pm.account_number,
                                (pm.payment_instructions[:80] if pm.payment_instructions else ''),
                            ],
                        ),
                    )
                    c.drawString(MARGIN_L, y, block[:110])
                    y -= 12

            # Signature block: line + issuer name/identification. What makes
            # the document a valid cuenta de cobro alongside the amounts.
            ensure_space(96)
            y -= 42
            c.setStrokeColor(GRAY_500)
            c.line(MARGIN_L, y, MARGIN_L + 200, y)
            y -= 12
            c.setFont(_font('regular'), 9)
            c.setFillColor(GRAY_500)
            if ext.payer_name:
                c.drawString(MARGIN_L, y, str(ext.payer_name)[:100])
                y -= 12
            payer_ident = _ident_line(
                ext.payer_identification_type, ext.payer_identification,
            )
            if payer_ident:
                c.drawString(MARGIN_L, y, payer_ident[:100])
                y -= 12
            c.setFont(_font('bold'), 8)
            c.setFillColor(GREEN_LIGHT)
            c.drawString(MARGIN_L, y, 'Firma')

            _draw_footer(c, page_num, client_name=ext.customer_name or '')
            c.save()
            out = buf.getvalue()
            buf.close()
            return out
        except Exception:
            logger.exception('Collection account PDF failed for document %s', document.id)
            return None
