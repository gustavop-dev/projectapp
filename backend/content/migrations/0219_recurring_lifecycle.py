from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0218_project_state_help'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurringpayment',
            name='archived_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recurringpayment',
            name='is_archived',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='recurringpayment',
            name='reminders_muted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='recurringpayment',
            name='reminders_muted_until',
            field=models.DateField(blank=True, null=True),
        ),
    ]
