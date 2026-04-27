"""Admin endpoints exposing static markdown diagnostic templates."""

from datetime import datetime, timezone as dt_timezone
from pathlib import Path

from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import WebAppDiagnostic
from content.services.diagnostic_service import build_render_context


TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent / 'templates' / 'diagnostics'
)

TEMPLATES = {
    'diagnostico-aplicacion': {
        'filename': 'diagnostico_aplicacion_es.md',
        'title': 'Diagnóstico de Aplicación',
    },
    'diagnostico-tecnico': {
        'filename': 'diagnostico_tecnico_es.md',
        'title': 'Diagnóstico Técnico',
    },
    'anexo': {
        'filename': 'anexo_es.md',
        'title': 'Anexo — Dimensionamiento',
    },
}


def _stat(slug, meta):
    path = TEMPLATES_DIR / meta['filename']
    try:
        stat = path.stat()
    except (FileNotFoundError, OSError):
        return None
    return {
        'slug': slug,
        'title': meta['title'],
        'filename': meta['filename'],
        'size_bytes': stat.st_size,
        'updated_at': datetime.fromtimestamp(
            stat.st_mtime, tz=dt_timezone.utc,
        ).isoformat(),
    }


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_diagnostic_templates(request):
    items = [info for slug, meta in TEMPLATES.items()
             if (info := _stat(slug, meta)) is not None]
    return Response(items)


def _apply_render_context(markdown: str, ctx: dict) -> str:
    for key, value in ctx.items():
        markdown = markdown.replace('{{' + key + '}}', str(value))
    return markdown


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_diagnostic_template(request, slug):
    meta = TEMPLATES.get(slug)
    if meta is None:
        return Response(
            {'error': 'template_not_found'},
            status=http_status.HTTP_404_NOT_FOUND,
        )
    path = TEMPLATES_DIR / meta['filename']
    try:
        content = path.read_text(encoding='utf-8')
        stat = path.stat()
    except (FileNotFoundError, OSError):
        return Response(
            {'error': 'template_file_missing'},
            status=http_status.HTTP_404_NOT_FOUND,
        )
    diagnostic_id = request.query_params.get('diagnostic_id')
    if diagnostic_id:
        try:
            diagnostic = WebAppDiagnostic.objects.get(pk=diagnostic_id)
        except (WebAppDiagnostic.DoesNotExist, ValueError):
            return Response(
                {'error': 'diagnostic_not_found'},
                status=http_status.HTTP_404_NOT_FOUND,
            )
        content = _apply_render_context(content, build_render_context(diagnostic))
    return Response({
        'slug': slug,
        'title': meta['title'],
        'filename': meta['filename'],
        'size_bytes': stat.st_size,
        'updated_at': datetime.fromtimestamp(
            stat.st_mtime, tz=dt_timezone.utc,
        ).isoformat(),
        'content_markdown': content,
    })
