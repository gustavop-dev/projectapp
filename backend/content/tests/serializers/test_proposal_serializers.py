"""Tests for proposal serializers — validation, computed fields, section filtering."""
import pytest
from freezegun import freeze_time

from content.models import ProposalSection
from content.serializers.proposal import (
    ProposalCreateUpdateSerializer,
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


class TestProposalDetailSerializerComputedFields:
    def test_public_url_present(self, proposal):
        serializer = ProposalDetailSerializer(
            proposal, context={'is_admin': True}
        )
        assert 'public_url' in serializer.data


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

    def test_full_payload_with_multiple_sections_is_valid(self):
        payload = self._valid_payload()
        payload['sections'].update({
            'executiveSummary': {'title': 'Summary', 'paragraphs': []},
            'investment': {'totalInvestment': '$5,000,000', 'currency': 'COP'},
        })
        serializer = ProposalFromJSONSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
