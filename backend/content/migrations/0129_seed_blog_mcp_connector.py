from django.db import migrations


def seed_blog_connector(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.get_or_create(
        slug='blog',
        defaults={
            'name': 'Blog Publisher',
            'description': (
                'Permite a Claude (claude.ai) crear, programar, editar y '
                'consultar posts del blog directamente.'
            ),
            'is_active': False,
        },
    )


def unseed_blog_connector(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.filter(slug='blog').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0128_mcpconnector'),
    ]
    operations = [
        migrations.RunPython(seed_blog_connector, unseed_blog_connector),
    ]
