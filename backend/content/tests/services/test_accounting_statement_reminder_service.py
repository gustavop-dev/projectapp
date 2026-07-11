"""Tests for the monthly statement reminder service (explicit dates)."""
from datetime import date
from decimal import Decimal

import pytest
from django.core import mail

from content.models import (
    AccountingSettings,
    CreditCard,
    CreditCardStatement,
    EmailLog,
)
from content.services.accounting_statement_reminder_service import (
    pending_statements,
    previous_month,
    run_statement_reminder,
)

TODAY = date(2026, 7, 10)
TARGET = date(2026, 6, 1)  # previous month of TODAY


@pytest.fixture
def reminder_settings(db):
    config = AccountingSettings.load()
    config.notification_recipients = ['gustavo@test.com']
    config.notifications_enabled = True
    config.statement_reminder_enabled = True
    config.statement_reminder_last_sent_at = None
    config.save()
    return config


@pytest.fixture(autouse=True)
def _clean_catalog(db):
    # Migration 0158 seeds 'T.C 0064'; these tests control the catalog.
    CreditCard.objects.all().delete()


def card(name='T.C 0064', since=date(2026, 5, 1), active=True):
    return CreditCard.objects.create(
        name=name,
        credit_limit=Decimal('8000000.00'),
        statements_since=since,
        is_active=active,
    )


def statement(card_name='T.C 0064', period=TARGET, status='processed', pdf=''):
    record = CreditCardStatement.objects.create(
        card_name=card_name,
        period_date=period,
        status=status,
        purchases_total=Decimal('100000.00'),
    )
    if pdf:
        record.pdf_file.name = pdf
        record.save(update_fields=['pdf_file'])
    return record


class TestPreviousMonth:
    def test_mid_month_maps_to_previous(self):
        assert previous_month(TODAY) == TARGET

    def test_january_maps_to_december(self):
        assert previous_month(date(2026, 1, 15)) == date(2025, 12, 1)


@pytest.mark.django_db
class TestPendingStatements:
    def test_missing_statement_is_pending(self):
        card()
        pending = pending_statements(TODAY)
        assert len(pending) == 1
        assert pending[0]['reason'] == 'Sin extracto registrado'

    def test_draft_statement_is_pending(self):
        card()
        statement(status='draft')
        assert pending_statements(TODAY)[0]['reason'] == (
            'Extracto en borrador (sin procesar)'
        )

    def test_processed_without_pdf_is_pending(self):
        card()
        statement(status='processed')
        assert 'PDF' in pending_statements(TODAY)[0]['reason']

    def test_processed_with_pdf_is_complete(self):
        card()
        statement(status='processed', pdf='statement_pdfs/2026/06/x.pdf')
        assert pending_statements(TODAY) == []

    def test_cards_before_statements_since_are_skipped(self):
        card(since=date(2026, 7, 1))  # statements start after TARGET
        assert pending_statements(TODAY) == []

    def test_inactive_cards_are_skipped(self):
        card(active=False)
        assert pending_statements(TODAY) == []


@pytest.mark.django_db
class TestRunStatementReminder:
    def test_sends_and_records_when_pending(self, reminder_settings):
        card()
        mail.outbox = []
        assert run_statement_reminder(today=TODAY) is True
        assert len(mail.outbox) == 1
        assert 'extracto' in mail.outbox[0].subject.lower()
        config = AccountingSettings.load()
        assert config.statement_reminder_last_sent_at == TODAY
        assert EmailLog.objects.filter(
            template_key='accounting_statement_reminder',
            status=EmailLog.Status.SENT,
        ).count() == 1

    def test_eight_day_cadence(self, reminder_settings):
        card()
        AccountingSettings.objects.filter(pk=1).update(
            statement_reminder_last_sent_at=date(2026, 7, 5),
        )
        assert run_statement_reminder(today=TODAY) is False  # 5 days
        AccountingSettings.objects.filter(pk=1).update(
            statement_reminder_last_sent_at=date(2026, 7, 2),
        )
        assert run_statement_reminder(today=TODAY) is True   # 8 days

    def test_toggle_off_suppresses(self, reminder_settings):
        card()
        AccountingSettings.objects.filter(pk=1).update(
            statement_reminder_enabled=False,
        )
        assert run_statement_reminder(today=TODAY) is False

    def test_nothing_pending_no_send(self, reminder_settings):
        card()
        statement(status='processed', pdf='statement_pdfs/2026/06/x.pdf')
        assert run_statement_reminder(today=TODAY) is False
