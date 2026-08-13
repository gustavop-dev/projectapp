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
- ``GET /api/projects/``  listing with scope, counts and header meta
"""

import logging

from django.db.models import (
    Count, Exists, IntegerField, OuterRef, Subquery, Value,
)
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import Project, UserProfile
from content.models import HostingRecord, IncomeRecord
from content.serializers.panel_projects import PanelProjectSerializer

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
