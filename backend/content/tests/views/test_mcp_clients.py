"""Tests for the Clients MCP connector HTTP endpoint."""
import pytest

from accounts.services import proposal_client_service
from content.models import McpConnector


@pytest.fixture
def clients_connector(db):
    connector, _ = McpConnector.objects.get_or_create(
        slug='clients', defaults={'name': 'Gestor de Clientes'},
    )
    connector.is_active = True
    connector.save(update_fields=['is_active'])
    token = connector.generate_token()
    return connector, token


def _url(token):
    return f'/api/mcp/clients/{token}/'


def _rpc(method, params=None, msg_id=1):
    message = {'jsonrpc': '2.0', 'id': msg_id, 'method': method}
    if params is not None:
        message['params'] = params
    return message


def _call(api_client, token, name, arguments):
    return api_client.post(
        _url(token),
        _rpc('tools/call', {'name': name, 'arguments': arguments}),
        format='json',
    )


def _make_client(name='ACME SAS', email='', phone='', company=''):
    return proposal_client_service.get_or_create_client_for_proposal(
        name=name, email=email, phone=phone, company=company,
    )


@pytest.mark.django_db
class TestClientsMcpToolList:
    def test_exposes_the_six_tools(self, api_client, clients_connector):
        _, token = clients_connector
        response = api_client.post(_url(token), _rpc('tools/list'), format='json')
        names = [t['name'] for t in response.data['result']['tools']]
        assert names == [
            'search_clients', 'list_clients', 'get_client',
            'create_client', 'update_client', 'delete_client',
        ]


@pytest.mark.django_db
class TestClientsMcpReads:
    def test_search_matches_by_company(self, api_client, clients_connector):
        _make_client(name='Juan', company='Panadería Bogotá')
        _, token = clients_connector
        response = _call(api_client, token, 'search_clients', {'q': 'Panadería'})
        text = response.data['result']['content'][0]['text']
        assert 'Panadería Bogotá' in text

    def test_list_clients_returns_count(self, api_client, clients_connector):
        _make_client(name='Uno', email='uno@x.com')
        _make_client(name='Dos', email='dos@x.com')
        _, token = clients_connector
        response = _call(api_client, token, 'list_clients', {})
        assert response.data['result']['isError'] is False
        assert '"count"' in response.data['result']['content'][0]['text']

    def test_get_client_nests_related(self, api_client, clients_connector):
        profile = _make_client(name='Detalle', email='detalle@x.com')
        _, token = clients_connector
        response = _call(api_client, token, 'get_client', {'client_id': profile.pk})
        text = response.data['result']['content'][0]['text']
        assert '"proposals"' in text and '"diagnostics"' in text

    def test_get_missing_client_errors(self, api_client, clients_connector):
        _, token = clients_connector
        response = _call(api_client, token, 'get_client', {'client_id': 999999})
        assert response.data['result']['isError'] is True


@pytest.mark.django_db
class TestClientsMcpWrites:
    def test_create_requires_some_identifier(self, api_client, clients_connector):
        _, token = clients_connector
        response = _call(api_client, token, 'create_client', {})
        assert response.data['result']['isError'] is True

    def test_create_client(self, api_client, clients_connector):
        _, token = clients_connector
        response = _call(api_client, token, 'create_client', {
            'name': 'Nuevo Cliente', 'email': 'nuevo@x.com',
        })
        assert response.data['result']['isError'] is False
        text = response.data['result']['content'][0]['text']
        assert 'Nuevo Cliente' in text

    def test_update_client(self, api_client, clients_connector):
        profile = _make_client(name='Viejo', email='viejo@x.com')
        _, token = clients_connector
        response = _call(api_client, token, 'update_client', {
            'client_id': profile.pk, 'company': 'Empresa X',
        })
        assert response.data['result']['isError'] is False
        assert 'Empresa X' in response.data['result']['content'][0]['text']

    def test_update_requires_a_field(self, api_client, clients_connector):
        profile = _make_client(name='Solo', email='solo@x.com')
        _, token = clients_connector
        response = _call(api_client, token, 'update_client', {'client_id': profile.pk})
        assert response.data['result']['isError'] is True

    def test_delete_orphan_client(self, api_client, clients_connector):
        profile = _make_client(name='Huérfano', email='orphan@x.com')
        _, token = clients_connector
        response = _call(api_client, token, 'delete_client', {'client_id': profile.pk})
        assert response.data['result']['isError'] is False


@pytest.fixture
def superuser_client(api_client, django_user_model):
    user = django_user_model.objects.create_user(
        username='root_clients_test', password='x', is_staff=True, is_superuser=True,
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestClientsConnectorPanel:
    def test_panel_lists_clients_connector_with_tools(self, superuser_client, clients_connector):
        response = superuser_client.get('/api/mcp-connectors/')
        entry = next(c for c in response.data if c['slug'] == 'clients')
        tool_names = [t['name'] for t in entry['tools']]
        assert 'search_clients' in tool_names
        assert 'create_client' in tool_names
