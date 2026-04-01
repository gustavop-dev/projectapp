# Generated manually — BusinessProposal belongs to platform Deliverable

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_deliverable_optional_file_epic_meta_and_file_model'),
        ('content', '0055_add_technical_view_mode_choice'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessproposal',
            name='deliverable',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='business_proposal',
                to='accounts.deliverable',
            ),
        ),
    ]
