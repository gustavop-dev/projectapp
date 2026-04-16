"""Remap WebAppDiagnostic.status to the shared BusinessProposal vocabulary.

Mapping:
    initial_sent → sent
    in_analysis  → negotiating
    final_sent   → sent   (distinguished from the initial send by
                           the presence of `final_sent_at`)
    draft, accepted, rejected — unchanged

The forward operation uses bulk `.update()` so the rows sidestep enum
validation while in flight. The reverse operation restores the old values
by inspecting `final_sent_at` so the data round-trips cleanly.
"""

from django.db import migrations, models


OLD_CHOICES = [
    ('draft', 'Draft'),
    ('initial_sent', 'Initial sent'),
    ('in_analysis', 'In analysis'),
    ('final_sent', 'Final sent'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
]

NEW_CHOICES = [
    ('draft', 'Draft'),
    ('sent', 'Sent'),
    ('viewed', 'Viewed'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
    ('negotiating', 'Negotiating'),
    ('expired', 'Expired'),
    ('finished', 'Finished'),
]


def forward(apps, schema_editor):
    WebAppDiagnostic = apps.get_model('content', 'WebAppDiagnostic')
    WebAppDiagnostic.objects.filter(
        status__in=('initial_sent', 'final_sent'),
    ).update(status='sent')
    WebAppDiagnostic.objects.filter(status='in_analysis').update(status='negotiating')


def reverse(apps, schema_editor):
    WebAppDiagnostic = apps.get_model('content', 'WebAppDiagnostic')
    WebAppDiagnostic.objects.filter(status='negotiating').update(status='in_analysis')
    WebAppDiagnostic.objects.filter(
        status='sent', final_sent_at__isnull=False,
    ).update(status='final_sent')
    WebAppDiagnostic.objects.filter(
        status='sent', final_sent_at__isnull=True,
    ).update(status='initial_sent')
    WebAppDiagnostic.objects.filter(
        status__in=('viewed', 'expired', 'finished'),
    ).update(status='draft')


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0090_web_app_diagnostic'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
        migrations.AlterField(
            model_name='webappdiagnostic',
            name='status',
            field=models.CharField(
                choices=NEW_CHOICES,
                default='draft',
                max_length=20,
            ),
        ),
    ]
