from django.db import migrations


CARLOS_EMAIL = 'carlos18bp@gmail.com'
ALL_EMAIL_FAMILIES = [
    'proposals',
    'diagnostics',
    'documents_communications',
    'collections',
    'accounting',
    'platform',
    'tasks_operations',
    'security',
]


def enable_carlos_email_copy(apps, schema_editor):
    EmailCopyRecipient = apps.get_model('content', 'EmailCopyRecipient')
    EmailCopyRecipient.objects.update_or_create(
        email=CARLOS_EMAIL,
        defaults={
            'is_active': True,
            'families': list(ALL_EMAIL_FAMILIES),
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0224_emailattachmentsnapshot_source_document_set_null'),
    ]

    operations = [
        migrations.RunPython(
            enable_carlos_email_copy,
            migrations.RunPython.noop,
        ),
    ]
