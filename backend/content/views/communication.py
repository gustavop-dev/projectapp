from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import CommunicationMessage, CommunicationThread, Document
from content.serializers.communication import (
    CommunicationDateCorrectionWriteSerializer,
    CommunicationDraftUpdateSerializer,
    CommunicationMarkSentSerializer,
    CommunicationMessageCreateSerializer,
    CommunicationMessageSerializer,
    CommunicationThreadDetailSerializer,
    CommunicationThreadListSerializer,
    CommunicationThreadWriteSerializer,
    CommunicationVoidSerializer,
)
from content.services import communication_service


def _message_queryset():
    return (
        CommunicationMessage.objects
        .select_related('created_by', 'reply_to')
        .prefetch_related('documents', 'date_corrections__corrected_by')
    )


def _thread_queryset():
    return (
        CommunicationThread.objects
        .select_related('client__user', 'project')
        .annotate(
            messages_count=Count('messages', distinct=True),
            draft_count=Count(
                'messages',
                filter=Q(
                    messages__status=CommunicationMessage.Status.DRAFT,
                    messages__voided_at__isnull=True,
                ),
                distinct=True,
            ),
        )
        .prefetch_related(Prefetch('messages', queryset=_message_queryset()))
    )


def _business_error(exc):
    detail = exc.args[0] if exc.args else str(exc)
    if isinstance(detail, dict):
        return Response(detail, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': str(detail)}, status=status.HTTP_400_BAD_REQUEST)


def _positive_int(value, *, field, default=None, maximum=None):
    if value in (None, ''):
        return default, None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, Response(
            {field: 'Debe ser un número entero.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if parsed < 1:
        return None, Response(
            {field: 'Debe ser mayor que cero.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed, None


def _parse_date_filter(raw_value, *, field, end=False):
    if not raw_value:
        return None, None
    parsed_datetime = parse_datetime(raw_value)
    if parsed_datetime:
        return parsed_datetime, None
    parsed_date = parse_date(raw_value)
    if parsed_date:
        lookup = 'messages__occurred_at__date__lte' if end else 'messages__occurred_at__date__gte'
        return (lookup, parsed_date), None
    return None, Response(
        {field: 'Usa una fecha ISO válida.'},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def communication_threads(request):
    """List filtered conversations or create a new empty thread."""
    if request.method == 'POST':
        serializer = CommunicationThreadWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            thread = communication_service.create_thread(
                actor=request.user,
                **serializer.validated_data,
            )
        except communication_service.CommunicationError as exc:
            return _business_error(exc)
        thread = get_object_or_404(_thread_queryset(), pk=thread.pk)
        return Response(
            CommunicationThreadDetailSerializer(thread).data,
            status=status.HTTP_201_CREATED,
        )

    queryset = _thread_queryset()
    for field in ('client', 'project'):
        raw_value = request.query_params.get(field)
        if raw_value:
            parsed, error = _positive_int(raw_value, field=field)
            if error:
                return error
            queryset = queryset.filter(**{f'{field}_id': parsed})

    thread_status = request.query_params.get('status')
    if thread_status:
        valid_statuses = {choice for choice, _ in CommunicationThread.Status.choices}
        if thread_status not in valid_statuses:
            return Response(
                {'status': 'Estado de hilo inválido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = queryset.filter(status=thread_status)

    for field, choices in (
        ('channel', CommunicationMessage.Channel.choices),
        ('direction', CommunicationMessage.Direction.choices),
        ('message_status', CommunicationMessage.Status.choices),
    ):
        raw_value = request.query_params.get(field)
        if not raw_value:
            continue
        valid_values = {choice for choice, _ in choices}
        if raw_value not in valid_values:
            return Response(
                {field: 'Valor de filtro inválido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model_field = 'status' if field == 'message_status' else field
        queryset = queryset.filter(**{f'messages__{model_field}': raw_value})

    for field, end in (('date_from', False), ('date_to', True)):
        parsed, error = _parse_date_filter(
            request.query_params.get(field), field=field, end=end,
        )
        if error:
            return error
        if parsed:
            if isinstance(parsed, tuple):
                queryset = queryset.filter(**{parsed[0]: parsed[1]})
            else:
                lookup = 'messages__occurred_at__lte' if end else 'messages__occurred_at__gte'
                queryset = queryset.filter(**{lookup: parsed})

    query = request.query_params.get('q', '').strip()
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(client__company_name__icontains=query)
            | Q(client__user__first_name__icontains=query)
            | Q(client__user__last_name__icontains=query)
            | Q(client__user__email__icontains=query)
            | Q(messages__subject__icontains=query)
            | Q(messages__content__icontains=query)
        )

    page_number, error = _positive_int(
        request.query_params.get('page'), field='page', default=1,
    )
    if error:
        return error
    page_size, error = _positive_int(
        request.query_params.get('page_size'),
        field='page_size',
        default=20,
        maximum=100,
    )
    if error:
        return error
    paginator = Paginator(
        queryset.distinct().order_by('-last_activity_at', '-id'),
        page_size,
    )
    page = paginator.get_page(page_number)
    return Response({
        'results': CommunicationThreadListSerializer(page.object_list, many=True).data,
        'count': paginator.count,
        'page': page.number,
        'num_pages': paginator.num_pages,
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAdminUser])
def communication_thread_detail(request, thread_id):
    thread = get_object_or_404(_thread_queryset(), pk=thread_id)
    if request.method == 'PATCH':
        serializer = CommunicationThreadWriteSerializer(
            thread, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        try:
            communication_service.update_thread(
                thread,
                actor=request.user,
                **serializer.validated_data,
            )
        except communication_service.CommunicationError as exc:
            return _business_error(exc)
        thread = get_object_or_404(_thread_queryset(), pk=thread_id)
    return Response(CommunicationThreadDetailSerializer(thread).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def close_communication_thread(request, thread_id):
    thread = get_object_or_404(CommunicationThread, pk=thread_id)
    try:
        communication_service.close_thread(thread, actor=request.user)
    except communication_service.CommunicationError as exc:
        return _business_error(exc)
    return Response(CommunicationThreadDetailSerializer(
        get_object_or_404(_thread_queryset(), pk=thread_id),
    ).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reopen_communication_thread(request, thread_id):
    thread = get_object_or_404(CommunicationThread, pk=thread_id)
    try:
        communication_service.reopen_thread(thread, actor=request.user)
    except communication_service.CommunicationError as exc:
        return _business_error(exc)
    return Response(CommunicationThreadDetailSerializer(
        get_object_or_404(_thread_queryset(), pk=thread_id),
    ).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def communication_thread_messages(request, thread_id):
    thread = get_object_or_404(
        CommunicationThread.objects.select_related('client__user'),
        pk=thread_id,
    )
    serializer = CommunicationMessageCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = dict(serializer.validated_data)
    document_ids = validated_data.pop('document_ids', [])
    try:
        message = communication_service.create_message(
            thread=thread,
            actor=request.user,
            document_ids=document_ids,
            **validated_data,
        )
    except communication_service.CommunicationError as exc:
        return _business_error(exc)
    message = get_object_or_404(_message_queryset(), pk=message.pk)
    return Response(
        CommunicationMessageSerializer(message).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def communication_message_detail(request, message_id):
    message = get_object_or_404(
        _message_queryset().select_related('thread__client__user'),
        pk=message_id,
    )
    try:
        if request.method == 'DELETE':
            communication_service.delete_draft(message, actor=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = CommunicationDraftUpdateSerializer(
            message, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        validated_data = dict(serializer.validated_data)
        document_ids = validated_data.pop('document_ids', None)
        message = communication_service.update_draft(
            message,
            actor=request.user,
            document_ids=document_ids,
            **validated_data,
        )
    except communication_service.CommunicationError as exc:
        return _business_error(exc)
    return Response(CommunicationMessageSerializer(
        get_object_or_404(_message_queryset(), pk=message.pk),
    ).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def mark_communication_message_sent(request, message_id):
    message = get_object_or_404(
        CommunicationMessage.objects.select_related('thread'), pk=message_id,
    )
    serializer = CommunicationMarkSentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        message = communication_service.mark_sent(
            message,
            actor=request.user,
            **serializer.validated_data,
        )
    except communication_service.CommunicationError as exc:
        return _business_error(exc)
    return Response(CommunicationMessageSerializer(
        get_object_or_404(_message_queryset(), pk=message.pk),
    ).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def void_communication_message(request, message_id):
    message = get_object_or_404(
        CommunicationMessage.objects.select_related('thread'), pk=message_id,
    )
    serializer = CommunicationVoidSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        message = communication_service.void_message(
            message, actor=request.user, **serializer.validated_data,
        )
    except communication_service.CommunicationError as exc:
        return _business_error(exc)
    return Response(CommunicationMessageSerializer(
        get_object_or_404(_message_queryset(), pk=message.pk),
    ).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def correct_communication_message_date(request, message_id):
    message = get_object_or_404(
        CommunicationMessage.objects.select_related('thread'), pk=message_id,
    )
    serializer = CommunicationDateCorrectionWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        message = communication_service.correct_message_date(
            message, actor=request.user, **serializer.validated_data,
        )
    except communication_service.CommunicationError as exc:
        return _business_error(exc)
    return Response(CommunicationMessageSerializer(
        get_object_or_404(_message_queryset(), pk=message.pk),
    ).data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def document_communication_usage(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    messages = _message_queryset().filter(documents=document).select_related(
        'thread__client__user', 'thread__project',
    )
    rows = []
    for message in messages.order_by('-occurred_at', '-id'):
        rows.append({
            'message': CommunicationMessageSerializer(message).data,
            'thread': {
                'id': message.thread_id,
                'title': message.thread.title,
                'client_id': message.thread.client_id,
                'client_name': message.thread.client.user.get_full_name()
                or message.thread.client.company_name
                or message.thread.client.user.email,
                'project_id': message.thread.project_id,
                'project_name': message.thread.project.name if message.thread.project else '',
            },
        })
    return Response({
        'document_id': document.id,
        'document_title': document.title,
        'count': len(rows),
        'results': rows,
    })
