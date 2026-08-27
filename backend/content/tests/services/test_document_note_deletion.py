import pytest
from django.urls import reverse

from content.models import (
    Document,
    DocumentNote,
    DocumentNoteEvent,
    DocumentState,
    DocumentStateEpisode,
    DocumentType,
)
from content.services.document_note_service import (
    create_note,
    delete_notes,
    finish_note,
    restore_note,
)
from content.services.document_state_service import open_state

pytestmark = pytest.mark.django_db


@pytest.fixture
def markdown_type():
    return DocumentType.objects.get_or_create(
        code='markdown', defaults={'name': 'Markdown', 'label': 'Markdown'},
    )[0]


@pytest.fixture
def document(markdown_type, admin_user):
    return Document.objects.create(
        title='Informe con observaciones',
        document_type=markdown_type,
        created_by=admin_user,
        updated_by=admin_user,
    )


def _state(key):
    return DocumentState.objects.select_related('group').get(system_key=key)


def test_delete_moves_note_to_trash(document, admin_user):
    note = create_note(document, content='Texto de prueba', actor=admin_user)

    result = delete_notes(document, note_ids=[note.id], actor=admin_user)

    note.refresh_from_db()
    assert note.deleted_at is not None
    assert note.deleted_by == admin_user
    assert result['deleted_note_ids'] == [note.id]


def test_delete_event_does_not_copy_note_content(document, admin_user):
    note = create_note(document, content='No conservar este texto', actor=admin_user)

    delete_notes(document, note_ids=[note.id], actor=admin_user)

    event = DocumentNoteEvent.objects.get(note=note, event_type='deleted')
    assert event.actor == admin_user
    assert 'No conservar este texto' not in str(event.details)


def test_delete_event_survives_future_note_purge(document, admin_user):
    note = create_note(document, content='Contenido purgable', actor=admin_user)
    delete_notes(document, note_ids=[note.id], actor=admin_user)
    event = DocumentNoteEvent.objects.get(note=note, event_type='deleted')

    note.delete()

    event.refresh_from_db()
    assert event.note is None


def test_delete_last_open_note_closes_note_origin_state(document, admin_user):
    note = create_note(
        document,
        content='Corregir total',
        actor=admin_user,
        mark_needs_fix=True,
    )

    result = delete_notes(document, note_ids=[note.id], actor=admin_user)

    note.episode.refresh_from_db()
    assert note.episode.outcome == DocumentStateEpisode.Outcome.REMOVED
    assert result['state_closed'] is True


def test_delete_one_open_note_keeps_shared_state_open(document, admin_user):
    first = create_note(
        document, content='Primera', actor=admin_user, mark_needs_fix=True,
    )
    second = create_note(
        document, content='Segunda', actor=admin_user, mark_needs_fix=True,
    )

    result = delete_notes(document, note_ids=[first.id], actor=admin_user)

    second.episode.refresh_from_db()
    assert second.episode.closed_at is None
    assert result['state_closed'] is False


@pytest.mark.parametrize('note_status', ['resolved', 'discarded'])
def test_delete_accepts_finished_notes(document, admin_user, note_status):
    note = create_note(document, content='Observación terminada', actor=admin_user)
    finish_note(note, actor=admin_user, outcome=note_status)

    delete_notes(document, note_ids=[note.id], actor=admin_user)

    note.refresh_from_db()
    assert note.deleted_at is not None


def test_bulk_delete_rejects_foreign_note_atomically(
    admin_client, document, markdown_type, admin_user,
):
    local = create_note(document, content='Local', actor=admin_user)
    other_document = Document.objects.create(
        title='Otro', document_type=markdown_type, created_by=admin_user,
    )
    foreign = create_note(other_document, content='Ajena', actor=admin_user)

    response = admin_client.post(
        reverse('bulk-delete-document-notes', args=[document.pk]),
        {'note_ids': [local.id, foreign.id]},
        format='json',
    )

    assert response.status_code == 409
    assert DocumentNote.objects.filter(pk=local.id, deleted_at__isnull=True).exists()


def test_bulk_delete_rejects_duplicate_ids(admin_client, document, admin_user):
    note = create_note(document, content='Duplicada', actor=admin_user)

    response = admin_client.post(
        reverse('bulk-delete-document-notes', args=[document.pk]),
        {'note_ids': [note.id, note.id]},
        format='json',
    )

    assert response.status_code == 400
    assert DocumentNote.objects.filter(pk=note.id, deleted_at__isnull=True).exists()


def test_restore_open_note_reopens_note_state(document, admin_user):
    note = create_note(
        document, content='Pendiente', actor=admin_user, mark_needs_fix=True,
    )
    original_episode_id = note.episode_id
    delete_notes(document, note_ids=[note.id], actor=admin_user)

    note, result = restore_note(note, actor=admin_user)

    assert note.deleted_at is None
    assert note.episode_id != original_episode_id
    assert result['state_reopened'] is True
    assert note.episode.closed_at is None


def test_restore_resolved_note_does_not_open_state(document, admin_user):
    note = create_note(document, content='Ya resuelta', actor=admin_user)
    finish_note(note, actor=admin_user)
    delete_notes(document, note_ids=[note.id], actor=admin_user)
    before = document.state_episodes.filter(
        state__system_key='needs_fix', closed_at__isnull=True,
    ).count()

    note, result = restore_note(note, actor=admin_user)

    assert note.deleted_at is None
    assert result['state_reopened'] is False
    assert document.state_episodes.filter(
        state__system_key='needs_fix', closed_at__isnull=True,
    ).count() == before


def test_restore_conflict_leaves_note_in_trash(admin_client, document, admin_user):
    note = create_note(
        document, content='Pendiente', actor=admin_user, mark_needs_fix=True,
    )
    delete_notes(document, note_ids=[note.id], actor=admin_user)
    open_state(document, _state('closed'), actor=admin_user)

    response = admin_client.post(
        reverse('restore-document-note', args=[document.pk, note.pk]),
        format='json',
    )

    note.refresh_from_db()
    assert response.status_code == 409
    assert note.deleted_at is not None


def test_active_list_hides_deleted_note(admin_client, document, admin_user):
    note = create_note(document, content='Ruido', actor=admin_user)
    delete_notes(document, note_ids=[note.id], actor=admin_user)

    response = admin_client.get(reverse('document-notes', args=[document.pk]))

    assert response.status_code == 200
    assert response.json() == []


def test_trash_list_returns_deleted_note(admin_client, document, admin_user):
    note = create_note(document, content='Recuperable', actor=admin_user)
    delete_notes(document, note_ids=[note.id], actor=admin_user)

    response = admin_client.get(
        reverse('document-notes', args=[document.pk]), {'scope': 'deleted'},
    )

    assert response.status_code == 200
    assert response.json()[0]['content'] == 'Recuperable'
    assert response.json()[0]['deleted_by'] == admin_user.id


def test_event_api_returns_generic_audit(admin_client, document, admin_user):
    note = create_note(document, content='Contenido privado', actor=admin_user)
    delete_notes(document, note_ids=[note.id], actor=admin_user)

    response = admin_client.get(
        reverse('document-note-events', args=[document.pk]),
    )

    row = response.json()[0]
    assert row['event_type'] == 'deleted'
    assert row['actor'] == admin_user.id
    assert 'content' not in row


def test_finish_discard_closes_note_origin_state_without_client_flag(
    document, admin_user,
):
    note = create_note(
        document, content='No aplica', actor=admin_user, mark_needs_fix=True,
    )

    _, result = finish_note(
        note, actor=admin_user, outcome=DocumentNote.Status.DISCARDED,
    )

    assert result['state_closed'] is True


def test_finish_note_does_not_close_manual_state(document, admin_user):
    episode, _ = open_state(document, _state('needs_fix'), actor=admin_user)
    note = DocumentNote.objects.create(
        document=document,
        episode=episode,
        content='Ligada a una señal manual',
        created_by=admin_user,
    )

    _, result = finish_note(note, actor=admin_user)

    episode.refresh_from_db()
    assert episode.closed_at is None
    assert result['state_closed'] is False


def test_document_detail_hides_deleted_note(admin_client, document, admin_user):
    note = create_note(document, content='No mostrar', actor=admin_user)
    delete_notes(document, note_ids=[note.id], actor=admin_user)

    response = admin_client.get(reverse('retrieve-document', args=[document.pk]))

    assert response.status_code == 200
    assert response.json()['notes'] == []
