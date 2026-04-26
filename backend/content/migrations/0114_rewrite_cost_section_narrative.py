"""Rewrite the narrative of every diagnostic ``cost`` section to the new
default that justifies the diagnostic's value with concrete bullets and
makes the link to the General tab explicit.

The frontend ``CostSection`` and the PDF renderer both read
``content_json`` per section, so updating the seed alone would only
affect newly created diagnostics. This migration overwrites existing
``cost`` sections to keep all diagnostics aligned with the new default,
preserving each section's ``index`` so the visual numbering chosen by
the admin is not lost.
"""
from django.db import migrations


def rewrite_cost_sections(apps, schema_editor):
    import copy

    from content.seeds.diagnostic_template import _cost_section

    DiagnosticSection = apps.get_model('content', 'DiagnosticSection')
    template = _cost_section(0)['content_json']
    qs = (
        DiagnosticSection.objects
        .filter(section_type='cost')
        .only('id', 'content_json')
    )
    batch = []
    BATCH_SIZE = 500
    for section in qs.iterator(chunk_size=BATCH_SIZE):
        new_content = copy.deepcopy(template)
        existing_index = (section.content_json or {}).get('index')
        if existing_index:
            new_content['index'] = existing_index
        section.content_json = new_content
        batch.append(section)
        if len(batch) >= BATCH_SIZE:
            DiagnosticSection.objects.bulk_update(batch, ['content_json'])
            batch.clear()
    if batch:
        DiagnosticSection.objects.bulk_update(batch, ['content_json'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0113_backfill_selected_modules'),
    ]

    operations = [
        migrations.RunPython(rewrite_cost_sections, migrations.RunPython.noop),
    ]
