"""Behavioral smoke tests for curated annex generation."""
from io import BytesIO

import pytest
from django.utils import timezone
from freezegun import freeze_time
from pypdf import PdfReader

from content.models import ProposalSection
from content.services.formalization_content import FormalContent
from content.services.formalization_pdf import generate_formal_pdf

pytestmark = pytest.mark.django_db


@pytest.fixture
def formal_proposal(proposal):
    sections = {
        'functional_requirements': {'groups': [{'id': 'core', 'title': 'Operación', 'items': [{'id': 'orders', 'name': 'Pedidos', 'description': 'Registrar pedidos.'}]}]},
        'investment': {'paymentOptions': [{'label': '100% al entregar', 'description': ''}], 'valueReasons': ['SALES_SENTINEL']},
        'technical_document': {'purpose': 'Gestionar pedidos', 'epics': [{'epicKey': 'OP', 'title': 'Operación', 'requirements': [{'flowKey': 'OP-01', 'title': 'Crear pedido', 'description': 'Conservar fecha.', 'linked_item_ids': ['orders']}]}], 'growthReadiness': {'strategies': [{'dimension': 'Carga', 'preparation': 'Índices', 'evolution': 'FUTURE_SENTINEL'}]}},
        'roi_projection': {'subtitle': 'ROI_SENTINEL'},
    }
    for order, (key, data) in enumerate(sections.items()):
        ProposalSection.objects.create(proposal=proposal, section_type=key, title=key, order=order, content_json=data)
    return proposal


@freeze_time('2026-09-19 12:00:00')
def test_commercial_pdf_excludes_sales_copy(formal_proposal):
    raw = generate_formal_pdf(FormalContent(formal_proposal), 'commercial', timezone.now(), 'PROP-TEST')
    rendered = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(raw)).pages)
    assert 'Pedidos' in rendered
    assert '15.000,00 COP' in rendered
    assert 'SALES_SENTINEL' not in rendered
    assert 'ROI_SENTINEL' not in rendered


@freeze_time('2026-09-19 12:00:00')
def test_commercial_pdf_excludes_unselected_priceable_requirement(formal_proposal):
    """Fails if a declined priced requirement or its amount enters the formal annex."""
    requirements = formal_proposal.sections.get(section_type='functional_requirements')
    requirements.content_json['groups'][0]['items'].append({
        'id': 'campaigns',
        'name': 'Módulo comercial opcional',
        'description': 'OPTIONAL_SALES_SCOPE',
        'price': '5000',
        'is_required': False,
    })
    requirements.save(update_fields=['content_json'])

    raw = generate_formal_pdf(FormalContent(formal_proposal), 'commercial', timezone.now(), 'PROP-TEST')
    rendered = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(raw)).pages)

    assert 'OPTIONAL_SALES_SCOPE' not in rendered
    assert 'Módulo comercial opcional' not in rendered
    assert '10.000,00 COP' in rendered


@freeze_time('2026-09-19 12:00:00')
def test_curated_pdfs_preserve_legacy_requirement_traceability(formal_proposal):
    """Fails if legacy requirement references diverge between the commercial and technical annexes."""
    requirements = formal_proposal.sections.get(section_type='functional_requirements')
    del requirements.content_json['groups'][0]['items'][0]['id']
    requirements.save(update_fields=['content_json'])
    technical = formal_proposal.sections.get(section_type='technical_document')
    technical.content_json['epics'][0]['requirements'][0]['linked_item_ids'] = ['item-core-pedidos']
    technical.save(update_fields=['content_json'])

    commercial = generate_formal_pdf(FormalContent(formal_proposal), 'commercial', timezone.now(), 'PROP-TEST')
    technical = generate_formal_pdf(FormalContent(formal_proposal), 'technical', timezone.now(), 'PROP-TEST')
    commercial_text = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(commercial)).pages)
    technical_text = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(technical)).pages)

    assert 'item-core-pedidos' in commercial_text
    assert 'item-core-pedidos' in technical_text
    assert 'fr-core-pedidos' not in commercial_text
    assert 'fr-core-pedidos' not in technical_text


@freeze_time('2026-09-19 12:00:00')
def test_technical_pdf_excludes_future_scope(formal_proposal):
    raw = generate_formal_pdf(FormalContent(formal_proposal), 'technical', timezone.now(), 'PROP-TEST')
    rendered = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(raw)).pages)
    assert 'OP-01' in rendered
    assert 'Índices' in rendered
    assert 'FUTURE_SENTINEL' not in rendered
