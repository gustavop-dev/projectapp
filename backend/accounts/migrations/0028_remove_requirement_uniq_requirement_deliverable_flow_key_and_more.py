import django.db.models.deletion
from django.db import migrations, models


def migrate_to_phase_and_project(apps, schema_editor):
    """Populate Requirement.phase from Requirement.deliverable.business_proposal.project_phases.
    Populate BugReport.project from BugReport.deliverable.project.
    Orphans (no matching phase) keep phase=null.
    """
    Requirement = apps.get_model('accounts', 'Requirement')
    BugReport = apps.get_model('accounts', 'BugReport')
    ProjectPhase = apps.get_model('accounts', 'ProjectPhase')

    # Bugs: every bug has a deliverable, every deliverable has a project.
    for bug in BugReport.objects.select_related('deliverable').all():
        if bug.deliverable_id and bug.deliverable.project_id:
            bug.project_id = bug.deliverable.project_id
            bug.save(update_fields=['project'])

    # Requirements: try via deliverable → business_proposal → matching phase.
    # If no match, leave phase=null (orphan, handled at API level).
    for req in Requirement.objects.select_related('deliverable').all():
        d = req.deliverable
        if d is None:
            continue
        bp_id = getattr(d, 'business_proposal_id', None)
        if not bp_id:
            continue
        phase = ProjectPhase.objects.filter(
            business_proposal_id=bp_id, project_id=d.project_id,
        ).first()
        if phase is not None:
            req.phase_id = phase.id
            req.save(update_fields=['phase'])


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0027_remap_deliverable_categories'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='requirement',
            name='uniq_requirement_deliverable_flow_key',
        ),
        # Add new fields first (nullable, so existing rows are OK).
        migrations.AddField(
            model_name='bugreport',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bug_reports', to='accounts.project'),
        ),
        migrations.AddField(
            model_name='requirement',
            name='phase',
            field=models.ForeignKey(blank=True, help_text='Phase of the project this requirement belongs to.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='requirements', to='accounts.projectphase'),
        ),
        # Populate from the old deliverable FK.
        migrations.RunPython(migrate_to_phase_and_project, noop_reverse),
        # Now drop the legacy deliverable links.
        migrations.RemoveField(
            model_name='bugreport',
            name='deliverable',
        ),
        migrations.RemoveField(
            model_name='requirement',
            name='deliverable',
        ),
        migrations.AlterField(
            model_name='deliverablefile',
            name='category',
            field=models.CharField(choices=[('designs', 'Diseños'), ('documents', 'Documentos'), ('contract', 'Contrato'), ('amendment', 'Otrosí'), ('legal_annex', 'Anexo legal'), ('other', 'Otros')], default='other', max_length=20),
        ),
        migrations.AddConstraint(
            model_name='requirement',
            constraint=models.UniqueConstraint(condition=models.Q(('source_flow_key', ''), _negated=True), fields=('phase', 'source_flow_key'), name='uniq_requirement_phase_flow_key'),
        ),
    ]
