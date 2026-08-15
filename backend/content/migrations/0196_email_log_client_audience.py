"""Give the send log the two columns that attribute it to a client.

Columns only: the composite index ships in ``0198``, after the backfill has
finished rewriting every row, so MySQL does not maintain it through the
UPDATEs. Both AddFields are ALGORITHM=INSTANT on MySQL 8.0.12+.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0049_drop_client_status_tabs'),
        ('content', '0195_incomerecord_period_cadence_incomerecord_period_end_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='emaillog',
            name='audience',
            field=models.CharField(choices=[('client', 'Al cliente'), ('internal', 'Interno')], default='internal', max_length=10),
        ),
        migrations.AddField(
            model_name='emaillog',
            name='client',
            field=models.ForeignKey(blank=True, db_index=False, limit_choices_to={'role': 'client'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='email_logs', to='accounts.userprofile'),
        ),
    ]
