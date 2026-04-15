from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0087_task'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessproposal',
            name='automations_paused',
            field=models.BooleanField(
                default=True,
                help_text='When true, no automatic emails (reminder, urgency, inactivity) are sent for this proposal.',
            ),
        ),
    ]
