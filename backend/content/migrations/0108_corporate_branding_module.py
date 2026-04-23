from django.db import migrations

from content.services.proposal_service import ProposalService


def _get_default_corporate_module(language):
    sections = ProposalService.get_default_sections(language=language)
    vam = next(
        (s for s in sections if s['section_type'] == 'value_added_modules'),
        None,
    )
    if not vam:
        return None
    additional = (vam.get('content_json') or {}).get('additionalModules') or []
    return next(
        (m for m in additional if m.get('id') == 'corporate_branding_module'),
        None,
    )


def add_corporate_branding(apps, schema_editor):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalSection = apps.get_model('content', 'ProposalSection')

    sections = list(
        ProposalSection.objects.filter(section_type='value_added_modules')
    )
    if not sections:
        return

    proposal_ids = {s.proposal_id for s in sections}
    proposal_lang = {
        p.pk: (getattr(p, 'language', 'es') or 'es')
        for p in BusinessProposal.objects.filter(pk__in=proposal_ids).only('id', 'language')
    }

    module_by_lang = {}
    to_update = []
    for section in sections:
        content = section.content_json or {}
        additional = list(content.get('additionalModules') or [])
        if any(m.get('id') == 'corporate_branding_module' for m in additional):
            continue
        lang = proposal_lang.get(section.proposal_id, 'es')
        if lang not in module_by_lang:
            module_by_lang[lang] = _get_default_corporate_module(lang)
        module = module_by_lang[lang]
        if not module:
            continue
        ai_idx = next(
            (i for i, m in enumerate(additional) if m.get('id') == 'ai_module'),
            None,
        )
        if ai_idx is None:
            additional.append(module)
        else:
            additional.insert(ai_idx, module)
        content['additionalModules'] = additional
        section.content_json = content
        to_update.append(section)

    if to_update:
        ProposalSection.objects.bulk_update(to_update, ['content_json'], batch_size=100)


def remove_corporate_branding(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    to_update = []
    for section in ProposalSection.objects.filter(section_type='value_added_modules'):
        content = section.content_json or {}
        additional = content.get('additionalModules') or []
        filtered = [m for m in additional if m.get('id') != 'corporate_branding_module']
        if len(filtered) != len(additional):
            content['additionalModules'] = filtered
            section.content_json = content
            to_update.append(section)
    if to_update:
        ProposalSection.objects.bulk_update(to_update, ['content_json'], batch_size=100)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0107_diagnostic_slug_and_default_pattern'),
    ]

    operations = [
        migrations.RunPython(add_corporate_branding, remove_corporate_branding),
    ]
