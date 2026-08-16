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
- ``GET   /api/projects/<id>/unlinked-records/``  assign preview (PA-51)
- ``POST  /api/projects/<id>/assign-unlinked/``   assign confirmed ids (PA-51)
"""

import logging

from django.db.models import (
    Count, Exists, IntegerField, OuterRef, Q, Subquery, Value,
)
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import Project, UserProfile
from content.api_errors import error_response
from content.models import AccountingChangeLog, HostingRecord, IncomeRecord
from content.serializers.accounting import (
    HostingRecordSerializer,
    IncomeRecordSerializer,
    month_label,
)
from content.serializers.panel_projects import (
    CreatePanelProjectSerializer,
    PanelProjectSerializer,
    ProjectAssignUnlinkedSerializer,
    UpdatePanelProjectSerializer,
)
from content.services import accounting_service

EntityType = AccountingChangeLog.EntityType

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


def _unlinked_count_for(model):
    """Per-project count of the CLIENT's records still without a project.

    "Unlinked" reads from the record's own FK (``project IS NULL``) scoped to
    the project's client — the completion backlog the assign flow works on.
    A client with several projects repeats the number on each of their rows
    on purpose: the backlog belongs to the client, not to one project.
    """
    return Coalesce(
        Subquery(
            model.objects
            .filter(client__user_id=OuterRef('client_id'), project__isnull=True)
            .order_by()
            .values('client__user_id')
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
            unlinked_hostings_count=_unlinked_count_for(HostingRecord),
            unlinked_incomes_count=_unlinked_count_for(IncomeRecord),
        )
        .order_by('name')
    )


def _records_without_project_count():
    """Global backlog: accounting records with a client but no project.

    Client-less rows are excluded — without a client there is no project to
    propose (ownership is per client), and the module's own docs treat an
    empty project as a legitimate state, not pending work.
    """
    return (
        HostingRecord.objects
        .filter(client__isnull=False, project__isnull=True).count()
        + IncomeRecord.objects
        .filter(client__isnull=False, project__isnull=True).count()
    )


def _unlinked_qs(model, project):
    """The project's assignable set: its client's rows with no project yet."""
    return model.objects.filter(
        client__user=project.client, project__isnull=True,
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
        return error_response(
            "scope debe ser 'active', 'archived' o 'all'.",
            code='invalid_scope',
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
            'records_without_project': _records_without_project_count(),
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
        return error_response(
            'El cliente de un proyecto no se puede cambiar desde el panel.',
            code='client_immutable',
        )
    if project.status == Project.STATUS_ARCHIVED:
        # Documents precedent: an archived row is out of circulation.
        return error_response(
            'Restaura el proyecto para editarlo.',
            code='project_archived',
            hint='Usa Restaurar en la pestaña Archivados.',
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
        return error_response(
            'El proyecto ya está archivado.', code='already_archived',
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
        return error_response(
            'El proyecto no está archivado.', code='not_archived',
        )
    project.status = Project.STATUS_ACTIVE
    project.save(update_fields=['status', 'updated_at'])
    return Response(_annotated_row(project.pk))


def _archived_assign_error():
    return error_response(
        'Restaura el proyecto para asignarle registros.',
        code='project_archived',
        hint='Usa Restaurar en la pestaña Archivados.',
    )


def _unlinked_payload(project):
    """The visible plan: every assignable record, labelled for a human.

    Hostings lean on ``display_label`` (client — project — domain fallback);
    incomes carry concept plus kind and period so two same-concept rows stay
    distinguishable in the confirmation list.
    """
    hostings = [
        {'id': record.pk, 'label': record.display_label}
        for record in _unlinked_qs(HostingRecord, project)
    ]
    incomes = [
        {
            'id': record.pk,
            'label': record.concept,
            'kind_label': record.get_kind_display(),
            'period_label': month_label(record.period_date),
        }
        for record in _unlinked_qs(IncomeRecord, project)
    ]
    return {
        'client': PanelProjectSerializer().get_client(project),
        'hostings': hostings,
        'incomes': incomes,
        'total': len(hostings) + len(incomes),
    }


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_project_unlinked_records(request, project_id):
    """Preview for the assign flow: the client's records without a project.

    This is the list the operator confirms against — the apply endpoint
    receives these ids back, so nothing is ever assigned sight unseen.
    """
    project = get_object_or_404(Project, pk=project_id)
    if project.status == Project.STATUS_ARCHIVED:
        return _archived_assign_error()
    return Response(_unlinked_payload(project))


@api_view(['POST'])
@permission_classes([IsAdminUser])
def assign_project_unlinked_records(request, project_id):
    """Assign this project to the confirmed subset of its client's
    unlinked records.

    Explicit ids: what was confirmed is what runs. Ids that no longer exist
    → 409 ``records_not_found``; ids that stopped being assignable (they
    gained a project, or belong to another client) → 409 ``records_changed``.
    Both run before the service, so its atomic block never opens on a stale
    plan — the same contract as the accounting bulk-assign.
    """
    project = get_object_or_404(Project, pk=project_id)
    if project.status == Project.STATUS_ARCHIVED:
        return _archived_assign_error()

    serializer = ProjectAssignUnlinkedSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    hosting_ids = serializer.validated_data['hosting_ids']
    income_ids = serializer.validated_data['income_ids']

    missing = (
        accounting_service.missing_record_ids(EntityType.HOSTING, hosting_ids)
        + accounting_service.missing_record_ids(EntityType.INCOME, income_ids)
    )
    if missing:
        count = len(missing)
        verb = 'existe' if count == 1 else 'existen'
        return error_response(
            f'{count} de los registros seleccionados ya no {verb}.',
            code='records_not_found',
            hint='La lista se actualizó. Revísala y vuelve a intentarlo.',
            status=status.HTTP_409_CONFLICT,
            errors={'missing_ids': missing},
        )

    changed = sorted(
        (
            set(hosting_ids)
            - set(_unlinked_qs(HostingRecord, project)
                  .filter(pk__in=hosting_ids).values_list('pk', flat=True))
        )
        | (
            set(income_ids)
            - set(_unlinked_qs(IncomeRecord, project)
                  .filter(pk__in=income_ids).values_list('pk', flat=True))
        )
    )
    if changed:
        count = len(changed)
        noun = 'registro' if count == 1 else 'registros'
        return error_response(
            f'{count} {noun} de la lista ya no se pueden asignar '
            '(ganaron proyecto o cambiaron de cliente).',
            code='records_changed',
            hint='La lista se actualizó. Revísala y vuelve a intentarlo.',
            status=status.HTTP_409_CONFLICT,
            errors={'changed_ids': changed},
        )

    assigned_hostings = accounting_service.bulk_assign_project(
        EntityType.HOSTING, hosting_ids, project, request.user,
    ) if hosting_ids else []
    assigned_incomes = accounting_service.bulk_assign_project(
        EntityType.INCOME, income_ids, project, request.user,
    ) if income_ids else []
    logger.info(
        'Panel project %s assigned to %s hostings and %s incomes',
        project.pk, len(assigned_hostings), len(assigned_incomes),
    )
    # The cascade also rewrites the liquid children of an assigned expected
    # income; without them in the response the panel would map-replace the
    # parent and keep a stale child row. The counts stay parents-only — they
    # answer for the plan the operator confirmed.
    expected_pks = [
        record.pk for record in assigned_incomes
        if record.kind == IncomeRecord.Kind.EXPECTED
    ]
    income_rows = IncomeRecord.objects.filter(
        Q(pk__in=[record.pk for record in assigned_incomes])
        | Q(expected_income_id__in=expected_pks),
    )
    return Response({
        'assigned_hostings': len(assigned_hostings),
        'assigned_incomes': len(assigned_incomes),
        # Full rows, not just counts: an accounting tab open in the SPA
        # rebuilds from these instead of showing the stale "—" project cell.
        # Bounded by construction — only the confirmed preview ids run.
        'hostings': HostingRecordSerializer(assigned_hostings, many=True).data,
        'incomes': IncomeRecordSerializer(income_rows, many=True).data,
        'project': _annotated_row(project.pk),
    })
