"""
Admin endpoints for managing proposal clients (UserProfile, role=client).

These power the new ``/panel/clients`` page, the autocomplete in the proposal
create/edit form, and the orphan-cleanup workflow. They live alongside the
proposal admin views in ``content`` because they share the same auth context
(Django session + ``IsAdminUser``) and URL prefix as the rest of the panel.

Endpoints
---------
- ``GET    /api/proposals/client-profiles/``               list (search, orphans, limit)
- ``GET    /api/proposals/client-profiles/search/?q=``     autocomplete (max 20)
- ``GET    /api/proposals/client-profiles/status-counts/`` per-status counts
- ``GET    /api/proposals/client-profiles/<id>/``          detail with nested proposals
- ``POST   /api/proposals/client-profiles/create/``        standalone create
- ``PATCH  /api/proposals/client-profiles/<id>/update/``   update + cascade snapshots
- ``DELETE /api/proposals/client-profiles/<id>/delete/``   orphan-only delete
"""

import logging

from django.db.models import (
    Count, DateTimeField, Exists, IntegerField, Max, OuterRef, Q, Subquery,
    Sum, Value,
)
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import Project, UserProfile
from accounts.serializers import ProjectListSerializer
from accounts.services import proposal_client_service
from accounts.services.billing_code import (
    billing_code_error,
    normalize_billing_code,
)
from content.models import (
    BusinessProposal, Document, DocumentFolder, EmailLog, HostingRecord,
    IncomeRecord, WebAppDiagnostic,
)
from content.serializers.accounting import (
    HostingRecordSerializer,
    IncomeRecordSerializer,
    money_str,
)
from content.serializers.proposal import ProposalListSerializer
from content.services import accounting_service
from content.serializers.document import ClientDocumentRowSerializer
from content.serializers.proposal_clients import (
    ProposalClientSearchSerializer,
    ProposalClientSerializer,
)
from content.serializers.diagnostic import DiagnosticListSerializer

logger = logging.getLogger(__name__)


def _base_queryset():
    """Return a queryset of client profiles with the standard annotations."""
    return (
        UserProfile.objects.clients()
        .annotate(
            proposals_count=Count('proposals', distinct=True),
            projects_count=Count('user__projects', distinct=True),
            diagnostics_count=Count('web_app_diagnostics', distinct=True),
            last_proposal_at=Max('proposals__last_activity_at'),
            accepted_count=Count(
                'proposals',
                filter=Q(proposals__status__in=['accepted', 'finished']),
                distinct=True,
            ),
            last_status=Subquery(
                BusinessProposal.objects
                .filter(client=OuterRef('pk'))
                .order_by('-last_activity_at')
                .values('status')[:1]
            ),
            last_sent_at=Max('proposals__sent_at'),
            # Subquery, not a fourth Count(distinct=True): three reverse
            # joins already fan out here, and a fourth multiplies the rows
            # every aggregate above has to de-duplicate.
            incomes_count=Coalesce(
                Subquery(
                    IncomeRecord.objects
                    .filter(client=OuterRef('pk'))
                    .order_by()
                    .values('client')
                    .annotate(total=Count('id'))
                    .values('total')[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            hostings_count=Coalesce(
                Subquery(
                    HostingRecord.objects
                    .filter(client=OuterRef('pk'))
                    .order_by()
                    .values('client')
                    .annotate(total=Count('id'))
                    .values('total')[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            # Feeds the "Con hosting cobrado" preset. 'Cobrado' is the same
            # `is_active` the hosting row already renders as "Vigente", so the
            # count here reconciles with what the Hostings tab shows.
            active_hostings_count=Coalesce(
                Subquery(
                    HostingRecord.objects
                    .filter(client=OuterRef('pk'), is_active=True)
                    .order_by()
                    .values('client')
                    .annotate(total=Count('id'))
                    .values('total')[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            # Feeds the "Con proyecto activo" preset. `projects_count` above
            # counts every status, so an archived-only client would pass it;
            # Project.client points at the User, not at this profile.
            active_projects_count=Coalesce(
                Subquery(
                    Project.objects
                    .filter(
                        client=OuterRef('user_id'),
                        status=Project.STATUS_ACTIVE,
                    )
                    .order_by()
                    .values('client')
                    .annotate(total=Count('id'))
                    .values('total')[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            # Feeds the "Con diagnóstico facturado" subfilter, which reads the
            # MONEY rather than the entity: a diagnostic billed without its
            # WebAppDiagnostic ever being created is still billed, and asking
            # for both would hide exactly the rows worth chasing. `lost` is
            # written off, so it never counts; legacy rows carry origin='' and
            # simply do not match.
            diagnostic_incomes_count=Coalesce(
                Subquery(
                    IncomeRecord.objects
                    .filter(
                        client=OuterRef('pk'),
                        origin=IncomeRecord.Origin.DIAGNOSTIC,
                    )
                    .exclude(kind=IncomeRecord.Kind.LOST)
                    .order_by()
                    .values('client')
                    .annotate(total=Count('id'))
                    .values('total')[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            # The commercially valuable cut: a diagnostic no proposal ever
            # followed. Two correlations, one level each — the inner NOT EXISTS
            # binds to the diagnostic row, the outer Subquery to the client;
            # WebAppDiagnostic carries client_id itself, which is what keeps
            # this at OuterRef(...) instead of OuterRef(OuterRef(...)).
            #
            # ~Exists and not __in: BusinessProposal.client is nullable, so one
            # legacy row with a NULL client would make a NOT IN return nothing
            # at all. Anchored on the send rather than on created_at, because
            # created_at is when we opened the draft — a proposal written while
            # the diagnostic still sat unsent cannot be its outcome.
            diagnostics_without_proposal_count=Coalesce(
                Subquery(
                    WebAppDiagnostic.objects
                    .filter(client=OuterRef('pk'))
                    .exclude(status=WebAppDiagnostic.Status.DRAFT)
                    .filter(~Exists(
                        BusinessProposal.objects.filter(
                            client_id=OuterRef('client_id'),
                            created_at__gt=Coalesce(
                                OuterRef('initial_sent_at'),
                                OuterRef('created_at'),
                            ),
                        )
                    ))
                    .order_by()
                    .values('client')
                    .annotate(total=Count('id'))
                    .values('total')[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            # The Emails module counts contact, so all three read the rows
            # addressed to the client. The internal notices about their
            # records are in the modal, marked as such, but a digest that
            # reached the team is not contact with them.
            emails_sent_count=Coalesce(
                Subquery(
                    EmailLog.objects
                    .filter(
                        client=OuterRef('pk'),
                        audience=EmailLog.Audience.CLIENT,
                    )
                    .order_by()
                    .values('client')
                    .annotate(total=Count('id'))
                    .values('total')[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            emails_failed_count=Coalesce(
                Subquery(
                    EmailLog.objects
                    .filter(
                        client=OuterRef('pk'),
                        audience=EmailLog.Audience.CLIENT,
                        status=EmailLog.Status.FAILED,
                    )
                    .order_by()
                    .values('client')
                    .annotate(total=Count('id'))
                    .values('total')[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            # Top-1 rather than Max(): with the (client, audience, sent_at)
            # index this is a backwards scan that stops at the first row, and
            # it carries no GROUP BY. `last_proposal_at` above gets to use
            # Max() because `proposals` is already joined for proposals_count;
            # nothing joins email_logs.
            last_email_at=Subquery(
                EmailLog.objects
                .filter(
                    client=OuterRef('pk'),
                    audience=EmailLog.Audience.CLIENT,
                )
                .order_by('-sent_at')
                .values('sent_at')[:1],
                output_field=DateTimeField(),
            ),
            # The Documents module counts what the manager's list shows for
            # the client: active documents only — archiving is that module's
            # own visibility axis, so the pill reconciles with the list the
            # jump lands on. Document.client_user points at the User.
            documents_count=Coalesce(
                Subquery(
                    Document.objects
                    .filter(client_user=OuterRef('user_id'), is_archived=False)
                    .order_by()
                    .values('client_user')
                    .annotate(total=Count('id'))
                    .values('total')[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            # "A medio asociar": del cliente pero sin proyecto — la lista de
            # revisión que deja la pasada retroactiva.
            documents_no_project_count=Coalesce(
                Subquery(
                    Document.objects
                    .filter(
                        client_user=OuterRef('user_id'),
                        is_archived=False,
                        project__isnull=True,
                    )
                    .order_by()
                    .values('client_user')
                    .annotate(total=Count('id'))
                    .values('total')[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            # "Con carpeta": las carpetas que dicen ser de este cliente. Se
            # cuenta la relación de la carpeta, no las carpetas donde tiene
            # documentos — que una carpeta sea suya es ahora un dato, no una
            # inferencia por el nombre.
            document_folders_count=Coalesce(
                Subquery(
                    DocumentFolder.objects
                    .filter(client_user=OuterRef('user_id'), is_archived=False)
                    .order_by()
                    .values('client_user')
                    .annotate(total=Count('id'))
                    .values('total')[:1],
                    output_field=IntegerField(),
                ),
                Value(0),
            ),
            last_document_at=Subquery(
                Document.objects
                .filter(client_user=OuterRef('user_id'), is_archived=False)
                .order_by('-created_at')
                .values('created_at')[:1],
                output_field=DateTimeField(),
            ),
        )
    )


def _get_profile_or_404(client_id):
    return _base_queryset().filter(pk=client_id).first()


def _parse_bool(raw):
    """Parse a permissive boolean query param. ``None`` means 'unspecified'."""
    if raw is None:
        return None
    return str(raw).strip().lower() in ('1', 'true', 'yes', 'on')


def _billing_code_taken(code, *, exclude_pk=None):
    """Whether another profile already holds ``code`` (the column is unique)."""
    taken = UserProfile.objects.filter(billing_code=code)
    if exclude_pk is not None:
        taken = taken.exclude(pk=exclude_pk)
    return taken.exists()


def _validated_billing_fields(request_data):
    """(nit, billing_code, error_response) for a create payload.

    Checked up front so a duplicate code answers with a 400 the panel can show
    instead of the IntegrityError the unique column would otherwise raise.
    """
    nit = (request_data.get('nit') or '').strip()
    code = normalize_billing_code(request_data.get('billing_code'))
    if code:
        error = billing_code_error(code)
        if error:
            return nit, code, Response(
                {'error': 'invalid_billing_code', 'message': error},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if _billing_code_taken(code):
            return nit, code, Response(
                {
                    'error': 'billing_code_taken',
                    'message': 'Ese código de facturación ya está en uso.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    return nit, code, None


# ---------------------------------------------------------------------------
# List + search
# ---------------------------------------------------------------------------

# The orphan predicate: no proposals, projects, diagnostics, incomes or
# hostings. Matches ``is_orphan`` and the delete guard.
_ORPHAN_PREDICATE = {
    'proposals_count': 0, 'projects_count': 0, 'diagnostics_count': 0,
    'incomes_count': 0, 'hostings_count': 0,
}


def _apply_search(qs, search):
    """Case-insensitive match on email, first/last name and company."""
    if not search:
        return qs
    return qs.filter(
        Q(user__email__icontains=search)
        | Q(user__first_name__icontains=search)
        | Q(user__last_name__icontains=search)
        | Q(company_name__icontains=search)
    )


def _apply_status(qs, *, orphans, inactive):
    """
    Client-status cut, shared by the list and its counts so the number in the
    selector can never disagree with the rows the same selection returns.

    ``orphans`` is tri-state (None = no cut). ``inactive`` is exclusive:
    manually deactivated clients are hidden everywhere except their own tab,
    which is what makes the four options add up to the whole table.
    """
    if orphans is True:
        qs = qs.filter(**_ORPHAN_PREDICATE)
    elif orphans is False:
        qs = qs.exclude(**_ORPHAN_PREDICATE)
    return qs.filter(deactivated_at__isnull=not inactive)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_proposal_clients(request):
    """
    Return all client profiles with annotated proposal counts.

    Query params:
        - ``search``: case-insensitive match on email, first/last name, company.
        - ``orphans``: ``true`` returns only profiles with 0 proposals AND
          0 projects AND 0 diagnostics AND 0 incomes AND 0 hostings
          (matches ``is_orphan`` and the delete guard). ``false`` returns
          the inverse. Omit to include all.
        - ``without_projects``: ``true`` returns only clients with zero
          platform projects (a strictly weaker predicate than ``orphans``);
          ``false`` returns the inverse. Feeds the Projects module indicator.
        - ``inactive``: ``true`` returns only manually deactivated clients.
          Omitted/``false`` excludes them (panel default).
        - ``limit``: max rows to return (default 100, hard cap 500).
    """
    qs = _apply_search(_base_queryset(), (request.query_params.get('search') or '').strip())

    qs = _apply_status(
        qs,
        orphans=_parse_bool(request.query_params.get('orphans')),
        inactive=_parse_bool(request.query_params.get('inactive')) is True,
    )

    without_projects = _parse_bool(request.query_params.get('without_projects'))
    if without_projects is True:
        qs = qs.filter(projects_count=0)
    elif without_projects is False:
        qs = qs.filter(projects_count__gt=0)

    try:
        limit = min(int(request.query_params.get('limit', 100)), 500)
    except (TypeError, ValueError):
        limit = 100

    qs = qs.prefetch_related('proposals').order_by('-last_proposal_at', '-updated_at')[:limit]
    return Response(ProposalClientSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def proposal_client_status_counts(request):
    """
    Match count per client-status option, honouring the same ``search``.

    /panel/clients cuts by status on the server, so it only ever holds the rows
    of the selected one; without this the selector could not label the options
    it is not showing. Counting here (instead of over the loaded rows, like the
    module subfilters do) also keeps the numbers honest past the list's 500-row
    cap.
    """
    qs = _apply_search(_base_queryset(), (request.query_params.get('search') or '').strip())

    def count(**kwargs):
        return _apply_status(qs, **kwargs).count()

    return Response({
        'all': count(orphans=None, inactive=False),
        'active': count(orphans=False, inactive=False),
        'orphans': count(orphans=True, inactive=False),
        'inactive': count(orphans=None, inactive=True),
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def search_proposal_clients(request):
    """Lightweight autocomplete used by the proposal form. Max 20 results."""
    query = (request.query_params.get('q') or '').strip()
    qs = UserProfile.objects.clients()
    if query:
        qs = qs.filter(
            Q(user__email__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(company_name__icontains=query)
        )
    qs = qs.order_by('-updated_at')[:20]
    return Response(ProposalClientSearchSerializer(qs, many=True).data)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_proposal_client(request, client_id):
    """Return a client with everything that belongs to them nested:
    proposals, platform projects, diagnostics, accounting hostings and
    incomes — the one surface that answers "todo sobre este cliente"."""
    profile = _get_profile_or_404(client_id)
    if profile is None:
        return Response(
            {'error': 'client_not_found'}, status=status.HTTP_404_NOT_FOUND,
        )
    payload = ProposalClientSerializer(profile).data
    proposals = (
        profile.proposals
        .select_related('client__user')
        .order_by('-created_at')
    )
    payload['proposals'] = ProposalListSerializer(proposals, many=True).data
    projects = profile.user.projects.select_related('client__profile').order_by('-created_at')
    payload['projects'] = ProjectListSerializer(projects, many=True).data
    diagnostics = profile.web_app_diagnostics.select_related('client__user').order_by('-created_at')
    payload['diagnostics'] = DiagnosticListSerializer(diagnostics, many=True).data

    # select_related + the list annotations keep this per-row-query free:
    # the serializers fall back to one query per row for the client display
    # name and the collection-account flags otherwise.
    hostings = (
        profile.hosting_records
        .select_related('client__user')
        .order_by('-is_active', 'client_name')
    )
    payload['hostings'] = HostingRecordSerializer(hostings, many=True).data
    # What the hostings of this client cost per month, active ones only —
    # the number the per-client view exists to answer.
    payload['hostings_monthly_total'] = money_str(
        hostings.filter(is_active=True).aggregate(
            total=Sum('monthly_value'),
        )['total'] or 0,
    )

    incomes = (
        profile.income_records
        .select_related('client__user')
        .annotate(
            paid_amount=accounting_service.paid_amount_subquery(),
            **accounting_service.collection_account_subqueries(),
        )
        .order_by('-period_date')
    )
    payload['incomes'] = IncomeRecordSerializer(incomes, many=True).data

    # Los últimos 5 alcanzan para la ficha; "Ver todos" salta al módulo de
    # Documentos ya filtrado por el cliente, que es donde se trabaja en serio.
    documents = (
        profile.user.client_documents
        .filter(is_archived=False)
        .select_related('project', 'folder')
        .order_by('-created_at')
    )
    payload['documents'] = ClientDocumentRowSerializer(
        documents[:5], many=True,
    ).data
    payload['documents_total'] = documents.count()
    return Response(payload)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_proposal_client(request):
    """
    Standalone client creation (no proposal yet, no invitation email).

    Body: ``{name, email?, phone?, company?, nit?, billing_code?}``. ``email``
    is optional — when omitted, a placeholder is generated. The billing pair
    matches the edit form field for field, so a client can be filed complete in
    one step instead of being created and immediately edited.
    """
    name = (request.data.get('name') or '').strip()
    email = (request.data.get('email') or '').strip()
    phone = (request.data.get('phone') or '').strip()
    company = (request.data.get('company') or '').strip()

    if not name and not email and not company:
        return Response(
            {'error': 'name_or_email_required',
             'message': 'Debes proporcionar al menos un nombre, email o empresa.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    nit, billing_code, error_response = _validated_billing_fields(request.data)
    if error_response is not None:
        return error_response

    try:
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name=name, email=email, phone=phone, company=company,
            nit=nit, billing_code=billing_code,
        )
    except ValueError as exc:
        return Response(
            {'error': 'invalid_client_data', 'message': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    profile = _get_profile_or_404(profile.pk)
    return Response(
        ProposalClientSerializer(profile).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_proposal_client(request, client_id):
    """Update the client profile + cascade snapshots to all linked proposals."""
    profile = _get_profile_or_404(client_id)
    if profile is None:
        return Response(
            {'error': 'client_not_found'}, status=status.HTTP_404_NOT_FOUND,
        )

    # Billing identity fields live on the profile only (no proposal cascade).
    billing_updates = []
    if 'nit' in request.data:
        profile.nit = (request.data.get('nit') or '').strip()
        billing_updates.append('nit')
    if 'billing_code' in request.data:
        code = normalize_billing_code(request.data.get('billing_code'))
        error = billing_code_error(code) if code else None
        if error:
            return Response(
                {'error': 'invalid_billing_code', 'message': error},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if code and _billing_code_taken(code, exclude_pk=profile.pk):
            return Response(
                {
                    'error': 'billing_code_taken',
                    'message': 'Ese código de facturación ya está en uso.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile.billing_code = code
        billing_updates.append('billing_code')
    if billing_updates:
        profile.save(update_fields=billing_updates)

    payload = {}
    for key in ('name', 'email', 'phone', 'company'):
        if key in request.data:
            payload[key] = request.data[key]
    if 'is_inactive' in request.data:
        payload['is_inactive'] = _parse_bool(request.data.get('is_inactive'))

    if not payload:
        return Response(
            ProposalClientSerializer(profile).data, status=status.HTTP_200_OK,
        )

    try:
        proposal_client_service.update_client_profile(profile, **payload)
    except ValueError as exc:
        return Response(
            {'error': 'update_conflict', 'message': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    profile = _get_profile_or_404(client_id)
    return Response(ProposalClientSerializer(profile).data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_proposal_client(request, client_id):
    """
    Delete a client (and the underlying ``User``) only if it has zero
    proposals and zero platform projects. Returns 400 with a machine-readable
    error code otherwise.
    """
    profile = _get_profile_or_404(client_id)
    if profile is None:
        return Response(
            {'error': 'client_not_found'}, status=status.HTTP_404_NOT_FOUND,
        )

    try:
        proposal_client_service.delete_orphan_client(profile)
    except ValueError as exc:
        # Service raises ``ValueError('client_has_proposals:N')`` etc.
        code, _, count = str(exc).partition(':')
        return Response(
            {'error': code, 'count': int(count) if count.isdigit() else None},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(status=status.HTTP_204_NO_CONTENT)
