"""Turn the flat recipients JSON list into an administrable catalog.

``AccountingSettings.notification_recipients`` was a JSONField of plain
strings: no per-recipient state, no fecha de alta, no way to pause one
address without deleting it. This creates ``NotificationRecipient`` (one
row per address), moves whatever the singleton held into it, seeds the two
inboxes the module must reach, and drops the old field so there is a single
source of truth for who gets the module's automated email.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

# Inboxes that must be registered after this migration, per requirement.
SEEDED_EMAILS = ('team@projectapp.co', 'carlos18bp@gmail.com')

SOURCE_REF = 'migration:0191'


def move_recipients_to_catalog(apps, schema_editor):
    """Copy the singleton's list into the catalog, then seed the two inboxes."""
    AccountingSettings = apps.get_model('content', 'AccountingSettings')
    NotificationRecipient = apps.get_model('content', 'NotificationRecipient')

    existing = AccountingSettings.objects.filter(pk=1).first()
    stored = list(getattr(existing, 'notification_recipients', None) or [])

    seen = set()
    for raw in [*stored, *SEEDED_EMAILS]:
        email = str(raw or '').strip().lower()
        if not email or email in seen:
            continue
        seen.add(email)
        NotificationRecipient.objects.get_or_create(
            email=email,
            defaults={'is_active': True, 'source_ref': SOURCE_REF},
        )


def move_recipients_back(apps, schema_editor):
    """Write the active addresses back into the singleton's JSON list."""
    AccountingSettings = apps.get_model('content', 'AccountingSettings')
    NotificationRecipient = apps.get_model('content', 'NotificationRecipient')

    emails = list(
        NotificationRecipient.objects.filter(is_active=True)
        .order_by('email')
        .values_list('email', flat=True)
    )
    AccountingSettings.objects.filter(pk=1).update(notification_recipients=emails)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0190_hostingrecord_ordering_by_project'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationRecipient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True, default='')),
                ('source_ref', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notification Recipient',
                'verbose_name_plural': 'Notification Recipients',
                'ordering': ['email'],
            },
        ),
        # 'notification_recipient' is 22 chars — the column has to grow.
        migrations.AlterField(
            model_name='accountingchangelog',
            name='entity_type',
            field=models.CharField(choices=[('income', 'Ingreso'), ('expense', 'Gasto'), ('hosting', 'Hosting'), ('pocket', 'Bolsillo'), ('recurring', 'Pago recurrente'), ('ads', 'Ads'), ('card_snapshot', 'Saldo tarjeta'), ('credit_card', 'Tarjeta de crédito'), ('statement', 'Extracto de tarjeta'), ('statement_tx', 'Transacción de extracto'), ('merchant_alias', 'Alias de comercio'), ('notification_recipient', 'Destinatario de notificación'), ('settings', 'Configuración')], max_length=30),
        ),
        migrations.RunPython(move_recipients_to_catalog, move_recipients_back),
        migrations.RemoveField(
            model_name='accountingsettings',
            name='notification_recipients',
        ),
    ]
