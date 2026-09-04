from collections import defaultdict

from django.db import migrations, models


def backfill_recipient_headers(apps, schema_editor):
    EmailLog = apps.get_model('content', 'EmailLog')
    EmailDeliverySnapshot = apps.get_model('content', 'EmailDeliverySnapshot')

    EmailLog.objects.filter(delivery_role='copy').update(recipient_kind='bcc')

    recipients_by_delivery = defaultdict(list)
    primary_rows = (
        EmailLog.objects.filter(
            delivery_id__isnull=False,
            delivery_role='primary',
        )
        .order_by('sent_at', 'id')
        .values_list('delivery_id', 'recipient')
    )
    for delivery_id, recipient in primary_rows.iterator(chunk_size=1000):
        recipients_by_delivery[delivery_id].append(recipient)

    pending = []
    snapshots = EmailDeliverySnapshot.objects.only('id', 'delivery_id')
    for snapshot in snapshots.iterator(chunk_size=500):
        snapshot.to_recipients = recipients_by_delivery.get(
            snapshot.delivery_id, [],
        )
        snapshot.cc_recipients = []
        pending.append(snapshot)
        if len(pending) == 500:
            EmailDeliverySnapshot.objects.bulk_update(
                pending,
                ['to_recipients', 'cc_recipients'],
                batch_size=500,
            )
            pending = []
    if pending:
        EmailDeliverySnapshot.objects.bulk_update(
            pending,
            ['to_recipients', 'cc_recipients'],
            batch_size=500,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0245_merge_income_receivables_financing_policy'),
    ]

    operations = [
        migrations.AddField(
            model_name='emaillog',
            name='recipient_kind',
            field=models.CharField(
                choices=[
                    ('to', 'Para'),
                    ('cc', 'Copia visible'),
                    ('bcc', 'Copia oculta'),
                ],
                default='to',
                max_length=3,
            ),
        ),
        migrations.AddField(
            model_name='emaildeliverysnapshot',
            name='to_recipients',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='emaildeliverysnapshot',
            name='cc_recipients',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(backfill_recipient_headers, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(
                fields=['delivery_id', 'recipient_kind'],
                name='emaillog_delivery_kind',
            ),
        ),
    ]
