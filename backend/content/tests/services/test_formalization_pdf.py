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


@pytest.fixture
def module_terms_proposal(formal_proposal):
    requirements = formal_proposal.sections.get(section_type='functional_requirements')
    requirements.content_json['groups'].extend([
        {
            'id': 'priority-support',
            'title': 'Soporte prioritario',
            'is_calculator_module': True,
            'selected': True,
            'price_percent': 10,
            'items': [{'id': 'priority-channel', 'name': 'Canal prioritario', 'description': 'Soporte incluido.'}],
        },
        {
            'id': 'catalog-support',
            'title': 'Soporte de catálogo',
            'is_calculator_module': True,
            'selected': False,
            'price_percent': 5,
            'items': [{'id': 'catalog-channel', 'name': 'Canal catálogo', 'description': 'No seleccionado.'}],
        },
        {
            'id': 'threshold-support',
            'title': 'Soporte condicionado',
            'is_calculator_module': True,
            'selected': True,
            'price_percent': 1,
            'items': [{'id': 'threshold-channel', 'name': 'Canal condicionado', 'description': 'Umbral no alcanzado.'}],
        },
    ])
    requirements.save(update_fields=['content_json'])
    ProposalSection.objects.create(
        proposal=formal_proposal,
        section_type='value_added_modules',
        title='Módulos incluidos',
        order=10,
        content_json={
            'module_ids': ['priority-support', 'catalog-support', 'threshold-support'],
            'conditions': {
                'priority-support': {
                    'min_price_cop': 10000,
                    'duration_months': 12,
                    'discretionary_note': 'NOTA_DISCRECIONAL_ELEGIBLE',
                    'terms_clauses': [{'label': 'Cobertura', 'text': 'CLÁUSULA_ELEGIBLE'}],
                },
                'catalog-support': {
                    'min_price_cop': 0,
                    'terms_clauses': [{'label': 'Cobertura', 'text': 'TERMINO_NO_SELECCIONADO'}],
                },
                'threshold-support': {
                    'min_price_cop': 20000,
                    'terms_clauses': [{'label': 'Cobertura', 'text': 'TERMINO_BAJO_UMBRAL'}],
                },
            },
        },
    )
    return formal_proposal


@freeze_time('2026-09-19 12:00:00')
def test_commercial_pdf_includes_only_earned_module_terms(module_terms_proposal):
    """Fails if eligible module terms disappear or ineligible catalog terms become contractual obligations."""
    formal_proposal = module_terms_proposal

    raw = generate_formal_pdf(FormalContent(formal_proposal), 'commercial', timezone.now(), 'PROP-TEST')
    rendered = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(raw)).pages)

    assert 'CLÁUSULA_ELEGIBLE' in rendered
    assert 'Meses de vigencia: 12' in rendered
    assert 'NOTA_DISCRECIONAL_ELEGIBLE' in rendered
    assert 'TERMINO_NO_SELECCIONADO' not in rendered
    assert 'TERMINO_BAJO_UMBRAL' not in rendered


@freeze_time('2026-09-19 12:00:00')
def test_commercial_pdf_preserves_saved_hosting_options(formal_proposal):
    """Fails if the formal annex changes saved hosting prices or presents one option as selected."""
    formal_proposal.hosting_percent = 24
    formal_proposal.save(update_fields=['hosting_percent'])
    investment = formal_proposal.sections.get(section_type='investment')
    investment.content_json['hostingPlan'] = {
        'title': 'Hosting administrado',
        'freeMonths': 2,
        'freeMonthsVisible': True,
        'billingTiers': [
            {'label': 'Mensual', 'months': 1, 'discountPercent': 0},
            {'label': 'Trimestral', 'months': 3, 'discountPercent': 10},
        ],
    }
    investment.save(update_fields=['content_json'])

    raw = generate_formal_pdf(FormalContent(formal_proposal), 'commercial', timezone.now(), 'PROP-TEST')
    rendered = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(raw)).pages)

    assert '300,00 COP' in rendered
    assert '810,00 COP' in rendered
    assert 'Meses incluidos sin costo: 2' in rendered
    assert 'Modalidades disponibles; esta tabla no registra una elección de periodicidad.' in rendered


@freeze_time('2026-09-19 12:00:00')
def test_technical_pdf_excludes_future_scope(formal_proposal):
    raw = generate_formal_pdf(FormalContent(formal_proposal), 'technical', timezone.now(), 'PROP-TEST')
    rendered = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(raw)).pages)
    assert 'OP-01' in rendered
    assert 'Índices' in rendered
    assert 'FUTURE_SENTINEL' not in rendered
