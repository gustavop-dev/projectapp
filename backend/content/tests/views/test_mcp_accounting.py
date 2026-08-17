"""Tests for the Accounting MCP connector HTTP endpoint."""
import json
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.mcp.accounting_tools import ACCOUNTING_TOOLS
from content.models import (
    AccountingSettings,
    AdsSpendRecord,
    IncomeRecord,
    McpConnector,
    NotificationRecipient,
)
from content.serializers.accounting import AccountingSettingsSerializer
from content.services import accounting_service


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
        # 8 ledgers × 5 CRUD + 5 non-CRUD + 15 statement tools = 60
        assert len(names) == 60
        for expected in (
            'list_income', 'create_expense', 'delete_pocket', 'get_hosting',
            'update_recurring', 'get_dashboard', 'list_change_logs',
            'get_settings', 'update_settings', 'mute_income',
            'get_statement_instructions',
            'create_statement', 'resolve_merchants', 'finalize_statement',
            'list_notification_recipient', 'create_notification_recipient',
            'update_notification_recipient', 'delete_notification_recipient',
        ):
            assert expected in names

    def test_registry_length_matches_endpoint(self):
        assert len(ACCOUNTING_TOOLS) == 60


@pytest.mark.django_db
class TestAccountingMcpCrud:
    def test_create_income_attributed_to_actor(self, api_client, accounting_connector, mcp_superuser):
        _, token = accounting_connector
        response = _call(api_client, token, 'create_income', {
            'concept': 'Kore v2 anticipo',
            'kind': 'liquid',
            'period_date': '2026-04',
            'total_amount': '1000000',
            # Required since Aug 2026 — creating from the chat classifies a new
            # record just like the panel form does.
            'origin': 'development',
        })
        assert response.data['result']['isError'] is False
        record = IncomeRecord.objects.get(concept='Kore v2 anticipo')
        assert record.created_by_id == mcp_superuser.id

    def test_create_income_without_a_business_line_errors(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        """Creating from the chat classifies, so it is held to the same rule.

        Only settling is exempt, and for a reason that does not apply here:
        its children copy the origin of a parent that may predate the field,
        while this creates a record with nothing to copy from.
        """
        _, token = accounting_connector
        response = _call(api_client, token, 'create_income', {
            'concept': 'Sin línea', 'kind': 'liquid',
            'period_date': '2026-04', 'total_amount': '1000',
        })
        result = response.data['result']
        assert result['isError'] is True
        assert 'origin' in result['content'][0]['text']
        assert not IncomeRecord.objects.filter(concept='Sin línea').exists()

    def test_create_income_without_superuser_errors(self, api_client, accounting_connector):
        _, token = accounting_connector
        response = _call(api_client, token, 'create_income', {
            'concept': 'Sin actor', 'kind': 'liquid',
            'period_date': '2026-04', 'total_amount': '1000',
            # Complete on purpose: the refusal under test is the missing
            # superuser, not a payload the serializer would reject anyway.
            'origin': 'development',
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
        assert 'notifications_enabled' in text


def _payload(response):
    return json.loads(response.data['result']['content'][0]['text'])


@pytest.mark.django_db
class TestAccountingMcpHandlerBranches:
    @pytest.fixture(autouse=True)
    def _mute_notifications(self):
        with patch.object(accounting_service, '_notify'):
            yield

    def test_get_income_returns_record(
        self, api_client, accounting_connector, make_income,
    ):
        record = make_income(concept='Visible')
        _, token = accounting_connector
        response = _call(api_client, token, 'get_income', {'record_id': record.id})
        assert _payload(response)['concept'] == 'Visible'

    def test_create_income_invalid_payload_errors(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        _, token = accounting_connector
        response = _call(api_client, token, 'create_income', {
            'concept': 'Malo', 'kind': 'liquid',
            'period_date': '2026-04', 'total_amount': 'no-numero',
            # The invalid field under test is the amount; the rest is valid so
            # the assertion cannot pass on a different rejection.
            'origin': 'development',
        })
        result = response.data['result']
        assert result['isError'] is True
        assert 'Datos inválidos' in result['content'][0]['text']

    def test_update_income_without_fields_errors(
        self, api_client, accounting_connector, make_income, mcp_superuser,
    ):
        record = make_income(concept='Quieto')
        _, token = accounting_connector
        response = _call(api_client, token, 'update_income', {'record_id': record.id})
        assert response.data['result']['isError'] is True

    def test_update_income_invalid_payload_errors(
        self, api_client, accounting_connector, make_income, mcp_superuser,
    ):
        record = make_income(concept='Quieto')
        _, token = accounting_connector
        response = _call(api_client, token, 'update_income', {
            'record_id': record.id, 'total_amount': 'no-numero',
        })
        assert response.data['result']['isError'] is True

    def test_delete_income_removes_record(
        self, api_client, accounting_connector, make_income, mcp_superuser,
    ):
        record = make_income(concept='Borrable')
        _, token = accounting_connector
        response = _call(api_client, token, 'delete_income', {'record_id': record.id})
        assert _payload(response)['deleted'] is True
        assert not IncomeRecord.objects.filter(pk=record.pk).exists()

    def test_list_income_coerces_bool_and_skips_none_params(
        self, api_client, accounting_connector, make_income,
    ):
        make_income(concept='Filtrable', period_date=date(2026, 3, 1))
        _, token = accounting_connector
        response = _call(api_client, token, 'list_income', {
            'year': 2026, 'q': None, 'solo_demo': True,
        })
        assert _payload(response)['count'] == 1

    def test_list_income_invalid_year_errors(self, api_client, accounting_connector):
        _, token = accounting_connector
        response = _call(api_client, token, 'list_income', {'year': 'no-año'})
        assert response.data['result']['isError'] is True

    def test_list_ads_includes_accumulated(self, api_client, accounting_connector):
        AdsSpendRecord.objects.create(
            spend_date=date(2026, 3, 5), origin_card='T.C 0655',
            amount='150000',
        )
        _, token = accounting_connector
        response = _call(api_client, token, 'list_ads', {})
        results = _payload(response)['results']
        assert len(results) == 1
        assert 'accumulated' in results[0]

    def test_dashboard_invalid_year_errors(self, api_client, accounting_connector):
        _, token = accounting_connector
        response = _call(api_client, token, 'get_dashboard', {'year': 'no-año'})
        assert response.data['result']['isError'] is True

    def test_change_logs_list_and_filter_by_entity(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        _call(api_client, token := accounting_connector[1], 'create_income', {
            'concept': 'Log gen', 'kind': 'liquid',
            'period_date': '2026-04', 'total_amount': '5000',
            'origin': 'development',
        })
        response = _call(api_client, token, 'list_change_logs', {
            'entity_type': 'income', 'action': 'created', 'page': 1,
        })
        payload = _payload(response)
        assert payload['count'] >= 1
        assert payload['page'] == 1

    def test_change_logs_invalid_date_errors(self, api_client, accounting_connector):
        _, token = accounting_connector
        response = _call(api_client, token, 'list_change_logs', {
            'date_from': 'no-fecha',
        })
        assert response.data['result']['isError'] is True

    def test_change_logs_invalid_page_falls_back_to_one(
        self, api_client, accounting_connector,
    ):
        _, token = accounting_connector
        response = _call(api_client, token, 'list_change_logs', {'page': 'xx'})
        assert _payload(response)['page'] == 1

    def test_create_notification_recipient(
        self, api_client, accounting_connector, mcp_superuser, accounting_settings,
    ):
        _, token = accounting_connector
        response = _call(api_client, token, 'create_notification_recipient', {
            'email': 'socios@x.com',
        })
        assert response.data['result']['isError'] is False
        assert NotificationRecipient.objects.filter(
            email='socios@x.com', is_active=True,
        ).exists()

    def test_create_notification_recipient_rejects_duplicate(
        self, api_client, accounting_connector, mcp_superuser, accounting_settings,
    ):
        _, token = accounting_connector
        _call(api_client, token, 'create_notification_recipient', {
            'email': 'socios@x.com',
        })
        response = _call(api_client, token, 'create_notification_recipient', {
            'email': 'SOCIOS@x.com',
        })
        assert response.data['result']['isError'] is True
        assert NotificationRecipient.objects.filter(email='socios@x.com').count() == 1

    def test_update_settings_invalid_payload_errors(
        self, api_client, accounting_connector, mcp_superuser, accounting_settings,
    ):
        _, token = accounting_connector
        response = _call(api_client, token, 'update_settings', {
            'overdue_reminder_frequency': 'cada-rato',
        })
        assert response.data['result']['isError'] is True

    def test_update_settings_changes_income_view_mode(
        self, api_client, accounting_connector, mcp_superuser, accounting_settings,
    ):
        _, token = accounting_connector
        response = _call(api_client, token, 'update_settings', {
            'income_default_view_mode': 'classic',
        })
        assert response.data['result']['isError'] is False
        assert AccountingSettings.load().income_default_view_mode == 'classic'

    def test_update_settings_schema_declares_every_editable_field(self):
        """The declared schema drifted behind the serializer once (it listed
        3 of 6 editable fields); pin them to each other so it cannot again."""
        tool = next(t for t in ACCOUNTING_TOOLS if t['name'] == 'update_settings')
        properties = tool['input_schema']['properties']
        editable = set(AccountingSettingsSerializer.Meta.fields) - {'updated_at'}
        assert set(properties) == editable
        assert properties['income_default_view_mode']['enum'] == ['classic', 'grouped']


@pytest.mark.django_db
class TestAccountingMcpPocketGuardrails:
    """Auto-managed pocket movements (income/expense-backed) must stay locked
    on the MCP surface exactly like the panel — accounting_tools.py:17-18
    documents this guardrail but nothing exercised it until now.
    """

    def _create_liquid_pocket_income(self, api_client, token):
        response = _call(api_client, token, 'create_income', {
            'concept': 'Pago bolsillo directo',
            'kind': 'liquid',
            'destination': 'pocket',
            'period_date': '2026-04',
            'total_amount': '250000',
            'origin': 'development',
        })
        assert response.data['result']['isError'] is False
        record = IncomeRecord.objects.get(concept='Pago bolsillo directo')
        assert record.pocket_movement_id is not None
        return record

    def test_update_pocket_rejects_direction_flip_on_linked_movement(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        """Catches a refactor that drops _ensure_pocket_update_allowed's
        direction lock (accounting_service.py:288-299), letting an AI agent
        silently flip a linked movement in/out and desync it from its income.
        """
        _, token = accounting_connector
        record = self._create_liquid_pocket_income(api_client, token)
        movement = record.pocket_movement
        assert movement.direction == 'in'

        response = _call(api_client, token, 'update_pocket', {
            'record_id': movement.id, 'direction': 'out',
        })

        result = response.data['result']
        assert result['isError'] is True
        assert 'no se puede cambiar' in result['content'][0]['text']
        movement.refresh_from_db()
        assert movement.direction == 'in'

    def test_delete_pocket_cascades_to_linked_income_record(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        """Catches an AI agent silently deleting a real income record via
        delete_pocket without the cascade actually running (or without
        actually running at all) — accounting_service.py:392-426.
        """
        _, token = accounting_connector
        record = self._create_liquid_pocket_income(api_client, token)
        movement_id = record.pocket_movement_id

        response = _call(api_client, token, 'delete_pocket', {'record_id': movement_id})

        assert response.data['result']['isError'] is False
        assert not IncomeRecord.objects.filter(pk=record.id).exists()
        from content.models import PocketMovement

        assert not PocketMovement.objects.filter(pk=movement_id).exists()


@pytest.mark.django_db
class TestAccountingMcpPaymentStatusFilter:
    """list_income exposes the collection-state filter the panel already has."""

    def _seed(self, make_income):
        from decimal import Decimal

        pending = make_income(concept='Esperado sin pagos')
        paid = make_income(concept='Esperado pagado')
        make_income(
            concept='Pago total', kind=IncomeRecord.Kind.LIQUID,
            expected_income=paid,
        )
        partial = make_income(concept='Esperado parcial')
        make_income(
            concept='Abono inicial', kind=IncomeRecord.Kind.LIQUID,
            expected_income=partial,
            total_amount=Decimal('400000.00'),
            gustavo_amount=Decimal('200000.00'),
            carlos_amount=Decimal('200000.00'),
        )
        return pending, paid, partial

    def test_list_income_pending_returns_only_uncollected_expected(
        self, api_client, accounting_connector, make_income,
    ):
        self._seed(make_income)
        _, token = accounting_connector
        response = _call(api_client, token, 'list_income', {'payment_status': 'pending'})
        text = response.data['result']['content'][0]['text']
        assert 'Esperado sin pagos' in text
        assert 'Esperado pagado' not in text
        assert 'Esperado parcial' not in text

    def test_list_income_paid_returns_only_settled_expected(
        self, api_client, accounting_connector, make_income,
    ):
        self._seed(make_income)
        _, token = accounting_connector
        response = _call(api_client, token, 'list_income', {'payment_status': 'paid'})
        payload = json.loads(response.data['result']['content'][0]['text'])
        assert [row['concept'] for row in payload['results']] == ['Esperado pagado']

    def test_list_income_partial_rows_carry_annotated_amounts(
        self, api_client, accounting_connector, make_income,
    ):
        self._seed(make_income)
        _, token = accounting_connector
        response = _call(api_client, token, 'list_income', {'payment_status': 'partial'})
        payload = json.loads(response.data['result']['content'][0]['text'])
        assert [row['concept'] for row in payload['results']] == ['Esperado parcial']
        row = payload['results'][0]
        assert row['payment_status'] == 'partial'
        assert row['paid_amount'] == '400000.00'
        assert row['pending_amount'] == '600000.00'

    def test_list_income_rejects_unknown_payment_status(
        self, api_client, accounting_connector,
    ):
        _, token = accounting_connector
        response = _call(api_client, token, 'list_income', {'payment_status': 'settled'})
        assert response.data['result']['isError'] is True

    def test_income_schema_gates_payment_status_to_income_only(self):
        income_tool = next(t for t in ACCOUNTING_TOOLS if t['name'] == 'list_income')
        expense_tool = next(t for t in ACCOUNTING_TOOLS if t['name'] == 'list_expense')
        prop = income_tool['input_schema']['properties']['payment_status']
        assert prop['enum'] == ['pending', 'partial', 'paid']
        assert 'payment_status' not in expense_tool['input_schema']['properties']


@pytest.mark.django_db
class TestAccountingMcpPocketFilters:
    """list_pocket exposes the attribution + linkage cuts the panel has.

    They ride the shared filter layer, so the tool inherits them; the schema
    branch is what makes them discoverable.
    """

    def _seed(self, make_expense):
        from datetime import date
        from decimal import Decimal

        from content.models import PocketMovement

        draw = PocketMovement.objects.create(
            concept='Retiro Gustavo', movement_date=date(2026, 6, 1),
            direction=PocketMovement.Direction.OUT,
            amount=Decimal('300000.00'),
        )
        make_expense(
            pocket_movement=draw, category='personal',
            gustavo_amount=Decimal('800000.00'),
            carlos_amount=Decimal('0.00'),
        )
        PocketMovement.objects.create(
            concept='Movimiento viejo', movement_date=date(2026, 6, 2),
            direction=PocketMovement.Direction.OUT,
            amount=Decimal('80000.00'),
        )

    def test_list_pocket_filters_by_attribution(
        self, api_client, accounting_connector, make_expense,
    ):
        self._seed(make_expense)
        _, token = accounting_connector
        response = _call(api_client, token, 'list_pocket', {'attribution': 'gustavo'})
        payload = json.loads(response.data['result']['content'][0]['text'])
        assert [row['concept'] for row in payload['results']] == ['Retiro Gustavo']

    def test_list_pocket_filters_the_unlinked_movements(
        self, api_client, accounting_connector, make_expense,
    ):
        self._seed(make_expense)
        _, token = accounting_connector
        response = _call(api_client, token, 'list_pocket', {'linked': 'false'})
        payload = json.loads(response.data['result']['content'][0]['text'])
        assert [row['concept'] for row in payload['results']] == ['Movimiento viejo']

    def test_list_pocket_rejects_an_unknown_attribution(
        self, api_client, accounting_connector,
    ):
        _, token = accounting_connector
        response = _call(api_client, token, 'list_pocket', {'attribution': 'socio'})
        assert response.data['result']['isError'] is True

    def test_schema_gates_the_pocket_filters_to_pocket_only(self):
        pocket_tool = next(t for t in ACCOUNTING_TOOLS if t['name'] == 'list_pocket')
        income_tool = next(t for t in ACCOUNTING_TOOLS if t['name'] == 'list_income')
        props = pocket_tool['input_schema']['properties']
        assert 'gustavo' in props['attribution']['description']
        assert 'linked' in props
        assert 'attribution' not in income_tool['input_schema']['properties']


@pytest.mark.django_db
class TestAccountingMcpDeductions:
    """The expense tools see deductions but can never create them."""

    def test_list_expense_filters_by_deduction_type(
        self, api_client, accounting_connector, make_expense,
    ):
        make_expense(concept='Hosting mensual')
        make_expense(
            concept='Comisión Wompi', deduction_type='gateway_fee',
            total_amount=Decimal('4854.00'),
            gustavo_amount=Decimal('2427.00'),
            carlos_amount=Decimal('2427.00'),
        )
        _, token = accounting_connector

        response = _call(api_client, token, 'list_expense', {
            'deduction_type': 'gateway_fee',
        })

        payload = json.loads(response.data['result']['content'][0]['text'])
        assert [row['concept'] for row in payload['results']] == ['Comisión Wompi']

    def test_expense_list_schema_publishes_the_deduction_filter(self):
        tool = next(t for t in ACCOUNTING_TOOLS if t['name'] == 'list_expense')
        assert 'deduction_type' in tool['input_schema']['properties']

    def test_create_expense_with_deduction_type_errors(
        self, api_client, accounting_connector, mcp_superuser,
    ):
        _, token = accounting_connector

        response = _call(api_client, token, 'create_expense', {
            'concept': 'Comisión manual',
            'period_date': '2026-07',
            'total_amount': '4854.00',
            'deduction_type': 'gateway_fee',
        })

        assert response.data['result']['isError'] is True
        text = response.data['result']['content'][0]['text']
        assert 'liquidación' in text
