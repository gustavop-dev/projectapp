"""Tests for create_fake_accounting and its delete_fake_data integration."""
import pytest
from django.core import mail
from django.core.management import call_command
from django.db.models import F

from content.models import (
    AccountingSettings,
    AdsSpendRecord,
    ExpenseRecord,
    HostingRecord,
    IncomeRecord,
    Ledger,
    PocketMovement,
    RecurringPayment,
)


@pytest.mark.django_db
class TestCreateFakeAccounting:
    def test_creates_tagged_rows_for_every_entity(self):
        call_command('create_fake_accounting', '--count', '6')
        for model in (
            IncomeRecord, ExpenseRecord, HostingRecord,
            PocketMovement, RecurringPayment, AdsSpendRecord,
        ):
            assert model.objects.filter(source_ref='fake:accounting').exists()
        assert not IncomeRecord.objects.exclude(
            source_ref='fake:accounting',
        ).exists()

    def test_covers_every_income_kind_and_fulfilment_state(self):
        """The Ingresos tab renders Pagado/Parcial/Pendiente plus Perdido.

        Without a row in each, those UI paths ship unexercised by hand.
        """
        call_command('create_fake_accounting', '--count', '12')
        kinds = set(
            IncomeRecord.objects.values_list('kind', flat=True).distinct(),
        )
        assert kinds == {'expected', 'liquid', 'lost'}

        states = set()
        for expected in IncomeRecord.objects.filter(kind='expected'):
            paid = sum(
                child.total_amount
                for child in expected.liquid_records.filter(kind='liquid')
            )
            if not paid:
                states.add('pending')
            elif paid < expected.total_amount:
                states.add('partial')
            else:
                states.add('paid')
        assert states == {'pending', 'partial', 'paid'}

    def test_written_off_income_never_has_payments(self):
        call_command('create_fake_accounting', '--count', '12')
        for lost in IncomeRecord.objects.filter(kind='lost'):
            assert not lost.liquid_records.exists()

    def test_seeds_notification_recipients_when_empty(self):
        call_command('create_fake_accounting', '--count', '2')
        settings_obj = AccountingSettings.load()
        assert len(settings_obj.notification_recipients) == 2

    def test_sends_no_emails(self, accounting_settings):
        mail.outbox = []
        call_command('create_fake_accounting', '--count', '3')
        assert mail.outbox == []

    def test_partner_draws_mirror_company_expenses_fully_assigned(self):
        """A pocket draw attributed to a partner is a company-ledger
        expense 100% the partner's, category personal (#114)."""
        call_command('create_fake_accounting', '--count', '6')
        draws = ExpenseRecord.objects.filter(
            source_ref='fake:accounting',
            category=ExpenseRecord.Category.PERSONAL,
            pocket_movement__isnull=False,
        )
        assert draws.count() > 0
        assert draws.exclude(ledger=Ledger.COMPANY).count() == 0
        assert draws.exclude(
            pocket_movement__direction=PocketMovement.Direction.OUT,
        ).count() == 0
        assert draws.exclude(
            total_amount=F('pocket_movement__amount'),
        ).count() == 0
        assert draws.exclude(gustavo_amount=0).exclude(
            carlos_amount=0,
        ).count() == 0

    def test_pocket_outs_mix_linked_business_and_historical_rows(self):
        """Company pocket payments carry a linked business expense while
        some rows stay unlinked as pre-linkage history."""
        call_command('create_fake_accounting', '--count', '6')
        linked_business = ExpenseRecord.objects.filter(
            source_ref='fake:accounting',
            category=ExpenseRecord.Category.BUSINESS,
            pocket_movement__isnull=False,
        )
        assert linked_business.count() > 0
        historical = PocketMovement.objects.filter(
            source_ref='fake:accounting',
            income_record__isnull=True,
            expense_record__isnull=True,
        )
        assert historical.count() > 0

    def test_pocket_liquidations_record_exact_payment_day(self):
        """Liquid incomes into the pocket keep a full payment date, the
        liquidate modal's exact-day option (#114)."""
        call_command('create_fake_accounting', '--count', '12')
        exact = IncomeRecord.objects.filter(
            source_ref='fake:accounting',
            kind=IncomeRecord.Kind.LIQUID,
            destination=IncomeRecord.Destination.POCKET,
        ).exclude(period_date__day=1)
        assert exact.count() > 0

    def test_delete_fake_data_removes_only_fake_rows(self, make_income):
        real_income = make_income(concept='Ingreso real')
        call_command('create_fake_accounting', '--count', '4')
        call_command('delete_fake_data', '--confirm')
        assert not IncomeRecord.objects.filter(
            source_ref='fake:accounting',
        ).exists()
        assert not PocketMovement.objects.filter(
            source_ref='fake:accounting',
        ).exists()
        assert IncomeRecord.objects.filter(pk=real_income.pk).exists()
