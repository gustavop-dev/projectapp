"""Tests for content/views/document_folder.py — folder CRUD + document filter."""
import pytest
from django.urls import reverse

from content.models import Document, DocumentFolder

pytestmark = pytest.mark.django_db


@pytest.fixture
def folder(db):
    return DocumentFolder.objects.create(name='Cuentas de cobro')


class TestListDocumentFolders:
    def test_returns_200_with_list(self, admin_client, folder):
        url = reverse('list-document-folders')
        response = admin_client.get(url)

        assert response.status_code == 200
        names = [f['name'] for f in response.json()]
        assert 'Cuentas de cobro' in names

    def test_requires_admin_auth(self, api_client):
        url = reverse('list-document-folders')
        response = api_client.get(url)

        assert response.status_code == 401

    def test_document_count_reflects_assigned_documents(self, admin_client, folder):
        Document.objects.create(title='A', folder=folder)
        Document.objects.create(title='B', folder=folder)
        Document.objects.create(title='Orphan')

        url = reverse('list-document-folders')
        response = admin_client.get(url)

        assert response.status_code == 200
        entry = next(f for f in response.json() if f['id'] == folder.id)
        assert entry['document_count'] == 2


class TestCreateDocumentFolder:
    def test_creates_folder_and_auto_slug(self, admin_client):
        url = reverse('create-document-folder')
        response = admin_client.post(url, {'name': 'Contratos'}, format='json')

        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'Contratos'
        assert data['slug'] == 'contratos'

    def test_returns_400_on_missing_name(self, admin_client):
        url = reverse('create-document-folder')
        response = admin_client.post(url, {}, format='json')

        assert response.status_code == 400

    def test_auto_slug_handles_duplicate_names(self, admin_client):
        DocumentFolder.objects.create(name='Contratos')
        url = reverse('create-document-folder')
        response = admin_client.post(url, {'name': 'Contratos'}, format='json')

        assert response.status_code == 201
        assert response.json()['slug'] == 'contratos-2'


class TestUpdateDocumentFolder:
    def test_renames_folder(self, admin_client, folder):
        url = reverse('update-document-folder', kwargs={'folder_id': folder.id})
        response = admin_client.patch(url, {'name': 'Facturas'}, format='json')

        assert response.status_code == 200
        folder.refresh_from_db()
        assert folder.name == 'Facturas'

    def test_returns_404_for_nonexistent(self, admin_client):
        url = reverse('update-document-folder', kwargs={'folder_id': 99999})
        response = admin_client.patch(url, {'name': 'x'}, format='json')

        assert response.status_code == 404


class TestDeleteDocumentFolder:
    def test_deletes_empty_folder(self, admin_client, folder):
        url = reverse('delete-document-folder', kwargs={'folder_id': folder.id})
        response = admin_client.delete(url)

        assert response.status_code == 204
        assert not DocumentFolder.objects.filter(pk=folder.id).exists()

    def test_blocks_deletion_when_folder_has_documents(self, admin_client, folder):
        doc = Document.objects.create(title='Inside', folder=folder)

        url = reverse('delete-document-folder', kwargs={'folder_id': folder.id})
        response = admin_client.delete(url)

        assert response.status_code == 409
        body = response.json()
        assert body['document_count'] == 1
        assert 'detail' in body

        assert DocumentFolder.objects.filter(pk=folder.id).exists()
        doc.refresh_from_db()
        assert doc.folder_id == folder.id

    def test_returns_404_for_nonexistent(self, admin_client):
        url = reverse('delete-document-folder', kwargs={'folder_id': 99999})
        response = admin_client.delete(url)

        assert response.status_code == 404


class TestListDocumentsFolderFilter:
    def test_filter_by_folder_id_returns_only_matching(self, admin_client, folder):
        inside = Document.objects.create(title='Inside', folder=folder)
        Document.objects.create(title='Outside')

        url = reverse('list-documents')
        response = admin_client.get(url, {'folder': folder.id})

        assert response.status_code == 200
        titles = [d['title'] for d in response.json()]
        assert 'Inside' in titles
        assert 'Outside' not in titles
        assert response.json()[0]['id'] == inside.id

    def test_filter_by_folder_none_returns_uncategorized(self, admin_client, folder):
        Document.objects.create(title='Inside', folder=folder)
        Document.objects.create(title='Orphan')

        url = reverse('list-documents')
        response = admin_client.get(url, {'folder': 'none'})

        assert response.status_code == 200
        titles = [d['title'] for d in response.json()]
        assert titles == ['Orphan']

    def test_invalid_folder_param_returns_400(self, admin_client):
        url = reverse('list-documents')
        response = admin_client.get(url, {'folder': 'abc'})

        assert response.status_code == 400


class TestFolderHierarchy:
    def test_creates_folder_with_parent(self, admin_client, folder):
        url = reverse('create-document-folder')
        response = admin_client.post(
            url, {'name': 'Sub', 'parent': folder.id}, format='json',
        )

        assert response.status_code == 201
        assert response.json()['parent'] == folder.id

    def test_updates_parent(self, admin_client, folder):
        child = DocumentFolder.objects.create(name='Sub')

        url = reverse('update-document-folder', kwargs={'folder_id': child.id})
        response = admin_client.patch(url, {'parent': folder.id}, format='json')

        assert response.status_code == 200
        child.refresh_from_db()
        assert child.parent_id == folder.id

    def test_rejects_self_as_parent(self, admin_client, folder):
        url = reverse('update-document-folder', kwargs={'folder_id': folder.id})
        response = admin_client.patch(url, {'parent': folder.id}, format='json')

        assert response.status_code == 400
        assert 'parent' in response.json()

    def test_rejects_descendant_as_parent(self, admin_client, folder):
        # folder -> child -> grandchild; mover folder bajo grandchild = ciclo.
        child = DocumentFolder.objects.create(name='Child', parent=folder)
        grandchild = DocumentFolder.objects.create(name='Grandchild', parent=child)

        url = reverse('update-document-folder', kwargs={'folder_id': folder.id})
        response = admin_client.patch(
            url, {'parent': grandchild.id}, format='json',
        )

        assert response.status_code == 400
        assert 'parent' in response.json()

    def test_blocks_deletion_when_folder_has_children(self, admin_client, folder):
        DocumentFolder.objects.create(name='Sub', parent=folder)

        url = reverse('delete-document-folder', kwargs={'folder_id': folder.id})
        response = admin_client.delete(url)

        assert response.status_code == 409
        assert response.json()['children_count'] == 1
        assert DocumentFolder.objects.filter(pk=folder.id).exists()

    def test_allows_deletion_of_empty_leaf_folder(self, admin_client, folder):
        child = DocumentFolder.objects.create(name='Sub', parent=folder)

        url = reverse('delete-document-folder', kwargs={'folder_id': child.id})
        response = admin_client.delete(url)

        assert response.status_code == 204
        assert not DocumentFolder.objects.filter(pk=child.id).exists()

    def test_list_includes_parent_and_children_count_without_multiplying(
        self, admin_client, folder,
    ):
        DocumentFolder.objects.create(name='Sub A', parent=folder)
        DocumentFolder.objects.create(name='Sub B', parent=folder)
        Document.objects.create(title='Doc 1', folder=folder)
        Document.objects.create(title='Doc 2', folder=folder)

        url = reverse('list-document-folders')
        response = admin_client.get(url)

        assert response.status_code == 200
        entry = next(f for f in response.json() if f['id'] == folder.id)
        assert entry['parent'] is None
        # Sin distinct=True el JOIN cruzado daría 4 en ambos campos.
        assert entry['document_count'] == 2
        assert entry['children_count'] == 2
