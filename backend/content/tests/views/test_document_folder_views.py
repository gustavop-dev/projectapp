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
    def test_deletes_folder_and_keeps_documents_with_null_folder(
        self, admin_client, folder,
    ):
        doc = Document.objects.create(title='Inside', folder=folder)

        url = reverse('delete-document-folder', kwargs={'folder_id': folder.id})
        response = admin_client.delete(url)

        assert response.status_code == 204
        doc.refresh_from_db()
        assert doc.folder_id is None
        assert Document.objects.filter(pk=doc.pk).exists()

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
