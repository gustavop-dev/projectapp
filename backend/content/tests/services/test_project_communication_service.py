"""Ciclo de vida de la comunicación madre de un proyecto."""
import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model

from content.models import CommunicationThread
from content.services.client_communication_service import adopt_client_thread
from content.services.project_communication_service import (
    ProjectCommunicationThreadUnavailable,
    ensure_project_thread,
    require_project_thread,
    synchronize_existing_project_thread,
)


pytestmark = pytest.mark.django_db
User = get_user_model()


def make_client(email):
    user = User.objects.create_user(
        username=email, email=email, password='testpass123', first_name='Ana',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


def test_project_creation_provisions_one_mother_thread():
    client = make_client('provision@example.com')

    project = Project.objects.create(name='Portal Provision', client=client.user)

    thread = CommunicationThread.objects.get(managed_project=project)
    assert thread.title == 'Portal Provision'
    assert thread.client_id == client.pk
    assert thread.project_id == project.pk
    assert thread.thread_kind == 'project'


def test_ensure_is_idempotent():
    client = make_client('idempotent@example.com')
    project = Project.objects.create(name='Portal Idempotente', client=client.user)

    ensure_project_thread(project)
    ensure_project_thread(project)

    assert CommunicationThread.objects.filter(managed_project=project).count() == 1


def test_renaming_the_project_renames_its_mother_thread():
    client = make_client('rename@example.com')
    project = Project.objects.create(name='Nombre viejo', client=client.user)

    project.name = 'Nombre nuevo'
    project.save(update_fields=['name'])

    assert CommunicationThread.objects.get(managed_project=project).title == 'Nombre nuevo'


def test_a_project_whose_client_has_no_profile_is_skipped_not_crashed():
    """El post_save de Project no puede reventar por un cliente sin perfil."""
    user = User.objects.create_user(
        username='profileless@example.com', email='profileless@example.com',
        password='testpass123',
    )
    UserProfile.objects.filter(user=user).delete()

    project = Project.objects.create(name='Sin perfil', client=user)

    assert CommunicationThread.objects.filter(managed_project=project).count() == 0


def test_an_admin_owner_does_not_get_a_mother_thread():
    """`client` del hilo exige rol cliente: un admin no puede ser dueño."""
    user = User.objects.create_user(
        username='adminowner@example.com', email='adminowner@example.com',
        password='testpass123',
    )
    UserProfile.objects.update_or_create(
        user=user, defaults={'role': UserProfile.ROLE_ADMIN},
    )

    project = Project.objects.create(name='De un admin', client=user)

    assert ensure_project_thread(project) is None


def test_updating_a_historical_project_never_provisions_a_missing_thread():
    client = make_client('historical@example.com')
    project = Project.objects.create(name='Historico', client=client.user)
    CommunicationThread.objects.filter(managed_project=project).delete()

    assert synchronize_existing_project_thread(project) is None
    assert CommunicationThread.objects.filter(managed_project=project).count() == 0


def test_require_reports_instead_of_provisioning_silently():
    client = make_client('require@example.com')
    project = Project.objects.create(name='Requerido', client=client.user)
    CommunicationThread.objects.filter(managed_project=project).delete()

    with pytest.raises(ProjectCommunicationThreadUnavailable):
        require_project_thread(project)


def test_deleting_the_project_leaves_the_thread_as_manual():
    client = make_client('deleted@example.com')
    project = Project.objects.create(name='Se borra', client=client.user)
    thread = CommunicationThread.objects.get(managed_project=project)

    project.delete()
    thread.refresh_from_db()

    # SET_NULL en las dos puntas: la conversación sobrevive, degradada a suelta.
    assert thread.managed_project_id is None
    assert thread.thread_kind == 'manual'


def test_client_thread_adoption_requires_a_projectless_thread():
    client = make_client('adopt@example.com')
    project = Project.objects.create(name='Con proyecto', client=client.user)
    root = CommunicationThread.objects.get(managed_project=project)

    with pytest.raises(ValueError, match='madre de un proyecto'):
        adopt_client_thread(root, client)


def test_client_thread_adoption_marks_the_thread(admin_user):
    from content.services import communication_service

    client = make_client('adopt-ok@example.com')
    thread = communication_service.create_thread(
        actor=admin_user, client=client, title='General',
    )

    adopted = adopt_client_thread(thread, client)

    assert adopted.managed_client_id == client.pk
    assert adopted.thread_kind == 'client'


def test_a_client_cannot_have_two_mother_threads(admin_user):
    from content.services import communication_service

    client = make_client('two-roots@example.com')
    first = communication_service.create_thread(
        actor=admin_user, client=client, title='Primera',
    )
    second = communication_service.create_thread(
        actor=admin_user, client=client, title='Segunda',
    )
    adopt_client_thread(first, client)

    with pytest.raises(ValueError, match='ya tiene la comunicación madre'):
        adopt_client_thread(second, client)
