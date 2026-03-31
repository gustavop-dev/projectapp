# Data migration: Project.proposal -> BusinessProposal.deliverable + Deliverable row

from django.db import migrations


def forwards(apps, schema_editor):
    Project = apps.get_model('accounts', 'Project')
    Deliverable = apps.get_model('accounts', 'Deliverable')
    BusinessProposal = apps.get_model('content', 'BusinessProposal')

    for project in Project.objects.filter(proposal_id__isnull=False).iterator():
        try:
            bp = BusinessProposal.objects.get(pk=project.proposal_id)
        except BusinessProposal.DoesNotExist:
            continue
        if bp.deliverable_id:
            d = Deliverable.objects.filter(pk=bp.deliverable_id, project_id=project.id).first()
            if d:
                continue
        title = (bp.title or 'Propuesta comercial')[:300]
        d = Deliverable.objects.create(
            project_id=project.id,
            category='documents',
            title=title,
            description='',
            file=None,
            uploaded_by_id=project.client_id,
        )
        bp.deliverable_id = d.id
        bp.save(update_fields=['deliverable_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_deliverable_optional_file_epic_meta_and_file_model'),
        ('content', '0056_businessproposal_deliverable'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='project',
            name='proposal',
        ),
    ]
