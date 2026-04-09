# Generated 2026-04-09 — add 'finished' to BusinessProposal.status choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0077_update_default_contract_template_v3'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessproposal',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('sent', 'Sent'),
                    ('viewed', 'Viewed'),
                    ('accepted', 'Accepted'),
                    ('rejected', 'Rejected'),
                    ('negotiating', 'Negotiating'),
                    ('expired', 'Expired'),
                    ('finished', 'Finished'),
                ],
                default='draft',
                max_length=20,
            ),
        ),
    ]
