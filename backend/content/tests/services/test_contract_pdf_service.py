"""Tests for contract_pdf_service: parameter building, placeholder substitution, PDF generation."""
import io
import logging
import re
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

from content.services.contract_pdf_service import (
    _build_params,
    _draw_title_page,
    _render_block,
    _substitute_placeholders,
    generate_contract_pdf,
)
from content.services.pdf_utils import MARGIN_T, PAGE_H

pytestmark = pytest.mark.django_db


# Keys that _build_params() returns but are NOT used inside the markdown
# template (e.g. consumed only by _draw_title_page).
_TEMPLATE_EXEMPT_KEYS = {'contract_date'}


class TestBuildParams:
    def test_returns_defaults_for_empty_dict(self):
        result = _build_params({})
        assert result['contractor_full_name'] == '_______________'
        assert result['bank_account_type'] == 'Ahorros'
        assert result['contract_city'] == 'Medellín'

    def test_uses_provided_values(self):
        result = _build_params({
            'contractor_full_name': 'Carlos',
            'client_cedula': '123456',
        })
        assert result['contractor_full_name'] == 'Carlos'
        assert result['client_cedula'] == '123456'

    def test_fills_blanks_for_missing_keys(self):
        result = _build_params({'contractor_full_name': 'Carlos'})
        assert result['client_full_name'] == '_______________'
        assert result['contractor_email'] == '_______________'


class TestSubstitutePlaceholders:
    def test_replaces_known_placeholders(self):
        template = 'Hello {client_full_name}, CC {client_cedula}'
        params = {'client_full_name': 'Ana', 'client_cedula': '123'}
        result = _substitute_placeholders(template, params)
        assert result == 'Hello Ana, CC 123'

    def test_falls_back_on_unknown_placeholder(self, caplog):
        template = 'Hello {client_full_name} {unknown_field}'
        params = {'client_full_name': 'Ana'}
        with caplog.at_level(logging.WARNING):
            result = _substitute_placeholders(template, params)
        assert 'Ana' in result
        assert 'unknown_field' in caplog.text or '{unknown_field}' in result

    def test_handles_empty_template(self):
        assert _substitute_placeholders('', {'key': 'val'}) == ''


class TestGenerateContractPdf:
    @patch('content.services.contract_pdf_service._register_fonts')
    def test_returns_bytes_for_default_source(self, mock_fonts, contract_template):
        proposal = SimpleNamespace(
            contract_params={
                'contract_source': 'default',
                'client_full_name': 'Test Client',
                'client_cedula': '123456',
                'contractor_full_name': 'Contractor',
                'contractor_cedula': '654321',
                'contract_date': '2026-04-02',
            },
            pk=1,
        )
        result = generate_contract_pdf(proposal)
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0

    @patch('content.services.contract_pdf_service._register_fonts')
    def test_returns_bytes_for_custom_source(self, mock_fonts):
        proposal = SimpleNamespace(
            contract_params={
                'contract_source': 'custom',
                'custom_contract_markdown': '# Custom Contract\n\nThis is a custom contract.',
            },
            pk=2,
        )
        result = generate_contract_pdf(proposal)
        assert result is not None
        assert isinstance(result, bytes)

    def test_returns_none_when_no_default_template(self, db):
        from content.models import ContractTemplate
        ContractTemplate.objects.all().update(is_default=False)
        proposal = SimpleNamespace(
            contract_params={'contract_source': 'default'},
            pk=3,
        )
        result = generate_contract_pdf(proposal)
        assert result is None

    def test_returns_none_when_custom_markdown_empty(self):
        proposal = SimpleNamespace(
            contract_params={
                'contract_source': 'custom',
                'custom_contract_markdown': '',
            },
            pk=4,
        )
        result = generate_contract_pdf(proposal)
        assert result is None


class TestDraftMode:
    """generate_contract_pdf(proposal, draft=True) omits the signature block."""

    @patch('content.services.contract_pdf_service._draw_signature_block')
    @patch('content.services.contract_pdf_service._register_fonts')
    def test_draft_returns_bytes(self, mock_fonts, mock_sig, contract_template):
        """Draft mode produces valid PDF bytes."""
        proposal = SimpleNamespace(
            contract_params={
                'contract_source': 'default',
                'client_full_name': 'Test Client',
                'client_cedula': '123456',
                'contractor_full_name': 'Contractor',
                'contractor_cedula': '654321',
            },
            pk=10,
        )
        result = generate_contract_pdf(proposal, draft=True)
        assert result is not None
        assert isinstance(result, bytes)

    @patch('content.services.contract_pdf_service._draw_signature_block')
    @patch('content.services.contract_pdf_service._register_fonts')
    def test_draft_passes_none_as_signature_path(self, mock_fonts, mock_sig, contract_template):
        """Draft mode calls _draw_signature_block with signature_path=None (no image)."""
        proposal = SimpleNamespace(
            contract_params={
                'contract_source': 'default',
                'client_full_name': 'Test Client',
                'client_cedula': '123456',
                'contractor_full_name': 'Contractor',
                'contractor_cedula': '654321',
            },
            pk=11,
        )
        generate_contract_pdf(proposal, draft=True)
        assert mock_sig.call_count == 1
        _, call_kwargs = mock_sig.call_args
        assert call_kwargs.get('signature_path') is None

    @patch('content.services.contract_pdf_service._register_fonts')
    def test_draft_does_not_load_company_settings(self, mock_fonts, contract_template):
        """Draft mode never queries CompanySettings for the signature path."""
        with patch('content.models.CompanySettings') as mock_cs:
            proposal = SimpleNamespace(
                contract_params={
                    'contract_source': 'default',
                    'client_full_name': 'C',
                    'client_cedula': '1',
                    'contractor_full_name': 'X',
                    'contractor_cedula': '2',
                },
                pk=12,
            )
            generate_contract_pdf(proposal, draft=True)
            assert mock_cs.load.call_count == 0, "CompanySettings.load should not be called in draft mode"
            mock_cs.load.assert_not_called()


class TestSignatureRendering:
    """generate_contract_pdf(proposal, draft=False) passes the correct signature_path."""

    @patch('content.services.contract_pdf_service._register_fonts')
    def test_final_passes_sig_path_when_signature_is_set(self, mock_fonts, contract_template, tmp_path):
        """Final PDF passes contractor_signature.path as signature_path kwarg."""
        sig_file = tmp_path / 'sig.png'
        sig_file.write_bytes(b'fake_image')

        company = SimpleNamespace(
            contractor_signature=SimpleNamespace(path=str(sig_file)),
        )

        with patch('content.services.contract_pdf_service._draw_signature_block') as mock_sig, \
             patch('content.models.CompanySettings') as mock_cs:
            mock_cs.load.return_value = company
            proposal = SimpleNamespace(
                contract_params={
                    'contract_source': 'default',
                    'client_full_name': 'Client',
                    'client_cedula': '111',
                    'contractor_full_name': 'Contractor',
                    'contractor_cedula': '222',
                },
                pk=20,
            )
            generate_contract_pdf(proposal, draft=False)
            assert mock_sig.call_count == 1
            _, call_kwargs = mock_sig.call_args
            assert call_kwargs.get('signature_path') == str(sig_file)

    @patch('content.services.contract_pdf_service._register_fonts')
    def test_final_passes_none_when_no_signature_set(self, mock_fonts, contract_template):
        """Final PDF passes signature_path=None when company has no contractor_signature."""
        company = SimpleNamespace(contractor_signature=None)

        with patch('content.services.contract_pdf_service._draw_signature_block') as mock_sig, \
             patch('content.models.CompanySettings') as mock_cs:
            mock_cs.load.return_value = company
            proposal = SimpleNamespace(
                contract_params={
                    'contract_source': 'default',
                    'client_full_name': 'Client',
                    'client_cedula': '111',
                    'contractor_full_name': 'Contractor',
                    'contractor_cedula': '222',
                },
                pk=21,
            )
            generate_contract_pdf(proposal, draft=False)
            assert mock_sig.call_count == 1
            _, call_kwargs = mock_sig.call_args
            assert call_kwargs.get('signature_path') is None


class TestContractFontConstants:
    """Contract body uses Helvetica at the declared sizes."""

    def test_body_font_is_helvetica(self):
        from content.services.contract_pdf_service import _CONTRACT_BODY_FONT
        assert _CONTRACT_BODY_FONT == 'Helvetica'

    def test_body_font_size_is_eleven(self):
        from content.services.contract_pdf_service import _CONTRACT_BODY_SIZE
        assert _CONTRACT_BODY_SIZE == 11

    def test_body_leading_is_fifteen(self):
        from content.services.contract_pdf_service import _CONTRACT_BODY_LEADING
        assert _CONTRACT_BODY_LEADING == 15


class TestContractSpecialChars:
    """Contract generation handles special characters and long values without raising."""

    @patch('content.services.contract_pdf_service._register_fonts')
    def test_accented_names_do_not_raise(self, mock_fonts, contract_template):
        """Colombian names with tildes and accents render without error."""
        proposal = SimpleNamespace(
            contract_params={
                'contract_source': 'default',
                'client_full_name': 'Julián Andrés Ñoño García',
                'client_cedula': '1234567890',
                'contractor_full_name': 'María José Peñaloza Ruíz',
                'contractor_cedula': '9876543210',
            },
            pk=30,
        )
        result = generate_contract_pdf(proposal)
        assert result is not None

    @patch('content.services.contract_pdf_service._register_fonts')
    def test_long_bank_account_number_does_not_raise(self, mock_fonts, contract_template):
        """Very long bank account numbers render without overflow errors."""
        proposal = SimpleNamespace(
            contract_params={
                'contract_source': 'default',
                'client_full_name': 'Client',
                'client_cedula': '1',
                'contractor_full_name': 'Contractor',
                'contractor_cedula': '2',
                'bank_account_number': '9' * 30,  # unusually long account number
            },
            pk=31,
        )
        result = generate_contract_pdf(proposal)
        assert result is not None


class TestDefaultTemplateIntegrity:
    """Ensure the default ContractTemplate uses every placeholder that _build_params provides."""

    @pytest.fixture(autouse=True)
    def _load_default_template(self):
        from content.models import ContractTemplate
        tpl = ContractTemplate.get_default()
        assert tpl is not None, 'No default ContractTemplate in DB'
        self.template = tpl

    def test_contains_all_build_params_keys(self):
        expected_keys = set(_build_params({}).keys()) - _TEMPLATE_EXEMPT_KEYS
        found = set(re.findall(r'\{(\w+)\}', self.template.content_markdown))
        missing = expected_keys - found
        assert not missing, f'Placeholders missing from default template: {missing}'

    def test_has_no_unknown_placeholders(self):
        known_keys = set(_build_params({}).keys())
        found = set(re.findall(r'\{(\w+)\}', self.template.content_markdown))
        unknown = found - known_keys
        assert not unknown, f'Unknown placeholders in template (not in _build_params): {unknown}'

    def test_format_succeeds_with_all_params(self):
        params = _build_params({
            'client_full_name': 'Test Client',
            'client_cedula': '123',
            'contractor_full_name': 'Test Contractor',
            'contractor_cedula': '456',
        })
        result = self.template.content_markdown.format(**params)
        assert '{' not in result or '{{' in self.template.content_markdown


# ---------------------------------------------------------------------------
# _render_block — all block types
# ---------------------------------------------------------------------------

def _make_canvas():
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    ps = {'num': 1, 'client': 'Test'}
    y = PAGE_H - MARGIN_T
    return c, y, ps


class TestRenderBlock:
    def test_heading_level_1_renders_without_error(self):
        c, y, ps = _make_canvas()
        new_y = _render_block(c, y, {'type': 'heading', 'level': 1, 'text': 'Heading 1'}, ps)
        assert isinstance(new_y, (int, float))

    def test_heading_level_2_renders_without_error(self):
        c, y, ps = _make_canvas()
        new_y = _render_block(c, y, {'type': 'heading', 'level': 2, 'text': 'Heading 2'}, ps)
        assert isinstance(new_y, (int, float))

    def test_heading_level_3_renders_without_error(self):
        c, y, ps = _make_canvas()
        new_y = _render_block(c, y, {'type': 'heading', 'level': 3, 'text': 'Heading 3'}, ps)
        assert isinstance(new_y, (int, float))

    def test_paragraph_renders_without_error(self):
        c, y, ps = _make_canvas()
        new_y = _render_block(c, y, {'type': 'paragraph', 'text': 'Some body text.'}, ps)
        assert isinstance(new_y, (int, float))

    def test_unordered_list_renders_without_error(self):
        c, y, ps = _make_canvas()
        block = {'type': 'list', 'ordered': False, 'items': [{'text': 'Item A'}, {'text': 'Item B'}]}
        new_y = _render_block(c, y, block, ps)
        assert isinstance(new_y, (int, float))

    def test_ordered_list_renders_without_error(self):
        c, y, ps = _make_canvas()
        block = {'type': 'list', 'ordered': True, 'items': [{'text': 'First'}, {'text': 'Second'}]}
        new_y = _render_block(c, y, block, ps)
        assert isinstance(new_y, (int, float))

    def test_separator_renders_without_error(self):
        c, y, ps = _make_canvas()
        new_y = _render_block(c, y, {'type': 'separator'}, ps)
        assert isinstance(new_y, (int, float))

    def test_blockquote_renders_without_error(self):
        c, y, ps = _make_canvas()
        new_y = _render_block(c, y, {'type': 'blockquote', 'text': 'A quote.'}, ps)
        assert isinstance(new_y, (int, float))

    def test_code_block_renders_without_error(self):
        c, y, ps = _make_canvas()
        new_y = _render_block(c, y, {'type': 'code', 'text': 'def hello(): pass'}, ps)
        assert isinstance(new_y, (int, float))

    def test_table_renders_without_error(self):
        c, y, ps = _make_canvas()
        block = {
            'type': 'table',
            'headers': ['Col A', 'Col B'],
            'rows': [['val1', 'val2'], ['val3', 'val4']],
        }
        new_y = _render_block(c, y, block, ps)
        assert isinstance(new_y, (int, float))

    def test_unknown_block_type_returns_y_unchanged(self):
        c, y, ps = _make_canvas()
        new_y = _render_block(c, y, {'type': 'unknown_type'}, ps)
        assert new_y == y


class TestDrawTitlePage:
    def test_renders_without_error_when_no_contract_date(self):
        c, y, ps = _make_canvas()
        params = {'client_full_name': 'Client', 'contractor_full_name': 'Contractor', 'contract_date': ''}
        new_y = _draw_title_page(c, y, params, ps)
        assert isinstance(new_y, (int, float))

    def test_renders_without_error_with_contract_date(self):
        c, y, ps = _make_canvas()
        params = {
            'client_full_name': 'Client',
            'contractor_full_name': 'Contractor',
            'contract_date': '2026-04-25',
        }
        new_y = _draw_title_page(c, y, params, ps)
        # With a date, the y position should be lower than without
        c2, y2, ps2 = _make_canvas()
        params_no_date = {
            'client_full_name': 'Client',
            'contractor_full_name': 'Contractor',
            'contract_date': '',
        }
        new_y2 = _draw_title_page(c2, y2, params_no_date, ps2)
        assert new_y < new_y2


class TestGenerateContractPdfExceptionPath:
    def test_returns_none_when_rendering_raises_exception(self):
        proposal = SimpleNamespace(contract_params={'contract_source': 'custom'}, pk=99)
        with patch('content.services.contract_pdf_service._get_contract_markdown', side_effect=RuntimeError('boom')):
            result = generate_contract_pdf(proposal)
        assert result is None

    def test_returns_none_when_contract_params_is_none(self):
        proposal = SimpleNamespace(contract_params=None, pk=98)
        with patch('content.services.contract_pdf_service._get_contract_markdown', return_value=''):
            result = generate_contract_pdf(proposal)
        assert result is None
