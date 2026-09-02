"""Cross-cutting behavior of the operational MCP platform."""
import hashlib
from datetime import timedelta
from urllib.parse import urlsplit

import pytest
from django.utils import timezone as tz
from rest_framework.test import APIRequestFactory

from content.mcp.common_tools import build_common_tools
from content.mcp.context import McpExecutionContext, use_mcp_context
from content.mcp.protocol import ToolError, handle_message
from content.mcp.registry import normalize_tools
from content.mcp.upload_tools import begin_upload, complete_upload, store_artifact
from content.models import McpConnector, McpCredential, McpRequestLog, Task


pytestmark = pytest.mark.django_db


def _rpc(method, params=None, msg_id=1):
    message = {'jsonrpc': '2.0', 'id': msg_id, 'method': method}
    if params is not None:
        message['params'] = params
    return message


def _modern_rpc(method, params=None, msg_id=1):
    payload = dict(params or {})
    payload['_meta'] = {
        'io.modelcontextprotocol/protocolVersion': '2026-07-28',
        'io.modelcontextprotocol/clientCapabilities': {},
        'io.modelcontextprotocol/clientInfo': {
            'name': 'projectapp-tests',
            'version': '1.0.0',
        },
    }
    return _rpc(method, payload, msg_id)


def _call(api_client, slug, token, name, arguments=None, *, bearer=False):
    url = f'/api/mcp/{slug}/' if bearer else f'/api/mcp/{slug}/{token}/'
    headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'} if bearer else {}
    return api_client.post(
        url,
        _rpc('tools/call', {'name': name, 'arguments': arguments or {}}),
        format='json',
        **headers,
    )


@pytest.fixture
def tasks_connector():
    connector, _ = McpConnector.objects.get_or_create(
        slug='tasks', defaults={'name': 'Gestor de Tareas'},
    )
    connector.is_active = True
    connector.save(update_fields=['is_active'])
    token = connector.generate_token()
    return connector, token


@pytest.fixture
def confirmation_runtime(tasks_connector):
    connector, _ = tasks_connector
    credential = connector.credentials.get(label='Default')
    calls = []

    def destroy(arguments):
        calls.append(arguments['record_id'])
        return {'deleted': arguments['record_id']}

    sensitive = {
        'name': 'delete_record',
        'description': 'Elimina de forma controlada el registro solicitado.',
        'risk': 'sensitive',
        'requires_confirmation': True,
        'input_schema': {
            'type': 'object',
            'properties': {'record_id': {'type': 'integer'}},
            'required': ['record_id'],
        },
        'handler': destroy,
    }
    tools = []
    tools.extend(normalize_tools([
        sensitive,
        *build_common_tools('tasks', lambda: tools),
    ], 'tasks'))
    context = McpExecutionContext(
        connector=connector,
        credential=credential,
        request_id='test-request-id',
    )
    return tools, context, calls


def _preview(tools, context):
    with use_mcp_context(context):
        _, response = handle_message(
            _rpc('tools/call', {
                'name': 'delete_record',
                'arguments': {'record_id': 42},
            }),
            tools,
            context=context,
        )
    return response['result']['structuredContent']


def test_default_token_is_mirrored_into_a_scoped_credential(tasks_connector):
    connector, token = tasks_connector

    credential = connector.credentials.get(label='Default')

    assert credential.check_token(token) is True
    assert credential.allowed_tools == []


def test_service_actor_does_not_take_over_a_matching_human_username(
    api_client, django_user_model, tasks_connector,
):
    connector, token = tasks_connector
    human = django_user_model.objects.create_user(
        username='mcp_tasks',
        password='human-password',
        is_staff=False,
        is_superuser=False,
    )

    response = _call(api_client, 'tasks', token, 'list_tasks')

    human.refresh_from_db()
    credential = connector.credentials.get(label='Default')
    assert response.status_code == 200
    assert credential.actor_id != human.id
    assert credential.actor.username.startswith('mcp_tasks_')
    assert human.is_superuser is False
    assert human.has_usable_password() is True


def test_panel_creates_a_scoped_credential_and_reveals_the_secret_once(
    super_client, tasks_connector,
):
    connector, _ = tasks_connector

    response = super_client.post(
        '/api/mcp-connectors/tasks/credentials/',
        {'label': 'Sólo tablero', 'allowed_tools': ['list_tasks']},
        format='json',
    )

    assert response.status_code == 201
    assert response.data['credential'] not in McpCredential.objects.get(
        pk=response.data['id'],
    ).token_hash
    assert response.data['connector_url'].startswith('http://testserver/api/mcp/tasks/')


def test_panel_rejects_an_oversized_credential_label(super_client, tasks_connector):
    response = super_client.post(
        '/api/mcp-connectors/tasks/credentials/',
        {'label': 'x' * 101, 'allowed_tools': ['list_tasks']},
        format='json',
    )

    assert response.status_code == 400
    assert response.data['label'] == 'La etiqueta no puede superar 100 caracteres.'


def test_panel_normalizes_a_naive_future_credential_expiry(
    super_client, tasks_connector,
):
    expires_at = (tz.now() + timedelta(days=1)).replace(tzinfo=None)

    response = super_client.post(
        '/api/mcp-connectors/tasks/credentials/',
        {
            'label': 'Vigencia local',
            'allowed_tools': ['list_tasks'],
            'expires_at': expires_at.isoformat(),
        },
        format='json',
    )

    assert response.status_code == 201
    assert McpCredential.objects.get(pk=response.data['id']).expires_at is not None


def test_bearer_credential_can_call_an_allowed_tool(
    api_client, super_client, tasks_connector,
):
    _, _ = tasks_connector
    created = super_client.post(
        '/api/mcp-connectors/tasks/credentials/',
        {'label': 'Listar', 'allowed_tools': ['list_tasks']},
        format='json',
    )

    response = _call(
        api_client, 'tasks', created.data['credential'], 'list_tasks', bearer=True,
    )

    assert response.status_code == 200
    assert response.data['result']['isError'] is False


def test_bearer_credential_rejects_an_unlisted_tool(
    api_client, super_client, tasks_connector,
):
    _, _ = tasks_connector
    created = super_client.post(
        '/api/mcp-connectors/tasks/credentials/',
        {'label': 'Listar', 'allowed_tools': ['list_tasks']},
        format='json',
    )

    response = _call(
        api_client, 'tasks', created.data['credential'], 'get_task',
        {'task_id': 1}, bearer=True,
    )

    error = response.data['result']['structuredContent']['error']
    assert error['code'] == 'FORBIDDEN'


def test_rotating_a_scoped_credential_invalidates_its_previous_secret(
    api_client, super_client, tasks_connector,
):
    _, _ = tasks_connector
    created = super_client.post(
        '/api/mcp-connectors/tasks/credentials/',
        {'label': 'Rotable', 'allowed_tools': ['list_tasks']},
        format='json',
    )
    old_token = created.data['credential']

    rotated = super_client.post(
        f"/api/mcp-connectors/tasks/credentials/{created.data['id']}/rotate/",
        {},
        format='json',
    )

    assert _call(api_client, 'tasks', old_token, 'list_tasks').status_code == 404
    assert _call(
        api_client, 'tasks', rotated.data['credential'], 'list_tasks', bearer=True,
    ).status_code == 200


def test_revoked_credential_is_rejected_by_the_transport(
    api_client, super_client, tasks_connector,
):
    _, _ = tasks_connector
    created = super_client.post(
        '/api/mcp-connectors/tasks/credentials/',
        {'label': 'Temporal', 'allowed_tools': ['list_tasks']},
        format='json',
    )
    super_client.delete(
        f"/api/mcp-connectors/tasks/credentials/{created.data['id']}/",
    )

    response = _call(
        api_client, 'tasks', created.data['credential'], 'list_tasks', bearer=True,
    )

    assert response.status_code == 404


def test_tools_list_exposes_output_schema_and_annotations(api_client, tasks_connector):
    _, token = tasks_connector

    response = api_client.post(
        f'/api/mcp/tasks/{token}/', _rpc('tools/list'), format='json',
    )
    listed = next(
        tool for tool in response.data['result']['tools']
        if tool['name'] == 'list_tasks'
    )

    assert listed['outputSchema']['type'] == 'object'
    assert listed['annotations']['readOnlyHint'] is True


def test_sensitive_call_returns_preview_without_executing(confirmation_runtime):
    tools, context, calls = confirmation_runtime

    preview = _preview(tools, context)

    assert preview['confirmation_required'] is True
    assert calls == []


def test_confirm_action_executes_the_exact_previewed_arguments(confirmation_runtime):
    tools, context, calls = confirmation_runtime
    preview = _preview(tools, context)

    with use_mcp_context(context):
        _, response = handle_message(
            _rpc('tools/call', {
                'name': 'confirm_action',
                'arguments': {'confirmation_id': preview['confirmation_id']},
            }),
            tools,
            context=context,
        )

    assert response['result']['structuredContent']['result'] == {'deleted': 42}
    assert calls == [42]


def test_confirm_action_replay_does_not_execute_twice(confirmation_runtime):
    tools, context, calls = confirmation_runtime
    preview = _preview(tools, context)
    request = _rpc('tools/call', {
        'name': 'confirm_action',
        'arguments': {'confirmation_id': preview['confirmation_id']},
    })

    with use_mcp_context(context):
        handle_message(request, tools, context=context)
        _, replay = handle_message(request, tools, context=context)

    assert replay['result']['structuredContent']['replayed'] is True
    assert calls == [42]


def test_confirmation_cannot_cross_credentials(confirmation_runtime):
    tools, context, _ = confirmation_runtime
    preview = _preview(tools, context)
    other = McpCredential.objects.create(
        connector=context.connector,
        label='Other',
        token_hash=McpCredential.hash_token('other-token'),
    )
    foreign_context = McpExecutionContext(
        connector=context.connector,
        credential=other,
        request_id='foreign-request',
    )

    with use_mcp_context(foreign_context):
        _, response = handle_message(
            _rpc('tools/call', {
                'name': 'confirm_action',
                'arguments': {'confirmation_id': preview['confirmation_id']},
            }),
            tools,
            context=foreign_context,
        )

    assert response['result']['structuredContent']['error']['code'] == 'FORBIDDEN'


def test_signed_upload_verifies_size_and_sha256(
    api_client, settings, tmp_path, tasks_connector,
):
    settings.MEDIA_ROOT = tmp_path
    connector, _ = tasks_connector
    credential = connector.credentials.get(label='Default')
    body = b'contenido mcp'
    context = McpExecutionContext(
        connector=connector,
        credential=credential,
        request_id='upload-request',
        request=APIRequestFactory().get('/', HTTP_HOST='testserver'),
    )
    with use_mcp_context(context):
        upload = begin_upload({
            'filename': 'evidencia.txt',
            'content_type': 'text/plain',
            'size': len(body),
            'sha256': hashlib.sha256(body).hexdigest(),
        })
    path = urlsplit(upload['upload_url']).path
    received = api_client.generic('PUT', path, body, content_type='text/plain')

    with use_mcp_context(context):
        completed = complete_upload({'asset_id': upload['asset_id']})

    assert received.status_code == 200
    assert completed['sha256'] == hashlib.sha256(body).hexdigest()


def test_upload_rejects_an_extension_that_does_not_match_its_mime_type(
    tasks_connector,
):
    connector, _ = tasks_connector
    credential = connector.credentials.get(label='Default')
    context = McpExecutionContext(
        connector=connector,
        credential=credential,
        request_id='upload-extension-request',
    )

    with use_mcp_context(context), pytest.raises(ToolError, match='extensión'):
        begin_upload({
            'filename': 'evidencia.exe',
            'content_type': 'image/png',
            'size': 3,
            'sha256': hashlib.sha256(b'png').hexdigest(),
        })


def test_upload_rejects_content_that_does_not_match_its_mime_type(
    api_client, settings, tmp_path, tasks_connector,
):
    settings.MEDIA_ROOT = tmp_path
    connector, _ = tasks_connector
    credential = connector.credentials.get(label='Default')
    body = b'not really a png'
    context = McpExecutionContext(
        connector=connector,
        credential=credential,
        request_id='upload-content-request',
        request=APIRequestFactory().get('/', HTTP_HOST='testserver'),
    )
    with use_mcp_context(context):
        upload = begin_upload({
            'filename': 'evidencia.png',
            'content_type': 'image/png',
            'size': len(body),
            'sha256': hashlib.sha256(body).hexdigest(),
        })
    path = urlsplit(upload['upload_url']).path
    received = api_client.generic('PUT', path, body, content_type='image/png')

    with use_mcp_context(context), pytest.raises(
        ToolError,
        match='contenido no coincide',
    ):
        complete_upload({'asset_id': upload['asset_id']})

    assert received.status_code == 200


def test_temporary_output_artifact_has_a_signed_download(
    api_client, settings, tmp_path, tasks_connector,
):
    settings.MEDIA_ROOT = tmp_path
    connector, _ = tasks_connector
    credential = connector.credentials.get(label='Default')
    request = APIRequestFactory().get('/', HTTP_HOST='testserver')

    artifact = store_artifact(
        connector=connector,
        credential=credential,
        filename='reporte.csv',
        content_type='text/csv',
        content=b'a,b\n1,2\n',
        request=request,
    )
    response = api_client.get(urlsplit(artifact['download_url']).path)

    assert response.status_code == 200
    assert b''.join(response.streaming_content) == b'a,b\n1,2\n'


def test_operations_connector_calls_the_existing_panel_dashboard(api_client):
    connector = McpConnector.objects.get(slug='operations')
    connector.is_active = True
    connector.save(update_fields=['is_active'])
    token = connector.generate_token()

    response = _call(
        api_client, 'operations', token, 'get_operations_dashboard', {},
    )

    assert response.status_code == 200
    assert response.data['result']['isError'] is False


def test_tool_audit_records_credential_risk_and_request_id(api_client, tasks_connector):
    connector, token = tasks_connector
    task = Task.objects.create(title='Trazable', status='todo')

    response = _call(
        api_client, 'tasks', token, 'get_task', {'task_id': task.id},
    )

    event = McpRequestLog.objects.get(connector=connector, event='tool_call')
    assert event.credential.label == 'Default'
    assert event.risk_level == 'read'
    assert event.request_id == response['Mcp-Request-Id']
    assert event.object_refs == [{'field': 'task_id', 'value': task.id}]


def test_modern_discovery_advertises_the_stateless_contract(api_client, tasks_connector):
    _, token = tasks_connector

    response = api_client.post(
        f'/api/mcp/tasks/{token}/',
        _modern_rpc('server/discover'),
        format='json',
        HTTP_MCP_PROTOCOL_VERSION='2026-07-28',
        HTTP_MCP_METHOD='server/discover',
    )

    result = response.data['result']
    assert result['supportedVersions'] == ['2026-07-28']
    assert result['resultType'] == 'complete'
    assert result['cacheScope'] == 'private'
    assert result['_meta']['io.modelcontextprotocol/serverInfo']['name'] == (
        'projectapp-tasks-mcp'
    )


def test_modern_tools_list_includes_response_metadata(api_client, tasks_connector):
    _, token = tasks_connector

    response = api_client.post(
        f'/api/mcp/tasks/{token}/',
        _modern_rpc('tools/list'),
        format='json',
        HTTP_MCP_PROTOCOL_VERSION='2026-07-28',
        HTTP_MCP_METHOD='tools/list',
    )

    result = response.data['result']
    assert result['resultType'] == 'complete'
    assert result['ttlMs'] == 300_000
    assert response['Mcp-Protocol-Version'] == '2026-07-28'


def test_modern_transport_rejects_a_mismatched_tool_name(api_client, tasks_connector):
    _, token = tasks_connector

    response = api_client.post(
        f'/api/mcp/tasks/{token}/',
        _modern_rpc('tools/call', {
            'name': 'list_tasks',
            'arguments': {},
        }),
        format='json',
        HTTP_MCP_PROTOCOL_VERSION='2026-07-28',
        HTTP_MCP_METHOD='tools/call',
        HTTP_MCP_NAME='get_task',
    )

    assert response.status_code == 400
    assert response.data['error']['code'] == -32020


def test_modern_transport_requires_client_capabilities(api_client, tasks_connector):
    _, token = tasks_connector
    message = _modern_rpc('tools/list')
    del message['params']['_meta'][
        'io.modelcontextprotocol/clientCapabilities'
    ]

    response = api_client.post(
        f'/api/mcp/tasks/{token}/',
        message,
        format='json',
        HTTP_MCP_PROTOCOL_VERSION='2026-07-28',
        HTTP_MCP_METHOD='tools/list',
    )

    assert response.status_code == 400
    assert response.data['error']['code'] == -32602


def test_scoped_discovery_hides_ungranted_tools_and_keeps_controls(
    api_client, super_client, tasks_connector,
):
    created = super_client.post(
        '/api/mcp-connectors/tasks/credentials/',
        {'label': 'Lectura acotada', 'allowed_tools': ['list_tasks']},
        format='json',
    )

    response = api_client.post(
        '/api/mcp/tasks/',
        _rpc('tools/list'),
        format='json',
        HTTP_AUTHORIZATION=f"Bearer {created.data['credential']}",
    )

    names = {tool['name'] for tool in response.data['result']['tools']}
    assert {'list_tasks', 'describe_capabilities', 'confirm_action', 'cancel_action'} <= names
    assert 'get_task' not in names
