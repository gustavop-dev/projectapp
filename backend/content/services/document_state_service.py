from django.db import transaction
from django.utils import timezone

from content.models import (
    Document,
    DocumentState,
    DocumentStateEpisode,
    DocumentStateEpisodeEvent,
    DocumentStateGroup,
)
from content.services.document_type_codes import COLLECTION_ACCOUNT


class DocumentStateError(ValueError):
    def __init__(self, message, *, code='invalid_state_operation'):
        super().__init__(message)
        self.code = code


def document_supports_states(document):
    document_type = getattr(document, 'document_type', None)
    return not document_type or document_type.code != COLLECTION_ACCOUNT


def _canonical_state(state):
    visited = set()
    while state.merged_into_id and state.pk not in visited:
        visited.add(state.pk)
        state = state.merged_into
    return state


def _record_event(episode, event_type, actor, effective_at, **details):
    return DocumentStateEpisodeEvent.objects.create(
        episode=episode,
        event_type=event_type,
        actor=actor,
        effective_at=effective_at,
        details=details,
    )


def _close_locked(episode, *, actor, outcome, close_note='', closed_at=None):
    if episode.closed_at is not None:
        raise DocumentStateError(
            'Este episodio ya está cerrado.',
            code='episode_already_closed',
        )
    closed_at = closed_at or timezone.now()
    episode.closed_at = closed_at
    episode.closed_by = actor
    episode.outcome = outcome
    episode.close_note = str(close_note or '').strip()
    episode.save(update_fields=(
        'closed_at', 'closed_by', 'outcome', 'close_note', 'updated_at',
    ))
    event_by_outcome = {
        DocumentStateEpisode.Outcome.REMOVED: (
            DocumentStateEpisodeEvent.EventType.REMOVED
        ),
        DocumentStateEpisode.Outcome.TRANSITIONED: (
            DocumentStateEpisodeEvent.EventType.TRANSITIONED
        ),
        DocumentStateEpisode.Outcome.MERGED: (
            DocumentStateEpisodeEvent.EventType.MERGED
        ),
    }
    event_type = event_by_outcome.get(
        outcome,
        DocumentStateEpisodeEvent.EventType.CLOSED,
    )
    _record_event(
        episode,
        event_type,
        actor,
        closed_at,
        outcome=outcome,
        note=episode.close_note,
    )
    return episode


@transaction.atomic
def open_state(
    document,
    state,
    *,
    actor=None,
    opened_at=None,
    origin=DocumentStateEpisode.Origin.MANUAL,
    idempotent=False,
):
    """Open one state while enforcing exclusivity and incompatibilities."""
    locked_document = (
        Document.objects.select_for_update()
        .select_related('document_type')
        .get(pk=document.pk)
    )
    if not document_supports_states(locked_document):
        raise DocumentStateError(
            'Las cuentas de cobro conservan su ciclo comercial propio.',
            code='document_type_excluded',
        )

    state = _canonical_state(
        DocumentState.objects.select_related('group', 'merged_into').get(pk=state.pk),
    )
    if not state.is_active:
        raise DocumentStateError(
            'El estado está retirado y no se puede volver a abrir.',
            code='state_retired',
        )

    now = timezone.now()
    opened_at = opened_at or now
    if opened_at > now:
        raise DocumentStateError(
            'La fecha de apertura no puede estar en el futuro.',
            code='opened_at_in_future',
        )

    active = list(
        DocumentStateEpisode.objects.select_for_update()
        .filter(document=locked_document, closed_at__isnull=True)
        .select_related('state__group')
    )
    existing = next((episode for episode in active if episode.state_id == state.id), None)
    if existing:
        if idempotent:
            return existing, False
        raise DocumentStateError(
            'El documento ya tiene este estado activo.',
            code='state_already_active',
        )

    incompatible_ids = set(state.incompatibilities.values_list('id', flat=True))
    # Keep the rule safe even when legacy/imported through rows were written
    # only in one direction. The catalog exposes the relation as symmetric,
    # but the database table itself stores directional pairs.
    incompatible_ids.update(
        DocumentState.objects.filter(incompatibilities=state)
        .values_list('id', flat=True),
    )
    incompatible = [
        episode.state.name for episode in active
        if episode.state_id in incompatible_ids
    ]
    if incompatible:
        raise DocumentStateError(
            f'No se puede combinar con: {", ".join(incompatible)}.',
            code='incompatible_state',
        )

    if state.group.selection_mode == DocumentStateGroup.SelectionMode.EXCLUSIVE:
        for episode in active:
            if episode.state.group_id == state.group_id:
                if episode.opened_at and opened_at < episode.opened_at:
                    raise DocumentStateError(
                        'La transición no puede quedar antes del ciclo activo.',
                        code='transition_before_active_cycle',
                    )
                _close_locked(
                    episode,
                    actor=actor,
                    outcome=DocumentStateEpisode.Outcome.TRANSITIONED,
                    close_note=f'Transición a {state.name}',
                    # A backdated transition represents when the movement
                    # happened, not when it was entered into the system.
                    closed_at=opened_at,
                )

    episode = DocumentStateEpisode.objects.create(
        document=locked_document,
        state=state,
        opened_at=opened_at,
        opened_by=actor,
        origin=origin,
    )
    _record_event(
        episode,
        DocumentStateEpisodeEvent.EventType.OPENED,
        actor,
        opened_at,
        origin=origin,
    )
    return episode, True


@transaction.atomic
def close_episode(
    episode,
    *,
    actor=None,
    outcome=DocumentStateEpisode.Outcome.COMPLETED,
    close_note='',
):
    locked = (
        DocumentStateEpisode.objects.select_for_update()
        .select_related('state', 'document')
        .get(pk=episode.pk)
    )
    return _close_locked(
        locked,
        actor=actor,
        outcome=outcome,
        close_note=close_note,
    )


@transaction.atomic
def correct_opened_at(episode, opened_at, *, actor=None):
    locked = DocumentStateEpisode.objects.select_for_update().get(pk=episode.pk)
    now = timezone.now()
    if opened_at > now:
        raise DocumentStateError(
            'La fecha de apertura no puede estar en el futuro.',
            code='opened_at_in_future',
        )
    if locked.closed_at and opened_at > locked.closed_at:
        raise DocumentStateError(
            'La apertura no puede quedar después del cierre.',
            code='opened_at_after_close',
        )
    previous = locked.opened_at
    locked.opened_at = opened_at
    locked.save(update_fields=('opened_at', 'updated_at'))
    _record_event(
        locked,
        DocumentStateEpisodeEvent.EventType.OPENED_AT_CORRECTED,
        actor,
        opened_at,
        previous_opened_at=previous.isoformat() if previous else None,
        new_opened_at=opened_at.isoformat(),
    )
    return locked


def active_episode_for_key(document, system_key):
    return (
        DocumentStateEpisode.objects.filter(
            document=document,
            state__system_key=system_key,
            closed_at__isnull=True,
        )
        .select_related('state__group')
        .first()
    )


def ensure_initial_state(document, *, actor=None):
    """Give new generic documents the seeded draft cycle state when available."""
    if not document_supports_states(document):
        return None
    state = DocumentState.objects.filter(system_key='draft', is_active=True).first()
    if not state:
        return None
    episode, _ = open_state(
        document,
        state,
        actor=actor,
        origin=DocumentStateEpisode.Origin.MANUAL,
        idempotent=True,
    )
    return episode


@transaction.atomic
def merge_states(source, target, *, actor=None):
    source = (
        DocumentState.objects.select_for_update()
        .select_related('merged_into')
        .get(pk=source.pk)
    )
    target = _canonical_state(
        DocumentState.objects.select_for_update()
        .select_related('merged_into')
        .get(pk=target.pk),
    )
    if source.pk == target.pk:
        raise DocumentStateError(
            'El estado de origen y destino deben ser distintos.',
            code='same_merge_target',
        )
    if not target.is_active:
        raise DocumentStateError(
            'El estado de destino está retirado.',
            code='merge_target_retired',
        )
    if source.group_id != target.group_id:
        raise DocumentStateError(
            'Sólo se pueden fusionar estados del mismo grupo.',
            code='merge_group_mismatch',
        )
    if source.system_key:
        raise DocumentStateError(
            'Los estados semilla no se fusionan; se pueden renombrar o retirar.',
            code='system_state_merge_blocked',
        )

    active_source = list(
        DocumentStateEpisode.objects.select_for_update()
        .filter(state=source, closed_at__isnull=True)
        .select_related('document')
    )
    target_incompatible_ids = set(
        target.incompatibilities.values_list('id', flat=True),
    )
    target_incompatible_ids.update(
        DocumentState.objects.filter(incompatibilities=target)
        .values_list('id', flat=True),
    )
    conflicting_document_ids = set(
        DocumentStateEpisode.objects.filter(
            document_id__in=[episode.document_id for episode in active_source],
            state_id__in=target_incompatible_ids,
            closed_at__isnull=True,
        ).values_list('document_id', flat=True),
    )
    if conflicting_document_ids:
        raise DocumentStateError(
            'Hay documentos activos con estados incompatibles con el destino.',
            code='merge_target_incompatible',
        )
    target_document_ids = set(
        DocumentStateEpisode.objects.filter(
            state=target,
            closed_at__isnull=True,
            document_id__in=[episode.document_id for episode in active_source],
        ).values_list('document_id', flat=True),
    )
    for episode in active_source:
        if episode.document_id in target_document_ids:
            _close_locked(
                episode,
                actor=actor,
                outcome=DocumentStateEpisode.Outcome.MERGED,
                close_note=f'Fusionado con {target.name}',
            )
            continue
        original_state_id = episode.state_id
        episode.state = target
        episode.save(update_fields=('state', 'updated_at'))
        _record_event(
            episode,
            DocumentStateEpisodeEvent.EventType.MERGED,
            actor,
            timezone.now(),
            source_state_id=original_state_id,
            source_state_name=source.name,
            target_state_id=target.id,
            target_state_name=target.name,
        )

    inherited_incompatibilities = list(source.incompatibilities.exclude(pk=target.pk))
    if inherited_incompatibilities:
        target.incompatibilities.add(*inherited_incompatibilities)
    source.merged_into = target
    source.is_active = False
    source.updated_by = actor
    source.save(update_fields=('merged_into', 'is_active', 'updated_by', 'updated_at'))
    return source


def retire_state(state, *, actor=None):
    if state.episodes.filter(closed_at__isnull=True).exists():
        raise DocumentStateError(
            'Retira primero el estado de los documentos que todavía lo usan.',
            code='state_in_use',
        )
    state.is_active = False
    state.updated_by = actor
    state.save(update_fields=('is_active', 'updated_by', 'updated_at'))
    return state
