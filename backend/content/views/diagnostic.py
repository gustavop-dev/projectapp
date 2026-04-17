"""Admin + public DRF views for the WebAppDiagnostic feature.

Admin endpoints use Django session auth + IsAdminUser. The 3 public endpoints
(`retrieve`, `track`, `respond`) use AllowAny + UUID lookup.
"""

import logging

from django.db.models import Avg, Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from accounts.models import UserProfile
from content.models import (
    DiagnosticAttachment,
    DiagnosticChangeLog,
    DiagnosticSection,
    DiagnosticSectionView,
    DiagnosticViewEvent,
    WebAppDiagnostic,
)
from content.serializers.diagnostic import (
    ConfidentialityParamsSerializer,
    DiagnosticChangeLogSerializer,
    DiagnosticDetailSerializer,
    DiagnosticListSerializer,
    DiagnosticSectionSerializer,
    DiagnosticSectionUpdateSerializer,
    DiagnosticUpdateSerializer,
    PublicDiagnosticSerializer,
    serialize_diagnostic_attachment,
)
from content.services import diagnostic_service
from content.utils import get_client_ip

logger = logging.getLogger(__name__)


def _admin_qs(include_attachments=False):
    qs = (
        WebAppDiagnostic.objects
        .select_related('client__user')
        .prefetch_related('sections', 'change_logs')
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
    diagnostic_service.log_change(
        diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.UPDATED,
        description='Datos generales actualizados.',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_diagnostic(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    diagnostic.delete()
    return Response(status=http_status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────
# Admin — sections CRUD
# ──────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_diagnostic_sections(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    return Response(DiagnosticSectionSerializer(
        diagnostic.sections.all(), many=True,
    ).data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_diagnostic_section(request, diagnostic_id, section_id):
    section = get_object_or_404(
        DiagnosticSection.objects.select_related('diagnostic'),
        pk=section_id, diagnostic_id=diagnostic_id,
    )
    serializer = DiagnosticSectionUpdateSerializer(
        section, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors,
                        status=http_status.HTTP_400_BAD_REQUEST)
    serializer.save()
    diagnostic_service.log_change(
        section.diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.SECTION_UPDATED,
        field_name=section.section_type,
        description=f'Sección «{section.title}» actualizada.',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    return Response(DiagnosticSectionSerializer(section).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_update_diagnostic_sections(request, diagnostic_id):
    """Accept a list of ``{id, ...fields}`` entries and update in one call."""
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    payload = request.data.get('sections') or []
    if not isinstance(payload, list):
        return Response(
            {'error': 'sections_must_be_list'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    updated_ids = []
    for entry in payload:
        if not isinstance(entry, dict) or 'id' not in entry:
            continue
        section = DiagnosticSection.objects.filter(
            pk=entry['id'], diagnostic_id=diagnostic.id,
        ).first()
        if section is None:
            continue
        serializer = DiagnosticSectionUpdateSerializer(
            section, data=entry, partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            updated_ids.append(section.id)

    if updated_ids:
        diagnostic_service.log_change(
            diagnostic,
            change_type=DiagnosticChangeLog.ChangeType.SECTION_UPDATED,
            description=f'{len(updated_ids)} secciones actualizadas en bloque.',
            actor_type=DiagnosticChangeLog.ActorType.SELLER,
        )

    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reset_diagnostic_section(request, diagnostic_id, section_id):
    section = get_object_or_404(
        DiagnosticSection.objects.select_related('diagnostic'),
        pk=section_id, diagnostic_id=diagnostic_id,
    )
    diagnostic_service.reset_section(section)
    diagnostic_service.log_change(
        section.diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.SECTION_UPDATED,
        field_name=section.section_type,
        description=f'Sección «{section.title}» restaurada al contenido por defecto.',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    return Response(DiagnosticSectionSerializer(section).data)


# ──────────────────────────────────────────────────────────────────────────
# Admin — activity (change log)
# ──────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_diagnostic_activity(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    logs = diagnostic.change_logs.all()
    return Response(DiagnosticChangeLogSerializer(logs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_diagnostic_activity(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    change_type = (request.data.get('change_type') or 'note').strip()
    valid = {c[0] for c in DiagnosticChangeLog.ChangeType.choices}
    if change_type not in valid:
        return Response(
            {'error': 'invalid_change_type'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    description = (request.data.get('description') or '').strip()
    if not description:
        return Response(
            {'error': 'description_required'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    log = diagnostic_service.log_change(
        diagnostic,
        change_type=change_type,
        description=description,
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    return Response(
        DiagnosticChangeLogSerializer(log).data,
        status=http_status.HTTP_201_CREATED,
    )


# ──────────────────────────────────────────────────────────────────────────
# Admin — analytics
# ──────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def diagnostic_analytics(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)

    section_stats = (
        DiagnosticSectionView.objects
        .filter(view_event__diagnostic=diagnostic)
        .values('section_type', 'section_title')
        .annotate(
            total_seconds=Sum('time_spent_seconds'),
            avg_seconds=Avg('time_spent_seconds'),
            visits=Count('id'),
        )
        .order_by('-total_seconds')
    )
    total_sessions = diagnostic.view_events.count()
    total_time = (
        DiagnosticSectionView.objects
        .filter(view_event__diagnostic=diagnostic)
        .aggregate(total=Sum('time_spent_seconds'))['total'] or 0
    )

    return Response({
        'view_count': diagnostic.view_count,
        'last_viewed_at': (
            diagnostic.last_viewed_at.isoformat()
            if diagnostic.last_viewed_at else None
        ),
        'total_sessions': total_sessions,
        'total_time_spent_seconds': float(total_time or 0),
        'sections': [
            {
                'section_type': row['section_type'],
                'section_title': row['section_title'],
                'total_seconds': float(row['total_seconds'] or 0),
                'avg_seconds': float(row['avg_seconds'] or 0),
                'visits': row['visits'],
            }
            for row in section_stats
        ],
        'initial_sent_at': (
            diagnostic.initial_sent_at.isoformat()
            if diagnostic.initial_sent_at else None
        ),
        'final_sent_at': (
            diagnostic.final_sent_at.isoformat()
            if diagnostic.final_sent_at else None
        ),
        'responded_at': (
            diagnostic.responded_at.isoformat()
            if diagnostic.responded_at else None
        ),
    })


# ──────────────────────────────────────────────────────────────────────────
# Admin — send actions
# ──────────────────────────────────────────────────────────────────────────

def _send_and_transition(diagnostic, kind: str):
    from content.services.diagnostic_email_service import (
        DiagnosticEmailService,
    )

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
        diagnostic_service.transition_status(
            diagnostic, target,
            actor_type=DiagnosticChangeLog.ActorType.SELLER,
        )
    except ValueError as exc:
        return False, Response(
            {'error': str(exc).split(':')[0], 'message': str(exc)},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    try:
        email_ok = email_fn(diagnostic)
    except Exception:
        logger.exception('Email send failed for diagnostic %s (%s)',
                         diagnostic.uuid, kind)
        email_ok = False

    if email_ok:
        diagnostic_service.log_change(
            diagnostic,
            change_type=DiagnosticChangeLog.ChangeType.EMAIL_SENT,
            description=f'Email «{kind}» enviado al cliente.',
            actor_type=DiagnosticChangeLog.ActorType.SYSTEM,
        )
    return True, email_ok


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_initial(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    ok, email_ok = _send_and_transition(diagnostic, 'initial')
    if not ok:
        return email_ok
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    body = DiagnosticDetailSerializer(diagnostic).data
    body['email_ok'] = bool(email_ok)
    return Response(body)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def mark_in_analysis(request, diagnostic_id):
    """Manual transition SENT → NEGOTIATING once the client authorized."""
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    try:
        diagnostic_service.transition_status(
            diagnostic, WebAppDiagnostic.Status.NEGOTIATING,
            actor_type=DiagnosticChangeLog.ActorType.SELLER,
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
    ok, email_ok = _send_and_transition(diagnostic, 'final')
    if not ok:
        return email_ok
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    body = DiagnosticDetailSerializer(diagnostic).data
    body['email_ok'] = bool(email_ok)
    return Response(body)


# ──────────────────────────────────────────────────────────────────────────
# Public — view / track / respond
# ──────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_public_diagnostic(request, diagnostic_uuid):
    diagnostic = get_object_or_404(
        WebAppDiagnostic.objects.select_related('client__user')
        .prefetch_related('sections'),
        uuid=diagnostic_uuid,
    )
    if diagnostic.status in diagnostic_service.PUBLIC_VISIBLE_STATUSES:
        diagnostic_service.register_view(diagnostic)
    return Response(PublicDiagnosticSerializer(diagnostic).data)


def _ensure_view_event(diagnostic, request, session_id):
    """Return the existing ViewEvent for (diagnostic, session) or create one."""
    existing = (
        DiagnosticViewEvent.objects
        .filter(diagnostic=diagnostic, session_id=session_id)
        .order_by('-viewed_at')
        .first()
    )
    if existing is not None:
        return existing
    return DiagnosticViewEvent.objects.create(
        diagnostic=diagnostic,
        session_id=session_id,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:2000],
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def track_public_diagnostic(request, diagnostic_uuid):
    """Create (or reuse) a DiagnosticViewEvent for this public visit."""
    diagnostic = get_object_or_404(WebAppDiagnostic, uuid=diagnostic_uuid)
    session_id = (request.data.get('session_id') or '')[:64] or 'anonymous'
    _ensure_view_event(diagnostic, request, session_id)
    diagnostic_service.register_view(diagnostic)
    return Response({'view_count': diagnostic.view_count})


@api_view(['POST'])
@permission_classes([AllowAny])
def track_diagnostic_section_view(request, diagnostic_uuid):
    """Record per-section time spent during a public visit."""
    diagnostic = get_object_or_404(WebAppDiagnostic, uuid=diagnostic_uuid)
    session_id = (request.data.get('session_id') or '')[:64]
    section_type = (request.data.get('section_type') or '')[:50]
    section_title = (request.data.get('section_title') or '')[:255]
    time_spent = float(request.data.get('time_spent_seconds') or 0)

    if not session_id or not section_type:
        return Response(
            {'error': 'session_id_and_section_type_required'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    view_event = _ensure_view_event(diagnostic, request, session_id)
    DiagnosticSectionView.objects.create(
        view_event=view_event,
        section_type=section_type,
        section_title=section_title,
        time_spent_seconds=max(0.0, time_spent),
        entered_at=timezone.now(),
    )
    return Response({'ok': True})


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
        diagnostic_service.transition_status(
            diagnostic, target,
            actor_type=DiagnosticChangeLog.ActorType.CLIENT,
        )
    except ValueError as exc:
        return Response(
            {'error': str(exc).split(':')[0], 'message': str(exc)},
            status=http_status.HTTP_409_CONFLICT,
        )
    return Response(PublicDiagnosticSerializer(diagnostic).data)


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
    if attachment.is_generated:
        return Response(
            {'error': 'No se puede eliminar un documento generado por el sistema; regénerelo desde Editar parámetros.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    if attachment.file:
        attachment.file.delete(save=False)
    attachment.delete()
    return Response(status=http_status.HTTP_204_NO_CONTENT)


_SEND_ALLOWED_DOC_KEYS = {DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY}


def _diagnostic_pdf_meta(diagnostic):
    """Return ``(client_label, date_str)`` used to build PDF filenames."""
    client_label = (
        getattr(diagnostic.client, 'company_name', None)
        or diagnostic.title
        or 'cliente'
    )
    date_str = (diagnostic.created_at or timezone.now()).strftime('%Y-%m-%d')
    return client_label, date_str


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_diagnostic_attachments(request, diagnostic_id):
    """Email selected DiagnosticAttachments + system-generated docs to the client."""
    from content.services import diagnostic_documents_service
    from content.services.confidentiality_pdf_service import generate_confidentiality_pdf
    from content.services.pdf_utils import add_watermark_to_pdf, safe_pdf_filename

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)

    attachment_ids = request.data.get('attachment_ids') or []
    documents = request.data.get('documents') or []
    if not isinstance(attachment_ids, list):
        attachment_ids = []
    if not isinstance(documents, list):
        documents = []

    invalid = set(documents) - _SEND_ALLOWED_DOC_KEYS
    if invalid:
        return Response(
            {'error': f'Claves de documento no reconocidas: {sorted(invalid)}'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    if not attachment_ids and not documents:
        return Response(
            {'error': 'Debes seleccionar al menos un documento.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    extra_files = []
    if DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY in documents:
        has_params = bool(diagnostic.confidentiality_params)
        has_generated = diagnostic.attachments.filter(
            document_type=DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY,
            is_generated=True,
        ).exists()
        if not has_params and not has_generated:
            return Response(
                {'error': 'Debes generar el Acuerdo de Confidencialidad antes de enviarlo (Documentos → Generar acuerdo).'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        nda_bytes = generate_confidentiality_pdf(diagnostic, draft=True)
        if not nda_bytes:
            return Response(
                {'error': 'No se pudo generar el Acuerdo de Confidencialidad.'},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        watermarked = add_watermark_to_pdf(nda_bytes)
        client_label, date_str = _diagnostic_pdf_meta(diagnostic)
        extra_files.append((
            safe_pdf_filename('Acuerdo_Confidencialidad', client_label, date_str),
            watermarked,
            'application/pdf',
        ))

    ok, error = diagnostic_documents_service.send_attachments_to_client(
        diagnostic,
        attachment_ids=attachment_ids,
        subject=request.data.get('subject') or '',
        greeting=request.data.get('greeting') or '',
        body=request.data.get('body') or '',
        footer=request.data.get('footer') or '',
        document_descriptions=request.data.get('document_descriptions') or [],
        extra_files=extra_files,
    )
    if not ok:
        return Response(
            {'error': error or 'Error al enviar.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    diagnostic_service.log_change(
        diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.EMAIL_SENT,
        description='Adjuntos enviados al cliente.',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    return Response({'message': 'Documentos enviados.'})


# ──────────────────────────────────────────────────────────────────────────
# Acuerdo de Confidencialidad (NDA) PDF
# ──────────────────────────────────────────────────────────────────────────


def _generate_and_save_confidentiality_pdf(diagnostic):
    """Generate the NDA PDF for *diagnostic* and persist it as a generated
    DiagnosticAttachment. Replaces any prior generated NDA in place.
    """
    from django.core.files.base import ContentFile

    from content.services.confidentiality_pdf_service import generate_confidentiality_pdf
    from content.services.pdf_utils import safe_pdf_filename

    pdf_bytes = generate_confidentiality_pdf(diagnostic)
    if not pdf_bytes:
        return None

    client_label, date_str = _diagnostic_pdf_meta(diagnostic)
    filename = safe_pdf_filename('Acuerdo_Confidencialidad', client_label, date_str)

    existing = diagnostic.attachments.filter(
        document_type=DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY,
        is_generated=True,
    ).first()
    if existing:
        if existing.file:
            existing.file.delete(save=False)
        existing.file.save(filename, ContentFile(pdf_bytes), save=False)
        existing.title = 'Acuerdo de Confidencialidad'
        existing.save()
        return existing

    return DiagnosticAttachment.objects.create(
        diagnostic=diagnostic,
        document_type=DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY,
        title='Acuerdo de Confidencialidad',
        file=ContentFile(pdf_bytes, name=filename),
        is_generated=True,
        uploaded_by=None,
    )


@api_view(['POST', 'PATCH'])
@permission_classes([IsAdminUser])
def update_confidentiality_params(request, diagnostic_id):
    """Update NDA params on the diagnostic and (re)generate the stored PDF."""
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    serializer = ConfidentialityParamsSerializer(
        data=request.data.get('confidentiality_params', request.data),
    )
    serializer.is_valid(raise_exception=True)

    diagnostic.confidentiality_params = serializer.validated_data
    diagnostic.save(update_fields=['confidentiality_params', 'updated_at'])

    attachment = _generate_and_save_confidentiality_pdf(diagnostic)
    if not attachment:
        return Response(
            {'error': 'Parámetros guardados pero no se pudo generar el PDF.'},
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    diagnostic_service.log_change(
        diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.UPDATED,
        field_name='confidentiality_agreement',
        description='Acuerdo de Confidencialidad generado/actualizado.',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    return Response({
        'confidentiality_params': diagnostic.confidentiality_params,
        'attachment': serialize_diagnostic_attachment(attachment),
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def generate_confidentiality_pdf_view(request, diagnostic_id):
    """Force-regenerate the NDA PDF using the currently stored params."""
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    attachment = _generate_and_save_confidentiality_pdf(diagnostic)
    if not attachment:
        return Response(
            {'error': 'No se pudo generar el PDF.'},
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response({'attachment': serialize_diagnostic_attachment(attachment)})


def _confidentiality_filename(diagnostic, prefix):
    from content.services.pdf_utils import safe_pdf_filename

    client_label, date_str = _diagnostic_pdf_meta(diagnostic)
    return safe_pdf_filename(prefix, client_label, date_str)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def download_confidentiality_pdf(request, diagnostic_id):
    from django.http import FileResponse

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    attachment = diagnostic.attachments.filter(
        document_type=DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY,
        is_generated=True,
    ).first()
    if not attachment or not attachment.file:
        return Response(
            {'error': 'El acuerdo aún no ha sido generado.'},
            status=http_status.HTTP_404_NOT_FOUND,
        )
    return FileResponse(
        attachment.file.open('rb'),
        content_type='application/pdf',
        filename=_confidentiality_filename(diagnostic, 'Acuerdo_Confidencialidad'),
    )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def download_draft_confidentiality_pdf(request, diagnostic_id):
    from django.http import HttpResponse

    from content.services.confidentiality_pdf_service import generate_confidentiality_pdf
    from content.services.pdf_utils import add_watermark_to_pdf

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    pdf_bytes = generate_confidentiality_pdf(diagnostic, draft=True)
    if not pdf_bytes:
        return Response(
            {'error': 'No se pudo generar el borrador.'},
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    filename = _confidentiality_filename(diagnostic, 'Borrador_Acuerdo_Confidencialidad')
    response = HttpResponse(add_watermark_to_pdf(pdf_bytes), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


# ──────────────────────────────────────────────────────────────────────────
# Admin — email composer (history + send)
# ──────────────────────────────────────────────────────────────────────────

_COMPOSED_EMAIL_ALLOWED_EXT = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg',
}
_COMPOSED_EMAIL_MAX_FILE = 15 * 1024 * 1024  # 15 MB


def _parse_diagnostic_email(request, diagnostic):
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
        diagnostic_service.log_change(
            diagnostic,
            change_type=DiagnosticChangeLog.ChangeType.EMAIL_SENT,
            description=f'Correo enviado a {parsed["recipient_email"]}.',
            actor_type=DiagnosticChangeLog.ActorType.SELLER,
        )
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
