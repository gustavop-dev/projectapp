"""Tests for standalone email API views.

Covers: send_standalone_email, get_standalone_email_defaults, list_standalone_emails,
and the _parse_standalone_email validator (rate-limit, email, subject, sections, attachments).
"""
import json
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from content.models import EmailLog

pytestmark = pytest.mark.django_db


# ── get_standalone_email_defaults ─────────────────────────────────────────────

class TestGetStandaloneEmailDefaults:
    def test_returns_200_for_admin(self, admin_client):
        url = reverse('standalone-email-defaults')
        with patch(
            'content.services.proposal_email_service.ProposalEmailService._resolve_content',
            return_value={'subject': 'Hi', 'greeting': 'Hello', 'sections': [], 'footer': ''},
        ):
            response = admin_client.get(url)
        assert response.status_code == 200

    def test_returns_401_for_unauthenticated(self, api_client):
        url = reverse('standalone-email-defaults')
        response = api_client.get(url)
        assert response.status_code == 401


# ── list_standalone_emails ────────────────────────────────────────────────────

class TestListStandaloneEmails:
    def test_returns_200_with_empty_results(self, admin_client):
        url = reverse('list-standalone-emails')
        response = admin_client.get(url)
        assert response.status_code == 200
        assert 'results' in response.data
        assert response.data['results'] == []

    def test_returns_401_for_unauthenticated(self, api_client):
        url = reverse('list-standalone-emails')
        response = api_client.get(url)
        assert response.status_code == 401

    def test_includes_standalone_email_log_in_results(self, admin_client):
        EmailLog.objects.create(
            proposal=None,
            template_key='branded_email',
            recipient='test@example.com',
            subject='Test Subject',
            status='sent',
        )
        url = reverse('list-standalone-emails')
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.data['total'] == 1
        assert response.data['results'][0]['recipient'] == 'test@example.com'

    def test_excludes_proposal_tied_email_logs(self, admin_client, proposal):
        EmailLog.objects.create(
            proposal=proposal,
            template_key='branded_email',
            recipient='tied@example.com',
            subject='Proposal Email',
            status='sent',
        )
        url = reverse('list-standalone-emails')
        response = admin_client.get(url)
        assert response.data['total'] == 0

    def test_pagination_uses_page_size_20(self, admin_client):
        url = reverse('list-standalone-emails')
        response = admin_client.get(url)
        assert response.data['page_size'] == 20

    def test_page_query_param_accepted(self, admin_client):
        url = reverse('list-standalone-emails')
        response = admin_client.get(url, {'page': '1'})
        assert response.status_code == 200
        assert response.data['page'] == 1

    def test_invalid_page_param_falls_back_to_page_one(self, admin_client):
        url = reverse('list-standalone-emails')
        response = admin_client.get(url, {'page': 'notanumber'})
        assert response.status_code == 200
        assert response.data['page'] == 1


# ── send_standalone_email — auth ──────────────────────────────────────────────

class TestSendStandaloneEmailAuth:
    def test_returns_401_for_unauthenticated(self, api_client):
        url = reverse('send-standalone-email')
        response = api_client.post(url, {}, format='json')
        assert response.status_code == 401


# ── send_standalone_email — rate limit ────────────────────────────────────────

class TestSendStandaloneEmailRateLimit:
    @freeze_time('2026-04-01 12:00:00')
    def test_returns_429_when_recent_email_exists(self, admin_client):
        EmailLog.objects.create(
            proposal=None,
            template_key='branded_email',
            recipient='anyone@example.com',
            subject='Previous send',
            status='sent',
            sent_at=timezone.now() - timedelta(seconds=30),
        )
        url = reverse('send-standalone-email')
        response = admin_client.post(
            url,
            {'recipient_email': 'new@example.com', 'subject': 'Hello', 'sections': ['Body']},
            format='json',
        )
        assert response.status_code == 429


# ── send_standalone_email — validation ───────────────────────────────────────

class TestSendStandaloneEmailValidation:
    def test_returns_400_for_missing_recipient_email(self, admin_client):
        url = reverse('send-standalone-email')
        response = admin_client.post(
            url, {'subject': 'Hello', 'sections': ['Body']}, format='json',
        )
        assert response.status_code == 400

    def test_returns_400_for_invalid_recipient_email(self, admin_client):
        url = reverse('send-standalone-email')
        response = admin_client.post(
            url,
            {'recipient_email': 'not-an-email', 'subject': 'Hello', 'sections': ['Body']},
            format='json',
        )
        assert response.status_code == 400

    def test_returns_400_for_missing_subject(self, admin_client):
        url = reverse('send-standalone-email')
        response = admin_client.post(
            url,
            {'recipient_email': 'valid@example.com', 'sections': ['Body']},
            format='json',
        )
        assert response.status_code == 400

    def test_returns_400_for_empty_sections(self, admin_client):
        url = reverse('send-standalone-email')
        response = admin_client.post(
            url,
            {'recipient_email': 'valid@example.com', 'subject': 'Hi', 'sections': []},
            format='json',
        )
        assert response.status_code == 400

    def test_returns_400_for_invalid_sections_json_string(self, admin_client):
        url = reverse('send-standalone-email')
        response = admin_client.post(
            url,
            {
                'recipient_email': 'valid@example.com',
                'subject': 'Hi',
                'sections': '{not valid json',
            },
            format='multipart',
        )
        assert response.status_code == 400

    def test_returns_400_for_disallowed_attachment_extension(self, admin_client):
        url = reverse('send-standalone-email')
        bad_file = SimpleUploadedFile('virus.exe', b'bad content', content_type='application/octet-stream')
        response = admin_client.post(
            url,
            {
                'recipient_email': 'valid@example.com',
                'subject': 'Hi',
                'sections': json.dumps(['Body text']),
                'attachments': bad_file,
            },
            format='multipart',
        )
        assert response.status_code == 400

    def test_returns_400_for_oversized_attachment(self, admin_client):
        url = reverse('send-standalone-email')
        big_file = SimpleUploadedFile('report.pdf', b'x' * (15 * 1024 * 1024 + 1), content_type='application/pdf')
        response = admin_client.post(
            url,
            {
                'recipient_email': 'valid@example.com',
                'subject': 'Hi',
                'sections': json.dumps(['Body text']),
                'attachments': big_file,
            },
            format='multipart',
        )
        assert response.status_code == 400


# ── send_standalone_email — success / failure ─────────────────────────────────

class TestSendStandaloneEmailSuccess:
    def test_returns_200_when_email_sent_successfully(self, admin_client):
        url = reverse('send-standalone-email')
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_standalone_branded_email',
            return_value=True,
        ):
            response = admin_client.post(
                url,
                {
                    'recipient_email': 'client@example.com',
                    'subject': 'Hello from ProjectApp',
                    'sections': ['Section content here'],
                },
                format='json',
            )
        assert response.status_code == 200

    def test_returns_500_when_email_service_returns_false(self, admin_client):
        url = reverse('send-standalone-email')
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_standalone_branded_email',
            return_value=False,
        ):
            response = admin_client.post(
                url,
                {
                    'recipient_email': 'client@example.com',
                    'subject': 'Hello',
                    'sections': ['Some content'],
                },
                format='json',
            )
        assert response.status_code == 500
