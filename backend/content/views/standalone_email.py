"""
Standalone branded email endpoints — send, defaults, history.

These endpoints are NOT tied to a specific proposal. They allow the admin
to send generic branded emails to any recipient, similar to how the
Documents module works for PDF documents.
"""
import json
import mimetypes
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import EmailLog

_ALLOWED_EXT = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg'}
_MAX_FILE = 15 * 1024 * 1024  # 15 MB
_TEMPLATE_KEY = 'branded_email'


def _parse_standalone_email(request):
    """Validate and parse a standalone composed-email request.

    Returns ``(parsed_data, None)`` on success or ``(None, Response)`` on error.
    """
    # ── Rate limit: 1 email per minute for standalone ──
    one_min_ago = timezone.now() - timedelta(minutes=1)
    if EmailLog.objects.filter(
        proposal__isnull=True, template_key=_TEMPLATE_KEY,
        sent_at__gte=one_min_ago,
    ).exists():
        return None, Response(
            {'error': 'Espera al menos 1 minuto entre envíos.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # ── Required text fields ──
    recipient_email = (request.data.get('recipient_email') or '').strip()
    if not recipient_email:
        return None, Response(
            {'error': 'El campo destinatario es obligatorio.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        validate_email(recipient_email)
    except DjangoValidationError:
        return None, Response(
            {'error': 'El correo del destinatario no es válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    subject = (request.data.get('subject') or '').strip()
    if not subject:
        return None, Response(
            {'error': 'El asunto es obligatorio.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    greeting = (request.data.get('greeting') or '').strip()
    footer = (request.data.get('footer') or '').strip()

    # ── Sections (JSON-encoded string in multipart) ──
    raw_sections = request.data.get('sections', '[]')
    try:
        sections = json.loads(raw_sections) if isinstance(raw_sections, str) else raw_sections
    except (json.JSONDecodeError, TypeError):
        return None, Response(
            {'error': 'Las secciones deben ser un JSON válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(sections, list) or not any(s.strip() for s in sections if isinstance(s, str)):
        return None, Response(
            {'error': 'Debe incluir al menos una sección con contenido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    sections = [s for s in sections if isinstance(s, str) and s.strip()]

    # ── File attachments ──
    attachments = []
    for f in request.FILES.getlist('attachments'):
        ext = Path(f.name).suffix.lower()
        if ext not in _ALLOWED_EXT:
            return None, Response(
                {'error': f'Tipo de archivo {ext} no permitido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if f.size > _MAX_FILE:
            return None, Response(
                {'error': f'El archivo "{f.name}" excede el límite de 15 MB.'},
                status=status.HTTP_400_BAD_REQUEST,
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
def send_standalone_email(request):
    """Send a standalone branded email (not tied to any proposal)."""
    parsed, error_response = _parse_standalone_email(request)
    if error_response:
        return error_response

    from content.services.proposal_email_service import ProposalEmailService
    sent = ProposalEmailService.send_standalone_branded_email(
        recipient_email=parsed['recipient_email'],
        subject=parsed['subject'],
        greeting=parsed['greeting'],
        sections=parsed['sections'],
        footer=parsed['footer'],
        attachments=parsed['attachments'],
    )

    if sent:
        return Response(
            {'message': f'Correo enviado a {parsed["recipient_email"]}.'},
            status=status.HTTP_200_OK,
        )
    return Response(
        {'error': 'Error al enviar el correo. Intenta de nuevo.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_standalone_email_defaults(request):
    """Return admin-configurable defaults for the standalone email composer."""
    from content.services.proposal_email_service import ProposalEmailService

    context = {'client_name': '', 'title': ''}
    field_values = ProposalEmailService._resolve_content(_TEMPLATE_KEY, context)

    return Response(field_values, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_standalone_emails(request):
    """List standalone branded emails (paginated, 20 per page)."""
    logs = EmailLog.objects.filter(
        proposal__isnull=True,
        template_key=_TEMPLATE_KEY,
    ).order_by('-sent_at')

    total = logs.count()
    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    page_size = 20
    offset = (page - 1) * page_size

    data = [
        {
            'id': log.pk,
            'recipient': log.recipient,
            'subject': log.subject,
            'status': log.status,
            'sent_at': log.sent_at.isoformat(),
            'metadata': log.metadata,
        }
        for log in logs[offset:offset + page_size]
    ]
    return Response({
        'results': data,
        'total': total,
        'page': page,
        'page_size': page_size,
        'has_next': offset + page_size < total,
    }, status=status.HTTP_200_OK)
