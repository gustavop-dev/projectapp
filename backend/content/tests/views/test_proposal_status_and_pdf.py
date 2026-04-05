"""Tests for update_proposal_status (ACCEPTED branch) and _generate_and_save_contract_pdf."""
import pytest
from unittest.mock import patch
from django.urls import reverse

from content.models import BusinessProposal, ProposalChangeLog, ProposalDocument

pytestmark = pytest.mark.django_db


class TestUpdateProposalStatusAccepted:
    def _url(self, proposal):
        return reverse('update-proposal-status', kwargs={'proposal_id': proposal.id})

    def test_returns_400_for_invalid_status(self, admin_client, proposal):
        resp = admin_client.patch(self._url(proposal), {'status': 'invalid'}, format='json')

        assert resp.status_code == 400
        assert 'Invalid status' in resp.json()['error']

    def test_returns_400_for_disallowed_transition(self, admin_client, proposal):
        # proposal fixture is 'draft' — cannot go to 'accepted' directly
        resp = admin_client.patch(self._url(proposal), {'status': 'accepted'}, format='json')

        assert resp.status_code == 400
        assert 'Cannot transition' in resp.json()['error']

    def test_creates_changelog_on_valid_transition(self, admin_client, sent_proposal):
        # sent → negotiating is an allowed transition
        resp = admin_client.patch(self._url(sent_proposal), {'status': 'negotiating'}, format='json')

        assert resp.status_code == 200
        assert ProposalChangeLog.objects.filter(
            proposal=sent_proposal,
            change_type='status_change',
            new_value='negotiating',
        ).exists()

    def test_accepted_transition_calls_platform_onboarding(self, admin_client, negotiating_proposal):
        with patch(
            'accounts.services.proposal_platform_onboarding.handle_proposal_accepted_for_platform'
        ) as mock_accept:
            resp = admin_client.patch(
                self._url(negotiating_proposal), {'status': 'accepted'}, format='json'
            )

        assert resp.status_code == 200
        mock_accept.assert_called_once()
        _args, kwargs = mock_accept.call_args
        assert kwargs['source'] == 'admin_panel'

    def test_non_accepted_transition_does_not_call_platform_onboarding(
        self, admin_client, sent_proposal
    ):
        with patch(
            'accounts.services.proposal_platform_onboarding.handle_proposal_accepted_for_platform'
        ) as mock_accept:
            resp = admin_client.patch(
                self._url(sent_proposal), {'status': 'negotiating'}, format='json'
            )

        assert resp.status_code == 200
        mock_accept.assert_not_called()

    def test_returns_401_for_unauthenticated(self, api_client, sent_proposal):
        resp = api_client.patch(self._url(sent_proposal), {'status': 'negotiating'}, format='json')

        assert resp.status_code == 401


class TestGenerateAndSaveContractPdf:
    def test_saves_contract_document_when_pdf_generated(self, proposal):
        with patch('content.services.contract_pdf_service.generate_contract_pdf') as mock_gen:
            mock_gen.return_value = b'%PDF-1.4 fake pdf content'
            from content.views.proposal import _generate_and_save_contract_pdf
            _generate_and_save_contract_pdf(proposal)

        assert ProposalDocument.objects.filter(
            proposal=proposal,
            document_type=ProposalDocument.DOC_TYPE_CONTRACT,
        ).exists()

    def test_returns_early_when_pdf_generation_returns_none(self, proposal):
        with patch('content.services.contract_pdf_service.generate_contract_pdf') as mock_gen:
            mock_gen.return_value = None
            from content.views.proposal import _generate_and_save_contract_pdf
            _generate_and_save_contract_pdf(proposal)

        assert not ProposalDocument.objects.filter(
            proposal=proposal,
            document_type=ProposalDocument.DOC_TYPE_CONTRACT,
        ).exists()

    def test_get_or_create_prevents_duplicate_contract_documents(self, proposal):
        with patch('content.services.contract_pdf_service.generate_contract_pdf') as mock_gen:
            mock_gen.return_value = b'%PDF-1.4 fake pdf content'
            from content.views.proposal import _generate_and_save_contract_pdf
            _generate_and_save_contract_pdf(proposal)
            _generate_and_save_contract_pdf(proposal)

        assert ProposalDocument.objects.filter(
            proposal=proposal,
            document_type=ProposalDocument.DOC_TYPE_CONTRACT,
        ).count() == 1
