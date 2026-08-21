from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0206_proposal_intro_emphasis'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='client_custom_notes',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
