"""Los endpoints de cambio de cliente de una carpeta: preview, apply y staleness.

Mismo contrato que el de proyectos (PA-51/PA-55): el preview no escribe, el
modo se elige siempre, y los ids del plan viajan de vuelta como token para que
lo que corre sea exactamente lo que se mostró.
"""
import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from django.urls import reverse

from content.models import Document, DocumentFolder

pytestmark = pytest.mark.django_db


def make_client(email, *, first='Ana', last='Pérez'):
    user = get_user_model().objects.create_user(
        username=email, email=email, password='pass12345',
        first_name=first, last_name=last,
    )
    return UserProfile.objects.create(user=user, cedula='1049654583')


@pytest.fixture
def kore(db):
    return make_client('kore@example.com', first='Kore', last='SAS')


@pytest.fixture
def ana(db):
    return make_client('ana@example.com')


@pytest.fixture
def folder(kore):
    return DocumentFolder.objects.create(name='Kore', client_user=kore.user)


@pytest.fixture
def managed_project(kore):
    return Project.objects.create(name='Kore Project', client=kore.user)


def preview_url(folder):
    return reverse(
        'preview-document-folder-client-change', kwargs={'folder_id': folder.id},
    )


def apply_url(folder):
    return reverse(
        'change-document-folder-client', kwargs={'folder_id': folder.id},
    )


class TestPreviewFolderClientChange:
    def test_managed_project_root_is_rejected(self, admin_client, managed_project):
        """Falla si el preview permite cambiar el cliente de una raíz automática."""
        response = admin_client.get(preview_url(managed_project.document_root_folder))

        assert response.status_code == 409
        assert response.json()['code'] == 'managed_project_folder'

    def test_returns_the_impact_without_writing(self, admin_client, folder, kore, ana):
        document = Document.objects.create(
            title='A', folder=folder, client_user=kore.user,
        )

        response = admin_client.get(preview_url(folder), {'client_profile_id': ana.pk})

        assert response.status_code == 200
        body = response.json()
        assert body['totals']['documents'] == 1
        assert body['document_ids'] == [document.pk]
        document.refresh_from_db()
        assert document.client_user == kore.user

    def test_unknown_client_is_rejected(self, admin_client, folder):
        response = admin_client.get(preview_url(folder), {'client_profile_id': 99999})

        assert response.status_code == 400
        assert response.json()['code'] == 'client_not_found'

    def test_the_same_client_is_rejected(self, admin_client, folder, kore):
        response = admin_client.get(preview_url(folder), {'client_profile_id': kore.pk})

        assert response.status_code == 400
        assert response.json()['code'] == 'same_client'

    def test_requires_admin_auth(self, api_client, folder, ana):
        response = api_client.get(preview_url(folder), {'client_profile_id': ana.pk})

        assert response.status_code == 401


class TestApplyFolderClientChange:
    def test_managed_project_root_is_rejected(self, admin_client, managed_project):
        """Falla si el apply permite cambiar el cliente de una raíz automática."""
        response = admin_client.post(
            apply_url(managed_project.document_root_folder), {}, format='json',
        )

        assert response.status_code == 409
        assert response.json()['code'] == 'managed_project_folder'

    def test_propagate_moves_the_confirmed_plan(
        self, admin_client, folder, kore, ana,
    ):
        document = Document.objects.create(
            title='A', folder=folder, client_user=kore.user,
        )

        response = admin_client.post(apply_url(folder), {
            'client_profile_id': ana.pk,
            'mode': 'propagate',
            'document_ids': [document.pk],
            'folder_ids': [],
        }, format='json')

        assert response.status_code == 200
        assert response.json()['moved']['documents'] == 1
        document.refresh_from_db()
        assert document.client_user == ana.user

    def test_folder_only_leaves_the_content(self, admin_client, folder, kore, ana):
        document = Document.objects.create(
            title='A', folder=folder, client_user=kore.user,
        )

        response = admin_client.post(apply_url(folder), {
            'client_profile_id': ana.pk,
            'mode': 'folder_only',
            'document_ids': [document.pk],
            'folder_ids': [],
        }, format='json')

        assert response.status_code == 200
        document.refresh_from_db()
        assert document.client_user == kore.user
        folder.refresh_from_db()
        assert folder.client_user == ana.user

    def test_an_unknown_mode_is_rejected(self, admin_client, folder, ana):
        response = admin_client.post(apply_url(folder), {
            'client_profile_id': ana.pk, 'mode': 'whatever',
        }, format='json')

        assert response.status_code == 400
        assert response.json()['code'] == 'invalid_mode'

    def test_a_missing_mode_is_rejected(self, admin_client, folder, ana):
        response = admin_client.post(apply_url(folder), {
            'client_profile_id': ana.pk,
        }, format='json')

        assert response.status_code == 400

    def test_a_document_that_left_the_plan_returns_409(
        self, admin_client, folder, kore, ana,
    ):
        document = Document.objects.create(
            title='A', folder=folder, client_user=kore.user,
        )
        stale_id = document.pk
        document.delete()

        response = admin_client.post(apply_url(folder), {
            'client_profile_id': ana.pk,
            'mode': 'propagate',
            'document_ids': [stale_id],
            'folder_ids': [],
        }, format='json')

        assert response.status_code == 409
        assert response.json()['code'] == 'records_not_found'

    def test_a_document_added_after_the_preview_returns_409(
        self, admin_client, folder, kore, ana,
    ):
        Document.objects.create(title='Nuevo', folder=folder, client_user=kore.user)

        response = admin_client.post(apply_url(folder), {
            'client_profile_id': ana.pk,
            'mode': 'propagate',
            'document_ids': [],
            'folder_ids': [],
        }, format='json')

        assert response.status_code == 409
        assert response.json()['code'] == 'records_changed'
        folder.refresh_from_db()
        assert folder.client_user == kore.user
