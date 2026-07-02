"""Accounting change email notification tests.

Huey runs immediate (synchronous) outside production, so the task executes
inline and mail.outbox can be asserted directly.
"""
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core import mail

from content.models import AccountingChangeLog, AccountingSettings, EmailLog
from content.serializers.accounting import IncomeRecordCreateUpdateSerializer
from content.services import accounting_service
from content.services.accounting_email_service import (
    send_accounting_change_email,
)

EntityType = AccountingChangeLog.EntityType
Action = AccountingChangeLog.Action


def make_change_log(**overrides):
    defaults = {
        'entity_type': EntityType.INCOME,
        'object_id': 1,
        'object_repr': 'Kore - Inicio 40%',
        'action': Action.UPDATED,
        'changes': [{
            'field': 'total_amount',
            'label': 'Monto total',
            'old': '1000000.00',
            'new': '1160000.00',
        }],
        'actor_username': 'super_test',
    }
    defaults.update(overrides)
    return AccountingChangeLog.objects.create(**defaults)


@pytest.mark.django_db
class TestSendAccountingChangeEmail:
    def test_sends_one_email_to_all_recipients(self, accounting_settings):
        log = make_change_log()
        mail.outbox = []
        assert send_accounting_change_email(log.id) is True
        assert len(mail.outbox) == 1
        assert set(mail.outbox[0].to) == {
            'gustavo@test.com', 'carlos@test.com',
        }

    def test_subject_and_body_describe_the_change(self, accounting_settings):
        log = make_change_log()
        mail.outbox = []
        send_accounting_change_email(log.id)
        message = mail.outbox[0]
        assert '[Contabilidad]' in message.subject
        assert 'Ingreso actualizado' in message.subject
        assert 'Kore - Inicio 40%' in message.subject
        assert 'Monto total' in message.body
        assert '1000000.00' in message.body
        assert '1160000.00' in message.body
        assert 'super_test' in message.body

    def test_creates_email_log_row_per_recipient(self, accounting_settings):
        log = make_change_log()
        mail.outbox = []
        send_accounting_change_email(log.id)
        logs = EmailLog.objects.filter(template_key='accounting_change')
        assert logs.count() == 2
        assert set(logs.values_list('recipient', flat=True)) == {
            'gustavo@test.com', 'carlos@test.com',
        }
        assert all(row.status == EmailLog.Status.SENT for row in logs)
        assert logs.first().metadata['change_log_id'] == log.id

    def test_disabled_notifications_skip_sending(self, accounting_settings):
        accounting_settings.notifications_enabled = False
        accounting_settings.save()
        log = make_change_log()
        mail.outbox = []
        assert send_accounting_change_email(log.id) is False
        assert mail.outbox == []

    def test_empty_recipients_skip_sending(self, db):
        config = AccountingSettings.load()
        config.notification_recipients = []
        config.save()
        log = make_change_log()
        mail.outbox = []
        assert send_accounting_change_email(log.id) is False
        assert mail.outbox == []

    def test_missing_change_log_returns_false_without_raising(
        self, accounting_settings,
    ):
        assert send_accounting_change_email(999999) is False

    def test_send_failure_records_failed_email_logs(self, accounting_settings):
        log = make_change_log()
        mail.outbox = []
        with patch(
            'content.services.accounting_email_service.EmailMultiAlternatives.send',
            side_effect=OSError('smtp down'),
        ):
            assert send_accounting_change_email(log.id) is False
        failed = EmailLog.objects.filter(
            template_key='accounting_change',
            status=EmailLog.Status.FAILED,
        )
        assert failed.count() == 2
        assert 'smtp down' in failed.first().error_message


@pytest.mark.django_db
class TestEndToEndFromService:
    def test_create_record_enqueues_the_notification_task(
        self, superuser, accounting_settings,
    ):
        serializer = IncomeRecordCreateUpdateSerializer(data={
            'concept': 'Tendalux - Diseño 30%',
            'kind': 'expected',
            'period_date': '2026-02',
            'total_amount': '960000.00',
        })
        assert serializer.is_valid(), serializer.errors
        with patch('content.tasks.send_accounting_change_email') as task:
            income = accounting_service.create_record(
                EntityType.INCOME, serializer, superuser,
            )
        log = AccountingChangeLog.objects.get(
            entity_type=EntityType.INCOME, object_id=income.pk,
        )
        task.assert_called_once_with(log.id)
