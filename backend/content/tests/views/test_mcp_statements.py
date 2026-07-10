"""Tests for the credit-card statement MCP tools (slug accounting)."""
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import (
    CreditCardStatement,
    CreditCardTransaction,
    McpConnector,
    MerchantAlias,
)
from content.services import accounting_service

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


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
    return django_user_model.objects.create_user(
        username='mcp_stmt_actor', password='x',
        is_staff=True, is_superuser=True,
    )


def _url(token):
    return f'/api/mcp/accounting/{token}/'


def _payload(response):
    import json

    return json.loads(response.data['result']['content'][0]['text'])


def _call(api_client, token, name, arguments, msg_id=1):
    return api_client.post(
        _url(token),
        {
            'jsonrpc': '2.0', 'id': msg_id, 'method': 'tools/call',
            'params': {'name': name, 'arguments': arguments},
        },
        format='json',
    )


CREATE_ARGS = {
    'card_name': 'Visa Bancolombia',
    'period_date': '2026-06',
    'purchases_total': 100000,
    'transactions': [
        {
            'transaction_date': '2026-06-05',
            'raw_description': 'PAYU*NETFLIX 990011',
            'amount': 60000,
        },
        {
            'transaction_date': '2026-06-09',
            'raw_description': 'PRIMAX 8811',
            'amount': 40000,
        },
    ],
}


class TestInstructionsTool:
    def test_returns_phases_and_categories_vocab(
        self, api_client, accounting_connector,
    ):
        _, token = accounting_connector
        response = _call(api_client, token, 'get_statement_instructions', {})
        result = response.data['result']
        assert result['isError'] is False
        payload = _payload(response)
        assert 'FASE 1' in payload['instructions']
        assert 'NUNCA guardes alias sin aprobación' in payload['instructions']
        assert {'value': 'fuel', 'label': 'Gasolina'} in payload['categories']
        assert payload['workflow_version'] >= 1


class TestCreateStatementTool:
    def test_creates_draft_with_transactions(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        _, token = accounting_connector
        response = _call(api_client, token, 'create_statement', CREATE_ARGS)
        result = response.data['result']
        assert result['isError'] is False, result
        statement = CreditCardStatement.objects.get()
        assert statement.status == 'draft'
        assert statement.transactions.count() == 2
        assert statement.created_by_id == mcp_superuser.id

    def test_duplicate_returns_tool_error_with_existing_id(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        _, token = accounting_connector
        _call(api_client, token, 'create_statement', CREATE_ARGS)
        response = _call(api_client, token, 'create_statement', CREATE_ARGS)
        result = response.data['result']
        assert result['isError'] is True
        message = result['content'][0]['text']
        assert 'Ya existe un extracto' in message
        assert f'id={CreditCardStatement.objects.get().pk}' in message


class TestResolveAndLearnFlow:
    def test_resolve_save_finalize_roundtrip(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        _, token = accounting_connector
        _call(api_client, token, 'create_statement', CREATE_ARGS)
        statement = CreditCardStatement.objects.get()

        resolve = _call(api_client, token, 'resolve_merchants', {
            'raw_descriptions': ['PAYU*NETFLIX 990011', 'PRIMAX 8811'],
        })
        payload = _payload(resolve)
        assert payload['resolved'] == []
        assert len(payload['unresolved']) == 2

        save = _call(api_client, token, 'save_merchant_aliases', {
            'aliases': [
                {
                    'raw_description': 'PAYU*NETFLIX 990011',
                    'merchant_name': 'Netflix',
                    'category': 'software',
                },
                {
                    'raw_description': 'PRIMAX 8811',
                    'merchant_name': 'Primax',
                    'category': 'fuel',
                },
            ],
            'statement_id': statement.pk,
        })
        save_payload = _payload(save)
        assert save_payload['updated_transactions'] == 2
        assert MerchantAlias.objects.count() == 2

        finalize = _call(api_client, token, 'finalize_statement', {
            'statement_id': statement.pk,
        })
        finalize_payload = _payload(finalize)
        assert finalize_payload['statement']['status'] == 'processed'
        categories = {
            row['category'] for row in finalize_payload['category_totals']
        }
        assert categories == {'software', 'fuel'}

    def test_save_alias_rejects_invalid_category(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        _, token = accounting_connector
        response = _call(api_client, token, 'save_merchant_aliases', {
            'aliases': [{
                'raw_description': 'X', 'merchant_name': 'X',
                'category': 'no-existe',
            }],
        })
        assert response.data['result']['isError'] is True


class TestLifecycleGuards:
    def test_finalize_mismatch_reports_difference(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        _, token = accounting_connector
        args = {**CREATE_ARGS, 'purchases_total': 999999}
        _call(api_client, token, 'create_statement', args)
        statement = CreditCardStatement.objects.get()
        response = _call(api_client, token, 'finalize_statement', {
            'statement_id': statement.pk,
        })
        result = response.data['result']
        assert result['isError'] is True
        assert 'diferencia' in result['content'][0]['text']

    def test_delete_is_draft_only(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        _, token = accounting_connector
        _call(api_client, token, 'create_statement', CREATE_ARGS)
        statement = CreditCardStatement.objects.get()
        _call(api_client, token, 'finalize_statement', {
            'statement_id': statement.pk, 'force': True,
        })
        response = _call(api_client, token, 'delete_statement', {
            'statement_id': statement.pk,
        })
        result = response.data['result']
        assert result['isError'] is True
        assert CreditCardStatement.objects.count() == 1

    def test_status_tool_reports_processed_month(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        _, token = accounting_connector
        _call(api_client, token, 'create_statement', CREATE_ARGS)
        statement = CreditCardStatement.objects.get()
        _call(api_client, token, 'finalize_statement', {
            'statement_id': statement.pk, 'force': True,
        })
        response = _call(api_client, token, 'get_statement_status', {
            'year': 2026,
        })
        payload = _payload(response)
        assert payload['months'][5]['has_processed'] is True
        assert payload['cards'] == ['Visa Bancolombia']
