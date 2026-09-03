"""Branded, populated draft PDF for an administrative financing addendum."""

import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from content.services.contract_pdf_service import _render_block
from content.services.financing_agreement_service import resolve_agreement_markdown
from content.services.markdown_parser import markdown_to_blocks
from content.services.pdf_utils import (
    MARGIN_T,
    PAGE_H,
    PAGE_W,
    _draw_footer,
    _draw_header_bar,
    _font,
    _register_fonts,
)


class _DraftWatermarkCanvas(canvas.Canvas):
    """Paint the draft warning on every page immediately before emission."""

    def showPage(self):
        self.saveState()
        try:
            self.setFillAlpha(0.10)
        except AttributeError:
            pass
        self.setFillColor(HexColor('#64748B'))
        self.setFont('Helvetica-Bold', 44)
        self.translate(PAGE_W / 2, PAGE_H / 2)
        self.rotate(35)
        self.drawCentredString(0, 0, 'BORRADOR · SIN FIRMA')
        self.setFont('Helvetica-Bold', 11)
        self.drawCentredString(0, -28, 'REVISIÓN JURÍDICA PENDIENTE')
        self.restoreState()
        super().showPage()


class FinancingAgreementPdfService:
    @classmethod
    def build_draft(cls, agreement):
        markdown_text = (
            agreement.resolved_contract_markdown
            if agreement.resolved_contract_markdown
            else resolve_agreement_markdown(
                agreement,
                draft=True,
                require_core=False,
            )
        )
        blocks = markdown_to_blocks(markdown_text)

        _register_fonts()
        buffer = io.BytesIO()
        pdf = _DraftWatermarkCanvas(buffer, pagesize=A4)
        page_state = {
            'num': 1,
            'client': agreement.client_full_name,
        }
        _draw_header_bar(pdf)
        y = PAGE_H - MARGIN_T

        pdf.setFont(_font('regular'), 8)
        pdf.setFillColor(HexColor('#64748B'))
        pdf.drawString(48, y, 'Documento administrativo poblado · no apto para firma')
        y -= 26

        for block in blocks:
            if block.get('type') in ('heading', 'section_header'):
                y -= 8
            y = _render_block(pdf, y, block, page_state)

        _draw_footer(
            pdf,
            page_state['num'],
            client_name=agreement.client_full_name,
        )
        pdf.save()
        return buffer.getvalue()
