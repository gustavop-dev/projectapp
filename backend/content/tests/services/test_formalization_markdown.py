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
