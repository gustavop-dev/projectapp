"""Serializer tests for the accounting module."""
from datetime import date
from decimal import Decimal

import pytest

from content.models import HostingRecord, IncomeRecord, RecurringPayment
from content.serializers.accounting import (
    AccountingSettingsSerializer,
    ExpenseRecordCreateUpdateSerializer,
    HostingRecordCreateUpdateSerializer,
    IncomeRecordCreateUpdateSerializer,
    IncomeRecordSerializer,
    PocketMovementCreateUpdateSerializer,
    RecurringPaymentCreateUpdateSerializer,
)


def income_payload(**overrides):
    payload = {
        'concept': 'Tendalux - Inicio 40%',
        'kind': 'expected',
        'period_date': '2026-01',
        'total_amount': '1280000.00',
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestPeriodHandling:
    def test_accepts_year_month_and_normalizes_to_day_one(self):
        serializer = IncomeRecordCreateUpdateSerializer(data=income_payload())
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['period_date'] == date(2026, 1, 1)

    def test_full_date_is_normalized_to_day_one(self):
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(period_date='2026-03-15'),
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['period_date'] == date(2026, 3, 1)

    def test_invalid_month_is_rejected(self):
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(period_date='2026-13'),
        )
        assert not serializer.is_valid()
        assert 'period_date' in serializer.errors

    def test_read_serializer_emits_period_and_spanish_label(self, make_income):
        income = make_income(period_date=date(2026, 3, 1))
        data = IncomeRecordSerializer(income).data
        assert data['period'] == '2026-03'
        assert data['period_label'] == 'Marzo 2026'
        assert data['company_amount'] == '0.00'


@pytest.mark.django_db
class TestPartnerSplitDefaults:
    def test_create_defaults_to_half_and_half(self):
        serializer = IncomeRecordCreateUpdateSerializer(data=income_payload())
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['gustavo_amount'] == Decimal('640000.00')
        assert serializer.validated_data['carlos_amount'] == Decimal('640000.00')

    def test_odd_cent_goes_to_carlos(self):
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(total_amount='100.01'),
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['gustavo_amount'] == Decimal('50.00')
        assert serializer.validated_data['carlos_amount'] == Decimal('50.01')

    def test_explicit_split_is_preserved(self):
        serializer = ExpenseRecordCreateUpdateSerializer(data={
            'concept': 'Windsurf',
            'period_date': '2026-03',
            'total_amount': '3000000.00',
            'gustavo_amount': '1000000.00',
            'carlos_amount': '2000000.00',
        })
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['gustavo_amount'] == Decimal('1000000.00')

    def test_split_over_total_is_rejected_in_spanish(self):
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(
                gustavo_amount='700000.00', carlos_amount='700000.00',
            ),
        )
        assert not serializer.is_valid()
        assert 'socios' in str(serializer.errors)

    def test_negative_amount_is_rejected(self):
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(gustavo_amount='-1.00'),
        )
        assert not serializer.is_valid()
        assert 'gustavo_amount' in serializer.errors


@pytest.mark.django_db
class TestPersonalLedger:
    def test_personal_ledger_normalizes_split_to_owner(self):
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(
                ledger='gustavo',
                gustavo_amount='100.00', carlos_amount='200.00',
            ),
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['gustavo_amount'] == Decimal('1280000.00')
        assert serializer.validated_data['carlos_amount'] == Decimal('0')

    def test_personal_ledger_without_split_assigns_owner(self):
        serializer = ExpenseRecordCreateUpdateSerializer(data={
            'concept': 'Aporte Carro Onix',
            'period_date': '2026-06',
            'ledger': 'carlos',
            'total_amount': '3000000.00',
        })
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['carlos_amount'] == Decimal('3000000.00')
        assert serializer.validated_data['gustavo_amount'] == Decimal('0')

    def test_patch_to_personal_ledger_renormalizes_split(self, make_income):
        income = make_income(
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('50.00'),
            carlos_amount=Decimal('50.00'),
        )
        serializer = IncomeRecordCreateUpdateSerializer(
            income, data={'ledger': 'gustavo'}, partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['gustavo_amount'] == Decimal('100.00')
        assert serializer.validated_data['carlos_amount'] == Decimal('0')

    def test_patch_amount_on_personal_record_renormalizes(self, make_income):
        income = make_income(
            ledger=IncomeRecord.Ledger.CARLOS,
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('0.00'),
            carlos_amount=Decimal('100.00'),
        )
        serializer = IncomeRecordCreateUpdateSerializer(
            income, data={'total_amount': '250.00'}, partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['carlos_amount'] == Decimal('250.00')
        assert serializer.validated_data['gustavo_amount'] == Decimal('0')

    def test_personal_income_cannot_target_pocket(self):
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(
                kind='liquid', destination='pocket', ledger='gustavo',
            ),
        )
        assert not serializer.is_valid()
        assert 'personales' in str(serializer.errors)

    def test_personal_expense_cannot_be_paid_from_pocket(self):
        serializer = ExpenseRecordCreateUpdateSerializer(data={
            'concept': 'Gasto personal',
            'period_date': '2026-06',
            'ledger': 'gustavo',
            'paid_from': 'pocket',
            'total_amount': '100.00',
        })
        assert not serializer.is_valid()
        assert 'personales' in str(serializer.errors)

    def test_expected_income_link_must_share_ledger(self, make_income):
        expected = make_income(
            kind=IncomeRecord.Kind.EXPECTED,
            ledger=IncomeRecord.Ledger.GUSTAVO,
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('100.00'),
            carlos_amount=Decimal('0.00'),
        )
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(kind='liquid', expected_income=expected.pk),
        )
        assert not serializer.is_valid()
        assert 'contabilidad' in str(serializer.errors)

    def test_read_serializer_exposes_ledger_label(self, make_income):
        income = make_income(
            ledger=IncomeRecord.Ledger.GUSTAVO,
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('100.00'),
            carlos_amount=Decimal('0.00'),
        )
        data = IncomeRecordSerializer(income).data
        assert data['ledger'] == 'gustavo'
        assert data['ledger_label'] == 'Personal Gustavo'


@pytest.mark.django_db
class TestIncomeRules:
    def test_pocket_destination_requires_liquid_kind(self):
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(kind='expected', destination='pocket'),
        )
        assert not serializer.is_valid()
        assert 'líquidos' in str(serializer.errors)

    def test_pocket_destination_allowed_for_liquid(self):
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(kind='liquid', destination='pocket'),
        )
        assert serializer.is_valid(), serializer.errors

    def test_expected_income_link_must_point_to_expected_record(
        self, make_income,
    ):
        liquid = make_income(kind=IncomeRecord.Kind.LIQUID)
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(kind='liquid', expected_income=liquid.pk),
        )
        assert not serializer.is_valid()
        assert 'expected_income' in serializer.errors


@pytest.mark.django_db
class TestEntityDefaults:
    def test_hosting_payment_per_cycle_defaults_from_modality(self):
        serializer = HostingRecordCreateUpdateSerializer(data={
            'client_name': 'German - Kore',
            'monthly_value': '91667.00',
            'payment_modality': HostingRecord.Modality.SEMIANNUAL,
        })
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['payment_per_cycle'] == Decimal('550002.00')

    def test_hosting_validity_range_is_checked(self):
        serializer = HostingRecordCreateUpdateSerializer(data={
            'client_name': 'X',
            'monthly_value': '100.00',
            'valid_from': '2026-09-02',
            'valid_to': '2026-03-02',
        })
        assert not serializer.is_valid()
        assert 'vigencia' in str(serializer.errors)

    def test_recurring_cop_equivalent_defaults_to_price_for_cop(self):
        serializer = RecurringPaymentCreateUpdateSerializer(data={
            'name': 'Netflix',
            'price': '39800.00',
            'currency': RecurringPayment.Currency.COP,
        })
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['cop_equivalent'] == Decimal('39800.00')

    def test_recurring_usd_does_not_default_cop_equivalent(self):
        serializer = RecurringPaymentCreateUpdateSerializer(data={
            'name': 'Claude Code 20x',
            'price': '200.00',
            'currency': RecurringPayment.Currency.USD,
        })
        assert serializer.is_valid(), serializer.errors
        assert 'cop_equivalent' not in serializer.validated_data

    def test_pocket_movement_amount_must_be_positive(self):
        serializer = PocketMovementCreateUpdateSerializer(data={
            'concept': 'Ajuste',
            'movement_date': '2026-06-01',
            'direction': 'in',
            'amount': '0.00',
        })
        assert not serializer.is_valid()
        assert 'amount' in serializer.errors


@pytest.mark.django_db
class TestSettingsSerializer:
    def test_rejects_invalid_recipient_email(self):
        serializer = AccountingSettingsSerializer(data={
            'notification_recipients': ['not-an-email'],
        })
        assert not serializer.is_valid()
        assert 'notification_recipients' in serializer.errors

    def test_accepts_valid_recipient_list(self):
        serializer = AccountingSettingsSerializer(data={
            'notification_recipients': ['gustavo@test.com', 'carlos@test.com'],
            'notifications_enabled': True,
        })
        assert serializer.is_valid(), serializer.errors
