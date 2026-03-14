"""Tests for portfolio works serializers.

Covers: _get_lang context fallback, _validate_portfolio_json error paths,
validate_content_json_en on CreateUpdate and FromJSON serializers.
"""
import pytest
from rest_framework import serializers as drf_serializers

from content.serializers.portfolio_works import (
    PortfolioWorkCreateUpdateSerializer,
    PortfolioWorkDetailSerializer,
    PortfolioWorkFromJSONSerializer,
    PortfolioWorkListSerializer,
    _validate_portfolio_json,
)

pytestmark = pytest.mark.django_db


_VALID_CONTENT_JSON = {
    'problem': {'title': 'P', 'description': 'D'},
    'solution': {'title': 'S', 'description': 'D'},
    'results': {'title': 'R', 'description': 'D'},
}


class TestGetLangContextFallback:
    """Cover _get_lang when context has 'lang' key but no 'request'."""

    def test_lang_from_context_without_request(self, published_portfolio_work):
        """Serializer picks lang from context dict when no request is present."""
        serializer = PortfolioWorkListSerializer(
            published_portfolio_work,
            context={'lang': 'en'},
        )
        assert serializer.data['title'] == published_portfolio_work.title_en

    def test_lang_defaults_to_es_without_request(self, published_portfolio_work):
        """Serializer defaults to Spanish when context has no request and no lang."""
        serializer = PortfolioWorkDetailSerializer(
            published_portfolio_work,
            context={},
        )
        assert serializer.data['title'] == published_portfolio_work.title_es


class TestValidatePortfolioJson:
    """Cover _validate_portfolio_json error paths (lines 224, 226, 234)."""

    def test_rejects_non_dict_value(self):
        """content_json must be a dict."""
        with pytest.raises(drf_serializers.ValidationError, match='must be a JSON object') as exc_info:
            _validate_portfolio_json('not a dict')
        assert 'must be a JSON object' in str(exc_info.value.detail[0])

    def test_rejects_missing_required_key(self):
        """content_json must include problem, solution, and results keys."""
        with pytest.raises(drf_serializers.ValidationError, match='must include a "problem" key') as exc_info:
            _validate_portfolio_json({'solution': {}, 'results': {}})
        assert 'problem' in str(exc_info.value.detail[0])

    def test_rejects_non_dict_section(self):
        """Each section must be a dict."""
        with pytest.raises(drf_serializers.ValidationError, match='must be a JSON object with title') as exc_info:
            _validate_portfolio_json({
                'problem': 'not a dict',
                'solution': {'title': 'S', 'description': 'D'},
                'results': {'title': 'R', 'description': 'D'},
            })
        assert 'problem' in str(exc_info.value.detail[0])

    def test_returns_value_for_falsy_input(self):
        """Empty/None value passes through without validation."""
        assert _validate_portfolio_json(None) is None
        assert _validate_portfolio_json({}) == {}


class TestCreateUpdateSerializerContentJsonEn:
    """Cover validate_content_json_en on PortfolioWorkCreateUpdateSerializer (line 179)."""

    def test_valid_content_json_en_passes_validation(self, db):
        payload = {
            'title_es': 'Titulo',
            'title_en': 'Title',
            'project_url': 'https://example.com',
            'content_json_en': _VALID_CONTENT_JSON,
        }
        serializer = PortfolioWorkCreateUpdateSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['content_json_en'] == _VALID_CONTENT_JSON

    def test_invalid_content_json_en_fails_validation(self, db):
        payload = {
            'title_es': 'Titulo',
            'title_en': 'Title',
            'project_url': 'https://example.com',
            'content_json_en': {'problem': {}},
        }
        serializer = PortfolioWorkCreateUpdateSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'content_json_en' in serializer.errors


class TestFromJSONSerializerContentJsonEn:
    """Cover validate_content_json_en on PortfolioWorkFromJSONSerializer (line 211)."""

    def test_valid_non_empty_content_json_en_passes(self):
        payload = {
            'title_es': 'Titulo',
            'title_en': 'Title',
            'project_url': 'https://example.com',
            'content_json_es': _VALID_CONTENT_JSON,
            'content_json_en': _VALID_CONTENT_JSON,
        }
        serializer = PortfolioWorkFromJSONSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['content_json_en'] == _VALID_CONTENT_JSON

    def test_invalid_non_empty_content_json_en_fails(self):
        payload = {
            'title_es': 'Titulo',
            'title_en': 'Title',
            'project_url': 'https://example.com',
            'content_json_es': _VALID_CONTENT_JSON,
            'content_json_en': {'only_problem': {}},
        }
        serializer = PortfolioWorkFromJSONSerializer(data=payload)
        assert not serializer.is_valid()
        assert 'content_json_en' in serializer.errors
