"""Tests for standalone email API views.

Covers: send_standalone_email, get_standalone_email_defaults, list_standalone_emails,
preview_composed_email, and the _parse_standalone_email validator
(rate-limit, email, subject, sections, attachments).
"""
import json
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from content.models import EmailLog, EmailTemplateConfig

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

    def test_get_includes_config_defaults_and_signers(self, admin_client, settings):
        url = reverse('standalone-email-defaults')
        response = admin_client.get(url)
        assert response.status_code == 200
        assert set(response.data['config']) == {'greeting', 'footer', 'signer'}
        assert set(response.data['defaults']) == {'greeting', 'footer', 'signer'}
        assert response.data['is_customized'] is False
        signer_keys = {s['key'] for s in response.data['available_signers']}
        assert signer_keys == set(settings.EMAIL_SIGNATURES)
        assert 'client_name' in response.data['available_variables']


# ── standalone_email_defaults — PUT ───────────────────────────────────────────

class TestPutStandaloneEmailDefaults:
    def test_returns_401_for_unauthenticated(self, api_client):
        url = reverse('standalone-email-defaults')
        response = api_client.put(url, {}, format='json')
        assert response.status_code == 401

    def test_saves_custom_values_as_overrides(self, admin_client):
        url = reverse('standalone-email-defaults')
        payload = {
            'greeting': 'Buen día {client_name}',
            'footer': 'Hasta pronto.',
            'signer': 'carlos',
        }
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 200

        config = EmailTemplateConfig.objects.get(template_key='branded_email')
        assert config.content_overrides == {
            'greeting': 'Buen día {client_name}',
            'footer': 'Hasta pronto.',
            'signer': 'carlos',
        }
        assert response.data['config']['greeting'] == 'Buen día {client_name}'
        assert response.data['config']['signer'] == 'carlos'
        assert response.data['is_customized'] is True

    def test_values_equal_to_defaults_are_not_stored(self, admin_client, settings):
        EmailTemplateConfig.objects.create(
            template_key='branded_email',
            content_overrides={'greeting': 'Custom', 'signer': 'carlos'},
        )
        url = reverse('standalone-email-defaults')
        payload = {
            'greeting': 'Hola {client_name}',
            'footer': '',
            'signer': settings.EMAIL_DEFAULT_SIGNER,
        }
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 200

        config = EmailTemplateConfig.objects.get(template_key='branded_email')
        assert config.content_overrides == {}
        assert response.data['is_customized'] is False

    def test_returns_400_for_unknown_signer(self, admin_client):
        url = reverse('standalone-email-defaults')
        response = admin_client.put(url, {'signer': 'nadie'}, format='json')
        assert response.status_code == 400
        assert EmailTemplateConfig.objects.filter(template_key='branded_email').count() == 0

    def test_configured_signer_is_used_in_standalone_preview(self, admin_client, settings):
        EmailTemplateConfig.objects.create(
            template_key='branded_email',
            content_overrides={'signer': 'carlos'},
        )
        url = reverse('preview-composed-email')
        response = admin_client.post(url, {'sections': ['contenido']}, format='json')
        assert response.status_code == 200
        assert settings.EMAIL_SIGNATURES['carlos']['name'] in response.data['html_preview']


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


# ── preview_composed_email ────────────────────────────────────────────────────

class TestPreviewComposedEmail:
    def test_returns_401_for_unauthenticated(self, api_client):
        url = reverse('preview-composed-email')
        response = api_client.post(url, {}, format='json')
        assert response.status_code == 401

    def test_returns_real_branded_template_html(self, admin_client):
        url = reverse('preview-composed-email')
        response = admin_client.post(
            url,
            {
                'subject': 'Asunto de prueba',
                'greeting': 'Hola Carlos',
                'sections': [{'text': 'Contenido de la sección.', 'markdown': False}],
                'footer': 'Quedamos atentos.',
                'attachment_names': ['contrato.pdf'],
            },
            format='json',
        )
        assert response.status_code == 200
        html = response.data['html_preview']
        assert response.data['subject'] == 'Asunto de prueba'
        assert 'Hola Carlos' in html
        assert 'Contenido de la sección.' in html
        assert 'contrato.pdf' in html
        # Elegant footer: dark contact card + social + copyright.
        assert 'team@projectapp.co' in html
        assert 'background:#001713' in html
        assert '© 2026 ProjectApp' in html

    def test_markdown_section_renders_html(self, admin_client):
        url = reverse('preview-composed-email')
        response = admin_client.post(
            url,
            {
                'sections': [
                    {'text': '**negrita**\n\n- uno\n- dos', 'markdown': True},
                ],
            },
            format='json',
        )
        assert response.status_code == 200
        html = response.data['html_preview']
        assert '<strong style="font-weight:500;">negrita</strong>' in html
        assert '<ul' in html

    def test_legacy_string_sections_accepted(self, admin_client):
        url = reverse('preview-composed-email')
        response = admin_client.post(
            url, {'sections': ['texto plano']}, format='json',
        )
        assert response.status_code == 200
        assert 'texto plano' in response.data['html_preview']

    @freeze_time('2026-04-01 12:00:00')
    def test_preview_bypasses_send_rate_limit(self, admin_client):
        EmailLog.objects.create(
            proposal=None,
            template_key='branded_email',
            recipient='anyone@example.com',
            subject='Previous send',
            status='sent',
            sent_at=timezone.now() - timedelta(seconds=30),
        )
        url = reverse('preview-composed-email')
        response = admin_client.post(
            url, {'sections': ['contenido']}, format='json',
        )
        assert response.status_code == 200

    def test_preview_creates_no_email_log(self, admin_client):
        url = reverse('preview-composed-email')
        admin_client.post(url, {'sections': ['contenido']}, format='json')
        assert EmailLog.objects.count() == 0

    def test_returns_400_for_malformed_sections_json(self, admin_client):
        url = reverse('preview-composed-email')
        response = admin_client.post(
            url, {'sections': '{not valid json'}, format='multipart',
        )
        assert response.status_code == 400

    def test_proposal_id_resolves_proposal_signature(self, admin_client, proposal, settings):
        proposal.email_signed_by = 'gustavo'
        proposal.save(update_fields=['email_signed_by'])
        url = reverse('preview-composed-email')
        response = admin_client.post(
            url,
            {'sections': ['contenido'], 'proposal_id': proposal.id},
            format='json',
        )
        assert response.status_code == 200
        signature = settings.EMAIL_SIGNATURES['gustavo']['name']
        assert signature in response.data['html_preview']


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

    def test_dict_sections_accepted_and_normalized(self, admin_client):
        url = reverse('send-standalone-email')
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_standalone_branded_email',
            return_value=True,
        ) as mock_send:
            response = admin_client.post(
                url,
                {
                    'recipient_email': 'client@example.com',
                    'subject': 'Hola',
                    'sections': [
                        {'text': '**md**', 'markdown': True},
                        'texto plano',
                    ],
                },
                format='json',
            )
        assert response.status_code == 200
        assert mock_send.call_args.kwargs['sections'] == [
            {'text': '**md**', 'markdown': True},
            {'text': 'texto plano', 'markdown': False},
        ]

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
