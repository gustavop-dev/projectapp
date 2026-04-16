import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0093_task_alert'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiagnosticSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section_type', models.CharField(choices=[
                    ('purpose', 'Propósito + Escala de Severidad'),
                    ('radiography', 'Radiografía de la Aplicación'),
                    ('categories', 'Categorías Evaluadas'),
                    ('delivery_structure', 'Estructura de la Entrega'),
                    ('executive_summary', 'Resumen Ejecutivo'),
                    ('cost', 'Costo y Formas de Pago'),
                    ('timeline', 'Cronograma'),
                    ('scope', 'Alcance y Consideraciones'),
                ], max_length=30)),
                ('title', models.CharField(max_length=255)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_enabled', models.BooleanField(default=True)),
                ('content_json', models.JSONField(blank=True, default=dict)),
                ('visibility', models.CharField(choices=[
                    ('initial', 'Sólo envío inicial'),
                    ('final', 'Sólo envío final'),
                    ('both', 'Ambos envíos'),
                ], default='both', max_length=10)),
                ('diagnostic', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sections',
                    to='content.webappdiagnostic',
                )),
            ],
            options={
                'verbose_name': 'Diagnostic Section',
                'verbose_name_plural': 'Diagnostic Sections',
                'ordering': ['order'],
                'unique_together': {('diagnostic', 'section_type')},
            },
        ),
        migrations.CreateModel(
            name='DiagnosticChangeLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_type', models.CharField(choices=[
                    ('created', 'Created'),
                    ('updated', 'Updated'),
                    ('section_updated', 'Section Updated'),
                    ('sent', 'Sent'),
                    ('viewed', 'Viewed'),
                    ('negotiating', 'Negotiating'),
                    ('accepted', 'Accepted'),
                    ('rejected', 'Rejected'),
                    ('finished', 'Finished'),
                    ('email_sent', 'Email Sent'),
                    ('note', 'Note'),
                    ('call', 'Call'),
                    ('meeting', 'Meeting'),
                    ('followup', 'Follow-up'),
                    ('status_change', 'Status Change'),
                ], max_length=30)),
                ('field_name', models.CharField(blank=True, default='', max_length=100)),
                ('old_value', models.TextField(blank=True, default='')),
                ('new_value', models.TextField(blank=True, default='')),
                ('description', models.TextField(blank=True, default='')),
                ('actor_type', models.CharField(blank=True, choices=[
                    ('client', 'Client'),
                    ('seller', 'Seller'),
                    ('system', 'System'),
                ], default='', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('diagnostic', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='change_logs',
                    to='content.webappdiagnostic',
                )),
            ],
            options={
                'verbose_name': 'Diagnostic Change Log',
                'verbose_name_plural': 'Diagnostic Change Logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DiagnosticViewEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(help_text='Client-side generated session identifier.', max_length=64)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, default='')),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
                ('diagnostic', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='view_events',
                    to='content.webappdiagnostic',
                )),
            ],
            options={
                'verbose_name': 'Diagnostic View Event',
                'verbose_name_plural': 'Diagnostic View Events',
                'ordering': ['-viewed_at'],
            },
        ),
        migrations.CreateModel(
            name='DiagnosticSectionView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section_type', models.CharField(max_length=50)),
                ('section_title', models.CharField(blank=True, default='', max_length=255)),
                ('time_spent_seconds', models.FloatField(default=0)),
                ('entered_at', models.DateTimeField()),
                ('view_event', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='section_views',
                    to='content.diagnosticviewevent',
                )),
            ],
            options={
                'verbose_name': 'Diagnostic Section View',
                'verbose_name_plural': 'Diagnostic Section Views',
                'ordering': ['entered_at'],
            },
        ),
    ]
