"""Regression coverage for the legacy document workflow expansion."""
from importlib import import_module

import pytest
from django.apps import apps

from content.models import (
    Document,
    DocumentNote,
    DocumentState,
    DocumentStateEpisode,
    DocumentStateEpisodeEvent,
    DocumentStateGroup,
    DocumentTag,
    DocumentType,
)


pytestmark = pytest.mark.django_db
migration = import_module('content.migrations.0210_document_state_episodes')


@pytest.fixture
def expanded_legacy_documents():
    # The test database already ran 0210. Recreate its pre-data-migration
    # catalog state so the one-shot production backfill can be exercised.
    DocumentStateEpisode.objects.all().delete()
    DocumentState.objects.all().delete()
    DocumentStateGroup.objects.all().delete()

    markdown_type, _ = DocumentType.objects.get_or_create(
        code='markdown', defaults={'name': 'Markdown'},
    )
    collection_type, _ = DocumentType.objects.get_or_create(
        code='collection_account', defaults={'name': 'Cuenta de cobro'},
    )
    tag = DocumentTag.objects.create(name='Urgente', color='red')
    visible = Document.objects.create(
        title='Documento publicado',
        document_type=markdown_type,
        status=Document.Status.PUBLISHED,
        client_custom_notes=[{
            'title': 'Revisar total',
            'content': 'El total no coincide.',
        }],
    )
    visible.tags.add(tag)
    unclassified = Document.objects.create(
        title='Documento borrador',
        document_type=markdown_type,
        status=Document.Status.DRAFT,
    )
    collection = Document.objects.create(
        title='Cuenta existente',
        document_type=collection_type,
        status=Document.Status.PUBLISHED,
    )
    collection.tags.add(tag)

    # Current post-save code eagerly expands JSON notes. That signal did not
    # exist in the pre-0210 production state represented by this fixture.
    visible.document_notes.all().delete()

    migration.seed_states_and_expand_legacy_data(apps, None)
    return {
        'visible': visible,
        'unclassified': unclassified,
        'collection': collection,
    }


def test_published_only_becomes_client_visible(expanded_legacy_documents):
    visible = expanded_legacy_documents['visible']
    unclassified = expanded_legacy_documents['unclassified']

    visible.refresh_from_db()
    unclassified.refresh_from_db()

    assert visible.is_client_visible is True
    assert unclassified.is_client_visible is False


def test_existing_documents_do_not_receive_an_invented_cycle_state(
    expanded_legacy_documents,
):
    visible = expanded_legacy_documents['visible']
    unclassified = expanded_legacy_documents['unclassified']

    cycle_episodes = DocumentStateEpisode.objects.filter(
        document_id__in=(visible.id, unclassified.id),
        state__group__selection_mode='exclusive',
    )

    assert not cycle_episodes.exists()


def test_legacy_tag_becomes_an_open_episode_with_unknown_time(
    expanded_legacy_documents,
):
    visible = expanded_legacy_documents['visible']
    episode = DocumentStateEpisode.objects.get(
        document=visible,
        state__normalized_name='urgente',
    )
    event = DocumentStateEpisodeEvent.objects.get(episode=episode)

    assert episode.opened_at is None
    assert episode.origin == 'migration'
    assert event.effective_at is None
    assert event.details['opening_time_known'] is False


def test_collection_accounts_are_excluded_from_state_migration(
    expanded_legacy_documents,
):
    collection = expanded_legacy_documents['collection']

    assert not DocumentStateEpisode.objects.filter(document=collection).exists()


def test_legacy_notes_become_normalized_notes_with_unknown_time(
    expanded_legacy_documents,
):
    visible = expanded_legacy_documents['visible']
    note = DocumentNote.objects.get(document=visible)

    assert note.title == 'Revisar total'
    assert note.content == 'El total no coincide.'
    assert note.created_at_known is False
