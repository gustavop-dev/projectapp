"""Tests for the bulk_action endpoint.

Covers: delete, expire, resend actions, validation errors,
permission checks, and edge cases.
"""
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from content.models import BusinessProposal

pytestmark = pytest.mark.django_db

BULK_URL = reverse('bulk-action')


class TestBulkActionDelete:
    """POST /api/proposals/bulk-action/ with action=delete"""

    def test_deletes_selected_proposals(self, admin_client, db):
        p1 = BusinessProposal.objects.create(
            title='Delete Me 1', client_name='A', client_email='a@test.com',
            status='draft', expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        p2 = BusinessProposal.objects.create(
            title='Delete Me 2', client_name='B', client_email='b@test.com',
            status='draft', expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        response = admin_client.post(BULK_URL, {
            'ids': [p1.id, p2.id],
            'action': 'delete',
        }, format='json')
        assert response.status_code == 200
        assert response.data['affected'] == 2
        assert response.data['action'] == 'delete'
        assert not BusinessProposal.objects.filter(pk__in=[p1.id, p2.id]).exists()

    def test_delete_nonexistent_ids_returns_zero_affected(self, admin_client):
        response = admin_client.post(BULK_URL, {
            'ids': [999998, 999999],
            'action': 'delete',
        }, format='json')
        assert response.status_code == 200
        assert response.data['affected'] == 0


class TestBulkActionExpire:
    """POST /api/proposals/bulk-action/ with action=expire"""

    def test_expires_non_expired_proposals(self, admin_client, db):
        p1 = BusinessProposal.objects.create(
            title='Expire Me', client_name='C', client_email='c@test.com',
            status='sent', sent_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        response = admin_client.post(BULK_URL, {
            'ids': [p1.id],
            'action': 'expire',
        }, format='json')
        assert response.status_code == 200
        assert response.data['affected'] == 1
        p1.refresh_from_db()
        assert p1.status == 'expired'

    def test_skips_already_expired_proposals(self, admin_client, expired_proposal):
        response = admin_client.post(BULK_URL, {
            'ids': [expired_proposal.id],
            'action': 'expire',
        }, format='json')
        assert response.status_code == 200
        assert response.data['affected'] == 0


class TestBulkActionResend:
    """POST /api/proposals/bulk-action/ with action=resend"""

    @patch('content.services.proposal_service.ProposalService.resend_proposal')
    def test_resends_sent_proposals(self, mock_resend, admin_client, sent_proposal):
        response = admin_client.post(BULK_URL, {
            'ids': [sent_proposal.id],
            'action': 'resend',
        }, format='json')
        assert response.status_code == 200
        assert response.data['affected'] == 1
        mock_resend.assert_called_once_with(sent_proposal)

    @patch('content.services.proposal_service.ProposalService.resend_proposal')
    def test_skips_draft_proposals_on_resend(self, mock_resend, admin_client, proposal):
        response = admin_client.post(BULK_URL, {
            'ids': [proposal.id],
            'action': 'resend',
        }, format='json')
        assert response.status_code == 200
        assert response.data['affected'] == 0
        mock_resend.assert_not_called()

    @patch('content.services.proposal_service.ProposalService.resend_proposal')
    def test_skips_proposals_without_email(self, mock_resend, admin_client, db):
        p = BusinessProposal.objects.create(
            title='No Email', client_name='X', client_email='',
            status='sent', sent_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        response = admin_client.post(BULK_URL, {
            'ids': [p.id],
            'action': 'resend',
        }, format='json')
        assert response.status_code == 200
        assert response.data['affected'] == 0
        mock_resend.assert_not_called()

    @patch('content.services.proposal_service.ProposalService.resend_proposal', side_effect=Exception('SMTP error'))
    def test_resend_failure_does_not_crash(self, mock_resend, admin_client, sent_proposal):
        response = admin_client.post(BULK_URL, {
            'ids': [sent_proposal.id],
            'action': 'resend',
        }, format='json')
        assert response.status_code == 200
        assert response.data['affected'] == 0


class TestBulkActionValidation:
    """Validation and permission checks for bulk_action."""

    def test_empty_ids_returns_400(self, admin_client):
        response = admin_client.post(BULK_URL, {
            'ids': [],
            'action': 'delete',
        }, format='json')
        assert response.status_code == 400

    def test_missing_ids_returns_400(self, admin_client):
        response = admin_client.post(BULK_URL, {
            'action': 'delete',
        }, format='json')
        assert response.status_code == 400

    def test_invalid_action_returns_400(self, admin_client, sent_proposal):
        response = admin_client.post(BULK_URL, {
            'ids': [sent_proposal.id],
            'action': 'invalid_action',
        }, format='json')
        assert response.status_code == 400

    def test_unauthenticated_returns_403(self, api_client, sent_proposal):
        response = api_client.post(BULK_URL, {
            'ids': [sent_proposal.id],
            'action': 'delete',
        }, format='json')
        assert response.status_code in (401, 403)

    def test_non_staff_user_returns_403(self, api_client, db, sent_proposal):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        regular_user = User.objects.create_user(
            username='regular_bulk', password='pass123', is_staff=False,
        )
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(BULK_URL, {
            'ids': [sent_proposal.id],
            'action': 'delete',
        }, format='json')
        assert response.status_code == 403
