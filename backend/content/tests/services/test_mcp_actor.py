"""Tests for content.mcp.actor.mcp_actor — actor resolution for MCP writes.

MCP tool handlers have no request.user, so accounting/task writes resolve an
attribution actor here: the configured superuser, else the first active
superuser, else a ToolError (surfaced to the model, not a 500).
"""
import pytest
from django.contrib.auth import get_user_model

from content.mcp.actor import mcp_actor
from content.mcp.protocol import ToolError

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_returns_configured_superuser_by_username(settings):
    settings.MCP_ACTOR_USERNAME = 'mcp-bot'
    User.objects.create_superuser(username='decoy', email='decoy@t.com', password='p')
    bot = User.objects.create_superuser(username='mcp-bot', email='bot@t.com', password='p')

    assert mcp_actor() == bot


def test_raises_when_configured_username_has_no_superuser(settings):
    settings.MCP_ACTOR_USERNAME = 'ghost'
    User.objects.create_superuser(username='real', email='real@t.com', password='p')

    with pytest.raises(ToolError) as exc:
        mcp_actor()
    assert 'superuser' in str(exc.value)


def test_falls_back_to_first_active_superuser_by_pk(settings):
    settings.MCP_ACTOR_USERNAME = ''
    User.objects.create_superuser(username='first-su', email='first@t.com', password='p')
    User.objects.create_superuser(username='second-su', email='second@t.com', password='p')

    expected = User.objects.filter(
        is_superuser=True, is_active=True,
    ).order_by('pk').first()
    assert mcp_actor() == expected


def test_raises_when_no_active_superuser_exists(settings):
    settings.MCP_ACTOR_USERNAME = ''
    User.objects.filter(is_superuser=True).delete()
    User.objects.create_user(username='plain', email='plain@t.com', password='p')

    with pytest.raises(ToolError) as exc:
        mcp_actor()
    assert 'superuser' in str(exc.value)
