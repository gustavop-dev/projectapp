# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_deliverable_client_folder_and_upload'),
        ('content', '0057_businessproposal_platform_onboarding_completed_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='deliverable',
            field=models.ForeignKey(
                blank=True,
                help_text='Optional scope: show this document under a specific deliverable.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='documents',
                to='accounts.deliverable',
            ),
        ),
    ]
