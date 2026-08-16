"""Attribute the send log's existing rows to a client.

The columns are new; the history is not. Proposal rows already name their
client through the proposal, and the accounting ones name a record that
does — the same three mappings ``_client_target_q`` resolves at query time,
inlined here because a migration cannot call a service. The hosting payment
notice resolves through its payment, which that query-time mapping never
learned to read.

The three digests stay NULL on purpose: each covers several clients at
once, so filing it under whichever record happened to come first would be a
lie the clients list would then count.
"""

from django.db import migrations
from django.db.models import OuterRef, Subquery

CHUNK = 500

# Notices whose recipient was the client's own address. Mirrors
# ``proposal_email_service.CLIENT_FACING_TEMPLATE_KEYS`` plus the cuenta de
# cobro; the composed ones are absent because their audience depends on the
# address the panel typed, which no historical row records.
CLIENT_AUDIENCE_KEYS = (
    'proposal_sent_client',
    'proposal_multi_sent_client',
    'proposal_reminder',
    'proposal_urgency',
    'proposal_urgency_no_discount',
    'proposal_accepted_client',
    'proposal_finished_client',
    'proposal_rejected_client',
    'proposal_reengagement',
    'proposal_abandonment_followup',
    'proposal_investment_interest_followup',
    'proposal_scheduled_followup',
    'proposal_negotiation_confirmation',
    'proposal_documents_sent',
    'magic_link',
    'diagnostic_initial_sent',
    'diagnostic_final_sent',
    'diagnostic_documents_sent',
    'collection_account_sent',
)

# Accounting notices that name a single record. The digests are absent by
# design: the payment calendar also carries income and hosting targets, so a
# target-driven pass without this scope would attribute it to whichever one
# it happened to list first.
SINGLE_RECORD_KEYS = ('accounting_change', 'collection_account_sent')

# entity_type -> (model, path from that model to the client profile id)
TARGET_SOURCES = {
    'income': ('IncomeRecord', 'client_id'),
    'hosting': ('HostingRecord', 'client_id'),
    'collection_account': ('Document', 'client_user__profile__id'),
}


def _assign(EmailLog, client_by_log):
    """Write the resolved owners in batches of one UPDATE ... CASE each."""
    rows = [
        EmailLog(pk=log_id, client_id=client_id)
        for log_id, client_id in client_by_log.items()
        if client_id
    ]
    for start in range(0, len(rows), CHUNK):
        EmailLog.objects.bulk_update(rows[start:start + CHUNK], ['client'])


def forwards(apps, schema_editor):
    EmailLog = apps.get_model('content', 'EmailLog')
    EmailLogTarget = apps.get_model('content', 'EmailLogTarget')
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    Payment = apps.get_model('accounts', 'Payment')

    # 1. Audience. Everything else keeps the column default ('internal').
    EmailLog.objects.filter(
        template_key__in=CLIENT_AUDIENCE_KEYS,
    ).update(audience='client')

    # 2. Proposal rows: the client is one hop away, so the database can do it
    #    in one statement. A joined F() reference would raise — Django only
    #    accepts a correlated subquery in update().
    EmailLog.objects.filter(
        client__isnull=True, proposal__isnull=False,
    ).update(
        client_id=Subquery(
            BusinessProposal.objects
            .filter(pk=OuterRef('proposal_id'))
            .values('client_id')[:1]
        ),
    )

    # 3. Accounting rows, through the record the notice was about.
    for entity_type, (model_name, client_path) in TARGET_SOURCES.items():
        model = apps.get_model('content', model_name)
        pairs = list(
            EmailLogTarget.objects
            .filter(
                entity_type=entity_type,
                email_log__client__isnull=True,
                email_log__template_key__in=SINGLE_RECORD_KEYS,
            )
            .values_list('email_log_id', 'object_id')
        )
        owners = dict(
            model.objects
            .filter(pk__in={object_id for _, object_id in pairs})
            .values_list('pk', client_path)
        )
        _assign(EmailLog, {
            log_id: owners.get(object_id) for log_id, object_id in pairs
        })

    # 4. The hosting payment notice: payment -> subscription -> project ->
    #    client user -> profile. Its own pass because `payment` targets are
    #    exactly what the query-time mapping cannot follow.
    pairs = list(
        EmailLogTarget.objects
        .filter(
            entity_type='payment',
            email_log__client__isnull=True,
            email_log__template_key='payment_status_team',
        )
        .values_list('email_log_id', 'object_id')
    )
    owners = dict(
        Payment.objects
        .filter(pk__in={object_id for _, object_id in pairs})
        .values_list('pk', 'subscription__project__client__profile__id')
    )
    _assign(EmailLog, {
        log_id: owners.get(object_id) for log_id, object_id in pairs
    })


def backwards(apps, schema_editor):
    """Drop what forwards() derived; nothing it read is touched."""
    EmailLog = apps.get_model('content', 'EmailLog')
    EmailLog.objects.update(client=None, audience='internal')


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0196_email_log_client_audience'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
