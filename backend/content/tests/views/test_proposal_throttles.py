"""Throttling on the public proposal endpoints.

All requests hit nonexistent proposals (cheap 404s) — DRF throttling runs
before the handler, so they still consume the per-IP budget. The autouse
_reset_throttle_cache fixture isolates each test.
"""
import uuid

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

MISSING = uuid.uuid4()


def _hammer(client, method, url, times, payload=None):
    responses = [
        getattr(client, method)(url, payload or {}, format='json')
        for _ in range(times)
    ]
    return [r.status_code for r in responses]


class TestPublicProposalActionThrottle:
    def test_respond_throttled_after_10_per_minute(self, api_client):
        url = reverse('respond-to-proposal', kwargs={'proposal_uuid': MISSING})
        codes = _hammer(api_client, 'post', url, 11)
        assert all(c == 404 for c in codes[:10])
        assert codes[10] == 429

    def test_comment_throttled_after_10_per_minute(self, api_client):
        url = reverse('comment-on-proposal', kwargs={'proposal_uuid': MISSING})
        codes = _hammer(api_client, 'post', url, 11)
        assert codes[10] == 429

    def test_share_link_throttled_after_10_per_minute(self, api_client):
        url = reverse('create-share-link', kwargs={'proposal_uuid': MISSING})
        codes = _hammer(api_client, 'post', url, 11)
        assert codes[10] == 429

    def test_schedule_followup_throttled_after_10_per_minute(self, api_client):
        url = reverse('schedule-followup', kwargs={'proposal_uuid': MISSING})
        codes = _hammer(api_client, 'post', url, 11)
        assert codes[10] == 429


class TestProposalPdfThrottle:
    def test_pdf_download_throttled_after_6_per_minute(self, api_client):
        url = reverse('download-proposal-pdf', kwargs={'proposal_uuid': MISSING})
        codes = _hammer(api_client, 'get', url, 7)
        assert all(c == 404 for c in codes[:6])
        assert codes[6] == 429

    def test_staff_users_are_exempt(self, admin_client):
        url = reverse('download-proposal-pdf', kwargs={'proposal_uuid': MISSING})
        codes = _hammer(admin_client, 'get', url, 8)
        assert all(c == 404 for c in codes)


class TestMagicLinkRequestThrottle:
    def test_magic_link_throttled_after_5_per_minute(self, api_client):
        url = reverse('request-magic-link')
        codes = _hammer(api_client, 'post', url, 6)
        assert 429 not in codes[:5]
        assert codes[5] == 429
