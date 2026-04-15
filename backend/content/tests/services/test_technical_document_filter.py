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
