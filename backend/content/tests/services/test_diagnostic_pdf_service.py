"""Tests for DiagnosticPdfService and its per-section renderers."""

import io
from unittest.mock import MagicMock, patch

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.services.diagnostic_pdf_service import (
    DiagnosticPdfService,
    _draw_cover,
    _render_categories,
    _render_cost,
    _render_delivery_structure,
    _render_executive_summary,
    _render_purpose,
    _render_radiography,
    _render_scope,
    _render_timeline,
)
from content.services.pdf_utils import MARGIN_T, PAGE_H, _register_fonts


# -- Canvas helper fixture ---------------------------------------------------


@pytest.fixture
def pdf_canvas():
    """Return a blank reportlab canvas suitable for renderer calls."""
    _register_fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    return c


@pytest.fixture
def mock_diagnostic():
    """Lightweight mock diagnostic for renderer tests that avoids DB access."""
    d = MagicMock()
    d.client_name = 'Acme Corp'
    d.title = 'Web App Diagnostic'
    d.created_at = None
    d.investment_amount = None
    d.currency = 'COP'
    d.payment_terms = {}
    d.duration_label = ''
    return d


# -- DiagnosticPdfService.generate() -----------------------------------------


@pytest.mark.django_db
def test_generate_returns_bytes_for_diagnostic_with_all_sections_enabled(diagnostic):
    result = DiagnosticPdfService.generate(diagnostic)
    assert isinstance(result, bytes)
    assert len(result) > 100


@pytest.mark.django_db
@patch('content.services.diagnostic_pdf_service.canvas.Canvas', side_effect=Exception('canvas fail'))
def test_generate_returns_none_when_canvas_creation_raises(_mock_canvas, diagnostic):
    result = DiagnosticPdfService.generate(diagnostic)
    assert result is None


@pytest.mark.django_db
def test_generate_returns_bytes_when_all_sections_are_disabled(diagnostic):
    diagnostic.sections.all().update(is_enabled=False)
    result = DiagnosticPdfService.generate(diagnostic)
    assert isinstance(result, bytes)


@pytest.mark.django_db
def test_generate_only_renders_enabled_sections(diagnostic):
    diagnostic.sections.exclude(section_type='purpose').update(is_enabled=False)
    result = DiagnosticPdfService.generate(diagnostic)
    assert isinstance(result, bytes)


# -- _draw_cover -------------------------------------------------------------


def test_draw_cover_renders_short_client_name_without_error(pdf_canvas, mock_diagnostic):
    mock_diagnostic.client_name = 'Acme'
    _draw_cover(pdf_canvas, mock_diagnostic)  # must not raise


def test_draw_cover_wraps_long_client_name(pdf_canvas, mock_diagnostic):
    mock_diagnostic.client_name = 'Very Long Client Company Name That Exceeds Limit'
    _draw_cover(pdf_canvas, mock_diagnostic)  # must not raise — triggers textwrap branch


def test_draw_cover_handles_empty_client_name(pdf_canvas, mock_diagnostic):
    mock_diagnostic.client_name = ''
    mock_diagnostic.title = ''
    _draw_cover(pdf_canvas, mock_diagnostic)  # must not raise


# -- _render_purpose ---------------------------------------------------------


def test_render_purpose_skips_scope_note_when_absent(pdf_canvas, mock_diagnostic):
    data = {'paragraphs': ['Intro paragraph.'], 'scopeNote': None}
    y_before = PAGE_H - MARGIN_T
    y_after = _render_purpose(pdf_canvas, y_before, data, mock_diagnostic, {'num': 2, 'client': ''})
    assert y_after <= y_before


def test_render_purpose_includes_scope_note_when_present(pdf_canvas, mock_diagnostic):
    data = {
        'paragraphs': ['Intro.'],
        'scopeNote': 'This is the scope of the diagnostic.',
        'severityLevels': [],
    }
    y_before = PAGE_H - MARGIN_T
    y_after = _render_purpose(pdf_canvas, y_before, data, mock_diagnostic, {'num': 2, 'client': ''})
    assert y_after < y_before


def test_render_purpose_includes_severity_levels_when_present(pdf_canvas, mock_diagnostic):
    data = {
        'paragraphs': [],
        'severityLevels': [{'level': 'Crítico', 'meaning': 'Afecta disponibilidad'}],
    }
    y_before = PAGE_H - MARGIN_T
    y_after = _render_purpose(pdf_canvas, y_before, data, mock_diagnostic, {'num': 2, 'client': ''})
    assert y_after <= y_before


# -- _render_executive_summary -----------------------------------------------


def test_render_executive_summary_skips_counts_when_empty(pdf_canvas, mock_diagnostic):
    data = {'intro': 'Summary intro.', 'severityCounts': {}, 'highlights': []}
    y_before = PAGE_H - MARGIN_T
    y_after = _render_executive_summary(pdf_canvas, y_before, data, mock_diagnostic, {'num': 2, 'client': ''})
    assert y_after < y_before


def test_render_executive_summary_renders_severity_counts(pdf_canvas, mock_diagnostic):
    data = {
        'intro': 'Summary intro.',
        'severityCounts': {'critico': 2, 'alto': 3, 'medio': 5, 'bajo': 1},
        'narrative': 'Overall the application is stable.',
        'highlights': ['Highlight one', 'Highlight two'],
    }
    y_before = PAGE_H - MARGIN_T
    y_after = _render_executive_summary(pdf_canvas, y_before, data, mock_diagnostic, {'num': 2, 'client': ''})
    assert y_after < y_before


# -- _render_cost ------------------------------------------------------------


def test_render_cost_skips_payment_description_when_absent(pdf_canvas, mock_diagnostic):
    data = {'paymentDescription': []}
    y_before = PAGE_H - MARGIN_T
    y_after = _render_cost(pdf_canvas, y_before, data, mock_diagnostic, {'num': 2, 'client': ''})
    assert y_after <= y_before


def test_render_cost_renders_payment_description_bullets(pdf_canvas, mock_diagnostic):
    mock_diagnostic.investment_amount = 5000000
    mock_diagnostic.currency = 'COP'
    mock_diagnostic.payment_terms = {'initial_pct': 50, 'final_pct': 50}
    data = {
        'paymentDescription': [
            {'label': 'Anticipo', 'detail': 'Al firmar contrato'},
            {'label': 'Saldo', 'detail': 'Al entregar'},
        ],
        'note': 'Precios incluyen IVA.',
    }
    y_before = PAGE_H - MARGIN_T
    y_after = _render_cost(pdf_canvas, y_before, data, mock_diagnostic, {'num': 2, 'client': ''})
    assert y_after < y_before


# -- _render_categories ------------------------------------------------------


def test_render_categories_renders_recommendations(pdf_canvas, mock_diagnostic):
    data = {
        'categories': [
            {
                'title': 'Seguridad',
                'description': 'Análisis de seguridad.',
                'strengths': ['HTTPS habilitado'],
                'findings': [{'level': 'alto', 'title': 'Sin WAF', 'detail': 'Vulnerable'}],
                'recommendations': [{'level': 'alto', 'title': 'Implementar WAF', 'detail': ''}],
            }
        ]
    }
    y_before = PAGE_H - MARGIN_T
    y_after = _render_categories(pdf_canvas, y_before, data, mock_diagnostic, {'num': 2, 'client': ''})
    assert y_after < y_before


# -- _render_timeline --------------------------------------------------------


def test_render_timeline_renders_distribution(pdf_canvas, mock_diagnostic):
    mock_diagnostic.duration_label = '8 semanas'
    data = {
        'distribution': [
            {'dayRange': 'Semana 1-2', 'description': 'Análisis inicial'},
            {'dayRange': 'Semana 3-8', 'description': 'Implementación'},
        ]
    }
    y_before = PAGE_H - MARGIN_T
    y_after = _render_timeline(pdf_canvas, y_before, data, mock_diagnostic, {'num': 2, 'client': ''})
    assert y_after < y_before


# -- _render_scope -----------------------------------------------------------


def test_render_scope_renders_considerations(pdf_canvas, mock_diagnostic):
    data = {'considerations': ['El alcance no incluye soporte post-entrega.', 'Sin mantenimiento']}
    y_before = PAGE_H - MARGIN_T
    y_after = _render_scope(pdf_canvas, y_before, data, mock_diagnostic, {'num': 2, 'client': ''})
    assert y_after < y_before
