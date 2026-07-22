"""Tests for the weekly card-debt reminder service (explicit dates)."""
from datetime import date
from decimal import Decimal

import pytest
from django.core import mail

from content.models import AccountingSettings, CardBalanceSnapshot, EmailLog
from content.services.accounting_card_reminder_service import (
    cycle_friday,
    run_card_reminder,
)

FRIDAY = date(2026, 7, 3)


@pytest.fixture
def reminder_settings(db):
    config = AccountingSettings.load()
    config.notification_recipients = ['gustavo@test.com', 'carlos@test.com']
    config.notifications_enabled = True
    config.card_reminder_enabled = True
    config.save()
    return config


def snapshot(day, card='T.C 0064'):
    return CardBalanceSnapshot.objects.create(
        snapshot_date=day, card_name=card,
        available_amount=Decimal('100.00'), debt_amount=Decimal('900.00'),
    )


class TestCycleFriday:
    def test_friday_is_its_own_cycle_start(self):
        assert cycle_friday(FRIDAY) == FRIDAY

    def test_weekend_and_weekdays_map_to_previous_friday(self):
        assert cycle_friday(date(2026, 7, 4)) == FRIDAY   # sábado
        assert cycle_friday(date(2026, 7, 6)) == FRIDAY   # lunes
        assert cycle_friday(date(2026, 7, 9)) == FRIDAY   # jueves
        assert cycle_friday(date(2026, 7, 10)) == date(2026, 7, 10)  # viernes


@pytest.mark.django_db
class TestRunCardReminder:
    def test_sends_on_friday_without_snapshot(self, reminder_settings):
        mail.outbox = []
        assert run_card_reminder(today=FRIDAY) is True
        assert len(mail.outbox) == 1
        assert 'deuda de tarjetas' in mail.outbox[0].subject
        assert '(recordatorio #' not in mail.outbox[0].subject
        config = AccountingSettings.load()
        assert config.card_reminder_cycle_start == FRIDAY
        assert config.card_reminder_last_sent_at == FRIDAY
        assert EmailLog.objects.filter(
            template_key='accounting_card_reminder', status=EmailLog.Status.SENT,
        ).count() == 2

    def test_body_formats_debt_and_snapshot_date(self, reminder_settings):
        CardBalanceSnapshot.objects.create(
            snapshot_date=date(2026, 6, 26), card_name='T.C 0064',
            available_amount=Decimal('100.00'),
            debt_amount=Decimal('6476857.00'),
        )
        mail.outbox = []
        assert run_card_reminder(today=FRIDAY) is True
        body = mail.outbox[0].body
        assert "deuda $6'476.857" in body
        assert 'Vie, 26 jun 2026' in body
        assert '6476857.00' not in body

    def test_snapshot_on_or_after_friday_suppresses(self, reminder_settings):
        snapshot(FRIDAY)
        assert run_card_reminder(today=FRIDAY) is False

    def test_future_snapshot_also_suppresses(self, reminder_settings):
        snapshot(date(2026, 7, 8))
        assert run_card_reminder(today=FRIDAY) is False

    def test_older_snapshot_does_not_suppress(self, reminder_settings):
        snapshot(date(2026, 6, 26))
        assert run_card_reminder(today=FRIDAY) is True

    def test_realerts_after_two_days_not_before(self, reminder_settings):
        assert run_card_reminder(today=FRIDAY) is True
        mail.outbox = []
        # Sábado (+1 día): dentro de la ventana, no reenvía.
        assert run_card_reminder(today=date(2026, 7, 4)) is False
        # Domingo (+2 días): re-alerta con número creciente.
        assert run_card_reminder(today=date(2026, 7, 5)) is True
        assert '(recordatorio #2)' in mail.outbox[-1].subject

    def test_new_friday_opens_new_cycle(self, reminder_settings):
        assert run_card_reminder(today=FRIDAY) is True
        # Jueves siguiente (+6 días, sin snapshot): sigue el ciclo viejo.
        assert run_card_reminder(today=date(2026, 7, 9)) is True
        mail.outbox = []
        # Viernes siguiente: ciclo nuevo → cuenta desde #1 aunque el último
        # envío fue ayer.
        assert run_card_reminder(today=date(2026, 7, 10)) is True
        assert '(recordatorio #' not in mail.outbox[-1].subject
        assert AccountingSettings.load().card_reminder_cycle_start == date(2026, 7, 10)

    def test_respects_card_reminder_toggle(self, reminder_settings):
        reminder_settings.card_reminder_enabled = False
        reminder_settings.save()
        assert run_card_reminder(today=FRIDAY) is False

    def test_respects_global_notifications_toggle(self, reminder_settings):
        reminder_settings.notifications_enabled = False
        reminder_settings.save()
        assert run_card_reminder(today=FRIDAY) is False

    def test_no_recipients_does_not_mark_cycle(self, reminder_settings):
        reminder_settings.notification_recipients = []
        reminder_settings.save()
        assert run_card_reminder(today=FRIDAY) is False
        config = AccountingSettings.load()
        assert config.card_reminder_cycle_start is None
        assert config.card_reminder_last_sent_at is None
