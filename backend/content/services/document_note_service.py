from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from content.models import DocumentNote, DocumentState, DocumentStateEpisode
from content.services.document_state_service import (
    active_episode_for_key,
    close_episode,
    open_state,
)


class DocumentNoteError(ValueError):
    pass


def sync_legacy_notes(document, *, actor=None):
    """Expand legacy JSON notes once without overwriting normalized history."""
    if document.document_notes.exists():
        return
    notes = document.client_custom_notes or []
    DocumentNote.objects.bulk_create([
        DocumentNote(
            document=document,
            title=str(note.get('title') or '').strip(),
            content=str(note.get('content') or '').strip(),
            order=index,
            created_by=actor,
            created_at_known=False,
        )
        for index, note in enumerate(notes)
        if str(note.get('title') or '').strip() or str(note.get('content') or '').strip()
    ])


@transaction.atomic
def create_note(
    document,
    *,
    title='',
    content,
    actor=None,
    mark_needs_fix=False,
):
    content = str(content or '').strip()
    title = str(title or '').strip()
    if not content:
        raise DocumentNoteError('La observación no puede estar vacía.')

    episode = None
    if mark_needs_fix:
        episode = active_episode_for_key(document, 'needs_fix')
        if episode is None:
            state = DocumentState.objects.filter(
                system_key='needs_fix', is_active=True,
            ).first()
            if state:
                episode, _ = open_state(
                    document,
                    state,
                    actor=actor,
                    origin=DocumentStateEpisode.Origin.NOTE,
                    idempotent=True,
                )

    order = (
        document.document_notes.aggregate(max_order=Max('order'))['max_order']
        or 0
    )
    if document.document_notes.exists():
        order += 1
    return DocumentNote.objects.create(
        document=document,
        episode=episode,
        title=title,
        content=content,
        order=order,
        created_by=actor,
    )


def update_note(note, *, title=None, content=None):
    if note.status != DocumentNote.Status.OPEN:
        raise DocumentNoteError('Sólo se pueden editar observaciones pendientes.')
    update_fields = ['updated_at']
    if title is not None:
        note.title = str(title).strip()
        update_fields.append('title')
    if content is not None:
        content = str(content).strip()
        if not content:
            raise DocumentNoteError('La observación no puede estar vacía.')
        note.content = content
        update_fields.append('content')
    note.save(update_fields=update_fields)
    return note


@transaction.atomic
def finish_note(
    note,
    *,
    actor=None,
    outcome=DocumentNote.Status.RESOLVED,
    resolution_note='',
    close_linked_state=False,
    move_cycle_to_bug_attended=False,
):
    note = DocumentNote.objects.select_for_update().select_related(
        'episode__state', 'document',
    ).get(pk=note.pk)
    if note.status != DocumentNote.Status.OPEN:
        raise DocumentNoteError('La observación ya no está pendiente.')
    if outcome not in (DocumentNote.Status.RESOLVED, DocumentNote.Status.DISCARDED):
        raise DocumentNoteError('El resultado de la observación no es válido.')

    note.status = outcome
    note.resolution_note = str(resolution_note or '').strip()
    note.resolved_by = actor
    note.resolved_at = timezone.now()
    note.save(update_fields=(
        'status', 'resolution_note', 'resolved_by', 'resolved_at', 'updated_at',
    ))

    state_closed = False
    cycle_moved = False
    if close_linked_state and note.episode_id and note.episode.closed_at is None:
        still_open = DocumentNote.objects.filter(
            episode_id=note.episode_id,
            status=DocumentNote.Status.OPEN,
        ).exists()
        if not still_open:
            state_outcome = (
                DocumentStateEpisode.Outcome.COMPLETED
                if outcome == DocumentNote.Status.RESOLVED
                else DocumentStateEpisode.Outcome.REMOVED
            )
            close_episode(
                note.episode,
                actor=actor,
                outcome=state_outcome,
                close_note=note.resolution_note,
            )
            state_closed = True
            if move_cycle_to_bug_attended and outcome == DocumentNote.Status.RESOLVED:
                state = DocumentState.objects.filter(
                    system_key='bug_resolved', is_active=True,
                ).first()
                if state:
                    open_state(
                        note.document,
                        state,
                        actor=actor,
                        origin=DocumentStateEpisode.Origin.NOTE,
                        idempotent=True,
                    )
                    cycle_moved = True

    return note, {
        'state_closed': state_closed,
        'cycle_moved': cycle_moved,
    }
