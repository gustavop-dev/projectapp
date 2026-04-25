import copy
import importlib
from types import SimpleNamespace

import pytest
from django.apps import apps

from content.models import ProposalSection


pytestmark = pytest.mark.django_db

migration_module = importlib.import_module(
    'content.migrations.0085_canonicalize_technical_document_linked_module_ids',
)


def _schema_editor():
    return SimpleNamespace(connection=SimpleNamespace(alias='default'))


def test_migration_canonicalizes_legacy_ids_and_removes_camel_case(proposal):  # quality: disable test_too_long (migration test must verify full before/after state across all legacy ID variants)
    ProposalSection.objects.create(
        proposal=proposal,
        section_type='functional_requirements',
        title='Requirements',
        order=0,
        is_enabled=True,
        content_json={
            'groups': [
                {'id': 'views', 'title': 'Vistas', 'items': [{'name': 'Home'}]},
            ],
            'additionalModules': [
                {'id': 'pwa_module', 'title': 'PWA', 'is_calculator_module': True, 'price_percent': 40},
            ],
        },
    )
    ProposalSection.objects.create(
        proposal=proposal,
        section_type='investment',
        title='Investment',
        order=1,
        is_enabled=True,
        content_json={
            'modules': [
                {'id': 'priority-support', 'title': 'Priority Support'},
            ],
        },
    )
    technical_section = ProposalSection.objects.create(
        proposal=proposal,
        section_type='technical_document',
        title='Technical',
        order=2,
        is_enabled=True,
        content_json={
            'purpose': 'Doc',
            'epics': [
                {
                    'title': 'Mobile',
                    'linkedModuleIds': ['views'],
                    'requirements': [
                        {'title': 'Installable', 'linkedModuleIds': ['pwa_module']},
                        {'title': 'Support', 'linkedModuleIds': ['priority-support']},
                    ],
                },
            ],
        },
    )

    migration_module.forwards(apps, _schema_editor())

    technical_section.refresh_from_db()
    epic = technical_section.content_json['epics'][0]

    assert epic['linked_module_ids'] == ['group-views']
    assert 'linkedModuleIds' not in epic
    assert epic['requirements'][0]['linked_module_ids'] == ['module-pwa_module']
    assert 'linkedModuleIds' not in epic['requirements'][0]
    assert epic['requirements'][1]['linked_module_ids'] == ['priority-support']


def test_migration_is_idempotent_for_already_canonical_content(proposal):
    ProposalSection.objects.create(
        proposal=proposal,
        section_type='functional_requirements',
        title='Requirements',
        order=0,
        is_enabled=True,
        content_json={
            'groups': [
                {'id': 'views', 'title': 'Vistas', 'items': [{'name': 'Home'}]},
            ],
        },
    )
    technical_section = ProposalSection.objects.create(
        proposal=proposal,
        section_type='technical_document',
        title='Technical',
        order=1,
        is_enabled=True,
        content_json={
            'purpose': 'Doc',
            'epics': [
                {
                    'title': 'Mobile',
                    'linked_module_ids': ['group-views'],
                    'requirements': [
                        {'title': 'Home', 'linked_module_ids': ['group-views']},
                    ],
                },
            ],
        },
    )

    migration_module.forwards(apps, _schema_editor())
    technical_section.refresh_from_db()
    first_pass = copy.deepcopy(technical_section.content_json)

    migration_module.forwards(apps, _schema_editor())
    technical_section.refresh_from_db()

    assert technical_section.content_json == first_pass
