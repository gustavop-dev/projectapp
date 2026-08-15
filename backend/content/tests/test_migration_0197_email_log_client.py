"""The one-shot backfill that files the existing send log under its clients.

`EmailLog.client` is new; the history is not. The migration recovers the
owner from the proposal, from the record the accounting notice was about,
and from the payment behind a hosting notice — and deliberately leaves the
digests unattributed. It runs once in production, so its logic is exercised
here rather than trusted.
"""
from decimal import Decimal
from importlib import import_module

import pytest
from django.apps import apps

from content.models import BusinessProposal, EmailLog, EmailLogTarget

pytestmark = pytest.mark.django_db

migration = import_module(
    'content.migrations.0197_backfill_email_log_client',
)


def run_backfill():
    migration.forwards(apps, None)


def make_log(template_key, **kwargs):
    return EmailLog.objects.create(
        template_key=template_key,
        recipient='ana@test.com',
        subject='Aviso',
        status=EmailLog.Status.SENT,
        **kwargs,
    )


def link(log, entity_type, object_id):
    EmailLogTarget.objects.create(
        email_log=log, entity_type=entity_type, object_id=object_id,
        object_repr='',
    )


def test_a_proposal_send_is_filed_under_the_proposals_client(
    make_client_profile, proposal,
):
    client = make_client_profile()
    BusinessProposal.objects.filter(pk=proposal.pk).update(client=client)
    log = make_log('proposal_sent_client', proposal=proposal)

    run_backfill()

    log.refresh_from_db()
    assert log.client_id == client.id
    assert log.audience == EmailLog.Audience.CLIENT


def test_a_change_notice_is_filed_under_the_client_of_its_income(
    make_client_profile, make_income,
):
    client = make_client_profile()
    income = make_income(client=client)
    log = make_log('accounting_change')
    link(log, 'income', income.id)

    run_backfill()

    log.refresh_from_db()
    assert log.client_id == client.id
    # It reached the team, not the client: it counts as their trail, not as
    # contact with them.
    assert log.audience == EmailLog.Audience.INTERNAL


def test_a_digest_naming_a_clients_income_stays_unattributed(
    make_client_profile, make_income,
):
    """The cut this migration exists to get right.

    The payment calendar carries income targets like a change notice does,
    so a target-driven pass without the template scope would file a digest
    covering six clients under whichever one it listed first.
    """
    client = make_client_profile()
    income = make_income(client=client)
    log = make_log('accounting_payment_calendar')
    link(log, 'income', income.id)

    run_backfill()

    log.refresh_from_db()
    assert log.client_id is None
    assert log.audience == EmailLog.Audience.INTERNAL


def test_a_target_pointing_at_a_deleted_record_leaves_the_row_unattributed(
    make_client_profile, make_income,
):
    client = make_client_profile()
    income = make_income(client=client)
    income_id = income.id
    income.delete()
    log = make_log('accounting_change')
    link(log, 'income', income_id)

    run_backfill()

    log.refresh_from_db()
    assert log.client_id is None


def test_an_income_without_a_client_leaves_the_row_unattributed(make_income):
    income = make_income(client=None)
    log = make_log('accounting_change')
    link(log, 'income', income.id)

    run_backfill()

    log.refresh_from_db()
    assert log.client_id is None


def test_the_cuenta_de_cobro_is_the_accounting_notice_that_counts_as_contact():
    log = make_log('collection_account_sent')

    run_backfill()

    log.refresh_from_db()
    assert log.audience == EmailLog.Audience.CLIENT


def test_backwards_drops_only_what_forwards_derived(
    make_client_profile, proposal,
):
    client = make_client_profile()
    BusinessProposal.objects.filter(pk=proposal.pk).update(client=client)
    log = make_log('proposal_sent_client', proposal=proposal)
    run_backfill()

    migration.backwards(apps, None)

    log.refresh_from_db()
    assert log.client_id is None
    assert log.audience == EmailLog.Audience.INTERNAL
    # The proposal link it was derived from is untouched.
    assert log.proposal_id == proposal.id
