from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0033_alter_proposalalert_alert_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessproposal',
            name='automations_paused',
            field=models.BooleanField(
                default=False,
                help_text='When true, no automatic emails (reminder, urgency, inactivity) are sent for this proposal.',
            ),
        ),
    ]
