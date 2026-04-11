"""Tests for Document serializers.

Covers: DocumentListSerializer, DocumentDetailSerializer,
DocumentCreateUpdateSerializer, DocumentFromMarkdownSerializer.
"""
import pytest

from content.models import Document
from content.serializers.document import (
    DocumentCreateUpdateSerializer,
    DocumentDetailSerializer,
    DocumentFromMarkdownSerializer,
    DocumentListSerializer,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def document(db):
    """A minimal Document instance."""
    return Document.objects.create(
        title='Test Document',
        client_name='ACME Corp',
        language='es',
        cover_type='generic',
        content_markdown='# Hello',
        content_json={'sections': []},
    )


# ── DocumentListSerializer ─────────────────────────────────────────────────────

class TestDocumentListSerializer:
    def test_serializes_expected_fields(self, document):
        data = DocumentListSerializer(document).data
        expected = {
            'id', 'uuid', 'title', 'slug', 'status', 'client_name',
            'language', 'cover_type', 'include_portada', 'include_subportada',
            'include_contraportada', 'created_at', 'updated_at',
        }
        assert set(data.keys()) == expected

    def test_excludes_content_markdown(self, document):
        data = DocumentListSerializer(document).data
        assert 'content_markdown' not in data

    def test_excludes_content_json(self, document):
        data = DocumentListSerializer(document).data
        assert 'content_json' not in data

    def test_title_value_matches_instance(self, document):
        data = DocumentListSerializer(document).data
        assert data['title'] == 'Test Document'


# ── DocumentDetailSerializer ───────────────────────────────────────────────────

class TestDocumentDetailSerializer:
    def test_includes_content_markdown(self, document):
        data = DocumentDetailSerializer(document).data
        assert 'content_markdown' in data
        assert data['content_markdown'] == '# Hello'

    def test_includes_content_json(self, document):
        data = DocumentDetailSerializer(document).data
        assert 'content_json' in data
        assert data['content_json'] == {'sections': []}

    def test_serializes_all_expected_fields(self, document):
        data = DocumentDetailSerializer(document).data
        expected = {
            'id', 'uuid', 'title', 'slug', 'status',
            'content_markdown', 'content_json', 'client_name',
            'language', 'cover_type', 'include_portada', 'include_subportada',
            'include_contraportada', 'created_at', 'updated_at',
        }
        assert set(data.keys()) == expected


# ── DocumentCreateUpdateSerializer ────────────────────────────────────────────

class TestDocumentCreateUpdateSerializer:
    def test_valid_with_required_title(self):
        serializer = DocumentCreateUpdateSerializer(data={'title': 'New Doc'})
        assert serializer.is_valid(), serializer.errors

    def test_invalid_without_title(self):
        serializer = DocumentCreateUpdateSerializer(data={})
        assert not serializer.is_valid()
        assert 'title' in serializer.errors

    def test_content_markdown_is_optional(self):
        serializer = DocumentCreateUpdateSerializer(data={'title': 'Doc A'})
        assert serializer.is_valid(), serializer.errors
        assert 'content_markdown' not in serializer.errors

    def test_content_json_is_optional(self):
        serializer = DocumentCreateUpdateSerializer(data={'title': 'Doc B'})
        assert serializer.is_valid(), serializer.errors
        assert 'content_json' not in serializer.errors

    def test_invalid_language_choice(self):
        serializer = DocumentCreateUpdateSerializer(
            data={'title': 'Doc', 'language': 'xx'},
        )
        assert not serializer.is_valid()
        assert 'language' in serializer.errors

    def test_invalid_status_choice(self):
        serializer = DocumentCreateUpdateSerializer(
            data={'title': 'Doc', 'status': 'invalid'},
        )
        assert not serializer.is_valid()
        assert 'status' in serializer.errors


# ── DocumentFromMarkdownSerializer ────────────────────────────────────────────

class TestDocumentFromMarkdownSerializer:
    def test_valid_with_title_and_markdown(self):
        serializer = DocumentFromMarkdownSerializer(
            data={'title': 'My Doc', 'markdown': '# Content'},
        )
        assert serializer.is_valid(), serializer.errors

    def test_invalid_without_markdown(self):
        serializer = DocumentFromMarkdownSerializer(data={'title': 'My Doc'})
        assert not serializer.is_valid()
        assert 'markdown' in serializer.errors

    def test_invalid_without_title(self):
        serializer = DocumentFromMarkdownSerializer(data={'markdown': '# Content'})
        assert not serializer.is_valid()
        assert 'title' in serializer.errors

    def test_invalid_language_choice(self):
        serializer = DocumentFromMarkdownSerializer(
            data={'title': 'Doc', 'markdown': '# x', 'language': 'zz'},
        )
        assert not serializer.is_valid()
        assert 'language' in serializer.errors

    def test_defaults_language_to_es(self):
        serializer = DocumentFromMarkdownSerializer(
            data={'title': 'Doc', 'markdown': '# x'},
        )
        assert serializer.is_valid()
        assert serializer.validated_data['language'] == 'es'

    def test_defaults_include_portada_to_true(self):
        serializer = DocumentFromMarkdownSerializer(
            data={'title': 'Doc', 'markdown': '# x'},
        )
        assert serializer.is_valid()
        assert serializer.validated_data['include_portada'] is True

    def test_defaults_client_name_to_empty_string(self):
        serializer = DocumentFromMarkdownSerializer(
            data={'title': 'Doc', 'markdown': '# x'},
        )
        assert serializer.is_valid()
        assert serializer.validated_data['client_name'] == ''
