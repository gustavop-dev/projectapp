# Generated manually for platform onboarding idempotency

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0056_businessproposal_deliverable'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessproposal',
            name='platform_onboarding_completed_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Set when acceptance onboarding (sync + welcome email) completed; prevents duplicate runs.',
                null=True,
            ),
        ),
    ]
