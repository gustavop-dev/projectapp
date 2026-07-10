"""Tests for the Accounting MCP connector HTTP endpoint."""
import pytest

from content.mcp.accounting_tools import ACCOUNTING_TOOLS
from content.models import IncomeRecord, McpConnector


@pytest.fixture
def accounting_connector(db):
    connector, _ = McpConnector.objects.get_or_create(
        slug='accounting', defaults={'name': 'Contabilidad'},
    )
    connector.is_active = True
    connector.save(update_fields=['is_active'])
    return connector, connector.generate_token()


@pytest.fixture
def mcp_superuser(db, django_user_model):
    """A superuser so mcp_actor() can attribute accounting writes."""
    return django_user_model.objects.create_user(
        username='mcp_acc_actor', password='x', is_staff=True, is_superuser=True,
    )


def _url(token):
    return f'/api/mcp/accounting/{token}/'


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
class TestAccountingMcpToolList:
    def test_exposes_per_ledger_and_non_crud_tools(self, api_client, accounting_connector):
        _, token = accounting_connector
        response = api_client.post(_url(token), _rpc('tools/list'), format='json')
        names = [t['name'] for t in response.data['result']['tools']]
        # 7 ledgers × 5 CRUD + 4 non-CRUD + 15 statement tools = 54
        assert len(names) == 54
        for expected in (
            'list_income', 'create_expense', 'delete_pocket', 'get_hosting',
            'update_recurring', 'get_dashboard', 'list_change_logs',
            'get_settings', 'update_settings', 'get_statement_instructions',
            'create_statement', 'resolve_merchants', 'finalize_statement',
        ):
            assert expected in names

    def test_registry_length_matches_endpoint(self):
        assert len(ACCOUNTING_TOOLS) == 54


@pytest.mark.django_db
class TestAccountingMcpCrud:
    def test_create_income_attributed_to_actor(self, api_client, accounting_connector, mcp_superuser):
        _, token = accounting_connector
        response = _call(api_client, token, 'create_income', {
            'concept': 'Kore v2 anticipo',
            'kind': 'liquid',
            'period_date': '2026-04',
            'total_amount': '1000000',
        })
        assert response.data['result']['isError'] is False
        record = IncomeRecord.objects.get(concept='Kore v2 anticipo')
        assert record.created_by_id == mcp_superuser.id

    def test_create_income_without_superuser_errors(self, api_client, accounting_connector):
        _, token = accounting_connector
        response = _call(api_client, token, 'create_income', {
            'concept': 'Sin actor', 'kind': 'liquid',
            'period_date': '2026-04', 'total_amount': '1000',
        })
        assert response.data['result']['isError'] is True

    def test_list_income_filters_by_q(self, api_client, accounting_connector, make_income):
        make_income(concept='Alfa ingreso')
        make_income(concept='Beta ingreso')
        _, token = accounting_connector
        response = _call(api_client, token, 'list_income', {'q': 'Alfa'})
        text = response.data['result']['content'][0]['text']
        assert 'Alfa ingreso' in text
        assert 'Beta ingreso' not in text

    def test_update_income(self, api_client, accounting_connector, make_income, mcp_superuser):
        record = make_income(concept='Original')
        _, token = accounting_connector
        response = _call(api_client, token, 'update_income', {
            'record_id': record.id, 'concept': 'Editado',
        })
        assert response.data['result']['isError'] is False
        record.refresh_from_db()
        assert record.concept == 'Editado'

    def test_get_missing_record_errors(self, api_client, accounting_connector):
        _, token = accounting_connector
        response = _call(api_client, token, 'get_income', {'record_id': 999999})
        assert response.data['result']['isError'] is True


@pytest.mark.django_db
class TestAccountingMcpNonCrud:
    def test_dashboard(self, api_client, accounting_connector, make_income):
        make_income(concept='X', period_date=__import__('datetime').date(2026, 3, 1))
        _, token = accounting_connector
        response = _call(api_client, token, 'get_dashboard', {'year': 2026})
        assert response.data['result']['isError'] is False

    def test_get_settings(self, api_client, accounting_connector, accounting_settings):
        _, token = accounting_connector
        response = _call(api_client, token, 'get_settings', {})
        text = response.data['result']['content'][0]['text']
        assert 'notification_recipients' in text
