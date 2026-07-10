"""API tests for the credit-card statement endpoints (superuser-only)."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import (
    CreditCardStatement,
    CreditCardTransaction,
    MerchantAlias,
)
from content.services import accounting_service

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


CREATE_PAYLOAD = {
    'card_name': 'Visa Bancolombia',
    'period': None,  # replaced below
    'period_date': '2026-06',
    'purchases_total': '100000.00',
    'transactions': [
        {
            'transaction_date': '2026-06-05',
            'raw_description': 'PAYU*NETFLIX 990011',
            'amount': '60000.00',
        },
        {
            'transaction_date': '2026-06-09',
            'raw_description': 'PRIMAX 8811',
            'amount': '40000.00',
        },
    ],
}
CREATE_PAYLOAD.pop('period')


def _create_statement(client):
    response = client.post(
        '/api/accounting/statements/create/', CREATE_PAYLOAD, format='json',
    )
    assert response.status_code == 201, response.data
    return response.data


class TestStatementAuth:
    def test_requires_authentication(self, api_client):
        assert api_client.get(
            '/api/accounting/statements/',
        ).status_code in (401, 403)

    def test_staff_without_superuser_is_rejected(self, admin_client):
        assert admin_client.get(
            '/api/accounting/statements/',
        ).status_code == 403


class TestStatementCreate:
    def test_creates_draft_with_nested_transactions(self, super_client):
        data = _create_statement(super_client)
        assert data['status'] == 'draft'
        assert len(data['transactions']) == 2
        assert data['transactions_sum'] == '100000.00'

    def test_duplicate_card_period_returns_400(self, super_client):
        _create_statement(super_client)
        response = super_client.post(
            '/api/accounting/statements/create/', CREATE_PAYLOAD,
            format='json',
        )
        assert response.status_code == 400
        assert 'Ya existe un extracto' in str(response.data)

    def test_invalid_transaction_rolls_back_everything(self, super_client):
        payload = {
            **CREATE_PAYLOAD,
            'transactions': [
                CREATE_PAYLOAD['transactions'][0],
                {'transaction_date': '2026-06-09'},  # missing fields
            ],
        }
        response = super_client.post(
            '/api/accounting/statements/create/', payload, format='json',
        )
        assert response.status_code == 400
        assert CreditCardStatement.objects.count() == 0
        assert CreditCardTransaction.objects.count() == 0


class TestStatementStatusGrid:
    def test_status_endpoint_resolves_before_detail_route(self, super_client):
        _create_statement(super_client)
        response = super_client.get(
            '/api/accounting/statements/status/?year=2026',
        )
        assert response.status_code == 200
        assert len(response.data['months']) == 12
        assert response.data['months'][5]['has_draft'] is True

    def test_rejects_invalid_year(self, super_client):
        response = super_client.get(
            '/api/accounting/statements/status/?year=abc',
        )
        assert response.status_code == 400


class TestStatementLifecycleEndpoints:
    def test_finalize_mismatch_returns_400_with_difference(self, super_client):
        data = _create_statement(super_client)
        CreditCardStatement.objects.filter(pk=data['id']).update(
            purchases_total=Decimal('999999.00'),
        )
        response = super_client.post(
            f"/api/accounting/statements/{data['id']}/finalize/", {},
            format='json',
        )
        assert response.status_code == 400
        assert 'diferencia' in str(response.data)

    def test_finalize_and_reopen_roundtrip(self, super_client):
        data = _create_statement(super_client)
        response = super_client.post(
            f"/api/accounting/statements/{data['id']}/finalize/", {},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['status'] == 'processed'
        response = super_client.post(
            f"/api/accounting/statements/{data['id']}/reopen/", {},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['status'] == 'draft'

    def test_delete_cascades_transactions(self, super_client):
        data = _create_statement(super_client)
        response = super_client.delete(
            f"/api/accounting/statements/{data['id']}/delete/",
        )
        assert response.status_code == 204
        assert CreditCardTransaction.objects.count() == 0


class TestTransactionEndpoints:
    def test_bulk_create_appends_to_draft(self, super_client):
        data = _create_statement(super_client)
        response = super_client.post(
            f"/api/accounting/statements/{data['id']}/transactions/batch/",
            {'transactions': [{
                'transaction_date': '2026-06-15',
                'raw_description': 'UBER TRIP',
                'amount': '25000.00',
            }]},
            format='json',
        )
        assert response.status_code == 201
        assert CreditCardTransaction.objects.count() == 3

    def test_update_transaction_of_processed_statement_is_blocked(
        self, super_client,
    ):
        data = _create_statement(super_client)
        super_client.post(
            f"/api/accounting/statements/{data['id']}/finalize/", {},
            format='json',
        )
        tx_id = data['transactions'][0]['id']
        response = super_client.patch(
            f"/api/accounting/statements/{data['id']}/transactions/{tx_id}/update/",
            {'merchant_name': 'Netflix'},
            format='json',
        )
        assert response.status_code == 400


class TestMerchantAliasEndpoints:
    def test_resolve_endpoint_matches_normalized(self, super_client):
        MerchantAlias.objects.create(
            match_text='PAYU*NETFLIX', merchant_name='Netflix',
            default_category='software',
        )
        response = super_client.post(
            '/api/accounting/merchant-aliases/resolve/',
            {'raw_descriptions': ['payu*netflix 12', 'RARO SAS']},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['resolved'][0]['merchant_name'] == 'Netflix'
        assert response.data['unresolved'] == ['RARO SAS']

    def test_create_alias_normalizes_match_text(self, super_client):
        response = super_client.post(
            '/api/accounting/merchant-aliases/create/',
            {'match_text': 'primax 8811', 'merchant_name': 'Primax',
             'default_category': 'fuel'},
            format='json',
        )
        assert response.status_code == 201
        assert response.data['match_text'] == 'PRIMAX'
