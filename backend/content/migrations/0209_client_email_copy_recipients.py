import content.models.client_email_copy_recipient
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0208_recalculate_recurring_cop_equivalent'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientEmailCopyRecipient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('families', models.JSONField(default=content.models.client_email_copy_recipient.default_client_email_families)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Client Email Copy Recipient',
                'verbose_name_plural': 'Client Email Copy Recipients',
                'ordering': ['email'],
            },
        ),
        migrations.AddField(
            model_name='emaillog',
            name='delivery_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='emaillog',
            name='delivery_role',
            field=models.CharField(choices=[('primary', 'Envío principal'), ('copy', 'Copia interna')], default='primary', max_length=10),
        ),
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(fields=['delivery_id', 'delivery_role'], name='emaillog_delivery_role'),
        ),
    ]
