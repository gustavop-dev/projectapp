from django.db import migrations

# One row per new panel MCP connector. Seeded inactive and tokenless — the
# operator generates a token and toggles it on in /panel/mcps. slug must match
# the key registered in TOOLS_BY_SLUG (content/views/mcp_blog.py).
CONNECTORS = [
    (
        'proposals',
        'Gestor de Propuestas',
        'Permite a Claude (claude.ai) listar, crear, editar (desde JSON), '
        'enviar, duplicar y eliminar propuestas comerciales, y gestionar sus '
        'enlaces de compartición.',
    ),
    (
        'diagnostics',
        'Gestor de Diagnósticos',
        'Permite a Claude gestionar diagnósticos web: crear (desde un cliente), '
        'editar datos y secciones, mover el estado, enviar los documentos '
        'inicial/final y leer las plantillas.',
    ),
    (
        'clients',
        'Gestor de Clientes',
        'Permite a Claude buscar, listar, crear, actualizar y eliminar clientes '
        'de propuestas/diagnósticos (perfiles compartidos).',
    ),
    (
        'tasks',
        'Gestor de Tareas',
        'Permite a Claude gestionar el tablero Kanban: crear, mover, archivar y '
        'duplicar tareas, y administrar comentarios y alertas.',
    ),
    (
        'accounting',
        'Contabilidad',
        'Permite a Claude gestionar la contabilidad personal (ingresos, gastos, '
        'hostings, pocket, recurrentes, ads, tarjetas), el dashboard, la '
        'auditoría y la configuración. Dato financiero sensible.',
    ),
]


def seed_connectors(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    for slug, name, description in CONNECTORS:
        McpConnector.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'description': description, 'is_active': False},
        )


def unseed_connectors(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    slugs = [slug for slug, _, _ in CONNECTORS]
    McpConnector.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0135_document_requires_signature_document_signature_ip_and_more'),
    ]
    operations = [
        migrations.RunPython(seed_connectors, unseed_connectors),
    ]
