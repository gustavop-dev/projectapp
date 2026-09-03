import uuid

import content.models.mcp_upload
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


CONNECTORS = {
    'operations': (
        'Operaciones',
        'Dashboard, indicadores, alertas y conteos globales de solo lectura.',
    ),
    'commercial': (
        'Gestor Comercial',
        'Clientes, propuestas, diagnósticos, módulos, paquetes de horas y financiación.',
    ),
    'projects': (
        'Gestor de Proyectos',
        'Proyectos, asignaciones, estados, transiciones e historial operativo.',
    ),
    'content': (
        'Gestor de Contenido',
        'Blog, portafolio, QR, Linktrees y publicaciones de LinkedIn.',
    ),
    'accounting-ledger': (
        'Contabilidad · Libro',
        'Ingresos, gastos, bolsillo, recurrentes, Ads, categorías y exportaciones.',
    ),
    'accounting-billing': (
        'Contabilidad · Cobros',
        'Cuentas de cobro, hosting, ciclos y comunicaciones contables.',
    ),
    'accounting-cards': (
        'Contabilidad · Tarjetas',
        'Tarjetas, extractos, transacciones, alias y recordatorios.',
    ),
}


def seed_connectors_and_credentials(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpCredential = apps.get_model('content', 'McpCredential')
    for slug, (name, description) in CONNECTORS.items():
        McpConnector.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'description': description,
                'is_active': False,
            },
        )
    for connector in McpConnector.objects.exclude(token_hash=''):
        McpCredential.objects.get_or_create(
            connector=connector,
            label='Default',
            defaults={
                'token_hash': connector.token_hash,
                'token_prefix': connector.token_prefix,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0239_expand_communications_mcp_parity'),
    ]

    operations = [
        migrations.CreateModel(
            name='McpCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(default='Default', max_length=100)),
                ('token_hash', models.CharField(db_index=True, max_length=64)),
                ('token_prefix', models.CharField(blank=True, default='', max_length=8)),
                ('allowed_tools', models.JSONField(blank=True, default=list, help_text='Empty means every tool exposed by the connector.')),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mcp_credentials', to=settings.AUTH_USER_MODEL)),
                ('connector', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credentials', to='content.mcpconnector')),
            ],
            options={'ordering': ['connector_id', 'created_at', 'id']},
        ),
        migrations.AddConstraint(
            model_name='mcpcredential',
            constraint=models.UniqueConstraint(fields=('connector', 'label'), name='uniq_mcp_credential_label'),
        ),
        migrations.CreateModel(
            name='McpActionIntent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tool_name', models.CharField(max_length=120)),
                ('arguments', models.JSONField(default=dict)),
                ('arguments_hash', models.CharField(max_length=64)),
                ('impact', models.JSONField(blank=True, default=dict)),
                ('resource_etags', models.JSONField(blank=True, default=dict)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('executed', 'Executed'), ('expired', 'Expired'), ('cancelled', 'Cancelled')], db_index=True, default='pending', max_length=12)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('executed_at', models.DateTimeField(blank=True, null=True)),
                ('result', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('connector', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_intents', to='content.mcpconnector')),
                ('credential', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_intents', to='content.mcpcredential')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='mcpactionintent',
            index=models.Index(fields=['credential', 'status', 'expires_at'], name='mcp_intent_cred_status_idx'),
        ),
        migrations.CreateModel(
            name='McpUpload',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('filename', models.CharField(max_length=255)),
                ('content_type', models.CharField(max_length=120)),
                ('expected_size', models.PositiveBigIntegerField()),
                ('expected_sha256', models.CharField(max_length=64)),
                ('received_size', models.PositiveBigIntegerField(default=0)),
                ('next_chunk_index', models.PositiveIntegerField(default=0)),
                ('file', models.FileField(blank=True, upload_to=content.models.mcp_upload.mcp_upload_path)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('complete', 'Complete'), ('consumed', 'Consumed'), ('aborted', 'Aborted')], db_index=True, default='pending', max_length=12)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('consumed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('connector', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploads', to='content.mcpconnector')),
                ('credential', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploads', to='content.mcpcredential')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='mcprequestlog',
            name='credential',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='request_logs', to='content.mcpcredential'),
        ),
        migrations.AddField(
            model_name='mcprequestlog',
            name='duration_ms',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mcprequestlog',
            name='error_code',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='mcprequestlog',
            name='object_refs',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='mcprequestlog',
            name='request_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=36),
        ),
        migrations.AddField(
            model_name='mcprequestlog',
            name='risk_level',
            field=models.CharField(blank=True, choices=[('read', 'Read'), ('write', 'Reversible write'), ('sensitive', 'Sensitive')], default='', max_length=12),
        ),
        migrations.AddField(
            model_name='mcprequestlog',
            name='tool_name',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AlterField(
            model_name='mcprequestlog',
            name='event',
            field=models.CharField(choices=[('handshake', 'Handshake'), ('discovery', 'Discovery'), ('tool_call', 'Tool call'), ('auth_error', 'Auth error'), ('origin_rejected', 'Origin rejected')], max_length=20),
        ),
        migrations.RunPython(
            seed_connectors_and_credentials,
            migrations.RunPython.noop,
        ),
    ]
