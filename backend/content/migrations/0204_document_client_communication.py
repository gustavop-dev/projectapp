from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0203_hosting_nine_month_terms'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='client_email_body',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='document',
            name='client_email_subject',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='document',
            name='client_whatsapp_message',
            field=models.TextField(blank=True, default=''),
        ),
    ]
