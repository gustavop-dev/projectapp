"""Tests for the post_save signals added in accounts/signals.py:
- ``ensure_user_profile``: every User must end up with a UserProfile.
- ``sync_proposals_on_profile_save``/``sync_proposals_on_user_save``:
  BusinessProposal client snapshot fields stay in sync with the canonical
  UserProfile/User identity.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TransactionTestCase

from accounts.models import UserProfile
from content.models import BusinessProposal

User = get_user_model()


class EnsureUserProfileSignalTests(TransactionTestCase):
    """TransactionTestCase actually commits, so transaction.on_commit fires."""

    def test_creates_client_profile_for_regular_user(self):
        user = User.objects.create_user(
            username='auto-client@t.com', email='auto-client@t.com', password='x',
        )
        assert UserProfile.objects.get(user=user).role == UserProfile.ROLE_CLIENT

    def test_creates_admin_profile_for_superuser(self):
        user = User.objects.create_superuser(
            username='auto-admin@t.com', email='auto-admin@t.com', password='x',
        )
        assert UserProfile.objects.get(user=user).role == UserProfile.ROLE_ADMIN

    def test_explicit_profile_inside_atomic_wins_over_signal(self):
        """Contract: services that need a non-default role must wrap User+
        Profile creation in transaction.atomic so the on_commit signal
        sees the explicit profile and becomes a no-op."""
        with transaction.atomic():
            user = User.objects.create_user(
                username='explicit@t.com', email='explicit@t.com', password='x',
            )
            UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN)
        assert UserProfile.objects.filter(user=user).count() == 1
        assert UserProfile.objects.get(user=user).role == UserProfile.ROLE_ADMIN


@pytest.mark.django_db
def test_sync_proposals_on_profile_save_updates_phone_snapshot():
    user = User.objects.create_user(
        username='sync-c@t.com', email='sync-c@t.com', password='x',
        first_name='Old', last_name='Name',
    )
    profile = UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT, phone='000',
    )
    proposal = BusinessProposal.objects.create(
        title='P1', client=profile,
        client_name='Old Name', client_email='sync-c@t.com', client_phone='000',
    )

    profile.phone = '999'
    profile.save()

    proposal.refresh_from_db()
    assert proposal.client_phone == '999'


@pytest.mark.django_db
def test_sync_proposals_on_user_save_updates_name_snapshot():
    user = User.objects.create_user(
        username='sync-u@t.com', email='sync-u@t.com', password='x',
        first_name='Old', last_name='Name',
    )
    profile = UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT, phone='000',
    )
    proposal = BusinessProposal.objects.create(
        title='P2', client=profile,
        client_name='Old Name', client_email='sync-u@t.com', client_phone='000',
    )

    user.first_name = 'New'
    user.save()

    proposal.refresh_from_db()
    assert proposal.client_name == 'New Name'


@pytest.mark.django_db
def test_sync_skipped_for_admin_profile_save():
    """Saving an admin profile must not touch BusinessProposal rows."""
    client_user = User.objects.create_user(
        username='c@t.com', email='c@t.com', password='x',
        first_name='Cli', last_name='Ent',
    )
    client_profile = UserProfile.objects.create(
        user=client_user, role=UserProfile.ROLE_CLIENT,
    )
    proposal = BusinessProposal.objects.create(
        title='P3', client=client_profile,
        client_name='Cli Ent', client_email='c@t.com', client_phone='',
    )
    snapshot_updated_at = proposal.updated_at

    admin_user = User.objects.create_user(
        username='a@t.com', email='a@t.com', password='x',
    )
    admin_profile = UserProfile.objects.create(
        user=admin_user, role=UserProfile.ROLE_ADMIN, phone='123',
    )
    admin_profile.phone = '456'
    admin_profile.save()

    proposal.refresh_from_db()
    assert proposal.updated_at == snapshot_updated_at
