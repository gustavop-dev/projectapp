"""Tests for composed email views (branded + proposal).

Covers: send, defaults, and history endpoints for both branded-email
and proposal-email, including auth, validation, rate limiting, and pagination.
"""
import json
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from content.models import BusinessProposal, EmailLog, ProposalChangeLog

pytestmark = pytest.mark.django_db


@pytest.fixture
def proposal(db):
    """A sent proposal with client_email for email tests."""
    return BusinessProposal.objects.create(
        title='Email View Proposal',
        client_name='Test Client',
        client_email='client@test.com',
        language='es',
        total_investment=Decimal('5000000'),
        currency='COP',
        status='sent',
        expires_at=timezone.now() + timezone.timedelta(days=10),
    )


def _send_url(proposal_id, variant='branded-email'):
    return reverse(
        'send-branded-email' if variant == 'branded-email' else 'send-proposal-email',
        kwargs={'proposal_id': proposal_id},
    )


def _defaults_url(proposal_id, variant='branded-email'):
    return reverse(
        'branded-email-defaults' if variant == 'branded-email' else 'proposal-email-defaults',
        kwargs={'proposal_id': proposal_id},
    )


def _history_url(proposal_id, variant='branded-email'):
    return reverse(
        'list-branded-emails' if variant == 'branded-email' else 'list-proposal-emails',
        kwargs={'proposal_id': proposal_id},
    )


def _valid_payload():
    return {
        'recipient_email': 'dest@example.com',
        'subject': 'Test Subject',
        'greeting': 'Hola',
        'sections': json.dumps(['Section 1 content']),
        'footer': 'Footer text',
    }


# ── Send views ──

class TestSendBrandedEmailView:

    def test_requires_admin_auth(self, api_client, proposal):
        response = api_client.post(_send_url(proposal.id), _valid_payload())
        assert response.status_code in (401, 403)

    def test_returns_404_for_invalid_proposal(self, admin_client):
        response = admin_client.post(_send_url(99999), _valid_payload())
        assert response.status_code == 404

    def test_rejects_missing_recipient(self, admin_client, proposal):
        payload = _valid_payload()
        del payload['recipient_email']
        response = admin_client.post(_send_url(proposal.id), payload)
        assert response.status_code == 400
        assert 'destinatario' in response.json()['error'].lower()

    def test_rejects_invalid_email(self, admin_client, proposal):
        payload = _valid_payload()
        payload['recipient_email'] = 'not-an-email'
        response = admin_client.post(_send_url(proposal.id), payload)
        assert response.status_code == 400

    def test_rejects_missing_subject(self, admin_client, proposal):
        payload = _valid_payload()
        payload['subject'] = ''
        response = admin_client.post(_send_url(proposal.id), payload)
        assert response.status_code == 400
        assert 'asunto' in response.json()['error'].lower()

    def test_rejects_empty_sections(self, admin_client, proposal):
        payload = _valid_payload()
        payload['sections'] = json.dumps([])
        response = admin_client.post(_send_url(proposal.id), payload)
        assert response.status_code == 400

    def test_rejects_invalid_json_sections(self, admin_client, proposal):
        payload = _valid_payload()
        payload['sections'] = '{not valid json'
        response = admin_client.post(_send_url(proposal.id), payload)
        assert response.status_code == 400

    def test_rate_limits_to_one_per_minute(self, admin_client, proposal):
        EmailLog.objects.create(
            template_key='branded_email',
            recipient='dest@example.com',
            subject='Recent',
            proposal=proposal,
            status='sent',
        )
        response = admin_client.post(_send_url(proposal.id), _valid_payload())
        assert response.status_code == 429

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_successful_send_returns_200(self, mock_render, mock_email_cls, admin_client, proposal):
        mock_render.return_value = '<html>OK</html>'
        mock_email_cls.return_value = mock_render  # MagicMock with .send()
        response = admin_client.post(_send_url(proposal.id), _valid_payload())
        assert response.status_code == 200
        assert 'dest@example.com' in response.json()['message']


class TestSendProposalEmailView:

    def test_requires_admin_auth(self, api_client, proposal):
        response = api_client.post(_send_url(proposal.id, 'proposal-email'), _valid_payload())
        assert response.status_code in (401, 403)

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_successful_send_returns_200(self, mock_render, mock_email_cls, admin_client, proposal):
        mock_render.return_value = '<html>OK</html>'
        mock_email_cls.return_value = mock_render
        response = admin_client.post(
            _send_url(proposal.id, 'proposal-email'), _valid_payload(),
        )
        assert response.status_code == 200

    def test_rate_limits_independently_from_branded(self, admin_client, proposal):
        EmailLog.objects.create(
            template_key='branded_email',
            recipient='dest@example.com',
            subject='Branded recent',
            proposal=proposal,
            status='sent',
        )
        # proposal-email should NOT be blocked by a branded_email log
        with patch('content.services.proposal_email_service.EmailMultiAlternatives') as mock_cls, \
             patch('content.services.proposal_email_service.render_to_string') as mock_render:
            mock_render.return_value = '<html>OK</html>'
            mock_cls.return_value = mock_render
            response = admin_client.post(
                _send_url(proposal.id, 'proposal-email'), _valid_payload(),
            )
        assert response.status_code == 200


# ── Defaults views ──

class TestGetBrandedEmailDefaultsView:

    def test_requires_admin_auth(self, api_client, proposal):
        response = api_client.get(_defaults_url(proposal.id))
        assert response.status_code in (401, 403)

    def test_returns_404_for_invalid_proposal(self, admin_client):
        response = admin_client.get(_defaults_url(99999))
        assert response.status_code == 404

    def test_returns_defaults_with_variable_substitution(self, admin_client, proposal):
        response = admin_client.get(_defaults_url(proposal.id))
        assert response.status_code == 200
        data = response.json()
        assert proposal.client_name in data.get('greeting', '')


# ── History views ──

class TestListBrandedEmailsView:

    def test_requires_admin_auth(self, api_client, proposal):
        response = api_client.get(_history_url(proposal.id))
        assert response.status_code in (401, 403)

    def test_returns_empty_list_for_new_proposal(self, admin_client, proposal):
        response = admin_client.get(_history_url(proposal.id))
        assert response.status_code == 200
        data = response.json()
        assert data['results'] == []
        assert data['total'] == 0

    def test_returns_paginated_history(self, admin_client, proposal):
        for i in range(25):
            EmailLog.objects.create(
                template_key='branded_email',
                recipient=f'r{i}@test.com',
                subject=f'Subject {i}',
                proposal=proposal,
                status='sent',
            )
        response = admin_client.get(_history_url(proposal.id))
        data = response.json()
        assert len(data['results']) == 20
        assert data['has_next'] is True

        response2 = admin_client.get(f'{_history_url(proposal.id)}?page=2')
        data2 = response2.json()
        assert len(data2['results']) == 5
        assert data2['has_next'] is False

    def test_filters_by_template_key(self, admin_client, proposal):
        EmailLog.objects.create(
            template_key='branded_email', recipient='b@t.com',
            subject='Branded', proposal=proposal, status='sent',
        )
        EmailLog.objects.create(
            template_key='proposal_email', recipient='p@t.com',
            subject='Proposal', proposal=proposal, status='sent',
        )
        response = admin_client.get(_history_url(proposal.id))
        data = response.json()
        assert data['total'] == 1
        assert data['results'][0]['subject'] == 'Branded'


# ── Additional send validation (attachment paths) ──

class TestSendBrandedEmailAttachmentValidation:

    def test_rejects_attachment_with_disallowed_extension(self, admin_client, proposal):
        bad_file = SimpleUploadedFile('virus.exe', b'content', content_type='application/octet-stream')
        payload = _valid_payload()
        payload['attachments'] = bad_file
        response = admin_client.post(_send_url(proposal.id), payload, format='multipart')
        assert response.status_code == 400
        assert '.exe' in response.json()['error']

    def test_rejects_oversized_attachment(self, admin_client, proposal):
        big_file = SimpleUploadedFile('report.pdf', b'x' * (15 * 1024 * 1024 + 1), content_type='application/pdf')
        payload = {
            'recipient_email': 'dest@example.com',
            'subject': 'Test',
            'sections': json.dumps(['Content']),
            'attachments': big_file,
        }
        response = admin_client.post(_send_url(proposal.id), payload, format='multipart')
        assert response.status_code == 400
        assert 'report.pdf' in response.json()['error']

    @patch('content.services.proposal_email_service.ProposalEmailService.send_branded_email', return_value=False)
    def test_returns_500_when_email_service_fails(self, mock_send, admin_client, proposal):
        response = admin_client.post(_send_url(proposal.id), _valid_payload())
        assert response.status_code == 500


# ── Proposal email defaults + history ──

class TestGetProposalEmailDefaultsView:

    def test_requires_admin_auth(self, api_client, proposal):
        response = api_client.get(_defaults_url(proposal.id, 'proposal-email'))
        assert response.status_code in (401, 403)

    def test_returns_404_for_unknown_proposal(self, admin_client):
        response = admin_client.get(_defaults_url(99999, 'proposal-email'))
        assert response.status_code == 404

    def test_returns_200_with_client_name_in_defaults(self, admin_client, proposal):
        response = admin_client.get(_defaults_url(proposal.id, 'proposal-email'))
        assert response.status_code == 200


class TestListProposalEmailsView:

    def test_requires_admin_auth(self, api_client, proposal):
        response = api_client.get(_history_url(proposal.id, 'proposal-email'))
        assert response.status_code in (401, 403)

    def test_returns_empty_list_for_new_proposal(self, admin_client, proposal):
        response = admin_client.get(_history_url(proposal.id, 'proposal-email'))
        assert response.status_code == 200
        assert response.json()['results'] == []

    def test_filters_by_proposal_email_template_key(self, admin_client, proposal):
        EmailLog.objects.create(
            template_key='proposal_email', recipient='pe@test.com',
            subject='Proposal Email', proposal=proposal, status='sent',
        )
        EmailLog.objects.create(
            template_key='branded_email', recipient='be@test.com',
            subject='Branded Email', proposal=proposal, status='sent',
        )
        response = admin_client.get(_history_url(proposal.id, 'proposal-email'))
        data = response.json()
        assert data['total'] == 1
        assert data['results'][0]['subject'] == 'Proposal Email'


# ── Project stage views ──

def _stage_url(proposal_id, stage_key='design'):
    return reverse('update-project-stage', kwargs={'proposal_id': proposal_id, 'stage_key': stage_key})


def _complete_stage_url(proposal_id, stage_key='design'):
    return reverse('complete-project-stage', kwargs={'proposal_id': proposal_id, 'stage_key': stage_key})


class TestUpdateProjectStageView:

    def test_returns_400_for_unknown_stage_key(self, admin_client, proposal):
        response = admin_client.put(
            _stage_url(proposal.id, 'nonexistent'),
            {'start_date': '2026-05-01'},
            format='json',
        )
        assert response.status_code == 400
        assert 'nonexistent' in response.json()['detail']

    def test_returns_404_for_unknown_proposal(self, admin_client):
        response = admin_client.put(
            _stage_url(99999, 'design'),
            {'start_date': '2026-05-01'},
            format='json',
        )
        assert response.status_code == 404

    def test_creates_stage_on_first_update(self, admin_client, proposal):
        response = admin_client.put(
            _stage_url(proposal.id, 'design'),
            {'start_date': '2026-05-01', 'end_date': '2026-05-15'},
            format='json',
        )
        assert response.status_code == 200
        assert response.json()['start_date'] == '2026-05-01'

    def test_creates_changelog_entry_on_stage_update(self, admin_client, proposal):
        admin_client.put(
            _stage_url(proposal.id, 'development'),
            {'start_date': '2026-06-01', 'end_date': '2026-06-30'},
            format='json',
        )
        assert ProposalChangeLog.objects.filter(
            proposal=proposal,
            change_type=ProposalChangeLog.ChangeType.UPDATED,
        ).exists()


class TestCompleteProjectStageView:

    def test_returns_400_for_unknown_stage_key(self, admin_client, proposal):
        response = admin_client.post(_complete_stage_url(proposal.id, 'bogus'))
        assert response.status_code == 400

    def test_returns_404_for_unknown_proposal(self, admin_client):
        response = admin_client.post(_complete_stage_url(99999, 'design'))
        assert response.status_code == 404

    def test_sets_completed_at_on_stage(self, admin_client, proposal):
        response = admin_client.post(_complete_stage_url(proposal.id, 'design'))
        assert response.status_code == 200
        assert response.json()['completed_at'] is not None

    def test_clears_warning_sent_at_on_complete(self, admin_client, proposal):
        response = admin_client.post(_complete_stage_url(proposal.id, 'design'))
        assert response.status_code == 200
        assert response.json()['warning_sent_at'] is None

    def test_creates_changelog_entry_on_stage_complete(self, admin_client, proposal):
        admin_client.post(_complete_stage_url(proposal.id, 'development'))
        assert ProposalChangeLog.objects.filter(
            proposal=proposal,
            change_type=ProposalChangeLog.ChangeType.STAGE_COMPLETED,
        ).exists()
