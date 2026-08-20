"""Surgically patch ProposalDefaultConfig.sections_json from code DEFAULT_SECTIONS.

The DB-backed ``ProposalDefaultConfig.sections_json`` is the live template that
seeds every new proposal (``get_default_sections``). It is an old snapshot of the
code ``DEFAULT_SECTIONS`` / ``DEFAULT_SECTIONS_EN`` and has drifted. Rather than
overwriting the whole snapshot (which would also revert unrelated sections that
have merely evolved in code), this command patches ONLY the fields this change
cares about, copying their current values from code:

  - investment.hostingPlan.billingTiers   (nine-month/semiannual/quarterly, no monthly)
  - investment.hostingPlan.renewalNote     (new SMLMV + 8% formula)
  - corporate_branding_module.selected / default_selected = True
  - reports_alerts_module.title/description/items          (Telegram removed)
  - dark_mode_module.title/description                     (renamed)
  - free modules title/description/items                   (scope caps: analytics 6
    reports, KPI dashboard 8 KPIs / 4 charts / 5 alerts, manual 15 articles + 1
    update, admin listed managers only, AI automation one (1) process)
  - value_added_modules.conditions                         (per-module terms with caps)
  - value_added_modules.module_ids                         (display order)
  - features group title/description/items                 (atomic Google auth:
    registration and sign-in as two separate items)
  - functional_requirements groups/additionalModules       (default entries the
    stored snapshot predates are re-injected in code order; stored entries win
    per id, so operator customizations survive)

Everything else in sections_json is left untouched.

Usage:
    python manage.py refresh_proposal_default_config            # dry-run
    python manage.py refresh_proposal_default_config --apply    # writes + backup
    python manage.py refresh_proposal_default_config --language es --apply
"""
import copy
import json
import os

from django.core.management.base import BaseCommand

from content.models import ProposalDefaultConfig
from content.services.proposal_service import (
    DEFAULT_SECTIONS,
    DEFAULT_SECTIONS_EN,
)

PATCHED_MODULE_IDS = (
    'corporate_branding_module',
    'reports_alerts_module',
    'dark_mode_module',
    'admin_module',
    'analytics_dashboard',
    'kpi_dashboard_module',
    'manual_module',
    'ai_automation_module',
    'features',
)


def _code_sections(language):
    source = DEFAULT_SECTIONS_EN if language == 'en' else DEFAULT_SECTIONS
    return copy.deepcopy(source)


def _section(sections, section_type):
    for s in (sections or []):
        if isinstance(s, dict) and s.get('section_type') == section_type:
            return s
    return None


def _module(section, module_id):
    cj = (section or {}).get('content_json') or {}
    for arr in ('groups', 'additionalModules'):
        for g in (cj.get(arr) or []):
            if isinstance(g, dict) and g.get('id') == module_id:
                return g
    return None


def _reinject_missing_fr_entries(fr, code_fr):
    """Re-inject default FR groups/modules the stored config predates.

    Only runs when an id from code is absent in the stored array. The array is
    then rebuilt following code order: the stored entry wins per id (operator
    customizations survive), code fills the gaps, and stored-only extras keep
    their relative order at the end. With nothing missing the stored array is
    left untouched, order included.
    """
    changes = []
    cj = (fr or {}).get('content_json')
    code_cj = (code_fr or {}).get('content_json')
    if not isinstance(cj, dict) or not isinstance(code_cj, dict):
        return changes

    for arr in ('groups', 'additionalModules'):
        stored = [g for g in (cj.get(arr) or []) if isinstance(g, dict)]
        code_list = [
            g for g in (code_cj.get(arr) or [])
            if isinstance(g, dict) and g.get('id')
        ]
        if not code_list:
            continue
        stored_by_id = {g.get('id'): g for g in stored if g.get('id')}
        code_ids = [g['id'] for g in code_list]
        missing = [gid for gid in code_ids if gid not in stored_by_id]
        if not missing:
            continue
        rebuilt = [
            stored_by_id.get(g['id']) or copy.deepcopy(g) for g in code_list
        ]
        rebuilt += [
            g for g in stored
            if not g.get('id') or g.get('id') not in set(code_ids)
        ]
        cj[arr] = rebuilt
        changes.append(
            f'functional_requirements.{arr}: re-injected missing {missing}')
    return changes


def _patch(sections, code):
    """Mutate *sections* in place with the targeted fields from *code*.

    Returns a list of human-readable change descriptions.
    """
    changes = []

    # --- investment hosting plan ---
    inv, code_inv = _section(sections, 'investment'), _section(code, 'investment')
    hp = (inv or {}).get('content_json', {}).get('hostingPlan') if inv else None
    code_hp = (code_inv or {}).get('content_json', {}).get('hostingPlan') if code_inv else None
    if isinstance(hp, dict) and isinstance(code_hp, dict):
        old_tiers = [t.get('frequency') for t in (hp.get('billingTiers') or [])
                     if isinstance(t, dict)]
        new_tiers = copy.deepcopy(code_hp.get('billingTiers') or [])
        if hp.get('billingTiers') != new_tiers:
            hp['billingTiers'] = new_tiers
            changes.append(
                f"hosting billingTiers {old_tiers} -> "
                f"{[t.get('frequency') for t in new_tiers]}")
        if 'renewalNote' in code_hp and hp.get('renewalNote') != code_hp['renewalNote']:
            hp['renewalNote'] = code_hp['renewalNote']
            changes.append('hosting renewalNote -> new SMLMV+8% formula')
        if 'coverageNote' in code_hp and hp.get('coverageNote') != code_hp['coverageNote']:
            hp['coverageNote'] = code_hp['coverageNote']
            changes.append('hosting coverageNote -> code')

    # --- functional_requirements modules ---
    fr = _section(sections, 'functional_requirements')
    code_fr = _section(code, 'functional_requirements')
    changes += _reinject_missing_fr_entries(fr, code_fr)
    for mid in PATCHED_MODULE_IDS:
        g, code_g = _module(fr, mid), _module(code_fr, mid)
        if not isinstance(g, dict) or not isinstance(code_g, dict):
            continue
        if mid == 'corporate_branding_module':
            if not (g.get('selected') and g.get('default_selected')):
                g['selected'] = True
                g['default_selected'] = True
                changes.append(f'{mid}.selected -> True')
        else:
            for field in ('title', 'description', 'items'):
                if field in code_g and g.get(field) != code_g[field]:
                    g[field] = copy.deepcopy(code_g[field])
                    changes.append(f'{mid}.{field} -> code')

    # --- value_added_modules conditions (per-module gating/terms) ---
    va = _section(sections, 'value_added_modules')
    code_va = _section(code, 'value_added_modules')
    conds = (va or {}).get('content_json', {}).get('conditions') if va else None
    code_conds = (code_va or {}).get('content_json', {}).get('conditions') if code_va else None
    if isinstance(conds, dict) and isinstance(code_conds, dict):
        for mid, code_cond in code_conds.items():
            if conds.get(mid) != code_cond:
                conds[mid] = copy.deepcopy(code_cond)
                changes.append(f'conditions.{mid} -> code')

    # --- value_added_modules display order ---
    va_cj = (va or {}).get('content_json') if va else None
    code_va_cj = (code_va or {}).get('content_json') if code_va else None
    if isinstance(va_cj, dict) and isinstance(code_va_cj, dict):
        code_ids = code_va_cj.get('module_ids')
        if code_ids and va_cj.get('module_ids') != code_ids:
            old_ids = va_cj.get('module_ids')
            va_cj['module_ids'] = copy.deepcopy(code_ids)
            changes.append(f'module_ids {old_ids} -> {code_ids}')

        # --- value_added_modules general legal provisions ---
        code_general = code_va_cj.get('general_terms')
        if isinstance(code_general, dict) and va_cj.get('general_terms') != code_general:
            va_cj['general_terms'] = copy.deepcopy(code_general)
            changes.append('general_terms -> code')

    # --- commercial_conditions scope clause ---
    # The scope wording was corrected in code but had no sync path, so stored
    # configs kept serving the stale paragraph in the generated PDF.
    cc = _section(sections, 'commercial_conditions')
    code_cc = _section(code, 'commercial_conditions')
    cc_cj = (cc or {}).get('content_json') if cc else None
    code_cc_cj = (code_cc or {}).get('content_json') if code_cc else None
    if isinstance(cc_cj, dict) and isinstance(code_cc_cj, dict):
        for field in ('scopeTitle', 'scopeParagraphs', 'effortBadge'):
            if field in code_cc_cj and cc_cj.get(field) != code_cc_cj[field]:
                cc_cj[field] = copy.deepcopy(code_cc_cj[field])
                changes.append(f'commercial_conditions.{field} -> code')

    return changes


class Command(BaseCommand):
    help = 'Surgically patch ProposalDefaultConfig.sections_json from code defaults.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Write the changes (default: dry-run).')
        parser.add_argument('--language', choices=['es', 'en'], default=None,
                            help='Only this language (default: all configs).')
        parser.add_argument('--backup-dir', default=None,
                            help='Directory for JSON backups (default: cwd).')

    def handle(self, *args, **opts):
        apply = opts['apply']
        backup_dir = opts['backup_dir'] or os.getcwd()
        qs = ProposalDefaultConfig.objects.all()
        if opts['language']:
            qs = qs.filter(language=opts['language'])

        if not qs.exists():
            self.stdout.write('No ProposalDefaultConfig rows found. '
                              'New proposals already use code DEFAULT_SECTIONS.')
            return

        for config in qs:
            lang = config.language
            current = copy.deepcopy(config.sections_json or [])
            code = _code_sections(lang)
            changes = _patch(current, code)

            self.stdout.write(self.style.MIGRATE_HEADING(
                f'\n=== config language={lang} ==='))
            if not changes:
                self.stdout.write('  already up to date — nothing to patch.')
                continue
            for c in changes:
                self.stdout.write(f'  • {c}')

            if not apply:
                continue

            backup_path = os.path.join(
                backup_dir, f'proposal_default_config_{lang}.backup.json')
            with open(backup_path, 'w', encoding='utf-8') as fh:
                json.dump(config.sections_json or [], fh,
                          ensure_ascii=False, indent=2)
            config.sections_json = current
            config.save(update_fields=['sections_json'])
            self.stdout.write(self.style.SUCCESS(
                f'  ✅ applied {len(changes)} change(s). backup -> {backup_path}'))

        if not apply:
            self.stdout.write(self.style.WARNING(
                '\nDry-run only. Re-run with --apply to write the changes.'))
