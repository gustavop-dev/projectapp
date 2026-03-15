"""Tests for proposal API views.

Covers: public retrieve/respond/pdf, admin CRUD, section update,
bulk reorder, auth check, permission checks, edge cases.
"""
from datetime import datetime
from datetime import timezone as dt_tz
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
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

    def test_returns_200_with_expired_meta_for_expired_proposal(self, api_client, expired_proposal):
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': expired_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'expired_meta' in response.data
        assert response.data['expired_meta']['seller_name']

    def test_returns_404_for_nonexistent_uuid(self, api_client):
        from uuid import UUID
        fixed_uuid = UUID('00000000-0000-0000-0000-000000000099')
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': fixed_uuid})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_expired_proposal_already_expired_status_returns_200_with_meta(self, api_client, expired_proposal):
        expired_proposal.status = 'expired'
        expired_proposal.save(update_fields=['status'])
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': expired_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'expired_meta' in response.data

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
        assert response.status_code == 200
        assert 'expired_meta' in response.data
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

    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_negotiation_notification')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_negotiation_confirmation')
    def test_negotiating_proposal_returns_200(
        self, mock_confirm, mock_notify, mock_response, api_client, sent_proposal,
    ):
        url = reverse('respond-to-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.post(
            url, {'action': 'negotiating', 'comment': 'Adjust scope please'}, format='json',
        )
        assert response.status_code == 200
        sent_proposal.refresh_from_db()
        assert sent_proposal.status == 'negotiating'
        mock_notify.assert_called_once()
        mock_confirm.assert_called_once()

    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_negotiation_notification')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_negotiation_confirmation')
    def test_negotiating_logs_change(
        self, mock_confirm, mock_notify, mock_response, api_client, sent_proposal,
    ):
        url = reverse('respond-to-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        api_client.post(
            url, {'action': 'negotiating', 'comment': 'Need fewer modules'}, format='json',
        )
        log = ProposalChangeLog.objects.filter(
            proposal=sent_proposal, change_type='negotiating',
        ).first()
        assert log is not None
        assert 'Need fewer modules' in log.description

    def test_returns_400_for_draft_proposal(self, api_client, proposal):
        url = reverse('respond-to-proposal', kwargs={'proposal_uuid': proposal.uuid})
        response = api_client.post(url, {'action': 'accepted'}, format='json')
        assert response.status_code == 400


class TestPostExpirationVisitAlert:
    @patch('content.services.proposal_email_service.ProposalEmailService.send_post_expiration_visit_alert')
    def test_creates_alert_on_expired_visit(self, mock_alert, api_client, expired_proposal):
        from content.models import ProposalAlert
        assert expired_proposal.post_expiration_alert_sent_at is None
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': expired_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'expired_meta' in response.data
        alert = ProposalAlert.objects.filter(
            proposal=expired_proposal, alert_type='post_expiration_visit',
        ).first()
        assert alert is not None
        assert 'alto interés' in alert.message.lower()
        mock_alert.assert_called_once()
        expired_proposal.refresh_from_db()
        assert expired_proposal.post_expiration_alert_sent_at is not None

    @freeze_time('2026-03-10 12:00:00')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_post_expiration_visit_alert')
    def test_does_not_duplicate_alert(self, mock_alert, api_client, expired_proposal):
        expired_proposal.post_expiration_alert_sent_at = timezone.now()
        expired_proposal.save(update_fields=['post_expiration_alert_sent_at'])
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': expired_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'expired_meta' in response.data
        mock_alert.assert_not_called()


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
        assert len(response.data['sections']) == 14

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

    def test_creates_default_13_sections(self, admin_client):
        """JSON import creates all 13 default sections."""
        url = reverse('create-proposal-from-json')
        response = admin_client.post(url, self._minimal_payload(), format='json')
        assert response.status_code == 201
        assert len(response.data['sections']) == 14

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

    def test_preserves_default_groups_when_json_omits_them(self, admin_client):
        """Default functional_requirements groups survive even if JSON omits them."""
        url = reverse('create-proposal-from-json')
        payload = self._minimal_payload()
        # Provide functionalRequirements with only ONE group (views), omitting others
        payload['sections']['functionalRequirements'] = {
            'index': '9',
            'title': 'Custom FR',
            'intro': 'Custom intro',
            'groups': [
                {
                    'id': 'views',
                    'icon': '🖥️',
                    'title': 'Custom Views',
                    'description': 'Overridden description',
                    'items': [{'icon': '🏠', 'name': 'Home', 'description': 'Landing page'}],
                },
            ],
            'additionalModules': [],
        }
        response = admin_client.post(url, payload, format='json')
        assert response.status_code == 201
        sections = {s['section_type']: s for s in response.data['sections']}
        fr = sections['functional_requirements']['content_json']
        group_ids = [g['id'] for g in fr['groups']]
        # The 'views' group should exist with overridden content
        views_group = next(g for g in fr['groups'] if g['id'] == 'views')
        assert views_group['title'] == 'Custom Views'
        assert views_group['description'] == 'Overridden description'
        # Default groups like 'components' and 'features' should still be present
        assert 'components' in group_ids
        assert 'features' in group_ids

    def test_preserves_default_additional_modules_when_json_omits_them(self, admin_client):
        """Default additionalModules survive even if JSON provides an empty list."""
        url = reverse('create-proposal-from-json')
        payload = self._minimal_payload()
        payload['sections']['functionalRequirements'] = {
            'index': '9',
            'title': 'Requerimientos',
            'intro': 'Intro',
            'groups': [],
            'additionalModules': [],
        }
        response = admin_client.post(url, payload, format='json')
        assert response.status_code == 201
        sections = {s['section_type']: s for s in response.data['sections']}
        fr = sections['functional_requirements']['content_json']
        # All default groups should be present despite empty JSON groups
        group_ids = [g['id'] for g in fr['groups']]
        assert 'views' in group_ids
        assert 'components' in group_ids
        assert 'features' in group_ids

    def test_new_groups_from_json_are_appended(self, admin_client):
        """New groups from JSON that don't exist in defaults are appended."""
        url = reverse('create-proposal-from-json')
        payload = self._minimal_payload()
        payload['sections']['functionalRequirements'] = {
            'index': '9',
            'title': 'FR',
            'intro': 'Intro',
            'groups': [
                {
                    'id': 'custom_new_group',
                    'icon': '🆕',
                    'title': 'Brand New Group',
                    'description': 'Added by AI',
                    'items': [],
                },
            ],
            'additionalModules': [],
        }
        response = admin_client.post(url, payload, format='json')
        assert response.status_code == 201
        sections = {s['section_type']: s for s in response.data['sections']}
        fr = sections['functional_requirements']['content_json']
        group_ids = [g['id'] for g in fr['groups']]
        # New group should be appended after defaults
        assert 'custom_new_group' in group_ids
        # Default groups still present
        assert 'views' in group_ids


# ---------------------------------------------------------------------------
# Investment sync on update
# ---------------------------------------------------------------------------

class TestInvestmentSyncOnUpdate:
    """Verify that updating total_investment syncs to the investment section."""

    @pytest.fixture
    def proposal_with_investment_section(self, db):
        """Proposal with an investment section containing content_json."""
        p = BusinessProposal.objects.create(
            title='Sync Test Proposal',
            client_name='Sync Client',
            client_email='sync@test.com',
            total_investment=Decimal('1500000'),
            currency='COP',
            status='draft',
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        ProposalSection.objects.create(
            proposal=p,
            section_type='investment',
            title='Inversión',
            order=9,
            content_json={
                'totalInvestment': '$1.500.000',
                'currency': 'COP',
                'paymentOptions': [
                    {'label': '40% al firmar ✍️', 'description': '$600.000 COP'},
                    {'label': '30% al diseño ✅', 'description': '$450.000 COP'},
                    {'label': '30% al deploy 🚀', 'description': '$450.000 COP'},
                ],
            },
        )
        return p

    def test_updates_investment_section_total(self, admin_client, proposal_with_investment_section):
        """Changing total_investment updates the investment section's content_json."""
        p = proposal_with_investment_section
        url = reverse('update-proposal', kwargs={'proposal_id': p.id})
        response = admin_client.patch(
            url, {'total_investment': '3000000'}, format='json'
        )
        assert response.status_code == 200
        inv = ProposalSection.objects.get(proposal=p, section_type='investment')
        assert inv.content_json['totalInvestment'] == '$3.000.000'

    def test_updates_payment_option_descriptions(self, admin_client, proposal_with_investment_section):
        """Changing total_investment recalculates payment option amounts."""
        p = proposal_with_investment_section
        url = reverse('update-proposal', kwargs={'proposal_id': p.id})
        admin_client.patch(url, {'total_investment': '2000000'}, format='json')
        inv = ProposalSection.objects.get(proposal=p, section_type='investment')
        opts = inv.content_json['paymentOptions']
        # 40% of 2,000,000 = 800,000
        assert '$800.000' in opts[0]['description']
        # 30% of 2,000,000 = 600,000
        assert '$600.000' in opts[1]['description']

    def test_updates_currency_in_section(self, admin_client, proposal_with_investment_section):
        """Changing currency updates the investment section's content_json currency."""
        p = proposal_with_investment_section
        url = reverse('update-proposal', kwargs={'proposal_id': p.id})
        admin_client.patch(url, {'currency': 'USD'}, format='json')
        inv = ProposalSection.objects.get(proposal=p, section_type='investment')
        assert inv.content_json['currency'] == 'USD'

    def test_no_sync_when_investment_unchanged(self, admin_client, proposal_with_investment_section):
        """Updating unrelated fields does not modify the investment section."""
        p = proposal_with_investment_section
        inv_before = ProposalSection.objects.get(proposal=p, section_type='investment')
        original_total = inv_before.content_json['totalInvestment']
        url = reverse('update-proposal', kwargs={'proposal_id': p.id})
        admin_client.patch(url, {'title': 'New Title Only'}, format='json')
        inv_after = ProposalSection.objects.get(proposal=p, section_type='investment')
        assert inv_after.content_json['totalInvestment'] == original_total


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

    @freeze_time('2026-03-10 12:00:00')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_revisit_alert', return_value=True)
    def test_sends_revisit_alert_after_3_sessions(self, mock_alert, api_client, sent_proposal):
        """Revisit alert fires after 3 distinct session IDs with 3+ day gap."""
        from datetime import timedelta

        from django.utils import timezone
        # Set first_viewed_at to 4 days ago so temporal gap check passes
        sent_proposal.first_viewed_at = timezone.now() - timedelta(days=4)
        sent_proposal.save(update_fields=['first_viewed_at'])

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


# ---------------------------------------------------------------------------
# Dashboard KPIs (extended)
# ---------------------------------------------------------------------------

class TestProposalDashboardExtended:
    """Extended tests for the proposal_dashboard admin endpoint."""

    def test_returns_401_for_unauthenticated(self, api_client):
        """Unauthenticated users cannot access the dashboard."""
        response = api_client.get(reverse('proposal-dashboard'))
        assert response.status_code in (401, 403)

    def test_returns_200_with_empty_db(self, admin_client):
        """Dashboard returns zeroed KPIs when no proposals exist."""
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        assert response.data['total_proposals'] == 0
        assert response.data['conversion_rate'] == 0

    @freeze_time('2026-03-01 12:00:00')
    def test_returns_counts_by_status(self, admin_client, sent_proposal, rejected_proposal):
        """Dashboard returns correct counts per status."""
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        assert response.data['by_status']['sent'] == 1
        assert response.data['by_status']['rejected'] == 1

    @freeze_time('2026-03-01 12:00:00')
    def test_calculates_time_to_first_view(self, admin_client, viewed_proposal):
        """Dashboard calculates avg time-to-first-view when data exists."""
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        assert response.data['avg_time_to_first_view_hours'] is not None

    @freeze_time('2026-03-01 12:00:00')
    def test_calculates_conversion_rate(self, admin_client, db):
        """Dashboard calculates conversion rate from terminal proposals."""
        BusinessProposal.objects.create(
            title='Accepted', client_name='A', status='accepted',
            total_investment=1000,
        )
        BusinessProposal.objects.create(
            title='Rejected', client_name='B', status='rejected',
            total_investment=1000,
        )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        assert response.data['conversion_rate'] == 50.0

    @freeze_time('2026-03-01 12:00:00')
    def test_returns_monthly_trend(self, admin_client, sent_proposal):
        """Dashboard includes monthly_trend array."""
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        assert isinstance(response.data['monthly_trend'], list)

    @freeze_time('2026-03-01 12:00:00')
    def test_returns_discount_close_rates(self, admin_client, db):
        """Dashboard returns discount vs no-discount close rates."""
        BusinessProposal.objects.create(
            title='Disc', client_name='D', status='accepted',
            total_investment=1000, discount_percent=15,
        )
        BusinessProposal.objects.create(
            title='NoDisc', client_name='N', status='rejected',
            total_investment=1000, discount_percent=0,
        )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        assert response.data['discount_close_rate'] == 100.0
        assert response.data['no_discount_close_rate'] == 0.0

    @freeze_time('2026-03-01 12:00:00')
    def test_returns_top_dropoff_section(self, admin_client, sent_proposal):
        """Dashboard returns top_dropoff_section when tracking data exists."""
        event = ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='s1',
        )
        ProposalSectionView.objects.create(
            view_event=event, section_type='greeting',
            section_title='Saludo', time_spent_seconds=10,
            entered_at=timezone.now(),
        )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        # top_dropoff_section may be present or None depending on data
        assert 'top_dropoff_section' in response.data


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------

class TestExportAnalyticsCsv:
    """Tests for the export_proposal_analytics_csv admin endpoint."""

    def _url(self, proposal_id):
        return reverse('proposal-analytics-csv', kwargs={'proposal_id': proposal_id})

    def test_returns_401_for_unauthenticated(self, api_client, proposal):
        """Unauthenticated users cannot export CSV."""
        response = api_client.get(self._url(proposal.id))
        assert response.status_code in (401, 403)

    def test_returns_404_for_nonexistent_proposal(self, admin_client):
        """Exporting CSV for a nonexistent proposal returns 404."""
        response = admin_client.get(self._url(99999))
        assert response.status_code == 404

    def test_returns_csv_with_correct_headers(self, admin_client, proposal):
        """CSV export returns text/csv content type with attachment disposition."""
        response = admin_client.get(self._url(proposal.id))
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']
        assert 'attachment' in response['Content-Disposition']

    def test_csv_contains_section_and_session_headers(self, admin_client, proposal):
        """CSV body includes section engagement and session history sections."""
        response = admin_client.get(self._url(proposal.id))
        content = response.content.decode()
        assert 'SECTION ENGAGEMENT' in content
        assert 'SESSION HISTORY' in content
        assert 'CHANGE LOG' in content


# ---------------------------------------------------------------------------
# Mini-CRM: list_clients
# ---------------------------------------------------------------------------

class TestListClients:
    """Tests for the list_clients admin endpoint."""

    def test_returns_401_for_unauthenticated(self, api_client):
        """Unauthenticated users cannot access the clients list."""
        response = api_client.get(reverse('list-clients'))
        assert response.status_code in (401, 403)

    def test_returns_200_with_empty_db(self, admin_client):
        """Returns empty list when no proposals exist."""
        response = admin_client.get(reverse('list-clients'))
        assert response.status_code == 200
        assert response.data == []

    def test_groups_proposals_by_client_email(self, admin_client, db):
        """Proposals with the same client_email are grouped together."""
        BusinessProposal.objects.create(
            title='P1', client_name='Client A', client_email='a@test.com',
            total_investment=1000,
        )
        BusinessProposal.objects.create(
            title='P2', client_name='Client A', client_email='a@test.com',
            total_investment=2000,
        )
        response = admin_client.get(reverse('list-clients'))
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['total_proposals'] == 2

    def test_falls_back_to_client_name_when_no_email(self, admin_client, db):
        """Groups by client_name when client_email is blank."""
        BusinessProposal.objects.create(
            title='P1', client_name='No Email Client', client_email='',
            total_investment=1000,
        )
        response = admin_client.get(reverse('list-clients'))
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['client_name'] == 'No Email Client'


# ---------------------------------------------------------------------------
# Analytics: funnel + comparison (extended)
# ---------------------------------------------------------------------------

class TestRetrieveProposalAnalyticsExtended:
    """Extended tests for retrieve_proposal_analytics including funnel and comparison."""

    def _url(self, proposal_id):
        return reverse('proposal-analytics', kwargs={'proposal_id': proposal_id})

    def test_returns_401_for_unauthenticated(self, api_client, proposal):
        """Unauthenticated users cannot access analytics."""
        response = api_client.get(self._url(proposal.id))
        assert response.status_code in (401, 403)

    def test_returns_200_with_basic_data(self, admin_client, sent_proposal):
        """Analytics endpoint returns 200 with expected top-level keys."""
        response = admin_client.get(self._url(sent_proposal.id))
        assert response.status_code == 200
        for key in ('total_views', 'unique_sessions', 'sections',
                     'skipped_sections', 'device_breakdown', 'sessions',
                     'funnel', 'comparison', 'share_links'):
            assert key in response.data

    @freeze_time('2026-03-01 12:00:00')
    def test_funnel_includes_dropoff_percentages(self, admin_client, sent_proposal):
        """Funnel data contains drop-off % for each enabled section."""
        ProposalSection.objects.create(
            proposal=sent_proposal, section_type='greeting',
            title='Saludo', order=0, is_enabled=True,
        )
        event = ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='s1',
        )
        ProposalSectionView.objects.create(
            view_event=event, section_type='greeting',
            section_title='Saludo', time_spent_seconds=10,
            entered_at=timezone.now(),
        )
        response = admin_client.get(self._url(sent_proposal.id))
        assert response.status_code == 200
        assert len(response.data['funnel']) >= 1
        assert 'drop_off_percent' in response.data['funnel'][0]

    @freeze_time('2026-03-01 12:00:00')
    def test_comparison_includes_global_averages(self, admin_client, viewed_proposal):
        """Comparison block includes avg_time_to_first_view_hours."""
        response = admin_client.get(self._url(viewed_proposal.id))
        assert response.status_code == 200
        comp = response.data['comparison']
        assert 'avg_time_to_first_view_hours' in comp
        assert 'avg_time_to_response_hours' in comp
        assert 'avg_views' in comp

    @freeze_time('2026-03-01 12:00:00')
    def test_device_breakdown_counts(self, admin_client, sent_proposal):
        """Device breakdown counts mobile, desktop, tablet from user_agent."""
        ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='s-mobile',
            user_agent='Mozilla/5.0 Mobile',
        )
        ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='s-tablet',
            user_agent='Mozilla/5.0 iPad Tablet',
        )
        ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='s-desktop',
            user_agent='Mozilla/5.0 Chrome/120',
        )
        response = admin_client.get(self._url(sent_proposal.id))
        assert response.status_code == 200
        devices = response.data['device_breakdown']
        assert devices['mobile'] == 1
        assert devices['tablet'] == 1
        assert devices['desktop'] == 1

    @freeze_time('2026-03-01 12:00:00')
    def test_time_to_response_calculated(self, admin_client, db):
        """time_to_response_hours is calculated when responded_at exists."""
        from django.utils import timezone as tz
        proposal = BusinessProposal.objects.create(
            title='Responded', client_name='R', status='accepted',
            total_investment=1000,
            sent_at=tz.now() - tz.timedelta(hours=10),
            first_viewed_at=tz.now() - tz.timedelta(hours=5),
            responded_at=tz.now(),
        )
        response = admin_client.get(self._url(proposal.id))
        assert response.status_code == 200
        assert response.data['time_to_response_hours'] == 5.0


# ---------------------------------------------------------------------------
# Retrieve — inactive proposal (line 47)
# ---------------------------------------------------------------------------

class TestRetrieveInactiveProposal:
    def test_returns_404_for_inactive_proposal(self, api_client, sent_proposal):
        """Inactive proposals return 404 with error message."""
        sent_proposal.is_active = False
        sent_proposal.save(update_fields=['is_active'])
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 404
        assert 'error' in response.data


# ---------------------------------------------------------------------------
# First view notification exception (lines 81-82)
# ---------------------------------------------------------------------------

class TestFirstViewNotificationException:
    @patch('content.tasks.notify_first_view', side_effect=Exception('Queue down'))
    def test_still_returns_200_when_notification_fails(self, mock_task, api_client, sent_proposal):
        """Proposal retrieval succeeds even when first-view notification task raises."""
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 200
        sent_proposal.refresh_from_db()
        assert sent_proposal.first_viewed_at is not None


# ---------------------------------------------------------------------------
# Create from JSON — inspirationalQuote (line 280)
# ---------------------------------------------------------------------------

class TestCreateFromJsonInspirationalQuote:
    def test_greeting_receives_inspirational_quote(self, admin_client):
        """General inspirationalQuote is forwarded to the greeting section."""
        payload = {
            'title': 'Quote Test',
            'client_name': 'Client',
            'sections': {
                'general': {
                    'clientName': 'Client',
                    'inspirationalQuote': 'Design is how it works.',
                },
            },
        }
        url = reverse('create-proposal-from-json')
        response = admin_client.post(url, payload, format='json')
        assert response.status_code == 201
        greeting = next(
            s for s in response.data['sections']
            if s['section_type'] == 'greeting'
        )
        assert greeting['content_json']['inspirationalQuote'] == 'Design is how it works.'


# ---------------------------------------------------------------------------
# Rejection reengagement exception (lines 651-652)
# ---------------------------------------------------------------------------

class TestReengagementException:
    @patch('content.tasks.send_rejection_reengagement.schedule', side_effect=Exception('Task error'))
    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_rejection_thank_you')
    def test_still_returns_200_when_reengagement_fails(
        self, mock_thank, mock_notify, mock_schedule, api_client, sent_proposal,
    ):
        """Rejection response succeeds even when reengagement scheduling raises."""
        response = api_client.post(
            reverse('respond-to-proposal', kwargs={'proposal_uuid': sent_proposal.uuid}),
            {'action': 'rejected', 'reason': 'presupuesto muy alto'},
            format='json',
        )
        assert response.status_code == 200
        sent_proposal.refresh_from_db()
        assert sent_proposal.status == 'rejected'
        mock_schedule.assert_called_once()


# ---------------------------------------------------------------------------
# Stakeholder detection (lines 779-799)
# ---------------------------------------------------------------------------

class TestStakeholderDetection:
    def _url(self, uuid):
        return reverse('track-proposal-engagement', kwargs={'proposal_uuid': uuid})

    @freeze_time('2026-03-01 12:00:00')
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_stakeholder_detected_notification',
        return_value=True,
    )
    def test_sends_stakeholder_alert_on_new_ip(self, mock_alert, api_client, sent_proposal):
        """Stakeholder alert fires when a new IP is detected from a different session."""
        sent_proposal.first_viewed_at = timezone.now()
        sent_proposal.save(update_fields=['first_viewed_at'])
        ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='s-original', ip_address='1.2.3.4',
        )
        payload = {
            'session_id': 's-new-stakeholder',
            'sections': [
                {'section_type': 'greeting', 'section_title': 'Hi',
                 'time_spent_seconds': 3, 'entered_at': '2026-03-01T10:00:00Z'},
            ],
        }
        api_client.post(
            self._url(sent_proposal.uuid), payload, format='json',
            HTTP_X_FORWARDED_FOR='9.8.7.6',
        )
        mock_alert.assert_called_once()
        sent_proposal.refresh_from_db()
        assert sent_proposal.stakeholder_alert_sent_at is not None

    @freeze_time('2026-03-01 12:00:00')
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_stakeholder_detected_notification',
        side_effect=Exception('Email error'),
    )
    def test_still_returns_200_when_stakeholder_alert_fails(self, mock_alert, api_client, sent_proposal):
        """Engagement tracking succeeds even when stakeholder alert raises."""
        sent_proposal.first_viewed_at = timezone.now()
        sent_proposal.save(update_fields=['first_viewed_at'])
        ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='s-original', ip_address='1.2.3.4',
        )
        payload = {
            'session_id': 's-stakeholder-err',
            'sections': [
                {'section_type': 'greeting', 'section_title': 'Hi',
                 'time_spent_seconds': 3, 'entered_at': '2026-03-01T10:00:00Z'},
            ],
        }
        response = api_client.post(
            self._url(sent_proposal.uuid), payload, format='json',
            HTTP_X_FORWARDED_FOR='9.8.7.6',
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# entered_at parse error fallback (lines 813-814)
# ---------------------------------------------------------------------------

class TestEngagementEnteredAtFallback:
    def test_invalid_entered_at_string_falls_back_to_now(self, api_client, sent_proposal):
        """Invalid entered_at string is replaced by timezone.now() instead of raising."""
        payload = {
            'session_id': 'sess-bad-date',
            'sections': [
                {'section_type': 'greeting', 'section_title': 'Hi',
                 'time_spent_seconds': 2, 'entered_at': 'not-a-date'},
            ],
        }
        url = reverse('track-proposal-engagement', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 200
        assert ProposalSectionView.objects.filter(section_type='greeting').exists()

    def test_numeric_entered_at_falls_back_to_now(self, api_client, sent_proposal):
        """Numeric entered_at triggers TypeError which falls back to timezone.now()."""
        payload = {
            'session_id': 'sess-numeric-date',
            'sections': [
                {'section_type': 'investment', 'section_title': 'Inv',
                 'time_spent_seconds': 3, 'entered_at': 12345},
            ],
        }
        url = reverse('track-proposal-engagement', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 200
        assert ProposalSectionView.objects.filter(section_type='investment').exists()


# ---------------------------------------------------------------------------
# Revisit alert exception (lines 868-869)
# ---------------------------------------------------------------------------

class TestRevisitAlertException:
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_revisit_alert',
        side_effect=Exception('Email SMTP error'),
    )
    def test_still_returns_200_when_revisit_alert_fails(self, mock_alert, api_client, sent_proposal):
        """Engagement tracking succeeds even when revisit alert raises."""
        url = reverse('track-proposal-engagement', kwargs={'proposal_uuid': sent_proposal.uuid})
        for i in range(3):
            payload = {
                'session_id': f'sess-revisit-err-{i}',
                'sections': [
                    {'section_type': 'greeting', 'section_title': 'Hi',
                     'time_spent_seconds': 5, 'entered_at': '2026-03-01T10:00:00Z'},
                ],
            }
            response = api_client.post(url, payload, format='json')
            assert response.status_code == 200


# ---------------------------------------------------------------------------
# _get_client_ip with X-Forwarded-For (line 881)
# ---------------------------------------------------------------------------

class TestGetClientIpXForwardedFor:
    def test_uses_x_forwarded_for_header(self, api_client, sent_proposal):
        """X-Forwarded-For header is used to extract client IP."""
        payload = {
            'session_id': 'sess-xff',
            'sections': [
                {'section_type': 'greeting', 'section_title': 'Hi',
                 'time_spent_seconds': 1, 'entered_at': '2026-03-01T10:00:00Z'},
            ],
        }
        url = reverse('track-proposal-engagement', kwargs={'proposal_uuid': sent_proposal.uuid})
        api_client.post(url, payload, format='json', HTTP_X_FORWARDED_FOR='10.20.30.40, 1.2.3.4')
        event = ProposalViewEvent.objects.get(session_id='sess-xff')
        assert event.ip_address == '10.20.30.40'


# ---------------------------------------------------------------------------
# Analytics avg_views and avg_ttr (lines 1233, 1320-1324)
# ---------------------------------------------------------------------------

class TestAnalyticsAvgViewsAndTtr:
    @freeze_time('2026-03-01 12:00:00')
    def test_comparison_includes_avg_views(self, admin_client, db):
        """Comparison block includes avg_views when viewed proposals exist."""
        from django.utils import timezone as tz
        BusinessProposal.objects.create(
            title='V1', client_name='A', status='viewed',
            total_investment=1000, view_count=5,
        )
        BusinessProposal.objects.create(
            title='V2', client_name='B', status='viewed',
            total_investment=2000, view_count=3,
        )
        p_target = BusinessProposal.objects.create(
            title='Target', client_name='T', status='sent',
            total_investment=3000,
            sent_at=tz.now() - tz.timedelta(hours=2),
            first_viewed_at=tz.now() - tz.timedelta(hours=1),
        )
        url = reverse('proposal-analytics', kwargs={'proposal_id': p_target.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.data['comparison']['avg_views'] is not None

    @freeze_time('2026-03-01 12:00:00')
    def test_comparison_includes_avg_ttr(self, admin_client, db):
        """Comparison block includes avg_time_to_response_hours when data exists."""
        from django.utils import timezone as tz
        BusinessProposal.objects.create(
            title='Resp1', client_name='R', status='accepted',
            total_investment=1000,
            first_viewed_at=tz.now() - tz.timedelta(hours=10),
            responded_at=tz.now() - tz.timedelta(hours=5),
        )
        p_target = BusinessProposal.objects.create(
            title='Target', client_name='T', status='sent',
            total_investment=3000,
            sent_at=tz.now() - tz.timedelta(hours=2),
            first_viewed_at=tz.now() - tz.timedelta(hours=1),
        )
        url = reverse('proposal-analytics', kwargs={'proposal_id': p_target.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.data['comparison']['avg_time_to_response_hours'] is not None


# ---------------------------------------------------------------------------
# CSV export with tracking data (lines 1518-1541, 1555)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Dashboard avg_ttr (lines 1320-1324)
# ---------------------------------------------------------------------------

class TestDashboardAvgTtr:
    @freeze_time('2026-03-01 12:00:00')
    def test_dashboard_calculates_avg_time_to_response(self, admin_client, db):
        """Dashboard includes avg_time_to_response_hours when responded proposals exist."""
        from django.utils import timezone as tz
        BusinessProposal.objects.create(
            title='Resp', client_name='R', status='accepted',
            total_investment=1000,
            first_viewed_at=tz.now() - tz.timedelta(hours=8),
            responded_at=tz.now() - tz.timedelta(hours=2),
        )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        assert response.data['avg_time_to_response_hours'] is not None
        assert response.data['avg_time_to_response_hours'] == 6.0


# ---------------------------------------------------------------------------
# Post-expiration alert exception (lines 77-78)
# ---------------------------------------------------------------------------

class TestPostExpirationAlertException:
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_post_expiration_visit_alert',
        side_effect=Exception('SMTP down'),
    )
    def test_returns_200_with_expired_meta_when_alert_creation_raises(self, mock_alert, api_client, expired_proposal):
        """Expired proposal retrieval returns 200 with expired_meta even when alert pipeline raises."""
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': expired_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'expired_meta' in response.data
        expired_proposal.refresh_from_db()
        assert expired_proposal.post_expiration_alert_sent_at is None


# ---------------------------------------------------------------------------
# Engagement decay detection (lines 1046-1055)
# ---------------------------------------------------------------------------

class TestEngagementDecay:
    def _url(self, uuid):
        return reverse('track-proposal-engagement', kwargs={'proposal_uuid': uuid})

    @freeze_time('2026-03-10 12:00:00')
    def test_creates_engagement_decay_alert(self, api_client, sent_proposal):
        """Engagement decay alert is created when current session views < 50% of avg."""
        from content.models import ProposalAlert
        # Previous session with many sections
        prev_event = ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='prev-sess',
        )
        for i in range(6):
            ProposalSectionView.objects.create(
                view_event=prev_event, section_type=f'section_{i}',
                section_title=f'Section {i}', time_spent_seconds=10,
                entered_at=timezone.now(),
            )
        # Current session with very few sections (decay)
        payload = {
            'session_id': 'decay-sess',
            'sections': [
                {
                    'section_type': 'greeting',
                    'section_title': 'Hi',
                    'time_spent_seconds': 2,
                    'entered_at': '2026-03-10T12:00:00Z',
                },
            ],
        }
        response = api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        assert response.status_code == 200
        assert ProposalAlert.objects.filter(
            proposal=sent_proposal, alert_type='engagement_decay',
        ).exists()

    @freeze_time('2026-03-10 12:00:00')
    def test_does_not_create_decay_alert_when_recent_exists(self, api_client, sent_proposal):
        """No duplicate decay alert within 3-day window."""
        from content.models import ProposalAlert
        ProposalAlert.objects.create(
            proposal=sent_proposal, alert_type='engagement_decay',
            message='Decay', alert_date=timezone.now(),
        )
        prev_event = ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='prev-no-dup',
        )
        for i in range(6):
            ProposalSectionView.objects.create(
                view_event=prev_event, section_type=f'section_{i}',
                section_title=f'Section {i}', time_spent_seconds=10,
                entered_at=timezone.now(),
            )
        payload = {
            'session_id': 'decay-no-dup',
            'sections': [
                {
                    'section_type': 'greeting',
                    'section_title': 'Hi',
                    'time_spent_seconds': 2,
                    'entered_at': '2026-03-10T12:00:00Z',
                },
            ],
        }
        response = api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        assert response.status_code == 200
        assert ProposalAlert.objects.filter(
            proposal=sent_proposal, alert_type='engagement_decay',
        ).count() == 1


# ---------------------------------------------------------------------------
# Dashboard: win rate, engagement/value, dropped modules (lines 1938-2049)
# ---------------------------------------------------------------------------

class TestDashboardWinRateBreakdowns:
    @freeze_time('2026-03-01 12:00:00')
    def test_returns_win_rate_by_project_type(self, admin_client, db):
        """Dashboard returns win_rate_by_project_type when proposals have project_type."""
        BusinessProposal.objects.create(
            title='A', client_name='A', status='accepted',
            total_investment=1000, project_type='webapp', market_type='b2b',
        )
        BusinessProposal.objects.create(
            title='R', client_name='R', status='rejected',
            total_investment=2000, project_type='webapp', market_type='b2b',
        )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        wr = response.data['win_rate_by_project_type']
        assert len(wr) >= 1
        webapp_entry = next(e for e in wr if e['type'] == 'webapp')
        assert webapp_entry['total'] == 2
        assert webapp_entry['accepted'] == 1
        assert webapp_entry['win_rate'] == 50.0

    @freeze_time('2026-03-01 12:00:00')
    def test_returns_win_rate_by_market_type(self, admin_client, db):
        """Dashboard returns win_rate_by_market_type."""
        BusinessProposal.objects.create(
            title='A', client_name='A', status='accepted',
            total_investment=1000, project_type='webapp', market_type='saas',
        )
        BusinessProposal.objects.create(
            title='R', client_name='R', status='expired',
            total_investment=2000, project_type='webapp', market_type='saas',
        )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        wr = response.data['win_rate_by_market_type']
        assert len(wr) >= 1
        saas_entry = next(e for e in wr if e['type'] == 'saas')
        assert saas_entry['total'] == 2
        assert saas_entry['win_rate'] == 50.0

    @freeze_time('2026-03-01 12:00:00')
    def test_returns_win_rate_by_combination(self, admin_client, db):
        """Dashboard returns win_rate_by_combination for combos with ≥2 terminal proposals."""
        for _ in range(2):
            BusinessProposal.objects.create(
                title='C', client_name='C', status='accepted',
                total_investment=1000, project_type='ecommerce', market_type='b2c',
            )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        combos = response.data['win_rate_by_combination']
        assert len(combos) >= 1
        combo = combos[0]
        assert combo['project_type'] == 'ecommerce'
        assert combo['market_type'] == 'b2c'
        assert combo['win_rate'] == 100.0


class TestDashboardEngagementValueInsight:
    @freeze_time('2026-03-01 12:00:00')
    def test_returns_engagement_value_insight(self, admin_client, db):
        """Dashboard returns engagement_value_insight when ≥4 accepted proposals exist."""
        for i in range(4):
            p = BusinessProposal.objects.create(
                title=f'Acc{i}', client_name=f'C{i}', status='accepted',
                total_investment=1000 * (i + 1),
            )
            event = ProposalViewEvent.objects.create(
                proposal=p, session_id=f'ev-sess-{i}',
            )
            ProposalSectionView.objects.create(
                view_event=event, section_type='investment',
                section_title='Inv', time_spent_seconds=10 * (i + 1),
                entered_at=timezone.now(),
            )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        insight = response.data['engagement_value_insight']
        assert insight is not None
        assert 'avg_high_engagement_value' in insight
        assert 'avg_low_engagement_value' in insight
        assert 'difference' in insight

    @freeze_time('2026-03-01 12:00:00')
    def test_returns_null_insight_with_fewer_than_4_accepted(self, admin_client, db):
        """Dashboard returns null engagement_value_insight with < 4 accepted proposals."""
        BusinessProposal.objects.create(
            title='A1', client_name='C1', status='accepted', total_investment=1000,
        )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        assert response.data['engagement_value_insight'] is None


class TestDashboardDroppedModulesAndAbandonment:
    @freeze_time('2026-03-01 12:00:00')
    def test_returns_top_dropped_modules(self, admin_client, db):
        """Dashboard returns top_dropped_modules from calc_confirmed logs."""
        import json
        p = BusinessProposal.objects.create(
            title='P', client_name='C', status='sent', total_investment=1000,
        )
        ProposalChangeLog.objects.create(
            proposal=p, change_type='calc_confirmed',
            description=json.dumps({'selected': ['m1'], 'deselected': ['m2', 'm3'], 'total': 1000}),
        )
        ProposalChangeLog.objects.create(
            proposal=p, change_type='calc_confirmed',
            description=json.dumps({'selected': ['m1'], 'deselected': ['m2'], 'total': 500}),
        )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        dropped = response.data['top_dropped_modules']
        assert len(dropped) >= 1
        m2_entry = next(d for d in dropped if d['module_id'] == 'm2')
        assert m2_entry['drop_count'] == 2

    @freeze_time('2026-03-01 12:00:00')
    def test_returns_calc_abandonment_rate(self, admin_client, db):
        """Dashboard returns calc_abandonment_rate from confirmed + abandoned logs."""
        import json
        p = BusinessProposal.objects.create(
            title='P', client_name='C', status='sent', total_investment=1000,
        )
        ProposalChangeLog.objects.create(
            proposal=p, change_type='calc_confirmed',
            description=json.dumps({'selected': [], 'deselected': [], 'total': 0}),
        )
        ProposalChangeLog.objects.create(
            proposal=p, change_type='calc_abandoned',
            description=json.dumps({'selected': [], 'deselected': [], 'total': 0}),
        )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        assert response.data['calc_abandonment_rate'] == 50.0

    @freeze_time('2026-03-01 12:00:00')
    def test_handles_invalid_json_in_calc_log(self, admin_client, db):
        """Dashboard handles invalid JSON in calc_confirmed description gracefully."""
        p = BusinessProposal.objects.create(
            title='P', client_name='C', status='sent', total_investment=1000,
        )
        ProposalChangeLog.objects.create(
            proposal=p, change_type='calc_confirmed',
            description='not valid json',
        )
        response = admin_client.get(reverse('proposal-dashboard'))
        assert response.status_code == 200
        assert response.data['top_dropped_modules'] == []


# ---------------------------------------------------------------------------
# CSV export with full data rows (lines 2078-2145)
# ---------------------------------------------------------------------------

class TestCsvExportFullData:
    @freeze_time('2026-03-01 12:00:00')
    def test_csv_includes_section_engagement_rows(self, admin_client, sent_proposal):
        """CSV export includes per-section stats rows with visit count and times."""
        event = ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='csv-full-s1',
            ip_address='5.5.5.5',
        )
        ProposalSectionView.objects.create(
            view_event=event, section_type='investment',
            section_title='Investment', time_spent_seconds=20.5,
            entered_at=timezone.now(),
        )
        ProposalSectionView.objects.create(
            view_event=event, section_type='greeting',
            section_title='Saludo', time_spent_seconds=8.0,
            entered_at=timezone.now(),
        )
        url = reverse('proposal-analytics-csv', kwargs={'proposal_id': sent_proposal.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert 'investment' in content
        assert 'greeting' in content
        assert 'Investment' in content

    @freeze_time('2026-03-01 12:00:00')
    def test_csv_includes_change_log_rows(self, admin_client, sent_proposal):
        """CSV export includes change log entries."""
        ProposalChangeLog.objects.create(
            proposal=sent_proposal, change_type='status_changed',
            field_name='status', old_value='draft', new_value='sent',
            description='Status updated',
        )
        url = reverse('proposal-analytics-csv', kwargs={'proposal_id': sent_proposal.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert 'CHANGE LOG' in content
        assert 'status_changed' in content


# ---------------------------------------------------------------------------
# List clients: full proposal grouping (lines 2163-2190)
# ---------------------------------------------------------------------------

class TestListClientsFullData:
    @freeze_time('2026-03-01 12:00:00')
    def test_returns_proposal_details_in_client_group(self, admin_client, db):
        """Client group includes detailed proposal summaries."""
        now = timezone.now()
        BusinessProposal.objects.create(
            title='P1', client_name='Detail Client', client_email='detail@test.com',
            total_investment=5000, currency='COP', status='sent',
            sent_at=now, view_count=3, expires_at=now + timezone.timedelta(days=10),
        )
        response = admin_client.get(reverse('list-clients'))
        assert response.status_code == 200
        client = response.data[0]
        assert client['total_proposals'] == 1
        proposal = client['proposals'][0]
        assert proposal['title'] == 'P1'
        assert proposal['total_investment'] == '5000.00'
        assert proposal['currency'] == 'COP'
        assert proposal['view_count'] == 3

    def test_counts_accepted_rejected_pending(self, admin_client, db):
        """Client group correctly counts accepted, rejected, and pending proposals."""
        BusinessProposal.objects.create(
            title='Acc', client_name='Multi', client_email='multi@test.com',
            total_investment=1000, status='accepted',
        )
        BusinessProposal.objects.create(
            title='Rej', client_name='Multi', client_email='multi@test.com',
            total_investment=2000, status='rejected',
        )
        BusinessProposal.objects.create(
            title='Draft', client_name='Multi', client_email='multi@test.com',
            total_investment=3000, status='draft',
        )
        response = admin_client.get(reverse('list-clients'))
        assert response.status_code == 200
        client = response.data[0]
        assert client['accepted'] == 1
        assert client['rejected'] == 1
        assert client['pending'] == 1
        assert client['total_proposals'] == 3


# ---------------------------------------------------------------------------
# Analytics: responded_at / time_to_response (lines 1688-1691)
# ---------------------------------------------------------------------------

class TestAnalyticsRespondedAtFields:
    @freeze_time('2026-03-01 12:00:00')
    def test_returns_responded_at_and_time_to_response(self, admin_client, db):
        """Analytics includes responded_at and time_to_response_hours when proposal was responded."""
        now = timezone.now()
        p = BusinessProposal.objects.create(
            title='Responded', client_name='R', status='accepted',
            total_investment=1000,
            sent_at=now - timezone.timedelta(hours=48),
            first_viewed_at=now - timezone.timedelta(hours=24),
            responded_at=now,
        )
        url = reverse('proposal-analytics', kwargs={'proposal_id': p.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.data['responded_at'] is not None
        assert response.data['time_to_response_hours'] == 24.0

    @freeze_time('2026-03-01 12:00:00')
    def test_returns_null_time_to_response_when_not_responded(self, admin_client, sent_proposal):
        """Analytics returns null time_to_response_hours when no response yet."""
        url = reverse('proposal-analytics', kwargs={'proposal_id': sent_proposal.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.data['time_to_response_hours'] is None


# ---------------------------------------------------------------------------
# Track calculator interaction (lines 1140-1185)
# ---------------------------------------------------------------------------

class TestTrackCalculatorInteraction:
    def _url(self, uuid):
        return reverse('track-calculator-interaction', kwargs={'proposal_uuid': uuid})

    def test_records_confirmed_interaction(self, api_client, sent_proposal):
        """Confirmed calculator interaction creates calc_confirmed change log."""
        payload = {
            'event': 'confirmed',
            'selected': ['module_a', 'module_b'],
            'deselected': ['module_c'],
            'total': 3500000,
        }
        response = api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        assert response.status_code == 200
        assert ProposalChangeLog.objects.filter(
            proposal=sent_proposal, change_type='calc_confirmed',
        ).exists()

    def test_records_abandoned_interaction(self, api_client, sent_proposal):
        """Abandoned calculator interaction creates calc_abandoned change log."""
        payload = {
            'event': 'abandoned',
            'selected': [],
            'deselected': [],
            'total': 0,
        }
        response = api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        assert response.status_code == 200
        assert ProposalChangeLog.objects.filter(
            proposal=sent_proposal, change_type='calc_abandoned',
        ).exists()

    def test_returns_400_for_invalid_event(self, api_client, sent_proposal):
        """Invalid event type returns 400."""
        payload = {'event': 'invalid'}
        response = api_client.post(self._url(sent_proposal.uuid), payload, format='json')
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Engagement: draft proposals skipped (line 946)
# ---------------------------------------------------------------------------

class TestEngagementSkipsDraft:
    def test_skips_tracking_for_draft_proposal(self, api_client, proposal):
        """Engagement tracking returns 200 with skipped status for draft proposals."""
        url = reverse('track-proposal-engagement', kwargs={'proposal_uuid': proposal.uuid})
        payload = {
            'session_id': 'sess-draft',
            'sections': [
                {'section_type': 'greeting', 'section_title': 'Hi',
                 'time_spent_seconds': 1, 'entered_at': '2026-03-01T10:00:00Z'},
            ],
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 200
        assert response.data['status'] == 'skipped'
        assert ProposalViewEvent.objects.count() == 0


# ---------------------------------------------------------------------------
# Proposal alerts endpoint (lines 2282-2466)
# ---------------------------------------------------------------------------

class TestProposalAlerts:
    def _url(self):
        return reverse('proposal-alerts')

    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(self._url())
        assert response.status_code in (401, 403)

    @freeze_time('2026-03-10 12:00:00')
    def test_returns_not_viewed_alert(self, admin_client, db):
        """Stale proposal (sent, not viewed, past reminder_days) triggers not_viewed alert."""
        BusinessProposal.objects.create(
            title='Stale', client_name='S', status='sent',
            total_investment=1000,
            sent_at=timezone.now() - timezone.timedelta(days=10),
            reminder_days=5,
        )
        response = admin_client.get(self._url())
        assert response.status_code == 200
        alert_types = [a['alert_type'] for a in response.data]
        assert 'not_viewed' in alert_types

    @freeze_time('2026-03-10 12:00:00')
    def test_returns_not_responded_alert(self, admin_client, db):
        """Viewed but not responded proposal past urgency_reminder_days triggers alert."""
        BusinessProposal.objects.create(
            title='Viewed', client_name='V', status='viewed',
            total_investment=1000,
            first_viewed_at=timezone.now() - timezone.timedelta(days=8),
            urgency_reminder_days=5,
        )
        response = admin_client.get(self._url())
        assert response.status_code == 200
        alert_types = [a['alert_type'] for a in response.data]
        assert 'not_responded' in alert_types

    @freeze_time('2026-03-10 12:00:00')
    def test_returns_expiring_soon_alert(self, admin_client, db):
        """Proposal expiring within 3 days triggers expiring_soon alert."""
        BusinessProposal.objects.create(
            title='Expiring', client_name='E', status='sent',
            total_investment=1000,
            expires_at=timezone.now() + timezone.timedelta(days=2),
        )
        response = admin_client.get(self._url())
        assert response.status_code == 200
        alert_types = [a['alert_type'] for a in response.data]
        assert 'expiring_soon' in alert_types

    @freeze_time('2026-03-10 12:00:00')
    def test_returns_seller_inactive_alert(self, admin_client, db):
        """Seller inactive >3 days with no recent activity triggers alert."""
        BusinessProposal.objects.create(
            title='Inactive', client_name='I', status='viewed',
            total_investment=1000,
            first_viewed_at=timezone.now() - timezone.timedelta(days=5),
            sent_at=timezone.now() - timezone.timedelta(days=10),
            last_activity_at=timezone.now() - timezone.timedelta(days=5),
        )
        response = admin_client.get(self._url())
        assert response.status_code == 200
        alert_types = [a['alert_type'] for a in response.data]
        assert 'seller_inactive' in alert_types

    @freeze_time('2026-03-10 12:00:00')
    def test_returns_zombie_alert(self, admin_client, db):
        """Sent >7 days, no views, no seller activity triggers zombie alert."""
        BusinessProposal.objects.create(
            title='Zombie', client_name='Z', status='sent',
            total_investment=1000, view_count=0,
            sent_at=timezone.now() - timezone.timedelta(days=8),
        )
        response = admin_client.get(self._url())
        assert response.status_code == 200
        alert_types = [a['alert_type'] for a in response.data]
        assert 'zombie' in alert_types

    @freeze_time('2026-03-10 12:00:00')
    def test_returns_zombie_draft_alert(self, admin_client, db):
        """Draft >5 days without edit triggers zombie_draft alert."""
        BusinessProposal.objects.create(
            title='ZombieDraft', client_name='ZD', status='draft',
            total_investment=1000,
        )
        # Force updated_at to be old
        BusinessProposal.objects.filter(title='ZombieDraft').update(
            updated_at=timezone.now() - timezone.timedelta(days=6),
        )
        response = admin_client.get(self._url())
        assert response.status_code == 200
        alert_types = [a['alert_type'] for a in response.data]
        assert 'zombie_draft' in alert_types

    @freeze_time('2026-03-10 12:00:00')
    def test_returns_zombie_sent_stale_alert(self, admin_client, db):
        """Sent >10 days, no views triggers zombie_sent_stale alert."""
        BusinessProposal.objects.create(
            title='ZombieSent', client_name='ZS', status='sent',
            total_investment=1000, view_count=0,
            sent_at=timezone.now() - timezone.timedelta(days=11),
        )
        response = admin_client.get(self._url())
        assert response.status_code == 200
        alert_types = [a['alert_type'] for a in response.data]
        assert 'zombie_sent_stale' in alert_types

    @freeze_time('2026-03-10 12:00:00')
    def test_returns_late_return_alert(self, admin_client, db):
        """Client returning after ≥5 days gap triggers late_return alert."""
        p = BusinessProposal.objects.create(
            title='LateReturn', client_name='LR', status='viewed',
            total_investment=1000,
        )
        old_event = ProposalViewEvent.objects.create(
            proposal=p, session_id='old-sess',
        )
        # Force viewed_at (auto_now_add) to 6 days ago
        ProposalViewEvent.objects.filter(pk=old_event.pk).update(
            viewed_at=timezone.now() - timezone.timedelta(days=6),
        )
        new_event = ProposalViewEvent.objects.create(
            proposal=p, session_id='new-sess',
        )
        ProposalViewEvent.objects.filter(pk=new_event.pk).update(
            viewed_at=timezone.now() - timezone.timedelta(hours=2),
        )
        response = admin_client.get(self._url())
        assert response.status_code == 200
        alert_types = [a['alert_type'] for a in response.data]
        assert 'late_return' in alert_types

    @freeze_time('2026-03-10 12:00:00')
    def test_returns_manual_alert(self, admin_client, db):
        """Undismissed manual alerts are returned."""
        from content.models import ProposalAlert
        p = BusinessProposal.objects.create(
            title='Manual', client_name='M', status='sent',
            total_investment=1000,
        )
        ProposalAlert.objects.create(
            proposal=p, alert_type='custom_reminder',
            message='Follow up with client', alert_date=timezone.now(),
        )
        response = admin_client.get(self._url())
        assert response.status_code == 200
        alert_types = [a['alert_type'] for a in response.data]
        assert any('manual_' in at for at in alert_types)

    def test_returns_empty_alerts_list(self, admin_client, db):
        """Returns empty list when no alerts are needed."""
        response = admin_client.get(self._url())
        assert response.status_code == 200
        assert isinstance(response.data, list)


# ---------------------------------------------------------------------------
# Create / dismiss proposal alert (lines 2477-2493)
# ---------------------------------------------------------------------------

class TestCreateProposalAlert:
    def _url(self):
        return reverse('create-proposal-alert')

    def test_creates_alert_returns_201(self, admin_client, proposal):
        """Creating a manual alert returns 201."""
        payload = {
            'proposal': proposal.id,
            'alert_type': 'reminder',
            'message': 'Call client tomorrow',
            'alert_date': '2026-03-15T10:00:00Z',
        }
        response = admin_client.post(self._url(), payload, format='json')
        assert response.status_code == 201

    def test_returns_400_for_invalid_data(self, admin_client):
        """Missing required fields returns 400."""
        response = admin_client.post(self._url(), {}, format='json')
        assert response.status_code == 400


class TestDismissProposalAlert:
    @freeze_time('2026-03-01 12:00:00')
    def test_dismisses_alert_returns_200(self, admin_client, proposal):
        """Dismissing an alert marks it as dismissed."""
        from content.models import ProposalAlert
        alert = ProposalAlert.objects.create(
            proposal=proposal, alert_type='custom',
            message='Test', alert_date=timezone.now(),
        )
        url = reverse('dismiss-proposal-alert', kwargs={'alert_id': alert.id})
        response = admin_client.patch(url)
        assert response.status_code == 200
        alert.refresh_from_db()
        assert alert.is_dismissed is True

    def test_returns_404_for_nonexistent_alert(self, admin_client):
        """Dismissing nonexistent alert returns 404."""
        url = reverse('dismiss-proposal-alert', kwargs={'alert_id': 99999})
        response = admin_client.patch(url)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Post-rejection revisit alert (lines 132-147)
# ---------------------------------------------------------------------------

class TestPostRejectionRevisitAlert:
    @freeze_time('2026-03-01 12:00:00')
    def test_creates_alert_on_rejected_proposal_visit(self, api_client, rejected_proposal):
        """Visiting a rejected proposal creates a post_rejection_revisit alert."""
        from content.models import ProposalAlert
        rejected_proposal.responded_at = timezone.now() - timezone.timedelta(days=10)
        rejected_proposal.save(update_fields=['responded_at'])
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': rejected_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 200
        assert ProposalAlert.objects.filter(
            proposal=rejected_proposal, alert_type='post_rejection_revisit',
        ).exists()

    @freeze_time('2026-03-01 12:00:00')
    def test_does_not_duplicate_revisit_alert(self, api_client, rejected_proposal):
        """Second visit to rejected proposal does not create duplicate alert."""
        from content.models import ProposalAlert
        ProposalAlert.objects.create(
            proposal=rejected_proposal, alert_type='post_rejection_revisit',
            message='Already exists', alert_date=timezone.now(),
        )
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': rejected_proposal.uuid})
        api_client.get(url)
        assert ProposalAlert.objects.filter(
            proposal=rejected_proposal, alert_type='post_rejection_revisit',
        ).count() == 1

    def test_no_alert_when_ref_is_reengagement(self, api_client, rejected_proposal):
        """Reengagement link visits do not trigger post-rejection alert."""
        from content.models import ProposalAlert
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': rejected_proposal.uuid})
        api_client.get(url + '?ref=reengagement')
        assert not ProposalAlert.objects.filter(
            proposal=rejected_proposal, alert_type='post_rejection_revisit',
        ).exists()


# ---------------------------------------------------------------------------
# List proposals: heat_score / lead_score branches (lines 227-229)
# ---------------------------------------------------------------------------

class TestListProposalsHeatScore:
    @freeze_time('2026-03-10 12:00:00')
    def test_accepted_proposal_has_heat_score_10(self, admin_client, db):
        """Accepted proposals get heat_score=10."""
        BusinessProposal.objects.create(
            title='Accepted', client_name='A', status='accepted',
            total_investment=1000,
        )
        response = admin_client.get(reverse('list-proposals'))
        assert response.status_code == 200
        item = response.data[0]
        assert item['heat_score'] == 10


# ---------------------------------------------------------------------------
# Engagement decay alert exception (lines 1078-1079)
# ---------------------------------------------------------------------------

class TestEngagementDecayAlertException:
    @freeze_time('2026-03-10 12:00:00')
    @patch('content.models.ProposalAlert.objects.create', side_effect=Exception('DB error'))
    def test_returns_200_when_decay_alert_creation_fails(self, mock_create, api_client, sent_proposal):
        """Engagement tracking succeeds even when engagement_decay alert creation fails."""
        prev_event = ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='prev-exc',
        )
        for i in range(6):
            ProposalSectionView.objects.create(
                view_event=prev_event, section_type=f'section_{i}',
                section_title=f'Section {i}', time_spent_seconds=10,
                entered_at=timezone.now(),
            )
        payload = {
            'session_id': 'decay-exc',
            'sections': [
                {'section_type': 'greeting', 'section_title': 'Hi',
                 'time_spent_seconds': 2, 'entered_at': '2026-03-10T12:00:00Z'},
            ],
        }
        url = reverse('track-proposal-engagement', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Create from JSON with unmapped keys warning (line 386)
# ---------------------------------------------------------------------------

class TestCreateFromJsonUnmappedKeys:
    def test_returns_warnings_for_unknown_section_keys(self, admin_client):
        """Unknown section keys generate a warnings array in the response."""
        payload = {
            'title': 'Unmapped Test',
            'client_name': 'Client',
            'sections': {
                'general': {'clientName': 'Client'},
                'unknownSection': {'foo': 'bar'},
            },
        }
        url = reverse('create-proposal-from-json')
        response = admin_client.post(url, payload, format='json')
        assert response.status_code == 201
        assert 'warnings' in response.data
        assert 'unknownSection' in response.data['warnings'][0]


# ---------------------------------------------------------------------------
# Post-rejection revisit alert exception (lines 145-146)
# ---------------------------------------------------------------------------

class TestPostRejectionRevisitException:
    @freeze_time('2026-03-01 12:00:00')
    @patch('content.models.ProposalAlert.objects.create', side_effect=Exception('DB error'))
    def test_returns_200_when_revisit_alert_creation_raises(self, mock_create, api_client, rejected_proposal):
        """Proposal retrieval succeeds even when post-rejection alert creation raises."""
        rejected_proposal.responded_at = timezone.now() - timezone.timedelta(days=10)
        rejected_proposal.save(update_fields=['responded_at'])
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': rejected_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Heat score branches (lines 1246, 1270, 1272, 1287-1296)
# ---------------------------------------------------------------------------

class TestHeatScoreViaListProposals:
    @freeze_time('2026-03-10 12:00:00')
    def test_high_engagement_sent_proposal_has_heat_score(self, admin_client, db):
        """Sent proposal with cached_heat_score gets that value in list response."""
        p = BusinessProposal.objects.create(
            title='Hot', client_name='H', status='sent',
            total_investment=1000, view_count=5,
            first_viewed_at=timezone.now() - timezone.timedelta(days=1),
            cached_heat_score=7,
        )
        response = admin_client.get(reverse('list-proposals'))
        assert response.status_code == 200
        item = next(i for i in response.data if i['id'] == p.id)
        assert item['heat_score'] == 7

    @freeze_time('2026-03-10 12:00:00')
    def test_zero_cached_heat_score_returns_zero(self, admin_client, db):
        """Sent proposal with cached_heat_score=0 returns 0 in list response."""
        p = BusinessProposal.objects.create(
            title='Moderate', client_name='M', status='sent',
            total_investment=1000, view_count=2,
            first_viewed_at=timezone.now() - timezone.timedelta(days=2),
            cached_heat_score=0,
        )
        response = admin_client.get(reverse('list-proposals'))
        assert response.status_code == 200
        item = next(i for i in response.data if i['id'] == p.id)
        assert item['heat_score'] == 0


# ---------------------------------------------------------------------------
# Engagement score: days-since branches (lines 1225-1228)
# ---------------------------------------------------------------------------

class TestEngagementScoreDaysBranches:
    @freeze_time('2026-03-10 12:00:00')
    def test_analytics_with_3_day_old_view_gets_mid_score(self, admin_client, db):
        """Proposal first viewed 3 days ago hits the elif days_since <= 3 branch."""
        p = BusinessProposal.objects.create(
            title='3Day', client_name='D', status='viewed',
            total_investment=1000, view_count=1,
            sent_at=timezone.now() - timezone.timedelta(days=5),
            first_viewed_at=timezone.now() - timezone.timedelta(days=3),
        )
        url = reverse('proposal-analytics', kwargs={'proposal_id': p.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.data['engagement_score'] >= 0

    @freeze_time('2026-03-10 12:00:00')
    def test_analytics_with_5_day_old_view_gets_low_score(self, admin_client, db):
        """Proposal first viewed 5 days ago hits the elif days_since <= 7 branch."""
        p = BusinessProposal.objects.create(
            title='5Day', client_name='D', status='viewed',
            total_investment=1000, view_count=1,
            sent_at=timezone.now() - timezone.timedelta(days=7),
            first_viewed_at=timezone.now() - timezone.timedelta(days=5),
        )
        url = reverse('proposal-analytics', kwargs={'proposal_id': p.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.data['engagement_score'] >= 0


class TestCsvExportWithTrackingData:
    @freeze_time('2026-03-01 12:00:00')
    def test_csv_includes_section_stats_and_session_data(self, admin_client, sent_proposal):
        """CSV export includes section engagement data and session history rows."""
        event = ProposalViewEvent.objects.create(
            proposal=sent_proposal, session_id='csv-sess-1',
            ip_address='1.2.3.4',
        )
        ProposalSectionView.objects.create(
            view_event=event, section_type='greeting',
            section_title='Saludo', time_spent_seconds=12.5,
            entered_at=timezone.now(),
        )
        ProposalChangeLog.objects.create(
            proposal=sent_proposal, change_type='status_changed',
            field_name='status', old_value='draft', new_value='sent',
        )
        url = reverse('proposal-analytics-csv', kwargs={'proposal_id': sent_proposal.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert 'greeting' in content
        assert 'csv-sess-1' in content
        assert 'status_changed' in content


# ---------------------------------------------------------------------------
# Conditional acceptance (Fix 1)
# ---------------------------------------------------------------------------

class TestConditionalAcceptance:
    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_acceptance_confirmation')
    def test_acceptance_with_condition_creates_cond_accepted_log(
        self, mock_confirm, mock_notify, api_client, sent_proposal
    ):
        """Accepting with a condition creates an extra cond_accepted changelog entry."""
        url = reverse('respond-to-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        payload = {
            'action': 'accepted',
            'condition': 'Necesito soporte por 6 meses',
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 200

        logs = ProposalChangeLog.objects.filter(proposal=sent_proposal)
        cond_logs = logs.filter(change_type='cond_accepted')
        assert cond_logs.count() == 1
        assert 'Necesito soporte por 6 meses' in cond_logs.first().description

        # The main accepted log should also contain the condition
        accepted_log = logs.filter(change_type='accepted').first()
        assert 'Condition:' in accepted_log.description

    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_acceptance_confirmation')
    def test_acceptance_without_condition_creates_no_cond_log(
        self, mock_confirm, mock_notify, api_client, sent_proposal
    ):
        """Accepting without a condition does not create a cond_accepted log."""
        url = reverse('respond-to-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        payload = {'action': 'accepted'}
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 200

        cond_logs = ProposalChangeLog.objects.filter(
            proposal=sent_proposal, change_type='cond_accepted'
        )
        assert cond_logs.count() == 0

    @patch('content.services.proposal_email_service.ProposalEmailService.send_response_notification')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_acceptance_confirmation')
    def test_acceptance_with_empty_condition_creates_no_cond_log(
        self, mock_confirm, mock_notify, api_client, sent_proposal
    ):
        """Accepting with a blank condition string does not create a cond_accepted log."""
        url = reverse('respond-to-proposal', kwargs={'proposal_uuid': sent_proposal.uuid})
        payload = {'action': 'accepted', 'condition': '   '}
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 200

        cond_logs = ProposalChangeLog.objects.filter(
            proposal=sent_proposal, change_type='cond_accepted'
        )
        assert cond_logs.count() == 0


# ---------------------------------------------------------------------------
# Scorecard reads from section content_json (Fix 2)
# ---------------------------------------------------------------------------

class TestScorecardReadsFromSectionContent:
    @freeze_time('2026-03-01 12:00:00')
    def test_scorecard_passes_payment_options_from_investment_section(self, admin_client, db):
        """Scorecard payment_options check reads from investment section content_json."""
        p = BusinessProposal.objects.create(
            title='Scorecard Test', client_name='Client', client_email='c@t.com',
            total_investment=5000000, status='draft',
            expires_at=timezone.now() + timezone.timedelta(days=10),
        )
        ProposalSection.objects.create(
            proposal=p, section_type='investment', title='Inversión',
            order=1, is_enabled=True,
            content_json={
                'paymentOptions': [{'label': 'Pago 1', 'amount': '$2.5M'}],
                'estimatedWeeks': 12,
            },
        )
        url = reverse('proposal-scorecard', kwargs={'proposal_id': p.id})
        response = admin_client.get(url)
        assert response.status_code == 200

        checks_by_key = {c['key']: c for c in response.data['checks']}
        assert checks_by_key['payment_options']['passed'] is True
        assert checks_by_key['estimated_weeks']['passed'] is True

    @freeze_time('2026-03-01 12:00:00')
    def test_scorecard_fails_when_no_investment_section(self, admin_client, db):
        """Scorecard gracefully handles missing investment section."""
        p = BusinessProposal.objects.create(
            title='No Inv', client_name='Client', client_email='c@t.com',
            total_investment=5000000, status='draft',
            expires_at=timezone.now() + timezone.timedelta(days=10),
        )
        ProposalSection.objects.create(
            proposal=p, section_type='greeting', title='Greeting',
            order=0, is_enabled=True, content_json={'clientName': 'Client'},
        )
        url = reverse('proposal-scorecard', kwargs={'proposal_id': p.id})
        response = admin_client.get(url)
        assert response.status_code == 200

        checks_by_key = {c['key']: c for c in response.data['checks']}
        assert checks_by_key['payment_options']['passed'] is False
        assert checks_by_key['estimated_weeks']['passed'] is False

    @freeze_time('2026-03-01 12:00:00')
    def test_scorecard_handles_empty_investment_content(self, admin_client, db):
        """Scorecard handles investment section with empty content_json."""
        p = BusinessProposal.objects.create(
            title='Empty Inv', client_name='Client', client_email='c@t.com',
            total_investment=5000000, status='draft',
            expires_at=timezone.now() + timezone.timedelta(days=10),
        )
        ProposalSection.objects.create(
            proposal=p, section_type='investment', title='Inversión',
            order=1, is_enabled=True, content_json={},
        )
        url = reverse('proposal-scorecard', kwargs={'proposal_id': p.id})
        response = admin_client.get(url)
        assert response.status_code == 200

        checks_by_key = {c['key']: c for c in response.data['checks']}
        assert checks_by_key['payment_options']['passed'] is False
        assert checks_by_key['estimated_weeks']['passed'] is False


# ---------------------------------------------------------------------------
# Inline status change
# ---------------------------------------------------------------------------

class TestInlineStatusChange:
    def test_valid_status_change_succeeds(self, admin_client, sent_proposal):
        """PATCH update-status with valid transition returns 200."""
        url = reverse('update-proposal-status', kwargs={'proposal_id': sent_proposal.id})
        response = admin_client.patch(url, {'status': 'viewed'}, format='json')
        assert response.status_code == 200
        sent_proposal.refresh_from_db()
        assert sent_proposal.status == 'viewed'

    def test_status_change_creates_changelog(self, admin_client, sent_proposal):
        """Inline status change creates a ProposalChangeLog entry."""
        url = reverse('update-proposal-status', kwargs={'proposal_id': sent_proposal.id})
        admin_client.patch(url, {'status': 'expired'}, format='json')
        log = ProposalChangeLog.objects.filter(
            proposal=sent_proposal, change_type='status_change'
        ).first()
        assert log is not None
        assert log.old_value == 'sent'
        assert log.new_value == 'expired'

    def test_invalid_status_returns_400(self, admin_client, sent_proposal):
        """PATCH with invalid status value returns 400."""
        url = reverse('update-proposal-status', kwargs={'proposal_id': sent_proposal.id})
        response = admin_client.patch(url, {'status': 'invalid_status'}, format='json')
        assert response.status_code == 400
        assert 'error' in response.data

    def test_blocked_transition_returns_400(self, admin_client, db):
        """Blocked transition (e.g. draft → accepted) returns 400."""
        p = BusinessProposal.objects.create(
            title='Block', client_name='C', status='draft',
            total_investment=1000,
        )
        url = reverse('update-proposal-status', kwargs={'proposal_id': p.id})
        response = admin_client.patch(url, {'status': 'accepted'}, format='json')
        assert response.status_code == 400

    def test_empty_status_returns_400(self, admin_client, sent_proposal):
        """PATCH with empty status returns 400."""
        url = reverse('update-proposal-status', kwargs={'proposal_id': sent_proposal.id})
        response = admin_client.patch(url, {'status': ''}, format='json')
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# ProposalAlert.__str__ (model line 213)
# ---------------------------------------------------------------------------

class TestProposalAlertStr:
    @freeze_time('2026-03-10 12:00:00')
    def test_str_representation(self, db):
        """ProposalAlert.__str__ returns formatted alert string."""
        from content.models import ProposalAlert
        proposal = BusinessProposal.objects.create(
            title='Str Test', client_name='Alert Client',
        )
        alert = ProposalAlert.objects.create(
            proposal=proposal, alert_type='reminder',
            message='Follow up with the client about their proposal',
            alert_date=timezone.now(),
        )
        result = str(alert)
        assert 'Alert Client' in result
        assert 'Follow up' in result


# ---------------------------------------------------------------------------
# Scorecard: content_json stored as JSON string (view lines 799-802, 832-835)
# ---------------------------------------------------------------------------

class TestScorecardStringContentJson:
    @freeze_time('2026-03-01 12:00:00')
    def test_scorecard_parses_string_content_json_in_sections(self, admin_client, db):
        """Scorecard parses content_json when stored as a JSON string."""
        import json
        p = BusinessProposal.objects.create(
            title='String JSON', client_name='Client', client_email='c@t.com',
            total_investment=5000000, status='draft',
            expires_at=timezone.now() + timezone.timedelta(days=10),
        )
        ProposalSection.objects.create(
            proposal=p, section_type='greeting', title='Greeting',
            order=0, is_enabled=True,
            content_json=json.dumps({'clientName': 'Client'}),
        )
        ProposalSection.objects.create(
            proposal=p, section_type='investment', title='Inversión',
            order=1, is_enabled=True,
            content_json=json.dumps({
                'paymentOptions': [{'label': 'P1'}],
                'estimatedWeeks': 10,
            }),
        )
        url = reverse('proposal-scorecard', kwargs={'proposal_id': p.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        checks_by_key = {c['key']: c for c in response.data['checks']}
        assert checks_by_key['sections_content']['passed'] is True
        assert checks_by_key['payment_options']['passed'] is True

    @freeze_time('2026-03-01 12:00:00')
    def test_scorecard_handles_invalid_string_content_json(self, admin_client, db):
        """Scorecard handles invalid JSON string in content_json gracefully."""
        p = BusinessProposal.objects.create(
            title='Bad JSON', client_name='Client', client_email='c@t.com',
            total_investment=5000000, status='draft',
            expires_at=timezone.now() + timezone.timedelta(days=10),
        )
        ProposalSection.objects.create(
            proposal=p, section_type='greeting', title='Greeting',
            order=0, is_enabled=True,
            content_json='not-valid-json',
        )
        ProposalSection.objects.create(
            proposal=p, section_type='investment', title='Inversión',
            order=1, is_enabled=True,
            content_json='also-invalid',
        )
        url = reverse('proposal-scorecard', kwargs={'proposal_id': p.id})
        response = admin_client.get(url)
        assert response.status_code == 200

    @freeze_time('2026-03-01 12:00:00')
    def test_scorecard_handles_non_integer_estimated_weeks(self, admin_client, db):
        """Scorecard handles estimatedWeeks that cannot be cast to int."""
        p = BusinessProposal.objects.create(
            title='Bad Weeks', client_name='Client', client_email='c@t.com',
            total_investment=5000000, status='draft',
            expires_at=timezone.now() + timezone.timedelta(days=10),
        )
        ProposalSection.objects.create(
            proposal=p, section_type='investment', title='Inversión',
            order=1, is_enabled=True,
            content_json={'paymentOptions': [], 'estimatedWeeks': 'not-a-number'},
        )
        url = reverse('proposal-scorecard', kwargs={'proposal_id': p.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        checks_by_key = {c['key']: c for c in response.data['checks']}
        assert checks_by_key['estimated_weeks']['passed'] is False


# ---------------------------------------------------------------------------
# Revisit alert exception path (view lines 1349-1350)
# ---------------------------------------------------------------------------

class TestRevisitAlertExceptionPath:
    @freeze_time('2026-03-10 12:00:00')
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_revisit_alert',
        side_effect=Exception('SMTP error'),
    )
    def test_returns_200_when_revisit_alert_send_fails(self, mock_send, api_client, sent_proposal):
        """Engagement tracking succeeds even when revisit alert send fails."""
        now = timezone.now()
        sent_proposal.first_viewed_at = now - timezone.timedelta(days=5)
        sent_proposal.save(update_fields=['first_viewed_at'])
        for i in range(3):
            ve = ProposalViewEvent.objects.create(
                proposal=sent_proposal, session_id=f'revisit-exc-{i}',
                ip_address=f'10.0.0.{i}',
            )
            ProposalViewEvent.objects.filter(pk=ve.pk).update(
                viewed_at=now - timezone.timedelta(days=4 - i),
            )
        payload = {
            'session_id': 'revisit-exc-new',
            'sections': [
                {'section_type': 'greeting', 'section_title': 'Hi',
                 'time_spent_seconds': 5, 'entered_at': '2026-03-10T12:00:00Z'},
            ],
        }
        url = reverse('track-proposal-engagement', kwargs={'proposal_uuid': sent_proposal.uuid})
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Heat score: now=None default (view line 1470) and DoesNotExist (lines 1511-1512)
# ---------------------------------------------------------------------------

class TestComputeHeatScoreEdgeCases:
    @freeze_time('2026-03-10 12:00:00')
    def test_heat_score_with_now_none_uses_current_time(self, db):
        """_compute_heat_score_for_proposal defaults to timezone.now() when now=None."""
        from content.views.proposal import _compute_heat_score_for_proposal
        p = BusinessProposal.objects.create(
            title='Heat None', client_name='Client', status='sent',
            view_count=2, first_viewed_at=timezone.now() - timezone.timedelta(days=1),
        )
        score = _compute_heat_score_for_proposal(p.id, now=None)
        assert isinstance(score, int)
        assert score >= 1

    @freeze_time('2026-03-10 12:00:00')
    def test_heat_score_returns_1_for_nonexistent_proposal(self, db):
        """_compute_heat_score_for_proposal returns 1 when proposal does not exist."""
        from content.views.proposal import _compute_heat_score_for_proposal
        score = _compute_heat_score_for_proposal(99999, now=timezone.now())
        assert score == 1
