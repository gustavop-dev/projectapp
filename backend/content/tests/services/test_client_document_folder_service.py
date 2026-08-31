"""Adoption lifecycle of the folder that represents a client."""
import pytest
from accounts.models import Project, UserProfile

from content.models import DocumentFolder
from content.services.client_document_folder_service import (
    ClientFolderAdoptionRequired, adopt_client_folder, require_client_folder,
    synchronize_existing_client_folder,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def client_user(django_user_model):
    user = django_user_model.objects.create_user(
        username='adopt@example.com',
        email='adopt@example.com',
        password='pass12345',
    )
    UserProfile.objects.update_or_create(
        user=user, defaults={'role': UserProfile.ROLE_CLIENT},
    )
    return user


def test_adoption_marks_the_root_and_leaves_its_content_in_place(client_user):
    root = DocumentFolder.objects.create(name='Littigio', client_user=client_user)
    child = DocumentFolder.objects.create(name='Contratos', parent=root)

    adopted = adopt_client_folder(root, client_user)
    child.refresh_from_db()

    assert adopted.managed_client_id == client_user.pk
    assert adopted.folder_kind == 'client'
    assert adopted.parent_id is None
    # El subárbol hereda al cliente, igual que en proyectos.
    assert child.client_user_id == client_user.pk
    assert child.parent_id == root.pk


def test_adoption_is_idempotent(client_user):
    root = DocumentFolder.objects.create(name='Littigio', client_user=client_user)

    adopt_client_folder(root, client_user)
    adopt_client_folder(DocumentFolder.objects.get(pk=root.pk), client_user)

    assert DocumentFolder.objects.filter(managed_client=client_user).count() == 1


def test_a_second_root_cannot_take_an_owned_client(client_user):
    first = DocumentFolder.objects.create(name='Gustavo', client_user=client_user)
    second = DocumentFolder.objects.create(name='Gustavo CLI', client_user=client_user)
    adopt_client_folder(first, client_user)

    with pytest.raises(ValueError, match='ya tiene la carpeta madre'):
        adopt_client_folder(second, client_user)


def test_a_subfolder_is_never_adopted(client_user):
    parent = DocumentFolder.objects.create(name='Propia')
    child = DocumentFolder.objects.create(
        name='Anidada', parent=parent, client_user=client_user,
    )

    with pytest.raises(ValueError, match='carpeta raíz'):
        adopt_client_folder(child, client_user)


def test_a_project_associated_root_is_never_adopted(client_user):
    Project.objects.bulk_create([Project(name='Kore', client=client_user)])
    project = Project.objects.get(name='Kore')
    root = DocumentFolder.objects.create(
        name='Kore', client_user=client_user, project=project,
    )

    with pytest.raises(ValueError, match='asociada a un proyecto'):
        adopt_client_folder(root, client_user)


def test_require_client_folder_refuses_to_provision_silently(client_user):
    """No hay provisión automática: se avisa, no se crea a espaldas de nadie."""
    with pytest.raises(ClientFolderAdoptionRequired):
        require_client_folder(client_user)

    assert DocumentFolder.objects.filter(managed_client=client_user).count() == 0


def test_synchronize_fills_the_client_of_a_later_subfolder(client_user):
    root = DocumentFolder.objects.create(name='Littigio', client_user=client_user)
    adopt_client_folder(root, client_user)
    orphan = DocumentFolder.objects.create(name='Nueva', parent=root)

    synchronize_existing_client_folder(client_user)
    orphan.refresh_from_db()

    assert orphan.client_user_id == client_user.pk


def test_deleting_the_client_leaves_the_folder_as_manual(client_user):
    root = DocumentFolder.objects.create(name='Littigio', client_user=client_user)
    adopt_client_folder(root, client_user)

    client_user.delete()
    root.refresh_from_db()

    # SET_NULL en las dos puntas: la carpeta sobrevive, degradada a propia.
    assert root.managed_client_id is None
    assert root.folder_kind == 'manual'
