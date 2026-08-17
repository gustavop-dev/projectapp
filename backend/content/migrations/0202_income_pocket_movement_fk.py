"""Income → pocket movement goes from OneToOne to ForeignKey.

An abono (one client payment covering several expected incomes) books ONE
pocket movement and N liquid children sharing it — the child row IS the
per-income allocation, so the unique constraint behind the OneToOne has to
go. Existing rows are untouched: every current link is a valid FK row.

MySQL note: dropping the unique index that backs a FK makes InnoDB rebuild
the plain index under the FK — Django emits the drop/re-add dance itself,
but run this on staging MySQL before production (dev SQLite won't catch an
index-dependency error).
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0201_document_audit_entity_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incomerecord',
            name='pocket_movement',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='income_records',
                to='content.pocketmovement',
            ),
        ),
    ]
