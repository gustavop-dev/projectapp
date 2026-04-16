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
from content.models import (
    DiagnosticAttachment, DiagnosticDocument, WebAppDiagnostic,
)
from content.serializers.diagnostic import (
    DiagnosticDetailSerializer,
    DiagnosticDocumentSerializer,
    DiagnosticDocumentUpdateSerializer,
    DiagnosticListSerializer,
    DiagnosticUpdateSerializer,
    PublicDiagnosticSerializer,
    serialize_diagnostic_attachment,
)
from content.services import diagnostic_service

logger = logging.getLogger(__name__)


def _admin_qs(include_attachments=False):
    qs = (
        WebAppDiagnostic.objects
        .select_related('client__user')
        .prefetch_related('documents')
    )
    if include_attachments:
        qs = qs.prefetch_related('attachments')
    return qs


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
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    return Response(
        DiagnosticDetailSerializer(diagnostic).data,
        status=http_status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_diagnostic(request, diagnostic_id):
    diagnostic = get_object_or_404(_admin_qs(include_attachments=True), pk=diagnostic_id)
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
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
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
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
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
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_final(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    ok, err = _send_and_transition(diagnostic, 'final')
    if not ok:
        return err
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
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


# ──────────────────────────────────────────────────────────────────────────
# Admin — attachments (files uploaded to a diagnostic)
# ──────────────────────────────────────────────────────────────────────────

_ATTACHMENT_ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg',
}
_ATTACHMENT_MAX_SIZE = 15 * 1024 * 1024  # 15 MB


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_diagnostic_attachments(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    return Response(
        [serialize_diagnostic_attachment(a)
         for a in diagnostic.attachments.all()],
    )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def upload_diagnostic_attachment(request, diagnostic_id):
    from pathlib import Path

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file provided.'},
                        status=http_status.HTTP_400_BAD_REQUEST)

    ext = Path(file.name).suffix.lower()
    if ext not in _ATTACHMENT_ALLOWED_EXTENSIONS:
        allowed = ', '.join(sorted(_ATTACHMENT_ALLOWED_EXTENSIONS))
        return Response(
            {'error': f'File type {ext} not allowed. Allowed: {allowed}'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    if file.size > _ATTACHMENT_MAX_SIZE:
        return Response(
            {'error': 'File too large. Maximum size is 15 MB.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    document_type = request.data.get(
        'document_type', DiagnosticAttachment.DOC_TYPE_OTHER,
    )
    valid_types = {c[0] for c in DiagnosticAttachment.DOC_TYPE_CHOICES}
    if document_type not in valid_types:
        return Response(
            {'error': f'Invalid document_type: {document_type}'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    title = (request.data.get('title') or file.name).strip()[:300] or file.name
    custom_type_label = (request.data.get('custom_type_label') or '').strip()[:100]

    attachment = DiagnosticAttachment.objects.create(
        diagnostic=diagnostic,
        document_type=document_type,
        title=title,
        file=file,
        custom_type_label=(
            custom_type_label
            if document_type == DiagnosticAttachment.DOC_TYPE_OTHER
            else ''
        ),
        uploaded_by=request.user if request.user.is_authenticated else None,
    )
    return Response(
        serialize_diagnostic_attachment(attachment),
        status=http_status.HTTP_201_CREATED,
    )


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_diagnostic_attachment(request, diagnostic_id, attachment_id):
    attachment = get_object_or_404(
        DiagnosticAttachment,
        pk=attachment_id, diagnostic_id=diagnostic_id,
    )
    if attachment.file:
        attachment.file.delete(save=False)
    attachment.delete()
    return Response(status=http_status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_diagnostic_attachments(request, diagnostic_id):
    """Email selected DiagnosticAttachments to the client."""
    from content.services import diagnostic_documents_service

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)

    attachment_ids = request.data.get('attachment_ids') or []
    if not isinstance(attachment_ids, list) or not attachment_ids:
        return Response(
            {'error': 'Debes seleccionar al menos un documento.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    ok, error = diagnostic_documents_service.send_attachments_to_client(
        diagnostic,
        attachment_ids=attachment_ids,
        subject=request.data.get('subject') or '',
        greeting=request.data.get('greeting') or '',
        body=request.data.get('body') or '',
        footer=request.data.get('footer') or '',
        document_descriptions=request.data.get('document_descriptions') or [],
    )
    if not ok:
        return Response(
            {'error': error or 'Error al enviar.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    return Response({'message': 'Documentos enviados.'})


# ──────────────────────────────────────────────────────────────────────────
# Admin — email composer (history + send)
# ──────────────────────────────────────────────────────────────────────────

_COMPOSED_EMAIL_ALLOWED_EXT = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg',
}
_COMPOSED_EMAIL_MAX_FILE = 15 * 1024 * 1024  # 15 MB


def _parse_diagnostic_email(request, diagnostic):
    """Validate/parse a composed-email multipart request for diagnostics.

    Enforces a 1-minute-per-diagnostic rate limit in addition to field
    validation so any caller (not just the view) is protected.
    """
    import json
    import mimetypes
    from datetime import timedelta
    from pathlib import Path

    from django.core.exceptions import ValidationError as DjangoValidationError
    from django.core.validators import validate_email

    from content.models import EmailLog
    from content.services.diagnostic_email_service import DiagnosticEmailService

    one_min_ago = timezone.now() - timedelta(minutes=1)
    recent = EmailLog.objects.filter(
        template_key=DiagnosticEmailService.TEMPLATE_CUSTOM,
        metadata__diagnostic_uuid=str(diagnostic.uuid),
        sent_at__gte=one_min_ago,
    ).exists()
    if recent:
        return None, Response(
            {'error': 'Espera al menos 1 minuto entre envíos.'},
            status=http_status.HTTP_429_TOO_MANY_REQUESTS,
        )

    recipient_email = (request.data.get('recipient_email') or '').strip()
    if not recipient_email:
        return None, Response(
            {'error': 'El campo destinatario es obligatorio.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    try:
        validate_email(recipient_email)
    except DjangoValidationError:
        return None, Response(
            {'error': 'El correo del destinatario no es válido.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    subject = (request.data.get('subject') or '').strip()
    if not subject:
        return None, Response(
            {'error': 'El asunto es obligatorio.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    greeting = (request.data.get('greeting') or '').strip()
    footer = (request.data.get('footer') or '').strip()

    raw_sections = request.data.get('sections', '[]')
    try:
        sections = (
            json.loads(raw_sections) if isinstance(raw_sections, str)
            else raw_sections
        )
    except (json.JSONDecodeError, TypeError):
        return None, Response(
            {'error': 'Las secciones deben ser un JSON válido.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(sections, list) or not any(
        s.strip() for s in sections if isinstance(s, str)
    ):
        return None, Response(
            {'error': 'Debe incluir al menos una sección con contenido.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    sections = [s for s in sections if isinstance(s, str) and s.strip()]

    attachments = []
    for f in request.FILES.getlist('attachments'):
        ext = Path(f.name).suffix.lower()
        if ext not in _COMPOSED_EMAIL_ALLOWED_EXT:
            return None, Response(
                {'error': f'Tipo de archivo {ext} no permitido.'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        if f.size > _COMPOSED_EMAIL_MAX_FILE:
            return None, Response(
                {'error': f'El archivo "{f.name}" excede el límite de 15 MB.'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        mime_type = mimetypes.guess_type(f.name)[0] or 'application/octet-stream'
        attachments.append((f.name, f.read(), mime_type))

    return {
        'recipient_email': recipient_email,
        'subject': subject,
        'greeting': greeting,
        'sections': sections,
        'footer': footer,
        'attachments': attachments or None,
    }, None


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_diagnostic_email(request, diagnostic_id):
    from content.services.diagnostic_email_service import DiagnosticEmailService

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    parsed, error = _parse_diagnostic_email(request, diagnostic)
    if error:
        return error

    ok = DiagnosticEmailService.send_custom_email(
        diagnostic,
        recipient_email=parsed['recipient_email'],
        subject=parsed['subject'],
        greeting=parsed['greeting'],
        sections=parsed['sections'],
        footer=parsed['footer'],
        attachments=parsed['attachments'],
    )
    if ok:
        return Response({'message': f'Correo enviado a {parsed["recipient_email"]}.'})
    return Response(
        {'error': 'Error al enviar el correo. Intenta de nuevo.'},
        status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_diagnostic_email_defaults(request, diagnostic_id):
    from content.services.diagnostic_email_service import DiagnosticEmailService

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    return Response(DiagnosticEmailService.get_defaults(diagnostic))


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_diagnostic_emails(request, diagnostic_id):
    from content.services.diagnostic_email_service import DiagnosticEmailService

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    try:
        page = int(request.query_params.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    return Response(DiagnosticEmailService.list_emails(diagnostic, page=page))


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
