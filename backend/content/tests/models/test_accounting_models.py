"""Model-level tests for the accounting module."""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from content.models import (
    AccountingChangeLog,
    AccountingSettings,
    CardBalanceSnapshot,
    HostingRecord,
    PocketMovement,
    RecurringPayment,
)


@pytest.mark.django_db
class TestPartnerSplit:
    def test_clean_rejects_partner_sum_over_total(self, make_income):
        income = make_income(
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('60.00'),
            carlos_amount=Decimal('60.00'),
        )
        with pytest.raises(ValidationError) as exc_info:
            income.full_clean()
        assert 'socios' in str(exc_info.value)

    def test_clean_rejects_negative_amounts(self, make_income):
        income = make_income(
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('-10.00'),
            carlos_amount=Decimal('0.00'),
        )
        with pytest.raises(ValidationError) as exc_info:
            income.full_clean()
        assert 'gustavo_amount' in exc_info.value.message_dict

    def test_company_amount_is_the_unassigned_remainder(self, make_income):
        income = make_income(
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('30.00'),
            carlos_amount=Decimal('30.00'),
        )
        assert income.company_amount == Decimal('40.00')

    def test_full_split_leaves_zero_company_amount(self, make_expense):
        expense = make_expense(
            total_amount=Decimal('80.00'),
            gustavo_amount=Decimal('40.00'),
            carlos_amount=Decimal('40.00'),
        )
        assert expense.company_amount == Decimal('0.00')


@pytest.mark.django_db
class TestAccountingSettings:
    def test_save_forces_pk_1(self):
        settings_obj = AccountingSettings(
            notification_recipients=['a@test.com'],
        )
        settings_obj.pk = 99
        settings_obj.save()
        assert settings_obj.pk == 1

    def test_load_is_idempotent_singleton(self):
        first = AccountingSettings.load()
        second = AccountingSettings.load()
        assert first.pk == second.pk == 1
        assert AccountingSettings.objects.count() == 1


@pytest.mark.django_db
class TestAccountingChangeLog:
    def test_ordering_is_latest_first(self):
        older = AccountingChangeLog.objects.create(
            entity_type=AccountingChangeLog.EntityType.INCOME,
            object_id=1,
            object_repr='Ingreso A',
            action=AccountingChangeLog.Action.CREATED,
        )
        newer = AccountingChangeLog.objects.create(
            entity_type=AccountingChangeLog.EntityType.INCOME,
            object_id=1,
            object_repr='Ingreso A',
            action=AccountingChangeLog.Action.UPDATED,
        )
        assert list(AccountingChangeLog.objects.all()) == [newer, older]

    def test_str_includes_entity_action_and_repr(self):
        log = AccountingChangeLog.objects.create(
            entity_type=AccountingChangeLog.EntityType.EXPENSE,
            object_id=5,
            object_repr='Claude Code 20x',
            action=AccountingChangeLog.Action.DELETED,
        )
        assert 'Gasto' in str(log)
        assert 'Eliminado' in str(log)
        assert 'Claude Code 20x' in str(log)


@pytest.mark.django_db
class TestPocketMovement:
    def test_amount_must_be_positive(self):
        movement = PocketMovement(
            concept='Ajuste',
            movement_date=date(2026, 6, 1),
            direction=PocketMovement.Direction.IN,
            amount=Decimal('0.00'),
        )
        with pytest.raises(ValidationError) as exc_info:
            movement.full_clean()
        assert 'amount' in exc_info.value.message_dict

    def test_manual_movement_is_not_auto_managed(self):
        movement = PocketMovement.objects.create(
            concept='Trans. Gustavo',
            movement_date=date(2026, 5, 9),
            direction=PocketMovement.Direction.OUT,
            amount=Decimal('200000.00'),
        )
        assert movement.is_auto_managed is False


@pytest.mark.django_db
class TestRecurringPayment:
    def test_monthly_cop_cost_prorates_annual_frequency(self):
        payment = RecurringPayment.objects.create(
            name='NameCheap',
            price=Decimal('10.98'),
            currency=RecurringPayment.Currency.USD,
            cop_equivalent=Decimal('43920.00'),
            frequency=RecurringPayment.Frequency.ANNUAL,
        )
        assert payment.monthly_cop_cost == Decimal('3660.00')

    def test_monthly_cop_cost_is_zero_without_cop_equivalent(self):
        payment = RecurringPayment.objects.create(
            name='Apollo',
            price=Decimal('0.00'),
            cop_equivalent=Decimal('0.00'),
            frequency=RecurringPayment.Frequency.MONTHLY,
        )
        assert payment.monthly_cop_cost == Decimal('0')


@pytest.mark.django_db
class TestSimpleReprs:
    def test_hosting_record_str(self):
        hosting = HostingRecord.objects.create(
            client_name='German - Kore',
            domain_url='https://korehealths.com/',
            monthly_value=Decimal('91667.00'),
        )
        assert 'German - Kore' in str(hosting)

    def test_card_snapshot_str(self):
        snapshot = CardBalanceSnapshot.objects.create(
            snapshot_date=date(2026, 7, 1),
            card_name='T.C 0064',
            available_amount=Decimal('3849046.00'),
            debt_amount=Decimal('4150954.00'),
        )
        assert 'T.C 0064' in str(snapshot)
