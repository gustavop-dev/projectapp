"""Tests for blog-related Huey tasks.

Covers: publish_scheduled_blog_posts periodic task.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from content.models import BlogPost

pytestmark = pytest.mark.django_db


BLOG_POST_BASE = {
    'title_es': 'Post programado',
    'title_en': 'Scheduled post',
    'excerpt_es': 'Extracto.',
    'excerpt_en': 'Excerpt.',
    'content_es': '<p>C</p>',
    'content_en': '<p>C</p>',
}


def _run_publish_task():
    """Execute the publish_scheduled_blog_posts task synchronously."""
    import content.tasks as tasks_module
    tasks_module.publish_scheduled_blog_posts.call_local()


class TestPublishScheduledBlogPosts:
    @freeze_time('2026-01-15 12:00:00')
    def test_publishes_post_with_past_published_at(self):
        """A draft post with published_at in the past gets published."""
        post = BlogPost.objects.create(
            **BLOG_POST_BASE,
            is_published=False,
            published_at=timezone.now() - timedelta(minutes=5),
        )
        _run_publish_task()
        post.refresh_from_db()
        assert post.is_published is True

    @freeze_time('2026-01-15 12:00:00')
    def test_does_not_publish_post_with_future_published_at(self):
        """A draft post with published_at in the future stays as draft."""
        post = BlogPost.objects.create(
            **BLOG_POST_BASE,
            is_published=False,
            published_at=timezone.now() + timedelta(hours=2),
        )
        _run_publish_task()
        post.refresh_from_db()
        assert post.is_published is False

    @freeze_time('2026-01-15 12:00:00')
    def test_does_not_affect_already_published_posts(self):
        """Already published posts are not re-processed."""
        post = BlogPost.objects.create(
            **BLOG_POST_BASE,
            is_published=True,
            published_at=timezone.now() - timedelta(days=1),
        )
        _run_publish_task()
        post.refresh_from_db()
        assert post.is_published is True

    def test_does_not_publish_draft_without_published_at(self):
        """A plain draft (no published_at) remains unpublished."""
        post = BlogPost.objects.create(
            **BLOG_POST_BASE,
            is_published=False,
            published_at=None,
        )
        _run_publish_task()
        post.refresh_from_db()
        assert post.is_published is False

    @freeze_time('2026-01-15 12:00:00')
    def test_publishes_multiple_scheduled_posts(self):
        """Multiple scheduled posts with past dates are all published."""
        posts = []
        for i in range(3):
            p = BlogPost.objects.create(
                title_es=f'Post {i}',
                title_en=f'Post {i}',
                excerpt_es='E',
                excerpt_en='E',
                content_es='C',
                content_en='C',
                is_published=False,
                published_at=timezone.now() - timedelta(minutes=i + 1),
            )
            posts.append(p)
        _run_publish_task()
        for p in posts:
            p.refresh_from_db()
            assert p.is_published is True

    @freeze_time('2026-01-15 12:00:00')
    def test_scheduled_publish_triggers_linkedin_auto_publish(self):
        """Scheduled publication also fires the LinkedIn auto-publish pipeline,
        so the post reaches LinkedIn without admins having to manually re-publish."""
        post = BlogPost.objects.create(
            **BLOG_POST_BASE,
            is_published=False,
            published_at=timezone.now() - timedelta(minutes=1),
            linkedin_summary_es='Resumen para LinkedIn.',
        )
        with patch('content.views.blog.auto_publish_blog_to_linkedin') as mock_auto:
            _run_publish_task()
            mock_auto.assert_called_once()
            called_post = mock_auto.call_args[0][0]
            assert called_post.id == post.id

        post.refresh_from_db()
        assert post.is_published is True


def _run_single_publish(post_id):
    """Execute the publish_single_scheduled_blog one-shot task synchronously."""
    import content.tasks as tasks_module
    tasks_module.publish_single_scheduled_blog.call_local(post_id)


class TestPublishSingleScheduledBlog:
    def test_publishes_draft_and_triggers_linkedin(self):
        post = BlogPost.objects.create(
            **BLOG_POST_BASE,
            is_published=False,
            published_at=timezone.now() - timedelta(seconds=1),
            linkedin_summary_es='Resumen.',
        )
        with patch('content.views.blog.auto_publish_blog_to_linkedin') as mock_auto:
            _run_single_publish(post.id)
            mock_auto.assert_called_once()
            assert mock_auto.call_args[0][0].id == post.id

        post.refresh_from_db()
        assert post.is_published is True

    def test_skips_if_already_published(self):
        post = BlogPost.objects.create(
            **BLOG_POST_BASE,
            is_published=True,
            published_at=timezone.now() - timedelta(days=1),
        )
        with patch('content.views.blog.auto_publish_blog_to_linkedin') as mock_auto:
            _run_single_publish(post.id)
            mock_auto.assert_not_called()

    def test_skips_when_post_missing(self):
        with patch('content.views.blog.auto_publish_blog_to_linkedin') as mock_auto:
            _run_single_publish(999999)
            mock_auto.assert_not_called()

    def test_skips_when_no_published_at(self):
        post = BlogPost.objects.create(
            **BLOG_POST_BASE,
            is_published=False,
            published_at=None,
        )
        with patch('content.views.blog.auto_publish_blog_to_linkedin') as mock_auto:
            _run_single_publish(post.id)
            mock_auto.assert_not_called()
        post.refresh_from_db()
        assert post.is_published is False
