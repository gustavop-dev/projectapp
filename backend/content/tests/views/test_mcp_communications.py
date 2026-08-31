"""Behavior tests for the Communications MCP connector."""
import json
from datetime import UTC, datetime
from importlib import import_module

import pytest
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model

from accounts.models import Project, UserProfile
from content.models import (
    CommunicationMessage,
    CommunicationThread,
    Document,
    DocumentType,
    McpConnector,
)
from content.services import communication_service


pytestmark = pytest.mark.django_db
User = get_user_model()
OCCURRED_AT = datetime(2026, 8, 26, 15, 0, tzinfo=UTC)


@pytest.fixture
def communications_connector():
    connector, _ = McpConnector.objects.get_or_create(
        slug='communications', defaults={'name': 'Gestor de Comunicaciones'},
    )
    connector.is_active = True
    connector.save(update_fields=['is_active'])
    return connector, connector.generate_token()


@pytest.fixture
def mcp_superuser():
    return User.objects.create_superuser(
        username='mcp_communications',
        email='mcp-communications@example.com',
        password='testpass123',
    )


def make_client(email, *, first_name='Ana'):
    user = User.objects.create_user(
        username=email,
        email=email,
        first_name=first_name,
        password='testpass123',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


def rpc(method, params=None):
    message = {'jsonrpc': '2.0', 'id': 1, 'method': method}
    if params is not None:
        message['params'] = params
    return message


def call_tool(api_client, token, name, arguments):
    return api_client.post(
        f'/api/mcp/communications/{token}/',
        rpc('tools/call', {'name': name, 'arguments': arguments}),
        format='json',
    )


def payload(response):
    return json.loads(response.data['result']['content'][0]['text'])


def test_seeded_communications_connector_has_safe_defaults():
    connector = McpConnector.objects.get(slug='communications')

    assert (
        connector.is_active,
        connector.token_hash,
        connector.token_prefix,
    ) == (False, '', '')


def test_seed_refresh_preserves_existing_connector_credentials():
    connector = McpConnector.objects.get(slug='blog')
    connector.is_active = True
    connector.token_hash = 'a' * 64
    connector.token_prefix = 'existing'
    connector.save(update_fields=['is_active', 'token_hash', 'token_prefix'])

    migration = import_module('content.migrations.0212_seed_communications_mcp')
    migration.seed_and_refresh_connectors(django_apps, None)
    connector.refresh_from_db()

    assert (
        connector.is_active,
        connector.token_hash,
        connector.token_prefix,
    ) == (True, 'a' * 64, 'existing')


def test_tool_list_exposes_minimum_communications_surface(
    api_client, communications_connector,
):
    _, token = communications_connector

    response = api_client.post(
        f'/api/mcp/communications/{token}/', rpc('tools/list'), format='json',
    )

    assert [tool['name'] for tool in response.data['result']['tools']] == [
        'list_threads',
        'get_thread',
        'create_thread',
        'create_message',
        'mark_message_sent',
    ]


def test_list_threads_schema_exposes_reply_status(
    api_client, communications_connector,
):
    _, token = communications_connector

    response = api_client.post(
        f'/api/mcp/communications/{token}/', rpc('tools/list'), format='json',
    )

    list_threads_tool = next(
        tool for tool in response.data['result']['tools']
        if tool['name'] == 'list_threads'
    )
    assert list_threads_tool['inputSchema']['properties']['reply_status']['enum'] == [
        'answered', 'unanswered',
    ]


def test_tool_list_describes_project_text_search(
    api_client, communications_connector,
):
    _, token = communications_connector

    response = api_client.post(
        f'/api/mcp/communications/{token}/', rpc('tools/list'), format='json',
    )

    list_tool = next(
        tool for tool in response.data['result']['tools']
        if tool['name'] == 'list_threads'
    )
    assert 'proyecto' in list_tool['inputSchema']['properties']['q']['description']


def test_create_thread_requires_client(
    api_client, communications_connector, mcp_superuser,
):
    _, token = communications_connector

    response = call_tool(api_client, token, 'create_thread', {'title': 'Sin cliente'})

    assert response.data['result']['isError'] is True
    # La madre que el proyecto provisiona al crearse no cuenta: lo que se
    # verifica es que el tool NO cree un hilo, y esa no la creo el tool.
    assert CommunicationThread.objects.filter(managed_project__isnull=True).count() == 0


def test_create_thread_rejects_project_from_another_client(
    api_client, communications_connector, mcp_superuser,
):
    owner = make_client('owner-mcp@example.com')
    other = make_client('other-mcp@example.com')
    project = Project.objects.create(name='Proyecto ajeno', client=other.user)
    _, token = communications_connector

    response = call_tool(api_client, token, 'create_thread', {
        'client_id': owner.id,
        'project_id': project.id,
        'title': 'Hilo inválido',
    })

    assert response.data['result']['isError'] is True
    # La madre que el proyecto provisiona al crearse no cuenta: lo que se
    # verifica es que el tool NO cree un hilo, y esa no la creo el tool.
    assert CommunicationThread.objects.filter(managed_project__isnull=True).count() == 0


def test_create_and_get_thread_preserve_client_project(
    api_client, communications_connector, mcp_superuser,
):
    client = make_client('thread-mcp@example.com')
    project = Project.objects.create(name='Portal MCP', client=client.user)
    _, token = communications_connector

    created = call_tool(api_client, token, 'create_thread', {
        'client_id': client.id,
        'project_id': project.id,
        'title': 'Aprobación MCP',
    })
    opened = call_tool(
        api_client, token, 'get_thread', {'thread_id': payload(created)['id']},
    )

    assert payload(opened)['client_id'] == client.id
    assert payload(opened)['project_id'] == project.id
    assert payload(opened)['messages'] == []


def test_list_threads_filters_by_client(
    api_client, communications_connector, mcp_superuser,
):
    first = make_client('first-mcp@example.com')
    second = make_client('second-mcp@example.com')
    communication_service.create_thread(actor=mcp_superuser, client=first, title='Primero')
    communication_service.create_thread(actor=mcp_superuser, client=second, title='Segundo')
    _, token = communications_connector

    response = call_tool(
        api_client, token, 'list_threads', {'client_id': first.id},
    )

    assert [row['title'] for row in payload(response)['results']] == ['Primero']


def test_list_threads_filters_sent_messages_without_reply(
    api_client, communications_connector, mcp_superuser,
):
    client = make_client('unanswered-mcp@example.com')
    pending = communication_service.create_thread(
        actor=mcp_superuser, client=client, title='Pendiente',
    )
    answered = communication_service.create_thread(
        actor=mcp_superuser, client=client, title='Respondido',
    )
    communication_service.create_message(
        thread=pending,
        actor=mcp_superuser,
        channel='whatsapp',
        direction='outgoing',
        status='sent',
        subject='',
        content='¿Confirmas?',
        occurred_at=OCCURRED_AT,
    )
    sent = communication_service.create_message(
        thread=answered,
        actor=mcp_superuser,
        channel='whatsapp',
        direction='outgoing',
        status='sent',
        subject='',
        content='¿Confirmas?',
        occurred_at=OCCURRED_AT,
    )
    communication_service.create_message(
        thread=answered,
        actor=mcp_superuser,
        channel='whatsapp',
        direction='incoming',
        status='received',
        subject='',
        content='Confirmado.',
        occurred_at=OCCURRED_AT,
        reply_to=sent,
    )
    _, token = communications_connector

    response = call_tool(
        api_client, token, 'list_threads', {'reply_status': 'unanswered'},
    )

    assert [row['title'] for row in payload(response)['results']] == ['Pendiente']


def test_list_threads_searches_project_name(
    api_client, communications_connector, mcp_superuser,
):
    client = make_client('project-search-mcp@example.com')
    matching_project = Project.objects.create(
        name='Portal Boreal MCP', client=client.user,
    )
    other_project = Project.objects.create(
        name='Tienda Austral MCP', client=client.user,
    )
    communication_service.create_thread(
        actor=mcp_superuser,
        client=client,
        project=matching_project,
        title='Revisión MCP',
    )
    communication_service.create_thread(
        actor=mcp_superuser,
        client=client,
        project=other_project,
        title='Revisión MCP',
    )
    _, token = communications_connector

    response = call_tool(
        api_client, token, 'list_threads', {'q': 'boreal'},
    )

    # La madre del proyecto lleva su mismo nombre, asi que tambien casa con la
    # busqueda: se compara sobre los hilos manuales, que es lo que el test mide.
    rows = [
        row for row in payload(response)['results']
        if row['thread_kind'] == 'manual'
    ]
    assert [row['project_name'] for row in rows] == [
        'Portal Boreal MCP',
    ]


def test_incoming_message_is_recorded_as_received(
    api_client, communications_connector, mcp_superuser,
):
    client = make_client('incoming-mcp@example.com')
    thread = communication_service.create_thread(
        actor=mcp_superuser, client=client, title='Respuesta recibida',
    )
    _, token = communications_connector

    response = call_tool(api_client, token, 'create_message', {
        'thread_id': thread.id,
        'channel': 'whatsapp',
        'direction': 'incoming',
        'content': 'Confirmo la aprobación.',
        'occurred_at': OCCURRED_AT.isoformat(),
    })

    assert payload(response)['status'] == CommunicationMessage.Status.RECEIVED


def test_outgoing_message_is_draft_and_references_document(
    api_client, communications_connector, mcp_superuser,
):
    client = make_client('document-mcp@example.com')
    thread = communication_service.create_thread(
        actor=mcp_superuser, client=client, title='Documento',
    )
    document_type, _ = DocumentType.objects.get_or_create(
        code='markdown', defaults={'name': 'Markdown', 'label': 'Markdown'},
    )
    document = Document.objects.create(
        title='Propuesta aprobada',
        document_type=document_type,
        client_user=client.user,
    )
    _, token = communications_connector

    response = call_tool(api_client, token, 'create_message', {
        'thread_id': thread.id,
        'channel': 'email',
        'direction': 'outgoing',
        'subject': 'Propuesta',
        'content': 'Adjunto la propuesta aprobada.',
        'document_ids': [document.id],
    })

    result = payload(response)
    assert result['status'] == CommunicationMessage.Status.DRAFT
    assert result['documents'][0]['id'] == document.id


def test_message_rejects_document_from_another_client(
    api_client, communications_connector, mcp_superuser,
):
    owner = make_client('doc-owner-mcp@example.com')
    other = make_client('doc-other-mcp@example.com')
    thread = communication_service.create_thread(
        actor=mcp_superuser, client=owner, title='Documento ajeno',
    )
    document_type, _ = DocumentType.objects.get_or_create(
        code='markdown', defaults={'name': 'Markdown', 'label': 'Markdown'},
    )
    document = Document.objects.create(
        title='Documento ajeno', document_type=document_type, client_user=other.user,
    )
    _, token = communications_connector

    response = call_tool(api_client, token, 'create_message', {
        'thread_id': thread.id,
        'channel': 'whatsapp',
        'direction': 'outgoing',
        'content': 'No debe guardarse.',
        'document_ids': [document.id],
    })

    assert response.data['result']['isError'] is True
    assert CommunicationMessage.objects.count() == 0


def test_closed_thread_rejects_message(
    api_client, communications_connector, mcp_superuser,
):
    client = make_client('closed-mcp@example.com')
    thread = communication_service.create_thread(
        actor=mcp_superuser, client=client, title='Cerrado',
    )
    communication_service.close_thread(thread, actor=mcp_superuser)
    _, token = communications_connector

    response = call_tool(api_client, token, 'create_message', {
        'thread_id': thread.id,
        'channel': 'whatsapp',
        'direction': 'incoming',
        'content': 'Llegó tarde.',
    })

    assert response.data['result']['isError'] is True
    assert CommunicationMessage.objects.count() == 0


def test_mark_message_sent_transitions_only_the_draft(
    api_client, communications_connector, mcp_superuser,
):
    client = make_client('sent-mcp@example.com')
    thread = communication_service.create_thread(
        actor=mcp_superuser, client=client, title='Envío',
    )
    message = communication_service.create_message(
        thread=thread,
        actor=mcp_superuser,
        channel='whatsapp',
        direction='outgoing',
        status='draft',
        subject='',
        content='Mensaje enviado externamente.',
        occurred_at=OCCURRED_AT,
    )
    _, token = communications_connector

    response = call_tool(api_client, token, 'mark_message_sent', {
        'message_id': message.id,
    })

    assert payload(response)['status'] == CommunicationMessage.Status.SENT


def test_mark_received_message_as_sent_is_rejected(
    api_client, communications_connector, mcp_superuser,
):
    client = make_client('received-mcp@example.com')
    thread = communication_service.create_thread(
        actor=mcp_superuser, client=client, title='Entrante',
    )
    message = communication_service.create_message(
        thread=thread,
        actor=mcp_superuser,
        channel='whatsapp',
        direction='incoming',
        status='received',
        subject='',
        content='Mensaje entrante.',
        occurred_at=OCCURRED_AT,
    )
    _, token = communications_connector

    response = call_tool(api_client, token, 'mark_message_sent', {
        'message_id': message.id,
    })

    assert response.data['result']['isError'] is True
    message.refresh_from_db()
    assert message.status == CommunicationMessage.Status.RECEIVED
