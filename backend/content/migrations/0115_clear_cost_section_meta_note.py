"""Clear the meta-instructive ``note`` from existing diagnostic ``cost``
sections.

Migration ``0114`` inserted a note explaining to the client where the
investment amount and percentages came from. That copy was meant as
admin-facing context, not propuesta-facing content — the percentages
are already rendered in the segmented bar in the public view, so the
note is redundant and looks like internal metadata.
"""
from django.db import migrations


# 0114 wrote this exact string into every cost section's content_json via
# deepcopy of the seed template, so any section still holding it post-0114
# is a known seed-generated note (not admin-authored).
KNOWN_META_NOTES = [
    (
        'El monto, la moneda y los porcentajes que ves arriba se '
        'toman directamente del tab General de la vista detalle de '
        'este diagnóstico. Si durante el levantamiento inicial se '
        'identifica un alcance significativamente mayor al estimado, '
        'el valor puede ajustarse antes de continuar.'
    ),
]


def clear_meta_notes(apps, schema_editor):
    DiagnosticSection = apps.get_model('content', 'DiagnosticSection')
    qs = (
        DiagnosticSection.objects
        .filter(section_type='cost', content_json__note__in=KNOWN_META_NOTES)
        .only('id', 'content_json')
    )
    batch = []
    BATCH_SIZE = 500
    for section in qs.iterator(chunk_size=BATCH_SIZE):
        new_content = dict(section.content_json or {})
        new_content['note'] = ''
        section.content_json = new_content
        batch.append(section)
        if len(batch) >= BATCH_SIZE:
            DiagnosticSection.objects.bulk_update(batch, ['content_json'])
            batch.clear()
    if batch:
        DiagnosticSection.objects.bulk_update(batch, ['content_json'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0114_rewrite_cost_section_narrative'),
    ]

    operations = [
        migrations.RunPython(clear_meta_notes, migrations.RunPython.noop),
    ]
