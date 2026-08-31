"""API contract for the folder that represents a client."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import UserProfile
from content.models import DocumentFolder
from content.services.client_document_folder_service import adopt_client_folder


pytestmark = pytest.mark.django_db


def _client_user(email, first_name='Marco', last_name='Camacho'):
    user = get_user_model().objects.create_user(
        username=email, email=email, password='pass12345',
        first_name=first_name, last_name=last_name,
    )
    UserProfile.objects.update_or_create(
        user=user, defaults={'role': UserProfile.ROLE_CLIENT},
    )
    return user


@pytest.fixture
def client_root():
    user = _client_user('view-client@example.com')
    root = DocumentFolder.objects.create(name='Littigio', client_user=user)
    return adopt_client_folder(root, user)


def test_list_marks_the_client_root_and_speaks_profile_ids(admin_client, client_root):
    response = admin_client.get(reverse('list-document-folders'))
    row = next(r for r in response.data if r['id'] == client_root.id)

    assert row['folder_kind'] == 'client'
    # El panel habla en pk de UserProfile en toda asociación de cliente.
    assert row['managed_client'] == client_root.client_user.profile.id
    assert row['client'] == client_root.client_user.profile.id


def test_client_root_can_still_be_renamed(admin_client, client_root):
    """A diferencia de la raíz de proyecto: el nombre lo pone el operador."""
    response = admin_client.patch(
        reverse('update-document-folder', kwargs={'folder_id': client_root.id}),
        {'name': 'Littigio S.A.S.'},
        format='json',
    )

    assert response.status_code == 200, response.data
    client_root.refresh_from_db()
    assert client_root.name == 'Littigio S.A.S.'


def test_client_root_cannot_change_owner(admin_client, client_root):
    other = _client_user('other-view@example.com', 'Otra', 'Persona')

    response = admin_client.patch(
        reverse('update-document-folder', kwargs={'folder_id': client_root.id}),
        {'client': other.profile.id},
        format='json',
    )

    assert response.status_code == 409
    assert response.data['code'] == 'managed_client_folder'


def test_client_root_cannot_stop_being_a_root(admin_client, client_root):
    parent = DocumentFolder.objects.create(name='Propia')

    response = admin_client.patch(
        reverse('update-document-folder', kwargs={'folder_id': client_root.id}),
        {'parent': parent.id},
        format='json',
    )

    assert response.status_code == 409
    assert response.data['code'] == 'managed_client_folder'


def test_client_root_cannot_be_archived(admin_client, client_root):
    response = admin_client.patch(
        reverse('archive-document-folder', kwargs={'folder_id': client_root.id}),
        {},
        format='json',
    )

    assert response.status_code == 409
    assert response.data['code'] == 'managed_client_folder'


def test_client_root_cannot_be_deleted(admin_client, client_root):
    response = admin_client.delete(
        reverse('delete-document-folder', kwargs={'folder_id': client_root.id}),
    )

    assert response.status_code == 409
    assert DocumentFolder.objects.filter(pk=client_root.id).exists()


def test_child_created_under_the_client_root_inherits_the_client(admin_client, client_root):
    response = admin_client.post(
        reverse('create-document-folder'),
        {'name': 'Contratos', 'parent': client_root.id},
        format='json',
    )

    assert response.status_code == 201, response.data
    child = DocumentFolder.objects.get(pk=response.data['id'])
    assert child.client_user_id == client_root.client_user_id
    assert child.managed_client_id is None


def test_reorder_ignores_the_client_root(admin_client, client_root):
    client_root.order = 7
    client_root.save(update_fields=['order'])
    manual_root = DocumentFolder.objects.create(name='Carpeta personal', order=9)

    response = admin_client.post(
        reverse('reorder-document-folders'),
        {'ids': [client_root.id, manual_root.id]},
        format='json',
    )

    assert response.status_code == 200
    manual_root.refresh_from_db()
    client_root.refresh_from_db()
    assert manual_root.order == 1
    # La raíz gestionada no participa del orden manual.
    assert client_root.order == 7


def test_navigation_exposes_the_client_managed_root(admin_client, client_root):
    response = admin_client.get(reverse('document-navigation'))
    entry = next(
        c for c in response.data['clients']
        if c['id'] == client_root.client_user.profile.id
    )

    assert entry['managed_root_id'] == client_root.id


def test_navigation_reports_no_root_for_a_client_without_one(admin_client):
    user = _client_user('rootless@example.com', 'Sin', 'Carpeta')

    response = admin_client.get(reverse('document-navigation'))
    entry = next(c for c in response.data['clients'] if c['id'] == user.profile.id)

    # La mayoría de los clientes no adoptó carpeta: el campo existe y es null.
    assert entry['managed_root_id'] is None
