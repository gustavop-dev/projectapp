"""Archivado de hilos: eje de visibilidad, independiente de abierto/cerrado."""
import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from django.urls import reverse

from content.models import CommunicationThread
from content.services import communication_service


pytestmark = pytest.mark.django_db
User = get_user_model()


def make_client(email):
    user = User.objects.create_user(
        username=email, email=email, password='testpass123', first_name='Ana',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


@pytest.fixture
def archive_context(admin_user):
    client = make_client('archive@example.com')
    project = Project.objects.create(name='Proyecto archivable', client=client.user)
    manual = communication_service.create_thread(
        actor=admin_user, client=client, title='Conversación suelta',
    )
    return {
        'client': client,
        'project': project,
        'manual': manual,
        'root': project.communication_root_thread,
    }


def test_archiving_takes_the_thread_out_of_the_default_listing(
    admin_client, archive_context,
):
    response = admin_client.post(
        reverse('archive-communication-thread', args=[archive_context['manual'].id]),
    )

    assert response.status_code == 200
    assert response.data['is_archived'] is True
    listed = admin_client.get(reverse('communication-threads'))
    assert archive_context['manual'].id not in [
        row['id'] for row in listed.data['results']
    ]


def test_archived_scope_lists_only_archived_threads(admin_client, archive_context):
    admin_client.post(
        reverse('archive-communication-thread', args=[archive_context['manual'].id]),
    )

    response = admin_client.get(
        reverse('communication-threads'), {'scope': 'archived'},
    )

    assert [row['id'] for row in response.data['results']] == [
        archive_context['manual'].id
    ]


def test_all_scope_shows_both_states(admin_client, archive_context):
    admin_client.post(
        reverse('archive-communication-thread', args=[archive_context['manual'].id]),
    )

    response = admin_client.get(reverse('communication-threads'), {'scope': 'all'})

    assert len(response.data['results']) == 2


def test_invalid_scope_is_rejected(admin_client, archive_context):
    response = admin_client.get(
        reverse('communication-threads'), {'scope': 'basura'},
    )

    assert response.status_code == 400
    assert 'scope' in response.data


def test_archiving_is_independent_from_closing(
    admin_client, admin_user, archive_context,
):
    """Cerrar bloquea la escritura; archivar sólo saca de la vista."""
    communication_service.close_thread(archive_context['manual'], actor=admin_user)

    listed = admin_client.get(reverse('communication-threads'))

    # Cerrado y aun asi visible: son dos ejes distintos.
    row = next(
        r for r in listed.data['results'] if r['id'] == archive_context['manual'].id
    )
    assert row['status'] == 'closed'
    assert row['is_archived'] is False


def test_the_project_mother_thread_cannot_be_archived(admin_client, archive_context):
    response = admin_client.post(
        reverse('archive-communication-thread', args=[archive_context['root'].id]),
    )

    assert response.status_code == 400
    assert 'madre' in response.data['detail']
    archive_context['root'].refresh_from_db()
    assert archive_context['root'].is_archived is False


def test_unarchiving_returns_the_thread_to_the_default_listing(
    admin_client, archive_context,
):
    admin_client.post(
        reverse('archive-communication-thread', args=[archive_context['manual'].id]),
    )

    response = admin_client.post(
        reverse('unarchive-communication-thread', args=[archive_context['manual'].id]),
    )

    assert response.status_code == 200
    assert response.data['is_archived'] is False
    listed = admin_client.get(reverse('communication-threads'))
    assert archive_context['manual'].id in [row['id'] for row in listed.data['results']]


def test_facet_counts_follow_the_requested_scope(admin_client, archive_context):
    admin_client.post(
        reverse('archive-communication-thread', args=[archive_context['manual'].id]),
    )

    active = admin_client.get(reverse('communication-threads'))
    archived = admin_client.get(
        reverse('communication-threads'), {'scope': 'archived'},
    )

    # El scope entra como filtro, asi que las facetas se recalculan dentro de el
    # sin necesidad de una estructura de conteos aparte.
    assert active.data['facets']['navigation_total'] == 1
    assert archived.data['facets']['navigation_total'] == 1
    assert archived.data['facets']['without_project_count'] == 1


def test_archived_threads_keep_their_kind(admin_client, admin_user, archive_context):
    thread = CommunicationThread.objects.get(pk=archive_context['manual'].id)
    communication_service.archive_thread(thread, actor=admin_user)

    assert thread.thread_kind == 'manual'
    assert thread.archived_at is not None
