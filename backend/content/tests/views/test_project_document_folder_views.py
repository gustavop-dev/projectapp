"""API contract for managed project roots."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import Project, UserProfile
from content.models import DocumentFolder


pytestmark = pytest.mark.django_db


@pytest.fixture
def project():
    user = get_user_model().objects.create_user(
        username='managed-folder@example.com',
        email='managed-folder@example.com',
        password='pass12345',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)
    return Project.objects.create(name='Vastago', client=user)


def test_list_marks_project_root_with_state_visibility(admin_client, project):
    response = admin_client.get(reverse('list-document-folders'))

    root = next(item for item in response.data if item['managed_project'] == project.id)
    assert root['folder_kind'] == 'project'
    assert root['managed_project_state']['system_key'] == 'development'
    assert root['is_project_visible'] is True


def test_child_created_under_project_inherits_association(admin_client, project):
    root = project.document_root_folder

    response = admin_client.post(
        reverse('create-document-folder'),
        {'name': 'Actas', 'parent': root.id},
        format='json',
    )

    assert response.status_code == 201, response.data
    child = DocumentFolder.objects.get(pk=response.data['id'])
    assert child.project_id == project.id
    assert child.client_user_id == project.client_id
    assert child.managed_project_id is None


def test_project_root_cannot_be_renamed_from_documents(admin_client, project):
    root = project.document_root_folder

    response = admin_client.patch(
        reverse('update-document-folder', kwargs={'folder_id': root.id}),
        {'name': 'Otro nombre'},
        format='json',
    )

    assert response.status_code == 409
    assert response.data['code'] == 'managed_project_folder'


def test_project_root_cannot_be_archived(admin_client, project):
    root = project.document_root_folder

    response = admin_client.patch(
        reverse('archive-document-folder', kwargs={'folder_id': root.id}),
        {},
        format='json',
    )

    assert response.status_code == 409
    assert response.data['code'] == 'managed_project_folder'


def test_project_root_cannot_be_deleted(admin_client, project):
    root = project.document_root_folder

    response = admin_client.delete(
        reverse('delete-document-folder', kwargs={'folder_id': root.id}),
    )

    assert response.status_code == 409
    assert DocumentFolder.objects.filter(pk=root.id).exists()


def test_reorder_ignores_a_managed_project_root(admin_client, project):
    """Falla si un payload legado altera el orden de una raíz automática."""
    managed_root = project.document_root_folder
    managed_root.order = 7
    managed_root.save(update_fields=['order'])
    manual_root = DocumentFolder.objects.create(name='Carpeta personal', order=9)

    response = admin_client.post(
        reverse('reorder-document-folders'),
        {'ids': [managed_root.id, manual_root.id]},
        format='json',
    )

    assert response.status_code == 200
    manual_root.refresh_from_db()
    managed_root.refresh_from_db()
    assert manual_root.order == 1
    assert managed_root.order == 7
