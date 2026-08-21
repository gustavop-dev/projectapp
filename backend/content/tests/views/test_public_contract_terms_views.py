from unittest.mock import patch

import pytest
from django.urls import reverse

from content.models import ContractTemplate

pytestmark = pytest.mark.django_db


def create_contract_template():
    return ContractTemplate.objects.create(
        name='Contrato global',
        content_markdown=(
            'Entre {client_full_name} y {contractor_full_name}.\n\n'
            '## CLÁUSULA PRIMERA — OBJETO\n\nObjeto del servicio.\n\n'
            '## CLÁUSULA SEGUNDA — PAGOS\n\nCuenta {bank_account_number}.'
        ),
        is_default=True,
    )


def preview_url(proposal):
    return reverse(
        'retrieve-public-contract-terms',
        kwargs={'proposal_uuid': proposal.uuid},
    )


def download_url(proposal):
    return reverse(
        'download-public-draft-contract-pdf',
        kwargs={'proposal_uuid': proposal.uuid},
    )


def test_preview_returns_linkable_masked_clauses(api_client, proposal):
    create_contract_template()
    proposal.contract_params = {
        'contract_source': 'custom',
        'custom_contract_markdown': 'SECRETO PERSONALIZADO',
        'client_full_name': 'Nombre Real',
    }
    proposal.save(update_fields=['contract_params'])

    response = api_client.get(preview_url(proposal))

    assert response.status_code == 200
    assert response.data['clauses'][0]['id'] == 'clause-01'
    assert 'XXX-XXX-XXX' in str(response.data)
    assert 'SECRETO PERSONALIZADO' not in str(response.data)
    assert 'Nombre Real' not in str(response.data)


def test_preview_returns_not_found_when_module_is_hidden(api_client, proposal):
    proposal.show_contract_terms = False
    proposal.save(update_fields=['show_contract_terms'])

    response = api_client.get(preview_url(proposal))

    assert response.status_code == 404


def test_preview_returns_not_found_for_english_proposal(api_client, proposal):
    proposal.language = 'en'
    proposal.save(update_fields=['language'])

    response = api_client.get(preview_url(proposal))

    assert response.status_code == 404


def test_preview_returns_not_found_for_inactive_proposal(api_client, proposal):
    proposal.is_active = False
    proposal.save(update_fields=['is_active'])

    response = api_client.get(preview_url(proposal))

    assert response.status_code == 404


def test_preview_returns_service_unavailable_without_default_template(
    api_client,
    proposal,
):
    ContractTemplate.objects.all().update(is_default=False)

    response = api_client.get(preview_url(proposal))

    assert response.status_code == 503


@patch('content.services.pdf_utils.add_watermark_to_pdf', return_value=b'watermarked')
@patch('content.services.contract_pdf_service.generate_contract_pdf', return_value=b'draft')
def test_download_uses_masked_global_draft(
    generate_pdf,
    add_watermark,
    api_client,
    proposal,
):
    create_contract_template()
    proposal.contract_params = {
        'contract_source': 'custom',
        'custom_contract_markdown': 'CUSTOM',
    }
    proposal.save(update_fields=['contract_params'])

    response = api_client.get(download_url(proposal))

    assert response.status_code == 200
    assert response.content == b'watermarked'
    generate_pdf.assert_called_once_with(
        proposal,
        draft=True,
        force_default=True,
    )
    add_watermark.assert_called_once_with(b'draft')


def test_download_returns_not_found_when_module_is_hidden(api_client, proposal):
    proposal.show_contract_terms = False
    proposal.save(update_fields=['show_contract_terms'])

    response = api_client.get(download_url(proposal))

    assert response.status_code == 404


def test_download_returns_service_unavailable_without_default_template(
    api_client,
    proposal,
):
    ContractTemplate.objects.all().update(is_default=False)

    response = api_client.get(download_url(proposal))

    assert response.status_code == 503
