import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0121_update_contracttemplate_help_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentfolder',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='children',
                to='content.documentfolder',
            ),
        ),
    ]
