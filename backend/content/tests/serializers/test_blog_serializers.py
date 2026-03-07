"""Tests for blog serializers — _get_lang helper, language-resolved fields,
validate_sources, _validate_content_json, BlogPostFromJSONSerializer."""
import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from content.serializers.blog import (
    BlogPostCreateUpdateSerializer,
    BlogPostDetailSerializer,
    BlogPostFromJSONSerializer,
    BlogPostListSerializer,
    _validate_content_json,
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


class TestBlogPostDetailSerializerNewFields:
    def test_content_json_resolved_by_lang(self, blog_post_with_json):
        request = _make_request(lang='es')
        serializer = BlogPostDetailSerializer(blog_post_with_json, context={'request': request})
        assert serializer.data['content_json']['intro'] == 'Introducción en español.'

    def test_content_json_resolved_en(self, blog_post_with_json):
        request = _make_request(lang='en')
        serializer = BlogPostDetailSerializer(blog_post_with_json, context={'request': request})
        assert serializer.data['content_json']['intro'] == 'Introduction in English.'

    def test_meta_title_resolved_by_lang(self, blog_post_with_json):
        blog_post_with_json.meta_title_es = 'Título SEO ES'
        blog_post_with_json.meta_title_en = 'SEO Title EN'
        blog_post_with_json.save()
        request = _make_request(lang='en')
        serializer = BlogPostDetailSerializer(blog_post_with_json, context={'request': request})
        assert serializer.data['meta_title'] == 'SEO Title EN'

    def test_includes_category_and_read_time(self, blog_post_with_json):
        serializer = BlogPostDetailSerializer(blog_post_with_json, context={})
        assert serializer.data['category'] == 'technology'
        assert serializer.data['read_time_minutes'] == 8
        assert serializer.data['is_featured'] is True


class TestValidateContentJson:
    """Tests for the _validate_content_json helper function."""

    def test_valid_schema_passes(self):
        value = {'intro': 'I', 'sections': [{'heading': 'H'}], 'conclusion': 'C', 'cta': 'A'}
        result = _validate_content_json(value)
        assert result == value

    def test_empty_dict_passes(self):
        """Empty dict is valid — no content_json provided yet."""
        result = _validate_content_json({})
        assert result == {}

    def test_none_passes(self):
        """None is valid — field not provided."""
        result = _validate_content_json(None)
        assert result is None

    def test_non_dict_rejected(self):
        from rest_framework import serializers
        with pytest.raises(serializers.ValidationError) as exc_info:
            _validate_content_json('not a dict')
        assert 'JSON object' in str(exc_info.value.detail)

    def test_missing_intro_rejected(self):
        from rest_framework import serializers
        with pytest.raises(serializers.ValidationError) as exc_info:
            _validate_content_json({'sections': []})
        assert 'intro' in str(exc_info.value.detail)

    def test_missing_sections_rejected(self):
        from rest_framework import serializers
        with pytest.raises(serializers.ValidationError) as exc_info:
            _validate_content_json({'intro': 'I'})
        assert 'sections' in str(exc_info.value.detail)

    def test_sections_not_list_rejected(self):
        from rest_framework import serializers
        with pytest.raises(serializers.ValidationError) as exc_info:
            _validate_content_json({'intro': 'I', 'sections': 'not a list'})
        assert 'list' in str(exc_info.value.detail)

    def test_section_without_heading_rejected(self):
        from rest_framework import serializers
        with pytest.raises(serializers.ValidationError) as exc_info:
            _validate_content_json({'intro': 'I', 'sections': [{'content': 'no heading'}]})
        assert 'heading' in str(exc_info.value.detail)

    def test_non_dict_section_rejected(self):
        from rest_framework import serializers
        with pytest.raises(serializers.ValidationError) as exc_info:
            _validate_content_json({'intro': 'I', 'sections': ['string']})
        assert 'JSON object' in str(exc_info.value.detail)


class TestBlogPostFromJSONSerializer:
    def test_valid_payload_passes(self):
        payload = {
            'title_es': 'T ES', 'title_en': 'T EN',
            'excerpt_es': 'E ES', 'excerpt_en': 'E EN',
            'content_json_es': {'intro': 'I', 'sections': [{'heading': 'H'}]},
        }
        serializer = BlogPostFromJSONSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors

    def test_missing_title_en_rejected(self):
        payload = {
            'title_es': 'T ES',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_json_es': {'intro': 'I', 'sections': []},
        }
        serializer = BlogPostFromJSONSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'title_en' in serializer.errors

    def test_missing_content_json_es_rejected(self):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
        }
        serializer = BlogPostFromJSONSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'content_json_es' in serializer.errors

    def test_invalid_content_json_es_rejected(self):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_json_es': {'no_intro': True},
        }
        serializer = BlogPostFromJSONSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'content_json_es' in serializer.errors

    def test_optional_fields_default_correctly(self):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_json_es': {'intro': 'I', 'sections': []},
        }
        serializer = BlogPostFromJSONSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        data = serializer.validated_data
        assert data['category'] == ''
        assert data['read_time_minutes'] == 0
        assert data['is_featured'] is False
        assert data['sources'] == []

    def test_invalid_sources_rejected(self):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_json_es': {'intro': 'I', 'sections': []},
            'sources': [{'name': 'No URL'}],
        }
        serializer = BlogPostFromJSONSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'sources' in serializer.errors

    def test_content_json_en_optional_empty(self):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_json_es': {'intro': 'I', 'sections': []},
            'content_json_en': {},
        }
        serializer = BlogPostFromJSONSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
