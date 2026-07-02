"""Tests for the Blog Publisher MCP tool handlers."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone as tz

from content.mcp.protocol import ToolError
from content.mcp.tools import BLOG_TOOLS
from content.models import BlogPost


def _tool(name):
    return next(t for t in BLOG_TOOLS if t['name'] == name)


VALID_POST = {
    'title_es': 'Cómo elegir tu stack',
    'title_en': 'How to choose your stack',
    'excerpt_es': 'Resumen corto.',
    'excerpt_en': 'Short summary.',
    'content_json_es': {
        'intro': 'Introducción.',
        'sections': [{'heading': 'Sección', 'content': 'Contenido.'}],
    },
}


class TestGetBlogTemplate:
    def test_returns_template_and_categories(self, db):
        result = _tool('get_blog_template')['handler']({})
        assert 'content_json_es' in result['template']
        assert any(c['slug'] == 'technology' for c in result['available_categories'])


@pytest.mark.django_db
class TestCreateBlogPost:
    def test_creates_draft_and_reports_status(self):
        result = _tool('create_blog_post')['handler'](dict(VALID_POST))
        assert result['status'] == 'draft'
        post = BlogPost.objects.get(pk=result['id'])
        assert post.is_published is False
        assert result['public_url'].endswith(f"/{post.slug}")

    def test_scheduled_create_enqueues_huey_task(self):
        future = (tz.now() + timedelta(days=2)).isoformat()
        args = dict(VALID_POST, is_published=False, published_at=future)
        with patch('content.tasks.publish_single_scheduled_blog') as mock_task:
            result = _tool('create_blog_post')['handler'](args)
        assert result['status'] == 'scheduled'
        assert mock_task.schedule.call_count == 1

    def test_invalid_payload_raises_tool_error_with_field_names(self):
        with pytest.raises(ToolError) as exc:
            _tool('create_blog_post')['handler']({'title_es': 'solo esto'})
        assert 'title_en' in str(exc.value)


@pytest.mark.django_db
class TestUpdateBlogPost:
    def test_partial_update_changes_fields(self, draft_blog_post):
        result = _tool('update_blog_post')['handler']({
            'post_id': draft_blog_post.id,
            'title_es': 'Título corregido',
        })
        draft_blog_post.refresh_from_db()
        assert draft_blog_post.title_es == 'Título corregido'
        assert result['id'] == draft_blog_post.id

    def test_unknown_post_raises_tool_error(self):
        with pytest.raises(ToolError) as exc:
            _tool('update_blog_post')['handler']({'post_id': 99999, 'title_es': 'x'})
        assert 'No existe un blog post con id=99999' in str(exc.value)


@pytest.mark.django_db
class TestDeleteBlogPost:
    def test_deletes_draft(self, draft_blog_post):
        result = _tool('delete_blog_post')['handler']({'post_id': draft_blog_post.id})
        assert result['deleted'] is True
        assert not BlogPost.objects.filter(pk=draft_blog_post.id).exists()

    def test_refuses_to_delete_published_post(self, blog_post):
        assert blog_post.is_published is True
        with pytest.raises(ToolError) as exc:
            _tool('delete_blog_post')['handler']({'post_id': blog_post.id})
        assert BlogPost.objects.filter(pk=blog_post.id).exists()
        assert 'publicado' in str(exc.value)


@pytest.mark.django_db
class TestListBlogPosts:
    def test_lists_with_status_and_pagination(self, blog_post, draft_blog_post):
        result = _tool('list_blog_posts')['handler']({'page': 1, 'page_size': 10})
        assert result['count'] == 2
        statuses = {p['id']: p['status'] for p in result['results']}
        assert statuses[blog_post.id] == 'published'
        assert statuses[draft_blog_post.id] == 'draft'


@pytest.mark.django_db
class TestGetBlogCalendar:
    def test_returns_posts_in_range(self, blog_post):
        today = tz.now().strftime('%Y-%m-%d')
        result = _tool('get_blog_calendar')['handler']({'start': today, 'end': today})
        assert any(p['id'] == blog_post.id for p in result['posts'])

    def test_invalid_dates_raise_tool_error(self):
        with pytest.raises(ToolError) as exc:
            _tool('get_blog_calendar')['handler']({'start': 'ayer', 'end': 'hoy'})
        assert 'YYYY-MM-DD' in str(exc.value)
