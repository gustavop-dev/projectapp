from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from django.core.files.storage import FileSystemStorage
from pypdf import PdfReader
from rest_framework.test import APIClient

from content.models import (
    FinancingAgreement,
    FinancingAgreementTemplate,
    HourPackage,
    Nationality,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def pro_package():
    return HourPackage.objects.create(
        nationality=Nationality.COL,
        name_es='Paquete Pro',
        name_en='Pro Pack',
        hours=60,
        hourly_rate=Decimal('32000.00'),
        discount_percent=20,
        order=99,
        is_active=True,
    )


@pytest.fixture
def agreement_template():
    return FinancingAgreementTemplate.objects.create(
        name='Otrosí API',
        version=1,
        is_default=True,
        content_markdown=(
            '# OTROSÍ {agreement_number}\n\n{client_full_name} '
            '{client_id_type} {client_id_number} {contractor_full_name} '
            '{contractor_id_type} {contractor_id_number} '
            '{original_contract_reference} {original_contract_date} '
            '{project_name} {financed_scope} {financed_balance}\n\n'
            '{installment_schedule}\n\n{hosting_value} {modality_label} '
            '{modality_terms} {partnership_end_date}'
        ),
    )


@pytest.fixture
def financing_client(make_client_profile):
    return make_client_profile(
        company='Semilla SAS',
        nit='901234567-8',
        email='ana@semilla.co',
        first_name='Ana',
        last_name='Semilla',
    )


def _payload(client, **overrides):
    payload = {
        'client_id': client.id,
        'original_contract_reference': 'Contrato de desarrollo 014',
        'original_contract_date': '2026-01-10',
        'project_name': 'Vástago',
        'financed_scope': 'Implementación de la fase de analítica.',
        'modality': 'five_year',
        'partnership_start_date': '2026-02-01',
        'currency': 'COP',
        'total_value': '12000000.00',
        'initial_payment': '0.00',
        'hosting_value': '500000.00',
        'hosting_period': 'monthly',
        'first_installment_date': '2026-03-05',
    }
    payload.update(overrides)
    return payload


def test_admin_creates_populated_agreement_with_twelve_installments(
    admin_client,
    financing_client,
    agreement_template,
):
    """Fails if an admin-created draft loses its legal client or payment data."""
    response = admin_client.post(
        '/api/financing/agreements/',
        _payload(financing_client),
        format='json',
    )

    assert response.status_code == 201
    assert response.data['client_full_name'] == 'Ana Semilla'
    assert response.data['client_id_number'] == '901234567-8'
    assert len(response.data['installment_schedule']) == 12
    assert response.data['financed_balance'] == '12000000.00'


def test_draft_pdf_contains_populated_legal_identity(
    admin_client,
    financing_client,
    agreement_template,
    company_settings,
):
    """Fails if the admin draft PDF omits the selected client's legal identity."""
    created = admin_client.post(
        '/api/financing/agreements/',
        _payload(financing_client),
        format='json',
    )

    response = admin_client.get(
        f'/api/financing/agreements/{created.data["id"]}/draft-pdf/',
    )
    text = '\n'.join(
        page.extract_text() or ''
        for page in PdfReader(BytesIO(response.content)).pages
    )

    assert response.status_code == 200
    assert 'Ana Semilla' in text
    assert 'BORRADOR' in text
    assert 'XXX-XXX-XXX' not in text


def test_ready_rejects_schedule_outside_first_five_days(
    admin_client,
    financing_client,
    agreement_template,
    company_settings,
):
    """Fails if an admin can mark ready a schedule with a late due date."""
    created = admin_client.post(
        '/api/financing/agreements/',
        _payload(financing_client),
        format='json',
    )
    schedule = created.data['installment_schedule']
    schedule[0]['due_date'] = '2026-03-06'
    patched = admin_client.patch(
        f'/api/financing/agreements/{created.data["id"]}/',
        {'installment_schedule': schedule},
        format='json',
    )

    assert patched.status_code == 400
    assert 'installment_schedule' in patched.data


def test_completed_five_year_agreement_allows_second_cycle(
    admin_client,
    financing_client,
    agreement_template,
    company_settings,
    tmp_path,
    monkeypatch,
):
    """Fails if the admin lifecycle cannot create an approved second five-year cycle."""
    field = FinancingAgreement._meta.get_field('signed_document')
    monkeypatch.setattr(
        field,
        'storage',
        FileSystemStorage(location=tmp_path, base_url=None),
    )
    created = admin_client.post(
        '/api/financing/agreements/',
        _payload(financing_client),
        format='json',
    )
    agreement_id = created.data['id']
    ready = admin_client.post(
        f'/api/financing/agreements/{agreement_id}/mark-ready/',
        {},
        format='json',
    )
    upload = BytesIO(b'%PDF-1.4\n%%EOF')
    upload.name = 'firmado.pdf'
    active = admin_client.post(
        f'/api/financing/agreements/{agreement_id}/upload-signed/',
        {'signed_document': upload},
        format='multipart',
    )
    completed = admin_client.post(
        f'/api/financing/agreements/{agreement_id}/complete/',
        {'completion_note': 'Pago íntegro verificado contra soportes.'},
        format='json',
    )
    second = admin_client.post(
        f'/api/financing/agreements/{agreement_id}/create-second-cycle/',
        {},
        format='json',
    )

    assert ready.status_code == 200
    assert active.data['status'] == 'active'
    assert completed.data['status'] == 'completed'
    assert second.status_code == 201
    assert second.data['cycle_number'] == 2
    assert second.data['previous_agreement'] == agreement_id
    assert second.data['total_value'] == '0.00'


def test_non_admin_cannot_list_financing_agreements(
    financing_client,
    agreement_template,
):
    """Fails if the administrative agreement list becomes publicly accessible."""
    response = APIClient().get('/api/financing/agreements/')

    assert response.status_code in (401, 403)
