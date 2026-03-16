from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0046_add_post_rejection_revisit_alert_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessproposal',
            name='hosting_discount_semiannual',
            field=models.PositiveIntegerField(
                default=20,
                help_text='Default discount % for semiannual (6-month) hosting payments.',
            ),
        ),
        migrations.AddField(
            model_name='businessproposal',
            name='hosting_discount_quarterly',
            field=models.PositiveIntegerField(
                default=10,
                help_text='Default discount % for quarterly (3-month) hosting payments.',
            ),
        ),
    ]
