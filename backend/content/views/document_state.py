from difflib import SequenceMatcher

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import (
    Document,
    DocumentNote,
    DocumentState,
    DocumentStateEpisode,
    DocumentStateGroup,
)
from content.models.document_state import normalize_document_state_name
from content.serializers.document_state import (
    CloseDocumentStateSerializer,
    CorrectEpisodeOpeningSerializer,
    CreateDocumentNoteSerializer,
    DocumentNoteSerializer,
    DocumentStateEpisodeSerializer,
    DocumentStateGroupSerializer,
    DocumentStateSerializer,
    FinishDocumentNoteSerializer,
    OpenDocumentStateSerializer,
    UpdateDocumentNoteSerializer,
)
from content.services.document_note_service import (
    DocumentNoteError,
    create_note,
    finish_note,
    update_note,
)
from content.services.document_state_service import (
    DocumentStateError,
    close_episode,
    correct_opened_at,
    merge_states,
    open_state,
    retire_state,
)


def _state_error(exc, http_status=status.HTTP_400_BAD_REQUEST):
    return Response(
        {'detail': str(exc), 'code': getattr(exc, 'code', 'invalid_operation')},
        status=http_status,
    )


def _catalog_queryset(include_retired=False):
    queryset = (
        DocumentState.objects.select_related('group', 'merged_into')
        .prefetch_related('incompatibilities')
        .annotate(
            active_document_count=Count(
                'episodes__document',
                filter=Q(episodes__closed_at__isnull=True),
                distinct=True,
            ),
            historical_episode_count=Count('episodes', distinct=True),
        )
        .order_by('group__order', 'order', 'name')
    )
    if not include_retired:
        queryset = queryset.filter(is_active=True, merged_into__isnull=True)
    return queryset


def _documents_with_multiple_group_states(group):
    return (
        DocumentStateEpisode.objects.filter(
            state__group=group,
            closed_at__isnull=True,
        )
        .values('document_id')
        .annotate(state_count=Count('state_id', distinct=True))
        .filter(state_count__gt=1)
    )


def _state_update_conflict(state, validated_data):
    target_group = validated_data.get('group', state.group)
    if (
        target_group.selection_mode
        == DocumentStateGroup.SelectionMode.EXCLUSIVE
    ):
        source_documents = DocumentStateEpisode.objects.filter(
            state=state,
            closed_at__isnull=True,
        ).values('document_id')
        if DocumentStateEpisode.objects.filter(
            document_id__in=source_documents,
            state__group=target_group,
            closed_at__isnull=True,
        ).exclude(state=state).exists():
            return (
                'Hay documentos que ya tienen otro estado vigente en el '
                'grupo exclusivo de destino.'
            )

    proposed = validated_data.get('incompatibilities')
    if proposed is not None:
        source_documents = DocumentStateEpisode.objects.filter(
            state=state,
            closed_at__isnull=True,
        ).values('document_id')
        if DocumentStateEpisode.objects.filter(
            document_id__in=source_documents,
            state__in=proposed,
            closed_at__isnull=True,
        ).exists():
            return (
                'Hay documentos que usan simultáneamente estados que quedarían '
                'marcados como incompatibles.'
            )
    return None


def _similar_states(query):
    normalized_query = normalize_document_state_name(query)
    if not normalized_query:
        return []
    query_tokens = {token for token in normalized_query.split() if len(token) >= 3}
    candidates = []
    for state in _catalog_queryset(include_retired=False):
        normalized_name = state.normalized_name
        state_tokens = {token for token in normalized_name.split() if len(token) >= 3}
        score = SequenceMatcher(None, normalized_query, normalized_name).ratio()
        has_substring = (
            normalized_query in normalized_name or normalized_name in normalized_query
        )
        shared_token = bool(query_tokens & state_tokens)
        if has_substring or shared_token or score >= 0.65:
            candidates.append((max(score, 0.9 if has_substring else 0), state))
    candidates.sort(key=lambda item: (-item[0], item[1].name.casefold()))
    return [
        {
            **DocumentStateSerializer(state).data,
            'similarity': round(score, 3),
        }
        for score, state in candidates[:5]
    ]


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def document_state_groups(request):
    if request.method == 'GET':
        groups = DocumentStateGroup.objects.annotate(
            state_count=Count('states', filter=Q(states__is_active=True)),
        )
        return Response(DocumentStateGroupSerializer(groups, many=True).data)
    serializer = DocumentStateGroupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'POST'])
@permission_classes([IsAdminUser])
def document_state_group_detail(request, group_id):
    group = get_object_or_404(DocumentStateGroup, pk=group_id)
    if request.method == 'POST':
        if group.states.filter(is_active=True).exists():
            return Response(
                {
                    'detail': 'Retira o mueve primero los estados activos del grupo.',
                    'code': 'group_in_use',
                },
                status=status.HTTP_409_CONFLICT,
            )
        group.is_active = False
        group.save(update_fields=('is_active', 'updated_at'))
        return Response(DocumentStateGroupSerializer(group).data)
    serializer = DocumentStateGroupSerializer(
        group, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    new_mode = serializer.validated_data.get('selection_mode', group.selection_mode)
    if new_mode != group.selection_mode:
        expected_modes = {
            item.system_key: DocumentStateSerializer.SYSTEM_GROUP_MODES.get(
                item.system_key,
            )
            for item in group.states.exclude(system_key__isnull=True)
        }
        if any(mode and mode != new_mode for mode in expected_modes.values()):
            return Response(
                {
                    'detail': 'El grupo contiene estados semilla con una función fija.',
                    'code': 'system_group_mode_conflict',
                },
                status=status.HTTP_409_CONFLICT,
            )
        if (
            new_mode == DocumentStateGroup.SelectionMode.EXCLUSIVE
            and _documents_with_multiple_group_states(group).exists()
        ):
            return Response(
                {
                    'detail': (
                        'Hay documentos con varios estados vigentes en este grupo.'
                    ),
                    'code': 'group_has_multiple_active_states',
                },
                status=status.HTTP_409_CONFLICT,
            )
    serializer.save()
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def document_states(request):
    if request.method == 'GET':
        include_retired = str(
            request.query_params.get('include_retired') or '',
        ).lower() in ('1', 'true', 'yes')
        return Response(
            DocumentStateSerializer(
                _catalog_queryset(include_retired=include_retired), many=True,
            ).data,
        )

    payload = request.data.copy()
    confirm_similar = bool(payload.pop('confirm_similar', False))
    if not payload.get('group'):
        signals = DocumentStateGroup.objects.filter(
            selection_mode=DocumentStateGroup.SelectionMode.ADDITIVE,
            is_active=True,
        ).order_by('order').first()
        if not signals:
            return Response(
                {'group': 'No hay un grupo aditivo disponible.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload['group'] = signals.pk
    if not payload.get('color'):
        payload['color'] = DocumentState.Color.GRAY

    suggestions = _similar_states(payload.get('name', ''))
    if suggestions and not confirm_similar:
        return Response(
            {
                'detail': 'Hay estados parecidos. Revisa antes de crear otro.',
                'code': 'similar_states',
                'suggestions': suggestions,
            },
            status=status.HTTP_409_CONFLICT,
        )
    serializer = DocumentStateSerializer(data=payload)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(created_by=request.user, updated_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def document_state_suggestions(request):
    return Response(_similar_states(request.query_params.get('q', '')))


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_document_state(request, state_id):
    state = get_object_or_404(
        DocumentState.objects.select_related('group'), pk=state_id,
    )
    serializer = DocumentStateSerializer(state, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    conflict = _state_update_conflict(state, serializer.validated_data)
    if conflict:
        return Response(
            {'detail': conflict, 'code': 'active_state_rule_conflict'},
            status=status.HTTP_409_CONFLICT,
        )
    serializer.save(updated_by=request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def retire_document_state(request, state_id):
    state = get_object_or_404(DocumentState, pk=state_id)
    try:
        retire_state(state, actor=request.user)
    except DocumentStateError as exc:
        return _state_error(exc, status.HTTP_409_CONFLICT)
    return Response(DocumentStateSerializer(state).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def merge_document_state(request, state_id):
    source = get_object_or_404(DocumentState, pk=state_id)
    target = get_object_or_404(DocumentState, pk=request.data.get('target_state_id'))
    try:
        merge_states(source, target, actor=request.user)
    except DocumentStateError as exc:
        return _state_error(exc, status.HTTP_409_CONFLICT)
    return Response(DocumentStateSerializer(source).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def open_document_state(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    serializer = OpenDocumentStateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        episode, created = open_state(
            document,
            serializer.validated_data['state'],
            actor=request.user,
            opened_at=serializer.validated_data.get('opened_at'),
            origin=serializer.validated_data['origin'],
        )
    except DocumentStateError as exc:
        return _state_error(exc)
    return Response(
        DocumentStateEpisodeSerializer(episode).data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def close_document_state(request, document_id, episode_id):
    episode = get_object_or_404(
        DocumentStateEpisode, pk=episode_id, document_id=document_id,
    )
    serializer = CloseDocumentStateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        episode = close_episode(
            episode,
            actor=request.user,
            outcome=serializer.validated_data['outcome'],
            close_note=serializer.validated_data['note'],
        )
    except DocumentStateError as exc:
        return _state_error(exc)
    return Response(DocumentStateEpisodeSerializer(episode).data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def correct_document_state_opening(request, document_id, episode_id):
    episode = get_object_or_404(
        DocumentStateEpisode, pk=episode_id, document_id=document_id,
    )
    serializer = CorrectEpisodeOpeningSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        episode = correct_opened_at(
            episode, serializer.validated_data['opened_at'], actor=request.user,
        )
    except DocumentStateError as exc:
        return _state_error(exc)
    return Response(DocumentStateEpisodeSerializer(episode).data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def document_state_history(request, document_id):
    get_object_or_404(Document, pk=document_id)
    episodes = (
        DocumentStateEpisode.objects.filter(document_id=document_id)
        .select_related(
            'state__group', 'opened_by', 'closed_by',
        )
        .prefetch_related(
            'events__actor', 'notes__created_by', 'notes__resolved_by',
        )
        .order_by('-updated_at', '-id')
    )
    return Response(DocumentStateEpisodeSerializer(episodes, many=True).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def document_notes(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    if request.method == 'GET':
        notes = document.document_notes.select_related(
            'created_by', 'resolved_by', 'episode',
        )
        return Response(DocumentNoteSerializer(notes, many=True).data)
    serializer = CreateDocumentNoteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        note = create_note(document, actor=request.user, **serializer.validated_data)
    except (DocumentNoteError, DocumentStateError) as exc:
        return _state_error(exc)
    return Response(DocumentNoteSerializer(note).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_document_note(request, document_id, note_id):
    note = get_object_or_404(DocumentNote, pk=note_id, document_id=document_id)
    serializer = UpdateDocumentNoteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        note = update_note(note, **serializer.validated_data)
    except DocumentNoteError as exc:
        return _state_error(exc)
    return Response(DocumentNoteSerializer(note).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def finish_document_note(request, document_id, note_id):
    note = get_object_or_404(DocumentNote, pk=note_id, document_id=document_id)
    serializer = FinishDocumentNoteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        note, transitions = finish_note(
            note, actor=request.user, **serializer.validated_data,
        )
    except (DocumentNoteError, DocumentStateError) as exc:
        return _state_error(exc)
    return Response({
        'note': DocumentNoteSerializer(note).data,
        **transitions,
    })
