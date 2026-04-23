"""Backfill ``BusinessProposal.selected_modules`` for legacy rows.

Before this migration, ``_calculate_effective_total_investment`` and
``default_selected_modules_from_content`` both fell back to the admin's
``selected`` / ``default_selected`` flags in FR content whenever
``selected_modules`` was empty. That fallback hid an ambiguity — an empty
array could mean either "never customized" or "confirmed with zero
modules".

With the gate now on ``has_confirmed_module_selection`` (True iff a
``calc_confirmed`` change log exists), we need legacy rows with that flag
set but an empty list to carry an explicit canonical list so the literal
interpretation preserves their current effective totals.
"""
from django.db import migrations


def backfill(apps, schema_editor):
    from content.services.proposal_service import (
        admin_default_calculator_group_ids,
    )

    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalChangeLog = apps.get_model('content', 'ProposalChangeLog')
    ProposalSection = apps.get_model('content', 'ProposalSection')

    confirmed_ids = set(
        ProposalChangeLog.objects
        .filter(change_type='calc_confirmed')
        .values_list('proposal_id', flat=True)
        .distinct()
    )

    candidates = BusinessProposal.objects.filter(
        id__in=confirmed_ids, selected_modules=[],
    )

    fr_rows = ProposalSection.objects.filter(
        proposal_id__in=candidates.values_list('id', flat=True),
        section_type='functional_requirements',
    ).values_list('proposal_id', 'content_json')
    fr_by_proposal = dict(fr_rows)

    updated = 0
    for proposal in candidates:
        bare_ids = admin_default_calculator_group_ids(fr_by_proposal.get(proposal.id))
        if bare_ids:
            proposal.selected_modules = [f'module-{gid}' for gid in sorted(bare_ids)]
            proposal.save(update_fields=['selected_modules'])
            updated += 1

    if updated:
        print(
            f'[0113_backfill_selected_modules] Backfilled selected_modules '
            f'on {updated} legacy proposal(s).'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0112_rename_remaining_contract_document_references'),
    ]

    operations = [
        migrations.RunPython(backfill, reverse_code=migrations.RunPython.noop),
    ]
