"""Tests for create_fake_accounting and its delete_fake_data integration."""
import pytest
from django.core import mail
from django.core.management import call_command

from content.models import (
    AccountingSettings,
    AdsSpendRecord,
    ExpenseRecord,
    HostingRecord,
    IncomeRecord,
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

    def test_seeds_notification_recipients_when_empty(self):
        call_command('create_fake_accounting', '--count', '2')
        settings_obj = AccountingSettings.load()
        assert len(settings_obj.notification_recipients) == 2

    def test_sends_no_emails(self, accounting_settings):
        mail.outbox = []
        call_command('create_fake_accounting', '--count', '3')
        assert mail.outbox == []

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
