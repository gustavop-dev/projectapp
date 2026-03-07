"""Tests for proposal API views.

Covers: public retrieve/respond/pdf, admin CRUD, section update,
bulk reorder, auth check, permission checks, edge cases.
"""
from datetime import datetime
from datetime import timezone as dt_tz
from unittest.mock import patch

import pytest
from django.urls import reverse
from freezegun import freeze_time

from content.models import (
    BusinessProposal,
    ProposalChangeLog,
    ProposalSection,
    ProposalSectionView,
    ProposalShareLink,
    ProposalViewEvent,
)

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
        from uuid import UUID
        fixed_uuid = UUID('00000000-0000-0000-0000-000000000099')
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': fixed_uuid})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_expired_proposal_already_expired_status_returns_410(self, api_client, expired_proposal):
        expired_proposal.status = 'expired'
        expired_proposal.save(update_fields=['status'])
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': expired_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 410

    @freeze_time('2026-03-01 12:00:00')
    def test_expired_proposal_with_sent_status_updates_to_expired(self, api_client, db):
        proposal = BusinessProposal.objects.create(
            title='Stale Sent',
            client_name='Client',
            client_email='c@test.com',
            status='sent',
            expires_at=datetime(2026, 2, 28, 12, 0, 0, tzinfo=dt_tz.utc),
        )
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 410
        proposal.refresh_from_db()
        assert proposal.status == 'expired'

    def test_does_not_change_status_from_draft_to_viewed(self, api_client, proposal):
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': proposal.uuid})
        api_client.get(url)
        proposal.refresh_from_db()
        assert proposal.status == 'draft'


class TestDownloadProposalPdf:
    """Tests for the download_proposal_pdf endpoint."""

    @patch('content.services.proposal_pdf_service.ProposalPdfService.generate')
    def test_returns_pdf_when_generation_succeeds(
        self, mock_generate, api_client, sent_proposal,
    ):
        """Verify a successful PDF generation returns 200 with PDF content."""
        mock_generate.return_value = b'%PDF-fake-content'
        url = reverse('download-proposal-pdf', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert b'%PDF-fake-content' in response.content

    @patch('content.services.proposal_pdf_service.ProposalPdfService.generate')
    def test_returns_500_when_generation_fails(
        self, mock_generate, api_client, sent_proposal,
    ):
        """Verify a failed PDF generation returns 500."""
        mock_generate.return_value = None
        url = reverse('download-proposal-pdf', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 500

    def test_returns_410_for_expired_proposal(self, api_client, expired_proposal):
        """Verify expired proposals return 410 Gone."""
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

    def test_creates_proposal_with_default_sections(self, admin_client):
        payload = {
            'title': 'Full Proposal',
            'client_name': 'Client',
            'client_email': 'c@test.com',
            'language': 'es',
            'total_investment': '5000.00',
            'currency': 'COP',
        }
        response = admin_client.post(
            reverse('create-proposal'), payload, format='json'
        )
        assert response.status_code == 201
        assert len(response.data['sections']) == 12

    def test_auto_fills_investment_section_from_proposal_data(self, admin_client):
        """Investment section auto-fills totalInvestment, currency, and paymentOptions."""
        payload = {
            'title': 'Investment Test',
            'client_name': 'Client',
            'client_email': 'c@test.com',
            'language': 'es',
            'total_investment': '3500000.00',
            'currency': 'COP',
        }
        response = admin_client.post(
            reverse('create-proposal'), payload, format='json'
        )
        assert response.status_code == 201
        investment_section = next(
            s for s in response.data['sections']
            if s['section_type'] == 'investment'
        )
        content = investment_section['content_json']
        assert content['totalInvestment'] == '$3,500,000'
        assert content['currency'] == 'COP'
        assert len(content['paymentOptions']) == 3

    def test_auto_fills_greeting_client_name(self, admin_client):
        """Greeting section auto-fills clientName from the proposal client_name."""
        payload = {
            'title': 'Greeting Test',
            'client_name': 'María García',
            'client_email': 'maria@test.com',
            'language': 'es',
            'total_investment': '1000.00',
            'currency': 'COP',
        }
        response = admin_client.post(
            reverse('create-proposal'), payload, format='json'
        )
        assert response.status_code == 201
        greeting_section = next(
            s for s in response.data['sections']
            if s['section_type'] == 'greeting'
        )
        assert greeting_section['content_json']['clientName'] == 'María García'

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

    def test_returns_400_for_invalid_data(self, admin_client, proposal):
        url = reverse('update-proposal', kwargs={'proposal_id': proposal.id})
        response = admin_client.patch(
            url, {'expires_at': '2020-01-01T00:00:00Z'}, format='json'
        )
        assert response.status_code == 400

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

    def test_returns_400_for_invalid_content_json(self, admin_client, proposal_section):
        url = reverse('update-proposal-section', kwargs={'section_id': proposal_section.id})
        response = admin_client.patch(
            url, {'content_json': 'not-a-dict'}, format='json'
        )
        assert response.status_code == 400

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
# create_proposal_from_json
# ---------------------------------------------------------------------------

class TestCreateProposalFromJSON:
    def _minimal_payload(self):
        """Return a minimal valid create-from-json payload."""
        return {
            'title': 'JSON Proposal',
            'client_name': 'JSON Client',
            'sections': {
                'general': {'clientName': 'JSON Client'},
            },
        }

    def test_creates_proposal_returns_201(self, admin_client):
        url = reverse('create-proposal-from-json')
        response = admin_client.post(url, self._minimal_payload(), format='json')
        assert response.status_code == 201

    def test_creates_proposal_with_correct_title(self, admin_client):
        url = reverse('create-proposal-from-json')
        response = admin_client.post(url, self._minimal_payload(), format='json')
        assert response.data['title'] == 'JSON Proposal'

    def test_creates_default_12_sections(self, admin_client):
        url = reverse('create-proposal-from-json')
        response = admin_client.post(url, self._minimal_payload(), format='json')
        assert response.status_code == 201
        assert len(response.data['sections']) == 12

    def test_greeting_section_has_client_name(self, admin_client):
        url = reverse('create-proposal-from-json')
        payload = self._minimal_payload()
        payload['sections']['general']['clientName'] = 'JSON Client'
        response = admin_client.post(url, payload, format='json')
        sections = {s['section_type']: s for s in response.data['sections']}
        assert sections['greeting']['content_json']['clientName'] == 'JSON Client'

    def test_custom_section_content_overrides_default(self, admin_client):
        url = reverse('create-proposal-from-json')
        payload = self._minimal_payload()
        payload['sections']['executiveSummary'] = {
            'title': 'Custom Summary',
            'paragraphs': ['Custom paragraph.'],
        }
        response = admin_client.post(url, payload, format='json')
        assert response.status_code == 201
        sections = {s['section_type']: s for s in response.data['sections']}
        assert sections['executive_summary']['content_json']['title'] == 'Custom Summary'

    def test_returns_400_for_missing_general_key(self, admin_client):
        url = reverse('create-proposal-from-json')
        payload = {
            'title': 'Bad Proposal',
            'client_name': 'Client',
            'sections': {'executiveSummary': {}},
        }
        response = admin_client.post(url, payload, format='json')
        assert response.status_code == 400

    def test_returns_403_for_non_admin(self, api_client, db):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='nonadmin', password='pass')
        api_client.force_authenticate(user=user)
        url = reverse('create-proposal-from-json')
        response = api_client.post(url, self._minimal_payload(), format='json')
        assert response.status_code == 403

    def test_returns_401_for_unauthenticated(self, api_client):
        url = reverse('create-proposal-from-json')
        response = api_client.post(url, self._minimal_payload(), format='json')
        assert response.status_code in (401, 403)


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


# ---------------------------------------------------------------------------
# Share link endpoints
# ---------------------------------------------------------------------------

class TestCreateShareLink:
    def _url(self, uuid):
        return reverse('create-share-link', kwargs={'proposal_uuid': uuid})

    @patch('content.services.proposal_email_service.ProposalEmailService.send_share_notification', return_value=True)
    def test_creates_share_link_returns_201(self, mock_notify, api_client, sent_proposal):
        response = api_client.post(
            self._url(sent_proposal.uuid),
            {'name': 'Bob', 'email': 'bob@co.com'},
            format='json',
        )
        assert response.status_code == 201
        assert response.data['shared_by_name'] == 'Bob'
        assert ProposalShareLink.objects.count() == 1

    @patch('content.services.proposal_email_service.ProposalEmailService.send_share_notification', return_value=True)
    def test_sends_share_notification(self, mock_notify, api_client, sent_proposal):
        """Creating a share link triggers a notification email to the sales team."""
        response = api_client.post(
            self._url(sent_proposal.uuid),
            {'name': 'Bob', 'email': 'bob@co.com'},
            format='json',
        )
        assert response.status_code == 201
        mock_notify.assert_called_once()

    def test_returns_400_when_name_missing(self, api_client, sent_proposal):
        response = api_client.post(
            self._url(sent_proposal.uuid),
            {'email': 'bob@co.com'},
            format='json',
        )
        assert response.status_code == 400

    def test_returns_404_for_inactive_proposal(self, api_client, sent_proposal):
        sent_proposal.is_active = False
        sent_proposal.save(update_fields=['is_active'])
        response = api_client.post(
            self._url(sent_proposal.uuid),
            {'name': 'Bob'},
            format='json',
        )
        assert response.status_code == 404

    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_share_notification',
        side_effect=Exception('SMTP error'),
    )
    def test_still_creates_link_when_notification_fails(self, mock_notify, api_client, sent_proposal):
        response = api_client.post(
            self._url(sent_proposal.uuid),
            {'name': 'Bob'},
            format='json',
        )
        assert response.status_code == 201
        assert ProposalShareLink.objects.count() == 1


class TestRetrieveSharedProposal:
    def _url(self, share_uuid):
        return reverse('retrieve-shared-proposal', kwargs={'share_uuid': share_uuid})

    def test_returns_200_with_proposal_data(self, api_client, share_link):
        response = api_client.get(self._url(share_link.uuid))
        assert response.status_code == 200
        assert response.data['uuid'] is not None

    def test_increments_view_count(self, api_client, share_link):
        api_client.get(self._url(share_link.uuid))
        share_link.refresh_from_db()
        assert share_link.view_count == 1

    def test_sets_first_viewed_at_on_first_visit(self, api_client, share_link):
        assert share_link.first_viewed_at is None
        api_client.get(self._url(share_link.uuid))
        share_link.refresh_from_db()
        assert share_link.first_viewed_at is not None

    def test_records_viewer_info_from_query_params(self, api_client, share_link):
        api_client.get(self._url(share_link.uuid) + '?name=Carlos&email=carlos@test.com')
        share_link.refresh_from_db()
        assert share_link.recipient_name == 'Carlos'
        assert share_link.recipient_email == 'carlos@test.com'

    def test_does_not_overwrite_existing_recipient(self, api_client, share_link):
        share_link.recipient_name = 'Original'
        share_link.save(update_fields=['recipient_name'])
        api_client.get(self._url(share_link.uuid) + '?name=Override')
        share_link.refresh_from_db()
        assert share_link.recipient_name == 'Original'

    def test_returns_404_for_inactive_proposal(self, api_client, share_link):
        share_link.proposal.is_active = False
        share_link.proposal.save(update_fields=['is_active'])
        response = api_client.get(self._url(share_link.uuid))
        assert response.status_code == 404

    def test_returns_410_for_expired_proposal(self, api_client, share_link):
        share_link.proposal.expires_at = datetime(2020, 1, 1, tzinfo=dt_tz.utc)
        share_link.proposal.status = 'expired'
        share_link.proposal.save(update_fields=['expires_at', 'status'])
        response = api_client.get(self._url(share_link.uuid))
        assert response.status_code == 410


# ---------------------------------------------------------------------------
# Schedule follow-up
# ---------------------------------------------------------------------------

class TestScheduleFollowup:
    def _url(self, uuid):
        return reverse('schedule-followup', kwargs={'proposal_uuid': uuid})

    @patch('content.tasks.send_scheduled_followup.schedule')
    def test_schedules_followup_returns_200(self, mock_task, api_client, rejected_proposal):
        response = api_client.post(
            self._url(rejected_proposal.uuid),
            {'months': 3},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['status'] == 'scheduled'
        rejected_proposal.refresh_from_db()
        assert rejected_proposal.followup_scheduled_at is not None

    def test_returns_400_for_non_rejected_proposal(self, api_client, sent_proposal):
        response = api_client.post(
            self._url(sent_proposal.uuid),
            {'months': 3},
            format='json',
        )
        assert response.status_code == 400

    @freeze_time('2026-03-10 12:00:00')
    @patch('content.tasks.send_scheduled_followup.schedule')
    def test_returns_400_when_already_scheduled(self, mock_task, api_client, rejected_proposal):
        from django.utils import timezone
        rejected_proposal.followup_scheduled_at = timezone.now()
        rejected_proposal.save(update_fields=['followup_scheduled_at'])
        response = api_client.post(
            self._url(rejected_proposal.uuid),
            {'months': 3},
            format='json',
        )
        assert response.status_code == 400

    def test_returns_400_for_invalid_months(self, api_client, rejected_proposal):
        response = api_client.post(
            self._url(rejected_proposal.uuid),
            {'months': 0},
            format='json',
        )
        assert response.status_code == 400

    def test_returns_400_for_months_over_12(self, api_client, rejected_proposal):
        response = api_client.post(
            self._url(rejected_proposal.uuid),
            {'months': 13},
            format='json',
        )
        assert response.status_code == 400

    @patch('content.tasks.send_scheduled_followup.schedule')
    def test_creates_change_log_entry(self, mock_task, api_client, rejected_proposal):
        api_client.post(
            self._url(rejected_proposal.uuid),
            {'months': 6},
            format='json',
        )
        log = ProposalChangeLog.objects.filter(
            proposal=rejected_proposal, field_name='followup_scheduled_at'
        )
        assert log.exists()

    @patch('content.tasks.send_scheduled_followup.schedule', side_effect=Exception('Huey down'))
    def test_still_saves_followup_when_task_scheduling_fails(self, mock_task, api_client, rejected_proposal):
        response = api_client.post(
            self._url(rejected_proposal.uuid),
            {'months': 3},
            format='json',
        )
        assert response.status_code == 200
        rejected_proposal.refresh_from_db()
        assert rejected_proposal.followup_scheduled_at is not None


# ---------------------------------------------------------------------------
# Track engagement
# ---------------------------------------------------------------------------

class TestTrackProposalEngagement:
    def _url(self, uuid):
        return reverse('track-proposal-engagement', kwargs={'proposal_uuid': uuid})

    def test_records_section_views_returns_200(self, api_client, sent_proposal):
        """Valid engagement payload creates view event and section view records."""
        payload = {
            'session_id': 'sess-001',
            'sections': [
                {
                    'section_type': 'greeting',
                    'section_title': 'Welcome',
                    'time_spent_seconds': 5.2,
                    'entered_at': '2026-03-01T10:00:00Z',
                },
            ],
        }
        response = api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        assert response.status_code == 200
        assert ProposalViewEvent.objects.filter(proposal=sent_proposal).count() == 1
        assert ProposalSectionView.objects.count() == 1

    def test_returns_400_when_session_id_missing(self, api_client, sent_proposal):
        payload = {'sections': [{'section_type': 'greeting', 'time_spent_seconds': 1}]}
        response = api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        assert response.status_code == 400

    def test_returns_400_when_sections_empty(self, api_client, sent_proposal):
        payload = {'session_id': 'sess-001', 'sections': []}
        response = api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        assert response.status_code == 400

    def test_updates_existing_section_view_on_duplicate(self, api_client, sent_proposal):
        """Sending the same section twice updates time_spent rather than creating a duplicate."""
        payload = {
            'session_id': 'sess-002',
            'sections': [
                {
                    'section_type': 'investment',
                    'section_title': 'Investment',
                    'time_spent_seconds': 10.0,
                    'entered_at': '2026-03-01T10:00:00Z',
                },
            ],
        }
        api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        payload['sections'][0]['time_spent_seconds'] = 25.0
        api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        sv = ProposalSectionView.objects.filter(section_type='investment')
        assert sv.count() == 1
        assert sv.first().time_spent_seconds == 25.0

    def test_skips_section_without_section_type(self, api_client, sent_proposal):
        payload = {
            'session_id': 'sess-003',
            'sections': [
                {'section_title': 'No Type', 'time_spent_seconds': 1},
            ],
        }
        response = api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        assert response.status_code == 200
        assert ProposalSectionView.objects.count() == 0

    @patch('content.services.proposal_email_service.ProposalEmailService.send_revisit_alert', return_value=True)
    def test_sends_revisit_alert_after_3_sessions(self, mock_alert, api_client, sent_proposal):
        """Revisit alert fires after 3 distinct session IDs track engagement."""
        for i in range(3):
            payload = {
                'session_id': f'sess-{i}',
                'sections': [
                    {
                        'section_type': 'greeting',
                        'section_title': 'Welcome',
                        'time_spent_seconds': 5,
                        'entered_at': '2026-03-01T10:00:00Z',
                    },
                ],
            }
            api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        mock_alert.assert_called_once()
        assert mock_alert.call_args[0][0].pk == sent_proposal.pk


# ---------------------------------------------------------------------------
# Comment on proposal
# ---------------------------------------------------------------------------

class TestCommentOnProposal:
    def _url(self, uuid):
        return reverse('comment-on-proposal', kwargs={'proposal_uuid': uuid})

    @patch('content.services.proposal_email_service.ProposalEmailService.send_comment_notification')
    def test_submits_comment_returns_200(self, mock_notify, api_client, sent_proposal):
        response = api_client.post(
            self._url(sent_proposal.uuid),
            {'comment': 'Can we negotiate the price?'},
            format='json',
        )
        assert response.status_code == 200
        assert ProposalChangeLog.objects.filter(
            proposal=sent_proposal, change_type='commented'
        ).exists()

    def test_returns_400_for_empty_comment(self, api_client, sent_proposal):
        response = api_client.post(
            self._url(sent_proposal.uuid),
            {'comment': ''},
            format='json',
        )
        assert response.status_code == 400

    def test_returns_400_for_draft_proposal(self, api_client, proposal):
        response = api_client.post(
            self._url(proposal.uuid),
            {'comment': 'Hello'},
            format='json',
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Duplicate proposal
# ---------------------------------------------------------------------------

class TestDuplicateProposal:
    def _url(self, pk):
        return reverse('duplicate-proposal', kwargs={'proposal_id': pk})

    def test_duplicates_proposal_returns_201(self, admin_client, proposal, proposal_section):
        response = admin_client.post(self._url(proposal.id))
        assert response.status_code == 201
        assert BusinessProposal.objects.count() == 2
        new = BusinessProposal.objects.exclude(pk=proposal.id).first()
        assert new.title == f'{proposal.title} (copia)'
        assert new.status == 'draft'

    def test_duplicated_proposal_has_sections(self, admin_client, proposal, proposal_section):
        response = admin_client.post(self._url(proposal.id))
        assert response.status_code == 201
        new_id = response.data['id']
        assert ProposalSection.objects.filter(proposal_id=new_id).count() == 1

    def test_creates_change_log_entry(self, admin_client, proposal):
        admin_client.post(self._url(proposal.id))
        new = BusinessProposal.objects.exclude(pk=proposal.id).first()
        assert ProposalChangeLog.objects.filter(
            proposal=new, change_type='duplicated'
        ).exists()

    def test_returns_401_for_unauthenticated(self, api_client, proposal):
        response = api_client.post(self._url(proposal.id))
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Toggle active
# ---------------------------------------------------------------------------

class TestToggleProposalActive:
    def _url(self, pk):
        return reverse('toggle-proposal-active', kwargs={'proposal_id': pk})

    def test_toggles_active_to_false(self, admin_client, proposal):
        assert proposal.is_active is True
        response = admin_client.post(self._url(proposal.id))
        assert response.status_code == 200
        proposal.refresh_from_db()
        assert proposal.is_active is False

    def test_toggles_active_to_true(self, admin_client, proposal):
        proposal.is_active = False
        proposal.save(update_fields=['is_active'])
        response = admin_client.post(self._url(proposal.id))
        assert response.status_code == 200
        proposal.refresh_from_db()
        assert proposal.is_active is True

    def test_returns_401_for_unauthenticated(self, api_client, proposal):
        response = api_client.post(self._url(proposal.id))
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Resend proposal
# ---------------------------------------------------------------------------

class TestResendProposal:
    def _url(self, pk):
        return reverse('resend-proposal', kwargs={'proposal_id': pk})

    @patch('content.services.proposal_service.ProposalService.resend_proposal')
    def test_resends_proposal_returns_200(self, mock_resend, admin_client, sent_proposal):
        response = admin_client.post(self._url(sent_proposal.id))
        assert response.status_code == 200
        mock_resend.assert_called_once()

    @patch('content.services.proposal_service.ProposalService.resend_proposal')
    def test_creates_change_log_entry(self, mock_resend, admin_client, sent_proposal):
        admin_client.post(self._url(sent_proposal.id))
        assert ProposalChangeLog.objects.filter(
            proposal=sent_proposal, change_type='resent'
        ).exists()

    @patch(
        'content.services.proposal_service.ProposalService.resend_proposal',
        side_effect=ValueError('Missing email'),
    )
    def test_returns_400_on_service_error(self, mock_resend, admin_client, sent_proposal):
        response = admin_client.post(self._url(sent_proposal.id))
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class TestRetrieveProposalAnalytics:
    def _url(self, pk):
        return reverse('proposal-analytics', kwargs={'proposal_id': pk})

    def test_returns_200_with_analytics_data(self, admin_client, sent_proposal):
        response = admin_client.get(self._url(sent_proposal.id))
        assert response.status_code == 200
        data = response.data
        assert 'total_views' in data
        assert 'unique_sessions' in data
        assert 'sections' in data
        assert 'funnel' in data
        assert 'comparison' in data
        assert 'share_links' in data

    def test_returns_time_to_first_view_when_available(self, admin_client, viewed_proposal):
        response = admin_client.get(self._url(viewed_proposal.id))
        assert response.status_code == 200
        assert response.data['time_to_first_view_hours'] is not None

    def test_returns_401_for_unauthenticated(self, api_client, sent_proposal):
        response = api_client.get(self._url(sent_proposal.id))
        assert response.status_code in (401, 403)


class TestExportProposalAnalyticsCsv:
    def _url(self, pk):
        return reverse('proposal-analytics-csv', kwargs={'proposal_id': pk})

    def test_returns_csv_content_type(self, admin_client, sent_proposal):
        response = admin_client.get(self._url(sent_proposal.id))
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']

    def test_returns_401_for_unauthenticated(self, api_client, sent_proposal):
        response = api_client.get(self._url(sent_proposal.id))
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestProposalDashboard:
    def _url(self):
        return reverse('proposal-dashboard')

    def test_returns_200_with_dashboard_data(self, admin_client, sent_proposal):
        response = admin_client.get(self._url())
        assert response.status_code == 200
        data = response.data
        assert 'total_proposals' in data
        assert 'by_status' in data
        assert 'conversion_rate' in data
        assert 'monthly_trend' in data

    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(self._url())
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# JSON template
# ---------------------------------------------------------------------------

class TestGetProposalJsonTemplate:
    def _url(self):
        return reverse('proposal-json-template')

    def test_returns_200_with_template_json(self, admin_client):
        response = admin_client.get(self._url())
        assert response.status_code == 200
        assert '_meta' in response.data

    def test_accepts_lang_query_param(self, admin_client):
        response = admin_client.get(self._url() + '?lang=en')
        assert response.status_code == 200

    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(self._url())
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Respond — re-engagement scheduling
# ---------------------------------------------------------------------------

class TestRespondReengagement:
    def _url(self, uuid):
        return reverse('respond-to-proposal', kwargs={'proposal_uuid': uuid})

    @patch('content.tasks.send_rejection_reengagement.schedule')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_rejection_thank_you')
    def test_schedules_reengagement_for_budget_rejection(
        self, mock_thank, mock_notify, mock_schedule, api_client, sent_proposal,
    ):
        response = api_client.post(
            self._url(sent_proposal.uuid),
            {'action': 'rejected', 'reason': 'presupuesto alto'},
            format='json',
        )
        assert response.status_code == 200
        sent_proposal.refresh_from_db()
        assert sent_proposal.status == 'rejected'
        mock_schedule.assert_called_once()

    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_rejection_thank_you')
    def test_does_not_schedule_reengagement_for_non_budget_rejection(
        self, mock_thank, mock_notify, api_client, sent_proposal,
    ):
        with patch('content.tasks.send_rejection_reengagement.schedule') as mock_schedule:
            response = api_client.post(
                self._url(sent_proposal.uuid),
                {'action': 'rejected', 'reason': 'another option'},
                format='json',
            )
            assert response.status_code == 200
            mock_schedule.assert_not_called()

    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_acceptance_confirmation')
    def test_acceptance_sends_confirmation_email(
        self, mock_confirm, mock_notify, api_client, sent_proposal,
    ):
        response = api_client.post(
            self._url(sent_proposal.uuid),
            {'action': 'accepted'},
            format='json',
        )
        assert response.status_code == 200
        mock_confirm.assert_called_once()

    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    def test_sets_responded_at_on_response(self, mock_notify, api_client, sent_proposal):
        api_client.post(
            self._url(sent_proposal.uuid),
            {'action': 'accepted'},
            format='json',
        )
        sent_proposal.refresh_from_db()
        assert sent_proposal.responded_at is not None
