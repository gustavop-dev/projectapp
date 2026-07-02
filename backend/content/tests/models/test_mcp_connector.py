"""Tests for the McpConnector model (token lifecycle)."""
import pytest

from content.models import McpConnector


@pytest.mark.django_db
class TestMcpConnectorTokens:
    def _connector(self):
        connector, _ = McpConnector.objects.get_or_create(
            slug='blog',
            defaults={'name': 'Blog Publisher'},
        )
        return connector

    def test_blog_connector_is_seeded_inactive(self):
        connector = McpConnector.objects.get(slug='blog')
        assert connector.is_active is False
        assert connector.token_hash == ''

    def test_generate_token_returns_plaintext_and_stores_hash(self):
        connector = self._connector()
        token = connector.generate_token()
        connector.refresh_from_db()
        assert len(token) >= 40
        assert connector.token_hash != ''
        assert token not in connector.token_hash
        assert connector.token_prefix == token[:8]

    def test_check_token_accepts_current_token_only(self):
        connector = self._connector()
        token = connector.generate_token()
        assert connector.check_token(token) is True
        assert connector.check_token('wrong-token') is False
        assert connector.check_token('') is False

    def test_regenerating_invalidates_previous_token(self):
        connector = self._connector()
        old_token = connector.generate_token()
        new_token = connector.generate_token()
        assert connector.check_token(old_token) is False
        assert connector.check_token(new_token) is True

    def test_check_token_false_when_no_token_generated(self):
        connector = self._connector()
        connector.token_hash = ''
        assert connector.check_token('anything') is False
