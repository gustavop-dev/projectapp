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
def test_technical_pdf_excludes_future_scope(formal_proposal):
    raw = generate_formal_pdf(FormalContent(formal_proposal), 'technical', timezone.now(), 'PROP-TEST')
    rendered = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(raw)).pages)
    assert 'OP-01' in rendered
    assert 'Índices' in rendered
    assert 'FUTURE_SENTINEL' not in rendered
