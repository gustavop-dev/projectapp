"""The one-shot backfill that makes the send log's history useful on day one.

Every accounting notice has always written the ids of what it was about into
`EmailLog.metadata`. The migration turns those six known shapes into queryable
`EmailLogTarget` rows; it runs once in production, so its logic is exercised
here rather than trusted.
"""
from decimal import Decimal
from importlib import import_module

import pytest
from django.apps import apps

from content.models import AccountingChangeLog, CreditCard, EmailLog, EmailLogTarget

pytestmark = pytest.mark.django_db

migration = import_module(
    'content.migrations.0194_backfill_email_log_targets',
)


def run_backfill():
    migration.forwards(apps, None)


def make_log(template_key, metadata, **kwargs):
    return EmailLog.objects.create(
        template_key=template_key,
        recipient='ana@test.com',
        subject='[Contabilidad]',
        status=EmailLog.Status.SENT,
        metadata=metadata,
        **kwargs,
    )


def targets_of(log):
    return sorted(
        EmailLogTarget.objects.filter(email_log=log)
        .values_list('entity_type', 'object_id'),
    )


def test_a_change_notice_recovers_its_record_and_its_action():
    change_log = AccountingChangeLog.objects.create(
        entity_type='hosting', object_id=7, object_repr='Kore',
        action='deleted',
    )
    log = make_log('accounting_change', {
        'change_log_id': change_log.id,
        'entity_type': 'hosting',
        'action': 'deleted',
    })

    run_backfill()

    assert targets_of(log) == [('hosting', 7)]
    log.refresh_from_db()
    # Which is what the "Eliminaciones" preset cuts on.
    assert log.origin_action == 'deleted'
    assert EmailLogTarget.objects.get(email_log=log).object_repr == 'Kore'


def test_a_cuenta_de_cobro_recovers_all_three_of_its_links():
    log = make_log('collection_account_sent', {
        'document_id': 3,
        'public_number': 'PA-KORE-001',
        'hosting_id': 4,
        'income_record_id': 9,
    })

    run_backfill()

    assert targets_of(log) == [
        ('collection_account', 3), ('hosting', 4), ('income', 9),
    ]


def test_a_digest_recovers_every_record_it_named():
    log = make_log('accounting_payment_calendar', {
        'date': '2026-08-15',
        'incomes': [{'id': 1, 'title': 'Kore anual'}, {'id': 2, 'title': 'Otro'}],
        'recurring': [{'id': 5, 'title': 'Figma'}],
        'hostings': [{'id': 8, 'title': 'kore.co'}],
    })

    run_backfill()

    assert targets_of(log) == [
        ('hosting', 8), ('income', 1), ('income', 2), ('recurring', 5),
    ]


def test_the_statement_reminder_resolves_its_cards_by_name():
    """That notice stored names, not ids — the catalog closes the gap."""
    card = CreditCard.objects.create(
        name='Visa Bancolombia', credit_limit=Decimal('5000000.00'),
    )
    log = make_log('accounting_statement_reminder', {
        'period': '2026-07-01',
        'pending': [
            {'card_name': 'Visa Bancolombia', 'reason': 'Sin extracto'},
            {'card_name': 'Tarjeta que ya no existe', 'reason': 'Sin extracto'},
        ],
    })

    run_backfill()

    assert targets_of(log) == [('credit_card', card.id)]


def test_a_payment_notice_recovers_its_payment():
    log = make_log('payment_status_team', {
        'payment_id': 12, 'to_status': 'paid', 'source': 'wompi',
    })

    run_backfill()

    assert targets_of(log) == [('payment', 12)]


def test_the_card_reminder_is_left_alone_because_it_stored_no_id():
    """Not a gap to paper over: inventing links would be worse than none."""
    log = make_log('accounting_card_reminder', {
        'cycle_friday': '2026-08-14', 'reminder_number': 2,
    })

    run_backfill()

    assert targets_of(log) == []


def test_traffic_from_outside_the_module_is_not_touched():
    log = make_log('proposal_sent', {'proposal_id': 4})

    run_backfill()

    assert targets_of(log) == []


def test_running_it_twice_does_not_duplicate_the_links():
    log = make_log('payment_status_team', {'payment_id': 12})

    run_backfill()
    run_backfill()

    assert EmailLogTarget.objects.filter(email_log=log).count() == 1


def test_a_row_whose_change_log_is_gone_is_skipped_not_crashed():
    log = make_log('accounting_change', {'change_log_id': 9999})

    run_backfill()

    assert targets_of(log) == []
    log.refresh_from_db()
    assert log.origin_action == ''
