from django.db.models import Count, Q
from django.db.models.functions import Lower
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.api_errors import error_response
from content.models import Document, DocumentThread, DocumentThreadItem
from content.serializers.document_thread import (
    DocumentThreadCandidateSerializer,
    DocumentThreadCreateSerializer,
    DocumentThreadSerializer,
    DocumentThreadUpdateSerializer,
)
from content.services.document_thread_query import thread_detail_queryset
from content.services.document_thread_service import (
    DocumentThreadError,
    create_document_thread,
    dissolve_document_thread,
    update_document_thread,
)


class DocumentThreadCandidatePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


def _thread_error_response(exc):
    return error_response(
        str(exc),
        code=exc.code,
        hint=exc.hint,
        status=exc.status_code,
    )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def document_thread_detail(request, document_id):
    """Return the complete thread for a document, or JSON null when standalone."""
    document = get_object_or_404(Document, pk=document_id)
    membership = DocumentThreadItem.objects.filter(document=document).first()
    if membership is None:
        return JsonResponse(None, safe=False)
    thread = get_object_or_404(thread_detail_queryset(), pk=membership.thread_id)
    return Response(DocumentThreadSerializer(thread).data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def document_thread_candidates(request):
    """Search documents that can be added, retaining unavailable matches."""
    scope = str(request.query_params.get('scope') or 'active').strip().lower()
    if scope not in {'active', 'all'}:
        return Response(
            {'scope': 'El estado solicitado no es válido. Usa active o all.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    excluded_ids = set()
    raw_document_id = request.query_params.get('document_id')
    if raw_document_id not in (None, ''):
        try:
            document_id = int(raw_document_id)
        except (TypeError, ValueError):
            return Response(
                {'document_id': 'El identificador del documento no es válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        source_document = get_object_or_404(Document, pk=document_id)
        excluded_ids.add(source_document.pk)
        source_membership = DocumentThreadItem.objects.filter(
            document=source_document,
        ).first()
        if source_membership:
            excluded_ids.update(
                DocumentThreadItem.objects.filter(
                    thread_id=source_membership.thread_id,
                ).values_list('document_id', flat=True),
            )

    raw_thread_id = request.query_params.get('thread_id')
    if raw_thread_id not in (None, ''):
        try:
            thread_id = int(raw_thread_id)
        except (TypeError, ValueError):
            return Response(
                {'thread_id': 'El identificador del hilo no es válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        get_object_or_404(DocumentThread, pk=thread_id)
        excluded_ids.update(
            DocumentThreadItem.objects.filter(thread_id=thread_id).values_list(
                'document_id', flat=True,
            ),
        )

    documents = (
        Document.objects.select_related(
            'document_type', 'folder', 'project', 'client_user__profile',
            'thread_item__thread',
        )
        .annotate(
            thread_document_count=Count(
                'thread_item__thread__items', distinct=True,
            ),
        )
        .exclude(pk__in=excluded_ids)
    )
    if scope == 'active':
        documents = documents.filter(is_archived=False)

    search = str(request.query_params.get('search') or '').strip()[:200]
    if search:
        documents = documents.filter(
            Q(title__icontains=search)
            | Q(folder__name__icontains=search)
            | Q(client_name__icontains=search)
            | Q(client_user__first_name__icontains=search)
            | Q(client_user__last_name__icontains=search)
            | Q(client_user__profile__company_name__icontains=search)
            | Q(project__name__icontains=search),
        )
    documents = documents.order_by(Lower('title'), 'id')

    paginator = DocumentThreadCandidatePagination()
    page = paginator.paginate_queryset(documents, request)
    serializer = DocumentThreadCandidateSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_thread(request):
    serializer = DocumentThreadCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        thread = create_document_thread(
            title=serializer.validated_data['title'],
            items=serializer.validated_data['items'],
            actor=request.user,
        )
    except DocumentThreadError as exc:
        return _thread_error_response(exc)
    thread = get_object_or_404(thread_detail_queryset(), pk=thread.pk)
    return Response(DocumentThreadSerializer(thread).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def update_or_delete_thread(request, thread_id):
    thread = get_object_or_404(DocumentThread, pk=thread_id)
    if request.method == 'DELETE':
        dissolve_document_thread(thread=thread)
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = DocumentThreadUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        updated, dissolved = update_document_thread(
            thread=thread,
            actor=request.user,
            title=serializer.validated_data.get('title'),
            items=serializer.validated_data.get('items'),
        )
    except DocumentThreadError as exc:
        return _thread_error_response(exc)
    if dissolved:
        return Response({'thread': None, 'dissolved': True})
    updated = get_object_or_404(thread_detail_queryset(), pk=updated.pk)
    return Response(DocumentThreadSerializer(updated).data)
