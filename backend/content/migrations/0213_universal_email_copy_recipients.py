import content.models.email_copy_recipient
from django.db import migrations, models


LEGACY_ALL = {
    'proposals',
    'diagnostics',
    'documents_manual',
    'collections',
    'platform',
}

EXPANDED_ALL = [
    'proposals',
    'diagnostics',
    'documents_communications',
    'collections',
    'accounting',
    'platform',
    'tasks_operations',
    'security',
]


def expand_legacy_families(apps, schema_editor):
    Recipient = apps.get_model('content', 'EmailCopyRecipient')
    for recipient in Recipient.objects.all().iterator():
        selected = set(recipient.families or [])
        if selected == LEGACY_ALL:
            recipient.families = list(EXPANDED_ALL)
        else:
            recipient.families = [
                'documents_communications' if family == 'documents_manual'
                else family
                for family in recipient.families or []
            ]
        recipient.save(update_fields=['families'])


def restore_legacy_families(apps, schema_editor):
    Recipient = apps.get_model('content', 'EmailCopyRecipient')
    for recipient in Recipient.objects.all().iterator():
        selected = set(recipient.families or [])
        legacy = []
        for family in (
            'proposals', 'diagnostics', 'documents_communications',
            'collections', 'platform',
        ):
            if family not in selected:
                continue
            legacy.append(
                'documents_manual'
                if family == 'documents_communications' else family
            )
        recipient.families = legacy
        recipient.save(update_fields=['families'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0212_seed_communications_mcp'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ClientEmailCopyRecipient',
            new_name='EmailCopyRecipient',
        ),
        migrations.AlterModelOptions(
            name='emailcopyrecipient',
            options={
                'ordering': ['email'],
                'verbose_name': 'Email Copy Recipient',
                'verbose_name_plural': 'Email Copy Recipients',
            },
        ),
        migrations.AlterField(
            model_name='emailcopyrecipient',
            name='families',
            field=models.JSONField(
                default=content.models.email_copy_recipient.default_email_copy_families,
            ),
        ),
        migrations.RunPython(
            expand_legacy_families,
            restore_legacy_families,
        ),
        migrations.AlterField(
            model_name='emaillog',
            name='audience',
            field=models.CharField(
                choices=[
                    ('client', 'Al cliente'),
                    ('internal', 'Interno'),
                    ('security', 'Seguridad'),
                ],
                default='internal',
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='emaillog',
            name='status',
            field=models.CharField(
                choices=[
                    ('sent', 'Sent'),
                    ('delivered', 'Delivered'),
                    ('bounced', 'Bounced'),
                    ('failed', 'Failed'),
                    ('skipped', 'Omitida'),
                ],
                default='sent',
                max_length=20,
            ),
        ),
    ]
