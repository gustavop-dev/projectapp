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
        reply_to=overrides.get('reply_to'),
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


def test_unanswered_reply_status_excludes_threads_with_active_reply(
    admin_client, admin_user,
):
    client = make_client('reply-filter@example.com', 'Fabiola')
    pending = communication_service.create_thread(
        actor=admin_user, client=client, title='Pendiente',
    )
    answered = communication_service.create_thread(
        actor=admin_user, client=client, title='Respondido',
    )
    make_message(pending, admin_user)
    sent = make_message(answered, admin_user)
    make_message(
        answered,
        admin_user,
        direction='incoming',
        status='received',
        reply_to=sent,
    )

    response = admin_client.get(
        reverse('communication-threads'), {'reply_status': 'unanswered'},
    )

    assert response.status_code == 200
    assert [row['title'] for row in response.data['results']] == ['Pendiente']


def test_answered_reply_status_ignores_voided_replies(admin_client, admin_user):
    client = make_client('voided-reply@example.com', 'Gabriela')
    thread = communication_service.create_thread(
        actor=admin_user, client=client, title='Respuesta anulada',
    )
    sent = make_message(thread, admin_user)
    reply = make_message(
        thread,
        admin_user,
        direction='incoming',
        status='received',
        reply_to=sent,
    )
    communication_service.void_message(reply, actor=admin_user, reason='Duplicada')

    response = admin_client.get(
        reverse('communication-threads'), {'reply_status': 'answered'},
    )

    assert response.status_code == 200
    assert response.data['results'] == []


def test_reply_status_facet_includes_honest_zero(admin_client, admin_user):
    client = make_client('reply-facet@example.com', 'Helena')
    thread = communication_service.create_thread(
        actor=admin_user, client=client, title='Sin respuesta',
    )
    make_message(thread, admin_user)

    response = admin_client.get(reverse('communication-threads'))

    assert response.status_code == 200
    assert response.data['facets']['filters']['reply_status'] == {
        'answered': 0,
        'unanswered': 1,
    }


def test_tab_counts_include_zero_for_the_full_dataset(admin_client, admin_user):
    client = make_client('tab-counts@example.com', 'Isabel')
    thread = communication_service.create_thread(
        actor=admin_user, client=client, title='Borrador',
    )
    make_message(thread, admin_user, status='draft')

    response = admin_client.post(
        reverse('communication-thread-tab-counts'),
        {
            'tabs': [
                {'id': 'all', 'filters': {}},
                {'id': 'draft-pending', 'filters': {'message_status': ['draft']}},
                {'id': 'channel-email', 'filters': {'channel': ['email']}},
            ],
        },
        format='json',
    )

    assert response.status_code == 200
    assert response.data['counts'] == {
        'all': 1,
        'draft-pending': 1,
        'channel-email': 0,
    }


def test_tab_counts_reject_invalid_filter_values(admin_client):
    response = admin_client.post(
        reverse('communication-thread-tab-counts'),
        {'tabs': [{'id': 'bad', 'filters': {'reply_status': ['waiting']}}]},
        format='json',
    )

    assert response.status_code == 400
    assert 'waiting' in response.data['reply_status']


def test_tab_counts_reject_non_object_filters(admin_client):
    response = admin_client.post(
        reverse('communication-thread-tab-counts'),
        {'tabs': [{'id': 'bad', 'filters': []}]},
        format='json',
    )

    assert response.status_code == 400
    assert response.data['tabs'] == 'Los filtros de cada pestaña deben ser un objeto.'


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
