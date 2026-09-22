"""Contract and query-budget guards for lightweight platform selectors."""
from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models.signals import post_init
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from accounts.models import Project, ProjectAdminAccess, UserProfile
from accounts.services.credential_cipher import encrypt_secret
from accounts.services.tokens import get_tokens_for_user
from content.models import BusinessProposal, DocumentState, DocumentStateGroup
from content.services.entity_history import without_history


User = get_user_model()
pytestmark = pytest.mark.django_db

MAX_PROPOSAL_SELECTOR_QUERIES = 6
MAX_ELIGIBLE_PROPOSAL_QUERIES = 6
MAX_PROJECT_ACCESS_LIST_QUERIES = 6

PROPOSAL_SELECTOR_URL = '/api/accounts/proposals/'
PROJECT_ACCESS_URL = '/api/accounts/projects/access/'


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='selector-admin@example.com',
        email='selector-admin@example.com',
        password='selector-admin-password',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_ADMIN,
        is_onboarded=True,
        profile_completed=True,
    )
    return user


@pytest.fixture
def admin_headers(admin_user):
    return {'HTTP_AUTHORIZATION': f'Bearer {get_tokens_for_user(admin_user)["access"]}'}


def _client(index):
    email = f'selector-client-{index}@example.com'
    user = User.objects.create_user(
        username=email,
        email=email,
        password='selector-client-password',
        first_name=f'Client{index}',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        is_onboarded=True,
        profile_completed=True,
        company_name=f'Company {index}',
    )
    return user


def _proposal(index, *, email='proposal-client@example.com', status='accepted', total=Decimal('100.00')):
    return BusinessProposal.objects.create(
        title=f'Selector proposal {index}',
        client_name=f'Proposal client {index}',
        client_email=email,
        status=status,
        total_investment=total,
        contract_params={'private_terms': 'x' * 50000},
    )


def _project(index, client, *, name=None, legacy_secret=''):
    return Project.objects.create(
        name=name or f'Selector project {index:02d}',
        client=client,
        status=Project.STATUS_ACTIVE,
        admin_password_encrypted=legacy_secret,
    )


class TestProposalSelectorQueryBudgets:
    def test_selector_preserves_summary_contract(self, api_client, admin_headers):
        """Fails if the proposal selector drops a declared summary value."""
        proposal = _proposal(1, total=Decimal('0.00'))

        response = api_client.get(PROPOSAL_SELECTOR_URL, **admin_headers)

        assert response.status_code == 200
        assert response.json() == [{
            'id': proposal.id,
            'title': 'Selector proposal 1',
            'client_name': 'Proposal client 1',
            'client_email': 'proposal-client@example.com',
            'total_investment': '0.00',
            'currency': 'COP',
            'hosting_percent': 60,
            'hosting_discount_nine_month': 40,
            'hosting_discount_semiannual': 20,
            'hosting_discount_quarterly': 10,
            'status': 'accepted',
        }]

    def test_selector_orders_by_created_at(self, api_client, admin_headers):
        """Fails if selector annotations lose newest-proposal-first ordering."""
        older = _proposal(1)
        newer = _proposal(2)
        BusinessProposal.objects.filter(pk=older.pk).update(
            created_at=datetime(2026, 1, 1, tzinfo=datetime_timezone.utc),
        )
        BusinessProposal.objects.filter(pk=newer.pk).update(
            created_at=datetime(2026, 1, 2, tzinfo=datetime_timezone.utc),
        )

        response = api_client.get(PROPOSAL_SELECTOR_URL, **admin_headers)

        assert response.status_code == 200
        assert [item['id'] for item in response.json()] == [newer.id, older.id]

    def test_selector_query_budget_is_constant(self, api_client, admin_headers):
        """Fails if selector serialization rehydrates contract JSON per proposal."""
        _proposal(1)

        with CaptureQueriesContext(connection) as one_queries:
            one_response = api_client.get(PROPOSAL_SELECTOR_URL, **admin_headers)

        for index in range(2, 51):
            _proposal(index)
        with CaptureQueriesContext(connection) as fifty_queries:
            fifty_response = api_client.get(PROPOSAL_SELECTOR_URL, **admin_headers)

        assert [len(one_response.json()), len(fifty_response.json())] == [1, 50]
        assert len(one_queries) == len(fifty_queries) <= MAX_PROPOSAL_SELECTOR_QUERIES

    def test_selector_defers_contract_params(self, api_client, admin_headers):
        """Fails if selector hydration starts loading private contract parameters."""
        _proposal(1)
        _proposal(2)
        deferred_columns = []

        def remember_proposal(sender, instance, **kwargs):
            deferred_columns.append(instance.get_deferred_fields())

        post_init.connect(remember_proposal, sender=BusinessProposal, weak=False)
        try:
            response = api_client.get(PROPOSAL_SELECTOR_URL, **admin_headers)
        finally:
            post_init.disconnect(remember_proposal, sender=BusinessProposal)

        assert response.status_code == 200
        assert len(deferred_columns) == 2
        assert all('contract_params' in columns for columns in deferred_columns)

    def test_selector_rejects_unauthenticated(self, api_client):
        """Fails if the proposal selector permits requests without a JWT."""
        response = api_client.get(PROPOSAL_SELECTOR_URL)

        assert response.status_code == 401


class TestEligibleProposalQueryBudgets:
    def test_eligible_proposals_preserves_zero_total(self, api_client, admin_headers):
        """Fails if an empty proposal investment no longer serializes as zero."""
        client = _client(1)
        proposal = _proposal(1, email=client.email.upper(), total=Decimal('0.00'))

        response = api_client.get(
            f'/api/accounts/clients/{client.id}/eligible-proposals/', **admin_headers,
        )

        assert response.status_code == 200
        assert response.json() == [{
            'id': proposal.id,
            'title': 'Selector proposal 1',
            'status': 'accepted',
            'total_amount': 0,
        }]

    def test_eligible_proposals_orders_by_descending_id(self, api_client, admin_headers):
        """Fails if eligible proposal rows stop sorting by newest identifier."""
        client = _client(1)
        older = _proposal(1, email=client.email)
        newer = _proposal(2, email=client.email)

        response = api_client.get(
            f'/api/accounts/clients/{client.id}/eligible-proposals/', **admin_headers,
        )

        assert response.status_code == 200
        assert [item['id'] for item in response.json()] == [newer.id, older.id]

    def test_eligible_proposals_query_budget_is_constant(self, api_client, admin_headers):
        """Fails if eligible rows load contract JSON once for each proposal."""
        client = _client(1)
        _proposal(1, email=client.email.upper())
        url = f'/api/accounts/clients/{client.id}/eligible-proposals/'

        with CaptureQueriesContext(connection) as one_queries:
            one_response = api_client.get(url, **admin_headers)

        for index in range(2, 51):
            _proposal(index, email=client.email.upper(), status='finished')
        with CaptureQueriesContext(connection) as fifty_queries:
            fifty_response = api_client.get(url, **admin_headers)

        assert [len(one_response.json()), len(fifty_response.json())] == [1, 50]
        assert len(one_queries) == len(fifty_queries) <= MAX_ELIGIBLE_PROPOSAL_QUERIES

    def test_eligible_proposals_defers_target_client_password(self, api_client, admin_headers):
        """Fails if eligible proposal lookup hydrates the target password hash."""
        client = _client(1)
        _proposal(1, email=client.email)
        deferred_columns = []

        def remember_target_client(sender, instance, **kwargs):
            if instance.pk == client.id:
                deferred_columns.append(instance.get_deferred_fields())

        post_init.connect(remember_target_client, sender=User, weak=False)
        try:
            response = api_client.get(
                f'/api/accounts/clients/{client.id}/eligible-proposals/', **admin_headers,
            )
        finally:
            post_init.disconnect(remember_target_client, sender=User)

        assert response.status_code == 200
        assert len(deferred_columns) == 1
        assert 'password' in deferred_columns[0]

    def test_eligible_proposals_defers_contract_params(self, api_client, admin_headers):
        """Fails if eligible proposal hydration starts loading contract parameters."""
        client = _client(1)
        _proposal(1, email=client.email)
        _proposal(2, email=client.email, status='finished')
        deferred_columns = []

        def remember_proposal(sender, instance, **kwargs):
            deferred_columns.append(instance.get_deferred_fields())

        post_init.connect(remember_proposal, sender=BusinessProposal, weak=False)
        try:
            response = api_client.get(
                f'/api/accounts/clients/{client.id}/eligible-proposals/', **admin_headers,
            )
        finally:
            post_init.disconnect(remember_proposal, sender=BusinessProposal)

        assert response.status_code == 200
        assert len(deferred_columns) == 2
        assert all('contract_params' in columns for columns in deferred_columns)

    def test_eligible_proposals_rejects_unauthenticated(self, api_client):
        """Fails if the eligible proposal selector permits anonymous requests."""
        response = api_client.get('/api/accounts/clients/1/eligible-proposals/')

        assert response.status_code == 401


class TestProjectAccessQueryBudgets:
    def test_access_list_treats_whitespace_legacy_secret_as_present(self, api_client, admin_headers):
        """Fails if whitespace-only legacy ciphertext is treated as no password."""
        with without_history():
            project = _project(1, _client(1), legacy_secret=' ')

        response = api_client.get(PROJECT_ACCESS_URL, **admin_headers)

        assert response.status_code == 200
        assert response.json()[0]['has_password'] is True
        assert response.json()[0]['id'] == project.id

    def test_access_list_treats_whitespace_environment_secret_as_present(self, api_client, admin_headers):
        """Fails if whitespace-only environment ciphertext is treated as no password."""
        project = _project(1, _client(1))
        with without_history():
            ProjectAdminAccess.objects.create(
                project=project,
                environment=ProjectAdminAccess.Environment.PRODUCTION,
                admin_password_encrypted=' ',
            )

        response = api_client.get(PROJECT_ACCESS_URL, **admin_headers)

        assert response.status_code == 200
        assert response.json()[0]['has_password'] is True
        assert response.json()[0]['id'] == project.id

    def test_access_list_reports_no_secret_as_false(self, api_client, admin_headers):
        """Fails if empty ciphertext reports an administrative password."""
        project = _project(1, _client(1))

        response = api_client.get(PROJECT_ACCESS_URL, **admin_headers)

        assert response.status_code == 200
        assert response.json()[0]['has_password'] is False
        assert response.json()[0]['id'] == project.id

    def test_access_list_excludes_decommissioned_state(self, api_client, admin_headers):
        """Fails if decommissioned projects return in the access summary."""
        group = DocumentStateGroup.objects.create(
            catalog=DocumentStateGroup.Catalog.PROJECTS,
            name='Selector states',
        )
        state = DocumentState.objects.create(
            group=group,
            name='Selector decommissioned',
            operational_effect=DocumentState.OperationalEffect.DECOMMISSIONED,
        )
        project = _project(1, _client(1), name='Decommissioned selector')
        Project.objects.filter(pk=project.pk).update(current_state=state)

        response = api_client.get(PROJECT_ACCESS_URL, **admin_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_access_list_orders_by_name(self, api_client, admin_headers):
        """Fails if access rows stop sorting alphabetically by project name."""
        _project(1, _client(1), name='Zulu selector')
        _project(2, _client(2), name='Alpha selector')

        response = api_client.get(PROJECT_ACCESS_URL, **admin_headers)

        assert response.status_code == 200
        assert [item['name'] for item in response.json()] == ['Alpha selector', 'Zulu selector']

    def test_access_list_query_budget_is_constant(self, api_client, admin_headers):
        """Fails if access summary starts hydrating related credentials per project."""
        _project(1, _client(1))

        with CaptureQueriesContext(connection) as one_queries:
            one_response = api_client.get(PROJECT_ACCESS_URL, **admin_headers)

        for index in range(2, 51):
            project = _project(index, _client(index))
            ProjectAdminAccess.objects.create(
                project=project,
                environment=ProjectAdminAccess.Environment.STAGING,
                admin_password_encrypted=encrypt_secret('access-password'),
            )
        with CaptureQueriesContext(connection) as fifty_queries:
            fifty_response = api_client.get(PROJECT_ACCESS_URL, **admin_headers)

        assert [len(one_response.json()), len(fifty_response.json())] == [1, 50]
        assert len(one_queries) == len(fifty_queries) <= MAX_PROJECT_ACCESS_LIST_QUERIES

    def test_access_list_defers_legacy_ciphertext(self, api_client, admin_headers):
        """Fails if access summary hydrates legacy ciphertext for each project."""
        _project(1, _client(1), legacy_secret=encrypt_secret('legacy-password'))
        _project(2, _client(2))
        deferred_columns = []

        def remember_project(sender, instance, **kwargs):
            deferred_columns.append(instance.get_deferred_fields())

        post_init.connect(remember_project, sender=Project, weak=False)
        try:
            response = api_client.get(PROJECT_ACCESS_URL, **admin_headers)
        finally:
            post_init.disconnect(remember_project, sender=Project)

        assert response.status_code == 200
        assert len(deferred_columns) == 2
        assert all('admin_password_encrypted' in columns for columns in deferred_columns)

    def test_access_list_does_not_hydrate_environment_accesses(self, api_client, admin_headers):
        """Fails if access summary prefetches environment credential rows."""
        project = _project(1, _client(1))
        ProjectAdminAccess.objects.create(
            project=project,
            environment=ProjectAdminAccess.Environment.PRODUCTION,
            admin_password_encrypted=encrypt_secret('access-password'),
        )
        initialized_access_ids = []

        def remember_access(sender, instance, **kwargs):
            initialized_access_ids.append(instance.pk)

        post_init.connect(remember_access, sender=ProjectAdminAccess, weak=False)
        try:
            response = api_client.get(PROJECT_ACCESS_URL, **admin_headers)
        finally:
            post_init.disconnect(remember_access, sender=ProjectAdminAccess)

        assert response.status_code == 200
        assert initialized_access_ids == []
