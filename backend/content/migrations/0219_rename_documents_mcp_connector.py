from django.db import migrations


OLD_NAME = 'Gestor de Documentos'
NEW_NAME = 'Gestor Documental'

OLD_DESCRIPTION = (
    'Da a Claude (claude.ai) acceso al gestor de documentos del panel: '
    'listar, crear y renombrar carpetas, y listar, leer, crear, editar y '
    'eliminar documentos en Markdown (que el panel convierte a PDF). '
    'No accede a las cuentas de cobro, no borra documentos publicados ni '
    'carpetas.'
)

NEW_DESCRIPTION = (
    'Da a Claude (claude.ai) acceso al gestor documental del panel: '
    'listar, crear y renombrar carpetas, y listar, leer, crear, editar y '
    'eliminar documentos en Markdown (que el panel convierte a PDF). '
    'No accede a las cuentas de cobro, no borra documentos publicados ni '
    'carpetas.'
)


def rename_documents_connector(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.filter(slug='documents').update(
        name=NEW_NAME,
        description=NEW_DESCRIPTION,
    )


def restore_documents_connector_name(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.filter(slug='documents').update(
        name=OLD_NAME,
        description=OLD_DESCRIPTION,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0218_project_state_help'),
    ]

    operations = [
        migrations.RunPython(
            rename_documents_connector,
            restore_documents_connector_name,
        ),
    ]
