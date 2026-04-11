"""Tests for uncovered branches in project_list_view POST with proposal_id.

Covers:
- project_list_view POST: creates project linked to a BusinessProposal (proposal branch)
- _extract_proposal_financial_data: called with proposal that has an investment section
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import (
    Project,
    UserProfile,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@projcreate.com', email='admin@projcreate.com', password='adminpass1',
        first_name='Admin', last_name='User',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@projcreate.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@projcreate.com', email='client@projcreate.com', password='clientpass1',
        first_name='Carlos', last_name='Ruiz',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, created_by=admin_user,
    )
    return user


@pytest.fixture
def unlinked_proposal():
    """BusinessProposal not yet linked to any deliverable."""
    from content.models import BusinessProposal
    return BusinessProposal.objects.create(
        title='Ready Proposal',
        client_name='Test Client',
        total_investment=Decimal('10000000'),
        status='accepted',
        hosting_percent=30,
    )


@pytest.fixture
def proposal_with_investment_section(unlinked_proposal):
    """BusinessProposal with an investment section containing billing tiers."""
    from content.models import ProposalSection
    ProposalSection.objects.create(
        proposal=unlinked_proposal,
        section_type='investment',
        title='Inversión',
        order=5,
        is_enabled=True,
        content_json={
            'hostingPlan': {
                'hostingPercent': 30,
                'billingTiers': [
                    {'frequency': 'monthly', 'months': 1, 'label': 'Mensual', 'badge': '', 'discountPercent': 0},
                    {'frequency': 'quarterly', 'months': 3, 'label': 'Trimestral', 'badge': '10%', 'discountPercent': 10},
                ],
            },
            'paymentOptions': [
                {'label': 'Inicio', 'description': '50% al inicio'},
                {'label': 'Entrega', 'description': '50% al finalizar'},
            ],
        },
    )
    return unlinked_proposal


# ===========================================================================
# project_list_view POST — with proposal_id (lines 644-695)
# ===========================================================================

class TestProjectCreateWithProposal:
    def test_admin_creates_project_linked_to_proposal(
        self, api_client, admin_headers, client_user, unlinked_proposal,
    ):
        """Admin can create a project with a proposal_id — links the proposal to a new deliverable."""
        resp = api_client.post('/api/accounts/projects/', {
            'name': 'Proposal Project',
            'client_id': client_user.id,
            'proposal_id': unlinked_proposal.id,
        }, format='json', **admin_headers)

        assert resp.status_code == 201
        # Proposal should now be linked to a deliverable
        unlinked_proposal.refresh_from_db()
        assert unlinked_proposal.deliverable_id is not None

    def test_project_created_with_proposal_has_hosting_tiers(
        self, api_client, admin_headers, client_user, proposal_with_investment_section,
    ):
        """When proposal has billing tiers, project stores them from _extract_proposal_financial_data."""
        resp = api_client.post('/api/accounts/projects/', {
            'name': 'Tiered Hosting Project',
            'client_id': client_user.id,
            'proposal_id': proposal_with_investment_section.id,
        }, format='json', **admin_headers)

        assert resp.status_code == 201
        project = Project.objects.get(id=resp.json()['id'])
        assert project.hosting_tiers  # billing_tiers branch in _extract_proposal_financial_data

    def test_project_created_with_proposal_has_payment_milestones(
        self, api_client, admin_headers, client_user, proposal_with_investment_section,
    ):
        """When proposal has paymentOptions, project stores them as payment_milestones."""
        resp = api_client.post('/api/accounts/projects/', {
            'name': 'Milestone Project',
            'client_id': client_user.id,
            'proposal_id': proposal_with_investment_section.id,
        }, format='json', **admin_headers)

        assert resp.status_code == 201
        project = Project.objects.get(id=resp.json()['id'])
        assert project.payment_milestones  # paymentOptions branch in _extract_proposal_financial_data

    def test_project_created_without_proposal_id_has_no_linked_deliverable(
        self, api_client, admin_headers, client_user,
    ):
        """When no proposal_id is passed, no deliverable is linked and hosting_tiers is empty."""
        resp = api_client.post('/api/accounts/projects/', {
            'name': 'Plain Project',
            'client_id': client_user.id,
        }, format='json', **admin_headers)

        assert resp.status_code == 201
        project = Project.objects.get(id=resp.json()['id'])
        assert not project.hosting_tiers
