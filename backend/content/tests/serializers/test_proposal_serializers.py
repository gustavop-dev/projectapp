"""Tests for proposal serializers — validation, computed fields, section filtering."""
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from freezegun import freeze_time
from rest_framework import serializers

from accounts.models import UserProfile
from content.models import (
    ProposalChangeLog,
    ProposalDocument,
    ProposalProjectStage,
    ProposalSection,
)
from content.serializers.proposal import (
    ContractParamsSerializer,
    EmailTemplateConfigSerializer,
    ProposalCreateUpdateSerializer,
    ProposalDefaultConfigSerializer,
    ProposalDetailSerializer,
    ProposalFromJSONSerializer,
    ProposalListSerializer,
    ProposalProjectStageSerializer,
    ProposalSectionUpdateSerializer,
)

pytestmark = pytest.mark.django_db
User = get_user_model()


def _create_change_logs(proposal, count):
    for index in range(count):
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='updated',
            actor_type='system',
            description=f'Change {index:02d}',
        )


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

    @patch('content.serializers.proposal.validate_email_domain_mx', return_value=False)
    def test_rejects_client_email_when_domain_has_no_mx(self, mock_validate_email_domain_mx):
        serializer = ProposalCreateUpdateSerializer(
            data={
                'title': 'Test',
                'client_name': 'Client',
                'client_email': 'bad@example.com',
                'total_investment': '1000.00',
                'currency': 'COP',
            }
        )

        assert not serializer.is_valid()
        assert 'client_email' in serializer.errors
        mock_validate_email_domain_mx.assert_called_once_with('bad@example.com')


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

    def test_project_stages_is_hidden_for_non_admin_context(self, proposal):
        ProposalProjectStage.objects.create(
            proposal=proposal,
            stage_key=ProposalProjectStage.StageKey.DESIGN,
            order=1,
        )

        serializer = ProposalDetailSerializer(proposal, context={'is_admin': False})

        assert serializer.data['project_stages'] == []

    def test_project_stages_is_included_for_admin_context(self, proposal):
        stage = ProposalProjectStage.objects.create(
            proposal=proposal,
            stage_key=ProposalProjectStage.StageKey.DESIGN,
            order=1,
        )

        serializer = ProposalDetailSerializer(proposal, context={'is_admin': True})

        assert serializer.data['project_stages'][0]['id'] == stage.id

    def test_proposal_documents_is_hidden_for_non_admin_context(self, proposal):
        ProposalDocument.objects.create(
            proposal=proposal,
            document_type=ProposalDocument.DOC_TYPE_OTHER,
            title='Annex',
            file=ContentFile(b'file-bytes', name='annex.pdf'),
        )

        serializer = ProposalDetailSerializer(proposal, context={'is_admin': False})

        assert serializer.data['proposal_documents'] == []

    def test_proposal_documents_is_included_for_admin_context(self, proposal):
        document = ProposalDocument.objects.create(
            proposal=proposal,
            document_type=ProposalDocument.DOC_TYPE_OTHER,
            title='Annex',
            file=ContentFile(b'file-bytes', name='annex.pdf'),
            custom_type_label='Annexo',
        )

        serializer = ProposalDetailSerializer(proposal, context={'is_admin': True})

        assert serializer.data['proposal_documents'][0]['id'] == document.id

    def test_change_logs_is_ordered_desc_and_limited_to_50_items(self, proposal):
        _create_change_logs(proposal, 55)

        serializer = ProposalDetailSerializer(proposal, context={'is_admin': True})

        assert len(serializer.data['change_logs']) == 50
        assert serializer.data['change_logs'][0]['description'] == 'Change 54'
        assert serializer.data['change_logs'][-1]['description'] == 'Change 05'


class TestProposalProjectStageSerializerValidation:
    def test_accepts_same_day_stage_range(self, proposal):
        serializer = ProposalProjectStageSerializer(
            data={
                'proposal': proposal.pk,
                'stage_key': ProposalProjectStage.StageKey.DESIGN,
                'order': 1,
                'start_date': '2026-04-10',
                'end_date': '2026-04-10',
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_rejects_stage_when_start_date_is_after_end_date(self, proposal):
        serializer = ProposalProjectStageSerializer(
            data={
                'proposal': proposal.pk,
                'stage_key': ProposalProjectStage.StageKey.DESIGN,
                'order': 1,
                'start_date': '2026-04-11',
                'end_date': '2026-04-10',
            }
        )

        assert not serializer.is_valid()
        assert 'end_date' in serializer.errors


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


class TestProposalCreateUpdateSerializerClientResolution:
    def test_create_uses_service_resolution_when_client_id_is_omitted(self):
        serializer = ProposalCreateUpdateSerializer(
            data={
                'title': 'Service Resolved Proposal',
                'client_name': 'Resolved Client',
                'client_email': 'resolved@example.com',
                'client_phone': '+57 300 0003',
                'client_company': 'Resolved Co',
                'total_investment': '1800.00',
                'currency': 'COP',
            }
        )
        user = User.objects.create_user(
            username='serializer-service@test.com',
            email='serializer-service@test.com',
            password='pass12345',
        )
        client_profile = UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)

        with patch(
            'content.serializers.proposal.proposal_client_service.get_or_create_client_for_proposal',
            return_value=client_profile,
        ) as mock_get_or_create, patch(
            'content.serializers.proposal.proposal_client_service.sync_snapshot'
        ) as mock_sync_snapshot:
            assert serializer.is_valid(), serializer.errors
            proposal_instance = serializer.save()

        assert proposal_instance.client_id == client_profile.pk
        mock_get_or_create.assert_called_once_with(
            name='Resolved Client',
            email='resolved@example.com',
            phone='+57 300 0003',
            company='Resolved Co',
        )
        mock_sync_snapshot.assert_called_once_with(proposal_instance)

    def test_create_uses_explicit_client_id_without_get_or_create(self):
        user = User.objects.create_user(
            username='serializer-client@test.com',
            email='serializer-client@test.com',
            password='pass12345',
        )
        client_profile = UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)
        serializer = ProposalCreateUpdateSerializer(
            data={
                'title': 'Client Bound Proposal',
                'client_id': client_profile.pk,
                'client_name': 'Ignored',
                'client_email': 'ignored@example.com',
                'total_investment': '1500.00',
                'currency': 'COP',
            }
        )

        with patch(
            'content.serializers.proposal.proposal_client_service.get_or_create_client_for_proposal'
        ) as mock_get_or_create, patch(
            'content.serializers.proposal.proposal_client_service.sync_snapshot'
        ) as mock_sync_snapshot:
            assert serializer.is_valid(), serializer.errors
            proposal_instance = serializer.save()

        assert proposal_instance.client_id == client_profile.pk
        mock_get_or_create.assert_not_called()
        mock_sync_snapshot.assert_called_once_with(proposal_instance)

    def test_update_propagates_client_updates_when_flag_is_true(self, proposal):
        user = User.objects.create_user(
            username='serializer-propagate@test.com',
            email='serializer-propagate@test.com',
            password='pass12345',
        )
        proposal.client = UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)
        proposal.save(update_fields=['client'])

        serializer = ProposalCreateUpdateSerializer(
            proposal,
            data={
                'client_name': 'Updated Client',
                'client_email': 'updated@example.com',
                'client_phone': '+57 300 0001',
                'client_company': 'Updated Co',
                'propagate_client_updates': True,
            },
            partial=True,
        )

        with patch(
            'content.serializers.proposal.proposal_client_service.update_client_profile'
        ) as mock_update_client_profile, patch(
            'content.serializers.proposal.proposal_client_service.sync_snapshot'
        ) as mock_sync_snapshot:
            assert serializer.is_valid(), serializer.errors
            serializer.save()

        mock_update_client_profile.assert_called_once()
        mock_sync_snapshot.assert_called_once()

    def test_update_does_not_propagate_client_updates_when_flag_is_false(self, proposal):
        user = User.objects.create_user(
            username='serializer-local@test.com',
            email='serializer-local@test.com',
            password='pass12345',
        )
        proposal.client = UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)
        proposal.save(update_fields=['client'])

        serializer = ProposalCreateUpdateSerializer(
            proposal,
            data={
                'client_name': 'Local Override',
                'client_phone': '+57 300 0002',
                'propagate_client_updates': False,
            },
            partial=True,
        )

        with patch(
            'content.serializers.proposal.proposal_client_service.update_client_profile'
        ) as mock_update_client_profile, patch(
            'content.serializers.proposal.proposal_client_service.sync_snapshot'
        ) as mock_sync_snapshot:
            assert serializer.is_valid(), serializer.errors
            serializer.save()

        mock_update_client_profile.assert_not_called()
        mock_sync_snapshot.assert_not_called()

    def test_update_switches_to_explicit_client_and_syncs_snapshot(self, proposal):
        original_user = User.objects.create_user(
            username='serializer-original@test.com',
            email='serializer-original@test.com',
            password='pass12345',
        )
        proposal.client = UserProfile.objects.create(user=original_user, role=UserProfile.ROLE_CLIENT)
        proposal.save(update_fields=['client'])

        new_user = User.objects.create_user(
            username='serializer-new@test.com',
            email='serializer-new@test.com',
            password='pass12345',
        )
        new_profile = UserProfile.objects.create(user=new_user, role=UserProfile.ROLE_CLIENT)
        serializer = ProposalCreateUpdateSerializer(
            proposal,
            data={'client_id': new_profile.pk},
            partial=True,
        )

        with patch(
            'content.serializers.proposal.proposal_client_service.sync_snapshot'
        ) as mock_sync_snapshot:
            assert serializer.is_valid(), serializer.errors
            updated = serializer.save()

        assert updated.client_id == new_profile.pk
        mock_sync_snapshot.assert_called_once_with(updated)


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
    def test_validate_raises_for_custom_source_without_markdown(self):
        serializer = ContractParamsSerializer()

        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate({
                'client_cedula': '123456',
                'contract_source': 'custom',
                'custom_contract_markdown': '',
            })
        assert 'custom_contract_markdown' in str(exc_info.value)

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
    def test_validate_language_rejects_non_supported_value(self):
        serializer = ProposalDefaultConfigSerializer()

        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_language('fr')
        assert 'Language must be "es" or "en".' in str(exc_info.value)

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

    def test_rejects_expiration_days_below_minimum(self):
        serializer = ProposalDefaultConfigSerializer(
            data={'language': 'es', 'sections_json': [], 'expiration_days': 0}
        )

        assert not serializer.is_valid()
        assert 'expiration_days' in serializer.errors

    def test_accepts_expiration_days_within_allowed_range(self):
        serializer = ProposalDefaultConfigSerializer(
            data={'language': 'es', 'sections_json': [], 'expiration_days': 365}
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


class TestSectionKeyMapValueAddedModules:
    """Round-trip contract for the valueAddedModules JSON key."""

    def test_value_added_modules_pair_in_section_key_map(self):
        from content.serializers.proposal import SECTION_KEY_MAP, SECTION_TYPE_TO_KEY

        assert SECTION_KEY_MAP['valueAddedModules'] == 'value_added_modules'
        assert SECTION_TYPE_TO_KEY['value_added_modules'] == 'valueAddedModules'

    def test_section_key_map_is_symmetric(self):
        from content.serializers.proposal import SECTION_KEY_MAP, SECTION_TYPE_TO_KEY

        for camel, snake in SECTION_KEY_MAP.items():
            assert SECTION_TYPE_TO_KEY[snake] == camel, (
                f'Key map asymmetry for {camel} ↔ {snake}'
            )

    def test_default_value_added_modules_content_round_trips(self):
        """Default content for value_added_modules preserves shape through key map."""
        from content.serializers.proposal import SECTION_KEY_MAP, SECTION_TYPE_TO_KEY
        from content.services.proposal_service import ProposalService

        cfg = ProposalService.get_default_section('es', 'value_added_modules')
        assert cfg is not None
        snake = cfg['section_type']
        camel = SECTION_TYPE_TO_KEY[snake]

        payload = {camel: cfg['content_json']}
        rehydrated_type = SECTION_KEY_MAP[camel]
        rehydrated_content = payload[camel]

        assert rehydrated_type == snake
        assert rehydrated_content['module_ids'] == cfg['content_json']['module_ids']
        assert rehydrated_content['justifications'] == cfg['content_json']['justifications']


class TestSlugValidation:
    def test_valid_slug_is_accepted(self):
        s = ProposalCreateUpdateSerializer(data={'slug': 'maria-lopez'}, partial=True)
        s.is_valid()
        assert 'slug' not in s.errors

    def test_slug_with_spaces_is_rejected(self):
        s = ProposalCreateUpdateSerializer(data={'slug': 'maria lopez'}, partial=True)
        s.is_valid()
        assert 'slug' in s.errors

    def test_slug_with_uppercase_is_rejected(self):
        s = ProposalCreateUpdateSerializer(data={'slug': 'Maria-Lopez'}, partial=True)
        s.is_valid()
        assert 'slug' in s.errors

    def test_slug_with_accents_is_rejected(self):
        s = ProposalCreateUpdateSerializer(data={'slug': 'maría-lópez'}, partial=True)
        s.is_valid()
        assert 'slug' in s.errors

    def test_slug_over_120_chars_is_rejected(self):
        s = ProposalCreateUpdateSerializer(data={'slug': 'a' * 121}, partial=True)
        s.is_valid()
        assert 'slug' in s.errors

    def test_duplicate_slug_is_rejected(self):
        from content.models import BusinessProposal
        BusinessProposal.objects.create(title='Existing', client_name='Someone', slug='taken-slug')
        s = ProposalCreateUpdateSerializer(data={'slug': 'taken-slug'}, partial=True)
        s.is_valid()
        assert 'slug' in s.errors

    def test_editing_own_slug_passes_uniqueness(self):
        from content.models import BusinessProposal
        proposal = BusinessProposal.objects.create(title='A', client_name='A', slug='my-slug')
        s = ProposalCreateUpdateSerializer(instance=proposal, data={'slug': 'my-slug'}, partial=True)
        s.is_valid()
        assert 'slug' not in s.errors

    def test_empty_slug_is_accepted(self):
        s = ProposalCreateUpdateSerializer(data={'slug': ''}, partial=True)
        s.is_valid()
        assert 'slug' not in s.errors
