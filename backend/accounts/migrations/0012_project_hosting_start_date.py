from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_project_payment_milestones_hosting_tiers'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='hosting_start_date',
            field=models.DateField(
                blank=True,
                help_text='Date when hosting billing should begin (set by admin).',
                null=True,
            ),
        ),
    ]
