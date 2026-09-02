from django.db import migrations


OLD_DESCRIPTION = (
    'Lista y abre hilos por cliente o proyecto, crea hilos, registra y edita '
    'borradores de correo o WhatsApp, referencia documentos y marca envíos externos.'
)
NEW_DESCRIPTION = (
    'Administra hilos y mensajes de clientes: consulta, crea y edita; cierra, '
    'reabre, archiva o restaura hilos; elimina borradores, registra envíos, '
    'anula mensajes y corrige fechas sin enviar por los canales.'
)


def update_communications_description(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.filter(slug='communications').update(
        description=NEW_DESCRIPTION,
    )


def restore_communications_description(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.filter(slug='communications').update(
        description=OLD_DESCRIPTION,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0236_document_threads'),
    ]

    operations = [
        migrations.RunPython(
            update_communications_description,
            restore_communications_description,
        ),
    ]
