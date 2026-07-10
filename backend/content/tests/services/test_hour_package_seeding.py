"""Tests for seeding proposal commercial conditions from the hour-package catalog."""
import pytest
from django.urls import reverse

from content.models import BusinessProposal, HourPackage
from content.services.hour_package_service import (
    seed_commercial_conditions_from_catalog,
)
from content.services.proposal_service import (
    build_proposal_from_json,
    create_section_for_proposal,
)

pytestmark = pytest.mark.django_db

BASE_CONTENT = {
    'index': '17',
    'title': 'Condiciones comerciales',
    'packagesTitle': 'Paquetes de horas',
    'packagesIntro': 'intro',
    'hourlyRate': 90000,
    'currency': 'COP',
    'packages': [
        {'name': 'Default', 'hours': 20, 'discountPercent': 0, 'note': 'n'},
    ],
    'effortBadge': 'badge',
    'scopeTitle': 'Alcance',
    'scopeParagraphs': ['p1'],
}


def _mex_packages():
    # Migration 0147 seeds MEX defaults; clear them so assertions on exact
    # package lists stay deterministic.
    HourPackage.objects.filter(nationality='MEX').delete()
    HourPackage.objects.create(
        nationality='MEX', name_es='Ágil MX', name_en='Agile MX',
        note_es='nota es', note_en='note en',
        hours=20, hourly_rate=45, discount_percent=0, order=2,
    )
    HourPackage.objects.create(
        nationality='MEX', name_es='Pro MX', name_en='Pro MX',
        hours=60, hourly_rate=40, discount_percent=10, order=1,
    )


class TestSeedService:
    def test_empty_catalog_returns_input_untouched(self):
        HourPackage.objects.all().delete()
        result = seed_commercial_conditions_from_catalog(
            BASE_CONTENT, nationality='COL', language='es',
        )
        assert result is BASE_CONTENT

    def test_seeds_spanish_names_and_notes(self):
        _mex_packages()
        result = seed_commercial_conditions_from_catalog(
            BASE_CONTENT, nationality='MEX', language='es',
        )
        assert [p['name'] for p in result['packages']] == ['Pro MX', 'Ágil MX']
        assert result['packages'][1]['note'] == 'nota es'

    def test_seeds_english_names_and_notes(self):
        _mex_packages()
        result = seed_commercial_conditions_from_catalog(
            BASE_CONTENT, nationality='MEX', language='en',
        )
        assert result['packages'][1]['name'] == 'Agile MX'
        assert result['packages'][1]['note'] == 'note en'

    def test_derives_currency_and_per_package_rate(self):
        _mex_packages()
        result = seed_commercial_conditions_from_catalog(
            BASE_CONTENT, nationality='MEX', language='es',
        )
        assert result['currency'] == 'USD'
        # Section-level rate keeps the first package's rate as baseline.
        assert result['hourlyRate'] == 40.0
        assert [p['hourlyRate'] for p in result['packages']] == [40.0, 45.0]
        assert [p['discountPercent'] for p in result['packages']] == [10, 0]

    def test_excludes_inactive_packages(self):
        _mex_packages()
        HourPackage.objects.create(
            nationality='MEX', name_es='Inactivo', name_en='Inactive',
            hours=100, hourly_rate=30, is_active=False, order=0,
        )
        result = seed_commercial_conditions_from_catalog(
            BASE_CONTENT, nationality='MEX', language='es',
        )
        assert all(p['name'] != 'Inactivo' for p in result['packages'])

    def test_does_not_touch_scope_texts(self):
        _mex_packages()
        result = seed_commercial_conditions_from_catalog(
            BASE_CONTENT, nationality='MEX', language='es',
        )
        assert result['scopeParagraphs'] == ['p1']
        assert result['effortBadge'] == 'badge'
        assert result['packagesTitle'] == 'Paquetes de horas'


class TestProposalCreationSeeding:
    def test_panel_create_seeds_from_catalog(self, admin_client):
        _mex_packages()
        payload = {
            'title': 'Propuesta MX', 'client_name': 'Cliente',
            'client_email': 'c@test.com', 'language': 'es',
            'total_investment': '5000.00', 'currency': 'USD',
            'nationality': 'MEX',
        }
        response = admin_client.post(
            reverse('create-proposal'), payload, format='json'
        )
        assert response.status_code == 201
        assert response.data['nationality'] == 'MEX'
        section = next(
            s for s in response.data['sections']
            if s['section_type'] == 'commercial_conditions'
        )
        content = section['content_json']
        assert content['currency'] == 'USD'
        assert [p['name'] for p in content['packages']] == ['Pro MX', 'Ágil MX']

    def test_panel_create_falls_back_to_defaults(self, admin_client):
        HourPackage.objects.all().delete()
        payload = {
            'title': 'Propuesta COL', 'client_name': 'Cliente',
            'client_email': 'c@test.com', 'language': 'es',
            'total_investment': '5000.00', 'currency': 'COP',
        }
        response = admin_client.post(
            reverse('create-proposal'), payload, format='json'
        )
        assert response.status_code == 201
        section = next(
            s for s in response.data['sections']
            if s['section_type'] == 'commercial_conditions'
        )
        content = section['content_json']
        assert content['currency'] == 'COP'
        assert [p['name'] for p in content['packages']] == [
            'Hora Puntual', 'Paquete Inicial', 'Paquete Ágil',
            'Paquete Pro', 'Paquete Premium',
        ]

    def test_from_json_seeds_when_section_not_in_payload(self):
        _mex_packages()
        proposal, _ = build_proposal_from_json({
            'title': 'JSON MX', 'client_name': 'Cliente',
            'nationality': 'MEX', 'language': 'es',
            'sections': {},
        })
        section = proposal.sections.get(section_type='commercial_conditions')
        assert section.content_json['currency'] == 'USD'
        assert section.content_json['packages'][0]['name'] == 'Pro MX'

    def test_from_json_respects_explicit_section_payload(self):
        _mex_packages()
        explicit = {
            'title': 'Custom', 'hourlyRate': 123, 'currency': 'COP',
            'packages': [{'name': 'Custom Pack', 'hours': 5,
                          'discountPercent': 0, 'note': ''}],
        }
        proposal, _ = build_proposal_from_json({
            'title': 'JSON explicit', 'client_name': 'Cliente',
            'nationality': 'MEX', 'language': 'es',
            'sections': {'commercialConditions': explicit},
        })
        section = proposal.sections.get(section_type='commercial_conditions')
        assert section.content_json['packages'][0]['name'] == 'Custom Pack'
        assert section.content_json['hourlyRate'] == 123

    def test_create_section_for_proposal_seeds(self):
        _mex_packages()
        proposal = BusinessProposal.objects.create(
            title='Sin sección', client_name='Cliente', nationality='MEX',
        )
        section = create_section_for_proposal(proposal, 'commercial_conditions')
        assert section.content_json['currency'] == 'USD'
        assert section.content_json['packages'][0]['hourlyRate'] == 40.0
