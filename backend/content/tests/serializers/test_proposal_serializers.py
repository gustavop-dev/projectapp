"""Tests for proposal serializers — validation, computed fields, section filtering."""
import pytest
from freezegun import freeze_time

from content.models import ProposalSection
from content.serializers.proposal import (
    ProposalCreateUpdateSerializer,
    ProposalDetailSerializer,
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
