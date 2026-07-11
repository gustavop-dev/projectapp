"""Service tests for accounting_statement_service (extractos)."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import (
    AccountingChangeLog,
    CreditCardStatement,
    CreditCardTransaction,
    ExpenseRecord,
    MerchantAlias,
    PocketMovement,
)
from content.serializers.accounting_statement import (
    CreditCardStatementWriteSerializer,
    CreditCardTransactionWriteSerializer,
)
from content.services import accounting_service, accounting_statement_service

pytestmark = pytest.mark.django_db

EntityType = AccountingChangeLog.EntityType


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify') as mock_notify:
        yield mock_notify


def _create(transactions=None, user=None, **header_overrides):
    header = {
        'card_name': 'Visa Bancolombia',
        'period_date': '2026-06',
        'purchases_total': '100000.00',
    }
    header.update(header_overrides)
    statement_serializer = CreditCardStatementWriteSerializer(data=header)
    assert statement_serializer.is_valid(), statement_serializer.errors
    transactions_serializer = CreditCardTransactionWriteSerializer(
        data=transactions or [], many=True,
    )
    assert transactions_serializer.is_valid(), transactions_serializer.errors
    return accounting_statement_service.create_statement_with_transactions(
        statement_serializer, transactions_serializer, user,
    )


TX = {
    'transaction_date': '2026-06-05',
    'raw_description': 'PAYU*NETFLIX 990011',
    'amount': '60000.00',
}


class TestCreateStatement:
    def test_creates_statement_with_transactions_atomically(self):
        statement = _create(transactions=[
            TX,
            {**TX, 'raw_description': 'PRIMAX 8811', 'amount': '40000.00'},
        ])
        assert statement.transactions.count() == 2
        assert statement.status == CreditCardStatement.Status.DRAFT

    def test_audit_shape_one_statement_email_txs_silent(self, _mute_notifications):
        statement = _create(transactions=[TX])
        statement_logs = AccountingChangeLog.objects.filter(
            entity_type=EntityType.STATEMENT,
        )
        tx_logs = AccountingChangeLog.objects.filter(
            entity_type=EntityType.STATEMENT_TX,
        )
        assert statement_logs.count() == 1
        assert tx_logs.count() == 1
        # Only the statement-level log notifies.
        assert _mute_notifications.call_count == 1

    def test_never_touches_expenses_or_pocket(self):
        _create(transactions=[TX])
        assert ExpenseRecord.objects.count() == 0
        assert PocketMovement.objects.count() == 0

    def test_known_alias_is_applied_on_create(self):
        MerchantAlias.objects.create(
            match_text='PAYU*NETFLIX',
            merchant_name='Netflix',
            default_category='software',
        )
        statement = _create(transactions=[TX])
        tx = statement.transactions.get()
        assert tx.merchant_name == 'Netflix'
        assert tx.category == 'software'
        assert tx.is_identified is True


class TestResolveMerchants:
    def test_splits_resolved_and_unresolved(self):
        MerchantAlias.objects.create(
            match_text='PAYU*NETFLIX', merchant_name='Netflix',
            default_category='software',
        )
        result = accounting_statement_service.resolve_merchants(
            ['payu*netflix 4411', 'EMPRESA RARA SAS'],
        )
        assert result['resolved'][0]['merchant_name'] == 'Netflix'
        assert result['unresolved'] == ['EMPRESA RARA SAS']


class TestSaveMerchantAliases:
    def test_upsert_is_idempotent_and_applies_to_draft(self):
        statement = _create(transactions=[TX])
        payload = [{
            'raw_description': 'PAYU*NETFLIX 990011',
            'merchant_name': 'Netflix',
            'category': 'software',
        }]
        first = accounting_statement_service.save_merchant_aliases(
            payload, None, statement_id=statement.pk,
        )
        second = accounting_statement_service.save_merchant_aliases(
            payload, None, statement_id=statement.pk,
        )
        assert MerchantAlias.objects.count() == 1
        assert first['updated_transactions'] == 1
        # Already identified: the second pass touches nothing.
        assert second['updated_transactions'] == 0
        tx = statement.transactions.get()
        assert tx.merchant_name == 'Netflix'
        assert tx.is_identified is True


class TestFinalize:
    def test_finalize_blocks_on_mismatch_with_difference(self):
        statement = _create(transactions=[TX])  # 60.000 vs 100.000
        with pytest.raises(ValueError) as excinfo:
            accounting_statement_service.finalize_statement(statement, None)
        assert 'diferencia' in str(excinfo.value)
        statement.refresh_from_db()
        assert statement.status == CreditCardStatement.Status.DRAFT

    def test_finalize_succeeds_within_tolerance(self):
        statement = _create(
            transactions=[{**TX, 'amount': '99999.50'}],
        )
        accounting_statement_service.finalize_statement(statement, None)
        statement.refresh_from_db()
        assert statement.status == CreditCardStatement.Status.PROCESSED

    def test_force_overrides_mismatch(self):
        statement = _create(transactions=[TX])
        accounting_statement_service.finalize_statement(
            statement, None, force=True,
        )
        statement.refresh_from_db()
        assert statement.status == CreditCardStatement.Status.PROCESSED

    def test_reopen_returns_to_draft(self):
        statement = _create(transactions=[TX])
        accounting_statement_service.finalize_statement(
            statement, None, force=True,
        )
        accounting_statement_service.reopen_statement(statement, None)
        statement.refresh_from_db()
        assert statement.status == CreditCardStatement.Status.DRAFT

    def test_processed_statement_rejects_new_transactions(self):
        statement = _create(transactions=[{**TX, 'amount': '100000.00'}])
        accounting_statement_service.finalize_statement(statement, None)
        serializer = CreditCardTransactionWriteSerializer(data=[TX], many=True)
        assert serializer.is_valid()
        with pytest.raises(ValueError):
            accounting_statement_service.add_transactions(
                statement, serializer, None,
            )


class TestMonthStatus:
    def test_grid_reports_twelve_months_with_statuses(self):
        statement = _create(transactions=[])
        accounting_statement_service.finalize_statement(
            statement, None, force=True,
        )
        _create(card_name='Mastercard', period_date='2026-07')
        payload = accounting_statement_service.statement_month_status(2026)
        assert len(payload['months']) == 12
        june = payload['months'][5]
        assert june['has_processed'] is True
        july = payload['months'][6]
        assert july['has_draft'] is True
        # `cards` merges statement names with the active catalog (the
        # seed migration adds 'T.C 0064').
        assert {'Mastercard', 'Visa Bancolombia'} <= set(payload['cards'])

    def test_category_totals_groups_amounts(self):
        statement = _create(transactions=[
            {**TX, 'category': 'software'},
            {**TX, 'raw_description': 'PRIMAX', 'amount': '40000.00',
             'category': 'fuel'},
        ])
        totals = accounting_statement_service.statement_category_totals(
            statement,
        )
        assert {row['category'] for row in totals} == {'software', 'fuel'}
        software = next(r for r in totals if r['category'] == 'software')
        assert software['total'] == '60000.00'


class TestMonthStatusCatalog:
    """year_options and per-month `applies` follow the card catalog."""

    @pytest.fixture(autouse=True)
    def _clean_catalog(self):
        # Migration 0158 seeds 'T.C 0064'; these tests need full control
        # over which catalog cards exist.
        from content.models import CreditCard

        CreditCard.objects.all().delete()

    def _catalog_card(self, **overrides):
        from content.models import CreditCard

        defaults = {
            'name': 'Visa Bancolombia',
            'credit_limit': Decimal('8000000.00'),
            'statements_since': date(2026, 5, 1),
        }
        defaults.update(overrides)
        return CreditCard.objects.create(**defaults)

    def test_year_options_and_applies_follow_statements_since(self):
        self._catalog_card()
        payload = accounting_statement_service.statement_month_status(2026)
        assert payload['year_options'][0] == 2026
        by_period = {month['period']: month for month in payload['months']}
        assert by_period['2026-04']['applies'] is False
        assert by_period['2026-05']['applies'] is True
        assert 'Visa Bancolombia' in payload['cards']

    def test_inactive_catalog_cards_do_not_shape_the_grid(self):
        self._catalog_card(is_active=False)
        payload = accounting_statement_service.statement_month_status(2026)
        assert all(month['applies'] for month in payload['months'])
        assert 'Visa Bancolombia' not in payload['cards']

    def test_fallback_uses_earliest_statement_year(self):
        _create(period_date='2025-11')
        payload = accounting_statement_service.statement_month_status(2025)
        assert payload['year_options'][0] == 2025
        by_period = {month['period']: month for month in payload['months']}
        # A month with an actual statement always applies.
        assert by_period['2025-11']['applies'] is True
