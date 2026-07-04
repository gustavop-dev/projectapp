"""Publish-now endpoint: success, double-publish guard, failure persistence."""
from unittest.mock import patch

import pytest
from django.urls import reverse

from content.models import LinkedInPost

pytestmark = pytest.mark.django_db

SVC = 'content.services.linkedin_post_service.publish_post_to_linkedin'


@patch(SVC, return_value={'success': True, 'post_id': 'urn:li:share:9', 'message': 'ok'})
def test_publish_success_stamps_fields(mock_pub, admin_client):
    post = LinkedInPost.objects.create(commentary='Hola')
    resp = admin_client.post(reverse('publish-linkedin-post', args=[post.id]))
    assert resp.status_code == 200
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_PUBLISHED
    assert post.linkedin_post_id == 'urn:li:share:9'
    assert post.published_at is not None


@patch(SVC)
def test_already_published_returns_409_and_skips_api(mock_pub, admin_client):
    post = LinkedInPost.objects.create(
        commentary='Hola', status=LinkedInPost.STATUS_PUBLISHED,
    )
    resp = admin_client.post(reverse('publish-linkedin-post', args=[post.id]))
    assert resp.status_code == 409
    mock_pub.assert_not_called()


@patch(SVC, return_value={'success': False, 'post_id': '', 'message': 'LinkedIn API error (500): boom'})
def test_api_failure_sets_failed_status(mock_pub, admin_client):
    post = LinkedInPost.objects.create(commentary='Hola')
    resp = admin_client.post(reverse('publish-linkedin-post', args=[post.id]))
    assert resp.status_code == 502
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_FAILED
    assert 'boom' in post.error_message


@patch(SVC, side_effect=ValueError('LinkedIn not connected. Please authorize first.'))
def test_not_connected_returns_400_and_reverts(mock_pub, admin_client):
    post = LinkedInPost.objects.create(commentary='Hola')
    resp = admin_client.post(reverse('publish-linkedin-post', args=[post.id]))
    assert resp.status_code == 400
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_FAILED


@patch(SVC, return_value={'success': True, 'post_id': 'urn:li:share:9', 'message': 'ok'})
def test_failed_post_can_be_retried(mock_pub, admin_client):
    post = LinkedInPost.objects.create(
        commentary='Hola', status=LinkedInPost.STATUS_FAILED, error_message='old',
    )
    resp = admin_client.post(reverse('publish-linkedin-post', args=[post.id]))
    assert resp.status_code == 200
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_PUBLISHED
    assert post.error_message == ''
