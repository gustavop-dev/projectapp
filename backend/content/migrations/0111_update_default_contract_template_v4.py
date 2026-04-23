# Generated 2026-04-23 — update default contract template v4:
# rename "Documento Propuesta de Negocio" → "Documento Propuesta Comercial"
# on the two ANEXO ADJUNTO lines inside Cláusula Segunda, add a second
# "Documento Detalle Técnico" ANEXO only under Parágrafo Segundo — Productos,
# and drop "Roles" from the Parágrafo Tercero heading.

from django.db import migrations


PRODUCTOS_OLD = (
    '### Parágrafo Segundo — Productos\n\n'
    'ANEXO ADJUNTO: Documento Propuesta de Negocio\n'
)
PRODUCTOS_NEW = (
    '### Parágrafo Segundo — Productos\n\n'
    'ANEXO ADJUNTO: Documento Propuesta Comercial\n\n'
    'ANEXO ADJUNTO: Documento Detalle Técnico\n'
)

CRONOGRAMA_OLD = (
    '### Parágrafo Tercero — Cronograma, Roles y Entregables\n\n'
    'ANEXO ADJUNTO: Documento Propuesta de Negocio\n'
)
CRONOGRAMA_NEW = (
    '### Parágrafo Tercero — Cronograma y Entregables\n\n'
    'ANEXO ADJUNTO: Documento Propuesta Comercial\n'
)


def _apply_replacements(apps, pairs):
    ContractTemplate = apps.get_model('content', 'ContractTemplate')
    template = ContractTemplate.objects.filter(is_default=True).first()
    if not template:
        return
    md = template.content_markdown
    for old, new in pairs:
        if old in md:
            md = md.replace(old, new, 1)
    if md != template.content_markdown:
        template.content_markdown = md
        template.save(update_fields=['content_markdown'])


def update_default_template(apps, schema_editor):
    _apply_replacements(apps, [
        (PRODUCTOS_OLD, PRODUCTOS_NEW),
        (CRONOGRAMA_OLD, CRONOGRAMA_NEW),
    ])


def revert_default_template(apps, schema_editor):
    _apply_replacements(apps, [
        (PRODUCTOS_NEW, PRODUCTOS_OLD),
        (CRONOGRAMA_NEW, CRONOGRAMA_OLD),
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0110_tracking_constraints_and_indexes'),
    ]

    operations = [
        migrations.RunPython(update_default_template, revert_default_template),
    ]
