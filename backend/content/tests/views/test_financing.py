import re
from decimal import Decimal
from io import BytesIO
from urllib.parse import quote

import pytest
from pypdf import PdfReader
from rest_framework.test import APIClient

from content.models import ExplainerVideoSettings, HourPackage, Nationality
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
    assert 'partnership-program.pdf' in response['Content-Disposition']


def test_public_pdf_names_spanish_download_after_partnership_program(pro_package):
    response = APIClient().get('/api/financing/public/pdf/?lang=es')

    assert response.status_code == 200
    assert 'filename="programa-de-alianza.pdf"' in response['Content-Disposition']


def test_public_pdf_titles_the_partnership_program(pro_package):
    """Fails if the booklet keeps presenting itself as a financing-only program."""
    response = APIClient().get('/api/financing/public/pdf/?lang=es')
    reader = PdfReader(BytesIO(response.content))

    assert reader.metadata.title == 'Programa de Alianza'
    assert 'Programa de Alianza' in (reader.pages[0].extract_text() or '')


def test_public_pdf_expands_financing_terms(pro_package):
    """Fails if the public PDF omits the commercial financing terms it promises."""
    response = APIClient().get('/api/financing/public/pdf/?lang=es')
    text = '\n'.join(
        page.extract_text() or ''
        for page in PdfReader(BytesIO(response.content)).pages
    )

    assert 'Las 8 condiciones comerciales' in text
    assert 'Custodia de código no es cesión de propiedad' in text
    assert 'Paquete Pro vigente' in text


def test_sitemap_lists_partnership_program_instead_of_financing(pro_package):
    """Fails if the sitemap drops the renamed page or keeps the redirected route."""
    response = APIClient().get('/sitemap.xml')
    body = response.content.decode()

    assert response.status_code == 200
    assert '<loc>https://projectapp.co/es-co/partnership-program</loc>' in body
    assert '<loc>https://projectapp.co/en-us/partnership-program</loc>' in body
    assert not re.search(r'/(?:es-co|en-us)/financing\b', body)


def test_public_program_names_the_partnership_program(pro_package):
    """Fails if the hero, CTA or WhatsApp message stop naming the Partnership Program."""
    spanish = APIClient().get('/api/financing/public/?lang=es').data
    english = APIClient().get('/api/financing/public/?lang=en').data

    assert spanish['hero']['eyebrow'].startswith('Programa de Alianza')
    assert spanish['cta']['title'] == 'Solicita tu evaluación para el Programa de Alianza'
    assert quote('Programa de Alianza') in spanish['cta']['whatsapp_url']
    assert english['hero']['eyebrow'].startswith('Partnership Program')
    assert english['cta']['title'] == 'Request your Partnership Program evaluation'


def test_public_program_points_canonical_path_to_partnership_program(pro_package):
    spanish = APIClient().get('/api/financing/public/?lang=es').data
    english = APIClient().get('/api/financing/public/?lang=en').data

    assert spanish['canonical_path'] == '/es-co/partnership-program'
    assert english['canonical_path'] == '/en-us/partnership-program'


def test_public_program_follows_financing_video_switch(pro_package):
    """Fails if hiding the Partnership Program video in the panel still shows it."""
    visible = APIClient().get('/api/financing/public/?lang=es')
    stored = ExplainerVideoSettings.load()
    stored.show_financing_video = False
    stored.save()
    hidden = APIClient().get('/api/financing/public/?lang=es')

    assert visible.data['show_explainer_video'] is True
    assert hidden.data['show_explainer_video'] is False
