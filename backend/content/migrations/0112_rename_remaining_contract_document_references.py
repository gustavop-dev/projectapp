# Generated 2026-04-23 — finish the rename started in
# 0111_update_default_contract_template_v4: replace every remaining
# reference to "Documento Propuesta de Negocio" (body paragraphs in
# garantía, hosting, precio, OTROSÍ, acuerdo total, título ejecutivo,
# etc.) with the new "Documento Propuesta Comercial" name so the default
# template reads consistently.

from django.db import migrations


OLD = 'Documento Propuesta de Negocio'
NEW = 'Documento Propuesta Comercial'


def _apply(apps, old_text, new_text):
    ContractTemplate = apps.get_model('content', 'ContractTemplate')
    template = ContractTemplate.objects.filter(is_default=True).first()
    if not template:
        return
    md = template.content_markdown
    if old_text not in md:
        return
    new_md = md.replace(old_text, new_text)
    if new_md != md:
        template.content_markdown = new_md
        template.save(update_fields=['content_markdown'])


def forwards(apps, schema_editor):
    _apply(apps, OLD, NEW)


def backwards(apps, schema_editor):
    _apply(apps, NEW, OLD)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0111_update_default_contract_template_v4'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
