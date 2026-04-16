"""Admin + public DRF views for the WebAppDiagnostic feature.

All admin endpoints use Django session auth + IsAdminUser. The 3 public
endpoints (`retrieve`, `track`, `respond`) use AllowAny + UUID lookup.
"""

import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from accounts.models import UserProfile
from content.models import DiagnosticDocument, WebAppDiagnostic
from content.serializers.diagnostic import (
    DiagnosticDetailSerializer,
    DiagnosticDocumentSerializer,
    DiagnosticDocumentUpdateSerializer,
    DiagnosticListSerializer,
    DiagnosticUpdateSerializer,
    PublicDiagnosticSerializer,
)
from content.services import diagnostic_service

logger = logging.getLogger(__name__)


def _admin_qs():
    return (
        WebAppDiagnostic.objects
        .select_related('client__user')
        .prefetch_related('documents')
    )


# ──────────────────────────────────────────────────────────────────────────
# Admin — list / create / detail / update
# ──────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_diagnostics(request):
    qs = _admin_qs()
    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)
    client_id = request.query_params.get('client')
    if client_id:
        qs = qs.filter(client_id=client_id)
    return Response(DiagnosticListSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_diagnostic(request):
    client_id = request.data.get('client_id')
    if not client_id:
        return Response(
            {'error': 'client_id_required'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    client = UserProfile.objects.filter(
        pk=client_id, role=UserProfile.ROLE_CLIENT,
    ).first()
    if client is None:
        return Response(
            {'error': 'client_not_found'},
            status=http_status.HTTP_404_NOT_FOUND,
        )

    language = (request.data.get('language') or 'es').lower()
    if language not in ('es', 'en'):
        language = 'es'
    title = (request.data.get('title') or '').strip()

    diagnostic = diagnostic_service.create_diagnostic(
        client=client,
        language=language,
        title=title,
        created_by=request.user if request.user.is_authenticated else None,
    )
    diagnostic = _admin_qs().get(pk=diagnostic.pk)
    return Response(
        DiagnosticDetailSerializer(diagnostic).data,
        status=http_status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_diagnostic(request, diagnostic_id):
    diagnostic = get_object_or_404(_admin_qs(), pk=diagnostic_id)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_diagnostic(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    serializer = DiagnosticUpdateSerializer(
        diagnostic, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors,
                        status=http_status.HTTP_400_BAD_REQUEST)
    serializer.save()
    diagnostic = _admin_qs().get(pk=diagnostic.pk)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_diagnostic(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    diagnostic.delete()
    return Response(status=http_status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────
# Admin — per-document edits
# ──────────────────────────────────────────────────────────────────────────

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_diagnostic_document(request, diagnostic_id, doc_id):
    doc = get_object_or_404(
        DiagnosticDocument.objects.select_related('diagnostic'),
        pk=doc_id, diagnostic_id=diagnostic_id,
    )
    serializer = DiagnosticDocumentUpdateSerializer(
        doc, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors,
                        status=http_status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(DiagnosticDocumentSerializer(doc).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def restore_diagnostic_document(request, diagnostic_id, doc_id):
    doc = get_object_or_404(
        DiagnosticDocument.objects.select_related('diagnostic'),
        pk=doc_id, diagnostic_id=diagnostic_id,
    )
    diagnostic_service.restore_document_from_template(doc)
    return Response(DiagnosticDocumentSerializer(doc).data)


# ──────────────────────────────────────────────────────────────────────────
# Admin — send actions
# ──────────────────────────────────────────────────────────────────────────

def _send_and_transition(diagnostic, kind: str):
    """Run email + status transition. Returns (ok: bool, error_response).

    Email errors are logged but do not abort the transition — the public link
    works regardless of email delivery (admin can resend manually).
    """
    from content.services.diagnostic_email_service import (
        DiagnosticEmailService,
    )

    # Both the initial and final sends land on Status.SENT; the service
    # distinguishes them by checking whether `initial_sent_at` is already set.
    if kind == 'initial':
        target = WebAppDiagnostic.Status.SENT
        email_fn = DiagnosticEmailService.send_initial_to_client
    elif kind == 'final':
        target = WebAppDiagnostic.Status.SENT
        email_fn = DiagnosticEmailService.send_final_to_client
    else:
        return False, Response({'error': 'unknown_kind'},
                               status=http_status.HTTP_400_BAD_REQUEST)

    try:
        diagnostic_service.transition_status(diagnostic, target)
    except ValueError as exc:
        return False, Response(
            {'error': str(exc).split(':')[0],
             'message': str(exc)},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    try:
        email_fn(diagnostic)
    except Exception:
        logger.exception('Email send failed for diagnostic %s (%s)',
                         diagnostic.uuid, kind)

    return True, None


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_initial(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    ok, err = _send_and_transition(diagnostic, 'initial')
    if not ok:
        return err
    diagnostic = _admin_qs().get(pk=diagnostic.pk)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def mark_in_analysis(request, diagnostic_id):
    """Manual transition SENT → NEGOTIATING once the client authorized."""
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    try:
        diagnostic_service.transition_status(
            diagnostic, WebAppDiagnostic.Status.NEGOTIATING,
        )
    except ValueError as exc:
        return Response(
            {'error': str(exc).split(':')[0], 'message': str(exc)},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    diagnostic = _admin_qs().get(pk=diagnostic.pk)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_final(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    ok, err = _send_and_transition(diagnostic, 'final')
    if not ok:
        return err
    diagnostic = _admin_qs().get(pk=diagnostic.pk)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


# ──────────────────────────────────────────────────────────────────────────
# Public — view / track / respond
# ──────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_public_diagnostic(request, diagnostic_uuid):
    diagnostic = get_object_or_404(
        WebAppDiagnostic.objects.select_related('client__user')
        .prefetch_related('documents'),
        uuid=diagnostic_uuid,
    )
    if diagnostic.status in diagnostic_service.PUBLIC_VISIBLE_STATUSES:
        diagnostic_service.register_view(diagnostic)
    return Response(PublicDiagnosticSerializer(diagnostic).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def track_public_diagnostic(request, diagnostic_uuid):
    diagnostic = get_object_or_404(WebAppDiagnostic, uuid=diagnostic_uuid)
    diagnostic_service.register_view(diagnostic)
    return Response({'view_count': diagnostic.view_count})


@api_view(['POST'])
@permission_classes([AllowAny])
def respond_public_diagnostic(request, diagnostic_uuid):
    diagnostic = get_object_or_404(WebAppDiagnostic, uuid=diagnostic_uuid)
    decision = (request.data.get('decision') or '').strip().lower()
    if decision not in ('accept', 'reject'):
        return Response(
            {'error': 'invalid_decision'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    target = (
        WebAppDiagnostic.Status.ACCEPTED
        if decision == 'accept'
        else WebAppDiagnostic.Status.REJECTED
    )
    try:
        diagnostic_service.transition_status(diagnostic, target)
    except ValueError as exc:
        return Response(
            {'error': str(exc).split(':')[0], 'message': str(exc)},
            status=http_status.HTTP_409_CONFLICT,
        )
    return Response(PublicDiagnosticSerializer(diagnostic).data)
