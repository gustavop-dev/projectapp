"""Tests for blog-related Huey tasks.

Covers: publish_scheduled_blog_posts periodic task.
"""
from datetime import timedelta

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
