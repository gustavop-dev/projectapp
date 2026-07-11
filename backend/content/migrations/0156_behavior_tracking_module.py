"""Backfill the paid behavior tracking additional module.

``DEFAULT_SECTIONS`` only shapes NEWLY created proposals, so existing ones need
a one-time backfill to offer the new ``behavior_tracking_module`` (priced
calculator module at 30%, not selected) in their functional requirements /
investment calculator. The module lands deselected, so no proposal's price or
selection changes — it just becomes available.

Sourcing the content from the live defaults is safe here: on a fresh database
there are no proposals to backfill (this migration becomes a no-op and new
proposals get the defaults directly), and on production it yields the current
correct values. The migration is idempotent — re-running it changes nothing,
and a proposal that already carries a (possibly customized)
``behavior_tracking_module`` is left untouched.
"""
from copy import deepcopy

from django.db import migrations


MODULE_ID = 'behavior_tracking_module'
ANCHOR_ID = 'reports_alerts_module'
FR_SECTION_TYPE = 'functional_requirements'
VA_SECTION_TYPE = 'value_added_modules'


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


def _behavior_module(defaults):
    fr = _find_section(defaults, FR_SECTION_TYPE)
    modules = (fr or {}).get('content_json', {}).get('additionalModules', []) or []
    return next(
        (m for m in modules if isinstance(m, dict) and m.get('id') == MODULE_ID),
        None,
    )


def _insert_before_anchor(modules, new_module):
    """Insert ``new_module`` right before the anchor module, appending when the
    anchor is missing. Returns (modules, changed); never duplicates."""
    if any(isinstance(m, dict) and m.get('id') == MODULE_ID for m in modules):
        return modules, False
    anchor_idx = next(
        (i for i, m in enumerate(modules)
         if isinstance(m, dict) and m.get('id') == ANCHOR_ID),
        None,
    )
    if anchor_idx is None:
        modules.append(deepcopy(new_module))
    else:
        modules.insert(anchor_idx, deepcopy(new_module))
    return modules, True


def _merge_missing_conditions(content_json, va_default_cj):
    """Self-heal: copy any value-added condition keys a proposal predates.
    Existing entries are never overwritten (presumed customized)."""
    conds = content_json.get('conditions')
    if not isinstance(conds, dict):
        conds = {}
        content_json['conditions'] = conds
    changed = False
    for key, value in (va_default_cj.get('conditions', {}) or {}).items():
        if key not in conds:
            conds[key] = deepcopy(value)
            changed = True
    return changed


def _augment_sections_json(sections, defaults):
    """Apply the additions to a list of section dicts (same shape as
    DEFAULT_SECTIONS / ProposalDefaultConfig.sections_json).

    Mutates ``sections`` in place and returns True when anything changed.
    Idempotent: pre-existing entries are left untouched.
    """
    if not isinstance(sections, list):
        return False
    module = _behavior_module(defaults)
    va_default_cj = (_find_section(defaults, VA_SECTION_TYPE) or {}).get(
        'content_json', {}) or {}
    changed = False

    fr = _find_section(sections, FR_SECTION_TYPE)
    if fr and isinstance(fr.get('content_json'), dict) and module:
        modules = fr['content_json'].get('additionalModules')
        if isinstance(modules, list):
            modules, modified = _insert_before_anchor(modules, module)
            if modified:
                fr['content_json']['additionalModules'] = modules
                changed = True

    va = _find_section(sections, VA_SECTION_TYPE)
    if va and isinstance(va.get('content_json'), dict):
        if _merge_missing_conditions(va['content_json'], va_default_cj):
            changed = True

    return changed


def backfill_default_configs(apps):
    """Patch populated ProposalDefaultConfig snapshots so NEW proposals pick up
    the module (the snapshot overrides the hardcoded DEFAULT_SECTIONS)."""
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
        module = _behavior_module(defaults)
        va_default_cj = (_find_section(defaults, VA_SECTION_TYPE) or {}).get(
            'content_json', {}) or {}

        # 1) Functional requirements: offer the module in the calculator.
        fr = ProposalSection.objects.filter(
            proposal=proposal,
            section_type=FR_SECTION_TYPE,
        ).first()
        if fr and isinstance(fr.content_json, dict) and module:
            modules = fr.content_json.get('additionalModules')
            if isinstance(modules, list):
                modules, changed = _insert_before_anchor(modules, module)
                if changed:
                    fr.content_json['additionalModules'] = modules
                    fr.save(update_fields=['content_json'])

        # 2) Value-added modules: self-heal any missing condition keys.
        va = ProposalSection.objects.filter(
            proposal=proposal,
            section_type=VA_SECTION_TYPE,
        ).first()
        if va and isinstance(va.content_json, dict):
            if _merge_missing_conditions(va.content_json, va_default_cj):
                va.save(update_fields=['content_json'])


def remove_module(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    ProposalDefaultConfig = apps.get_model('content', 'ProposalDefaultConfig')

    to_update = []
    for section in ProposalSection.objects.filter(section_type=FR_SECTION_TYPE):
        content = section.content_json or {}
        modules = content.get('additionalModules') or []
        filtered = [m for m in modules if m.get('id') != MODULE_ID]
        if len(filtered) != len(modules):
            content['additionalModules'] = filtered
            section.content_json = content
            to_update.append(section)
    if to_update:
        ProposalSection.objects.bulk_update(
            to_update, ['content_json'], batch_size=100)

    for cfg in ProposalDefaultConfig.objects.all():
        sections = cfg.sections_json or []
        changed = False
        for section in sections:
            if section.get('section_type') != FR_SECTION_TYPE:
                continue
            content = section.get('content_json') or {}
            modules = content.get('additionalModules') or []
            filtered = [m for m in modules if m.get('id') != MODULE_ID]
            if len(filtered) != len(modules):
                content['additionalModules'] = filtered
                section['content_json'] = content
                changed = True
        if changed:
            cfg.sections_json = sections
            cfg.save(update_fields=['sections_json'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0155_expenserecord_pocket_movement'),
    ]

    operations = [
        migrations.RunPython(backfill, remove_module),
    ]
