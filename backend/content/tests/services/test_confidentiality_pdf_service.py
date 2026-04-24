"""Tests for confidentiality_pdf_service: param building, substitution, block rendering, PDF generation."""
import io
import logging
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.models import ConfidentialityTemplate
from content.services.confidentiality_pdf_service import (
    _PARAM_KEYS,
    _PLACEHOLDER_BLANK,
    _PLACEHOLDER_DRAFT,
    _build_params,
    _get_markdown,
    _render_block,
    _substitute_placeholders,
    generate_confidentiality_pdf,
)
from content.services.pdf_utils import MARGIN_T, PAGE_H, _register_fonts

pytestmark = pytest.mark.django_db


# -- Helpers ------------------------------------------------------------------

def _make_diagnostic(params=None, pk=1):
    return SimpleNamespace(confidentiality_params=params, pk=pk, client=None)


def _make_canvas():
    _register_fonts()
    buf = io.BytesIO()
    return canvas.Canvas(buf, pagesize=A4)


def _make_ps():
    return {'num': 1, 'client': 'Test Client'}


def _default_template(markdown='Texto de prueba para {client_full_name}.'):
    return ConfidentialityTemplate.objects.create(
        name='Default NDA',
        content_markdown=markdown,
        is_default=True,
    )


# -- _build_params -----------------------------------------------------------

class TestBuildParams:
    def test_returns_defaults_when_raw_params_is_none(self):
        result = _build_params(None)
        assert set(result.keys()) == set(_PARAM_KEYS)

    def test_contractor_default_is_project_app_sas(self):
        result = _build_params(None)
        assert result['contractor_full_name'] == 'Project App SAS'

    def test_fills_blank_placeholder_for_unknown_key(self):
        result = _build_params({})
        assert result['client_full_name'] == _PLACEHOLDER_BLANK

    def test_preserves_provided_client_name(self):
        result = _build_params({'client_full_name': 'Ana Gómez'})
        assert result['client_full_name'] == 'Ana Gómez'

    def test_preserves_provided_cedula(self):
        result = _build_params({'client_cedula': '12345678'})
        assert result['client_cedula'] == '12345678'

    def test_draft_sets_all_values_to_draft_placeholder(self):
        result = _build_params(None, draft=True)
        assert all(v == _PLACEHOLDER_DRAFT for v in result.values())

    def test_draft_includes_all_param_keys(self):
        result = _build_params(None, draft=True)
        assert set(result.keys()) == set(_PARAM_KEYS)

    def test_draft_overrides_provided_params(self):
        result = _build_params({'client_full_name': 'Ana'}, draft=True)
        assert result['client_full_name'] == _PLACEHOLDER_DRAFT


# -- _substitute_placeholders ------------------------------------------------

class TestSubstitutePlaceholders:
    def test_replaces_known_key(self):
        result = _substitute_placeholders('Hola {client_full_name}.', {'client_full_name': 'Ana'})
        assert result == 'Hola Ana.'

    def test_falls_back_to_per_key_replacement_on_unknown_key(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = _substitute_placeholders(
                '{client_full_name} y {campo_desconocido}',
                {'client_full_name': 'Ana'},
            )
        assert 'Ana' in result

    def test_returns_text_unchanged_when_no_placeholders(self):
        result = _substitute_placeholders('Sin variables.', {})
        assert result == 'Sin variables.'

    def test_replaces_multiple_occurrences_of_same_key(self):
        result = _substitute_placeholders('{x} y {x}', {'x': 'Z'})
        assert result == 'Z y Z'


# -- _get_markdown -----------------------------------------------------------

class TestGetMarkdown:
    @pytest.fixture(autouse=True)
    def _clear_templates(self):
        ConfidentialityTemplate.objects.all().delete()

    def test_returns_empty_string_when_no_default_template(self):
        result = _get_markdown({'client_full_name': 'Ana'})
        assert result == ''

    def test_returns_substituted_markdown_when_template_exists(self):
        _default_template('Acuerdo con {client_full_name}.')
        result = _get_markdown({'client_full_name': 'Empresa XYZ'})
        assert 'Empresa XYZ' in result
        assert '{client_full_name}' not in result

    def test_normalises_double_dash_to_single_dash(self):
        _default_template('Plazo -- indefinido.')
        result = _get_markdown({})
        assert ' -- ' not in result
        assert ' - ' in result


# -- _render_block -----------------------------------------------------------

class TestRenderBlock:
    def setup_method(self):
        self.c = _make_canvas()
        self.y = PAGE_H - MARGIN_T
        self.ps = _make_ps()

    def _render(self, block):
        return _render_block(self.c, self.y, block, self.ps)

    def test_heading_level_1_returns_numeric_y(self):
        y = self._render({'type': 'heading', 'level': 1, 'text': 'Título principal'})
        assert isinstance(y, (int, float))

    def test_heading_level_2_returns_numeric_y(self):
        y = self._render({'type': 'heading', 'level': 2, 'text': 'Sección'})
        assert isinstance(y, (int, float))

    def test_heading_level_3_returns_numeric_y(self):
        y = self._render({'type': 'heading', 'level': 3, 'text': 'Subsección'})
        assert isinstance(y, (int, float))

    def test_paragraph_returns_numeric_y(self):
        y = self._render({'type': 'paragraph', 'text': 'Texto de prueba para el acuerdo.'})
        assert isinstance(y, (int, float))

    def test_ordered_list_returns_numeric_y(self):
        y = self._render({'type': 'list', 'ordered': True, 'items': ['Primero', 'Segundo']})
        assert isinstance(y, (int, float))

    def test_unordered_list_returns_numeric_y(self):
        y = self._render({'type': 'list', 'ordered': False, 'items': ['Alfa', 'Beta']})
        assert isinstance(y, (int, float))

    def test_blockquote_returns_numeric_y(self):
        y = self._render({'type': 'blockquote', 'text': 'Nota importante.'})
        assert isinstance(y, (int, float))

    def test_code_returns_numeric_y(self):
        y = self._render({'type': 'code', 'text': 'SELECT 1;', 'lang': 'sql'})
        assert isinstance(y, (int, float))

    def test_table_returns_numeric_y(self):
        y = self._render({
            'type': 'table',
            'headers': ['Columna A', 'Columna B'],
            'rows': [['Valor 1', 'Valor 2']],
        })
        assert isinstance(y, (int, float))

    def test_separator_returns_numeric_y(self):
        y = self._render({'type': 'separator'})
        assert isinstance(y, (int, float))

    def test_unknown_block_type_returns_y_unchanged(self):
        y = self._render({'type': 'unknown_xyz'})
        assert y == self.y


# -- generate_confidentiality_pdf --------------------------------------------

class TestGenerateConfidentialityPdf:
    @pytest.fixture(autouse=True)
    def _clear_templates(self):
        ConfidentialityTemplate.objects.all().delete()

    def test_returns_pdf_bytes_on_success(self):
        _default_template(
            '# Acuerdo\n\n'
            'Entre {client_full_name} y {contractor_full_name}.\n\n'
            'Ciudad: {contract_city}.',
        )
        diagnostic = _make_diagnostic({'client_full_name': 'Empresa SA', 'contract_city': 'Bogotá'})
        result = generate_confidentiality_pdf(diagnostic)
        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'

    def test_returns_none_when_no_template_exists(self):
        diagnostic = _make_diagnostic({'client_full_name': 'Empresa SA'})
        result = generate_confidentiality_pdf(diagnostic)
        assert result is None

    def test_returns_none_on_unexpected_exception(self):
        diagnostic = _make_diagnostic()
        with patch(
            'content.services.confidentiality_pdf_service._get_markdown',
            side_effect=RuntimeError('boom'),
        ):
            result = generate_confidentiality_pdf(diagnostic)
        assert result is None

    def test_draft_mode_returns_pdf_bytes(self):
        _default_template('Acuerdo para {client_full_name} en {contract_city}.')
        diagnostic = _make_diagnostic()
        result = generate_confidentiality_pdf(diagnostic, draft=True)
        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'
