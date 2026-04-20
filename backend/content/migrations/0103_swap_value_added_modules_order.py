from django.db import migrations


def _apply(section, new_order):
    section.order = new_order
    cj = section.content_json or {}
    if 'index' in cj:
        cj['index'] = str(new_order)
        section.content_json = cj
    section.save(update_fields=['order', 'content_json'])


def _swap(ProposalSection, vam_order, fr_order):
    pairs = {}
    qs = ProposalSection.objects.filter(
        section_type__in=('value_added_modules', 'functional_requirements'),
    ).only('id', 'proposal_id', 'section_type', 'order', 'content_json')
    for section in qs:
        pairs.setdefault(section.proposal_id, {})[section.section_type] = section

    for sections in pairs.values():
        vam = sections.get('value_added_modules')
        fr = sections.get('functional_requirements')
        if not vam or not fr:
            continue
        _apply(vam, vam_order)
        _apply(fr, fr_order)


def swap_vam_fr_order(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    _swap(ProposalSection, vam_order=10, fr_order=9)


def unswap_vam_fr_order(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    _swap(ProposalSection, vam_order=9, fr_order=10)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0102_value_added_modules_section'),
    ]

    operations = [
        migrations.RunPython(swap_vam_fr_order, unswap_vam_fr_order),
    ]
