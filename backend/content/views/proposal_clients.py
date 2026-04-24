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
- ``GET    /api/proposals/client-profiles/<id>/``          detail with nested proposals
- ``POST   /api/proposals/client-profiles/create/``        standalone create
- ``PATCH  /api/proposals/client-profiles/<id>/update/``   update + cascade snapshots
- ``DELETE /api/proposals/client-profiles/<id>/delete/``   orphan-only delete
"""

import logging

from django.db.models import Count, Max, OuterRef, Q, Subquery
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import UserProfile
from accounts.serializers import ProjectListSerializer
from accounts.services import proposal_client_service
from content.models import BusinessProposal
from content.serializers.proposal import ProposalListSerializer
from content.serializers.proposal_clients import (
    ProposalClientSearchSerializer,
    ProposalClientSerializer,
)
from content.serializers.diagnostic import DiagnosticListSerializer

logger = logging.getLogger(__name__)


def _base_queryset():
    """Return a queryset of client profiles with the standard annotations."""
    return (
        UserProfile.objects
        .filter(role=UserProfile.ROLE_CLIENT)
        .select_related('user')
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
        )
    )


def _get_profile_or_404(client_id):
    return _base_queryset().filter(pk=client_id).first()


def _parse_bool(raw):
    """Parse a permissive boolean query param. ``None`` means 'unspecified'."""
    if raw is None:
        return None
    return str(raw).strip().lower() in ('1', 'true', 'yes', 'on')


# ---------------------------------------------------------------------------
# List + search
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_proposal_clients(request):
    """
    Return all client profiles with annotated proposal counts.

    Query params:
        - ``search``: case-insensitive match on email, first/last name, company.
        - ``orphans``: ``true`` returns only profiles with 0 proposals AND
          0 projects. ``false`` returns the inverse. Omit to include all.
        - ``limit``: max rows to return (default 100, hard cap 500).
    """
    qs = _base_queryset()

    search = (request.query_params.get('search') or '').strip()
    if search:
        qs = qs.filter(
            Q(user__email__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(company_name__icontains=search)
        )

    orphans = _parse_bool(request.query_params.get('orphans'))
    if orphans is True:
        qs = qs.filter(proposals_count=0, projects_count=0)
    elif orphans is False:
        qs = qs.exclude(proposals_count=0, projects_count=0)

    try:
        limit = min(int(request.query_params.get('limit', 100)), 500)
    except (TypeError, ValueError):
        limit = 100

    qs = qs.prefetch_related('proposals').order_by('-last_proposal_at', '-updated_at')[:limit]
    return Response(ProposalClientSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def search_proposal_clients(request):
    """Lightweight autocomplete used by the proposal form. Max 20 results."""
    query = (request.query_params.get('q') or '').strip()
    qs = (
        UserProfile.objects
        .filter(role=UserProfile.ROLE_CLIENT)
        .select_related('user')
    )
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
    """Return a single client with proposals, platform projects, and diagnostics nested."""
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
    return Response(payload)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_proposal_client(request):
    """
    Standalone client creation (no proposal yet, no invitation email).

    Body: ``{name, email?, phone?, company?}``. ``email`` is optional —
    when omitted, a placeholder is generated.
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

    try:
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name=name, email=email, phone=phone, company=company,
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

    payload = {}
    for key in ('name', 'email', 'phone', 'company'):
        if key in request.data:
            payload[key] = request.data[key]

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
