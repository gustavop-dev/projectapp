"""Tests for content/views/document_folder.py — folder CRUD + document filter."""
import pytest
from django.urls import reverse

from content.models import Document, DocumentFolder
from content.models.document_folder import MAX_FOLDER_DEPTH

pytestmark = pytest.mark.django_db


@pytest.fixture
def folder(db):
    return DocumentFolder.objects.create(name='Cuentas de cobro')


def _make_chain(depth):
    """Build a chain root → child → grandchild ... with `depth` levels.

    depth=1 → only root. depth=2 → root + 1 child. etc.
    Returns the list (deepest at end).
    """
    chain = []
    parent = None
    for i in range(depth):
        f = DocumentFolder.objects.create(name=f'L{i}', parent=parent)
        chain.append(f)
        parent = f
    return chain


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


class TestNestedFolderModel:
    def test_get_depth(self, db):
        root = DocumentFolder.objects.create(name='Root')
        child = DocumentFolder.objects.create(name='Child', parent=root)
        grand = DocumentFolder.objects.create(name='Grand', parent=child)
        assert root.get_depth() == 0
        assert child.get_depth() == 1
        assert grand.get_depth() == 2

    def test_get_descendant_ids_includes_full_subtree(self, db):
        chain = _make_chain(3)
        descendants = chain[0].get_descendant_ids(include_self=False)
        assert descendants == {chain[1].pk, chain[2].pk}
        with_self = chain[0].get_descendant_ids(include_self=True)
        assert with_self == {chain[0].pk, chain[1].pk, chain[2].pk}


class TestCreateNestedFolder:
    def test_creates_with_parent(self, admin_client, folder):
        url = reverse('create-document-folder')
        response = admin_client.post(
            url, {'name': 'Activos', 'parent': folder.id}, format='json'
        )
        assert response.status_code == 201
        body = response.json()
        assert body['parent'] == folder.id
        assert body['depth'] == 1
        assert [p['id'] for p in body['path']] == [folder.id, body['id']]

    def test_rejects_depth_exceeded(self, admin_client):
        # Build MAX_FOLDER_DEPTH levels (max valid). One more should fail.
        chain = _make_chain(MAX_FOLDER_DEPTH)
        url = reverse('create-document-folder')
        response = admin_client.post(
            url, {'name': 'TooDeep', 'parent': chain[-1].id}, format='json'
        )
        assert response.status_code == 400
        assert 'parent' in response.json()


class TestUpdateNestedFolder:
    def test_rejects_self_parent(self, admin_client, folder):
        url = reverse('update-document-folder', kwargs={'folder_id': folder.id})
        response = admin_client.patch(url, {'parent': folder.id}, format='json')
        assert response.status_code == 400

    def test_rejects_cycle_into_descendant(self, admin_client):
        chain = _make_chain(3)
        url = reverse('update-document-folder', kwargs={'folder_id': chain[0].id})
        response = admin_client.patch(url, {'parent': chain[2].id}, format='json')
        assert response.status_code == 400
        assert 'parent' in response.json()


class TestDeleteWithChildren:
    def test_blocked_by_children(self, admin_client):
        chain = _make_chain(2)
        url = reverse('delete-document-folder', kwargs={'folder_id': chain[0].id})
        response = admin_client.delete(url)
        assert response.status_code == 409
        body = response.json()
        assert body['has_children'] is True
        assert 'has_children' in body['reasons']

    def test_blocked_by_documents_in_descendants(self, admin_client):
        chain = _make_chain(2)
        Document.objects.create(title='Inside Child', folder=chain[1])
        url = reverse('delete-document-folder', kwargs={'folder_id': chain[0].id})
        response = admin_client.delete(url)
        assert response.status_code == 409
        body = response.json()
        assert body['has_children'] is True
        assert body['document_count'] == 1
        assert 'has_documents' in body['reasons']


class TestRecursiveDocumentFilter:
    def test_filter_by_parent_includes_descendants(self, admin_client):
        root = DocumentFolder.objects.create(name='Clientes')
        child = DocumentFolder.objects.create(name='Activos', parent=root)
        Document.objects.create(title='RootDoc', folder=root)
        Document.objects.create(title='ChildDoc', folder=child)
        Document.objects.create(title='Outside')
        url = reverse('list-documents')
        response = admin_client.get(url, {'folder': root.id})
        assert response.status_code == 200
        titles = sorted(d['title'] for d in response.json())
        assert titles == ['ChildDoc', 'RootDoc']


class TestMoveFolder:
    def test_reparents_folder(self, admin_client):
        a = DocumentFolder.objects.create(name='A')
        b = DocumentFolder.objects.create(name='B')
        c = DocumentFolder.objects.create(name='C', parent=a)
        url = reverse('move-document-folder', kwargs={'folder_id': c.id})
        response = admin_client.post(url, {'parent_id': b.id}, format='json')
        assert response.status_code == 200
        c.refresh_from_db()
        assert c.parent_id == b.id

    def test_move_to_root(self, admin_client):
        chain = _make_chain(2)
        url = reverse('move-document-folder', kwargs={'folder_id': chain[1].id})
        response = admin_client.post(url, {'parent_id': None}, format='json')
        assert response.status_code == 200
        chain[1].refresh_from_db()
        assert chain[1].parent_id is None

    def test_rejects_move_into_descendant(self, admin_client):
        chain = _make_chain(3)
        url = reverse('move-document-folder', kwargs={'folder_id': chain[0].id})
        response = admin_client.post(url, {'parent_id': chain[2].id}, format='json')
        assert response.status_code == 400


class TestSerializerFields:
    def test_document_count_is_recursive(self, admin_client):
        root = DocumentFolder.objects.create(name='Root')
        child = DocumentFolder.objects.create(name='Child', parent=root)
        Document.objects.create(title='A', folder=root)
        Document.objects.create(title='B', folder=child)
        Document.objects.create(title='C', folder=child)
        url = reverse('list-document-folders')
        response = admin_client.get(url)
        assert response.status_code == 200
        entry = next(f for f in response.json() if f['id'] == root.id)
        assert entry['document_count'] == 3

    def test_path_root_to_self(self, admin_client):
        root = DocumentFolder.objects.create(name='Clientes')
        child = DocumentFolder.objects.create(name='Activos', parent=root)
        url = reverse('list-document-folders')
        response = admin_client.get(url)
        entry = next(f for f in response.json() if f['id'] == child.id)
        assert [p['name'] for p in entry['path']] == ['Clientes', 'Activos']


class TestReorderScopedByParent:
    def test_rejects_siblings_with_different_parents(self, admin_client):
        a = DocumentFolder.objects.create(name='A')
        b = DocumentFolder.objects.create(name='B', parent=a)
        c = DocumentFolder.objects.create(name='C')  # root
        url = reverse('reorder-document-folders')
        response = admin_client.post(
            url, {'parent_id': None, 'ids': [b.id, c.id]}, format='json'
        )
        assert response.status_code == 400

    def test_reorders_siblings_within_parent(self, admin_client):
        a = DocumentFolder.objects.create(name='A')
        b = DocumentFolder.objects.create(name='B')
        url = reverse('reorder-document-folders')
        response = admin_client.post(
            url, {'parent_id': None, 'ids': [b.id, a.id]}, format='json'
        )
        assert response.status_code == 200
        a.refresh_from_db(); b.refresh_from_db()
        assert b.order == 0 and a.order == 1
