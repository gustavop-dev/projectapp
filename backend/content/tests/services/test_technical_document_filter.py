"""Tests for content.services.technical_document_filter."""
import pytest

from content.services.technical_document_filter import (
    filter_technical_document_by_module_selection,
)

pytestmark = pytest.mark.django_db


def test_keeps_base_group_epic_when_selection_is_empty_but_group_is_always_included():
    doc = {
        'epics': [
            {
                'title': 'Base scope',
                'linked_module_ids': ['group-views'],
                'requirements': [
                    {'title': 'Home', 'linked_module_ids': ['group-views']},
                ],
            },
        ],
    }

    out = filter_technical_document_by_module_selection(
        doc,
        [],
        always_included_ids=['group-views'],
    )

    assert len(out['epics']) == 1
    assert len(out['epics'][0]['requirements']) == 1


def test_drops_optional_epic_when_selection_is_explicitly_empty():
    doc = {
        'epics': [
            {
                'title': 'Optional scope',
                'linked_module_ids': ['module-pwa_module'],
                'requirements': [
                    {'title': 'PWA shell', 'linked_module_ids': ['module-pwa_module']},
                ],
            },
        ],
    }

    out = filter_technical_document_by_module_selection(
        doc,
        [],
        always_included_ids=['group-views'],
    )

    assert out['epics'] == []


def test_normalizes_string_linked_module_ids():
    doc = {
        'epics': [
            {
                'title': 'String links',
                'requirements': [
                    {'title': 'Pagos', 'linked_module_ids': 'module-payments'},
                ],
            },
        ],
    }
    out = filter_technical_document_by_module_selection(doc, ['module-payments'])
    assert len(out['epics'][0]['requirements']) == 1


def test_treats_non_list_non_string_links_as_unlinked():
    doc = {
        'epics': [
            {
                'title': 'Raro',
                'requirements': [{'title': 'Base', 'linked_module_ids': 42}],
            },
        ],
    }
    out = filter_technical_document_by_module_selection(doc, [])
    assert len(out['epics'][0]['requirements']) == 1


def test_requirement_visible_without_selection_filter():
    doc = {
        'epics': [
            {
                'title': 'Legacy',
                'requirements': [
                    {'title': 'Linked', 'linked_module_ids': ['module-x']},
                ],
            },
        ],
    }
    out = filter_technical_document_by_module_selection(doc, None)
    assert len(out['epics'][0]['requirements']) == 1


def test_always_included_requirement_survives_unselected_module():
    doc = {
        'epics': [
            {
                'title': 'Mixto',
                'requirements': [
                    {'title': 'Incluida', 'linkedModuleIds': ['group-base']},
                    {'title': 'Opcional', 'linked_module_ids': ['module-extra']},
                ],
            },
        ],
    }
    out = filter_technical_document_by_module_selection(
        doc, [], always_included_ids=['group-base'],
    )
    titles = [r['title'] for r in out['epics'][0]['requirements']]
    assert titles == ['Incluida']


def test_epic_with_epic_key_header_survives_without_requirements():
    doc = {
        'epics': [
            {
                'epicKey': 'EP-9',
                'requirements': [
                    {'title': 'Opcional', 'linked_module_ids': ['module-extra']},
                ],
            },
        ],
    }
    out = filter_technical_document_by_module_selection(doc, [])
    assert len(out['epics']) == 1
    assert out['epics'][0]['requirements'] == []


def test_non_dict_content_returns_empty_document():
    assert filter_technical_document_by_module_selection(None, []) == {}
    assert filter_technical_document_by_module_selection(['x'], []) == {}


def test_non_dict_epics_are_skipped():
    doc = {'epics': ['texto suelto', {'title': 'Real', 'requirements': []}]}
    out = filter_technical_document_by_module_selection(doc, [])
    assert len(out['epics']) == 1
    assert out['epics'][0]['title'] == 'Real'


def test_non_list_requirements_treated_as_empty_with_meaningful_header():
    doc = {'epics': [{'title': 'Con header', 'requirements': 'no-es-lista'}]}
    out = filter_technical_document_by_module_selection(doc, [])
    assert out['epics'][0]['requirements'] == []
