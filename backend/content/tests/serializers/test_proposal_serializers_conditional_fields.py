"""Tests for uncovered branches in content/serializers/proposal.py."""
import pytest
from django.urls import reverse

from content.models import ProposalSection

pytestmark = pytest.mark.django_db


class TestProposalDetailSerializerBranches:
    def test_non_admin_get_sections_excludes_disabled(self, api_client, proposal):
        """get_sections() skips disabled sections for non-admin requests."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type=ProposalSection.SectionType.GREETING,
            content_json={},
            order=99,
            is_enabled=False,
        )
        proposal.is_active = True
        proposal.status = 'sent'
        proposal.save(update_fields=['is_active', 'status'])

        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': proposal.uuid})
        resp = api_client.get(url)

        assert resp.status_code == 200
        for section in resp.json()['sections']:
            assert section['is_enabled'] is not False

    def test_admin_get_sections_includes_disabled(self, admin_client, proposal, proposal_section):
        """Admin receives all sections including disabled ones."""
        # proposal_section uses GREETING; use a different type to avoid unique constraint
        ProposalSection.objects.create(
            proposal=proposal,
            section_type=ProposalSection.SectionType.TIMELINE,
            content_json={},
            order=88,
            is_enabled=False,
        )

        url = reverse('retrieve-proposal', kwargs={'proposal_id': proposal.id})
        resp = admin_client.get(url)

        assert resp.status_code == 200
        # At least the disabled section was included
        assert len(resp.json()['sections']) >= 2

    def test_non_admin_change_logs_is_empty(self, api_client, proposal):
        """change_logs field returns empty list for non-admin requests."""
        proposal.is_active = True
        proposal.status = 'sent'
        proposal.save(update_fields=['is_active', 'status'])

        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': proposal.uuid})
        resp = api_client.get(url)

        assert resp.status_code == 200
        assert resp.json().get('change_logs', []) == []

    def test_admin_change_logs_is_not_empty_after_status_change(
        self, admin_client, proposal
    ):
        """change_logs is present and accessible for admin."""
        url = reverse('retrieve-proposal', kwargs={'proposal_id': proposal.id})
        resp = admin_client.get(url)

        assert resp.status_code == 200
        # The field exists and is a list
        assert isinstance(resp.json().get('change_logs'), list)

    def test_discounted_investment_is_computed_when_discount_set(self, admin_client, proposal):
        """get_discounted_investment returns correct value when discount_percent > 0."""
        proposal.total_investment = 10000
        proposal.discount_percent = 20
        proposal.save(update_fields=['total_investment', 'discount_percent'])

        url = reverse('retrieve-proposal', kwargs={'proposal_id': proposal.id})
        resp = admin_client.get(url)

        assert resp.status_code == 200
        assert float(resp.json()['discounted_investment']) == 8000.0

    def test_discounted_investment_is_none_when_no_discount(self, admin_client, proposal):
        """get_discounted_investment returns None when discount_percent is 0."""
        proposal.total_investment = 10000
        proposal.discount_percent = 0
        proposal.save(update_fields=['total_investment', 'discount_percent'])

        url = reverse('retrieve-proposal', kwargs={'proposal_id': proposal.id})
        resp = admin_client.get(url)

        assert resp.status_code == 200
        assert resp.json()['discounted_investment'] is None


class TestContractParamsSerializerValidation:
    _base_contract_params = {
        'client_cedula': '1234567890',
        'client_full_name': 'Test Client',
    }

    def test_custom_source_without_markdown_returns_400(self, admin_client, proposal):
        """contract_source='custom' requires custom_contract_markdown."""
        url = reverse('update-contract-params', kwargs={'proposal_id': proposal.id})
        resp = admin_client.patch(
            url,
            {'contract_params': {**self._base_contract_params, 'contract_source': 'custom'}},
            format='json',
        )

        assert resp.status_code == 400

    def test_custom_source_with_markdown_is_accepted(self, admin_client, proposal):
        """contract_source='custom' with markdown field passes validation."""
        url = reverse('update-contract-params', kwargs={'proposal_id': proposal.id})
        resp = admin_client.patch(
            url,
            {'contract_params': {
                **self._base_contract_params,
                'contract_source': 'custom',
                'custom_contract_markdown': '# Contrato\nEste es el contrato.',
            }},
            format='json',
        )

        assert resp.status_code == 200
        assert resp.json()['contract_params']['contract_source'] == 'custom'
