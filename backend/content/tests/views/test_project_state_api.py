import pytest
from django.contrib.auth import get_user_model

from accounts.models import Project, UserProfile
from content.models import DocumentState, DocumentStateGroup

pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def client_profile():
    user = User.objects.create_user(
        username='lifecycle-client@example.com',
        email='lifecycle-client@example.com',
        password='pass12345',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


@pytest.fixture
def project(client_profile):
    return Project.objects.create(
        name='Proyecto de estados',
        client=client_profile.user,
    )


def state(key):
    return DocumentState.objects.get(
        catalog=DocumentStateGroup.Catalog.PROJECTS,
        system_key=key,
    )


def test_project_catalog_exposes_the_seven_seed_states(admin_client):
    response = admin_client.get('/api/project-states/')

    assert response.status_code == 200
    assert [item['system_key'] for item in response.data] == [
        'development',
        'active',
        'evolving',
        'paused',
        'suspended',
        'completed',
        'decommissioned',
    ]
    evolving = response.data[2]
    assert evolving['description'].startswith('Está en producción')
    assert evolving['operational_effect'] == 'operating'
    assert 'cobros' in evolving['operational_effect_help']
    visibility = {
        item['system_key']: item['show_in_document_manager']
        for item in response.data
    }
    assert visibility == {
        'development': True,
        'active': True,
        'evolving': True,
        'paused': False,
        'suspended': False,
        'completed': False,
        'decommissioned': False,
    }


def test_user_can_create_a_project_state_with_an_operational_effect(
    admin_client,
):
    response = admin_client.post('/api/project-states/', {
        'name': 'En garantía',
        'description': 'Opera con acompañamiento posterior a la entrega.',
        'color': 'purple',
        'operational_effect': 'operating',
    }, format='json')

    assert response.status_code == 201, response.data
    assert response.data['catalog'] == 'projects'
    assert response.data['description'] == (
        'Opera con acompañamiento posterior a la entrega.'
    )
    assert response.data['operational_effect'] == 'operating'


def test_user_configures_project_folder_visibility(admin_client):
    created = admin_client.post('/api/project-states/', {
        'name': 'En garantía visible',
        'description': 'Opera mientras recibe acompañamiento de garantía.',
        'color': 'purple',
        'operational_effect': 'operating',
        'show_in_document_manager': True,
    }, format='json')

    assert created.status_code == 201, created.data
    assert created.data['show_in_document_manager'] is True


def test_project_state_requires_a_help_description(admin_client):
    response = admin_client.post('/api/project-states/', {
        'name': 'En garantía',
        'description': '   ',
        'color': 'purple',
        'operational_effect': 'operating',
    }, format='json')

    assert response.status_code == 400
    assert response.data['description'] == [
        'Explica qué significa este estado para quien lo elige.'
    ]


def test_project_state_operational_effect_is_immutable(admin_client):
    custom = admin_client.post('/api/project-states/', {
        'name': 'En garantía',
        'description': 'Opera con acompañamiento posterior a la entrega.',
        'color': 'purple',
        'operational_effect': 'operating',
    }, format='json').data

    response = admin_client.patch(
        f"/api/project-states/{custom['id']}/",
        {'operational_effect': 'suspended'},
        format='json',
    )

    assert response.status_code == 409
    assert response.data['code'] == 'state_effect_immutable'
    assert DocumentState.objects.get(pk=custom['id']).operational_effect == 'operating'


def test_new_project_defaults_to_development_with_history(
    admin_client, client_profile,
):
    response = admin_client.post('/api/projects/create/', {
        'name': 'Proyecto nuevo',
        'client_profile_id': client_profile.pk,
    }, format='json')

    assert response.status_code == 201, response.data
    assert response.data['status'] == 'development'
    assert response.data['current_state']['name'] == 'En desarrollo'
    history = admin_client.get(
        f"/api/projects/{response.data['id']}/state-history/",
    )
    assert history.status_code == 200
    assert history.data[0]['state']['system_key'] == 'development'


def test_transition_api_previews_and_records_a_manual_change(
    admin_client, project,
):
    target = state('suspended')
    preview = admin_client.post(
        f'/api/projects/{project.pk}/state-transitions/preview/',
        {'state_id': target.pk},
        format='json',
    )

    assert preview.status_code == 200, preview.data
    applied = admin_client.post(
        f'/api/projects/{project.pk}/state-transitions/',
        {
            'state_id': target.pk,
            'impact_token': preview.data['impact_token'],
            'effective_at': preview.data['effective_at'],
            'note': 'Hosting detenido mientras el cliente se pone al día.',
        },
        format='json',
    )

    assert applied.status_code == 200, applied.data
    assert applied.data['project']['status'] == 'suspended'
    history = admin_client.get(
        f'/api/projects/{project.pk}/state-history/',
    )
    assert [item['state']['system_key'] for item in history.data] == [
        'suspended',
        'development',
    ]


def test_evolving_keeps_operating_effect_with_distinct_history(
    admin_client, project,
):
    target = state('evolving')
    preview = admin_client.post(
        f'/api/projects/{project.pk}/state-transitions/preview/',
        {'state_id': target.pk},
        format='json',
    )

    applied = admin_client.post(
        f'/api/projects/{project.pk}/state-transitions/',
        {
            'state_id': target.pk,
            'impact_token': preview.data['impact_token'],
            'effective_at': preview.data['effective_at'],
        },
        format='json',
    )

    assert applied.status_code == 200, applied.data
    assert applied.data['project']['status'] == 'evolving'
    assert applied.data['project']['current_state']['operational_effect'] == 'operating'
    project.refresh_from_db()
    assert project.status == Project.STATUS_ACTIVE
    history = admin_client.get(
        f'/api/projects/{project.pk}/state-history/',
    )
    assert history.data[0]['state']['system_key'] == 'evolving'


def test_direct_decommission_api_requires_a_note(admin_client, project):
    target = state('decommissioned')
    preview = admin_client.post(
        f'/api/projects/{project.pk}/state-transitions/preview/',
        {'state_id': target.pk},
        format='json',
    )

    response = admin_client.post(
        f'/api/projects/{project.pk}/state-transitions/',
        {
            'state_id': target.pk,
            'impact_token': preview.data['impact_token'],
            'effective_at': preview.data['effective_at'],
        },
        format='json',
    )

    assert response.status_code == 400
    assert response.data['code'] == 'direct_decommission_note_required'


def test_listing_meta_counts_every_catalog_state(admin_client, project):
    response = admin_client.get('/api/projects/', {'scope': 'all'})

    assert response.status_code == 200
    counts = {
        item['system_key']: item['count']
        for item in response.data['meta']['by_state']
    }
    assert counts['development'] == 1
    assert set(counts) == {
        'development', 'active', 'evolving', 'paused', 'suspended',
        'completed', 'decommissioned',
    }
    evolving = next(
        item for item in response.data['meta']['by_state']
        if item['system_key'] == 'evolving'
    )
    assert evolving['count'] == 0
    assert evolving['description'].startswith('Está en producción')
