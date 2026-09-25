"""MCP parity tests for the communications filing hierarchy."""
import json

import pytest
from accounts.models import UserProfile
from django.contrib.auth import get_user_model

from content.models import CommunicationFolder, CommunicationThread, McpConnector
from content.services import communication_service


pytestmark = pytest.mark.django_db
User = get_user_model()


def make_client(email):
    user = User.objects.create_user(
        username=email, email=email, password='testpass123',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


@pytest.fixture
def communications_connector():
    connector, _ = McpConnector.objects.get_or_create(
        slug='communications', defaults={'name': 'Gestor de Comunicaciones'},
    )
    connector.is_active = True
    connector.save(update_fields=['is_active'])
    return connector, connector.generate_token()


def call_tool(api_client, token, name, arguments):
    return api_client.post(
        f'/api/mcp/communications/{token}/',
        {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/call',
            'params': {'name': name, 'arguments': arguments},
        },
        format='json',
    )


def tool_payload(response):
    return json.loads(response.data['result']['content'][0]['text'])


def test_mcp_creates_updates_lists_and_deletes_an_empty_folder(api_client, communications_connector):
    """Falla si MCP no ofrece el mismo ciclo CRUD observable que el panel."""
    client = make_client('mcp-folder@example.com')
    _, token = communications_connector

    created = call_tool(api_client, token, 'create_folder', {
        'name': 'Preparación', 'client': client.id,
    })
    folder_id = tool_payload(created)['id']
    updated = call_tool(api_client, token, 'update_folder', {
        'folder_id': folder_id, 'name': 'Preparación final',
    })
    listed = call_tool(api_client, token, 'list_folders', {'client_id': client.id})
    deleted = call_tool(api_client, token, 'delete_folder', {'folder_id': folder_id})

    assert created.data['result']['isError'] is False
    assert tool_payload(updated)['name'] == 'Preparación final'
    assert tool_payload(listed)['results'][0]['id'] == folder_id
    assert tool_payload(deleted) == {'deleted': True, 'id': folder_id}
    assert CommunicationFolder.objects.filter(pk=folder_id).exists() is False


def test_mcp_rejects_a_foreign_parent_without_creating_the_folder(api_client, communications_connector):
    """Falla si MCP puede cruzar los árboles de comunicaciones de dos clientes."""
    owner = make_client('mcp-folder-owner@example.com')
    foreign = make_client('mcp-folder-foreign@example.com')
    foreign_parent = CommunicationFolder.objects.create(name='Ajena', client=foreign)
    _, token = communications_connector

    response = call_tool(api_client, token, 'create_folder', {
        'name': 'No creada', 'client': owner.id, 'parent': foreign_parent.id,
    })

    assert response.data['result']['isError'] is True
    assert 'mismo contexto' in response.data['result']['content'][0]['text']
    assert CommunicationFolder.objects.filter(client=owner).exists() is False


def test_mcp_rejects_unknown_folder_arguments(api_client, communications_connector):
    """Falla si MCP acepta campos que no pertenecen al contrato de carpetas."""
    client = make_client('mcp-folder-unknown@example.com')
    _, token = communications_connector

    response = call_tool(api_client, token, 'create_folder', {
        'name': 'Valida contrato', 'client': client.id, 'unexpected': True,
    })

    assert response.data['result']['isError'] is True
    assert 'Campos no permitidos: unexpected.' in response.data['result']['content'][0]['text']
    assert CommunicationFolder.objects.filter(client=client).exists() is False


def test_mcp_files_a_closed_thread_and_lists_it_by_folder(api_client, communications_connector, admin_user):
    """Falla si MCP no permite organizar un hilo cerrado o filtrarlo por carpeta."""
    client = make_client('mcp-folder-thread@example.com')
    folder = CommunicationFolder.objects.create(name='Cerrados', client=client)
    thread = communication_service.create_thread(
        actor=admin_user, client=client, title='Histórico MCP',
    )
    communication_service.close_thread(thread, actor=admin_user)
    _, token = communications_connector

    updated = call_tool(api_client, token, 'update_thread', {
        'thread_id': thread.id, 'folder_id': folder.id,
    })
    listed = call_tool(api_client, token, 'list_threads', {'folder': folder.id})

    assert updated.data['result']['isError'] is False
    assert tool_payload(updated)['folder_id'] == folder.id
    assert [row['id'] for row in tool_payload(listed)['results']] == [thread.id]
    thread.refresh_from_db()
    assert thread.folder_id == folder.id
