from copy import deepcopy
from importlib import import_module

import pytest
from django.apps import apps

from content.models import BusinessProposal, ProposalDefaultConfig, ProposalSection


pytestmark = pytest.mark.django_db
migration = import_module('content.migrations.0222_cross_cutting_features')


def functional_requirements(language='es', *, responsive_id='item-features-responsive'):
    responsive_name = 'Responsive Design' if language == 'en' else 'Diseño Responsive'
    return {
        'index': '9',
        'groups': [
            {'id': 'views', 'items': []},
            {
                'id': 'features',
                'items': [
                    {
                        'id': responsive_id,
                        'icon': '🌐',
                        'name': responsive_name,
                        'description': 'Context-specific responsive scope.',
                    },
                    {'id': 'item-features-search', 'name': 'Search'},
                ],
            },
            {'id': 'admin_module', 'items': []},
        ],
        'additionalModules': [],
    }


def make_proposal(status, *, language='es', is_active=True):
    proposal = BusinessProposal.objects.create(
        title=f'Proposal {status}',
        client_name='Client',
        language=language,
        status=status,
        is_active=is_active,
    )
    section = ProposalSection.objects.create(
        proposal=proposal,
        section_type='functional_requirements',
        title='Requirements',
        content_json=functional_requirements(language),
    )
    return section


def get_group(content_json, group_id):
    return next(group for group in content_json['groups'] if group['id'] == group_id)


def test_helper_moves_responsive_after_features_without_changing_its_id():
    content_json = functional_requirements(responsive_id='item-features-custom-responsive')

    changed = migration.add_cross_cutting_group(content_json, 'es')

    ids = [group['id'] for group in content_json['groups']]
    cross_cutting = get_group(content_json, migration.GROUP_ID)
    features = get_group(content_json, 'features')
    assert changed is True
    assert ids.index(migration.GROUP_ID) == ids.index('features') + 1
    assert cross_cutting['items'][0]['id'] == 'item-features-custom-responsive'
    assert cross_cutting['items'][0]['description'] == 'Context-specific responsive scope.'
    assert len(cross_cutting['items']) == 7
    assert [item['name'] for item in features['items']] == ['Search']


def test_helper_leaves_an_existing_custom_group_unchanged():
    content_json = functional_requirements()
    custom_group = {
        'id': migration.GROUP_ID,
        'title': 'Custom quality scope',
        'items': [{'id': 'custom-item', 'name': 'Custom item'}],
    }
    content_json['groups'].insert(2, deepcopy(custom_group))
    before = deepcopy(content_json)

    changed = migration.add_cross_cutting_group(content_json, 'es')

    assert changed is False
    assert content_json == before


def test_forward_updates_default_config():
    config = ProposalDefaultConfig.objects.create(
        language='en',
        sections_json=[{
            'section_type': 'functional_requirements',
            'content_json': functional_requirements('en'),
        }],
    )

    migration.add_cross_cutting_features(apps, None)

    config.refresh_from_db()
    config_group = get_group(
        config.sections_json[0]['content_json'],
        migration.GROUP_ID,
    )
    assert config_group['title'] == 'Cross-cutting Features'


def test_forward_updates_only_active_draft_snapshots():
    active_draft = make_proposal('draft')
    sent = make_proposal('sent')
    inactive_draft = make_proposal('draft', is_active=False)

    migration.add_cross_cutting_features(apps, None)

    active_draft.refresh_from_db()
    sent.refresh_from_db()
    inactive_draft.refresh_from_db()
    assert get_group(active_draft.content_json, migration.GROUP_ID)
    assert all(group['id'] != migration.GROUP_ID for group in sent.content_json['groups'])
    assert all(
        group['id'] != migration.GROUP_ID
        for group in inactive_draft.content_json['groups']
    )
