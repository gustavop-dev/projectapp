"""Tests for contract_pdf_service: parameter building, placeholder substitution, PDF generation."""
import logging
from unittest.mock import patch, MagicMock

import pytest

from content.services.contract_pdf_service import (
    _build_params,
    _substitute_placeholders,
    generate_contract_pdf,
)

pytestmark = pytest.mark.django_db


class TestBuildParams:
    def test_returns_defaults_for_empty_dict(self):
        result = _build_params({})
        assert result['contractor_full_name'] == '_______________'
        assert result['bank_account_type'] == 'Ahorros'
        assert result['contract_city'] == 'Medellin'

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
        proposal = MagicMock()
        proposal.contract_params = {
            'contract_source': 'default',
            'client_full_name': 'Test Client',
            'client_cedula': '123456',
            'contractor_full_name': 'Contractor',
            'contractor_cedula': '654321',
            'contract_date': '2026-04-02',
        }
        proposal.pk = 1
        result = generate_contract_pdf(proposal)
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0

    @patch('content.services.contract_pdf_service._register_fonts')
    def test_returns_bytes_for_custom_source(self, mock_fonts):
        proposal = MagicMock()
        proposal.contract_params = {
            'contract_source': 'custom',
            'custom_contract_markdown': '# Custom Contract\n\nThis is a custom contract.',
        }
        proposal.pk = 2
        result = generate_contract_pdf(proposal)
        assert result is not None
        assert isinstance(result, bytes)

    def test_returns_none_when_no_default_template(self, db):
        from content.models import ContractTemplate
        ContractTemplate.objects.all().update(is_default=False)
        proposal = MagicMock()
        proposal.contract_params = {'contract_source': 'default'}
        proposal.pk = 3
        result = generate_contract_pdf(proposal)
        assert result is None

    def test_returns_none_when_custom_markdown_empty(self):
        proposal = MagicMock()
        proposal.contract_params = {
            'contract_source': 'custom',
            'custom_contract_markdown': '',
        }
        proposal.pk = 4
        result = generate_contract_pdf(proposal)
        assert result is None
