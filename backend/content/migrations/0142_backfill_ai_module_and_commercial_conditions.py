"""Backfill the free AI automation module + commercial conditions section.

``DEFAULT_SECTIONS`` only shapes NEWLY created proposals, so existing ones need
a one-time backfill to pick up the Req 3 additions (the free
``ai_automation_module`` inside functional requirements + its value-added
condition/terms) and the PDF-only ``commercial_conditions`` section (hour
packages + scope-exclusion clause).

Sourcing the content from the live defaults is safe here: on a fresh database
there are no proposals to backfill (this migration becomes a no-op and new
proposals get the defaults directly), and on production it yields the current
correct values. The migration is idempotent — re-running it changes nothing.
"""
from copy import deepcopy

from django.db import migrations


def _defaults_for(lang):
    # Imported lazily so the migration only touches app code at run time.
    from content.services.proposal_service import (
        DEFAULT_SECTIONS,
        DEFAULT_SECTIONS_EN,
    )
    return DEFAULT_SECTIONS_EN if lang == 'en' else DEFAULT_SECTIONS


def _find_section(defaults, section_type):
    return next(
        (s for s in defaults if s.get('section_type') == section_type),
        None,
    )


def _ai_group(defaults):
    fr = _find_section(defaults, 'functional_requirements')
    groups = (fr or {}).get('content_json', {}).get('groups', []) or []
    return next(
        (g for g in groups if isinstance(g, dict)
         and g.get('id') == 'ai_automation_module'),
        None,
    )


def _augment_sections_json(sections, defaults):
    """Apply the Req 3 + commercial_conditions additions to a list of section
    dicts (same shape as DEFAULT_SECTIONS / ProposalDefaultConfig.sections_json).

    Mutates ``sections`` in place and returns True when anything changed.
    Idempotent: pre-existing entries are left untouched.
    """
    if not isinstance(sections, list):
        return False
    ai_group = _ai_group(defaults)
    va_default_cj = (_find_section(defaults, 'value_added_modules') or {}).get(
        'content_json', {}) or {}
    cc_default = _find_section(defaults, 'commercial_conditions')
    changed = False

    fr = _find_section(sections, 'functional_requirements')
    if fr and isinstance(fr.get('content_json'), dict) and ai_group:
        groups = fr['content_json'].get('groups')
        if isinstance(groups, list) and not any(
            isinstance(g, dict) and g.get('id') == 'ai_automation_module'
            for g in groups
        ):
            groups.append(deepcopy(ai_group))
            changed = True

    va = _find_section(sections, 'value_added_modules')
    if va and isinstance(va.get('content_json'), dict):
        cj = va['content_json']
        mids = cj.get('module_ids')
        if isinstance(mids, list) and 'ai_automation_module' not in mids:
            mids.append('ai_automation_module')
            changed = True
        just = cj.get('justifications')
        default_just = va_default_cj.get('justifications', {}) or {}
        if isinstance(just, dict) and 'ai_automation_module' not in just:
            ai_just = default_just.get('ai_automation_module')
            if ai_just:
                just['ai_automation_module'] = ai_just
                changed = True
        conds = cj.get('conditions')
        if not isinstance(conds, dict):
            conds = {}
            cj['conditions'] = conds
        for key, value in (va_default_cj.get('conditions', {}) or {}).items():
            if key not in conds:
                conds[key] = deepcopy(value)
                changed = True

    if cc_default and not _find_section(sections, 'commercial_conditions'):
        sections.append(deepcopy(cc_default))
        changed = True

    return changed


def backfill_default_configs(apps):
    """Patch populated ProposalDefaultConfig snapshots so NEW proposals pick up
    the additions (the snapshot overrides the hardcoded DEFAULT_SECTIONS)."""
    try:
        ProposalDefaultConfig = apps.get_model(
            'content', 'ProposalDefaultConfig')
    except LookupError:
        return
    for config in ProposalDefaultConfig.objects.iterator():
        sections = config.sections_json
        if not isinstance(sections, list) or not sections:
            continue  # empty snapshot → hardcoded defaults already apply
        lang = getattr(config, 'language', 'es') or 'es'
        if _augment_sections_json(sections, _defaults_for(lang)):
            config.sections_json = sections
            config.save(update_fields=['sections_json'])


def backfill(apps, schema_editor):
    backfill_default_configs(apps)

    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalSection = apps.get_model('content', 'ProposalSection')

    for proposal in BusinessProposal.objects.iterator():
        lang = getattr(proposal, 'language', 'es') or 'es'
        defaults = _defaults_for(lang)
        ai_group = _ai_group(defaults)
        va_default = _find_section(defaults, 'value_added_modules') or {}
        va_default_cj = va_default.get('content_json', {}) or {}

        # 1) Functional requirements: append the free AI automation group.
        fr = ProposalSection.objects.filter(
            proposal=proposal,
            section_type='functional_requirements',
        ).first()
        if fr and isinstance(fr.content_json, dict) and ai_group:
            groups = fr.content_json.get('groups')
            if isinstance(groups, list) and not any(
                isinstance(g, dict) and g.get('id') == 'ai_automation_module'
                for g in groups
            ):
                groups.append(deepcopy(ai_group))
                fr.content_json['groups'] = groups
                fr.save(update_fields=['content_json'])

        # 2) Value-added modules: reference the AI module + merge conditions.
        va = ProposalSection.objects.filter(
            proposal=proposal,
            section_type='value_added_modules',
        ).first()
        if va and isinstance(va.content_json, dict):
            cj = va.content_json
            changed = False

            mids = cj.get('module_ids')
            if isinstance(mids, list) and 'ai_automation_module' not in mids:
                mids.append('ai_automation_module')
                changed = True

            just = cj.get('justifications')
            default_just = va_default_cj.get('justifications', {}) or {}
            if isinstance(just, dict) and 'ai_automation_module' not in just:
                ai_just = default_just.get('ai_automation_module')
                if ai_just:
                    just['ai_automation_module'] = ai_just
                    changed = True

            conds = cj.get('conditions')
            if not isinstance(conds, dict):
                conds = {}
                cj['conditions'] = conds
            for key, value in (va_default_cj.get('conditions', {}) or {}).items():
                if key not in conds:
                    conds[key] = deepcopy(value)
                    changed = True

            if changed:
                va.content_json = cj
                va.save(update_fields=['content_json'])

        # 3) Create the PDF-only commercial_conditions section if missing.
        has_cc = ProposalSection.objects.filter(
            proposal=proposal,
            section_type='commercial_conditions',
        ).exists()
        cc_default = _find_section(defaults, 'commercial_conditions')
        if not has_cc and cc_default:
            content = deepcopy(cc_default.get('content_json', {}))
            currency = getattr(proposal, 'currency', 'COP') or 'COP'
            content['currency'] = currency
            if currency == 'USD':
                content['hourlyRate'] = 25
            ProposalSection.objects.create(
                proposal=proposal,
                section_type='commercial_conditions',
                title=cc_default.get('title', 'Condiciones comerciales'),
                order=cc_default.get('order', 17),
                is_enabled=True,
                content_json=content,
                is_wide_panel=cc_default.get('is_wide_panel', False),
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0141_alter_proposalsection_section_type'),
    ]

    operations = [
        migrations.RunPython(backfill, noop_reverse),
    ]
