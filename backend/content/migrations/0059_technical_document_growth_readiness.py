# Merge growthReadiness into existing technical_document section content_json

from copy import deepcopy

from django.db import migrations


def merge_growth_readiness(apps, schema_editor):
    from content.technical_document_defaults import EMPTY_TECHNICAL_DOCUMENT_JSON

    ProposalSection = apps.get_model('content', 'ProposalSection')
    default_gr = deepcopy(EMPTY_TECHNICAL_DOCUMENT_JSON.get('growthReadiness', {}))
    for sec in ProposalSection.objects.filter(section_type='technical_document'):
        cj = sec.content_json if isinstance(sec.content_json, dict) else {}
        if 'growthReadiness' in cj:
            continue
        new_cj = {**cj, 'growthReadiness': default_gr}
        sec.content_json = new_cj
        sec.save(update_fields=['content_json'])


def remove_growth_readiness(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    for sec in ProposalSection.objects.filter(section_type='technical_document'):
        cj = sec.content_json if isinstance(sec.content_json, dict) else {}
        if 'growthReadiness' not in cj:
            continue
        new_cj = {k: v for k, v in cj.items() if k != 'growthReadiness'}
        sec.content_json = new_cj
        sec.save(update_fields=['content_json'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0058_document_deliverable'),
    ]

    operations = [
        migrations.RunPython(merge_growth_readiness, remove_growth_readiness),
    ]
