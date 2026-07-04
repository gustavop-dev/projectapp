"""Guards on scheduled LinkedIn-post publishing (mirrors blog guards).

- L1: ETA task skips when scheduled_at is still in the future (reschedule race).
- L2: task is a no-op when the post was already published (atomic claim).
- L3: periodic sweep publishes due scheduled posts and skips drafts.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from content.models import LinkedInPost

pytestmark = pytest.mark.django_db

SVC = 'content.services.linkedin_post_service.publish_post_to_linkedin'


def _run_single(post_id):
    import content.tasks as tasks_module
    tasks_module.publish_single_scheduled_linkedin_post.call_local(post_id)


def _run_periodic():
    import content.tasks as tasks_module
    tasks_module.publish_scheduled_linkedin_posts.call_local()


@patch(SVC)
def test_eta_task_skips_future_schedule(mock_pub):
    post = LinkedInPost.objects.create(
        commentary='pronto', status=LinkedInPost.STATUS_SCHEDULED,
        scheduled_at=timezone.now() + timedelta(hours=3),
    )
    _run_single(post.id)
    mock_pub.assert_not_called()
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_SCHEDULED


@patch(SVC)
def test_eta_task_noop_when_already_published(mock_pub):
    post = LinkedInPost.objects.create(
        commentary='ya', status=LinkedInPost.STATUS_PUBLISHED,
        scheduled_at=timezone.now() - timedelta(minutes=5),
    )
    _run_single(post.id)
    mock_pub.assert_not_called()
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_PUBLISHED


@patch(SVC, return_value={'success': True, 'post_id': 'urn:li:share:7', 'message': 'ok'})
def test_eta_task_publishes_due_post(mock_pub):
    post = LinkedInPost.objects.create(
        commentary='ahora', status=LinkedInPost.STATUS_SCHEDULED,
        scheduled_at=timezone.now() - timedelta(minutes=1),
    )
    _run_single(post.id)
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_PUBLISHED
    assert post.linkedin_post_id == 'urn:li:share:7'


@patch(SVC, return_value={'success': True, 'post_id': 'urn:li:share:8', 'message': 'ok'})
def test_sweep_publishes_due_and_skips_drafts(mock_pub):
    due = LinkedInPost.objects.create(
        commentary='due', status=LinkedInPost.STATUS_SCHEDULED,
        scheduled_at=timezone.now() - timedelta(minutes=2),
    )
    draft = LinkedInPost.objects.create(commentary='draft')
    _run_periodic()
    due.refresh_from_db()
    draft.refresh_from_db()
    assert due.status == LinkedInPost.STATUS_PUBLISHED
    assert draft.status == LinkedInPost.STATUS_DRAFT
    assert mock_pub.call_count == 1


@patch(SVC, return_value={'success': False, 'post_id': '', 'message': 'err 500'})
def test_failed_publish_marks_failed_and_sweep_does_not_retry(mock_pub):
    post = LinkedInPost.objects.create(
        commentary='falla', status=LinkedInPost.STATUS_SCHEDULED,
        scheduled_at=timezone.now() - timedelta(minutes=2),
    )
    _run_periodic()
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_FAILED
    _run_periodic()
    assert mock_pub.call_count == 1  # failed posts require manual retry
