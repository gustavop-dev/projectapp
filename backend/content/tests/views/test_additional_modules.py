from datetime import datetime, timezone as datetime_timezone
from io import BytesIO
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from pypdf import PdfReader
from rest_framework.test import APIClient

from content.models import (
    AdditionalModule,
    AdditionalModuleCategory,
    AdditionalModuleShareLink,
    AdditionalModuleShareView,
)


pytestmark = pytest.mark.django_db
FIXED_REVOKED_AT = datetime(2026, 8, 20, 12, tzinfo=datetime_timezone.utc)


def module_data(category, slug='landing-page', order=0):
    return {
        'category': category,
        'slug': slug,
        'icon': '🚀',
        'order': order,
        'name_es': f'Módulo {slug}',
        'name_en': f'{slug} module',
        'summary_es': 'Resuelve una necesidad comercial concreta.',
        'summary_en': 'Solves one concrete commercial need.',
        'what_is_es': 'Una capacidad integrada a la plataforma.',
        'what_is_en': 'A capability integrated into the platform.',
        'purpose_es': 'Ayudar al cliente a completar una tarea.',
        'purpose_en': 'Help the customer complete a task.',
        'problems_solved_es': ['Evita trabajo manual.'],
        'problems_solved_en': ['Avoids manual work.'],
        'integrations_es': ['Se integra con el flujo principal.'],
        'integrations_en': ['Integrates with the core flow.'],
        'implementation_requirements_es': ['Definir reglas del negocio.'],
        'implementation_requirements_en': ['Define the business rules.'],
    }


@pytest.fixture
def catalog():
    AdditionalModuleShareView.objects.all().delete()
    AdditionalModuleShareLink.objects.all().delete()
    AdditionalModule.objects.all().delete()
    AdditionalModuleCategory.objects.all().delete()
    commerce = AdditionalModuleCategory.objects.create(
        slug='commerce',
        name_es='Comercio',
        name_en='Commerce',
        order=0,
    )
    experience = AdditionalModuleCategory.objects.create(
        slug='experience',
        name_es='Experiencia',
        name_en='Experience',
        order=1,
    )
    landing = AdditionalModule.objects.create(**module_data(commerce))
    pwa = AdditionalModule.objects.create(
        **module_data(experience, slug='pwa', order=0),
    )
    return commerce, experience, landing, pwa


@pytest.fixture
def staff_client():
    user = get_user_model().objects.create_user(
        username='catalog-admin',
        password='catalog-pass',
        is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    client.user = user
    return client


def create_share(user, modules, **overrides):
    share = AdditionalModuleShareLink.objects.create(
        recipient_label=overrides.get('recipient_label', 'Cliente demo'),
        language=overrides.get('language', 'es'),
        created_by=user,
    )
    share.selected_modules.set(modules)
    return share


def test_public_catalog_localizes_content_without_price_fields(catalog):
    response = APIClient().get('/api/additional-modules/public/?lang=en')

    assert response.status_code == 200
    assert response.data['total_modules'] == 2
    assert response.data['categories'][0]['name'] == 'Commerce'
    assert response.data['categories'][0]['modules'][0]['name'] == 'landing-page module'
    assert 'price' not in str(response.data).lower()


def test_public_catalog_rejects_unknown_language(catalog):
    response = APIClient().get('/api/additional-modules/public/?lang=fr')

    assert response.status_code == 400
    assert response.data['lang'] == ['Usa es o en.']


def test_admin_module_create_rejects_empty_detail_lists(catalog, staff_client):
    commerce, _experience, _landing, _pwa = catalog
    payload = module_data(commerce, slug='empty-details', order=3)
    payload['category'] = commerce.id
    payload['problems_solved_es'] = []

    response = staff_client.post(
        '/api/additional-modules/admin/modules/',
        payload,
        format='json',
    )

    assert response.status_code == 400
    assert response.data['problems_solved_es'] == ['Incluye al menos un elemento.']


def test_category_retire_conflicts_while_active_modules_remain(catalog, staff_client):
    commerce, _experience, _landing, _pwa = catalog

    response = staff_client.post(
        f'/api/additional-modules/admin/categories/{commerce.id}/retire/',
        {},
        format='json',
    )

    assert response.status_code == 409
    assert response.data['active_module_count'] == 1


def test_retiring_module_removes_it_from_public_catalog(catalog, staff_client):
    """Falla si un módulo retirado sigue visible en el índice público."""
    _commerce, _experience, landing, _pwa = catalog

    retire_response = staff_client.post(
        f'/api/additional-modules/admin/modules/{landing.id}/retire/',
        {},
        format='json',
    )
    catalog_response = APIClient().get('/api/additional-modules/public/?lang=es')

    public_slugs = [
        module['slug']
        for category in catalog_response.data['categories']
        for module in category['modules']
    ]
    assert retire_response.status_code == 200
    assert retire_response.data['is_active'] is False
    assert catalog_response.status_code == 200
    assert catalog_response.data['total_modules'] == 1
    assert landing.slug not in public_slugs


def test_share_create_persists_fixed_selection(catalog, staff_client):
    _commerce, _experience, landing, pwa = catalog

    response = staff_client.post(
        '/api/additional-modules/admin/shares/',
        {
            'recipient_label': 'Campaña agosto',
            'language': 'en',
            'selected_module_ids': [pwa.id],
        },
        format='json',
    )

    assert response.status_code == 201
    share = AdditionalModuleShareLink.objects.get(uuid=response.data['uuid'])
    assert list(share.selected_modules.values_list('id', flat=True)) == [pwa.id]
    assert landing.id not in list(share.selected_modules.values_list('id', flat=True))


def test_public_share_hides_internal_recipient_and_metrics(catalog, staff_client):
    _commerce, _experience, landing, _pwa = catalog
    share = create_share(staff_client.user, [landing], recipient_label='Cuenta privada')

    response = APIClient().get(
        f'/api/additional-modules/public/shares/{share.uuid}/',
    )

    assert response.status_code == 200
    body = str(response.data)
    assert 'Cuenta privada' not in body
    assert 'view_count' not in response.data
    assert response.data['total_modules'] == 1


def test_public_share_reads_updated_live_content(catalog, staff_client):
    _commerce, _experience, landing, _pwa = catalog
    share = create_share(staff_client.user, [landing])
    landing.name_es = 'Landing actualizada'
    landing.save(update_fields=['name_es', 'updated_at'])

    response = APIClient().get(
        f'/api/additional-modules/public/shares/{share.uuid}/',
    )

    assert response.data['categories'][0]['modules'][0]['name'] == 'Landing actualizada'


def test_revoked_share_returns_gone(catalog, staff_client):
    _commerce, _experience, landing, _pwa = catalog
    share = create_share(staff_client.user, [landing])
    share.is_active = False
    share.revoked_at = FIXED_REVOKED_AT
    share.save(update_fields=['is_active', 'revoked_at'])

    response = APIClient().get(
        f'/api/additional-modules/public/shares/{share.uuid}/',
    )

    assert response.status_code == 410


def test_share_without_active_modules_returns_gone(catalog, staff_client):
    _commerce, _experience, landing, _pwa = catalog
    share = create_share(staff_client.user, [landing])
    landing.is_active = False
    landing.save(update_fields=['is_active', 'updated_at'])

    response = APIClient().get(
        f'/api/additional-modules/public/shares/{share.uuid}/',
    )

    assert response.status_code == 410


def test_tracking_counts_one_open_per_session(catalog, staff_client):
    _commerce, _experience, landing, _pwa = catalog
    share = create_share(staff_client.user, [landing])
    client = APIClient()
    url = f'/api/additional-modules/public/shares/{share.uuid}/track/'
    payload = {'session_id': 'session_12345678'}

    first = client.post(url, payload, format='json')
    second = client.post(url, payload, format='json')

    share.refresh_from_db()
    assert first.data['status'] == 'recorded'
    assert second.data['status'] == 'existing'
    assert share.view_count == 1
    assert AdditionalModuleShareView.objects.filter(share_link=share).count() == 1


def test_staff_session_preview_is_not_tracked(catalog):
    _commerce, _experience, landing, _pwa = catalog
    user = get_user_model().objects.create_user(
        username='preview-admin', password='preview-pass', is_staff=True,
    )
    share = create_share(user, [landing])
    client = APIClient()
    assert client.login(username='preview-admin', password='preview-pass')

    response = client.post(
        f'/api/additional-modules/public/shares/{share.uuid}/track/',
        {'session_id': 'preview_12345678'},
        format='json',
    )

    assert response.data['status'] == 'skipped'
    assert not AdditionalModuleShareView.objects.filter(share_link=share).exists()


def test_reorder_applies_category_and_module_positions(catalog, staff_client):
    commerce, experience, landing, pwa = catalog
    current = staff_client.get('/api/additional-modules/admin/').data

    response = staff_client.post(
        '/api/additional-modules/admin/reorder/',
        {
            'revision': current['revision'],
            'category_ids': [experience.id, commerce.id],
            'module_groups': [
                {'category_id': experience.id, 'module_ids': [pwa.id, landing.id]},
                {'category_id': commerce.id, 'module_ids': []},
            ],
        },
        format='json',
    )

    landing.refresh_from_db()
    experience.refresh_from_db()
    assert response.status_code == 200
    assert experience.order == 0
    assert landing.category_id == experience.id
    assert landing.order == 1


def test_reorder_rejects_stale_revision(catalog, staff_client):
    commerce, experience, landing, pwa = catalog

    response = staff_client.post(
        '/api/additional-modules/admin/reorder/',
        {
            'revision': 'stale',
            'category_ids': [commerce.id, experience.id],
            'module_groups': [
                {'category_id': commerce.id, 'module_ids': [landing.id]},
                {'category_id': experience.id, 'module_ids': [pwa.id]},
            ],
        },
        format='json',
    )

    assert response.status_code == 409
    assert response.data['code'] == 'stale_catalog_revision'


def test_admin_pdf_respects_selected_modules(catalog, staff_client):
    """The generated document contains only the selection and no currency."""
    _commerce, _experience, landing, pwa = catalog

    response = staff_client.post(
        '/api/additional-modules/admin/pdf/',
        {'language': 'es', 'module_ids': [landing.id]},
        format='json',
    )

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'

    text = '\n'.join(
        page.extract_text() or ''
        for page in PdfReader(BytesIO(response.content)).pages
    )
    assert landing.name_es in text
    assert pwa.name_es not in text
    assert all(currency not in text for currency in ('$', 'COP', 'USD'))


def test_public_share_pdf_uses_the_fixed_module_selection(catalog, staff_client):
    """Falla si el PDF público ignora la selección fija del enlace."""
    _commerce, _experience, landing, _pwa = catalog
    share = create_share(staff_client.user, [landing])

    with patch(
        'content.views.additional_modules.AdditionalModulePdfService.build',
        return_value=b'%PDF-public-share',
    ) as build_pdf:
        response = APIClient().get(
            f'/api/additional-modules/public/shares/{share.uuid}/pdf/',
        )

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response.content == b'%PDF-public-share'
    build_pdf.assert_called_once_with(language='es', module_ids=[landing.id])


def test_unknown_share_returns_not_found(catalog):
    response = APIClient().get(
        '/api/additional-modules/public/shares/'
        '00000000-0000-4000-8000-000000000099/',
    )

    assert response.status_code == 404
