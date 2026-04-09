"""Tests for proposal serializers — validation, computed fields, section filtering."""
import pytest
from freezegun import freeze_time

from content.models import ProposalSection
from content.serializers.proposal import (
    ContractParamsSerializer,
    EmailTemplateConfigSerializer,
    ProposalCreateUpdateSerializer,
    ProposalDefaultConfigSerializer,
    ProposalDetailSerializer,
    ProposalFromJSONSerializer,
    ProposalListSerializer,
    ProposalSectionUpdateSerializer,
)

pytestmark = pytest.mark.django_db


class TestProposalCreateUpdateSerializerValidation:
    @freeze_time('2026-03-01 12:00:00')
    def test_rejects_past_expires_at(self):
        payload = {
            'title': 'Test',
            'client_name': 'Client',
            'client_email': 'c@test.com',
            'total_investment': '1000.00',
            'currency': 'COP',
            'expires_at': '2026-02-01T12:00:00Z',
        }
        serializer = ProposalCreateUpdateSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'expires_at' in serializer.errors

    @freeze_time('2026-03-01 12:00:00')
    def test_accepts_future_expires_at(self):
        payload = {
            'title': 'Test',
            'client_name': 'Client',
            'client_email': 'c@test.com',
            'total_investment': '1000.00',
            'currency': 'COP',
            'expires_at': '2026-04-01T12:00:00Z',
        }
        serializer = ProposalCreateUpdateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors

    def test_rejects_sent_status_without_client_email(self):
        payload = {
            'title': 'Test',
            'client_name': 'Client',
            'client_email': '',
            'total_investment': '1000.00',
            'currency': 'COP',
            'status': 'sent',
        }
        serializer = ProposalCreateUpdateSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'client_email' in serializer.errors

    def test_accepts_sent_status_with_client_email(self):
        payload = {
            'title': 'Test',
            'client_name': 'Client',
            'client_email': 'c@test.com',
            'total_investment': '1000.00',
            'currency': 'COP',
            'status': 'sent',
        }
        serializer = ProposalCreateUpdateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors


class TestProposalSectionUpdateSerializerValidation:
    def test_rejects_non_dict_content_json(self):
        serializer = ProposalSectionUpdateSerializer(
            data={'content_json': 'not a dict'}
        )
        assert not serializer.is_valid()
        assert 'content_json' in serializer.errors

    def test_accepts_dict_content_json(self, proposal_section):
        serializer = ProposalSectionUpdateSerializer(
            proposal_section,
            data={'content_json': {'heading': 'Updated'}},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors


class TestProposalDetailSerializerSections:
    def test_admin_context_returns_all_sections(self, proposal, proposal_section):
        disabled = ProposalSection.objects.create(
            proposal=proposal, section_type='timeline',
            title='Timeline', order=1, is_enabled=False,
        )
        serializer = ProposalDetailSerializer(
            proposal, context={'is_admin': True}
        )
        section_ids = [s['id'] for s in serializer.data['sections']]
        assert proposal_section.id in section_ids
        assert disabled.id in section_ids

    def test_public_context_excludes_disabled_sections(self, proposal, proposal_section):
        disabled = ProposalSection.objects.create(
            proposal=proposal, section_type='timeline',
            title='Timeline', order=1, is_enabled=False,
        )
        serializer = ProposalDetailSerializer(
            proposal, context={'is_admin': False}
        )
        section_ids = [s['id'] for s in serializer.data['sections']]
        assert proposal_section.id in section_ids
        assert disabled.id not in section_ids


class TestProposalListSerializerComputedFields:
    def test_days_remaining_present(self, proposal):
        serializer = ProposalListSerializer(proposal)
        assert 'days_remaining' in serializer.data

    def test_is_expired_present(self, proposal):
        serializer = ProposalListSerializer(proposal)
        assert 'is_expired' in serializer.data
        assert serializer.data['is_expired'] is False

    def test_language_field_present(self, proposal):
        serializer = ProposalListSerializer(proposal)
        assert 'language' in serializer.data

    def test_language_field_value(self, proposal):
        proposal.language = 'en'
        proposal.save()
        serializer = ProposalListSerializer(proposal)
        assert serializer.data['language'] == 'en'

    def test_sent_at_field_present(self, proposal):
        serializer = ProposalListSerializer(proposal)
        assert 'sent_at' in serializer.data

    def test_sent_at_field_null_for_draft(self, proposal):
        serializer = ProposalListSerializer(proposal)
        assert serializer.data['sent_at'] is None

    @freeze_time('2026-04-01 12:00:00')
    def test_sent_at_field_value_for_sent(self, proposal):
        from django.utils import timezone
        now = timezone.now()
        proposal.sent_at = now
        proposal.save()
        serializer = ProposalListSerializer(proposal)
        assert serializer.data['sent_at'] is not None


class TestProposalDetailSerializerComputedFields:
    def test_public_url_present(self, proposal):
        serializer = ProposalDetailSerializer(
            proposal, context={'is_admin': True}
        )
        assert 'public_url' in serializer.data

    def test_hosting_percent_present_with_default(self, proposal):
        serializer = ProposalDetailSerializer(
            proposal, context={'is_admin': True}
        )
        assert 'hosting_percent' in serializer.data
        assert serializer.data['hosting_percent'] == 30


class TestProposalCreateUpdateSerializerHostingPercent:
    def test_accepts_hosting_percent(self):
        payload = {
            'title': 'Test',
            'client_name': 'Client',
            'client_email': 'c@test.com',
            'total_investment': '1000.00',
            'currency': 'COP',
            'hosting_percent': 25,
        }
        serializer = ProposalCreateUpdateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['hosting_percent'] == 25

    def test_hosting_percent_defaults_to_30(self, proposal):
        """Model default hosting_percent is 30 and serializer omits it when not supplied."""
        assert proposal.hosting_percent == 30
        assert isinstance(proposal.hosting_percent, int)
        serializer = ProposalCreateUpdateSerializer(
            data={
                'title': 'Default Check',
                'client_name': 'C',
                'client_email': 'c@test.com',
                'total_investment': '500.00',
                'currency': 'COP',
            },
        )
        assert serializer.is_valid(), serializer.errors
        assert 'hosting_percent' not in serializer.validated_data or \
            serializer.validated_data['hosting_percent'] == 30


class TestProposalHostingBillingDiscounts:
    """Tests for hosting_discount_semiannual and hosting_discount_quarterly fields."""

    def test_detail_serializer_includes_discount_fields(self, proposal):
        serializer = ProposalDetailSerializer(
            proposal, context={'is_admin': True}
        )
        assert 'hosting_discount_semiannual' in serializer.data
        assert 'hosting_discount_quarterly' in serializer.data

    def test_detail_serializer_discount_defaults(self, proposal):
        serializer = ProposalDetailSerializer(
            proposal, context={'is_admin': True}
        )
        assert serializer.data['hosting_discount_semiannual'] == 20
        assert serializer.data['hosting_discount_quarterly'] == 10

    def test_create_serializer_accepts_discount_fields(self):
        payload = {
            'title': 'Test',
            'client_name': 'Client',
            'client_email': 'c@test.com',
            'total_investment': '1000.00',
            'currency': 'COP',
            'hosting_discount_semiannual': 15,
            'hosting_discount_quarterly': 5,
        }
        serializer = ProposalCreateUpdateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['hosting_discount_semiannual'] == 15
        assert serializer.validated_data['hosting_discount_quarterly'] == 5

    def test_model_defaults_for_discount_fields(self, proposal):
        assert proposal.hosting_discount_semiannual == 20
        assert proposal.hosting_discount_quarterly == 10


class TestProposalFromJSONSerializer:
    """Validation tests for ProposalFromJSONSerializer."""

    def _valid_payload(self, **overrides):
        """Return a minimal valid payload."""
        data = {
            'title': 'Test Proposal',
            'client_name': 'Test Client',
            'sections': {
                'general': {'clientName': 'Test Client'},
            },
        }
        data.update(overrides)
        return data

    def test_valid_minimal_payload_is_valid(self):
        serializer = ProposalFromJSONSerializer(data=self._valid_payload())
        assert serializer.is_valid(), serializer.errors

    def test_missing_general_key_is_invalid(self):
        payload = self._valid_payload()
        payload['sections'] = {'executiveSummary': {'title': 'Summary'}}
        serializer = ProposalFromJSONSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'sections' in serializer.errors

    def test_general_without_client_name_is_invalid(self):
        payload = self._valid_payload()
        payload['sections'] = {'general': {'clientName': ''}}
        serializer = ProposalFromJSONSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'sections' in serializer.errors

    def test_general_with_non_dict_value_is_invalid(self):
        payload = self._valid_payload()
        payload['sections'] = {'general': 'not a dict'}
        serializer = ProposalFromJSONSerializer(data=payload)
        assert not serializer.is_valid()

    @freeze_time('2026-03-01 12:00:00')
    def test_future_expires_at_is_valid(self):
        payload = self._valid_payload(expires_at='2026-06-01T12:00:00Z')
        serializer = ProposalFromJSONSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors

    @freeze_time('2026-03-01 12:00:00')
    def test_past_expires_at_is_invalid(self):
        payload = self._valid_payload(expires_at='2026-01-01T12:00:00Z')
        serializer = ProposalFromJSONSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'expires_at' in serializer.errors

    def test_null_expires_at_is_accepted(self):
        payload = self._valid_payload(expires_at=None)
        serializer = ProposalFromJSONSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors

    def test_meta_key_stripped_from_sections(self):
        payload = self._valid_payload()
        payload['sections']['_meta'] = {'version': '1.0'}
        serializer = ProposalFromJSONSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        assert '_meta' not in serializer.validated_data['sections']

    def test_blank_optional_metadata_fields_are_valid(self):
        """Regression: blank client_email/phone/project_type/market_type must not fail."""
        payload = self._valid_payload(
            client_email='',
            client_phone='',
            project_type='',
            market_type='',
        )
        serializer = ProposalFromJSONSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors

    def test_full_payload_with_multiple_sections_is_valid(self):
        payload = self._valid_payload()
        payload['sections'].update({
            'executiveSummary': {'title': 'Summary', 'paragraphs': []},
            'investment': {'totalInvestment': '$5,000,000', 'currency': 'COP'},
        })
        serializer = ProposalFromJSONSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors

    def test_technical_document_section_in_payload_is_valid(self):
        payload = self._valid_payload()
        payload['sections']['technicalDocument'] = {
            'purpose': 'Arquitectura',
            'epics': [{'epicKey': 'a', 'title': 'A', 'requirements': []}],
        }
        serializer = ProposalFromJSONSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        assert 'technicalDocument' in serializer.validated_data['sections']


class TestProposalDetailSerializerDiscountedInvestment:
    def test_discounted_investment_returns_none_when_no_discount(self, proposal):
        """get_discounted_investment returns None when discount_percent is 0."""
        proposal.discount_percent = 0
        proposal.save()
        serializer = ProposalDetailSerializer(proposal, context={'is_admin': True})
        assert serializer.data['discounted_investment'] is None

    def test_discounted_investment_returns_value_when_discount_set(self, proposal):
        """get_discounted_investment returns discounted value when discount_percent > 0."""
        from decimal import Decimal
        proposal.total_investment = Decimal('1000000')
        proposal.discount_percent = 10
        proposal.save()
        serializer = ProposalDetailSerializer(proposal, context={'is_admin': True})
        assert serializer.data['discounted_investment'] is not None


class TestContractParamsSerializerValidation:
    def test_rejects_custom_source_without_markdown(self):
        """ContractParamsSerializer rejects contract_source=custom with no custom_contract_markdown."""
        payload = {
            'client_cedula': '123456',
            'contract_source': 'custom',
            'custom_contract_markdown': '',
        }
        serializer = ContractParamsSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'custom_contract_markdown' in str(serializer.errors)

    def test_accepts_custom_source_with_markdown(self):
        """ContractParamsSerializer accepts contract_source=custom when markdown is provided."""
        payload = {
            'client_cedula': '123456',
            'contract_source': 'custom',
            'custom_contract_markdown': '# Contract\n\nCustom terms here.',
        }
        serializer = ContractParamsSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors

    def test_accepts_default_source_without_markdown(self):
        """ContractParamsSerializer accepts default contract_source without custom markdown."""
        payload = {
            'client_cedula': '123456',
            'contract_source': 'default',
        }
        serializer = ContractParamsSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors


class TestProposalDefaultConfigSerializerValidation:
    def test_rejects_invalid_language(self):
        """ProposalDefaultConfigSerializer rejects language values other than es/en."""
        serializer = ProposalDefaultConfigSerializer(
            data={'language': 'fr', 'sections_json': []}
        )
        assert not serializer.is_valid()
        assert 'language' in serializer.errors

    def test_rejects_non_list_sections_json(self):
        """ProposalDefaultConfigSerializer rejects sections_json that is not a list."""
        serializer = ProposalDefaultConfigSerializer(
            data={'language': 'es', 'sections_json': {'not': 'a list'}}
        )
        assert not serializer.is_valid()
        assert 'sections_json' in serializer.errors

    def test_rejects_non_dict_section_in_list(self):
        """ProposalDefaultConfigSerializer rejects sections_json containing non-dict items."""
        serializer = ProposalDefaultConfigSerializer(
            data={'language': 'es', 'sections_json': ['string_item']}
        )
        assert not serializer.is_valid()
        assert 'sections_json' in serializer.errors

    def test_rejects_section_missing_required_keys(self):
        """ProposalDefaultConfigSerializer rejects sections missing required keys."""
        serializer = ProposalDefaultConfigSerializer(
            data={'language': 'es', 'sections_json': [{'section_type': 'intro'}]}
        )
        assert not serializer.is_valid()
        assert 'sections_json' in serializer.errors

    def test_accepts_valid_sections_json(self):
        """ProposalDefaultConfigSerializer accepts a properly structured sections_json."""
        section = {
            'section_type': 'executive_summary',
            'title': 'Executive Summary',
            'order': 1,
            'content_json': {},
        }
        serializer = ProposalDefaultConfigSerializer(
            data={'language': 'es', 'sections_json': [section]}
        )
        assert serializer.is_valid(), serializer.errors


class TestEmailTemplateConfigSerializerValidation:
    def test_rejects_non_dict_content_overrides(self, db):
        """EmailTemplateConfigSerializer rejects content_overrides that is not a dict."""
        from content.models import EmailTemplateConfig
        config = EmailTemplateConfig.objects.create(
            template_key='test_key',
            content_overrides={},
        )
        serializer = EmailTemplateConfigSerializer(
            config,
            data={'content_overrides': 'not a dict'},
            partial=True,
        )
        assert not serializer.is_valid()
        assert 'content_overrides' in serializer.errors

    def test_accepts_dict_content_overrides(self, db):
        """EmailTemplateConfigSerializer accepts valid dict content_overrides."""
        from content.models import EmailTemplateConfig
        config = EmailTemplateConfig.objects.create(
            template_key='test_key2',
            content_overrides={},
        )
        serializer = EmailTemplateConfigSerializer(
            config,
            data={'content_overrides': {'subject': 'New Subject'}},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
