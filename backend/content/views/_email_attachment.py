"""Shared helpers for markdown→PDF email attachments and inline PDF responses."""
from django.http import HttpResponse
from rest_framework import status as http_status
from rest_framework.response import Response

from content.services.document_pdf_service import DocumentPdfService
from content.utils import coerce_bool, safe_slug


def inline_pdf_response(pdf_bytes: bytes, filename: str) -> HttpResponse:
    """Return PDF bytes as an inline HttpResponse with Content-Disposition."""
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


def render_markdown_pdf_response(request, *, client_name: str):
    """Validate request, generate PDF from markdown, return inline HttpResponse."""
    title = (request.data.get('title') or '').strip()
    markdown_text = request.data.get('markdown') or ''
    if not title:
        return Response({'error': 'title_required'},
                        status=http_status.HTTP_400_BAD_REQUEST)
    if not markdown_text.strip():
        return Response({'error': 'markdown_required'},
                        status=http_status.HTTP_400_BAD_REQUEST)

    pdf_bytes = DocumentPdfService.generate_from_markdown(
        title=title,
        markdown_text=markdown_text,
        client_name=client_name,
        include_portada=coerce_bool(request.data.get('include_portada')),
        include_subportada=coerce_bool(request.data.get('include_subportada')),
        include_contraportada=coerce_bool(request.data.get('include_contraportada')),
        language='es',
    )
    if not pdf_bytes:
        return Response({'error': 'pdf_generation_failed'},
                        status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

    return inline_pdf_response(pdf_bytes, f'{safe_slug(title, "documento")}.pdf')
