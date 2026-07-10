"""Serializer tests for the credit-card statement sub-module."""
from datetime import date
from decimal import Decimal

import pytest

from content.models import CreditCardStatement, MerchantAlias
from content.serializers.accounting_statement import (
    CreditCardStatementWriteSerializer,
    CreditCardTransactionWriteSerializer,
    MerchantAliasWriteSerializer,
)

pytestmark = pytest.mark.django_db

STATEMENT_PAYLOAD = {
    'card_name': 'Visa Bancolombia',
    'period_date': '2026-06',
    'purchases_total': '1500000.00',
}

TX_PAYLOAD = {
    'transaction_date': '2026-06-05',
    'raw_description': 'PAYU*NETFLIX',
    'amount': '44900.00',
}


class TestStatementWriteSerializer:
    def test_accepts_yyyy_mm_period_and_normalizes_to_day_one(self):
        serializer = CreditCardStatementWriteSerializer(data=STATEMENT_PAYLOAD)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['period_date'] == date(2026, 6, 1)

    def test_rejects_duplicate_card_period_in_spanish(self):
        CreditCardStatement.objects.create(
            card_name='Visa Bancolombia',
            period_date=date(2026, 6, 1),
            purchases_total=Decimal('1'),
        )
        serializer = CreditCardStatementWriteSerializer(data=STATEMENT_PAYLOAD)
        assert not serializer.is_valid()
        assert 'Ya existe un extracto' in str(serializer.errors)

    def test_status_is_not_writable(self):
        serializer = CreditCardStatementWriteSerializer(
            data={**STATEMENT_PAYLOAD, 'status': 'processed'},
        )
        assert serializer.is_valid(), serializer.errors
        assert 'status' not in serializer.validated_data


class TestTransactionWriteSerializer:
    def test_minimal_payload_is_valid(self):
        serializer = CreditCardTransactionWriteSerializer(data=TX_PAYLOAD)
        assert serializer.is_valid(), serializer.errors

    def test_negative_amount_is_allowed(self):
        serializer = CreditCardTransactionWriteSerializer(
            data={**TX_PAYLOAD, 'amount': '-44900.00'},
        )
        assert serializer.is_valid(), serializer.errors

    def test_installment_pair_must_be_complete(self):
        serializer = CreditCardTransactionWriteSerializer(
            data={**TX_PAYLOAD, 'installment_number': 3},
        )
        assert not serializer.is_valid()

    def test_installment_number_cannot_exceed_total(self):
        serializer = CreditCardTransactionWriteSerializer(
            data={
                **TX_PAYLOAD,
                'installment_number': 13,
                'installments_total': 12,
            },
        )
        assert not serializer.is_valid()

    def test_original_amount_requires_currency(self):
        serializer = CreditCardTransactionWriteSerializer(
            data={**TX_PAYLOAD, 'original_amount': '11.99'},
        )
        assert not serializer.is_valid()


class TestMerchantAliasWriteSerializer:
    def test_normalizes_match_text(self):
        serializer = MerchantAliasWriteSerializer(
            data={
                'match_text': ' payu*netflix  990011 ',
                'merchant_name': 'Netflix',
            },
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['match_text'] == 'PAYU*NETFLIX'

    def test_rejects_normalized_duplicate(self):
        MerchantAlias.objects.create(
            match_text='PAYU*NETFLIX', merchant_name='Netflix',
        )
        serializer = MerchantAliasWriteSerializer(
            data={'match_text': 'payu*netflix 123', 'merchant_name': 'Otro'},
        )
        assert not serializer.is_valid()
        assert 'Ya existe un alias' in str(serializer.errors)
