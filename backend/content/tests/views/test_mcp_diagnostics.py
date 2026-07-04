"""Tests for the Diagnostics MCP connector HTTP endpoint."""
import pytest

from accounts.services import proposal_client_service
from content.models import McpConnector, WebAppDiagnostic


@pytest.fixture
def diagnostics_connector(db):
    connector, _ = McpConnector.objects.get_or_create(
        slug='diagnostics', defaults={'name': 'Gestor de Diagnósticos'},
    )
    connector.is_active = True
    connector.save(update_fields=['is_active'])
    return connector, connector.generate_token()


@pytest.fixture
def a_client(db):
    return proposal_client_service.get_or_create_client_for_proposal(
        name='Cliente Diag', email='diagcli@x.com', phone='', company='',
    )


def _url(token):
    return f'/api/mcp/diagnostics/{token}/'


def _rpc(method, params=None, msg_id=1):
    message = {'jsonrpc': '2.0', 'id': msg_id, 'method': method}
    if params is not None:
        message['params'] = params
    return message


def _call(api_client, token, name, arguments):
    return api_client.post(
        _url(token), _rpc('tools/call', {'name': name, 'arguments': arguments}),
        format='json',
    )


@pytest.mark.django_db
class TestDiagnosticsMcp:
    def test_tool_list(self, api_client, diagnostics_connector):
        _, token = diagnostics_connector
        response = api_client.post(_url(token), _rpc('tools/list'), format='json')
        names = [t['name'] for t in response.data['result']['tools']]
        for expected in (
            'list_diagnostics', 'create_diagnostic', 'update_diagnostic_status',
            'send_initial', 'list_diagnostic_templates', 'delete_diagnostic',
        ):
            assert expected in names

    def test_create_requires_client(self, api_client, diagnostics_connector):
        _, token = diagnostics_connector
        response = _call(api_client, token, 'create_diagnostic', {})
        assert response.data['result']['isError'] is True

    def test_create_and_get(self, api_client, diagnostics_connector, a_client):
        _, token = diagnostics_connector
        created = _call(api_client, token, 'create_diagnostic', {
            'client_id': a_client.pk, 'title': 'Diag inicial',
        })
        assert created.data['result']['isError'] is False
        diagnostic = WebAppDiagnostic.objects.get(client=a_client)
        got = _call(api_client, token, 'get_diagnostic', {'diagnostic_id': diagnostic.id})
        assert got.data['result']['isError'] is False

    def test_status_transition_rejects_invalid(self, api_client, diagnostics_connector, a_client):
        diagnostic = WebAppDiagnostic.objects.create(client=a_client, status='draft')
        _, token = diagnostics_connector
        # draft → accepted is not an allowed transition.
        response = _call(api_client, token, 'update_diagnostic_status', {
            'diagnostic_id': diagnostic.id, 'status': 'accepted',
        })
        assert response.data['result']['isError'] is True

    def test_delete_is_unrestricted(self, api_client, diagnostics_connector, a_client):
        diagnostic = WebAppDiagnostic.objects.create(client=a_client, status='sent')
        _, token = diagnostics_connector
        response = _call(api_client, token, 'delete_diagnostic', {'diagnostic_id': diagnostic.id})
        assert response.data['result']['isError'] is False
        assert not WebAppDiagnostic.objects.filter(pk=diagnostic.id).exists()

    def test_list_templates(self, api_client, diagnostics_connector):
        _, token = diagnostics_connector
        response = _call(api_client, token, 'list_diagnostic_templates', {})
        assert response.data['result']['isError'] is False
