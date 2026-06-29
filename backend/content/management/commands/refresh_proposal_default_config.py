"""Surgically patch ProposalDefaultConfig.sections_json from code DEFAULT_SECTIONS.

The DB-backed ``ProposalDefaultConfig.sections_json`` is the live template that
seeds every new proposal (``get_default_sections``). It is an old snapshot of the
code ``DEFAULT_SECTIONS`` / ``DEFAULT_SECTIONS_EN`` and has drifted. Rather than
overwriting the whole snapshot (which would also revert unrelated sections that
have merely evolved in code), this command patches ONLY the fields this change
cares about, copying their current values from code:

  - investment.hostingPlan.billingTiers   (annual/semiannual/quarterly, no monthly)
  - investment.hostingPlan.renewalNote     (new SMLMV + 8% formula)
  - corporate_branding_module.selected / default_selected = True
  - reports_alerts_module.title/description/items          (Telegram removed)
  - dark_mode_module.title/description                     (renamed)

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
