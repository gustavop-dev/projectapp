"""Tests for content/views/document_tag.py — tag CRUD + document M2M + filters."""
import pytest
from django.urls import reverse

from content.models import Document, DocumentTag

pytestmark = pytest.mark.django_db


@pytest.fixture
def tag_urgent(db):
    return DocumentTag.objects.create(name='Urgente', color='red')


@pytest.fixture
def tag_signed(db):
    return DocumentTag.objects.create(name='Firmado', color='emerald')


class TestListDocumentTags:
    def test_returns_list(self, admin_client, tag_urgent, tag_signed):
        url = reverse('list-document-tags')
        response = admin_client.get(url)

        assert response.status_code == 200
        names = [t['name'] for t in response.json()]
        assert names == ['Firmado', 'Urgente']

    def test_requires_admin_auth(self, api_client):
        url = reverse('list-document-tags')
        response = api_client.get(url)

        assert response.status_code == 401


class TestCreateDocumentTag:
    def test_creates_tag_with_color(self, admin_client):
        url = reverse('create-document-tag')
        response = admin_client.post(
            url, {'name': 'Revisado', 'color': 'blue'}, format='json',
        )

        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'Revisado'
        assert data['color'] == 'blue'
        assert data['slug'] == 'revisado'

    def test_rejects_invalid_color(self, admin_client):
        url = reverse('create-document-tag')
        response = admin_client.post(
            url, {'name': 'Bad', 'color': 'neon'}, format='json',
        )

        assert response.status_code == 400


class TestUpdateDocumentTag:
    def test_renames_and_recolors(self, admin_client, tag_urgent):
        url = reverse('update-document-tag', kwargs={'tag_id': tag_urgent.id})
        response = admin_client.patch(
            url, {'name': 'Crítico', 'color': 'yellow'}, format='json',
        )

        assert response.status_code == 200
        tag_urgent.refresh_from_db()
        assert tag_urgent.name == 'Crítico'
        assert tag_urgent.color == 'yellow'


class TestDeleteDocumentTag:
    def test_deletes_tag_and_removes_from_documents(
        self, admin_client, tag_urgent,
    ):
        doc = Document.objects.create(title='With tag')
        doc.tags.add(tag_urgent)

        url = reverse('delete-document-tag', kwargs={'tag_id': tag_urgent.id})
        response = admin_client.delete(url)

        assert response.status_code == 204
        doc.refresh_from_db()
        assert doc.tags.count() == 0


class TestDocumentTagAssignment:
    def test_create_document_with_tag_ids(self, admin_client, tag_urgent, tag_signed):
        url = reverse('create-document')
        response = admin_client.post(
            url,
            {
                'title': 'Tagged doc',
                'content_json': {'meta': {}, 'blocks': []},
                'tag_ids': [tag_urgent.id, tag_signed.id],
            },
            format='json',
        )

        assert response.status_code == 201
        doc = Document.objects.get(pk=response.json()['id'])
        assert set(doc.tags.values_list('id', flat=True)) == {
            tag_urgent.id, tag_signed.id,
        }

    def test_update_document_replaces_tag_set(self, admin_client, tag_urgent, tag_signed):
        doc = Document.objects.create(title='Doc')
        doc.tags.add(tag_urgent)

        url = reverse('update-document', kwargs={'document_id': doc.id})
        response = admin_client.patch(
            url, {'tag_ids': [tag_signed.id]}, format='json',
        )

        assert response.status_code == 200
        doc.refresh_from_db()
        assert list(doc.tags.values_list('id', flat=True)) == [tag_signed.id]

    def test_detail_serializer_returns_tag_details_with_color(
        self, admin_client, tag_urgent,
    ):
        doc = Document.objects.create(title='Doc')
        doc.tags.add(tag_urgent)

        url = reverse('retrieve-document', kwargs={'document_id': doc.id})
        response = admin_client.get(url)

        assert response.status_code == 200
        details = response.json()['tag_details']
        assert details == [{'id': tag_urgent.id, 'name': 'Urgente', 'color': 'red'}]


class TestListDocumentsTagsFilter:
    def test_filter_by_single_tag(self, admin_client, tag_urgent, tag_signed):
        a = Document.objects.create(title='A')
        a.tags.add(tag_urgent)
        b = Document.objects.create(title='B')
        b.tags.add(tag_signed)

        url = reverse('list-documents')
        response = admin_client.get(url, {'tags': str(tag_urgent.id)})

        assert response.status_code == 200
        titles = [d['title'] for d in response.json()]
        assert titles == ['A']

    def test_filter_by_multiple_tags_or(self, admin_client, tag_urgent, tag_signed):
        a = Document.objects.create(title='A')
        a.tags.add(tag_urgent)
        b = Document.objects.create(title='B')
        b.tags.add(tag_signed)
        Document.objects.create(title='Neither')

        url = reverse('list-documents')
        response = admin_client.get(
            url, {'tags': f'{tag_urgent.id},{tag_signed.id}'},
        )

        assert response.status_code == 200
        titles = {d['title'] for d in response.json()}
        assert titles == {'A', 'B'}

    def test_invalid_tags_param_returns_400(self, admin_client):
        url = reverse('list-documents')
        response = admin_client.get(url, {'tags': '1,abc'})

        assert response.status_code == 400
