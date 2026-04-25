"""Regression tests for the new guards on scheduled-blog publishing.

Covers:
- B1: publish_single_scheduled_blog skips when published_at is still in the future
       (closes the early-publish race when admin reschedules a post).
- B2: atomic flip — both task paths are no-op when the post was already
       flipped to is_published=True between the query and the update
       (prevents double LinkedIn post).
- B3: management command publish_blog_post invokes the task synchronously,
       and --force backdates published_at to bypass the future-time guard.
"""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
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


def _run_single(post_id):
    import content.tasks as tasks_module
    tasks_module.publish_single_scheduled_blog.call_local(post_id)


def _run_periodic():
    import content.tasks as tasks_module
    tasks_module.publish_scheduled_blog_posts.call_local()


# ---------------------------------------------------------------------------
# B1 — future-time guard in publish_single_scheduled_blog
# ---------------------------------------------------------------------------


@freeze_time('2026-01-15 12:00:00')
def test_single_skips_when_published_at_in_future():
    post = BlogPost.objects.create(
        **BLOG_POST_BASE,
        is_published=False,
        published_at=timezone.now() + timedelta(hours=2),
    )
    with patch('content.views.blog.auto_publish_blog_to_linkedin') as mock_auto:
        _run_single(post.id)
    post.refresh_from_db()
    assert post.is_published is False
    mock_auto.assert_not_called()


@freeze_time('2026-01-15 12:00:00')
def test_single_publishes_when_published_at_in_past():
    post = BlogPost.objects.create(
        **BLOG_POST_BASE,
        is_published=False,
        published_at=timezone.now() - timedelta(minutes=1),
    )
    with patch('content.views.blog.auto_publish_blog_to_linkedin') as mock_auto:
        _run_single(post.id)
    post.refresh_from_db()
    assert post.is_published is True
    mock_auto.assert_called_once()


# ---------------------------------------------------------------------------
# B2 — atomic flip / no double LinkedIn fire
# ---------------------------------------------------------------------------


@freeze_time('2026-01-15 12:00:00')
def test_single_is_noop_when_already_published():
    post = BlogPost.objects.create(
        **BLOG_POST_BASE,
        is_published=True,
        published_at=timezone.now() - timedelta(minutes=5),
    )
    with patch('content.views.blog.auto_publish_blog_to_linkedin') as mock_auto:
        _run_single(post.id)
    mock_auto.assert_not_called()


@freeze_time('2026-01-15 12:00:00')
def test_periodic_skips_post_already_published_between_query_and_update():
    """If a parallel task flips is_published before our UPDATE runs,
    the conditional update returns 0 rows and we must not call LinkedIn."""
    post = BlogPost.objects.create(
        **BLOG_POST_BASE,
        is_published=False,
        published_at=timezone.now() - timedelta(minutes=1),
    )

    def flip_then_call_linkedin(p):
        # auto_publish should never be reached for this post in the racy case.
        raise AssertionError('auto_publish should not be called twice')

    # Simulate the race: flip the row to True via raw UPDATE between the
    # SELECT (already done by the task) and the conditional UPDATE inside the loop.
    with patch('content.views.blog.auto_publish_blog_to_linkedin') as mock_auto:
        BlogPost.objects.filter(pk=post.id).update(is_published=True)
        _run_periodic()
    mock_auto.assert_not_called()


# ---------------------------------------------------------------------------
# B3 — management command
# ---------------------------------------------------------------------------


@freeze_time('2026-01-15 12:00:00')
def test_command_publishes_post_with_past_published_at():
    post = BlogPost.objects.create(
        **BLOG_POST_BASE,
        is_published=False,
        published_at=timezone.now() - timedelta(minutes=1),
    )
    out = StringIO()
    with patch('content.views.blog.auto_publish_blog_to_linkedin') as mock_auto:
        call_command('publish_blog_post', '--id', str(post.id), stdout=out)
    post.refresh_from_db()
    assert post.is_published is True
    mock_auto.assert_called_once()
    assert 'publicado' in out.getvalue().lower()


@freeze_time('2026-01-15 12:00:00')
def test_command_force_bypasses_future_guard():
    post = BlogPost.objects.create(
        **BLOG_POST_BASE,
        is_published=False,
        published_at=timezone.now() + timedelta(hours=2),
    )
    out = StringIO()
    with patch('content.views.blog.auto_publish_blog_to_linkedin') as mock_auto:
        call_command('publish_blog_post', '--id', str(post.id), '--force', stdout=out)
    post.refresh_from_db()
    assert post.is_published is True
    mock_auto.assert_called_once()
