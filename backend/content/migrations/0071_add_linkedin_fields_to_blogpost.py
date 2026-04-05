from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0070_add_email_sent_change_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='linkedin_summary_es',
            field=models.TextField(
                blank=True, default='',
                help_text='Resumen para publicar en LinkedIn (español). Máximo ~1300 caracteres.',
            ),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='linkedin_summary_en',
            field=models.TextField(
                blank=True, default='',
                help_text='Summary for LinkedIn post (English). Max ~1300 characters.',
            ),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='linkedin_post_id',
            field=models.CharField(
                blank=True, default='', max_length=255,
                help_text='LinkedIn post URN after successful publication.',
            ),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='linkedin_published_at',
            field=models.DateTimeField(
                blank=True, null=True,
                help_text='Timestamp of last successful LinkedIn publication.',
            ),
        ),
    ]
