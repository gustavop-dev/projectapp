"""Admin APIs for the Project lifecycle catalog and transition history."""

from difflib import SequenceMatcher

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import Project
from content.models import (
    DocumentState,
    DocumentStateEpisode,
    DocumentStateGroup,
)
from content.models.document_state import normalize_document_state_name
from content.serializers.document_state import (
    DocumentStateEpisodeSerializer,
    DocumentStateGroupSerializer,
    DocumentStateSerializer,
)
from content.serializers.panel_projects import (
    PanelProjectSerializer,
    ProjectTransitionApplySerializer,
    ProjectTransitionPreviewSerializer,
)
from content.services.document_state_service import DocumentStateError, retire_state
from content.services.project_state_service import (
    ProjectStateError,
    apply_transition,
    merge_project_states,
    preview_transition,
)


def _error(exc, http_status=status.HTTP_400_BAD_REQUEST):
    return Response(
        {'detail': str(exc), 'code': getattr(exc, 'code', 'invalid_operation')},
        status=http_status,
    )


def _catalog(include_retired=False):
    queryset = (
        DocumentState.objects.filter(
            catalog=DocumentStateGroup.Catalog.PROJECTS,
        )
        .select_related('group', 'merged_into')
        .prefetch_related('incompatibilities')
        .annotate(
            active_project_count=Count(
                'current_projects',
                distinct=True,
            ),
            historical_episode_count=Count(
                'episodes',
                filter=Q(episodes__project__isnull=False),
                distinct=True,
            ),
        )
        .order_by('group__order', 'order', 'name')
    )
    if not include_retired:
        queryset = queryset.filter(is_active=True, merged_into__isnull=True)
    return queryset


def _similar_states(query):
    normalized = normalize_document_state_name(query)
    if not normalized:
        return []
    matches = []
    for state in _catalog():
        score = SequenceMatcher(None, normalized, state.normalized_name).ratio()
        if normalized in state.normalized_name or score >= 0.65:
            matches.append((score, state))
    matches.sort(key=lambda item: (-item[0], item[1].name.casefold()))
    return [
        {**DocumentStateSerializer(state).data, 'similarity': round(score, 3)}
        for score, state in matches[:5]
    ]


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def project_state_groups(request):
    if request.method == 'GET':
        groups = DocumentStateGroup.objects.filter(
            catalog=DocumentStateGroup.Catalog.PROJECTS,
        ).annotate(
            state_count=Count('states', filter=Q(states__is_active=True)),
        )
        return Response(DocumentStateGroupSerializer(groups, many=True).data)
    payload = request.data.copy()
    payload['catalog'] = DocumentStateGroup.Catalog.PROJECTS
    payload['selection_mode'] = DocumentStateGroup.SelectionMode.EXCLUSIVE
    serializer = DocumentStateGroupSerializer(data=payload)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def project_states(request):
    if request.method == 'GET':
        include_retired = str(
            request.query_params.get('include_retired') or '',
        ).lower() in ('1', 'true', 'yes')
        return Response(DocumentStateSerializer(
            _catalog(include_retired=include_retired),
            many=True,
        ).data)

    payload = request.data.copy()
    confirm_similar = bool(payload.pop('confirm_similar', False))
    payload['catalog'] = DocumentStateGroup.Catalog.PROJECTS
    if not payload.get('group'):
        group = DocumentStateGroup.objects.filter(
            catalog=DocumentStateGroup.Catalog.PROJECTS,
            selection_mode=DocumentStateGroup.SelectionMode.EXCLUSIVE,
            is_active=True,
        ).order_by('order', 'id').first()
        if not group:
            return Response(
                {'group': 'No hay un grupo de ciclo disponible.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload['group'] = group.pk
    suggestions = _similar_states(payload.get('name', ''))
    if suggestions and not confirm_similar:
        return Response({
            'detail': 'Hay estados parecidos. Revisa antes de crear otro.',
            'code': 'similar_states',
            'suggestions': suggestions,
        }, status=status.HTTP_409_CONFLICT)
    serializer = DocumentStateSerializer(data=payload)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(created_by=request.user, updated_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def project_state_suggestions(request):
    return Response(_similar_states(request.query_params.get('q', '')))


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_project_state(request, state_id):
    state = get_object_or_404(
        DocumentState.objects.select_related('group'),
        pk=state_id,
        catalog=DocumentStateGroup.Catalog.PROJECTS,
    )
    if (
        'operational_effect' in request.data
        and request.data['operational_effect'] != state.operational_effect
        and state.current_projects.exists()
    ):
        return Response({
            'detail': 'Mueve primero los proyectos que usan este estado.',
            'code': 'state_effect_in_use',
        }, status=status.HTTP_409_CONFLICT)
    payload = request.data.copy()
    payload['catalog'] = DocumentStateGroup.Catalog.PROJECTS
    serializer = DocumentStateSerializer(state, data=payload, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(updated_by=request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def retire_project_state(request, state_id):
    state = get_object_or_404(
        DocumentState,
        pk=state_id,
        catalog=DocumentStateGroup.Catalog.PROJECTS,
    )
    try:
        retire_state(state, actor=request.user)
    except DocumentStateError as exc:
        return _error(exc, status.HTTP_409_CONFLICT)
    return Response(DocumentStateSerializer(state).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def merge_project_state(request, state_id):
    source = get_object_or_404(
        DocumentState,
        pk=state_id,
        catalog=DocumentStateGroup.Catalog.PROJECTS,
    )
    target = get_object_or_404(
        DocumentState,
        pk=request.data.get('target_state_id'),
        catalog=DocumentStateGroup.Catalog.PROJECTS,
    )
    try:
        merge_project_states(source, target, actor=request.user)
    except ProjectStateError as exc:
        return _error(exc, status.HTTP_409_CONFLICT)
    return Response(DocumentStateSerializer(source).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def preview_project_state_transition(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related('current_state'),
        pk=project_id,
    )
    serializer = ProjectTransitionPreviewSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        payload = preview_transition(
            project,
            serializer.validated_data['state'],
            effective_at=serializer.validated_data.get('effective_at'),
        )
    except ProjectStateError as exc:
        return _error(exc)
    return Response(payload)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def apply_project_state_transition(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    serializer = ProjectTransitionApplySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data
    try:
        project, episode = apply_transition(
            project,
            data['state'],
            actor=request.user,
            impact_token=data['impact_token'],
            effective_at=data.get('effective_at'),
            note=data.get('note', ''),
            resolutions=data.get('resolutions', []),
        )
    except ProjectStateError as exc:
        code_status = (
            status.HTTP_409_CONFLICT
            if exc.code in (
                'stale_transition_preview',
                'pending_incomes',
                'pending_hosting_payments',
                'income_resolutions_required',
            )
            else status.HTTP_400_BAD_REQUEST
        )
        return _error(exc, code_status)
    return Response({
        'project': PanelProjectSerializer(project).data,
        'episode': DocumentStateEpisodeSerializer(episode).data,
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def project_state_history(request, project_id):
    get_object_or_404(Project, pk=project_id)
    episodes = (
        DocumentStateEpisode.objects.filter(project_id=project_id)
        .select_related('state__group', 'opened_by', 'closed_by')
        .prefetch_related('events__actor')
        .order_by('-updated_at', '-id')
    )
    return Response(DocumentStateEpisodeSerializer(episodes, many=True).data)
