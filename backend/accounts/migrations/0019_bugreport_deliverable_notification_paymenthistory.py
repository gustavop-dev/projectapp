# Generated manually — BugReport.project → deliverable; Notification.deliverable; PaymentHistory

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def _backfill_bug_deliverables(apps, schema_editor):
    BugReport = apps.get_model('accounts', 'BugReport')
    Deliverable = apps.get_model('accounts', 'Deliverable')
    Project = apps.get_model('accounts', 'Project')
    for bug in BugReport.objects.all().iterator():
        pid = bug.project_id
        d = Deliverable.objects.filter(project_id=pid).order_by('id').first()
        if d is None:
            proj = Project.objects.get(pk=pid)
            d = Deliverable.objects.create(
                project_id=pid,
                uploaded_by_id=proj.client_id,
                title='General',
                description='Auto-created for existing bug reports without deliverables.',
                category='other',
                current_version=0,
            )
        bug.deliverable_id = d.pk
        bug.save(update_fields=['deliverable_id'])


def _noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0018_deliverable_client_folder_and_upload'),
    ]

    operations = [
        migrations.AddField(
            model_name='bugreport',
            name='deliverable',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='bug_reports',
                to='accounts.deliverable',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='deliverable',
            field=models.ForeignKey(
                blank=True,
                help_text='Deliverable context for deep-linking when applicable.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='notifications',
                to='accounts.deliverable',
            ),
        ),
        migrations.CreateModel(
            name='PaymentHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_status', models.CharField(choices=[
                    ('pending', 'Pendiente'),
                    ('processing', 'Procesando'),
                    ('paid', 'Pagado'),
                    ('failed', 'Fallido'),
                    ('overdue', 'Vencido'),
                ], max_length=20)),
                ('to_status', models.CharField(choices=[
                    ('pending', 'Pendiente'),
                    ('processing', 'Procesando'),
                    ('paid', 'Pagado'),
                    ('failed', 'Fallido'),
                    ('overdue', 'Vencido'),
                ], max_length=20)),
                ('source', models.CharField(
                    blank=True,
                    choices=[
                        ('api', 'API'),
                        ('wompi_link', 'Wompi payment link'),
                        ('webhook', 'Wompi webhook'),
                        ('wompi_verify', 'Wompi verify'),
                        ('system', 'System'),
                    ],
                    default='',
                    max_length=32,
                )),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'payment',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='history',
                        to='accounts.payment',
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='paymenthistory',
            index=models.Index(fields=['payment', '-created_at'], name='accounts_pa_payment_6e1c8e_idx'),
        ),
        migrations.RunPython(_backfill_bug_deliverables, _noop_reverse),
        migrations.RemoveField(
            model_name='bugreport',
            name='project',
        ),
        migrations.AlterField(
            model_name='bugreport',
            name='deliverable',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='bug_reports',
                to='accounts.deliverable',
            ),
        ),
    ]
