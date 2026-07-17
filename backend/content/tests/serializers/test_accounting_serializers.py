"""Serializer tests for the accounting module."""
from datetime import date
from decimal import Decimal

import pytest

from content.models import HostingRecord, IncomeRecord, RecurringPayment
from content.serializers.accounting import (
    AccountingSettingsSerializer,
    CardBalanceSnapshotCreateUpdateSerializer,
    ExpenseRecordCreateUpdateSerializer,
    HostingRecordCreateUpdateSerializer,
    IncomeRecordCreateUpdateSerializer,
    IncomeRecordSerializer,
    PocketMovementCreateUpdateSerializer,
    RecurringPaymentCreateUpdateSerializer,
    month_label,
)


class TestMonthLabel:
    def test_empty_date_returns_a_blank_label(self):
        assert month_label(None) == ''


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

    def test_pocket_destination_rejected_for_lost_kind(self):
        serializer = IncomeRecordCreateUpdateSerializer(
            data=income_payload(kind='lost', destination='pocket'),
        )
        assert not serializer.is_valid()
        assert 'líquidos' in str(serializer.errors)

    def test_expected_without_payments_can_be_written_off(self, make_income):
        expected = make_income(kind=IncomeRecord.Kind.EXPECTED)
        serializer = IncomeRecordCreateUpdateSerializer(
            expected, data={'kind': 'lost'}, partial=True,
        )
        assert serializer.is_valid(), serializer.errors

    def test_expected_with_payments_cannot_be_written_off(self, make_income):
        """Writing it off would strand the liquid child and skew received_pct."""
        expected = make_income(kind=IncomeRecord.Kind.EXPECTED)
        make_income(
            kind=IncomeRecord.Kind.LIQUID,
            total_amount=Decimal('400000.00'),
            gustavo_amount=Decimal('200000.00'),
            carlos_amount=Decimal('200000.00'),
            expected_income=expected,
        )
        serializer = IncomeRecordCreateUpdateSerializer(
            expected, data={'kind': 'lost'}, partial=True,
        )
        assert not serializer.is_valid()
        assert 'ya tiene liquidaciones' in str(serializer.errors)

    def test_expected_with_only_a_lost_child_can_still_be_written_off(
        self, make_income,
    ):
        expected = make_income(kind=IncomeRecord.Kind.EXPECTED)
        make_income(kind=IncomeRecord.Kind.LOST, expected_income=expected)
        serializer = IncomeRecordCreateUpdateSerializer(
            expected, data={'kind': 'lost'}, partial=True,
        )
        assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
class TestIncomePaymentState:
    def test_payment_state_at_the_three_boundaries(self, make_income):
        cases = [
            (Decimal('0.00'), 'pending', '0.00', '1000000.00'),
            (Decimal('400000.00'), 'partial', '400000.00', '600000.00'),
            (Decimal('1000000.00'), 'paid', '1000000.00', '0.00'),
        ]
        for paid, status, paid_repr, pending_repr in cases:
            expected = make_income(
                kind=IncomeRecord.Kind.EXPECTED,
                total_amount=Decimal('1000000.00'),
            )
            if paid:
                make_income(
                    kind=IncomeRecord.Kind.LIQUID, total_amount=paid,
                    gustavo_amount=Decimal('0'), carlos_amount=Decimal('0'),
                    expected_income=expected,
                )
            data = IncomeRecordSerializer(expected).data
            assert data['payment_status'] == status
            assert data['paid_amount'] == paid_repr
            assert data['pending_amount'] == pending_repr

    def test_non_expected_rows_report_no_payment_state(self, make_income):
        for kind in (IncomeRecord.Kind.LIQUID, IncomeRecord.Kind.LOST):
            data = IncomeRecordSerializer(make_income(kind=kind)).data
            assert data['payment_status'] is None
            assert data['paid_amount'] is None
            assert data['pending_amount'] is None


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


@pytest.mark.django_db
class TestCardSnapshotDebtComputation:
    """Debt is server-computed (cupo − disponible) for catalog cards."""

    CARD = 'T.C Test 01'

    def _card(self, **overrides):
        from content.models import CreditCard

        defaults = {
            'name': self.CARD,
            'credit_limit': Decimal('8000000.00'),
            'statements_since': date(2026, 5, 1),
        }
        defaults.update(overrides)
        return CreditCard.objects.create(**defaults)

    def test_catalog_card_computes_debt_and_ignores_client_value(self):
        self._card()
        serializer = CardBalanceSnapshotCreateUpdateSerializer(data={
            'snapshot_date': '2026-07-10',
            'card_name': self.CARD,
            'available_amount': '3000000.00',
            'debt_amount': '1.00',
        })
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['debt_amount'] == Decimal('5000000.00')

    def test_available_over_limit_is_rejected(self):
        self._card()
        serializer = CardBalanceSnapshotCreateUpdateSerializer(data={
            'snapshot_date': '2026-07-10',
            'card_name': self.CARD,
            'available_amount': '9000000.00',
        })
        assert not serializer.is_valid()
        assert 'available_amount' in serializer.errors

    def test_non_catalog_card_requires_explicit_debt_on_create(self):
        payload = {
            'snapshot_date': '2026-07-10',
            'card_name': 'T.C Legacy',
            'available_amount': '3000000.00',
        }
        serializer = CardBalanceSnapshotCreateUpdateSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'debt_amount' in serializer.errors

        serializer = CardBalanceSnapshotCreateUpdateSerializer(
            data={**payload, 'debt_amount': '1200000.00'},
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['debt_amount'] == Decimal('1200000.00')

    def test_notes_only_update_keeps_stored_debt(self):
        from content.models import CardBalanceSnapshot

        card = self._card()
        snapshot = CardBalanceSnapshot.objects.create(
            snapshot_date=date(2026, 6, 1),
            card_name=self.CARD,
            available_amount=Decimal('3000000.00'),
            debt_amount=Decimal('5000000.00'),
        )
        # The cupo changed after the snapshot was written: a notes-only
        # edit must not rewrite the historic debt.
        card.credit_limit = Decimal('10000000.00')
        card.save(update_fields=['credit_limit'])

        serializer = CardBalanceSnapshotCreateUpdateSerializer(
            snapshot, data={'notes': 'revisado'}, partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        snapshot.refresh_from_db()
        assert snapshot.debt_amount == Decimal('5000000.00')

    def test_available_change_recomputes_with_current_cupo(self):
        from content.models import CardBalanceSnapshot

        self._card()
        snapshot = CardBalanceSnapshot.objects.create(
            snapshot_date=date(2026, 6, 1),
            card_name=self.CARD,
            available_amount=Decimal('3000000.00'),
            debt_amount=Decimal('5000000.00'),
        )
        serializer = CardBalanceSnapshotCreateUpdateSerializer(
            snapshot, data={'available_amount': '2000000.00'}, partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['debt_amount'] == Decimal('6000000.00')
