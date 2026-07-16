"""Tests for the linear context-diagnostic render (#112).

The section now flows full-width: paragraphs, optional opportunity block,
and the identified-challenges list rendered through the branded badge panel
(replacing the old two-column sidebar box and its tier logic).
"""
import io
from unittest.mock import patch

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.services.proposal_pdf_service import (
    MARGIN_T,
    PAGE_H,
    _register_fonts,
    _render_context_diagnostic,
)

pytestmark = pytest.mark.django_db

START_Y = 750
PS = {'num': 1, 'client': 'Test'}


@pytest.fixture
def pdf_canvas():
    _register_fonts()
    buf = io.BytesIO()
    return canvas.Canvas(buf, pagesize=A4)


def section_data(**overrides):
    data = {
        'index': '02',
        'title': 'Contexto y diagnóstico',
        'paragraphs': ['La operación depende de planillas manuales.'],
    }
    data.update(overrides)
    return data


class TestContextDiagnosticBadgePanel:
    def test_issues_render_through_the_badge_panel_with_custom_title(
        self, pdf_canvas,
    ):
        issues = ['Sin trazabilidad', 'Procesos duplicados']
        data = section_data(issues=issues, issuesTitle='Desafíos Identificados')

        with patch(
            'content.services.proposal_pdf_service._draw_badge_panel',
            return_value=300,
        ) as badge:
            result = _render_context_diagnostic(
                pdf_canvas, data, None, ps=PS, y=START_Y,
            )

        badge.assert_called_once()
        args = badge.call_args[0]
        assert args[2] == 'Desafíos Identificados'
        assert args[3] == issues
        assert result == 300

    def test_issues_title_defaults_to_problemas_identificados(self, pdf_canvas):
        data = section_data(issues=['Reprocesos'])

        with patch(
            'content.services.proposal_pdf_service._draw_badge_panel',
            return_value=280,
        ) as badge:
            _render_context_diagnostic(pdf_canvas, data, None, ps=PS, y=START_Y)

        assert badge.call_args[0][2] == 'Problemas Identificados'

    def test_without_issues_the_badge_panel_is_not_drawn(self, pdf_canvas):
        data = section_data()

        with patch(
            'content.services.proposal_pdf_service._draw_badge_panel',
        ) as badge:
            result = _render_context_diagnostic(
                pdf_canvas, data, None, ps=PS, y=START_Y,
            )

        badge.assert_not_called()
        assert badge.call_count == 0
        assert result <= START_Y


class TestContextDiagnosticOpportunity:
    def test_opportunity_renders_a_subtitle_with_the_default_title(
        self, pdf_canvas,
    ):
        data = section_data(opportunity='Digitalizar el flujo completo.')

        with patch(
            'content.services.proposal_pdf_service._draw_subtitle',
            return_value=500,
        ) as subtitle:
            _render_context_diagnostic(pdf_canvas, data, None, ps=PS, y=START_Y)

        subtitle.assert_called_once()
        assert subtitle.call_args[0][2] == 'La oportunidad'

    def test_without_opportunity_no_subtitle_is_drawn(self, pdf_canvas):
        data = section_data()

        with patch(
            'content.services.proposal_pdf_service._draw_subtitle',
        ) as subtitle:
            result = _render_context_diagnostic(
                pdf_canvas, data, None, ps=PS, y=START_Y,
            )

        subtitle.assert_not_called()
        assert subtitle.call_count == 0
        assert result <= START_Y


class TestContextDiagnosticLinearFlow:
    def test_full_section_with_default_y_returns_a_lower_numeric_y(
        self, pdf_canvas,
    ):
        data = section_data(
            opportunity='Digitalizar el flujo completo.',
            opportunityTitle='La oportunidad real',
            issues=['Sin trazabilidad', 'Reprocesos', 'Costos ocultos'],
            issuesTitle='Desafíos',
        )

        result = _render_context_diagnostic(
            pdf_canvas, data, None, ps=PS, y=None,
        )

        assert isinstance(result, (int, float))
        assert result < PAGE_H - MARGIN_T
