from django.db import migrations


PROJECT_STATES = (
    ('En desarrollo', 'development', 'blue', 'development', 0),
    ('Activo', 'active', 'emerald', 'operating', 1),
    ('Pausado', 'paused', 'yellow', 'paused', 2),
    ('Suspendido', 'suspended', 'orange', 'suspended', 3),
    ('Completado', 'completed', 'purple', 'completed', 4),
    ('Dado de baja', 'decommissioned', 'gray', 'decommissioned', 5),
)


def seed_project_states(apps, schema_editor):
    Project = apps.get_model('accounts', 'Project')
    State = apps.get_model('content', 'DocumentState')
    Episode = apps.get_model('content', 'DocumentStateEpisode')
    Event = apps.get_model('content', 'DocumentStateEpisodeEvent')
    Group = apps.get_model('content', 'DocumentStateGroup')

    group = Group.objects.create(
        catalog='projects',
        name='Ciclo del proyecto',
        selection_mode='exclusive',
        order=0,
    )
    states = {}
    for name, key, color, effect, order in PROJECT_STATES:
        state = State.objects.create(
            catalog='projects',
            name=name,
            normalized_name=name.casefold(),
            slug=key.replace('_', '-'),
            color=color,
            group=group,
            order=order,
            system_key=key,
            operational_effect=effect,
        )
        states[key] = state

    for project in Project.objects.all().iterator():
        state = states.get(project.status)
        project.state_review_required = True
        if state is None:
            project.current_state = None
            project.save(update_fields=('current_state', 'state_review_required'))
            continue
        project.current_state = state
        project.save(update_fields=('current_state', 'state_review_required'))
        episode = Episode.objects.create(
            project=project,
            state=state,
            opened_at=None,
            origin='migration',
        )
        Event.objects.create(
            episode=episode,
            event_type='opened',
            effective_at=None,
            details={
                'origin': 'migration',
                'opening_time_known': False,
                'legacy_status': project.status,
                'review_required': True,
            },
        )


def preserve_project_state_history(apps, schema_editor):
    # Expand/contract migration: state history cannot be compressed back into
    # the legacy choices field without discarding dates and transitions.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0055_project_workflow_state'),
        ('content', '0213_shared_workflow_state_catalog'),
    ]

    operations = [
        migrations.RunPython(
            seed_project_states,
            preserve_project_state_history,
        ),
    ]
