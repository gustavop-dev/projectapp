"""Regression tests for private Markdown and download proposal exports."""
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.urls import reverse
from pypdf import PdfWriter
from reportlab.pdfgen.canvas import Canvas

from content.models import ContractTemplate, ProposalDocument
from content.views.proposal import _generate_and_save_contract_pdf

pytestmark = pytest.mark.django_db


def _pdf_with_text(text):
    output = BytesIO()
    canvas = Canvas(output)
    canvas.drawString(72, 720, text)
    canvas.save()
    return output.getvalue()


def _blank_pdf():
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(output)
    return output.getvalue()


def _document(proposal, *, name, content, document_type='legal_annex', markdown=''):
    document = ProposalDocument.objects.create(
        proposal=proposal,
        document_type=document_type,
        title='Documento acordado',
        is_generated=document_type == ProposalDocument.DOC_TYPE_CONTRACT,
        content_markdown=markdown,
    )
    document.file.save(name, ContentFile(content), save=True)
    return document


@pytest.mark.parametrize(
    ('source', 'source_markdown', 'expected_clause'),
    [
        ('default', 'CLAUSULA DEFAULT {client_full_name}', 'CLAUSULA DEFAULT Cliente acordado'),
        ('custom', '# Contrato personalizado\n\nCLAUSULA CUSTOM ACORDADA', 'CLAUSULA CUSTOM ACORDADA'),
    ],
)
def test_contract_markdown_keeps_snapshot_written_during_generation(
    admin_client, company_settings, negotiating_proposal, source, source_markdown, expected_clause,
):
    """Fails if issuing a contract stops saving its agreed Markdown before later copies are requested."""
    ContractTemplate.objects.create(name='Versión original', content_markdown=source_markdown, is_default=True)
    negotiating_proposal.contract_params = {
        'contract_source': source,
        'custom_contract_markdown': source_markdown if source == 'custom' else '',
        'client_full_name': 'Cliente acordado',
        'client_cedula': '123456789',
        'contractor_full_name': 'Proveedor acordado',
        'contractor_nit': '900123456',
    }
    negotiating_proposal.save(update_fields=['contract_params'])
    _generate_and_save_contract_pdf(negotiating_proposal)
    ContractTemplate.objects.filter(is_default=True).update(content_markdown='CLAUSULA POSTERIOR')

    response = admin_client.get(reverse('contract-markdown', kwargs={'proposal_id': negotiating_proposal.pk}))

    assert response.status_code == 200
    assert expected_clause in response.json()['markdown']
    assert 'CLAUSULA POSTERIOR' not in response.json()['markdown']
    assert response['Cache-Control'] == 'private, no-store'
    saved = ProposalDocument.objects.get(proposal=negotiating_proposal, document_type='contract')
    assert saved.content_markdown.strip() == response.json()['markdown'].strip()


def test_contract_markdown_extracts_legacy_pdf_text_when_snapshot_is_absent(admin_client, negotiating_proposal):
    """Fails if a legacy contract without its snapshot cannot be copied from its saved PDF."""
    _document(
        negotiating_proposal,
        name='legacy-contract.pdf',
        content=_pdf_with_text('CLAUSULA LEGADA'),
        document_type=ProposalDocument.DOC_TYPE_CONTRACT,
    )

    response = admin_client.get(reverse('contract-markdown', kwargs={'proposal_id': negotiating_proposal.pk}))

    assert response.status_code == 200
    assert 'CLAUSULA LEGADA' in response.json()['markdown']
    assert response.json()['warnings'] == [
        'Texto extraído del PDF; el formato fue reconstruido. Las imágenes y firmas gráficas no se copian.',
    ]


def test_contract_markdown_rejects_legacy_pdf_without_extractable_text(admin_client, negotiating_proposal):
    """Fails if a blank or scanned legacy contract reports an empty copy as successful."""
    _document(
        negotiating_proposal,
        name='blank-contract.pdf',
        content=_blank_pdf(),
        document_type=ProposalDocument.DOC_TYPE_CONTRACT,
    )

    response = admin_client.get(reverse('contract-markdown', kwargs={'proposal_id': negotiating_proposal.pk}))

    assert response.status_code == 422
    assert response.json()['code'] == 'text_unavailable'


@pytest.mark.parametrize('url_name', ['proposal-attachment-download', 'proposal-attachment-markdown'])
def test_attachment_export_rejects_document_owned_by_another_proposal(
    admin_client, negotiating_proposal, accepted_proposal, url_name,
):
    """Fails if a proposal URL can download an attachment that belongs to another proposal."""
    foreign = _document(accepted_proposal, name='foreign.pdf', content=b'foreign bytes')
    url = reverse(url_name, kwargs={
        'proposal_id': negotiating_proposal.pk,
        'doc_id': foreign.pk,
    })

    response = admin_client.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize('url_name', ['proposal-attachment-download', 'proposal-attachment-markdown'])
def test_attachment_export_requires_an_administrator(api_client, negotiating_proposal, url_name):
    """Fails if unauthenticated callers can retrieve a proposal attachment."""
    document = _document(negotiating_proposal, name='private.pdf', content=_pdf_with_text('private text'))
    url = reverse(url_name, kwargs={
        'proposal_id': negotiating_proposal.pk,
        'doc_id': document.pk,
    })

    response = api_client.get(url)

    assert response.status_code == 401


def test_attachment_markdown_rejects_authenticated_nonstaff_user(api_client, negotiating_proposal):
    """Fails if a signed-in client account can copy a private proposal attachment."""
    user = get_user_model().objects.create_user(
        username='document_viewer', email='document-viewer@example.com', password='testpass123',
    )
    api_client.force_authenticate(user=user)
    document = _document(negotiating_proposal, name='staff-only.pdf', content=_pdf_with_text('staff-only text'))
    url = reverse('proposal-attachment-markdown', kwargs={
        'proposal_id': negotiating_proposal.pk,
        'doc_id': document.pk,
    })

    response = api_client.get(url)

    assert response.status_code == 403


def test_attachment_download_returns_original_bytes_with_safe_headers(admin_client, negotiating_proposal):
    """Fails if attachment download changes saved bytes or lets the browser render it inline."""
    document = _document(negotiating_proposal, name='anexo-final.pdf', content=b'original attachment bytes')
    url = reverse('proposal-attachment-download', kwargs={
        'proposal_id': negotiating_proposal.pk,
        'doc_id': document.pk,
    })

    response = admin_client.get(url)

    assert response.status_code == 200
    assert b''.join(response.streaming_content) == b'original attachment bytes'
    assert response['Content-Disposition'] == 'attachment; filename="anexo-final.pdf"'
    assert response['Cache-Control'] == 'private, no-store'
    assert response['X-Content-Type-Options'] == 'nosniff'
