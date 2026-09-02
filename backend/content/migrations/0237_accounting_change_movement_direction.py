from django.db import migrations, models


def backfill_pocket_movement_direction(apps, schema_editor):
    AccountingChangeLog = apps.get_model('content', 'AccountingChangeLog')
    direction_map = {
        'in': 'in',
        'ingreso': 'in',
        'out': 'out',
        'egreso': 'out',
    }
    changed_rows = []

    queryset = AccountingChangeLog.objects.filter(
        entity_type='pocket',
        movement_direction__isnull=True,
    ).only('id', 'action', 'changes', 'movement_direction')
    for log in queryset.iterator(chunk_size=500):
        for change in log.changes or []:
            if change.get('field') != 'direction':
                continue
            value = (
                change.get('old')
                if log.action == 'deleted'
                else change.get('new') or change.get('old')
            )
            direction = direction_map.get(str(value or '').strip().lower())
            if direction:
                log.movement_direction = direction
                changed_rows.append(log)
            break

    if changed_rows:
        AccountingChangeLog.objects.bulk_update(
            changed_rows,
            ['movement_direction'],
            batch_size=500,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0236_document_threads'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountingchangelog',
            name='movement_direction',
            field=models.CharField(
                blank=True,
                choices=[('in', 'Ingreso'), ('out', 'Egreso')],
                max_length=3,
                null=True,
            ),
        ),
        migrations.RunPython(
            backfill_pocket_movement_direction,
            migrations.RunPython.noop,
        ),
    ]
