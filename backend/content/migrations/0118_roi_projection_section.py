from django.db import migrations, models
from django.db.models import F


SECTION_TYPE_CHOICES = [
    ('greeting', 'Greeting'),
    ('executive_summary', 'Executive Summary'),
    ('context_diagnostic', 'Context & Diagnostic'),
    ('conversion_strategy', 'Conversion Strategy'),
    ('design_ux', 'Design & UX'),
    ('creative_support', 'Creative Support'),
    ('development_stages', 'Development Stages'),
    ('process_methodology', 'Process Methodology'),
    ('functional_requirements', 'Functional Requirements'),
    ('timeline', 'Timeline'),
    ('investment', 'Investment'),
    ('proposal_summary', 'Proposal Summary'),
    ('final_note', 'Final Note'),
    ('next_steps', 'Next Steps'),
    ('technical_document', 'Technical Document'),
    ('value_added_modules', 'Value Added Modules'),
    ('roi_projection', 'ROI Projection'),
]


_DEFAULTS_BY_LANGUAGE = {}


def _defaults_index(language):
    if language not in _DEFAULTS_BY_LANGUAGE:
        try:
            from content.services.proposal_service import ProposalService
            sections = ProposalService.get_default_sections(language=language)
        except Exception:
            sections = []
        _DEFAULTS_BY_LANGUAGE[language] = {
            cfg['section_type']: cfg for cfg in sections
        }
    return _DEFAULTS_BY_LANGUAGE[language]


def backfill_roi_projection(apps, schema_editor):
    """
    Add a disabled ``roi_projection`` section to every existing proposal.

    The section is created with ``is_enabled=False`` so it does not appear
    in the public view or PDF until an admin enables it and fills the
    KPIs/scenarios. Existing sections at ``order >= 4`` are bumped +1 so
    the new section sits between ``conversion_strategy`` (order=3) and
    ``investment`` (now order=5).
    """
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalSection = apps.get_model('content', 'ProposalSection')

    for proposal in BusinessProposal.objects.all().only('id', 'language'):
        already_has_section = ProposalSection.objects.filter(
            proposal_id=proposal.pk, section_type='roi_projection',
        ).exists()
        if already_has_section:
            continue

        ProposalSection.objects.filter(
            proposal_id=proposal.pk, order__gte=4,
        ).update(order=F('order') + 1)

        language = getattr(proposal, 'language', 'es') or 'es'
        cfg = _defaults_index(language).get('roi_projection')
        if not cfg:
            continue

        ProposalSection.objects.create(
            proposal_id=proposal.pk,
            section_type='roi_projection',
            title=cfg['title'],
            order=cfg['order'],
            is_enabled=False,
            content_json=dict(cfg['content_json']),
            is_wide_panel=cfg.get('is_wide_panel', False),
        )


def remove_roi_projection(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    ProposalSection.objects.filter(section_type='roi_projection').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0117_add_business_proposal_email_intro'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposalsection',
            name='section_type',
            field=models.CharField(choices=SECTION_TYPE_CHOICES, max_length=30),
        ),
        migrations.RunPython(backfill_roi_projection, remove_roi_projection),
    ]
