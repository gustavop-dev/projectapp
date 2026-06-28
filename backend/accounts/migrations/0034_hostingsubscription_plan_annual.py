from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0033_merge_20260520_1754'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hostingsubscription',
            name='plan',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('monthly', 'Mensual'),
                    ('quarterly', 'Trimestral'),
                    ('semiannual', 'Semestral'),
                    ('annual', 'Anual'),
                ],
                default='monthly',
            ),
        ),
    ]
