"""Repair the scope-of-work clause on proposals still in draft.

Migration 0167 refreshed ``ProposalDefaultConfig`` and the drafts that existed
at the time, but the JSON/MCP creation path took ``commercialConditions``
verbatim from the payload, so a proposal built from a stale snapshot could
still be born with the superseded wording *after* that migration ran. The
bypass is closed in ``build_proposal_from_json`` /
``apply_proposal_json_update`` (see ``enforce_scope_clause``); this pass fixes
the rows that slipped through in the meantime.

Scope is the same as 0167 and for the same reason: only ``draft`` proposals.
Anything already sent, viewed, negotiated, accepted, rejected, expired or
finished is a commercial document already delivered to a client, and its terms
must keep reading exactly as they were sent.

Reverse is a no-op — restoring superseded legal wording has no value.
"""
from copy import deepcopy

from django.db import migrations

DRAFT_STATUS = 'draft'
SECTION_TYPE = 'commercial_conditions'
SCOPE_FIELDS = ('scopeTitle', 'scopeParagraphs')


def _defaults_for(lang):
    # Imported lazily so the migration only touches app code at run time.
    from content.services.proposal_service import (
        DEFAULT_SECTIONS,
        DEFAULT_SECTIONS_EN,
    )
    return DEFAULT_SECTIONS_EN if lang == 'en' else DEFAULT_SECTIONS


def _default_scope_cj(lang):
    section = next(
        (s for s in _defaults_for(lang)
         if isinstance(s, dict) and s.get('section_type') == SECTION_TYPE),
        None,
    )
    return (section or {}).get('content_json') or {}


def repair_draft_scope_clause(apps, _schema_editor):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalSection = apps.get_model('content', 'ProposalSection')

    for proposal in BusinessProposal.objects.filter(status=DRAFT_STATUS).iterator():
        lang = getattr(proposal, 'language', 'es') or 'es'
        default_cj = _default_scope_cj(lang)
        if not default_cj:
            continue

        sections = ProposalSection.objects.filter(
            proposal=proposal, section_type=SECTION_TYPE,
        )
        for section in sections:
            content_json = section.content_json
            if not isinstance(content_json, dict):
                continue
            changed = False
            for field in SCOPE_FIELDS:
                if field in default_cj and content_json.get(field) != default_cj[field]:
                    content_json[field] = deepcopy(default_cj[field])
                    changed = True
            if changed:
                section.content_json = content_json
                section.save(update_fields=['content_json'])


def noop_reverse(_apps, _schema_editor):
    """Intentionally does nothing — see module docstring."""


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0167_value_added_legal_terms_clauses'),
    ]

    operations = [
        migrations.RunPython(repair_draft_scope_clause, noop_reverse),
    ]
