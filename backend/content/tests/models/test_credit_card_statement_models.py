"""Model tests for the credit-card statement sub-module."""
from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError

from content.models import (
    CreditCardStatement,
    CreditCardTransaction,
    MerchantAlias,
    normalize_descriptor,
)

pytestmark = pytest.mark.django_db


def _statement(**overrides):
    fields = {
        'card_name': 'Visa Bancolombia',
        'period_date': date(2026, 6, 1),
        'purchases_total': Decimal('1500000.00'),
    }
    fields.update(overrides)
    return CreditCardStatement.objects.create(**fields)


class TestNormalizeDescriptor:
    def test_uppercases_and_collapses_whitespace(self):
        assert normalize_descriptor('  payu*Netflix   co ') == 'PAYU*NETFLIX CO'

    def test_drops_digit_only_tokens(self):
        assert normalize_descriptor('PRIMAX 990011 MEDELLIN') == 'PRIMAX MEDELLIN'

    def test_keeps_mixed_alphanumeric_tokens(self):
        assert normalize_descriptor('UBER B2B 44') == 'UBER B2B'

    def test_empty_and_none_are_empty(self):
        assert normalize_descriptor('') == ''
        assert normalize_descriptor(None) == ''


class TestCreditCardStatement:
    def test_defaults_to_draft(self):
        statement = _statement()
        assert statement.status == CreditCardStatement.Status.DRAFT
        assert str(statement) == 'Visa Bancolombia — 2026-06'

    def test_card_and_period_are_unique_together(self):
        _statement()
        with pytest.raises(IntegrityError):
            _statement()

    def test_same_period_different_card_is_allowed(self):
        _statement()
        other = _statement(card_name='Mastercard Davivienda')
        assert other.pk is not None

    def test_deleting_statement_cascades_transactions(self):
        statement = _statement()
        CreditCardTransaction.objects.create(
            statement=statement,
            transaction_date=date(2026, 6, 5),
            raw_description='PAYU*NETFLIX',
            amount=Decimal('44900.00'),
        )
        statement.delete()
        assert CreditCardTransaction.objects.count() == 0


class TestMerchantAlias:
    def test_match_text_is_unique(self):
        MerchantAlias.objects.create(
            match_text='PAYU*NETFLIX', merchant_name='Netflix',
        )
        with pytest.raises(IntegrityError):
            MerchantAlias.objects.create(
                match_text='PAYU*NETFLIX', merchant_name='Otro',
            )
