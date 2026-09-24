from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('content', '0254_linktree_assets')]

    operations = [
        migrations.AddField(
            model_name='proposaldocument',
            name='content_markdown',
            field=models.TextField(blank=True, default='', help_text='Internal snapshot of the text used to generate the stored contract PDF.'),
        ),
    ]
