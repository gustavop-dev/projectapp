"""MCP tools for consulting and recording client communications.

The handlers deliberately reuse the panel serializers and service layer so a
conversation cannot bypass thread, message, reply, or document guardrails.
Marking a message as sent records an external fact; it never delivers email or
WhatsApp itself.
"""
import json

from django.core.paginator import Paginator

from content.mcp.actor import mcp_actor
from content.mcp.protocol import ToolError
from content.models import CommunicationMessage
from content.serializers.communication import (
    CommunicationMarkSentSerializer,
    CommunicationMessageCreateSerializer,
    CommunicationMessageSerializer,
    CommunicationThreadDetailSerializer,
    CommunicationThreadListSerializer,
    CommunicationThreadWriteSerializer,
)
from content.services import communication_query_service, communication_service


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


def _thread_or_error(thread_id):
    thread_id = _positive_int(thread_id, field='thread_id')
    thread = (
        communication_query_service.thread_queryset()
        .filter(pk=thread_id)
        .first()
    )
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
    query_params = {
        key: value for key, value in arguments.items()
        if key not in {'client_id', 'project_id', 'page', 'page_size'}
    }
    if arguments.get('client_id') not in (None, ''):
        query_params['client'] = arguments['client_id']
    if arguments.get('project_id') not in (None, ''):
        query_params['project'] = arguments['project_id']
    try:
        filters = communication_query_service.parse_filters(query_params)
    except communication_query_service.CommunicationFilterError as exc:
        raise ToolError(_serializer_error(exc.errors)) from exc

    queryset = communication_query_service.apply_filters(
        communication_query_service.thread_queryset(), filters,
    )

    page_number = _positive_int(arguments.get('page'), field='page', default=1)
    page_size = _positive_int(
        arguments.get('page_size'), field='page_size', default=20, maximum=100,
    )
    paginator = Paginator(
        communication_query_service.order_threads(queryset, filters.order), page_size,
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
        communication_query_service.thread_queryset().get(pk=thread.pk),
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
        communication_query_service.message_queryset().get(pk=message.pk),
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
        communication_query_service.message_queryset().get(pk=message.pk),
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
            'canal, dirección, estado del hilo, respuesta o estado/fecha de sus mensajes.'
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
                'reply_status': {'type': 'string', 'enum': ['answered', 'unanswered'], 'description': 'Respondido o sin respuesta; aplica a mensajes salientes enviados y no anulados.'},
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
