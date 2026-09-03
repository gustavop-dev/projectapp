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
    """Fails if the public program stops exposing the active localized package name."""
    payload = serialize_financing_program(language='en')

    assert payload['package']['name'] == 'Current Pro Pack'
    assert payload['package']['catalog_synced'] is True


def test_program_package_excludes_catalog_pricing(pro_package):
    """Fails if public financing data leaks the internal package price catalog."""
    payload = serialize_financing_program(language='es')

    assert set(payload['package']).isdisjoint({'hourly_rate', 'discount_percent', 'price'})
    assert '32000' not in str(payload)


def test_program_uses_fallback_when_package_is_inactive(pro_package):
    """Fails if an inactive package is presented as an available financing benefit."""
    pro_package.is_active = False
    pro_package.save(update_fields=['is_active', 'updated_at'])

    payload = serialize_financing_program(language='es')

    assert payload['package']['name'] == 'Paquete Pro'
    assert payload['package']['catalog_synced'] is False


def test_public_program_rejects_unknown_language(pro_package):
    """Fails if the public endpoint accepts a language it cannot localize."""
    response = APIClient().get('/api/financing/public/?lang=fr')

    assert response.status_code == 400
    assert response.data['lang'] == ['Usa es o en.']


def test_public_program_exposes_commercial_input_output(pro_package):
    """Fails if the calculator no longer explains its commercial input and output."""
    response = APIClient().get('/api/financing/public/?lang=es')

    assert response.status_code == 200
    assert response.data['calculator']['input']['title'] == 'Qué se ingresa'
    assert response.data['calculator']['output']['title'] == 'Qué se obtiene'


def test_public_program_exposes_two_percent_late_hosting_increase(pro_package):
    """Fails if overdue installments lose the configured Hosting consequence."""
    response = APIClient().get('/api/financing/public/?lang=es')
    payment_condition = response.data['conditions'][4]

    assert response.data['late_hosting_increase_percent'] == '2%'
    assert response.data['installment_due_day_range'] == [1, 5]
    assert payment_condition['summary'] == (
        'Cada cuota se paga entre los días 1 y 5 calendario del mes. '
        'Una cuota en mora aumenta en 2% el costo vigente del Hosting.'
    )


def test_public_program_exposes_inclusive_project_range(pro_package):
    response = APIClient().get('/api/financing/public/?lang=es')

    assert response.data['minimum_project_value_cop'] == Decimal('20000000.00')
    assert response.data['maximum_project_value_cop'] == Decimal('140000000.00')
    assert response.data['conditions'][5]['id'] == 'project-value-range'


def test_public_program_exposes_risk_based_initial_contribution(pro_package):
    response = APIClient().get('/api/financing/public/?lang=es')

    assert response.data['minimum_initial_payment_percent'] == '20%'
    assert response.data['maximum_financed_percent'] == '80%'
    assert response.data['conditions'][6]['id'] == 'risk-and-initial-payment'


def test_public_program_exposes_two_financing_cycles_for_five_year_option(pro_package):
    """Fails if the five-year option loses its second financed twelve-month cycle."""
    response = APIClient().get('/api/financing/public/?lang=es')
    five_year_option = response.data['options'][0]

    assert five_year_option['financing_cycles'] == 2
    assert five_year_option['highlights'][0] == (
        'Hasta dos ciclos separados de 12 meses al 0% de interés ordinario.'
    )


def test_public_pdf_sets_private_download_headers(pro_package):
    """Fails if the public PDF becomes cacheable or loses its named attachment."""
    response = APIClient().get('/api/financing/public/pdf/?lang=en')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response['Cache-Control'] == 'private, no-store'
    assert 'software-financing-program.pdf' in response['Content-Disposition']


def test_public_pdf_expands_financing_terms(pro_package):
    """Fails if the public PDF omits the commercial financing terms it promises."""
    response = APIClient().get('/api/financing/public/pdf/?lang=es')
    text = '\n'.join(
        page.extract_text() or ''
        for page in PdfReader(BytesIO(response.content)).pages
    )

    assert 'Las 7 condiciones comerciales' in text
    assert 'Custodia de código no es cesión de propiedad' in text
    assert 'Paquete Pro vigente' in text


def test_sitemap_includes_spanish_financing_route(pro_package):
    """Fails if the canonical Spanish financing page disappears from the sitemap."""
    response = APIClient().get('/sitemap.xml')

    assert response.status_code == 200
    assert '<loc>https://projectapp.co/es-co/financing</loc>' in response.content.decode()
