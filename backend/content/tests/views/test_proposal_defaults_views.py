"""Tests for proposal defaults API views (GET/PUT/RESET)."""
import pytest
from django.urls import reverse

from content.models import ProposalDefaultConfig

pytestmark = pytest.mark.django_db


SAMPLE_SECTIONS = [
    {
        'section_type': 'greeting',
        'title': 'Saludo',
        'order': 0,
        'is_wide_panel': False,
        'content_json': {'proposalTitle': '', 'clientName': ''},
    },
    {
        'section_type': 'executive_summary',
        'title': 'Resumen Ejecutivo',
        'order': 1,
        'is_wide_panel': True,
        'content_json': {'index': '02', 'title': 'Resumen'},
    },
]


# ---------------------------------------------------------------------------
# GET /api/proposals/defaults/
# ---------------------------------------------------------------------------


class TestGetProposalDefaults:
    def test_returns_hardcoded_defaults_when_no_db_config(self, admin_client):
        url = reverse('proposal-defaults')
        response = admin_client.get(url, {'lang': 'es'})
        assert response.status_code == 200
        data = response.json()
        assert data['language'] == 'es'
        assert data['id'] is None
        assert data['expiration_days'] == 21
        assert isinstance(data['sections_json'], list)
        assert len(data['sections_json']) > 0
        assert data['sections_json'][0]['section_type'] == 'greeting'

    def test_returns_db_config_when_exists(self, admin_client):
        ProposalDefaultConfig.objects.create(
            language='es', sections_json=SAMPLE_SECTIONS, expiration_days=28,
        )
        url = reverse('proposal-defaults')
        response = admin_client.get(url, {'lang': 'es'})
        assert response.status_code == 200
        data = response.json()
        assert data['id'] is not None
        assert data['expiration_days'] == 28
        assert len(data['sections_json']) == 2
        assert data['sections_json'][0]['section_type'] == 'greeting'

    def test_returns_english_hardcoded_defaults(self, admin_client):
        url = reverse('proposal-defaults')
        response = admin_client.get(url, {'lang': 'en'})
        assert response.status_code == 200
        data = response.json()
        assert data['language'] == 'en'
        assert isinstance(data['sections_json'], list)
        assert len(data['sections_json']) > 0

    def test_defaults_to_es_when_no_lang_param(self, admin_client):
        url = reverse('proposal-defaults')
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.json()['language'] == 'es'

    def test_rejects_invalid_language(self, admin_client):
        url = reverse('proposal-defaults')
        response = admin_client.get(url, {'lang': 'fr'})
        assert response.status_code == 400

    def test_requires_admin_auth(self, api_client):
        url = reverse('proposal-defaults')
        response = api_client.get(url)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/proposals/defaults/
# ---------------------------------------------------------------------------


class TestPutProposalDefaults:
    def test_creates_new_config(self, admin_client):
        url = reverse('proposal-defaults')
        payload = {
            'language': 'es',
            'sections_json': SAMPLE_SECTIONS,
            'expiration_days': 21,
        }
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] is not None
        assert data['language'] == 'es'
        assert data['expiration_days'] == 21
        assert len(data['sections_json']) == 2
        assert ProposalDefaultConfig.objects.filter(language='es').exists()

    def test_updates_existing_config(self, admin_client):
        ProposalDefaultConfig.objects.create(
            language='es', sections_json=SAMPLE_SECTIONS, expiration_days=21,
        )
        url = reverse('proposal-defaults')
        updated = [SAMPLE_SECTIONS[0]]
        payload = {'language': 'es', 'sections_json': updated, 'expiration_days': 14}
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 200
        assert len(response.json()['sections_json']) == 1
        assert response.json()['expiration_days'] == 14
        assert ProposalDefaultConfig.objects.filter(language='es').count() == 1

    def test_validates_sections_json_must_be_list(self, admin_client):
        url = reverse('proposal-defaults')
        payload = {'language': 'es', 'sections_json': {'not': 'a list'}}
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 400

    def test_validates_section_required_keys(self, admin_client):
        url = reverse('proposal-defaults')
        payload = {
            'language': 'es',
            'sections_json': [{'section_type': 'greeting'}],
        }
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 400

    def test_validates_language_choices(self, admin_client):
        url = reverse('proposal-defaults')
        payload = {'language': 'fr', 'sections_json': SAMPLE_SECTIONS}
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 400

    def test_validates_expiration_days_range(self, admin_client):
        url = reverse('proposal-defaults')
        payload = {
            'language': 'es',
            'sections_json': SAMPLE_SECTIONS,
            'expiration_days': 0,
        }
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 400

    def test_requires_admin_auth(self, api_client):
        url = reverse('proposal-defaults')
        payload = {'language': 'es', 'sections_json': SAMPLE_SECTIONS}
        response = api_client.put(url, payload, format='json')
        assert response.status_code == 401

    def test_persists_all_general_fields_round_trip(self, admin_client):
        url = reverse('proposal-defaults')
        payload = {
            'language': 'es',
            'sections_json': SAMPLE_SECTIONS,
            'default_currency': 'USD',
            'default_total_investment': '1234.50',
            'hosting_percent': 45,
            'hosting_discount_semiannual': 25,
            'hosting_discount_quarterly': 12,
            'expiration_days': 30,
            'reminder_days': 5,
            'urgency_reminder_days': 10,
            'default_discount_percent': 15,
            'default_slug_pattern': 'Mi Propuesta Especial',
        }
        put_resp = admin_client.put(url, payload, format='json')
        assert put_resp.status_code == 200, put_resp.content

        get_resp = admin_client.get(url, {'lang': 'es'})
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data['default_currency'] == 'USD'
        assert float(data['default_total_investment']) == 1234.50
        assert data['hosting_percent'] == 45
        assert data['hosting_discount_semiannual'] == 25
        assert data['hosting_discount_quarterly'] == 12
        assert data['expiration_days'] == 30
        assert data['reminder_days'] == 5
        assert data['urgency_reminder_days'] == 10
        assert data['default_discount_percent'] == 15
        assert data['default_slug_pattern'] == 'Mi Propuesta Especial'

    def test_rejects_hosting_percent_out_of_range(self, admin_client):
        url = reverse('proposal-defaults')
        payload = {
            'language': 'es',
            'sections_json': SAMPLE_SECTIONS,
            'hosting_percent': 150,
        }
        response = admin_client.put(url, payload, format='json')
        assert response.status_code == 400
        assert 'hosting_percent' in response.json()


# ---------------------------------------------------------------------------
# POST /api/proposals/defaults/reset/
# ---------------------------------------------------------------------------


class TestResetProposalDefaults:
    def test_deletes_existing_config(self, admin_client):
        ProposalDefaultConfig.objects.create(
            language='es', sections_json=SAMPLE_SECTIONS,
        )
        url = reverse('reset-proposal-defaults')
        response = admin_client.post(url, {'language': 'es'}, format='json')
        assert response.status_code == 200
        assert response.json()['deleted'] is True
        assert not ProposalDefaultConfig.objects.filter(language='es').exists()

    def test_returns_false_when_no_config_to_delete(self, admin_client):
        url = reverse('reset-proposal-defaults')
        response = admin_client.post(url, {'language': 'es'}, format='json')
        assert response.status_code == 200
        assert response.json()['deleted'] is False

    def test_rejects_invalid_language(self, admin_client):
        url = reverse('reset-proposal-defaults')
        response = admin_client.post(url, {'language': 'fr'}, format='json')
        assert response.status_code == 400

    def test_requires_admin_auth(self, api_client):
        url = reverse('reset-proposal-defaults')
        response = api_client.post(url, {'language': 'es'}, format='json')
        assert response.status_code == 401

    def test_only_deletes_requested_language(self, admin_client):
        ProposalDefaultConfig.objects.create(language='es', sections_json=SAMPLE_SECTIONS)
        ProposalDefaultConfig.objects.create(language='en', sections_json=SAMPLE_SECTIONS)
        url = reverse('reset-proposal-defaults')
        admin_client.post(url, {'language': 'es'}, format='json')
        assert not ProposalDefaultConfig.objects.filter(language='es').exists()
        assert ProposalDefaultConfig.objects.filter(language='en').exists()
