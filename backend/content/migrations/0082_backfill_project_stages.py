"""
Backfill ProposalProjectStage rows for existing accepted/finished proposals.

For each BusinessProposal already in 'accepted' or 'finished' status, create
two empty stage rows (design + development) so the admin can fill in dates
without having to click "create" first. The daily Huey task safely skips
rows whose start_date / end_date are NULL.

Idempotent: uses get_or_create on (proposal, stage_key) which is unique.
"""

from django.db import migrations


STAGES = [
    ('design', 0),
    ('development', 1),
]
TARGET_STATUSES = ('accepted', 'finished')


def forwards(apps, schema_editor):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalProjectStage = apps.get_model('content', 'ProposalProjectStage')

    proposals = BusinessProposal.objects.filter(status__in=TARGET_STATUSES)
    for proposal in proposals.iterator():
        for stage_key, order in STAGES:
            ProposalProjectStage.objects.get_or_create(
                proposal=proposal,
                stage_key=stage_key,
                defaults={'order': order},
            )


def backwards(apps, schema_editor):
    # Reversing wipes only the empty stage rows we created (no dates set).
    ProposalProjectStage = apps.get_model('content', 'ProposalProjectStage')
    ProposalProjectStage.objects.filter(
        start_date__isnull=True,
        end_date__isnull=True,
        completed_at__isnull=True,
        warning_sent_at__isnull=True,
        last_overdue_reminder_at__isnull=True,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0081_add_proposal_project_stage'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=backwards),
    ]
