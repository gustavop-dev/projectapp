"""
Unit tests for accounts.services.proposal_client_service.

Covers the get-or-create, update, delete, and snapshot helpers used by the
proposal admin panel to wire ``BusinessProposal.client`` to a real
``UserProfile``.
"""

import pytest
from django.contrib.auth import get_user_model

from accounts.models import Project, UserProfile
from accounts.services import proposal_client_service
from content.models.business_proposal import BusinessProposal

User = get_user_model()


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# get_or_create_client_for_proposal
# ---------------------------------------------------------------------------

class TestGetOrCreateClientForProposal:
    def test_creates_new_user_and_profile_from_inline_email(self):
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name='Sofia Aguirre',
            email='sofia@gmail.com',
            phone='+57 300 1111',
            company='Aguirre Studio',
        )
        assert profile.role == UserProfile.ROLE_CLIENT
        assert profile.user.email == 'sofia@gmail.com'
        assert profile.user.first_name == 'Sofia'
        assert profile.user.last_name == 'Aguirre'
        assert profile.phone == '+57 300 1111'
        assert profile.company_name == 'Aguirre Studio'
        assert profile.is_email_placeholder is False

    def test_reuses_existing_client_when_email_matches_case_insensitive(self):
        first = proposal_client_service.get_or_create_client_for_proposal(
            name='Mateo Ruiz', email='mateo@gmail.com',
        )
        second = proposal_client_service.get_or_create_client_for_proposal(
            name='Mateo R.', email='MATEO@gmail.com',
        )
        assert first.pk == second.pk

    def test_fills_missing_company_on_existing_profile(self):
        first = proposal_client_service.get_or_create_client_for_proposal(
            name='Carmen', email='carmen@gmail.com',
        )
        assert first.company_name == ''
        second = proposal_client_service.get_or_create_client_for_proposal(
            name='Carmen', email='carmen@gmail.com', company='LateCo',
        )
        assert second.pk == first.pk
        assert second.company_name == 'LateCo'

    def test_does_not_overwrite_existing_company(self):
        first = proposal_client_service.get_or_create_client_for_proposal(
            name='Lucia', email='lucia@gmail.com', company='OriginalCo',
        )
        second = proposal_client_service.get_or_create_client_for_proposal(
            name='Lucia', email='lucia@gmail.com', company='OtherCo',
        )
        assert second.company_name == 'OriginalCo'

    def test_generates_placeholder_when_email_is_blank(self):
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name='Sin Email', email='',
        )
        assert profile.is_email_placeholder is True
        assert profile.user.email == f'cliente_{profile.pk}@temp.example.com'
        assert profile.user.username == f'cliente_{profile.pk}'

    def test_generates_unique_placeholders_for_each_blank_email(self):
        first = proposal_client_service.get_or_create_client_for_proposal(name='A', email='')
        second = proposal_client_service.get_or_create_client_for_proposal(name='B', email='')
        assert first.pk != second.pk
        assert first.user.email != second.user.email

    def test_falls_through_to_placeholder_when_email_belongs_to_admin(self):
        admin_user = User.objects.create_user(
            username='admin@gmail.com',
            email='admin@gmail.com',
            password='pwd',
        )
        UserProfile.objects.create(
            user=admin_user, role=UserProfile.ROLE_ADMIN, is_onboarded=True,
        )
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name='Reuser', email='admin@gmail.com',
        )
        # Did NOT reuse the admin user — got a fresh placeholder profile.
        assert profile.user.pk != admin_user.pk
        assert profile.is_email_placeholder is True


# ---------------------------------------------------------------------------
# update_client_profile + sync_snapshot
# ---------------------------------------------------------------------------

class TestUpdateClientProfile:
    def test_update_client_profile_changes_user_and_cascades_snapshots(self):
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name='Ana Vega', email='ana@gmail.com',
        )
        # Create two proposals via service to mirror real wiring.
        p1 = BusinessProposal.objects.create(
            title='P1', client_name='Ana Vega', client_email='ana@gmail.com',
            client=profile, total_investment=1000,
        )
        p2 = BusinessProposal.objects.create(
            title='P2', client_name='Ana Vega', client_email='ana@gmail.com',
            client=profile, total_investment=2000,
        )

        proposal_client_service.update_client_profile(
            profile, name='Ana Maria Vega', phone='+57 300 9999',
        )

        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.client_name == 'Ana Maria Vega'
        assert p1.client_phone == '+57 300 9999'
        assert p2.client_name == 'Ana Maria Vega'
        assert p2.client_phone == '+57 300 9999'

    def test_update_client_profile_rejects_email_collision_with_other_user(self):
        a = proposal_client_service.get_or_create_client_for_proposal(
            name='A', email='a@gmail.com',
        )
        proposal_client_service.get_or_create_client_for_proposal(
            name='B', email='b@gmail.com',
        )
        with pytest.raises(ValueError, match='b@gmail.com'):
            proposal_client_service.update_client_profile(a, email='b@gmail.com')

    def test_clearing_email_to_blank_falls_back_to_placeholder(self):
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name='To Clear', email='clear@gmail.com',
        )
        proposal_client_service.update_client_profile(profile, email='')
        profile.user.refresh_from_db()
        assert profile.user.email == f'cliente_{profile.pk}@temp.example.com'

    def test_sync_snapshot_copies_canonical_fields_to_proposal(self):
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name='Sync Test', email='sync@gmail.com', phone='+57 300', company='SyncCo',
        )
        # Build a proposal with stale snapshot fields, then sync.
        proposal = BusinessProposal.objects.create(
            title='Sync',
            client_name='Stale Name',
            client_email='stale@example.com',
            client_phone='000',
            client=profile,
            total_investment=500,
        )
        proposal_client_service.sync_snapshot(proposal)
        proposal.refresh_from_db()
        assert proposal.client_name == 'Sync Test'
        assert proposal.client_email == 'sync@gmail.com'
        assert proposal.client_phone == '+57 300'


# ---------------------------------------------------------------------------
# delete_orphan_client
# ---------------------------------------------------------------------------

class TestDeleteOrphanClient:
    def test_deletes_orphan_with_zero_proposals_and_projects(self):
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name='Orphan', email='orphan@gmail.com',
        )
        user_pk = profile.user.pk
        proposal_client_service.delete_orphan_client(profile)
        assert not UserProfile.objects.filter(pk=profile.pk).exists()
        assert not User.objects.filter(pk=user_pk).exists()

    def test_blocks_deletion_when_client_has_proposals(self):
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name='Has Proposal', email='hasprop@gmail.com',
        )
        BusinessProposal.objects.create(
            title='X', client_name='Has Proposal', client_email='hasprop@gmail.com',
            client=profile, total_investment=1,
        )
        with pytest.raises(ValueError, match='client_has_proposals:1'):
            proposal_client_service.delete_orphan_client(profile)

    def test_blocks_deletion_when_client_has_platform_projects(self):
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name='Has Project', email='hasproj@gmail.com',
        )
        Project.objects.create(
            name='Live Project', client=profile.user, status=Project.STATUS_ACTIVE,
        )
        with pytest.raises(ValueError, match='client_has_projects:1'):
            proposal_client_service.delete_orphan_client(profile)


# ---------------------------------------------------------------------------
# generate_placeholder_email
# ---------------------------------------------------------------------------

class TestGeneratePlaceholderEmail:
    def test_format_includes_profile_id_and_temp_domain(self):
        assert (
            proposal_client_service.generate_placeholder_email(42)
            == 'cliente_42@temp.example.com'
        )
