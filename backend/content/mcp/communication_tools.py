"""MCP tools for consulting and recording client communications.

The handlers deliberately reuse the panel serializers and service layer so a
conversation cannot bypass thread, message, reply, or document guardrails.
Marking a message as sent records an external fact; it never delivers email or
WhatsApp itself.
"""
import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.dateparse import parse_date, parse_datetime

from content.mcp.actor import mcp_actor
from content.mcp.protocol import ToolError
from content.models import CommunicationMessage, CommunicationThread
from content.serializers.communication import (
    CommunicationMarkSentSerializer,
    CommunicationMessageCreateSerializer,
    CommunicationMessageSerializer,
    CommunicationThreadDetailSerializer,
    CommunicationThreadListSerializer,
    CommunicationThreadWriteSerializer,
)
from content.services import communication_service
from content.views.communication import _message_queryset, _thread_queryset


def _serializer_error(errors):
    return 'Datos inválidos: ' + json.dumps(errors, ensure_ascii=False, default=str)


def _positive_int(value, *, field, default=None, maximum=None):
    if value in (None, ''):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ToolError(f'{field} debe ser un número entero.') from exc
    if parsed < 1:
        raise ToolError(f'{field} debe ser mayor que cero.')
    return min(parsed, maximum) if maximum is not None else parsed


def _date_filter(value, *, field, end=False):
    if not value:
        return None
    parsed_datetime = parse_datetime(value)
    if parsed_datetime:
        lookup = 'messages__occurred_at__lte' if end else 'messages__occurred_at__gte'
        return lookup, parsed_datetime
    parsed_date = parse_date(value)
    if parsed_date:
        lookup = 'messages__occurred_at__date__lte' if end else 'messages__occurred_at__date__gte'
        return lookup, parsed_date
    raise ToolError(f'{field} debe ser una fecha ISO válida.')


def _thread_or_error(thread_id):
    thread_id = _positive_int(thread_id, field='thread_id')
    thread = _thread_queryset().filter(pk=thread_id).first()
    if thread is None:
        raise ToolError(f'No existe un hilo con id={thread_id}.')
    return thread


def _message_or_error(message_id):
    message_id = _positive_int(message_id, field='message_id')
    message = (
        CommunicationMessage.objects.select_related('thread')
        .filter(pk=message_id)
        .first()
    )
    if message is None:
        raise ToolError(f'No existe un mensaje con id={message_id}.')
    return message


def list_threads(arguments):
    """Return the same filtered, paginated thread list exposed by the panel."""
    queryset = _thread_queryset()

    for argument_name, model_field in (
        ('client_id', 'client_id'),
        ('project_id', 'project_id'),
    ):
        if arguments.get(argument_name) not in (None, ''):
            queryset = queryset.filter(**{
                model_field: _positive_int(arguments[argument_name], field=argument_name),
            })

    thread_status = arguments.get('status')
    if thread_status:
        valid = {value for value, _ in CommunicationThread.Status.choices}
        if thread_status not in valid:
            raise ToolError(f'status inválido; usa uno de {sorted(valid)}.')
        queryset = queryset.filter(status=thread_status)

    for field, choices in (
        ('channel', CommunicationMessage.Channel.choices),
        ('direction', CommunicationMessage.Direction.choices),
        ('message_status', CommunicationMessage.Status.choices),
    ):
        value = arguments.get(field)
        if not value:
            continue
        valid = {choice for choice, _ in choices}
        if value not in valid:
            raise ToolError(f'{field} inválido; usa uno de {sorted(valid)}.')
        model_field = 'status' if field == 'message_status' else field
        queryset = queryset.filter(**{f'messages__{model_field}': value})

    for field, end in (('date_from', False), ('date_to', True)):
        parsed = _date_filter(arguments.get(field), field=field, end=end)
        if parsed:
            queryset = queryset.filter(**{parsed[0]: parsed[1]})

    query = (arguments.get('q') or '').strip()
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

    page_number = _positive_int(arguments.get('page'), field='page', default=1)
    page_size = _positive_int(
        arguments.get('page_size'), field='page_size', default=20, maximum=100,
    )
    paginator = Paginator(
        queryset.distinct().order_by('-last_activity_at', '-id'), page_size,
    )
    page = paginator.get_page(page_number)
    return {
        'results': CommunicationThreadListSerializer(page.object_list, many=True).data,
        'count': paginator.count,
        'page': page.number,
        'num_pages': paginator.num_pages,
    }


def get_thread(arguments):
    """Open one complete thread, including messages and document references."""
    return CommunicationThreadDetailSerializer(
        _thread_or_error(arguments.get('thread_id')),
    ).data


def create_thread(arguments):
    data = {
        'client': arguments.get('client_id'),
        'title': arguments.get('title'),
    }
    if 'project_id' in arguments:
        data['project'] = arguments.get('project_id')
    serializer = CommunicationThreadWriteSerializer(data=data)
    if not serializer.is_valid():
        raise ToolError(_serializer_error(serializer.errors))
    try:
        thread = communication_service.create_thread(
            actor=mcp_actor(), **serializer.validated_data,
        )
    except communication_service.CommunicationError as exc:
        raise ToolError(str(exc.args[0] if exc.args else exc)) from exc
    return CommunicationThreadDetailSerializer(
        _thread_queryset().get(pk=thread.pk),
    ).data


def create_message(arguments):
    thread = _thread_or_error(arguments.get('thread_id'))
    data = {
        field: arguments[field]
        for field in (
            'channel', 'direction', 'subject', 'content', 'occurred_at',
            'document_ids',
        )
        if field in arguments
    }
    if 'reply_to_id' in arguments:
        data['reply_to'] = arguments.get('reply_to_id')
    serializer = CommunicationMessageCreateSerializer(data=data)
    if not serializer.is_valid():
        raise ToolError(_serializer_error(serializer.errors))
    validated_data = dict(serializer.validated_data)
    document_ids = validated_data.pop('document_ids', [])
    try:
        message = communication_service.create_message(
            thread=thread,
            actor=mcp_actor(),
            document_ids=document_ids,
            **validated_data,
        )
    except communication_service.CommunicationError as exc:
        raise ToolError(str(exc.args[0] if exc.args else exc)) from exc
    return CommunicationMessageSerializer(
        _message_queryset().get(pk=message.pk),
    ).data


def mark_message_sent(arguments):
    message = _message_or_error(arguments.get('message_id'))
    data = {
        'occurred_at': arguments['occurred_at'],
    } if 'occurred_at' in arguments else {}
    serializer = CommunicationMarkSentSerializer(data=data)
    if not serializer.is_valid():
        raise ToolError(_serializer_error(serializer.errors))
    try:
        communication_service.mark_sent(
            message,
            actor=mcp_actor(),
            **serializer.validated_data,
        )
    except communication_service.CommunicationError as exc:
        raise ToolError(str(exc.args[0] if exc.args else exc)) from exc
    return CommunicationMessageSerializer(
        _message_queryset().get(pk=message.pk),
    ).data


_THREAD_ID = {
    'thread_id': {
        'type': 'integer',
        'description': 'ID del hilo de comunicaciones que se quiere abrir o alimentar.',
    },
}


COMMUNICATION_TOOLS = [
    {
        'name': 'list_threads',
        'description': (
            'Lista hilos de comunicaciones, ordenados por actividad reciente. '
            'Úsala para localizar conversaciones por cliente, proyecto, texto, '
            'canal, dirección, estado del hilo o estado/fecha de sus mensajes.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'client_id': {'type': 'integer', 'description': 'Filtra por el ID del perfil de cliente.'},
                'project_id': {'type': 'integer', 'description': 'Filtra por el ID del proyecto.'},
                'status': {'type': 'string', 'enum': ['open', 'closed'], 'description': 'Estado actual del hilo.'},
                'channel': {'type': 'string', 'enum': ['email', 'whatsapp'], 'description': 'Canal de al menos un mensaje.'},
                'direction': {'type': 'string', 'enum': ['outgoing', 'incoming'], 'description': 'Dirección de al menos un mensaje.'},
                'message_status': {'type': 'string', 'enum': ['draft', 'sent', 'received', 'failed'], 'description': 'Estado de al menos un mensaje.'},
                'date_from': {'type': 'string', 'description': 'Fecha o fecha-hora ISO mínima de los mensajes.'},
                'date_to': {'type': 'string', 'description': 'Fecha o fecha-hora ISO máxima de los mensajes.'},
                'q': {'type': 'string', 'description': 'Texto en título, cliente, asunto o contenido.'},
                'page': {'type': 'integer', 'minimum': 1, 'description': 'Página, desde 1.'},
                'page_size': {'type': 'integer', 'minimum': 1, 'maximum': 100, 'description': 'Resultados por página; máximo 100.'},
            },
            'additionalProperties': False,
        },
        'handler': list_threads,
    },
    {
        'name': 'get_thread',
        'description': (
            'Abre un hilo completo con sus mensajes cronológicos, estados, '
            'respuestas, documentos referenciados y correcciones de fecha. '
            'No modifica la conversación.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': _THREAD_ID,
            'required': ['thread_id'],
            'additionalProperties': False,
        },
        'handler': get_thread,
    },
    {
        'name': 'create_thread',
        'description': (
            'Crea un hilo vacío para un cliente existente. client_id es '
            'obligatorio; project_id es opcional pero, si se envía, el proyecto '
            'debe pertenecer a ese cliente. El hilo nace abierto.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'client_id': {'type': 'integer', 'description': 'ID obligatorio del perfil de cliente.'},
                'project_id': {'type': ['integer', 'null'], 'description': 'ID opcional de un proyecto del mismo cliente.'},
                'title': {'type': 'string', 'description': 'Título descriptivo del hilo.'},
            },
            'required': ['client_id', 'title'],
            'additionalProperties': False,
        },
        'handler': create_thread,
    },
    {
        'name': 'create_message',
        'description': (
            'Agrega un mensaje a un hilo abierto. Los entrantes se registran '
            'como recibidos y los salientes como borradores; esta herramienta '
            'no envía correo ni WhatsApp. Puede responder otro mensaje del mismo '
            'hilo y referenciar documentos existentes del cliente.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                **_THREAD_ID,
                'channel': {'type': 'string', 'enum': ['email', 'whatsapp'], 'description': 'Canal en el que ocurrió u ocurrirá el mensaje.'},
                'direction': {'type': 'string', 'enum': ['outgoing', 'incoming'], 'description': 'outgoing para ProjectApp→cliente; incoming para cliente→ProjectApp.'},
                'subject': {'type': 'string', 'description': 'Asunto obligatorio en email y vacío en WhatsApp.'},
                'content': {'type': 'string', 'description': 'Texto completo del mensaje.'},
                'occurred_at': {'type': 'string', 'description': 'Fecha-hora ISO; usa la fecha actual si se omite.'},
                'reply_to_id': {'type': ['integer', 'null'], 'description': 'Mensaje previo del mismo hilo y dirección opuesta.'},
                'document_ids': {'type': 'array', 'items': {'type': 'integer'}, 'description': 'Documentos existentes del mismo cliente para referenciar.'},
            },
            'required': ['thread_id', 'channel', 'direction', 'content'],
            'additionalProperties': False,
        },
        'handler': create_message,
    },
    {
        'name': 'mark_message_sent',
        'description': (
            'Marca como enviado un borrador saliente activo y, opcionalmente, '
            'corrige la fecha-hora del envío. Sólo registra que el envío ocurrió '
            'fuera del sistema; no entrega el mensaje por ningún canal.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'message_id': {'type': 'integer', 'description': 'ID del borrador saliente que ya fue enviado externamente.'},
                'occurred_at': {'type': 'string', 'description': 'Fecha-hora ISO real del envío; conserva la actual si se omite.'},
            },
            'required': ['message_id'],
            'additionalProperties': False,
        },
        'handler': mark_message_sent,
    },
]
