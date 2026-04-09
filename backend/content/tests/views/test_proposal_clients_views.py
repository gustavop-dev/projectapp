"""
End-to-end tests for the proposal-side client management endpoints.

Covers ``/api/proposals/client-profiles/`` (list, search, retrieve, create,
update, delete) plus the integration with proposal create/update via
``client_id``.
"""

import pytest
from django.urls import reverse

from accounts.models import Project, UserProfile
from accounts.services import proposal_client_service
from content.models.business_proposal import BusinessProposal


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def real_client_with_proposal(db):
    """Active client with one proposal — should never be considered orphan."""
    profile = proposal_client_service.get_or_create_client_for_proposal(
        name='Activa Mendoza', email='activa@gmail.com', company='ActivaCo',
    )
    BusinessProposal.objects.create(
        title='Active proposal', client_name='Activa Mendoza',
        client_email='activa@gmail.com', client=profile, total_investment=1000,
    )
    return profile


@pytest.fixture
def orphan_client(db):
    """Client with zero proposals and zero projects — eligible for delete."""
    return proposal_client_service.get_or_create_client_for_proposal(
        name='Huerfano Solo', email='huerfano@gmail.com',
    )


@pytest.fixture
def placeholder_client(db):
    """Client created with empty email — placeholder, no proposals."""
    return proposal_client_service.get_or_create_client_for_proposal(
        name='Placeholder Client', email='',
    )


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

class TestListProposalClients:
    def test_returns_all_clients_for_admin(
        self, admin_client, real_client_with_proposal, orphan_client,
    ):
        response = admin_client.get(reverse('list-proposal-clients'))
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_search_filters_by_company_name_icontains(
        self, admin_client, real_client_with_proposal, orphan_client,
    ):
        response = admin_client.get(
            reverse('list-proposal-clients'), {'search': 'activa'},
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == real_client_with_proposal.pk

    def test_orphans_filter_true_excludes_clients_with_proposals(
        self, admin_client, real_client_with_proposal, orphan_client,
    ):
        response = admin_client.get(
            reverse('list-proposal-clients'), {'orphans': 'true'},
        )
        assert response.status_code == 200
        ids = [c['id'] for c in response.data]
        assert orphan_client.pk in ids
        assert real_client_with_proposal.pk not in ids

    def test_orphans_filter_false_excludes_orphan_clients(
        self, admin_client, real_client_with_proposal, orphan_client,
    ):
        response = admin_client.get(
            reverse('list-proposal-clients'), {'orphans': 'false'},
        )
        assert response.status_code == 200
        ids = [c['id'] for c in response.data]
        assert real_client_with_proposal.pk in ids
        assert orphan_client.pk not in ids

    def test_unauthenticated_user_is_rejected(self, api_client):
        response = api_client.get(reverse('list-proposal-clients'))
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Search (autocomplete)
# ---------------------------------------------------------------------------

class TestSearchProposalClients:
    def test_search_matches_email_substring(
        self, admin_client, real_client_with_proposal, orphan_client,
    ):
        response = admin_client.get(
            reverse('search-proposal-clients'), {'q': 'huerfano'},
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == orphan_client.pk

    def test_empty_query_returns_all_clients_capped(
        self, admin_client, real_client_with_proposal, orphan_client,
    ):
        response = admin_client.get(reverse('search-proposal-clients'), {'q': ''})
        assert response.status_code == 200
        assert len(response.data) == 2


# ---------------------------------------------------------------------------
# Retrieve detail
# ---------------------------------------------------------------------------

class TestRetrieveProposalClient:
    def test_detail_includes_nested_proposals(
        self, admin_client, real_client_with_proposal,
    ):
        response = admin_client.get(
            reverse('retrieve-proposal-client', args=[real_client_with_proposal.pk]),
        )
        assert response.status_code == 200
        assert response.data['id'] == real_client_with_proposal.pk
        assert 'proposals' in response.data
        assert len(response.data['proposals']) == 1
        assert response.data['proposals'][0]['title'] == 'Active proposal'

    def test_returns_404_for_unknown_client(self, admin_client):
        response = admin_client.get(reverse('retrieve-proposal-client', args=[999999]))
        assert response.status_code == 404
        assert response.data['error'] == 'client_not_found'


# ---------------------------------------------------------------------------
# Create (standalone)
# ---------------------------------------------------------------------------

class TestCreateProposalClient:
    def test_create_with_email_returns_persisted_profile(self, admin_client):
        response = admin_client.post(
            reverse('create-proposal-client'),
            {'name': 'New Standalone', 'email': 'standalone@gmail.com', 'company': 'StandCo'},
            format='json',
        )
        assert response.status_code == 201
        assert response.data['email'] == 'standalone@gmail.com'
        assert response.data['company'] == 'StandCo'
        assert response.data['is_email_placeholder'] is False
        assert UserProfile.objects.filter(pk=response.data['id']).exists()

    def test_create_without_email_generates_placeholder(self, admin_client):
        response = admin_client.post(
            reverse('create-proposal-client'),
            {'name': 'No Email Person'},
            format='json',
        )
        assert response.status_code == 201
        assert response.data['is_email_placeholder'] is True
        assert response.data['email'].endswith('@temp.example.com')

    def test_create_rejects_completely_empty_payload(self, admin_client):
        response = admin_client.post(
            reverse('create-proposal-client'), {}, format='json',
        )
        assert response.status_code == 400
        assert response.data['error'] == 'name_or_email_required'


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

class TestUpdateProposalClient:
    def test_update_cascades_snapshot_to_linked_proposals(
        self, admin_client, real_client_with_proposal,
    ):
        response = admin_client.patch(
            reverse('update-proposal-client', args=[real_client_with_proposal.pk]),
            {'phone': '+57 311 9999'},
            format='json',
        )
        assert response.status_code == 200
        proposal = real_client_with_proposal.proposals.first()
        proposal.refresh_from_db()
        assert proposal.client_phone == '+57 311 9999'


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

class TestDeleteProposalClient:
    def test_delete_orphan_returns_204(self, admin_client, orphan_client):
        response = admin_client.delete(
            reverse('delete-proposal-client', args=[orphan_client.pk]),
        )
        assert response.status_code == 204
        assert not UserProfile.objects.filter(pk=orphan_client.pk).exists()

    def test_delete_with_proposals_returns_400_with_error_code(
        self, admin_client, real_client_with_proposal,
    ):
        response = admin_client.delete(
            reverse('delete-proposal-client', args=[real_client_with_proposal.pk]),
        )
        assert response.status_code == 400
        assert response.data['error'] == 'client_has_proposals'
        assert response.data['count'] == 1

    def test_delete_with_platform_project_returns_400(
        self, admin_client, orphan_client,
    ):
        Project.objects.create(
            name='Live Project', client=orphan_client.user, status=Project.STATUS_ACTIVE,
        )
        response = admin_client.delete(
            reverse('delete-proposal-client', args=[orphan_client.pk]),
        )
        assert response.status_code == 400
        assert response.data['error'] == 'client_has_projects'


# ---------------------------------------------------------------------------
# Proposal create/update wiring (client_id resolution)
# ---------------------------------------------------------------------------

class TestProposalCreateWithClientId:
    def test_proposal_create_with_client_id_reuses_existing_profile(
        self, admin_client, real_client_with_proposal,
    ):
        response = admin_client.post(
            reverse('create-proposal'),
            {
                'title': 'Second proposal for same client',
                'client_id': real_client_with_proposal.pk,
                'client_name': 'ignored',
                'client_email': 'ignored@gmail.com',
                'total_investment': 5000,
                'currency': 'COP',
            },
            format='json',
        )
        assert response.status_code == 201
        proposal = BusinessProposal.objects.get(pk=response.data['id'])
        assert proposal.client_id == real_client_with_proposal.pk
        # Snapshot was rebuilt from the canonical profile, not the inline data.
        assert proposal.client_email == 'activa@gmail.com'

    def test_proposal_create_without_client_id_auto_creates_profile_from_email(
        self, admin_client,
    ):
        response = admin_client.post(
            reverse('create-proposal'),
            {
                'title': 'Auto-create test',
                'client_name': 'Brand New',
                'client_email': 'brandnew@gmail.com',
                'total_investment': 1000,
                'currency': 'COP',
            },
            format='json',
        )
        assert response.status_code == 201
        proposal = BusinessProposal.objects.get(pk=response.data['id'])
        assert proposal.client is not None
        assert proposal.client.user.email == 'brandnew@gmail.com'

    def test_proposal_create_without_email_generates_placeholder_client(
        self, admin_client,
    ):
        response = admin_client.post(
            reverse('create-proposal'),
            {
                'title': 'No email proposal',
                'client_name': 'Email Pending',
                'client_email': '',
                'total_investment': 1000,
                'currency': 'COP',
            },
            format='json',
        )
        assert response.status_code == 201
        proposal = BusinessProposal.objects.get(pk=response.data['id'])
        assert proposal.client.is_email_placeholder is True


# ---------------------------------------------------------------------------
# Edge cases — proposal/client lifecycle interactions
# ---------------------------------------------------------------------------

class TestProposalUpdatePropagatesClientChanges:
    def test_propagate_client_updates_cascades_to_other_proposals(
        self, admin_client, real_client_with_proposal,
    ):
        # Add a second proposal to the same client so we can verify cascade.
        BusinessProposal.objects.create(
            title='Sibling proposal',
            client=real_client_with_proposal,
            client_name='Activa Mendoza',
            client_email='activa@gmail.com',
            total_investment=2000,
        )
        original = real_client_with_proposal.proposals.first()

        response = admin_client.patch(
            reverse('update-proposal', args=[original.pk]),
            {
                'client_phone': '+57 311 0000',
                'propagate_client_updates': True,
            },
            format='json',
        )
        assert response.status_code == 200

        sibling = BusinessProposal.objects.exclude(pk=original.pk).get(
            client=real_client_with_proposal,
        )
        assert sibling.client_phone == '+57 311 0000'

    def test_inline_client_update_without_propagate_does_not_cascade(
        self, admin_client, real_client_with_proposal,
    ):
        # Capture the original (fixture) proposal id before creating the sibling.
        original_pk = real_client_with_proposal.proposals.values_list('pk', flat=True).first()
        sibling = BusinessProposal.objects.create(
            title='Sibling no-cascade',
            client=real_client_with_proposal,
            client_name='Activa Mendoza',
            client_email='activa@gmail.com',
            client_phone='untouched',
            total_investment=3000,
        )

        admin_client.patch(
            reverse('update-proposal', args=[original_pk]),
            {'client_phone': '+57 999 8888'},
            format='json',
        )

        # Sibling stays at 'untouched' because propagate flag was not set.
        sibling.refresh_from_db()
        assert sibling.client_phone == 'untouched'


class TestOrphanFlagTransitionsAfterProposalDelete:
    def test_client_becomes_orphan_after_last_proposal_is_deleted(
        self, admin_client, real_client_with_proposal,
    ):
        # First confirm: client is NOT orphan while it has a proposal.
        list_response = admin_client.get(
            reverse('list-proposal-clients'), {'orphans': 'false'},
        )
        ids = [c['id'] for c in list_response.data]
        assert real_client_with_proposal.pk in ids

        # Delete the only proposal.
        proposal = real_client_with_proposal.proposals.first()
        proposal.delete()

        # Client should now appear in the orphans filter.
        list_response = admin_client.get(
            reverse('list-proposal-clients'), {'orphans': 'true'},
        )
        ids = [c['id'] for c in list_response.data]
        assert real_client_with_proposal.pk in ids

    def test_orphan_can_be_deleted_after_last_proposal_removal(
        self, admin_client, real_client_with_proposal,
    ):
        proposal = real_client_with_proposal.proposals.first()
        proposal.delete()
        response = admin_client.delete(
            reverse('delete-proposal-client', args=[real_client_with_proposal.pk]),
        )
        assert response.status_code == 204
