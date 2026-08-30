from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import Project, UserProfile
from content.services import communication_service


pytestmark = pytest.mark.django_db
User = get_user_model()
OCCURRED_AT = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)


def make_client(email, name):
    user = User.objects.create_user(
        username=email,
        email=email,
        first_name=name,
        password='testpass123',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


def make_message(thread, actor, **overrides):
    return communication_service.create_message(
        thread=thread,
        actor=actor,
        channel=overrides.get('channel', 'whatsapp'),
        direction=overrides.get('direction', 'outgoing'),
        status=overrides.get('status', 'sent'),
        subject=overrides.get('subject', ''),
        content=overrides.get('content', 'Seguimiento'),
        occurred_at=overrides.get('occurred_at', OCCURRED_AT),
    )


def test_multi_value_dimensions_use_or_within_each_filter(admin_client, admin_user):
    first = make_client('first-filter@example.com', 'Ana')
    second = make_client('second-filter@example.com', 'Bea')
    project = Project.objects.create(name='Portal Ana', client=first.user)
    projected = communication_service.create_thread(
        actor=admin_user, client=first, project=project, title='WhatsApp',
    )
    unassigned = communication_service.create_thread(
        actor=admin_user, client=second, title='Correo',
    )
    make_message(projected, admin_user, channel='whatsapp', status='draft')
    make_message(
        unassigned, admin_user, channel='email', subject='Entrega',
        occurred_at=OCCURRED_AT + timedelta(hours=1),
    )

    response = admin_client.get(reverse('communication-threads'), {
        'channel': 'whatsapp,email',
        'message_status': 'draft,sent',
    })

    assert response.status_code == 200
    assert {row['title'] for row in response.data['results']} == {'WhatsApp', 'Correo'}
    assert response.data['facets']['without_project_count'] == 1
    assert response.data['facets']['projects'][0]['count'] == 1
    assert {row['count'] for row in response.data['facets']['clients']} == {1}


def test_message_dimensions_must_match_the_same_message(admin_client, admin_user):
    client = make_client('correlated@example.com', 'Carla')
    thread = communication_service.create_thread(
        actor=admin_user, client=client, title='Canales separados',
    )
    make_message(thread, admin_user, channel='whatsapp', direction='outgoing')
    make_message(
        thread,
        admin_user,
        channel='email',
        direction='incoming',
        status='received',
        subject='Respuesta',
    )

    response = admin_client.get(reverse('communication-threads'), {
        'channel': 'whatsapp', 'direction': 'incoming',
    })

    assert response.status_code == 200
    assert response.data['results'] == []


def test_project_none_keeps_unassigned_threads_reachable(admin_client, admin_user):
    client = make_client('unassigned@example.com', 'Diana')
    project = Project.objects.create(name='Proyecto', client=client.user)
    communication_service.create_thread(
        actor=admin_user, client=client, project=project, title='Con proyecto',
    )
    communication_service.create_thread(
        actor=admin_user, client=client, title='Sin proyecto',
    )

    response = admin_client.get(
        reverse('communication-threads'), {'project': 'none'},
    )

    assert response.status_code == 200
    assert [row['title'] for row in response.data['results']] == ['Sin proyecto']


def test_project_name_search_scopes_the_list_contract(admin_client, admin_user):
    client = make_client('project-search@example.com', 'Estela')
    matching_project = Project.objects.create(
        name='Portal Boreal', client=client.user,
    )
    other_project = Project.objects.create(
        name='Tienda Austral', client=client.user,
    )
    communication_service.create_thread(
        actor=admin_user,
        client=client,
        project=matching_project,
        title='Revisión de alcance',
    )
    communication_service.create_thread(
        actor=admin_user,
        client=client,
        project=other_project,
        title='Revisión de alcance',
    )

    response = admin_client.get(
        reverse('communication-threads'), {'q': 'boreal'},
    )

    assert response.status_code == 200
    assert [row['project_name'] for row in response.data['results']] == ['Portal Boreal']
    assert response.data['facets']['total'] == 1
    assert response.data['facets']['navigation_total'] == 1
    assert response.data['facets']['projects'] == [{
        'id': matching_project.id,
        'name': 'Portal Boreal',
        'client_id': client.id,
        'count': 1,
        'unavailable': False,
    }]


def test_facets_exclude_their_own_dimension(admin_client, admin_user):
    client = make_client('facets@example.com', 'Elena')
    whatsapp = communication_service.create_thread(
        actor=admin_user, client=client, title='WhatsApp',
    )
    email = communication_service.create_thread(
        actor=admin_user, client=client, title='Email',
    )
    make_message(whatsapp, admin_user, channel='whatsapp')
    make_message(email, admin_user, channel='email', subject='Estado')

    response = admin_client.get(
        reverse('communication-threads'), {'channel': 'whatsapp'},
    )

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['facets']['filters']['channel'] == {
        'email': 1, 'whatsapp': 1,
    }


def test_invalid_multi_value_token_returns_field_error(admin_client):
    response = admin_client.get(
        reverse('communication-threads'), {'status': 'open,unknown'},
    )

    assert response.status_code == 400
    assert 'unknown' in response.data['status']


def test_oldest_order_is_stable(admin_client, admin_user):
    client = make_client('order@example.com', 'Fabio')
    older = communication_service.create_thread(
        actor=admin_user, client=client, title='Viejo',
    )
    newer = communication_service.create_thread(
        actor=admin_user, client=client, title='Nuevo',
    )
    older.last_activity_at = OCCURRED_AT
    older.save(update_fields=['last_activity_at'])
    newer.last_activity_at = OCCURRED_AT + timedelta(days=1)
    newer.save(update_fields=['last_activity_at'])

    response = admin_client.get(
        reverse('communication-threads'), {'order': 'oldest'},
    )

    assert response.status_code == 200
    assert [row['title'] for row in response.data['results']] == ['Viejo', 'Nuevo']
