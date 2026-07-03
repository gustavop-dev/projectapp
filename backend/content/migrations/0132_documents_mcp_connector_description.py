from django.db import migrations

NEW_DESCRIPTION = (
    'Da a Claude (claude.ai) acceso al gestor de documentos del panel: '
    'listar, crear y renombrar carpetas, y listar, leer, crear, editar y '
    'eliminar documentos en Markdown (que el panel convierte a PDF). '
    'No accede a las cuentas de cobro, no borra documentos publicados ni '
    'carpetas.'
)

OLD_DESCRIPTION = (
    'Permite a Claude (claude.ai) navegar las carpetas y documentos del '
    'panel, y crear, leer, editar y eliminar documentos markdown directamente.'
)


def set_new_description(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.filter(slug='documents').update(description=NEW_DESCRIPTION)


def set_old_description(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.filter(slug='documents').update(description=OLD_DESCRIPTION)


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0131_seed_documents_mcp_connector'),
    ]
    operations = [
        migrations.RunPython(set_new_description, set_old_description),
    ]
