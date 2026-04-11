from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0074_increase_change_type_max_length_add_seller_inactivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposaldefaultconfig',
            name='expiration_days',
            field=models.PositiveIntegerField(
                default=21,
                help_text='Default proposal expiration period in days.',
            ),
        ),
    ]
