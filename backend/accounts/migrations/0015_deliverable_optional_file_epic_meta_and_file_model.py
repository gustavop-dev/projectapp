# Generated manually for platform deliverable hierarchy

from django.conf import settings
from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0014_theme_customization_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deliverable',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='deliverables/'),
        ),
        migrations.AddField(
            model_name='deliverable',
            name='source_epic_key',
            field=models.CharField(blank=True, db_index=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='deliverable',
            name='source_epic_title',
            field=models.CharField(blank=True, default='', max_length=300),
        ),
        migrations.AlterField(
            model_name='deliverable',
            name='category',
            field=models.CharField(
                choices=[
                    ('designs', 'Diseños'),
                    ('credentials', 'Credenciales'),
                    ('documents', 'Documentos'),
                    ('apks', 'APKs / Builds'),
                    ('contract', 'Contrato'),
                    ('amendment', 'Otrosí'),
                    ('legal_annex', 'Anexo legal'),
                    ('other', 'Otros'),
                ],
                default='other',
                max_length=20,
            ),
        ),
        migrations.AddConstraint(
            model_name='deliverable',
            constraint=models.UniqueConstraint(
                condition=~Q(source_epic_key=''),
                fields=('project', 'source_epic_key'),
                name='uniq_deliverable_project_epic_key',
            ),
        ),
        migrations.CreateModel(
            name='DeliverableFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='deliverables/attachments/')),
                ('title', models.CharField(blank=True, default='', max_length=300)),
                (
                    'category',
                    models.CharField(
                        choices=[
                            ('designs', 'Diseños'),
                            ('credentials', 'Credenciales'),
                            ('documents', 'Documentos'),
                            ('apks', 'APKs / Builds'),
                            ('contract', 'Contrato'),
                            ('amendment', 'Otrosí'),
                            ('legal_annex', 'Anexo legal'),
                            ('other', 'Otros'),
                        ],
                        default='other',
                        max_length=20,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'deliverable',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='attachment_files',
                        to='accounts.deliverable',
                    ),
                ),
                (
                    'uploaded_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='deliverable_attachment_files',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
