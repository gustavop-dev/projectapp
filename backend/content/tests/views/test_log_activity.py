"""Tests for the log_activity endpoint.

Covers: happy path, invalid change_type, empty description,
last_activity_at update, permission checks.
"""
import pytest
from django.urls import reverse
from django.utils import timezone

from content.models import BusinessProposal, ProposalChangeLog

pytestmark = pytest.mark.django_db


class TestLogActivity:
    """POST /api/proposals/<id>/log-activity/"""

    def _url(self, proposal_id):
        return reverse('log-activity', kwargs={'proposal_id': proposal_id})

    # ── Happy paths ──

    def test_log_call_activity_returns_201(self, admin_client, sent_proposal):
        response = admin_client.post(self._url(sent_proposal.id), {
            'change_type': 'call',
            'description': 'Llamada de seguimiento con el cliente.',
        })
        assert response.status_code == 201
        assert response.data['change_type'] == 'call'
        assert response.data['description'] == 'Llamada de seguimiento con el cliente.'

    def test_log_meeting_activity_returns_201(self, admin_client, sent_proposal):
        response = admin_client.post(self._url(sent_proposal.id), {
            'change_type': 'meeting',
            'description': 'Reunión virtual para revisión de requerimientos.',
        })
        assert response.status_code == 201
        assert response.data['change_type'] == 'meeting'

    def test_log_followup_activity_returns_201(self, admin_client, sent_proposal):
        response = admin_client.post(self._url(sent_proposal.id), {
            'change_type': 'followup',
            'description': 'Email de seguimiento enviado.',
        })
        assert response.status_code == 201
        assert response.data['change_type'] == 'followup'

    def test_log_note_activity_returns_201(self, admin_client, sent_proposal):
        response = admin_client.post(self._url(sent_proposal.id), {
            'change_type': 'note',
            'description': 'Cliente compara con otra agencia.',
        })
        assert response.status_code == 201
        assert response.data['change_type'] == 'note'

    def test_creates_changelog_entry(self, admin_client, sent_proposal):
        before_count = ProposalChangeLog.objects.filter(proposal=sent_proposal).count()
        admin_client.post(self._url(sent_proposal.id), {
            'change_type': 'call',
            'description': 'Seguimiento telefónico.',
        })
        after_count = ProposalChangeLog.objects.filter(proposal=sent_proposal).count()
        assert after_count == before_count + 1

    def test_updates_last_activity_at(self, admin_client, sent_proposal):
        old_activity = sent_proposal.last_activity_at
        admin_client.post(self._url(sent_proposal.id), {
            'change_type': 'call',
            'description': 'Llamada de seguimiento.',
        })
        sent_proposal.refresh_from_db()
        assert sent_proposal.last_activity_at is not None
        if old_activity:
            assert sent_proposal.last_activity_at >= old_activity

    # ── Error conditions ──

    def test_invalid_change_type_returns_400(self, admin_client, sent_proposal):
        response = admin_client.post(self._url(sent_proposal.id), {
            'change_type': 'invalid_type',
            'description': 'Some description.',
        })
        assert response.status_code == 400
        assert 'change_type' in response.data.get('error', '')

    def test_empty_description_returns_400(self, admin_client, sent_proposal):
        response = admin_client.post(self._url(sent_proposal.id), {
            'change_type': 'call',
            'description': '',
        })
        assert response.status_code == 400
        assert 'description' in response.data.get('error', '')

    def test_whitespace_only_description_returns_400(self, admin_client, sent_proposal):
        response = admin_client.post(self._url(sent_proposal.id), {
            'change_type': 'note',
            'description': '   ',
        })
        assert response.status_code == 400

    def test_missing_change_type_returns_400(self, admin_client, sent_proposal):
        response = admin_client.post(self._url(sent_proposal.id), {
            'description': 'No type provided.',
        })
        assert response.status_code == 400

    def test_nonexistent_proposal_returns_404(self, admin_client):
        response = admin_client.post(self._url(999999), {
            'change_type': 'call',
            'description': 'Should not work.',
        })
        assert response.status_code == 404

    # ── Permission checks ──

    def test_unauthenticated_returns_403(self, api_client, sent_proposal):
        response = api_client.post(self._url(sent_proposal.id), {
            'change_type': 'call',
            'description': 'Unauthorized attempt.',
        })
        assert response.status_code in (401, 403)

    def test_non_staff_user_returns_403(self, api_client, db, sent_proposal):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        regular_user = User.objects.create_user(
            username='regular', password='pass123', is_staff=False,
        )
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(self._url(sent_proposal.id), {
            'change_type': 'call',
            'description': 'Non-staff attempt.',
        })
        assert response.status_code == 403
