"""Tests for email template management API views."""
import pytest
from django.urls import reverse

from content.models import EmailTemplateConfig

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# GET /api/email-templates/ (list)
# ---------------------------------------------------------------------------


class TestEmailTemplateList:
    def test_returns_all_templates_with_metadata(self, admin_client):
        url = reverse('email-template-list')
        response = admin_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 24
        keys_in_item = {
            'template_key', 'name', 'description', 'category',
            'is_active', 'is_customized', 'editable_fields_count',
        }
        assert keys_in_item.issubset(set(data[0].keys()))

    def test_shows_is_customized_true_when_override_exists(self, admin_client):
        EmailTemplateConfig.objects.create(
            template_key='proposal_sent_client',
            content_overrides={'greeting': 'Custom greeting'},
        )
        url = reverse('email-template-list')
        response = admin_client.get(url)
        data = response.json()
        sent = next(t for t in data if t['template_key'] == 'proposal_sent_client')
        assert sent['is_customized'] is True

    def test_shows_is_active_false_when_disabled(self, admin_client):
        EmailTemplateConfig.objects.create(
            template_key='proposal_reminder',
            is_active=False,
        )
        url = reverse('email-template-list')
        response = admin_client.get(url)
        data = response.json()
        reminder = next(t for t in data if t['template_key'] == 'proposal_reminder')
        assert reminder['is_active'] is False

    def test_requires_admin_auth(self, api_client):
        url = reverse('email-template-list')
        response = api_client.get(url)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/email-templates/<key>/ (detail)
# ---------------------------------------------------------------------------


class TestEmailTemplateDetail:
    def test_returns_template_detail_basic_fields(self, admin_client):
        url = reverse('email-template-detail', kwargs={'template_key': 'proposal_sent_client'})
        response = admin_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data['template_key'] == 'proposal_sent_client'
        assert data['name'] == 'Propuesta Enviada'
        assert data['category'] == 'client'

    def test_returns_template_detail_editable_fields(self, admin_client):
        url = reverse('email-template-detail', kwargs={'template_key': 'proposal_sent_client'})
        response = admin_client.get(url)
        data = response.json()
        assert isinstance(data['editable_fields'], list)
        assert len(data['editable_fields']) > 0
        field_keys = {f['key'] for f in data['editable_fields']}
        assert 'greeting' in field_keys
        assert 'body' in field_keys
        assert 'cta_text' in field_keys

    def test_returns_current_values_from_db(self, admin_client):
        EmailTemplateConfig.objects.create(
            template_key='proposal_sent_client',
            content_overrides={'greeting': 'Custom hello'},
        )
        url = reverse('email-template-detail', kwargs={'template_key': 'proposal_sent_client'})
        response = admin_client.get(url)
        data = response.json()
        greeting_field = next(f for f in data['editable_fields'] if f['key'] == 'greeting')
        assert greeting_field['current_value'] == 'Custom hello'
        assert greeting_field['is_overridden'] is True

    def test_returns_404_for_unknown_key(self, admin_client):
        url = reverse('email-template-detail', kwargs={'template_key': 'nonexistent'})
        response = admin_client.get(url)
        assert response.status_code == 404

    def test_requires_admin_auth(self, api_client):
        url = reverse('email-template-detail', kwargs={'template_key': 'proposal_sent_client'})
        response = api_client.get(url)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/email-templates/<key>/ (update)
# ---------------------------------------------------------------------------


class TestEmailTemplateUpdate:
    def test_creates_config_on_first_save(self, admin_client):
        url = reverse('email-template-detail', kwargs={'template_key': 'proposal_sent_client'})
        payload = {
            'content_overrides': {'greeting': 'Hola mundo'},
            'is_active': True,
        }
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 200
        data = response.json()
        assert data['template_key'] == 'proposal_sent_client'
        assert data['content_overrides'] == {'greeting': 'Hola mundo'}
        assert EmailTemplateConfig.objects.filter(
            template_key='proposal_sent_client',
        ).exists()

    def test_updates_existing_config(self, admin_client):
        EmailTemplateConfig.objects.create(
            template_key='proposal_sent_client',
            content_overrides={'greeting': 'Old greeting'},
        )
        url = reverse('email-template-detail', kwargs={'template_key': 'proposal_sent_client'})
        payload = {
            'content_overrides': {'greeting': 'New greeting', 'body': 'New body'},
            'is_active': True,
        }
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 200
        config = EmailTemplateConfig.objects.get(template_key='proposal_sent_client')
        assert config.content_overrides == {'greeting': 'New greeting', 'body': 'New body'}

    def test_can_disable_template(self, admin_client):
        url = reverse('email-template-detail', kwargs={'template_key': 'proposal_reminder'})
        payload = {'content_overrides': {}, 'is_active': False}
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 200
        config = EmailTemplateConfig.objects.get(template_key='proposal_reminder')
        assert config.is_active is False

    def test_strips_empty_values_from_overrides(self, admin_client):
        url = reverse('email-template-detail', kwargs={'template_key': 'proposal_sent_client'})
        payload = {
            'content_overrides': {'greeting': 'Custom', 'body': '', 'cta_text': ''},
            'is_active': True,
        }
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 200
        config = EmailTemplateConfig.objects.get(template_key='proposal_sent_client')
        assert config.content_overrides == {'greeting': 'Custom'}

    def test_rejects_invalid_field_keys(self, admin_client):
        url = reverse('email-template-detail', kwargs={'template_key': 'proposal_sent_client'})
        payload = {
            'content_overrides': {'invalid_key': 'value'},
            'is_active': True,
        }
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 400

    def test_rejects_non_dict_overrides(self, admin_client):
        url = reverse('email-template-detail', kwargs={'template_key': 'proposal_sent_client'})
        payload = {
            'content_overrides': 'not a dict',
            'is_active': True,
        }
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 400

    def test_returns_404_for_unknown_key(self, admin_client):
        url = reverse('email-template-detail', kwargs={'template_key': 'nonexistent'})
        payload = {'content_overrides': {}, 'is_active': True}
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 404

    def test_requires_admin_auth(self, api_client):
        url = reverse('email-template-detail', kwargs={'template_key': 'proposal_sent_client'})
        payload = {'content_overrides': {}, 'is_active': True}
        response = api_client.put(url, payload, format='json')
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/email-templates/<key>/preview/
# ---------------------------------------------------------------------------


class TestEmailTemplatePreview:
    def test_returns_html_preview_for_html_template(self, admin_client):
        url = reverse('email-template-preview', kwargs={'template_key': 'proposal_sent_client'})
        response = admin_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert 'html_preview' in data
        assert '<html' in data['html_preview'].lower()
        assert data['template_key'] == 'proposal_sent_client'
        assert data['subject']

    def test_returns_plain_text_preview_for_contact(self, admin_client):
        url = reverse('email-template-preview', kwargs={'template_key': 'contact_notification'})
        response = admin_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert 'html_preview' in data
        assert data['template_key'] == 'contact_notification'

    def test_preview_uses_db_overrides(self, admin_client):
        EmailTemplateConfig.objects.create(
            template_key='proposal_sent_client',
            content_overrides={'greeting': 'CUSTOM_GREETING_MARKER'},
        )
        url = reverse('email-template-preview', kwargs={'template_key': 'proposal_sent_client'})
        response = admin_client.get(url)
        assert response.status_code == 200
        assert 'CUSTOM_GREETING_MARKER' in response.json()['html_preview']

    def test_returns_404_for_unknown_key(self, admin_client):
        url = reverse('email-template-preview', kwargs={'template_key': 'nonexistent'})
        response = admin_client.get(url)
        assert response.status_code == 404

    def test_requires_admin_auth(self, api_client):
        url = reverse('email-template-preview', kwargs={'template_key': 'proposal_sent_client'})
        response = api_client.get(url)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/email-templates/<key>/reset/
# ---------------------------------------------------------------------------


class TestEmailTemplateReset:
    def test_deletes_existing_config(self, admin_client):
        EmailTemplateConfig.objects.create(
            template_key='proposal_sent_client',
            content_overrides={'greeting': 'Custom'},
        )
        url = reverse('email-template-reset', kwargs={'template_key': 'proposal_sent_client'})
        response = admin_client.post(url)
        assert response.status_code == 200
        data = response.json()
        assert data['deleted'] is True
        assert data['template_key'] == 'proposal_sent_client'
        assert not EmailTemplateConfig.objects.filter(
            template_key='proposal_sent_client',
        ).exists()

    def test_returns_false_when_no_config_to_delete(self, admin_client):
        url = reverse('email-template-reset', kwargs={'template_key': 'proposal_sent_client'})
        response = admin_client.post(url)
        assert response.status_code == 200
        assert response.json()['deleted'] is False

    def test_returns_404_for_unknown_key(self, admin_client):
        url = reverse('email-template-reset', kwargs={'template_key': 'nonexistent'})
        response = admin_client.post(url)
        assert response.status_code == 404

    def test_requires_admin_auth(self, api_client):
        url = reverse('email-template-reset', kwargs={'template_key': 'proposal_sent_client'})
        response = api_client.post(url)
        assert response.status_code == 401

    def test_only_deletes_requested_template(self, admin_client):
        """Resetting one template must not affect other templates' overrides."""
        EmailTemplateConfig.objects.create(
            template_key='proposal_sent_client',
            content_overrides={'greeting': 'Custom'},
        )
        EmailTemplateConfig.objects.create(
            template_key='proposal_reminder',
            content_overrides={'greeting': 'Other custom'},
        )
        url = reverse('email-template-reset', kwargs={'template_key': 'proposal_sent_client'})
        admin_client.post(url)
        assert not EmailTemplateConfig.objects.filter(
            template_key='proposal_sent_client',
        ).exists()
        assert EmailTemplateConfig.objects.filter(
            template_key='proposal_reminder',
        ).exists()
