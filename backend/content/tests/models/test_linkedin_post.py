"""LinkedInPost model: defaults and status choices."""
import pytest

from content.models import LinkedInPost

pytestmark = pytest.mark.django_db


def test_create_post_defaults_to_draft():
    post = LinkedInPost.objects.create(commentary='Hola LinkedIn')
    assert post.status == LinkedInPost.STATUS_DRAFT
    assert post.scheduled_at is None
    assert post.published_at is None
    assert post.linkedin_post_id == ''
    assert post.error_message == ''


def test_str_shows_truncated_commentary():
    post = LinkedInPost.objects.create(commentary='x' * 80)
    assert str(post).startswith('x' * 40)
