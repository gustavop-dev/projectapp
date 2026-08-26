from django.db import migrations


# Persisted panel copy follows the registered tool surface. Existing connector
# credentials and active states are deliberately untouched.
CONNECTORS = {
    'blog': (
        'Blog Publisher',
        'Crea, programa, lista, abre, edita y elimina borradores del blog; '
        'incluye contenido bilingüe, SEO, fuentes y calendario editorial.',
    ),
    'documents': (
        'Gestor de Documentos',
        'Gestiona documentos markdown, carpetas, cliente/proyecto, visibilidad, '
        'estados, observaciones y notas privadas para el cliente.',
    ),
    'clients': (
        'Gestor de Clientes',
        'Busca y administra clientes compartidos por propuestas, proyectos, '
        'diagnósticos, documentos, contabilidad y comunicaciones.',
    ),
    'tasks': (
        'Gestor de Tareas',
        'Gestiona el tablero Kanban, incluidas tareas, estados, archivo, '
        'duplicación, comentarios y alertas.',
    ),
    'accounting': (
        'Contabilidad',
        'Gestiona registros contables, hostings, períodos, pagos parciales y '
        'abonos, bolsillo, tarjetas, extractos, auditoría y configuración. '
        'Contiene datos financieros sensibles.',
    ),
    'diagnostics': (
        'Gestor de Diagnósticos',
        'Crea y administra diagnósticos, cliente, metadatos, secciones, estados, '
        'envíos y plantillas con las mismas reglas del panel.',
    ),
    'proposals': (
        'Gestor de Propuestas',
        'Crea, abre, reimporta, envía, duplica y elimina propuestas completas, '
        'incluidos metadatos comerciales, contrato y enlaces compartidos.',
    ),
    'linkedin-personal': (
        'LinkedIn Personal Content',
        'Consulta la conexión personal de LinkedIn y administra borradores, '
        'programación, edición, eliminación y publicación de posts de texto.',
    ),
    'communications': (
        'Gestor de Comunicaciones',
        'Lista y abre hilos por cliente o proyecto, crea hilos, registra mensajes '
        'de correo o WhatsApp, referencia documentos y marca envíos externos.',
    ),
}


def seed_and_refresh_connectors(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    for slug, (name, description) in CONNECTORS.items():
        connector, created = McpConnector.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'description': description,
                'is_active': False,
            },
        )
        if not created:
            McpConnector.objects.filter(pk=connector.pk).update(
                name=name,
                description=description,
            )


def unseed_communications_connector(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.filter(slug='communications').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0211_merge_document_states_communications'),
    ]

    operations = [
        migrations.RunPython(
            seed_and_refresh_connectors,
            unseed_communications_connector,
        ),
    ]
