"""Backfill: one consolidated cycle per hosting carrying its pre-history
total_paid/cycles_count, so history becomes the source of truth without
losing the imported figures."""
from django.db import migrations

BACKFILL_REF = 'backfill:hosting-cycles'


def create_consolidated_cycles(apps, schema_editor):
    HostingRecord = apps.get_model('content', 'HostingRecord')
    HostingCycle = apps.get_model('content', 'HostingCycle')

    for hosting in HostingRecord.objects.filter(total_paid__gt=0):
        if hosting.cycles.exists():
            continue
        HostingCycle.objects.create(
            hosting_record=hosting,
            modality=hosting.payment_modality,
            amount=hosting.total_paid,
            paid_at=hosting.valid_from or hosting.created_at.date(),
            period_from=hosting.valid_from,
            period_to=hosting.valid_to,
            cycles_represented=max(hosting.cycles_count, 1),
            notes='Ciclo histórico consolidado (migración 0150)',
            source_ref=BACKFILL_REF,
        )


def remove_consolidated_cycles(apps, schema_editor):
    HostingCycle = apps.get_model('content', 'HostingCycle')
    HostingCycle.objects.filter(source_ref=BACKFILL_REF).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0149_hostingcycle'),
    ]

    operations = [
        migrations.RunPython(
            create_consolidated_cycles, remove_consolidated_cycles,
        ),
    ]
