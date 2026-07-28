"""Rewrite the value-added module terms as categorised legal clauses.

The terms of the free modules used to be one loose commercial paragraph per
module. They are now a list of categorised clauses (``terms_clauses``:
``[{label, text}]``) plus a section-level ``general_terms`` block, so the client
can tell the nature of each obligation apart — eligibility, scope, term,
third-party dependency, liability.

The same pass also repairs ``commercial_conditions.scopeParagraphs``: the scope
wording was corrected in code (``antes o durante``) but had no sync path, so
stored configurations kept serving the stale paragraph in the generated PDF.

Scope of the rewrite — deliberately narrow:

* ``ProposalDefaultConfig.sections_json`` (one row per language), and
* proposals still in ``draft``.

Proposals already sent, viewed, under negotiation, accepted, rejected, expired
or finished are left untouched: they are commercial documents already delivered
to the client, and their terms must keep reading exactly as they were sent.

Reverse is a no-op — restoring the old commercial wording has no value and we
would not want a downgrade to silently rewrite legal text.
"""
from copy import deepcopy

from django.db import migrations

DRAFT_STATUS = 'draft'


def _defaults_for(lang):
    # Imported lazily so the migration only touches app code at run time.
    from content.services.proposal_service import (
        DEFAULT_SECTIONS,
        DEFAULT_SECTIONS_EN,
    )
    return DEFAULT_SECTIONS_EN if lang == 'en' else DEFAULT_SECTIONS


def _find_section(sections, section_type):
    return next(
        (s for s in (sections or [])
         if isinstance(s, dict) and s.get('section_type') == section_type),
        None,
    )


def _apply_value_added(content_json, default_cj):
    """Copy the clause-shaped terms + general provisions onto a content_json."""
    if not isinstance(content_json, dict) or not isinstance(default_cj, dict):
        return False
    changed = False

    default_conds = default_cj.get('conditions') or {}
    conds = content_json.get('conditions')
    if not isinstance(conds, dict):
        conds = {}
        content_json['conditions'] = conds
    for mid, default_cond in default_conds.items():
        if not isinstance(default_cond, dict):
            continue
        cond = conds.get(mid)
        if not isinstance(cond, dict):
            # Module absent from this proposal: seed the whole entry.
            conds[mid] = deepcopy(default_cond)
            changed = True
            continue
        # Only the legal wording is refreshed. Per-proposal gating that a seller
        # may have tuned (minimums, duration) is preserved as-is.
        for field in ('terms_clauses', 'terms', 'discretionary_note'):
            if field in default_cond and cond.get(field) != default_cond[field]:
                cond[field] = deepcopy(default_cond[field])
                changed = True

    default_general = default_cj.get('general_terms')
    if isinstance(default_general, dict) and \
            content_json.get('general_terms') != default_general:
        content_json['general_terms'] = deepcopy(default_general)
        changed = True

    return changed


def _apply_commercial_conditions(content_json, default_cj):
    """Refresh the scope-of-work clause from code."""
    if not isinstance(content_json, dict) or not isinstance(default_cj, dict):
        return False
    changed = False
    for field in ('scopeTitle', 'scopeParagraphs', 'effortBadge'):
        if field in default_cj and content_json.get(field) != default_cj[field]:
            content_json[field] = deepcopy(default_cj[field])
            changed = True
    return changed


def _patch_sections_json(sections, defaults):
    """Patch a DEFAULT_SECTIONS-shaped list in place. Returns True if changed."""
    if not isinstance(sections, list):
        return False
    changed = False

    va = _find_section(sections, 'value_added_modules')
    va_default = _find_section(defaults, 'value_added_modules')
    if va and va_default:
        changed |= _apply_value_added(
            va.get('content_json'),
            (va_default.get('content_json') or {}),
        )

    cc = _find_section(sections, 'commercial_conditions')
    cc_default = _find_section(defaults, 'commercial_conditions')
    if cc and cc_default:
        changed |= _apply_commercial_conditions(
            cc.get('content_json'),
            (cc_default.get('content_json') or {}),
        )

    return changed


def apply_legal_terms(apps, _schema_editor):
    ProposalDefaultConfig = apps.get_model('content', 'ProposalDefaultConfig')
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalSection = apps.get_model('content', 'ProposalSection')

    # 1) Admin-editable defaults, one row per language.
    for config in ProposalDefaultConfig.objects.all():
        lang = getattr(config, 'language', 'es') or 'es'
        sections = config.sections_json
        if _patch_sections_json(sections, _defaults_for(lang)):
            config.sections_json = sections
            config.save(update_fields=['sections_json'])

    # 2) Draft proposals only — anything already sent keeps its wording.
    drafts = BusinessProposal.objects.filter(status=DRAFT_STATUS)
    for proposal in drafts.iterator():
        lang = getattr(proposal, 'language', 'es') or 'es'
        defaults = _defaults_for(lang)
        va_default_cj = (_find_section(defaults, 'value_added_modules') or {}).get(
            'content_json', {}) or {}
        cc_default_cj = (_find_section(defaults, 'commercial_conditions') or {}).get(
            'content_json', {}) or {}

        sections = ProposalSection.objects.filter(
            proposal=proposal,
            section_type__in=('value_added_modules', 'commercial_conditions'),
        )
        for section in sections:
            if not isinstance(section.content_json, dict):
                continue
            content_json = section.content_json
            if section.section_type == 'value_added_modules':
                changed = _apply_value_added(content_json, va_default_cj)
            else:
                changed = _apply_commercial_conditions(content_json, cc_default_cj)
            if changed:
                section.content_json = content_json
                section.save(update_fields=['content_json'])


def noop_reverse(_apps, _schema_editor):
    """Intentionally does nothing — see module docstring."""


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0165_update_default_contract_template_v5'),
    ]

    operations = [
        migrations.RunPython(apply_legal_terms, noop_reverse),
    ]
