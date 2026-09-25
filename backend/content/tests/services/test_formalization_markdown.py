"""Behavioral tests for Markdown exports of curated formal annexes."""
from datetime import datetime, timezone

import pytest

from content.models import ProposalSection
from content.services.formalization_content import FormalContent, FormalizationError
from content.services.formalization_markdown import generate_formal_markdown

pytestmark = pytest.mark.django_db


@pytest.fixture
def formal_markdown_proposal(proposal):
    proposal.language = 'en'
    proposal.save(update_fields=['language'])
    sections = {
        'functional_requirements': {
            'groups': [{
                'id': 'operations',
                'title': 'Operations',
                'items': [
                    {'id': 'orders', 'name': 'Orders', 'description': 'Record orders.'},
                    {
                        'id': 'optional-sales', 'name': 'Optional sales module',
                        'description': 'UNSELECTED_SENTINEL', 'price': '5000', 'is_required': False,
                    },
                ],
            }],
        },
        'investment': {
            'paymentOptions': [{'label': '100% on delivery', 'description': ''}],
            'valueReasons': ['SALES_SENTINEL'],
        },
        'technical_document': {
            'purpose': 'Manage orders',
            'epics': [{
                'epicKey': 'OPS', 'title': 'Operations',
                'requirements': [{
                    'flowKey': 'OPS-01', 'title': 'Create order',
                    'description': 'Keep a date.', 'linked_item_ids': ['orders'],
                }],
            }],
            'growthReadiness': {
                'strategies': [{
                    'dimension': 'Load', 'preparation': 'Indexes', 'evolution': 'FUTURE_SENTINEL',
                }],
            },
        },
        'roi_projection': {'subtitle': 'ROI_SENTINEL'},
    }
    for order, (section_type, content_json) in enumerate(sections.items()):
        ProposalSection.objects.create(
            proposal=proposal,
            section_type=section_type,
            title=section_type,
            order=order,
            content_json=content_json,
        )
    return proposal


def _export(proposal, kind):
    return generate_formal_markdown(
        FormalContent(proposal), kind, datetime(2026, 9, 24, 12, 0, tzinfo=timezone.utc), 'PROP-12',
    )


def test_commercial_markdown_preserves_selected_english_scope(formal_markdown_proposal):
    """Fails if commercial Markdown includes declined sales scope or loses its English projection."""
    export = _export(formal_markdown_proposal, 'commercial')

    assert export['title'] == 'Formal commercial proposal'
    assert 'Orders' in export['markdown']
    assert 'orders' in export['markdown']
    assert 'Optional sales module' not in export['markdown']
    assert 'UNSELECTED_SENTINEL' not in export['markdown']
    assert 'SALES_SENTINEL' not in export['markdown']
    assert 'ROI_SENTINEL' not in export['markdown']


def test_technical_markdown_preserves_selected_requirement_identifiers(formal_markdown_proposal):
    """Fails if technical Markdown loses the selected requirement traceability used by the formal PDF."""
    export = _export(formal_markdown_proposal, 'technical')

    assert export['title'] == 'Formal technical specification'
    assert 'OPS-01' in export['markdown']
    assert 'orders' in export['markdown']
    assert 'FUTURE_SENTINEL' not in export['markdown']


def test_formal_markdown_rejects_unknown_document_kind(formal_markdown_proposal):
    """Fails if an unsupported formal Markdown URL produces arbitrary document content."""
    with pytest.raises(FormalizationError, match='Tipo de documento inválido') as error:
        _export(formal_markdown_proposal, 'unsupported')

    assert error.value.code == 'invalid_document'


def test_formal_markdown_rejects_unstructured_scope(formal_markdown_proposal):
    """Fails if pasted unstructured requirements enter a legally formalized Markdown annex."""
    requirements = formal_markdown_proposal.sections.get(section_type='functional_requirements')
    requirements.content_json = {'_editMode': 'paste', 'rawText': 'UNSTRUCTURED_SCOPE'}
    requirements.save(update_fields=['content_json'])

    with pytest.raises(FormalizationError) as error:
        _export(formal_markdown_proposal, 'commercial')

    assert error.value.code == 'unstructured_content'


def test_technical_markdown_rejects_missing_selected_scope(formal_markdown_proposal):
    """Fails if a technical export can omit every selected requirement and still look valid."""
    technical = formal_markdown_proposal.sections.get(section_type='technical_document')
    technical.content_json = {'purpose': 'Manage orders', 'epics': []}
    technical.save(update_fields=['content_json'])

    with pytest.raises(FormalizationError) as error:
        _export(formal_markdown_proposal, 'technical')

    assert error.value.code == 'technical_scope_missing'


@pytest.mark.parametrize(('section_type', 'data', 'expected'), [
    ('design_ux', {'focusItems': [{'description': 'Accessible screens'}]}, 'Accessible screens'),
    ('creative_support', {'includes': ['Editorial assistance']}, 'Editorial assistance'),
    ('timeline', {'phases': [{'title': 'Build', 'tasks': ['Review orders']}]}, 'Review orders'),
    ('process_methodology', {'steps': [{'title': 'Review', 'clientAction': 'Approve screens'}]}, 'Approve screens'),
    ('development_stages', {'stages': [{'title': 'Delivery', 'description': 'Publish release'}]}, 'Publish release'),
    ('commercial_conditions', {'scopeParagraphs': ['Changes require approval']}, 'Changes require approval'),
    ('value_added_modules', {
        'module_ids': ['operations'],
        'conditions': {'operations': {'terms_clauses': [{'label': 'Term', 'text': 'Includes onboarding'}]}},
    }, 'Includes onboarding'),
])
def test_commercial_markdown_preserves_curated_section_content(
    formal_markdown_proposal, section_type, data, expected,
):
    """Fails if the public PDF schema causes a saved commercial provision to disappear from Markdown."""
    ProposalSection.objects.create(
        proposal=formal_markdown_proposal, section_type=section_type,
        title='Saved provision', order=10, content_json={**data, 'subtitle': 'SalesOnlySentinel'},
    )

    rendered = _export(formal_markdown_proposal, 'commercial')['markdown']

    assert expected in rendered
    assert 'Saved provision' in rendered
    assert 'SalesOnlySentinel' not in rendered


def test_commercial_markdown_preserves_saved_section_order(formal_markdown_proposal):
    """Fails if Markdown uses a fixed scope-first order despite the order captured for the PDF."""
    scope = formal_markdown_proposal.sections.get(section_type='functional_requirements')
    scope.order = 10
    scope.title = 'Scope last'
    scope.save(update_fields=['order', 'title'])
    investment = formal_markdown_proposal.sections.get(section_type='investment')
    investment.order = 0
    investment.title = 'Investment first'
    investment.save(update_fields=['order', 'title'])

    rendered = _export(formal_markdown_proposal, 'commercial')['markdown']

    assert '## 01. Investment first' in rendered
    assert rendered.index('Investment first') < rendered.index('Scope last')


def test_commercial_markdown_preserves_resolved_fractional_payment(formal_markdown_proposal):
    """Fails if the Markdown adapter recalculates or rounds the resolved payment amount."""
    formal_markdown_proposal.currency = 'USD'
    formal_markdown_proposal.total_investment = '6000.25'
    formal_markdown_proposal.save(update_fields=['currency', 'total_investment'])
    investment = formal_markdown_proposal.sections.get(section_type='investment')
    investment.content_json['paymentOptions'] = [{'label': '12.5% upon kickoff', 'description': 'OldAmount'}]
    investment.save(update_fields=['content_json'])

    rendered = _export(formal_markdown_proposal, 'commercial')['markdown']

    assert '1,000.25 USD' in rendered
    assert '125.03 USD' in rendered
    assert 'OldAmount' not in rendered


def test_commercial_markdown_uses_saved_hosting_terms(formal_markdown_proposal):
    """Fails if an export reseeds the hosting catalog instead of retaining the accepted proposal terms."""
    investment = formal_markdown_proposal.sections.get(section_type='investment')
    investment.content_json['hostingPlan'] = {
        'title': 'Hosting', 'monthlyPrice': 'SavedPrice', 'renewalNote': 'Renewal on anniversary',
        'specs': [{'label': 'Storage', 'value': '20 GB'}],
    }
    investment.save(update_fields=['content_json'])

    rendered = _export(formal_markdown_proposal, 'commercial')['markdown']

    assert 'SavedPrice' in rendered
    assert 'Renewal on anniversary' in rendered
    assert '20 GB' in rendered
    assert 'SMMLV' not in rendered


@pytest.mark.parametrize(('field', 'data', 'expected'), [
    ('environments', [{
        'name': 'Staging', 'purpose': 'Validation', 'whoAccesses': 'QA team',
        'url': 'PrivateSentinel', 'database': 'PrivateSentinel', 'credentials': 'PrivateSentinel',
    }], 'QA team'),
    ('integrations', {'excluded': [{
        'service': 'External service', 'reason': 'Outside scope', 'availability': 'PrivateSentinel',
    }]}, 'Outside scope'),
    ('growthReadiness', {'strategies': [{
        'dimension': 'Load', 'preparation': 'Query indexes', 'evolution': 'PrivateSentinel',
    }]}, 'Query indexes'),
])
def test_technical_markdown_exports_only_allowed_projection_fields(
    formal_markdown_proposal, field, data, expected,
):
    """Fails if adapting the PDF projection leaks internal fields or removes the permitted detail."""
    technical = formal_markdown_proposal.sections.get(section_type='technical_document')
    technical.content_json[field] = data
    technical.save(update_fields=['content_json'])

    rendered = _export(formal_markdown_proposal, 'technical')['markdown']

    assert expected in rendered
    assert 'PrivateSentinel' not in rendered
