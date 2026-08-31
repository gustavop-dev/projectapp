"""Database invariants for the folder that represents a client."""
import pytest
from accounts.models import Project, UserProfile
from django.db import IntegrityError, transaction

from content.models import DocumentFolder


pytestmark = pytest.mark.django_db


@pytest.fixture
def client_user(django_user_model):
    user = django_user_model.objects.create_user(
        username='client-root@example.com',
        email='client-root@example.com',
        password='pass12345',
    )
    UserProfile.objects.update_or_create(
        user=user, defaults={'role': UserProfile.ROLE_CLIENT},
    )
    return user


def test_managed_client_root_rejects_a_parent(client_user):
    """Falla si una subcarpeta puede representar al cliente."""
    parent = DocumentFolder.objects.create(name='Manual parent')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DocumentFolder.objects.create(
                name='Nested client root',
                parent=parent,
                client_user=client_user,
                managed_client=client_user,
            )


def test_managed_client_root_rejects_another_client(client_user, django_user_model):
    """Falla si la raíz queda apuntando a un cliente distinto del suyo."""
    other = django_user_model.objects.create_user(
        username='other-client@example.com',
        email='other-client@example.com',
        password='pass12345',
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DocumentFolder.objects.create(
                name='Mismatched client root',
                client_user=other,
                managed_client=client_user,
            )


def test_managed_client_root_rejects_archiving(client_user):
    """Falla si la carpeta del cliente puede entrar archivada a la base."""
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DocumentFolder.objects.create(
                name='Archived client root',
                client_user=client_user,
                managed_client=client_user,
                is_archived=True,
            )


def test_a_root_cannot_represent_a_project_and_a_client_at_once(client_user):
    """Falla si una misma raíz intenta ser los dos espacios a la vez."""
    Project.objects.bulk_create([Project(name='Dual root project', client=client_user)])
    project = Project.objects.get(name='Dual root project')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DocumentFolder.objects.create(
                name='Dual managed root',
                project=project,
                managed_project=project,
                client_user=client_user,
                managed_client=client_user,
            )


def test_folder_kind_names_the_client_space(client_user):
    """`folder_kind` distingue las tres clases, no sólo proyecto y manual."""
    manual = DocumentFolder.objects.create(name='Propia')
    client_root = DocumentFolder.objects.create(
        name='Cliente', client_user=client_user, managed_client=client_user,
    )

    assert manual.folder_kind == 'manual'
    assert client_root.folder_kind == 'client'
