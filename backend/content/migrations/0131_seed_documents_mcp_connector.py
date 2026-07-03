from django.db import migrations


def seed_documents_connector(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.get_or_create(
        slug='documents',
        defaults={
            'name': 'Gestor de Documentos',
            'description': (
                'Permite a Claude (claude.ai) navegar las carpetas y '
                'documentos del panel, y crear, leer, editar y eliminar '
                'documentos markdown directamente.'
            ),
            'is_active': False,
        },
    )


def unseed_documents_connector(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.filter(slug='documents').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0130_mcprequestlog'),
    ]
    operations = [
        migrations.RunPython(seed_documents_connector, unseed_documents_connector),
    ]
