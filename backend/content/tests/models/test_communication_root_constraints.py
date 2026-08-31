"""Database invariants for the thread that represents a project or a client."""
import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from content.models import CommunicationThread


pytestmark = pytest.mark.django_db
User = get_user_model()


def make_client(email):
    user = User.objects.create_user(
        username=email, email=email, password='testpass123', first_name='Ana',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


@pytest.fixture
def project_without_thread():
    """Crea el proyecto por SQL para que el post_save no le provisione madre."""
    client = make_client('constraint-owner@example.com')
    Project.objects.bulk_create([Project(name='Proyecto constraint', client=client.user)])
    project = Project.objects.get(name='Proyecto constraint')
    return project, client


def test_managed_project_thread_rejects_another_project(project_without_thread):
    project, client = project_without_thread
    Project.objects.bulk_create([Project(name='Otro constraint', client=client.user)])
    other = Project.objects.get(name='Otro constraint')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CommunicationThread.objects.create(
                title='Madre incoherente',
                client=client,
                project=other,
                managed_project=project,
            )


def test_managed_client_thread_rejects_another_client(project_without_thread):
    _project, client = project_without_thread
    other = make_client('other-constraint@example.com')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CommunicationThread.objects.create(
                title='Madre de otro',
                client=other,
                managed_client=client,
            )


def test_managed_thread_rejects_archiving(project_without_thread):
    project, client = project_without_thread

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CommunicationThread.objects.create(
                title='Madre archivada',
                client=client,
                project=project,
                managed_project=project,
                is_archived=True,
            )


def test_a_thread_cannot_represent_a_project_and_a_client_at_once(project_without_thread):
    project, client = project_without_thread

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CommunicationThread.objects.create(
                title='Madre doble',
                client=client,
                project=project,
                managed_project=project,
                managed_client=client,
            )


def test_thread_kind_names_the_three_classes(project_without_thread):
    project, client = project_without_thread
    manual = CommunicationThread.objects.create(title='Suelto', client=client)
    project_root = CommunicationThread.objects.create(
        title='Madre de proyecto', client=client, project=project,
        managed_project=project,
    )
    client_root = CommunicationThread.objects.create(
        title='Madre de cliente', client=client, managed_client=client,
    )

    assert manual.thread_kind == 'manual'
    assert project_root.thread_kind == 'project'
    assert client_root.thread_kind == 'client'
