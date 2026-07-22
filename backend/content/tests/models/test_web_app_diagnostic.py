"""Model-level tests for WebAppDiagnostic expiration."""
from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from content.models import WebAppDiagnostic

pytestmark = pytest.mark.django_db


def test_is_expired_false_without_expiry(diagnostic):
    assert diagnostic.expires_at is None
    assert diagnostic.is_expired is False
    assert diagnostic.days_remaining is None


def test_is_expired_true_when_status_expired(diagnostic):
    diagnostic.status = WebAppDiagnostic.Status.EXPIRED
    assert diagnostic.is_expired is True


@freeze_time('2026-01-15 12:00:00')
def test_is_expired_true_when_past_expiry(diagnostic):
    diagnostic.expires_at = timezone.now() - timedelta(days=1)
    assert diagnostic.is_expired is True


@freeze_time('2026-01-15 12:00:00')
def test_is_expired_false_when_future_expiry(diagnostic):
    diagnostic.expires_at = timezone.now() + timedelta(days=5)
    assert diagnostic.is_expired is False


@freeze_time('2026-01-15 12:00:00')
def test_days_remaining_counts_whole_days(diagnostic):
    diagnostic.expires_at = timezone.now() + timedelta(days=3, hours=2)
    assert diagnostic.days_remaining == 3


@freeze_time('2026-01-15 12:00:00')
def test_days_remaining_floors_at_zero(diagnostic):
    diagnostic.expires_at = timezone.now() - timedelta(days=2)
    assert diagnostic.days_remaining == 0
