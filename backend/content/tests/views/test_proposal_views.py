"""
Tests for proposal API views.

Covers: public retrieve/respond/pdf, admin CRUD, section update,
bulk reorder, auth check, permission checks, edge cases.
"""
import pytest
from unittest.mock import patch
from django.urls import reverse

from content.models import BusinessProposal, ProposalSection


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

class TestRetrievePublicProposal:
    def test_returns_200_for_valid_proposal(self, api_client, sent_proposal):
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 200

    def test_increments_view_count(self, api_client, sent_proposal):
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        api_client.get(url)
        sent_proposal.refresh_from_db()
        assert sent_proposal.view_count == 1

    def test_sets_first_viewed_at_on_first_visit(self, api_client, sent_proposal):
        assert sent_proposal.first_viewed_at is None
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        api_client.get(url)
        sent_proposal.refresh_from_db()
        assert sent_proposal.first_viewed_at is not None

    def test_updates_status_from_sent_to_viewed(self, api_client, sent_proposal):
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        api_client.get(url)
        sent_proposal.refresh_from_db()
        assert sent_proposal.status == 'viewed'

    def test_returns_410_for_expired_proposal(self, api_client, expired_proposal):
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': expired_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 410

    def test_returns_404_for_nonexistent_uuid(self, api_client):
        import uuid
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == 404


class TestDownloadProposalPdf:
    def test_returns_501_not_implemented(self, api_client, sent_proposal):
        url = reverse('download-proposal-pdf', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 501

    def test_returns_410_for_expired_proposal(self, api_client, expired_proposal):
        url = reverse('download-proposal-pdf', kwargs={'proposal_uuid': expired_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 410


class TestRespondToProposal:
    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    def test_accepts_proposal_returns_200(self, mock_notify, api_client, sent_proposal):
        url = reverse('respond-to-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.post(url, {'action': 'accepted'}, format='json')
        assert response.status_code == 200
        sent_proposal.refresh_from_db()
        assert sent_proposal.status == 'accepted'

    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    def test_rejects_proposal_returns_200(self, mock_notify, api_client, sent_proposal):
        url = reverse('respond-to-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.post(url, {'action': 'rejected'}, format='json')
        assert response.status_code == 200
        sent_proposal.refresh_from_db()
        assert sent_proposal.status == 'rejected'

    def test_returns_400_for_invalid_action(self, api_client, sent_proposal):
        url = reverse('respond-to-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.post(url, {'action': 'invalid'}, format='json')
        assert response.status_code == 400

    def test_returns_400_for_draft_proposal(self, api_client, proposal):
        url = reverse('respond-to-proposal', kwargs={'proposal_uuid': proposal.uuid})
        response = api_client.post(url, {'action': 'accepted'}, format='json')
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

class TestAdminListProposals:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('list-proposals'))
        assert response.status_code in (401, 403)

    def test_returns_200_for_admin(self, admin_client, proposal):
        response = admin_client.get(reverse('list-proposals'))
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_filters_by_status(self, admin_client, proposal, sent_proposal):
        response = admin_client.get(reverse('list-proposals'), {'status': 'sent'})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['status'] == 'sent'


class TestAdminRetrieveProposal:
    def test_returns_200_for_admin(self, admin_client, proposal):
        url = reverse('retrieve-proposal', kwargs={'proposal_id': proposal.id})
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('retrieve-proposal', kwargs={'proposal_id': 99999})
        response = admin_client.get(url)
        assert response.status_code == 404


class TestAdminCreateProposal:
    @patch('content.services.proposal_service.ProposalService.get_default_sections', return_value=[])
    def test_creates_proposal_returns_201(self, mock_sections, admin_client):
        payload = {
            'title': 'New Proposal',
            'client_name': 'New Client',
            'client_email': 'new@client.com',
            'language': 'es',
            'total_investment': '10000.00',
            'currency': 'COP',
        }
        response = admin_client.post(
            reverse('create-proposal'), payload, format='json'
        )
        assert response.status_code == 201
        assert BusinessProposal.objects.count() == 1

    def test_returns_400_with_missing_fields(self, admin_client):
        response = admin_client.post(
            reverse('create-proposal'), {}, format='json'
        )
        assert response.status_code == 400

    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.post(reverse('create-proposal'), {}, format='json')
        assert response.status_code in (401, 403)


class TestAdminUpdateProposal:
    def test_updates_proposal_returns_200(self, admin_client, proposal):
        url = reverse('update-proposal', kwargs={'proposal_id': proposal.id})
        response = admin_client.patch(
            url, {'title': 'Updated Title'}, format='json'
        )
        assert response.status_code == 200
        proposal.refresh_from_db()
        assert proposal.title == 'Updated Title'

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('update-proposal', kwargs={'proposal_id': 99999})
        response = admin_client.patch(url, {}, format='json')
        assert response.status_code == 404


class TestAdminDeleteProposal:
    def test_deletes_proposal_returns_204(self, admin_client, proposal):
        url = reverse('delete-proposal', kwargs={'proposal_id': proposal.id})
        response = admin_client.delete(url)
        assert response.status_code == 204
        assert BusinessProposal.objects.count() == 0

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('delete-proposal', kwargs={'proposal_id': 99999})
        response = admin_client.delete(url)
        assert response.status_code == 404


class TestAdminSendProposal:
    @patch('content.services.proposal_service.ProposalService.send_proposal')
    def test_sends_proposal_returns_200(self, mock_send, admin_client, proposal):
        url = reverse('send-proposal', kwargs={'proposal_id': proposal.id})
        response = admin_client.post(url, format='json')
        assert response.status_code == 200
        mock_send.assert_called_once()

    @patch('content.services.proposal_service.ProposalService.send_proposal')
    def test_returns_400_on_service_error(self, mock_send, admin_client, proposal):
        mock_send.side_effect = ValueError('Missing client_email')
        url = reverse('send-proposal', kwargs={'proposal_id': proposal.id})
        response = admin_client.post(url, format='json')
        assert response.status_code == 400


class TestAdminUpdateProposalSection:
    def test_updates_section_returns_200(self, admin_client, proposal_section):
        url = reverse('update-proposal-section', kwargs={'section_id': proposal_section.id})
        response = admin_client.patch(
            url, {'title': 'Updated Section'}, format='json'
        )
        assert response.status_code == 200
        proposal_section.refresh_from_db()
        assert proposal_section.title == 'Updated Section'

    def test_returns_404_for_nonexistent_section(self, admin_client):
        url = reverse('update-proposal-section', kwargs={'section_id': 99999})
        response = admin_client.patch(url, {}, format='json')
        assert response.status_code == 404


class TestBulkReorderSections:
    def test_reorders_sections_returns_200(self, admin_client, proposal, proposal_section):
        s2 = ProposalSection.objects.create(
            proposal=proposal, section_type='timeline', title='Timeline', order=1
        )
        url = reverse('reorder-sections', kwargs={'proposal_id': proposal.id})
        payload = {
            'sections': [
                {'id': proposal_section.id, 'order': 1},
                {'id': s2.id, 'order': 0},
            ]
        }
        response = admin_client.post(url, payload, format='json')
        assert response.status_code == 200
        assert response.data['reordered'] == 2

    def test_returns_400_for_invalid_sections_format(self, admin_client, proposal):
        url = reverse('reorder-sections', kwargs={'proposal_id': proposal.id})
        response = admin_client.post(url, {'sections': 'invalid'}, format='json')
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Auth check
# ---------------------------------------------------------------------------

class TestCheckAdminAuth:
    def test_returns_200_for_admin(self, admin_client):
        response = admin_client.get(reverse('check-admin-auth'))
        assert response.status_code == 200
        assert response.data['user']['is_staff'] is True

    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('check-admin-auth'))
        assert response.status_code in (401, 403)

    def test_returns_403_for_non_staff_user(self, api_client, db):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(
            username='regular', email='regular@test.com', password='pass123'
        )
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse('check-admin-auth'))
        assert response.status_code == 403
