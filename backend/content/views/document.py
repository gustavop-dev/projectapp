import copy
import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import Document
from content.serializers.document import (
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentCreateUpdateSerializer,
    DocumentFromMarkdownSerializer,
)
from content.services.markdown_parser import markdown_to_blocks

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_documents(request):
    """List all documents."""
    documents = Document.objects.all()
    serializer = DocumentListSerializer(documents, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_document(request):
    """Create a document from direct JSON input."""
    serializer = DocumentCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    document = serializer.save()

    # If markdown was provided but no JSON, parse it
    if document.content_markdown and not document.content_json:
        blocks = markdown_to_blocks(document.content_markdown)
        document.content_json = {
            'meta': {
                'title': document.title,
                'client_name': document.client_name,
                'cover_type': document.cover_type,
                'include_portada': document.include_portada,
                'include_subportada': document.include_subportada,
                'include_contraportada': document.include_contraportada,
            },
            'blocks': blocks,
        }
        document.save(update_fields=['content_json'])

    detail = DocumentDetailSerializer(document)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_document_from_markdown(request):
    """Create a document from markdown text."""
    serializer = DocumentFromMarkdownSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    markdown_text = data['markdown']
    blocks = markdown_to_blocks(markdown_text)

    document = Document.objects.create(
        title=data['title'],
        client_name=data.get('client_name', ''),
        language=data.get('language', 'es'),
        cover_type=data.get('cover_type', 'generic'),
        include_portada=data.get('include_portada', True),
        include_subportada=data.get('include_subportada', True),
        include_contraportada=data.get('include_contraportada', True),
        content_markdown=markdown_text,
        content_json={
            'meta': {
                'title': data['title'],
                'client_name': data.get('client_name', ''),
                'cover_type': data.get('cover_type', 'generic'),
                'include_portada': data.get('include_portada', True),
                'include_subportada': data.get('include_subportada', True),
                'include_contraportada': data.get('include_contraportada', True),
            },
            'blocks': blocks,
        },
    )

    detail = DocumentDetailSerializer(document)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def upload_document_markdown(request):
    """Create a document from an uploaded .md file."""
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response(
            {'file': 'No file uploaded.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Read file content
    try:
        markdown_text = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError:
        return Response(
            {'file': 'File must be a valid UTF-8 text file.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    title = request.data.get('title', uploaded_file.name.rsplit('.', 1)[0])
    client_name = request.data.get('client_name', '')
    language = request.data.get('language', 'es')
    cover_type = request.data.get('cover_type', 'generic')

    blocks = markdown_to_blocks(markdown_text)

    def _to_bool(value, default=True):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() not in ('false', '0', '')
        return default if value is None else bool(value)

    include_portada = _to_bool(request.data.get('include_portada'), default=True)
    include_subportada = _to_bool(request.data.get('include_subportada'), default=True)
    include_contraportada = _to_bool(request.data.get('include_contraportada'), default=True)

    document = Document.objects.create(
        title=title,
        client_name=client_name,
        language=language,
        cover_type=cover_type,
        include_portada=include_portada,
        include_subportada=include_subportada,
        include_contraportada=include_contraportada,
        content_markdown=markdown_text,
        content_json={
            'meta': {
                'title': title,
                'client_name': client_name,
                'cover_type': cover_type,
                'include_portada': include_portada,
                'include_subportada': include_subportada,
                'include_contraportada': include_contraportada,
            },
            'blocks': blocks,
        },
    )

    detail = DocumentDetailSerializer(document)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_document(request, document_id):
    """Get document detail."""
    document = get_object_or_404(Document, pk=document_id)
    serializer = DocumentDetailSerializer(document)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_document(request, document_id):
    """Update a document."""
    document = get_object_or_404(Document, pk=document_id)
    serializer = DocumentCreateUpdateSerializer(
        document, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    # Re-parse markdown if it changed
    if 'content_markdown' in request.data and document.content_markdown:
        blocks = markdown_to_blocks(document.content_markdown)
        document.content_json = {
            'meta': {
                'title': document.title,
                'client_name': document.client_name,
                'cover_type': document.cover_type,
                'include_portada': document.include_portada,
                'include_subportada': document.include_subportada,
                'include_contraportada': document.include_contraportada,
            },
            'blocks': blocks,
        }
        document.save(update_fields=['content_json'])

    detail = DocumentDetailSerializer(document)
    return Response(detail.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_document(request, document_id):
    """Delete a document."""
    document = get_object_or_404(Document, pk=document_id)
    document.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def duplicate_document(request, document_id):
    """Duplicate a document."""
    document = get_object_or_404(Document, pk=document_id)

    new_document = Document.objects.create(
        title=f'{document.title} (copia)',
        client_name=document.client_name,
        language=document.language,
        cover_type=document.cover_type,
        include_portada=document.include_portada,
        include_subportada=document.include_subportada,
        include_contraportada=document.include_contraportada,
        status=Document.Status.DRAFT,
        content_markdown=document.content_markdown,
        content_json=copy.deepcopy(document.content_json),
    )

    detail = DocumentDetailSerializer(new_document)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def download_document_pdf(request, document_id):
    """Generate and download document as PDF."""
    document = get_object_or_404(Document, pk=document_id)

    if not document.content_json or not document.content_json.get('blocks'):
        return Response(
            {'detail': 'Document has no content to generate PDF.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from content.services.document_pdf_service import DocumentPdfService  # noqa: E402
    pdf_bytes = DocumentPdfService.generate(document)

    if not pdf_bytes:
        return Response(
            {'detail': 'Failed to generate PDF.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Build filename
    safe_title = slugify(document.title) or 'document'
    filename = f'{safe_title}.pdf'

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
