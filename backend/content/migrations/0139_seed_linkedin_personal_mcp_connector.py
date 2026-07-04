from django.db import migrations

# LinkedIn Personal Content MCP connector. Seeded inactive and tokenless —
# the operator generates a token and toggles it on in /panel/mcps. slug must
# match the key registered in TOOLS_BY_SLUG (content/views/mcp_blog.py).
# "-personal" reserves the namespace for a future linkedin-company connector.
CONNECTORS = [
    (
        'linkedin-personal',
        'LinkedIn Personal Content',
        'Permite a Claude (claude.ai) gestionar los posts de LinkedIn del '
        'perfil personal: consultar la conexión OAuth y su expiración, '
        'listar/leer posts, crear borradores (solo texto), programarlos, '
        'editarlos, eliminarlos y publicarlos al instante.',
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
        ('content', '0138_linkedinpost'),
    ]
    operations = [
        migrations.RunPython(seed_connectors, unseed_connectors),
    ]
