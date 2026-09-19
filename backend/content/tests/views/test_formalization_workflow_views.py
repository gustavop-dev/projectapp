"""HTTP coverage for the formalization preparation and delivery workflow."""
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework.test import APIClient

from content.models import ProposalDocument, ProposalFormalization, ProposalSection


pytestmark = pytest.mark.django_db


@pytest.fixture
def formalization_payload():
    return {
        'documents': ['contract', 'commercial', 'technical'],
        'additional_doc_ids': [],
        'subject': 'Documentación para formalización de Acme',
        'greeting': 'Hola equipo Acme,',
        'body': 'Adjuntamos el paquete revisado para firma.',
        'footer': 'Equipo ProjectApp',
        'sections': [{'text': 'Por favor revisen los tres documentos.', 'markdown': False}],
        'recipient_emails': ['contact@acme.com'],
        'cc_emails': [],
    }


@pytest.fixture
def formalization_ready_proposal(proposal):
    sections = {
        'functional_requirements': {
            'groups': [{'id': 'orders', 'title': 'Pedidos', 'items': [{
                'id': 'create-order',
                'name': 'Crear pedido',
                'description': 'Registra una orden de un cliente.',
                'is_required': True,
            }]}],
        },
        'investment': {
            'paymentOptions': [{'label': '100% al entregar', 'description': ''}],
        },
        'technical_document': {
            'purpose': 'Gestionar pedidos de clientes.',
            'epics': [{'epicKey': 'ORD', 'title': 'Pedidos', 'requirements': [{
                'flowKey': 'ORD-01',
                'title': 'Crear pedido',
                'description': 'Registra una orden de un cliente.',
                'linked_item_ids': ['create-order'],
            }]}],
        },
    }
    for order, (section_type, content_json) in enumerate(sections.items()):
        ProposalSection.objects.create(
            proposal=proposal,
            section_type=section_type,
            title=section_type,
            order=order,
            content_json=content_json,
        )
    proposal.contract_params = {
        'contractor_full_name': 'ProjectApp S.A.S.',
        'contractor_email': 'legal@projectapp.co',
        'contract_city': 'Medellín',
        'bank_name': 'Banco de Prueba',
        'bank_account_number': '123456789',
        'contractor_nit': '900123456-7',
        'client_full_name': 'Acme Corp',
        'client_cedula': '1234567890',
        'client_email': 'contact@acme.com',
        'contract_date': '2026-09-19',
    }
    proposal.save(update_fields=['contract_params'])
    contract = ProposalDocument.objects.create(
        proposal=proposal,
        document_type=ProposalDocument.DOC_TYPE_CONTRACT,
        title='Contrato final',
        is_generated=True,
    )
    contract.file.save('contract.pdf', ContentFile(b'%PDF-1.4 final contract'), save=True)
    return proposal


def _prepare_url(proposal):
    return reverse('formalization-prepare', kwargs={'proposal_id': proposal.pk})


def _detail_url(proposal, preparation_id):
    return reverse('formalization-detail', kwargs={
        'proposal_id': proposal.pk,
        'preparation_id': preparation_id,
    })


def _send_url(proposal, preparation_id):
    return reverse('formalization-send', kwargs={
        'proposal_id': proposal.pk,
        'preparation_id': preparation_id,
    })


def _anonymous_client():
    return APIClient()


def _member_client():
    member = get_user_model().objects.create_user(
        username='formalization_member',
        email='member@example.com',
        password='testpass123',
    )
    client = APIClient()
    client.force_authenticate(user=member)
    return client


def _prepare_request(client, proposal, payload):
    return client.post(_prepare_url(proposal), payload, format='json')


def _send_request(client, proposal, _payload):
    return client.post(_send_url(proposal, uuid.uuid4()), format='json')


@pytest.fixture
def prepared_formalization(admin_client, formalization_ready_proposal, formalization_payload):
    response = admin_client.post(
        _prepare_url(formalization_ready_proposal), formalization_payload, format='json',
    )
    assert response.status_code == 201
    return formalization_ready_proposal, response.json()


def test_prepare_creates_three_private_files(
    admin_client, formalization_ready_proposal, formalization_payload,
):
    """Fails if the endpoint cannot create the complete formal review package."""
    response = admin_client.post(
        _prepare_url(formalization_ready_proposal), formalization_payload, format='json',
    )

    payload = response.json()

    assert response.status_code == 201
    assert response['Cache-Control'] == 'private, no-store'
    assert payload['subject'] == 'Documentación para formalización de Acme'
    assert payload['recipient_emails'] == ['contact@acme.com']
    assert [item['key'] for item in payload['files']] == ['contract', 'commercial', 'technical']
    assert ProposalFormalization.objects.filter(pk=payload['id']).count() == 1


def test_detail_returns_the_prepared_payload(admin_client, prepared_formalization):
    """Fails if review loses a prepared recipient, preview, or file identity."""
    proposal, prepared = prepared_formalization

    response = admin_client.get(_detail_url(proposal, prepared['id']))

    payload = response.json()
    root = f'/api/proposals/{proposal.pk}/formalization/preparations/{prepared["id"]}/'
    assert response.status_code == 200
    assert payload['id'] == prepared['id']
    assert payload['subject'] == 'Documentación para formalización de Acme'
    assert payload['recipient_emails'] == ['contact@acme.com']
    assert payload['html_preview'] == prepared['html_preview']
    assert [item['url'] for item in payload['files']] == [
        f'{root}files/{item["url"].split("/")[-2]}/' for item in prepared['files']
    ]


def test_send_delivers_one_prepared_package(admin_client, mailoutbox, prepared_formalization):
    """Fails if the send endpoint permits a second legal-document delivery."""
    proposal, prepared = prepared_formalization
    send_url = _send_url(proposal, prepared['id'])

    first_response = admin_client.post(send_url, format='json')
    repeat_response = admin_client.post(send_url, format='json')

    assert first_response.status_code == 200
    assert first_response.json()['status'] == 'sent'
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ['contact@acme.com']
    assert repeat_response.status_code == 409
    assert repeat_response.json()['code'] == 'preparation_consumed'


@pytest.mark.parametrize('kind', ['commercial', 'technical', 'contract'])
def test_pdf_download_returns_private_pdf(admin_client, formalization_ready_proposal, kind):
    """Fails if a curated formal PDF endpoint returns a cacheable or unusable document."""
    response = admin_client.get(reverse('formalization-pdf', kwargs={
        'proposal_id': formalization_ready_proposal.pk,
        'kind': kind,
    }))

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response['Content-Disposition'].startswith('attachment; filename=')
    assert response['Cache-Control'] == 'private, no-store'
    assert response.content.startswith(b'%PDF-')


@pytest.mark.parametrize(
    ('client_factory', 'request_builder', 'expected_status'),
    [
        (_anonymous_client, _prepare_request, 401),
        (_anonymous_client, _send_request, 401),
        (_member_client, _prepare_request, 403),
        (_member_client, _send_request, 403),
    ],
)
def test_permission_denies_nonstaff_formalization_requests(
    client_factory, request_builder, expected_status, formalization_ready_proposal, formalization_payload, mailoutbox,
):
    """Fails if a non-admin can prepare or dispatch a client formalization."""
    response = request_builder(
        client_factory(), formalization_ready_proposal, formalization_payload,
    )

    assert response.status_code == expected_status
    assert ProposalFormalization.objects.count() == 0
    assert len(mailoutbox) == 0


def test_send_returns_stale_source_error(admin_client, mailoutbox, prepared_formalization):
    """Fails if the endpoint delivers documents after the proposal title changes."""
    proposal, prepared = prepared_formalization
    proposal.title = 'Alcance revisado después de preparar'
    proposal.save(update_fields=['title'])

    response = admin_client.post(_send_url(proposal, prepared['id']), format='json')

    assert response.status_code == 409
    assert response.json()['code'] == 'stale_preparation'
    assert len(mailoutbox) == 0
