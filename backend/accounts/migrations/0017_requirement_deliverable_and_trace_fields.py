# Requirement -> Deliverable; trace fields for sync

from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


def forwards_assign_deliverable(apps, schema_editor):
    Requirement = apps.get_model('accounts', 'Requirement')
    Deliverable = apps.get_model('accounts', 'Deliverable')
    Project = apps.get_model('accounts', 'Project')
    BusinessProposal = apps.get_model('content', 'BusinessProposal')

    for project in Project.objects.all().iterator():
        reqs = Requirement.objects.filter(project_id=project.id)
        if not reqs.exists():
            continue
        bp_d_ids = list(
            BusinessProposal.objects.filter(
                deliverable_id__isnull=False,
            ).filter(
                deliverable__project_id=project.id,
            ).values_list('deliverable_id', flat=True)
        )
        default_d = None
        if bp_d_ids:
            default_d = Deliverable.objects.filter(
                project_id=project.id, id__in=bp_d_ids,
            ).order_by('id').first()
        if not default_d:
            default_d = Deliverable.objects.filter(project_id=project.id).order_by('id').first()
        if not default_d:
            default_d = Deliverable.objects.create(
                project_id=project.id,
                category='other',
                title='Alcance inicial',
                description='',
                file=None,
                uploaded_by_id=project.client_id,
            )
        reqs.update(deliverable_id=default_d.id)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_migrate_proposal_to_deliverable'),
        ('content', '0056_businessproposal_deliverable'),
    ]

    operations = [
        migrations.AddField(
            model_name='requirement',
            name='deliverable',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='requirements',
                to='accounts.deliverable',
            ),
        ),
        migrations.AddField(
            model_name='requirement',
            name='source_epic_key',
            field=models.CharField(blank=True, db_index=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='requirement',
            name='source_epic_title',
            field=models.CharField(blank=True, default='', max_length=300),
        ),
        migrations.AddField(
            model_name='requirement',
            name='source_flow_key',
            field=models.CharField(blank=True, db_index=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='requirement',
            name='synced_from_proposal',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(forwards_assign_deliverable, noop_reverse),
        migrations.RemoveField(
            model_name='requirement',
            name='project',
        ),
        migrations.AlterField(
            model_name='requirement',
            name='deliverable',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='requirements',
                to='accounts.deliverable',
            ),
        ),
        migrations.AddConstraint(
            model_name='requirement',
            constraint=models.UniqueConstraint(
                condition=~Q(source_flow_key=''),
                fields=('deliverable', 'source_flow_key'),
                name='uniq_requirement_deliverable_flow_key',
            ),
        ),
    ]
