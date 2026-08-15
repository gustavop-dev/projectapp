"""Backfill the send log's record links from the metadata already stored.

Every accounting notice has always written the ids of what it was about into
``EmailLog.metadata`` — a free-form dict nobody could query. The six shapes
are known, so the history can start out useful instead of only learning about
sends made after this deploy.

Two of them cannot be recovered: the card-debt reminder never stored a card
id (it quoted snapshots by name), and the statement reminder stored card
names, which are resolved back to the catalog here. Rows whose referenced
record is gone are simply skipped — a link to a deleted id would show an
empty row in the panel.
"""

from django.db import migrations

CHUNK = 500

ACCOUNTING_TEMPLATE_KEYS = (
    'accounting_change',
    'accounting_card_reminder',
    'accounting_statement_reminder',
    'accounting_payment_calendar',
    'collection_account_sent',
    'payment_status_team',
)


def _digest_targets(metadata):
    """Payment calendar: three sections, each naming its records by id."""
    pairs = []
    for key, entity_type in (
        ('incomes', 'income'),
        ('recurring', 'recurring'),
        ('hostings', 'hosting'),
    ):
        for item in metadata.get(key) or ():
            if isinstance(item, dict) and item.get('id'):
                pairs.append((entity_type, item['id'], item.get('title') or ''))
    return pairs


def forwards(apps, schema_editor):
    EmailLog = apps.get_model('content', 'EmailLog')
    EmailLogTarget = apps.get_model('content', 'EmailLogTarget')
    AccountingChangeLog = apps.get_model('content', 'AccountingChangeLog')
    CreditCard = apps.get_model('content', 'CreditCard')

    change_logs = {
        row.id: row
        for row in AccountingChangeLog.objects.all().only(
            'id', 'entity_type', 'object_id', 'object_repr', 'action',
        )
    }
    cards_by_name = {
        row.name: row.id for row in CreditCard.objects.all().only('id', 'name')
    }

    pending_targets = []
    pending_actions = []

    queryset = EmailLog.objects.filter(
        template_key__in=ACCOUNTING_TEMPLATE_KEYS,
    ).only('id', 'template_key', 'metadata', 'origin_action')

    for log in queryset.iterator(chunk_size=CHUNK):
        metadata = log.metadata if isinstance(log.metadata, dict) else {}
        pairs = []

        if log.template_key == 'accounting_change':
            change_log = change_logs.get(metadata.get('change_log_id'))
            if change_log is not None:
                pairs.append((
                    change_log.entity_type,
                    change_log.object_id,
                    change_log.object_repr,
                ))
                if change_log.action and not log.origin_action:
                    log.origin_action = change_log.action
                    pending_actions.append(log)
        elif log.template_key == 'collection_account_sent':
            pairs = [
                ('collection_account', metadata.get('document_id'),
                 metadata.get('public_number') or ''),
                ('hosting', metadata.get('hosting_id'), ''),
                ('income', metadata.get('income_record_id'), ''),
            ]
        elif log.template_key == 'accounting_payment_calendar':
            pairs = _digest_targets(metadata)
        elif log.template_key == 'accounting_statement_reminder':
            for item in metadata.get('pending') or ():
                card_id = cards_by_name.get((item or {}).get('card_name'))
                if card_id:
                    pairs.append(('credit_card', card_id, item['card_name']))
        elif log.template_key == 'payment_status_team':
            pairs = [('payment', metadata.get('payment_id'), '')]

        seen = set()
        for entity_type, object_id, object_repr in pairs:
            if not entity_type or not object_id:
                continue
            key = (entity_type, int(object_id))
            if key in seen:
                continue
            seen.add(key)
            pending_targets.append(EmailLogTarget(
                email_log_id=log.id,
                entity_type=entity_type,
                object_id=int(object_id),
                object_repr=str(object_repr)[:255],
            ))

        if len(pending_targets) >= CHUNK:
            EmailLogTarget.objects.bulk_create(
                pending_targets, ignore_conflicts=True,
            )
            pending_targets = []
        if len(pending_actions) >= CHUNK:
            EmailLog.objects.bulk_update(pending_actions, ['origin_action'])
            pending_actions = []

    if pending_targets:
        EmailLogTarget.objects.bulk_create(
            pending_targets, ignore_conflicts=True,
        )
    if pending_actions:
        EmailLog.objects.bulk_update(pending_actions, ['origin_action'])


def backwards(apps, schema_editor):
    """Drop what forwards() derived; the source metadata is untouched."""
    EmailLogTarget = apps.get_model('content', 'EmailLogTarget')
    EmailLog = apps.get_model('content', 'EmailLog')
    EmailLogTarget.objects.filter(
        email_log__template_key__in=ACCOUNTING_TEMPLATE_KEYS,
    ).delete()
    EmailLog.objects.filter(
        template_key='accounting_change',
    ).update(origin_action='')


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0193_email_log_targets_and_body'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
