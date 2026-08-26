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


def test_project_catalog_exposes_the_six_seed_states(admin_client):
    response = admin_client.get('/api/project-states/')

    assert response.status_code == 200
    assert [item['system_key'] for item in response.data] == [
        'development',
        'active',
        'paused',
        'suspended',
        'completed',
        'decommissioned',
    ]


def test_user_can_create_a_project_state_with_an_operational_effect(
    admin_client,
):
    response = admin_client.post('/api/project-states/', {
        'name': 'En garantía',
        'color': 'purple',
        'operational_effect': 'operating',
    }, format='json')

    assert response.status_code == 201, response.data
    assert response.data['catalog'] == 'projects'
    assert response.data['operational_effect'] == 'operating'


def test_project_state_operational_effect_is_immutable(admin_client):
    custom = admin_client.post('/api/project-states/', {
        'name': 'En garantía',
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
        item['operational_effect']: item['count']
        for item in response.data['meta']['by_state']
    }
    assert counts['development'] == 1
    assert set(counts) == {
        'development', 'operating', 'paused', 'suspended',
        'completed', 'decommissioned',
    }
