"""CRUD views for freeform LinkedIn posts (session-auth admin API)."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from content.models import LinkedInPost

pytestmark = pytest.mark.django_db


def test_list_returns_posts_newest_first(admin_client):
    LinkedInPost.objects.create(commentary='uno')
    LinkedInPost.objects.create(commentary='dos')
    resp = admin_client.get(reverse('list-linkedin-posts'))
    assert resp.status_code == 200
    assert [p['commentary'] for p in resp.data] == ['dos', 'uno']


def test_create_draft(admin_client):
    resp = admin_client.post(reverse('create-linkedin-post'), {'commentary': 'Hola'})
    assert resp.status_code == 201
    assert resp.data['status'] == 'draft'


@freeze_time('2026-01-15 12:00:00')
@patch('content.services.linkedin_post_service.schedule_linkedin_post_eta')
def test_create_with_future_schedule_sets_scheduled(mock_eta, admin_client):
    eta = (timezone.now() + timedelta(hours=2)).isoformat()
    resp = admin_client.post(
        reverse('create-linkedin-post'), {'commentary': 'Hola', 'scheduled_at': eta},
    )
    assert resp.status_code == 201
    assert resp.data['status'] == 'scheduled'
    mock_eta.assert_called_once()


@freeze_time('2026-01-15 12:00:00')
def test_create_with_past_schedule_rejected(admin_client):
    eta = (timezone.now() - timedelta(hours=1)).isoformat()
    resp = admin_client.post(
        reverse('create-linkedin-post'), {'commentary': 'Hola', 'scheduled_at': eta},
    )
    assert resp.status_code == 400


def test_update_published_post_conflict(admin_client):
    post = LinkedInPost.objects.create(
        commentary='ya salió', status=LinkedInPost.STATUS_PUBLISHED,
    )
    resp = admin_client.put(
        reverse('update-linkedin-post', args=[post.id]), {'commentary': 'edit'},
    )
    assert resp.status_code == 409


@freeze_time('2026-01-15 12:00:00')
def test_update_clearing_schedule_reverts_to_draft(admin_client):
    post = LinkedInPost.objects.create(
        commentary='prog', status=LinkedInPost.STATUS_SCHEDULED,
        scheduled_at=timezone.now() + timedelta(hours=1),
    )
    resp = admin_client.put(
        reverse('update-linkedin-post', args=[post.id]),
        {'commentary': 'prog', 'scheduled_at': ''},
    )
    assert resp.status_code == 200
    assert resp.data['status'] == 'draft'


def test_delete_post(admin_client):
    post = LinkedInPost.objects.create(commentary='bye')
    resp = admin_client.delete(reverse('delete-linkedin-post', args=[post.id]))
    assert resp.status_code == 204
    assert not LinkedInPost.objects.filter(pk=post.id).exists()


def test_requires_admin(api_client):
    resp = api_client.get(reverse('list-linkedin-posts'))
    assert resp.status_code in (401, 403)
