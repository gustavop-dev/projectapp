"""Tests for blog serializers — _get_lang helper, language-resolved fields, validate_sources."""
import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from content.serializers.blog import (
    BlogPostCreateUpdateSerializer,
    BlogPostDetailSerializer,
    BlogPostListSerializer,
)

pytestmark = pytest.mark.django_db

_factory = APIRequestFactory()


def _make_request(lang=None):
    params = {'lang': lang} if lang else {}
    return Request(_factory.get('/', params))


class TestGetLangHelper:
    def test_defaults_to_es_without_request(self, blog_post):
        serializer = BlogPostListSerializer(blog_post, context={})
        assert serializer.data['title'] == blog_post.title_es

    def test_returns_en_with_lang_query_param(self, blog_post):
        request = _make_request(lang='en')
        serializer = BlogPostListSerializer(blog_post, context={'request': request})
        assert serializer.data['title'] == blog_post.title_en

    def test_returns_es_with_lang_query_param(self, blog_post):
        request = _make_request(lang='es')
        serializer = BlogPostListSerializer(blog_post, context={'request': request})
        assert serializer.data['title'] == blog_post.title_es

    def test_falls_back_to_es_for_invalid_lang(self, blog_post):
        request = _make_request(lang='fr')
        serializer = BlogPostListSerializer(blog_post, context={'request': request})
        assert serializer.data['title'] == blog_post.title_es

    def test_uses_context_lang_without_request(self, blog_post):
        serializer = BlogPostListSerializer(blog_post, context={'lang': 'en'})
        assert serializer.data['title'] == blog_post.title_en


class TestBlogPostDetailSerializerLang:
    def test_content_field_resolved_by_lang(self, blog_post):
        request = _make_request(lang='en')
        serializer = BlogPostDetailSerializer(blog_post, context={'request': request})
        assert serializer.data['content'] == blog_post.content_en

    def test_excerpt_field_resolved_by_lang(self, blog_post):
        request = _make_request(lang='en')
        serializer = BlogPostDetailSerializer(blog_post, context={'request': request})
        assert serializer.data['excerpt'] == blog_post.excerpt_en


class TestValidateSources:
    def test_rejects_non_list_sources(self, admin_user):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_es': 'C', 'content_en': 'C',
            'sources': 'not a list',
        }
        serializer = BlogPostCreateUpdateSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'sources' in serializer.errors

    def test_rejects_non_dict_items_in_sources(self):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_es': 'C', 'content_en': 'C',
            'sources': ['not a dict'],
        }
        serializer = BlogPostCreateUpdateSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'sources' in serializer.errors

    def test_rejects_source_missing_name_key(self):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_es': 'C', 'content_en': 'C',
            'sources': [{'url': 'https://example.com'}],
        }
        serializer = BlogPostCreateUpdateSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'sources' in serializer.errors

    def test_rejects_source_missing_url_key(self):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_es': 'C', 'content_en': 'C',
            'sources': [{'name': 'Source'}],
        }
        serializer = BlogPostCreateUpdateSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'sources' in serializer.errors

    def test_accepts_valid_sources(self):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_es': 'C', 'content_en': 'C',
            'sources': [{'name': 'Source', 'url': 'https://example.com'}],
        }
        serializer = BlogPostCreateUpdateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
