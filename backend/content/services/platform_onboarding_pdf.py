"""
Branded PDF: step-by-step platform guide for clients after proposal acceptance.
Uses shared pdf_utils (header/footer/fonts) like technical_document_pdf.
"""

from __future__ import annotations

import io
import logging

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.services.pdf_utils import (
    ESMERALD,
    GRAY_500,
    MARGIN_L,
    MARGIN_T,
    PAGE_H,
    PAGE_W,
    _draw_footer,
    _draw_header_bar,
    _draw_paragraphs,
    _font,
    _register_fonts,
    _safe,
    _strip_emoji,
)

logger = logging.getLogger(__name__)


def generate_platform_onboarding_pdf(
    *,
    client_name: str = '',
    client_email: str = '',
    project_name: str = '',
    deliverable_title: str = '',
    platform_login_url: str = '',
) -> bytes | None:
    """
    Build a short instructional PDF. Returns PDF bytes or None on error.
    """
    try:
        _register_fonts()
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setTitle(_strip_emoji('Guía de la plataforma — Project App'))
        c.setAuthor('Project App')

        page_num = 1
        y = PAGE_H - MARGIN_T
        _draw_header_bar(c)

        def new_page():
            nonlocal y, page_num
            _draw_footer(c, page_num, client_name=_strip_emoji(client_name) or 'Cliente')
            c.showPage()
            page_num += 1
            _draw_header_bar(c)
            y = PAGE_H - MARGIN_T

        c.setFont(_font('light'), 26)
        c.setFillColor(ESMERALD)
        title = _strip_emoji('Guía de uso — Plataforma cliente')
        c.drawString(MARGIN_L, y, _safe(title[:80]))
        y -= 36

        c.setFont(_font('regular'), 11)
        c.setFillColor(GRAY_500)
        meta_parts = []
        if client_name:
            meta_parts.append(f'Cliente: {_strip_emoji(client_name)}')
        if project_name:
            meta_parts.append(f'Proyecto: {_strip_emoji(project_name)}')
        if deliverable_title:
            meta_parts.append(f'Entregable: {_strip_emoji(deliverable_title)}')
        if meta_parts:
            block = '  |  '.join(meta_parts)
            y = _draw_paragraphs(c, y, [block], font_size=10, color=GRAY_500)
            y -= 8

        sections: list[tuple[str, list[str]]] = [
            (
                '1. Acceso',
                [
                    f'Ingresa a la plataforma en: {platform_login_url or "(URL configurada por tu administrador)"}',
                    'Usa el correo con el que te registramos. Si es tu primer acceso, '
                    'completa la verificación y define tu contraseña cuando el sistema te lo pida.',
                ],
            ),
            (
                '2. Proyectos y entregables',
                [
                    'En el panel verás tus proyectos. Cada proyecto contiene entregables: '
                    'bloques de trabajo con documentos, propuesta comercial vinculada y requisitos.',
                    'Abre un entregable para ver PDFs, anexos y el tablero de requerimientos asociado.',
                ],
            ),
            (
                '3. Tablero (Kanban)',
                [
                    'Las tarjetas representan requisitos. Puedes moverlas según las reglas del proyecto; '
                    'en la columna de aprobación podrás confirmar entregas cuando corresponda.',
                ],
            ),
            (
                '4. Documentos',
                [
                    'Descarga la propuesta comercial y el detalle técnico cuando estén disponibles en el entregable.',
                    'También encontrarás contratos, anexos y cuentas de cobro en la misma vista de documentos.',
                    'Puedes subir PDFs en la sección indicada para aportes del cliente.',
                ],
            ),
            (
                '5. Soporte',
                [
                    'Ante dudas, responde al correo de tu proyecto o contacta a tu ejecutivo en Project App.',
                ],
            ),
        ]

        for heading, paras in sections:
            if y < 120:
                new_page()
            c.setFont(_font('bold'), 13)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, _safe(_strip_emoji(heading)))
            y -= 22
            c.setFont(_font('regular'), 10)
            c.setFillColor(GRAY_500)
            for p in paras:
                if y < 100:
                    new_page()
                y = _draw_paragraphs(c, y, [_strip_emoji(p)], font_size=10, color=GRAY_500)
                y -= 6
            y -= 10

        if client_email:
            if y < 80:
                new_page()
            c.setFont(_font('medium'), 10)
            c.setFillColor(ESMERALD)
            y = _draw_paragraphs(
                c, y,
                [f'Correo de contacto en plataforma: {client_email}'],
                font_size=10,
                color=GRAY_500,
            )

        _draw_footer(c, page_num, client_name=_strip_emoji(client_name) or 'Cliente')
        c.save()
        return buf.getvalue()
    except Exception:
        logger.exception('platform onboarding PDF generation failed')
        return None
