from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader
from rest_framework.test import APIClient

from content.models import HourPackage, Nationality
from content.services.financing_program_service import serialize_financing_program


pytestmark = pytest.mark.django_db


@pytest.fixture
def pro_package():
    HourPackage.objects.filter(
        nationality=Nationality.COL,
        hours=60,
    ).delete()
    return HourPackage.objects.create(
        nationality=Nationality.COL,
        name_es='Paquete Pro vigente',
        name_en='Current Pro Pack',
        note_es='Mejoras continuas.',
        note_en='Continuous improvements.',
        hours=60,
        hourly_rate=Decimal('32000'),
        discount_percent=20,
        is_active=True,
        order=3,
    )


def test_program_localizes_live_package_name(pro_package):
    payload = serialize_financing_program(language='en')

    assert payload['package']['name'] == 'Current Pro Pack'
    assert payload['package']['catalog_synced'] is True


def test_program_package_excludes_catalog_pricing(pro_package):
    payload = serialize_financing_program(language='es')

    assert set(payload['package']).isdisjoint({'hourly_rate', 'discount_percent', 'price'})
    assert '32000' not in str(payload)


def test_program_uses_fallback_when_package_is_inactive(pro_package):
    pro_package.is_active = False
    pro_package.save(update_fields=['is_active', 'updated_at'])

    payload = serialize_financing_program(language='es')

    assert payload['package']['name'] == 'Paquete Pro'
    assert payload['package']['catalog_synced'] is False


def test_public_program_rejects_unknown_language(pro_package):
    response = APIClient().get('/api/financing/public/?lang=fr')

    assert response.status_code == 400
    assert response.data['lang'] == ['Usa es o en.']


def test_public_program_exposes_commercial_input_output(pro_package):
    response = APIClient().get('/api/financing/public/?lang=es')

    assert response.status_code == 200
    assert response.data['calculator']['input']['title'] == 'Qué se ingresa'
    assert response.data['calculator']['output']['title'] == 'Qué se obtiene'
    assert len(response.data['conditions']) == 4


def test_public_pdf_sets_private_download_headers(pro_package):
    response = APIClient().get('/api/financing/public/pdf/?lang=en')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response['Cache-Control'] == 'private, no-store'
    assert 'software-financing-program.pdf' in response['Content-Disposition']


def test_public_pdf_expands_financing_terms(pro_package):
    response = APIClient().get('/api/financing/public/pdf/?lang=es')
    text = '\n'.join(
        page.extract_text() or ''
        for page in PdfReader(BytesIO(response.content)).pages
    )

    assert 'Las cuatro condiciones comerciales' in text
    assert 'Custodia de código no es cesión de propiedad' in text
    assert 'Paquete Pro vigente' in text


def test_sitemap_includes_spanish_financing_route(pro_package):
    response = APIClient().get('/sitemap.xml')

    assert response.status_code == 200
    assert '<loc>https://projectapp.co/es-co/financing</loc>' in response.content.decode()
