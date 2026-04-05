"""Tests for content/views/document.py — generic document CRUD + PDF download."""
from io import BytesIO
from unittest.mock import patch

import pytest
from django.urls import reverse

from content.models import Document, DocumentType

pytestmark = pytest.mark.django_db


# ── Fixtures ──

@pytest.fixture
def markdown_doc_type(db):
    """Reuse or create the 'markdown' DocumentType (seeded by migration 0052)."""
    obj, _ = DocumentType.objects.get_or_create(
        code='markdown',
        defaults={'name': 'Markdown', 'label': 'Markdown'},
    )
    return obj


@pytest.fixture
def document(db, markdown_doc_type):
    return Document.objects.create(
        title='Test Document',
        document_type=markdown_doc_type,
        client_name='ACME Corp',
        language='es',
        content_markdown='# Hello\n\nWorld',
        content_json={'meta': {}, 'blocks': [{'type': 'heading', 'text': 'Hello'}]},
    )


# ── list_documents ──

class TestListDocuments:
    def test_returns_200_with_list(self, admin_client, document):
        url = reverse('list-documents')
        response = admin_client.get(url)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_requires_admin_auth(self, api_client):
        url = reverse('list-documents')
        response = api_client.get(url)

        assert response.status_code == 401


# ── create_document ──

class TestCreateDocument:
    def test_creates_document_with_json_content(self, admin_client, markdown_doc_type):
        url = reverse('create-document')
        payload = {
            'title': 'New Doc',
            'content_json': {'meta': {}, 'blocks': []},
        }
        response = admin_client.post(url, payload, format='json')

        assert response.status_code == 201
        assert response.json()['title'] == 'New Doc'

    def test_creates_document_and_parses_markdown_when_no_json(self, admin_client):
        url = reverse('create-document')
        payload = {
            'title': 'Markdown Doc',
            'content_markdown': '# Title\n\nSome text.',
        }
        response = admin_client.post(url, payload, format='json')

        assert response.status_code == 201
        data = response.json()
        assert data['content_json'] is not None
        assert 'blocks' in data['content_json']

    def test_returns_400_on_invalid_payload(self, admin_client):
        url = reverse('create-document')
        response = admin_client.post(url, {}, format='json')

        assert response.status_code == 400

    def test_sets_markdown_doc_type_when_not_provided(self, admin_client, markdown_doc_type):
        url = reverse('create-document')
        payload = {
            'title': 'Doc No Type',
            'content_json': {'meta': {}, 'blocks': []},
        }
        response = admin_client.post(url, payload, format='json')

        assert response.status_code == 201
        doc = Document.objects.get(title='Doc No Type')
        assert doc.document_type.code == 'markdown'


# ── create_document_from_markdown ──

class TestCreateDocumentFromMarkdown:
    def test_creates_document_from_markdown(self, admin_client):
        url = reverse('create-document-from-markdown')
        payload = {
            'title': 'Markdown Creation',
            'markdown': '# Heading\n\nParagraph here.',
        }
        response = admin_client.post(url, payload, format='json')

        assert response.status_code == 201
        data = response.json()
        assert data['title'] == 'Markdown Creation'
        assert data['content_json']['blocks']

    def test_returns_400_on_missing_fields(self, admin_client):
        url = reverse('create-document-from-markdown')
        response = admin_client.post(url, {}, format='json')

        assert response.status_code == 400

    def test_creates_with_optional_fields(self, admin_client):
        url = reverse('create-document-from-markdown')
        payload = {
            'title': 'Full Doc',
            'markdown': '# Full\n\nContent.',
            'client_name': 'Test Client',
            'language': 'en',
            'cover_type': 'generic',
        }
        response = admin_client.post(url, payload, format='json')

        assert response.status_code == 201
        doc = Document.objects.get(title='Full Doc')
        assert doc.client_name == 'Test Client'
        assert doc.language == 'en'


# ── upload_document_markdown ──

class TestUploadDocumentMarkdown:
    def test_creates_document_from_uploaded_file(self, admin_client):
        url = reverse('upload-document-markdown')
        md_content = b'# Uploaded\n\nContent from file.'
        file_obj = BytesIO(md_content)
        file_obj.name = 'test.md'

        response = admin_client.post(
            url,
            {'file': file_obj, 'title': 'Uploaded Doc'},
            format='multipart',
        )

        assert response.status_code == 201
        assert response.json()['title'] == 'Uploaded Doc'

    def test_returns_400_when_no_file(self, admin_client):
        url = reverse('upload-document-markdown')
        response = admin_client.post(url, {}, format='multipart')

        assert response.status_code == 400

    def test_uses_filename_as_title_when_not_provided(self, admin_client):
        url = reverse('upload-document-markdown')
        md_content = b'# Auto Title'
        file_obj = BytesIO(md_content)
        file_obj.name = 'my-document.md'

        response = admin_client.post(url, {'file': file_obj}, format='multipart')

        assert response.status_code == 201
        assert response.json()['title'] == 'my-document'

    def test_include_portada_false_string_disables_portada(self, admin_client):
        url = reverse('upload-document-markdown')
        md_content = b'# Test'
        file_obj = BytesIO(md_content)
        file_obj.name = 'test.md'

        response = admin_client.post(
            url,
            {'file': file_obj, 'title': 'No Portada', 'include_portada': 'false'},
            format='multipart',
        )

        assert response.status_code == 201
        doc = Document.objects.get(title='No Portada')
        assert doc.include_portada is False

    def test_returns_400_on_non_utf8_file(self, admin_client):
        url = reverse('upload-document-markdown')
        file_obj = BytesIO(b'\xff\xfe invalid bytes')
        file_obj.name = 'bad.md'

        response = admin_client.post(url, {'file': file_obj}, format='multipart')

        assert response.status_code == 400


# ── retrieve_document ──

class TestRetrieveDocument:
    def test_returns_document_detail(self, admin_client, document):
        url = reverse('retrieve-document', kwargs={'document_id': document.id})
        response = admin_client.get(url)

        assert response.status_code == 200
        assert response.json()['title'] == 'Test Document'

    def test_returns_404_for_nonexistent(self, admin_client):
        url = reverse('retrieve-document', kwargs={'document_id': 99999})
        response = admin_client.get(url)

        assert response.status_code == 404


# ── update_document ──

class TestUpdateDocument:
    def test_updates_document_title(self, admin_client, document):
        url = reverse('update-document', kwargs={'document_id': document.id})
        response = admin_client.patch(url, {'title': 'Updated Title'}, format='json')

        assert response.status_code == 200
        document.refresh_from_db()
        assert document.title == 'Updated Title'

    def test_reparses_markdown_when_content_markdown_updated(self, admin_client, document):
        url = reverse('update-document', kwargs={'document_id': document.id})
        response = admin_client.patch(
            url, {'content_markdown': '# New Heading\n\nNew content.'}, format='json',
        )

        assert response.status_code == 200
        document.refresh_from_db()
        assert document.content_json is not None

    def test_returns_400_on_invalid_payload(self, admin_client, document):
        url = reverse('update-document', kwargs={'document_id': document.id})
        # Pass a non-string to a CharField — forces 400
        response = admin_client.patch(url, {'language': ['bad', 'list']}, format='json')

        assert response.status_code == 400

    def test_returns_404_for_nonexistent(self, admin_client):
        url = reverse('update-document', kwargs={'document_id': 99999})
        response = admin_client.patch(url, {'title': 'X'}, format='json')

        assert response.status_code == 404


# ── delete_document ──

class TestDeleteDocument:
    def test_deletes_document_and_returns_204(self, admin_client, document):
        doc_id = document.id
        url = reverse('delete-document', kwargs={'document_id': doc_id})
        response = admin_client.delete(url)

        assert response.status_code == 204
        assert not Document.objects.filter(pk=doc_id).exists()

    def test_returns_404_for_nonexistent(self, admin_client):
        url = reverse('delete-document', kwargs={'document_id': 99999})
        response = admin_client.delete(url)

        assert response.status_code == 404


# ── duplicate_document ──

class TestDuplicateDocument:
    def test_duplicates_document_with_copia_suffix(self, admin_client, document):
        url = reverse('duplicate-document', kwargs={'document_id': document.id})
        response = admin_client.post(url)

        assert response.status_code == 201
        data = response.json()
        assert '(copia)' in data['title']
        assert Document.objects.count() == 2

    def test_returns_404_for_nonexistent(self, admin_client):
        url = reverse('duplicate-document', kwargs={'document_id': 99999})
        response = admin_client.post(url)

        assert response.status_code == 404

    def test_returns_400_for_collection_account(self, admin_client, db):
        from content.services.document_type_codes import COLLECTION_ACCOUNT
        ca_type, _ = DocumentType.objects.get_or_create(
            code=COLLECTION_ACCOUNT,
            defaults={'name': 'Collection Account', 'label': 'Collection Account'},
        )
        doc = Document.objects.create(
            title='Collection Doc', document_type=ca_type, client_name='C',
        )
        url = reverse('duplicate-document', kwargs={'document_id': doc.id})
        response = admin_client.post(url)

        assert response.status_code == 400

    def test_duplicates_document_without_document_type(self, admin_client, markdown_doc_type):
        """Covers the `doc_type = document.document_type or get_markdown_document_type()` fallback."""
        doc = Document.objects.create(
            title='No Type Doc',
            document_type=None,
            content_json={'meta': {}, 'blocks': [{'type': 'heading', 'text': 'H'}]},
        )
        url = reverse('duplicate-document', kwargs={'document_id': doc.id})
        response = admin_client.post(url)

        assert response.status_code == 201
        data = response.json()
        assert '(copia)' in data['title']
        # document_type is not in the serializer response, verify via DB
        duplicate = Document.objects.get(pk=data['id'])
        assert duplicate.document_type is not None


# ── download_document_pdf ──

class TestDownloadDocumentPdf:
    def test_returns_pdf_bytes_for_document_with_content(self, admin_client, document):
        url = reverse('download-document-pdf', kwargs={'document_id': document.id})
        with patch(
            'content.services.document_pdf_service.DocumentPdfService.generate',
            return_value=b'%PDF-1.4 mock content',
        ):
            response = admin_client.get(url)

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert 'attachment' in response['Content-Disposition']
        assert '.pdf' in response['Content-Disposition']

    def test_returns_400_when_no_blocks(self, admin_client, markdown_doc_type):
        doc = Document.objects.create(
            title='Empty', document_type=markdown_doc_type,
            content_json={'meta': {}, 'blocks': []},
        )
        url = reverse('download-document-pdf', kwargs={'document_id': doc.id})
        response = admin_client.get(url)

        assert response.status_code == 400

    def test_returns_400_when_no_blocks_key(self, admin_client, markdown_doc_type):
        doc = Document.objects.create(
            title='No Blocks Key', document_type=markdown_doc_type,
            content_json={'meta': {}},
        )
        url = reverse('download-document-pdf', kwargs={'document_id': doc.id})
        response = admin_client.get(url)

        assert response.status_code == 400

    def test_returns_500_when_generation_fails(self, admin_client, document):
        url = reverse('download-document-pdf', kwargs={'document_id': document.id})
        with patch(
            'content.services.document_pdf_service.DocumentPdfService.generate',
            return_value=None,
        ):
            response = admin_client.get(url)

        assert response.status_code == 500
