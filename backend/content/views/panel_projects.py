"""Panel endpoints for the Projects module (Plataforma space).

``/panel/projects`` is the commercial face of ``accounts.Project``: the
platform (JWT) side keeps its own CRUD under ``/api/accounts/projects/``,
while these views speak the panel's language — Django session +
``IsAdminUser`` (the same tier as ``/panel/clients``, which already nests
hostings and incomes per client) and UserProfile ids for the client.

The accounting picker ``GET /api/accounting/projects/`` stays untouched:
it is superuser-scoped and shaped for a dropdown, not for administration.

Endpoints
---------
- ``GET   /api/projects/``                        listing with scope, counts, meta
- ``POST  /api/projects/create/``                 PA-38 minimum create
- ``PATCH /api/projects/<id>/update/``            name/description/status
- ``PATCH /api/projects/<id>/archive/``           status -> archived (PA-29)
- ``PATCH /api/projects/<id>/unarchive/``         status -> active
"""

import logging

from django.db.models import (
    Count, Exists, IntegerField, OuterRef, Subquery, Value,
)
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import Project, UserProfile
from content.models import HostingRecord, IncomeRecord
from content.serializers.panel_projects import (
    CreatePanelProjectSerializer,
    PanelProjectSerializer,
    UpdatePanelProjectSerializer,
)

logger = logging.getLogger(__name__)

_SCOPES = ('active', 'archived', 'all')


def _count_for(model):
    """Per-project row count as a Subquery annotation.

    Subquery instead of stacked ``Count(distinct=True)`` — same lesson as
    the clients list: parallel reverse joins multiply the rows every other
    aggregate then has to de-duplicate.
    """
    return Coalesce(
        Subquery(
            model.objects
            .filter(project=OuterRef('pk'))
            .order_by()
            .values('project')
            .annotate(total=Count('id'))
            .values('total')[:1],
            output_field=IntegerField(),
        ),
        Value(0),
    )


def _annotated_queryset():
    """Projects with the counts the listing shows, ordered for the table."""
    return (
        Project.objects
        .select_related('client__profile')
        .annotate(
            hostings_count=_count_for(HostingRecord),
            incomes_count=_count_for(IncomeRecord),
        )
        .order_by('name')
    )


def _clients_without_projects_count():
    """How many visible clients still have no project registered.

    ``.clients()`` plus the deactivated filter mirror the ``/panel/clients``
    default, so this number matches the list the module's indicator opens.
    """
    return (
        UserProfile.objects.clients()
        .filter(deactivated_at__isnull=True)
        .filter(~Exists(Project.objects.filter(client_id=OuterRef('user_id'))))
        .count()
    )


def _scope_or_none(request):
    """Scope pedido: 'active' (default), 'archived' o 'all'. None si es inválido.

    El parámetro selecciona datos, así que un valor inválido responde 400 —
    el mismo criterio que el scope del archivo de documentos.
    """
    raw = str(request.query_params.get('scope') or '').strip().lower()
    if not raw:
        return 'active'
    return raw if raw in _SCOPES else None


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_panel_projects(request):
    """Full project listing for the module: rows plus header meta.

    Query params:
        - ``scope``: ``active`` (default — everything not archived, paused
          and completed included), ``archived`` or ``all``.
    """
    scope = _scope_or_none(request)
    if scope is None:
        return Response(
            {
                'error': 'invalid_scope',
                'message': "scope debe ser 'active', 'archived' o 'all'.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    qs = _annotated_queryset()
    if scope == 'active':
        qs = qs.exclude(status=Project.STATUS_ARCHIVED)
    elif scope == 'archived':
        qs = qs.filter(status=Project.STATUS_ARCHIVED)

    total = Project.objects.count()
    archived = Project.objects.filter(status=Project.STATUS_ARCHIVED).count()
    return Response({
        'results': PanelProjectSerializer(qs, many=True).data,
        'meta': {
            'total': total,
            'active': total - archived,
            'archived': archived,
            'clients_without_projects': _clients_without_projects_count(),
        },
    })


def _annotated_row(project_id):
    """The listing-format row for one project — what every mutation answers."""
    return PanelProjectSerializer(_annotated_queryset().get(pk=project_id)).data


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_panel_project(request):
    serializer = CreatePanelProjectSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    project = serializer.save()
    logger.info(
        'Panel project %s created for client profile %s',
        project.pk, serializer.client_profile.pk,
    )
    return Response(_annotated_row(project.pk), status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_panel_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if 'client_profile_id' in request.data or 'client' in request.data:
        return Response(
            {
                'error': 'client_immutable',
                'message': 'El cliente de un proyecto no se puede cambiar desde el panel.',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if project.status == Project.STATUS_ARCHIVED:
        # Documents precedent: an archived row is out of circulation.
        return Response(
            {
                'error': 'project_archived',
                'message': 'Restaura el proyecto para editarlo.',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer = UpdatePanelProjectSerializer(
        project, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(_annotated_row(project.pk))


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def archive_panel_project(request, project_id):
    """Archive, never delete (PA-29): the accounting FKs stay in place and
    the row just leaves the active scope."""
    project = get_object_or_404(Project, pk=project_id)
    if project.status == Project.STATUS_ARCHIVED:
        return Response(
            {
                'error': 'already_archived',
                'message': 'El proyecto ya está archivado.',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    project.status = Project.STATUS_ARCHIVED
    project.save(update_fields=['status', 'updated_at'])
    return Response(_annotated_row(project.pk))


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def unarchive_panel_project(request, project_id):
    """Back to circulation — always to ``active``: the pre-archive status is
    not recorded (v1 trade-off, documented in the module plan)."""
    project = get_object_or_404(Project, pk=project_id)
    if project.status != Project.STATUS_ARCHIVED:
        return Response(
            {
                'error': 'not_archived',
                'message': 'El proyecto no está archivado.',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    project.status = Project.STATUS_ACTIVE
    project.save(update_fields=['status', 'updated_at'])
    return Response(_annotated_row(project.pk))
