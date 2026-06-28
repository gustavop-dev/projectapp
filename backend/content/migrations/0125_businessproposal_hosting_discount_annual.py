from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0124_hosting_percent_default_80'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessproposal',
            name='hosting_discount_annual',
            field=models.PositiveIntegerField(
                default=40,
                help_text='Default discount % for annual (12-month) hosting payments.',
            ),
        ),
        migrations.AddField(
            model_name='proposaldefaultconfig',
            name='hosting_discount_annual',
            field=models.PositiveSmallIntegerField(default=40),
        ),
    ]

