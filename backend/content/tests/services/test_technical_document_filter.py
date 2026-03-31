"""Tests for technical_document module filtering."""

import copy

import pytest

from content.services.technical_document_filter import (
    filter_technical_document_by_module_selection,
)


@pytest.fixture
def sample_doc():
    return {
        'purpose': 'Core purpose',
        'epics': [
            {
                'epicKey': 'core',
                'title': 'Core epic',
                'requirements': [
                    {'title': 'Base req', 'description': 'Always on'},
                    {
                        'title': 'Addon A',
                        'linked_module_ids': ['module-5'],
                    },
                ],
            },
            {
                'epicKey': 'gated',
                'title': 'Gated epic',
                'linked_module_ids': ['group-9'],
                'requirements': [
                    {'title': 'Inner', 'description': 'x'},
                ],
            },
        ],
    }


def test_no_filter_when_selected_none(sample_doc):
    """None selected_module_ids leaves epics unchanged."""
    original = copy.deepcopy(sample_doc)
    out = filter_technical_document_by_module_selection(sample_doc, None)
    assert out['epics'] == original['epics']


def test_empty_selection_drops_linked_requirements(sample_doc):
    """Empty list hides requirements with linked_module_ids."""
    out = filter_technical_document_by_module_selection(sample_doc, [])
    core = next(e for e in out['epics'] if e.get('epicKey') == 'core')
    titles = [r['title'] for r in core['requirements']]
    assert 'Base req' in titles
    assert 'Addon A' not in titles


def test_selection_includes_linked_requirement(sample_doc):
    """module-5 selected keeps Addon A."""
    out = filter_technical_document_by_module_selection(sample_doc, ['module-5'])
    core = next(e for e in out['epics'] if e.get('epicKey') == 'core')
    titles = [r['title'] for r in core['requirements']]
    assert 'Base req' in titles
    assert 'Addon A' in titles


def test_epic_level_gate_excludes_entire_epic(sample_doc):
    """Epic with linked_module_ids not in selection is removed."""
    out = filter_technical_document_by_module_selection(sample_doc, ['module-5'])
    keys = [e.get('epicKey') for e in out['epics']]
    assert 'gated' not in keys


def test_epic_level_gate_allows_when_selected(sample_doc):
    """Epic with linked group id visible when group selected."""
    out = filter_technical_document_by_module_selection(sample_doc, ['group-9'])
    keys = [e.get('epicKey') for e in out['epics']]
    assert 'gated' in keys
