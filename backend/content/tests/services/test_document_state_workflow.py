from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from content.models import (
    Document,
    DocumentNote,
    DocumentState,
    DocumentStateEpisode,
    DocumentStateEpisodeEvent,
    DocumentStateGroup,
    DocumentType,
)
from content.services.document_note_service import create_note, finish_note
from content.services.document_state_service import (
    DocumentStateError,
    close_episode,
    correct_opened_at,
    open_state,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def markdown_type():
    return DocumentType.objects.get_or_create(
        code='markdown', defaults={'name': 'Markdown', 'label': 'Markdown'},
    )[0]


@pytest.fixture
def document(markdown_type, admin_user):
    return Document.objects.create(
        title='Informe de avance',
        document_type=markdown_type,
        created_by=admin_user,
        updated_by=admin_user,
    )


def state(key):
    return DocumentState.objects.select_related('group').get(system_key=key)


def test_new_document_opens_draft_episode(document, admin_user):
    episode = document.state_episodes.get(closed_at__isnull=True)

    assert episode.state.system_key == 'draft'
    assert episode.opened_by == admin_user
    assert episode.events.get().event_type == DocumentStateEpisodeEvent.EventType.OPENED


def test_additive_state_coexists_with_cycle(document, admin_user):
    needs_fix, created = open_state(document, state('needs_fix'), actor=admin_user)

    active_keys = set(
        document.state_episodes.filter(closed_at__isnull=True)
        .values_list('state__system_key', flat=True),
    )
    assert created is True
    assert needs_fix.closed_at is None
    assert active_keys == {'draft', 'needs_fix'}


def test_cycle_transition_closes_previous_episode(document, admin_user):
    sent, _ = open_state(document, state('sent'), actor=admin_user)

    draft = document.state_episodes.get(state__system_key='draft')
    assert draft.outcome == DocumentStateEpisode.Outcome.TRANSITIONED
    assert draft.closed_at is not None
    assert sent.closed_at is None


def test_incompatible_state_rejects_open_episode(document, admin_user):
    open_state(document, state('needs_fix'), actor=admin_user)

    with pytest.raises(DocumentStateError) as exc_info:
        open_state(document, state('closed'), actor=admin_user)

    assert exc_info.value.code == 'incompatible_state'


def test_removed_episode_keeps_distinct_outcome(document, admin_user):
    episode, _ = open_state(document, state('needs_fix'), actor=admin_user)

    close_episode(
        episode,
        actor=admin_user,
        outcome=DocumentStateEpisode.Outcome.REMOVED,
        close_note='La marca se agregó por error.',
    )

    episode.refresh_from_db()
    assert episode.outcome == DocumentStateEpisode.Outcome.REMOVED
    assert episode.events.filter(event_type='removed').exists()


def test_state_can_repeat_after_closure(document, admin_user):
    first, _ = open_state(document, state('needs_fix'), actor=admin_user)
    close_episode(first, actor=admin_user)

    second, _ = open_state(document, state('needs_fix'), actor=admin_user)

    assert second.pk != first.pk
    assert document.state_episodes.filter(state__system_key='needs_fix').count() == 2


def test_opening_date_correction_records_event(document, admin_user):
    episode = document.state_episodes.get(state__system_key='draft')
    corrected = timezone.now() - timedelta(days=2)

    correct_opened_at(episode, corrected, actor=admin_user)

    episode.refresh_from_db()
    event = episode.events.get(event_type='opened_at_corrected')
    assert abs((episode.opened_at - corrected).total_seconds()) < 1
    assert event.details['new_opened_at'] == corrected.isoformat()


def test_resolving_last_note_moves_cycle(document, admin_user):
    note = create_note(
        document,
        content='Corregir el total mostrado.',
        actor=admin_user,
        mark_needs_fix=True,
    )

    note, result = finish_note(
        note,
        actor=admin_user,
        close_linked_state=True,
        move_cycle_to_bug_attended=True,
        resolution_note='Total corregido.',
    )

    assert note.status == DocumentNote.Status.RESOLVED
    assert result == {'state_closed': True, 'cycle_moved': True}
    assert document.state_episodes.filter(
        state__system_key='bug_resolved', closed_at__isnull=True,
    ).exists()


def test_state_filters_apply_or_semantics(admin_client, document, markdown_type, admin_user):
    sent_doc = Document.objects.create(
        title='Enviado', document_type=markdown_type, created_by=admin_user,
    )
    open_state(document, state('needs_fix'), actor=admin_user)
    open_state(sent_doc, state('sent'), actor=admin_user)

    response = admin_client.get(reverse('list-documents'), {
        'states': f'{state("needs_fix").pk},{state("sent").pk}',
    })

    assert response.status_code == 200
    assert {row['id'] for row in response.json()} == {document.pk, sent_doc.pk}


def test_absence_filter_excludes_matching_state(admin_client, document, markdown_type, admin_user):
    open_state(document, state('needs_fix'), actor=admin_user)
    clean = Document.objects.create(
        title='Sin observación', document_type=markdown_type, created_by=admin_user,
    )

    response = admin_client.get(reverse('list-documents'), {
        'without_states': state('needs_fix').pk,
    })

    assert response.status_code == 200
    ids = {row['id'] for row in response.json()}
    assert clean.pk in ids
    assert document.pk not in ids


def test_catalog_suggests_similar_name(admin_client):
    response = admin_client.post(reverse('document-states'), {
        'name': 'Arreglar bug',
    }, format='json')

    assert response.status_code == 409
    assert response.json()['code'] == 'similar_states'
    assert response.json()['suggestions'][0]['system_key'] == 'needs_fix'


def test_collection_account_rejects_workflow(admin_user):
    document_type = DocumentType.objects.get_or_create(
        code='collection_account',
        defaults={'name': 'Cuenta', 'label': 'Cuenta de cobro'},
    )[0]
    account = Document.objects.create(
        title='Cuenta 001', document_type=document_type, created_by=admin_user,
    )

    with pytest.raises(DocumentStateError) as exc_info:
        open_state(account, state('sent'), actor=admin_user)

    assert exc_info.value.code == 'document_type_excluded'
    assert not account.state_episodes.exists()


def test_inline_state_is_available_globally_via_api(admin_client, document):
    signals = DocumentStateGroup.objects.get(selection_mode='additive')
    created = admin_client.post(reverse('document-states'), {
        'name': 'Esperando firma',
        'group': signals.pk,
        'color': 'orange',
        'confirm_similar': True,
    }, format='json')

    assert created.status_code == 201
    state_id = created.json()['id']
    opened = admin_client.post(reverse('open-document-state', args=[document.pk]), {
        'state_id': state_id,
    }, format='json')

    assert opened.status_code == 201
    assert opened.json()['state']['name'] == 'Esperando firma'
    assert DocumentState.objects.get(pk=state_id).is_active is True


def test_close_api_records_removal_metadata(admin_client, document, admin_user):
    episode, _ = open_state(document, state('needs_fix'), actor=admin_user)

    response = admin_client.post(
        reverse('close-document-state', args=[document.pk, episode.pk]),
        {'outcome': 'removed', 'note': 'No correspondía a este documento.'},
        format='json',
    )

    assert response.status_code == 200
    assert response.json()['outcome'] == 'removed'
    assert response.json()['closed_by'] == admin_user.pk
    assert response.json()['close_note'] == 'No correspondía a este documento.'


def test_history_orders_latest_movement_first(admin_client, document, admin_user):
    needs_fix, _ = open_state(document, state('needs_fix'), actor=admin_user)
    close_episode(needs_fix, actor=admin_user)
    sent, _ = open_state(document, state('sent'), actor=admin_user)

    response = admin_client.get(reverse('document-state-history', args=[document.pk]))

    assert response.status_code == 200
    rows = response.json()
    assert rows[0]['id'] == sent.pk
    assert rows[0]['events'][0]['actor'] == admin_user.pk
    assert {event['event_type'] for event in rows[0]['events']} == {'opened'}


def test_note_api_resolves_linked_workflow(admin_client, document):
    created = admin_client.post(reverse('document-notes', args=[document.pk]), {
        'title': 'Total incorrecto',
        'content': 'Corregir el valor final.',
        'mark_needs_fix': True,
    }, format='json')
    assert created.status_code == 201

    response = admin_client.post(
        reverse('finish-document-note', args=[document.pk, created.json()['id']]),
        {
            'outcome': 'resolved',
            'resolution_note': 'Valor corregido.',
            'close_linked_state': True,
            'move_cycle_to_bug_attended': True,
        },
        format='json',
    )

    assert response.status_code == 200
    assert response.json()['state_closed'] is True
    assert response.json()['cycle_moved'] is True
    assert response.json()['note']['status'] == 'resolved'


def test_merge_duplicate_reassigns_open_episode(admin_client, document, admin_user):
    signals = DocumentStateGroup.objects.get(selection_mode='additive')
    source = DocumentState.objects.create(
        name='Arreglo pendiente', group=signals, color='orange',
    )
    target = DocumentState.objects.create(
        name='Corrección pendiente', group=signals, color='red',
    )
    episode, _ = open_state(document, source, actor=admin_user)

    response = admin_client.post(
        reverse('merge-document-state', args=[source.pk]),
        {'target_state_id': target.pk},
        format='json',
    )

    assert response.status_code == 200
    episode.refresh_from_db()
    source.refresh_from_db()
    assert episode.state == target
    assert source.merged_into == target
    assert source.is_active is False


def test_retire_rejects_state_still_in_use(admin_client, document, admin_user):
    signals = DocumentStateGroup.objects.get(selection_mode='additive')
    custom = DocumentState.objects.create(
        name='Pendiente de insumo', group=signals, color='yellow',
    )
    open_state(document, custom, actor=admin_user)

    response = admin_client.post(reverse('retire-document-state', args=[custom.pk]))

    assert response.status_code == 409
    assert response.json()['code'] == 'state_in_use'


def test_group_cannot_become_exclusive_with_concurrent_episodes(
    admin_client, document, admin_user,
):
    group = DocumentStateGroup.objects.create(
        name='Seguimiento', selection_mode='additive', order=3,
    )
    first = DocumentState.objects.create(name='Esperando firma', group=group)
    second = DocumentState.objects.create(name='Esperando pago', group=group)
    open_state(document, first, actor=admin_user)
    open_state(document, second, actor=admin_user)

    response = admin_client.patch(
        reverse('document-state-group-detail', args=[group.pk]),
        {'selection_mode': 'exclusive'},
        format='json',
    )

    assert response.status_code == 409
    assert response.json()['code'] == 'group_has_multiple_active_states'


def test_catalog_rule_rejects_an_active_incompatibility(
    admin_client, document, admin_user,
):
    signals = DocumentStateGroup.objects.get(selection_mode='additive')
    first = DocumentState.objects.create(name='Esperando firma', group=signals)
    second = DocumentState.objects.create(name='Firma rechazada', group=signals)
    open_state(document, first, actor=admin_user)
    open_state(document, second, actor=admin_user)

    response = admin_client.patch(
        reverse('update-document-state', args=[first.pk]),
        {'incompatibility_ids': [second.pk]},
        format='json',
    )

    assert response.status_code == 409
    assert response.json()['code'] == 'active_state_rule_conflict'
