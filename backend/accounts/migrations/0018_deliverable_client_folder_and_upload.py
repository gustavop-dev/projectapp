# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0017_requirement_deliverable_and_trace_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliverableClientFolder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='deliverable_client_folders',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'deliverable',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='client_folders',
                        to='accounts.deliverable',
                    ),
                ),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='DeliverableClientUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='deliverables/client_uploads/')),
                ('title', models.CharField(blank=True, default='', max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'deliverable',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='client_uploads',
                        to='accounts.deliverable',
                    ),
                ),
                (
                    'folder',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='uploads',
                        to='accounts.deliverableclientfolder',
                    ),
                ),
                (
                    'uploaded_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='deliverable_client_uploads',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
