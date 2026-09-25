"""Panel API contract for the independent communication-folder tree."""
import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from django.urls import reverse

from content.models import CommunicationFolder


pytestmark = pytest.mark.django_db
User = get_user_model()


def make_client(email):
    user = User.objects.create_user(
        username=email, email=email, password='testpass123',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


def test_admin_creates_lists_and_renames_a_project_folder(admin_client):
    """Falla si el panel no persiste o no devuelve la ubicación de una carpeta."""
    client = make_client('folder-api@example.com')
    project = Project.objects.create(name='Portal', client=client.user)
    collection_url = reverse('communication-folders')

    created = admin_client.post(collection_url, {
        'name': 'Entregables', 'client': client.id, 'project': project.id,
    }, format='json')
    folder_id = created.data['id']
    renamed = admin_client.patch(
        reverse('communication-folder-detail', args=[folder_id]),
        {'name': 'Entregables aprobados'}, format='json',
    )
    listed = admin_client.get(collection_url, {'client': client.id, 'project': project.id})

    assert created.status_code == 201
    assert renamed.status_code == 200
    assert listed.data == [{
        'id': folder_id,
        'name': 'Entregables aprobados',
        'parent': None,
        'client': client.id,
        'project': project.id,
        'created_at': listed.data[0]['created_at'],
        'updated_at': listed.data[0]['updated_at'],
    }]


def test_folder_collection_rejects_anonymous_and_non_staff_clients(api_client):
    """Falla si usuarios sin privilegios pueden consultar la organización interna."""
    non_staff = User.objects.create_user(
        username='folder-nonstaff', email='folder-nonstaff@example.com', password='testpass123',
    )
    url = reverse('communication-folders')

    anonymous = api_client.get(url)
    api_client.force_authenticate(user=non_staff)
    authenticated = api_client.get(url)

    assert anonymous.status_code == 401
    assert authenticated.status_code == 403


def test_admin_cannot_create_a_folder_for_a_foreign_project(admin_client):
    """Falla si un proyecto de otro cliente puede entrar en un árbol ajeno."""
    owner = make_client('folder-owner@example.com')
    foreign = make_client('folder-foreign@example.com')
    project = Project.objects.create(name='Ajeno', client=foreign.user)

    response = admin_client.post(reverse('communication-folders'), {
        'name': 'No corresponde', 'client': owner.id, 'project': project.id,
    }, format='json')

    assert response.status_code == 400
    assert response.data['project'] == ['El proyecto no pertenece al cliente.']
    assert CommunicationFolder.objects.count() == 0


def test_admin_deletes_an_empty_folder(admin_client):
    """Falla si una carpeta vacía no se puede retirar del árbol."""
    client = make_client('folder-delete@example.com')
    folder = CommunicationFolder.objects.create(name='Temporal', client=client)

    response = admin_client.delete(
        reverse('communication-folder-detail', args=[folder.id]),
    )

    assert response.status_code == 204
    assert CommunicationFolder.objects.filter(pk=folder.id).exists() is False
