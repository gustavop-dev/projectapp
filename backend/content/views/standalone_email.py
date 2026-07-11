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

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import Document, EmailLog

_ALLOWED_EXT = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg'}
_MAX_FILE = 15 * 1024 * 1024  # 15 MB
_TEMPLATE_KEY = 'branded_email'


def _parse_sections_field(raw_sections):
    """Parse a request ``sections`` field (JSON string or list).

    Returns ``(sections, error_message)`` where ``sections`` is the
    normalized ``[{'text', 'markdown'}]`` list. Accepts the legacy
    plain-string shape and the new ``{text, markdown}`` dicts.
    """
    from content.services.email_markdown import normalize_sections

    try:
        sections = json.loads(raw_sections) if isinstance(raw_sections, str) else raw_sections
    except (json.JSONDecodeError, TypeError):
        return None, 'Las secciones deben ser un JSON válido.'
    if sections is None:
        sections = []
    if not isinstance(sections, list):
        return None, 'Las secciones deben ser un JSON válido.'
    return normalize_sections(sections), None


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
    sections, sections_error = _parse_sections_field(request.data.get('sections', '[]'))
    if sections_error:
        return None, Response(
            {'error': sections_error},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not sections:
        return None, Response(
            {'error': 'Debe incluir al menos una sección con contenido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

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

    # ── Document references (PDFs generated server-side) ──
    raw_doc_ids = request.data.get('document_ids', '[]')
    try:
        document_ids = json.loads(raw_doc_ids) if isinstance(raw_doc_ids, str) else raw_doc_ids
    except (json.JSONDecodeError, TypeError):
        return None, Response(
            {'error': 'document_ids debe ser JSON válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not isinstance(document_ids, list):
        document_ids = []
    document_ids = [int(d) for d in document_ids if isinstance(d, (int, str)) and str(d).isdigit()]

    if document_ids:
        from content.services.document_pdf_service import DocumentPdfService
        documents = Document.objects.filter(pk__in=document_ids)
        for doc in documents:
            if not doc.content_json or not doc.content_json.get('blocks'):
                continue
            pdf_bytes = DocumentPdfService.generate(doc)
            if not pdf_bytes:
                continue
            filename = f'{doc.title or f"documento-{doc.pk}"}.pdf'
            attachments.append((filename, pdf_bytes, 'application/pdf'))

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


@api_view(['POST'])
@permission_classes([IsAdminUser])
def preview_composed_email(request):
    """Render the branded email HTML exactly as the send path would.

    Feeds the composers' "Vista previa" iframe: no email is sent, nothing
    is logged in ``EmailLog`` and the send rate limit does not apply.
    Accepts an optional ``proposal_id`` so the proposal composer's preview
    resolves the same signature as its send path.
    """
    subject = (request.data.get('subject') or '').strip()
    greeting = (request.data.get('greeting') or '').strip()
    footer = (request.data.get('footer') or '').strip()

    sections, sections_error = _parse_sections_field(request.data.get('sections', []))
    if sections_error:
        return Response(
            {'error': sections_error},
            status=status.HTTP_400_BAD_REQUEST,
        )

    attachment_names = request.data.get('attachment_names') or []
    if not isinstance(attachment_names, list):
        attachment_names = []
    attachment_names = [n.strip() for n in attachment_names if isinstance(n, str) and n.strip()]

    proposal = None
    proposal_id = request.data.get('proposal_id')
    if proposal_id:
        from content.models import BusinessProposal
        proposal = BusinessProposal.objects.filter(pk=proposal_id).first()

    from content.services.proposal_email_service import ProposalEmailService
    html_content, _ = ProposalEmailService.render_composed_email(
        _TEMPLATE_KEY, proposal, subject, greeting,
        sections, footer, attachment_names,
    )
    return Response(
        {'subject': subject, 'html_preview': html_content},
        status=status.HTTP_200_OK,
    )


def _available_signers():
    """Return the signers configured in settings as ``[{key, name, role}]``."""
    signatures = getattr(settings, 'EMAIL_SIGNATURES', {}) or {}
    return [
        {'key': key, 'name': sig.get('name', ''), 'role': sig.get('role', '')}
        for key, sig in signatures.items()
    ]


def _defaults_payload():
    """Build the standalone composer defaults payload (GET/PUT response).

    Top-level ``greeting``/``footer`` keep the historical shape consumed by
    the composer (overrides merged over defaults, variables substituted).
    ``config`` carries the raw editable values for the defaults form and
    ``defaults`` the registry/settings values used by "restore defaults".
    """
    from content.models import EmailTemplateConfig
    from content.services.email_template_registry import (
        get_default_field_values, get_template_entry,
    )
    from content.services.proposal_email_service import ProposalEmailService

    config = EmailTemplateConfig.objects.filter(template_key=_TEMPLATE_KEY).first()
    overrides = (config.content_overrides if config else {}) or {}
    defaults = get_default_field_values(_TEMPLATE_KEY)
    default_signer = getattr(settings, 'EMAIL_DEFAULT_SIGNER', 'gustavo')
    entry = get_template_entry(_TEMPLATE_KEY) or {}

    context = {'client_name': '', 'title': ''}
    field_values = ProposalEmailService._resolve_content(_TEMPLATE_KEY, context)

    return {
        **field_values,
        'config': {
            'greeting': overrides.get('greeting') or defaults.get('greeting', ''),
            'footer': overrides.get('footer') or defaults.get('footer', ''),
            'signer': overrides.get('signer') or default_signer,
        },
        'defaults': {
            'greeting': defaults.get('greeting', ''),
            'footer': defaults.get('footer', ''),
            'signer': default_signer,
        },
        'is_customized': bool(overrides),
        'available_signers': _available_signers(),
        'available_variables': entry.get('available_variables', []),
    }


@api_view(['GET', 'PUT'])
@permission_classes([IsAdminUser])
def standalone_email_defaults(request):
    """GET/PUT admin-configurable defaults for the standalone email composer.

    PUT stores ``greeting``/``footer``/``signer`` as ``content_overrides`` on
    the ``branded_email`` template config. Values that are empty or equal to
    the registry/settings default are dropped, so submitting the defaults (or
    blanks) restores the original behavior.
    """
    if request.method == 'GET':
        return Response(_defaults_payload(), status=status.HTTP_200_OK)

    from content.models import EmailTemplateConfig
    from content.services.email_template_registry import get_default_field_values

    greeting = (request.data.get('greeting') or '').strip()
    footer = (request.data.get('footer') or '').strip()
    signer = (request.data.get('signer') or '').strip()

    signatures = getattr(settings, 'EMAIL_SIGNATURES', {}) or {}
    if signer and signer not in signatures:
        return Response(
            {'error': 'El firmante seleccionado no es válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    defaults = get_default_field_values(_TEMPLATE_KEY)
    default_signer = getattr(settings, 'EMAIL_DEFAULT_SIGNER', 'gustavo')

    overrides = {}
    if greeting and greeting != defaults.get('greeting'):
        overrides['greeting'] = greeting
    if footer and footer != defaults.get('footer'):
        overrides['footer'] = footer
    if signer and signer != default_signer:
        overrides['signer'] = signer

    config = EmailTemplateConfig.objects.filter(template_key=_TEMPLATE_KEY).first()
    if config:
        config.content_overrides = overrides
        config.save(update_fields=['content_overrides', 'updated_at'])
    elif overrides:
        EmailTemplateConfig.objects.create(
            template_key=_TEMPLATE_KEY,
            content_overrides=overrides,
        )

    return Response(_defaults_payload(), status=status.HTTP_200_OK)


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
