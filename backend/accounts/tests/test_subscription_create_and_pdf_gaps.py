"""Tests for uncovered branches in project_subscription_view (POST) and
_build_proposal_pdf_http_response (success paths).

Covers:
- project_subscription_view POST: create subscription from proposal (success)
- project_subscription_view POST: subscription already exists (400)
- project_subscription_view POST: no linked proposal (400)
- project_subscription_view POST: invalid plan (400)
- deliverable_commercial_proposal_pdf_view: success (returns PDF bytes)
- deliverable_technical_document_pdf_view: success (returns PDF bytes)
"""
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import (
    Deliverable,
    HostingSubscription,
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
        username='admin@subcreate.com', email='admin@subcreate.com', password='adminpass1',
        first_name='Admin', last_name='User',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@subcreate.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@subcreate.com', email='client@subcreate.com', password='clientpass1',
        first_name='Carlos', last_name='Ruiz',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, created_by=admin_user,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@subcreate.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='SubCreate Project', client=client_user,
        status=Project.STATUS_ACTIVE,
    )


@pytest.fixture
def deliverable(project, admin_user):
    return Deliverable.objects.create(
        project=project,
        title='Main Deliverable',
        category=Deliverable.CATEGORY_DOCUMENTS,
        uploaded_by=admin_user,
    )


@pytest.fixture
def deliverable_with_bp(project, admin_user):
    """Deliverable linked to an accepted BusinessProposal with hosting data."""
    from content.models import BusinessProposal
    d = Deliverable.objects.create(
        project=project,
        title='Proposal Deliverable',
        category=Deliverable.CATEGORY_DOCUMENTS,
        uploaded_by=admin_user,
    )
    bp = BusinessProposal.objects.create(
        title='Test Proposal',
        client_name='Test Client',
        total_investment=Decimal('12000000'),
        status='accepted',
        hosting_percent=30,
        hosting_discount_quarterly=10,
        hosting_discount_semiannual=20,
        deliverable=d,
    )
    d._test_bp = bp
    return d


@pytest.fixture
def subscription(project):
    sub = HostingSubscription(
        project=project, plan=HostingSubscription.PLAN_MONTHLY,
        base_monthly_amount=Decimal('300000'), discount_percent=0,
        start_date='2026-01-01', next_billing_date='2026-02-01',
        status=HostingSubscription.STATUS_ACTIVE,
    )
    sub.calculate_amounts()
    sub.save()
    return sub


# ===========================================================================
# project_subscription_view POST — create subscription
# ===========================================================================

class TestProjectSubscriptionCreate:
    def test_creates_subscription_from_linked_proposal(
        self, api_client, client_headers, project, deliverable_with_bp,
    ):
        """Client can create a monthly subscription from a linked proposal."""
        url = f'/api/accounts/projects/{project.id}/subscription/'
        resp = api_client.post(
            url, {'plan': HostingSubscription.PLAN_MONTHLY},
            format='json', **client_headers,
        )

        assert resp.status_code == 201
        assert HostingSubscription.objects.filter(project=project).exists()

    def test_returns_400_when_subscription_already_exists(
        self, api_client, client_headers, project, subscription,
    ):
        """POST returns 400 when a subscription already exists for the project."""
        url = f'/api/accounts/projects/{project.id}/subscription/'
        resp = api_client.post(
            url, {'plan': HostingSubscription.PLAN_MONTHLY},
            format='json', **client_headers,
        )

        assert resp.status_code == 400

    def test_returns_400_when_no_linked_proposal(
        self, api_client, client_headers, project,
    ):
        """POST returns 400 when the project has no linked BusinessProposal."""
        url = f'/api/accounts/projects/{project.id}/subscription/'
        resp = api_client.post(
            url, {'plan': HostingSubscription.PLAN_MONTHLY},
            format='json', **client_headers,
        )

        assert resp.status_code == 400

    def test_returns_400_when_plan_is_invalid(
        self, api_client, client_headers, project, deliverable_with_bp,
    ):
        """POST returns 400 when an invalid plan is supplied."""
        url = f'/api/accounts/projects/{project.id}/subscription/'
        resp = api_client.post(
            url, {'plan': 'biannual'},
            format='json', **client_headers,
        )

        assert resp.status_code == 400

    def test_admin_can_create_quarterly_subscription(
        self, api_client, admin_headers, project, deliverable_with_bp,
    ):
        """Admin can create a quarterly subscription."""
        url = f'/api/accounts/projects/{project.id}/subscription/'
        resp = api_client.post(
            url, {'plan': HostingSubscription.PLAN_QUARTERLY},
            format='json', **admin_headers,
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data['plan'] == HostingSubscription.PLAN_QUARTERLY


# ===========================================================================
# deliverable_commercial_proposal_pdf_view — success (returns PDF bytes)
# ===========================================================================

class TestDeliverableCommercialProposalPdfSuccess:
    @patch('content.services.proposal_pdf_service.ProposalPdfService.generate', return_value=b'%PDF-commercial')
    def test_returns_pdf_for_accepted_proposal(
        self, mock_pdf, api_client, admin_headers, project, deliverable_with_bp,
    ):
        """Returns a PDF response when proposal has an accepted status and PDF generates."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{deliverable_with_bp.id}/download/commercial-proposal-pdf/'
        )
        resp = api_client.get(url, **admin_headers)

        assert resp.status_code == 200
        assert resp['Content-Type'] == 'application/pdf'


# ===========================================================================
# deliverable_technical_document_pdf_view — success (returns PDF bytes)
# ===========================================================================

class TestDeliverableTechnicalDocumentPdfSuccess:
    @patch('content.services.technical_document_pdf.generate_technical_document_pdf', return_value=b'%PDF-technical')
    def test_returns_technical_pdf_for_accepted_proposal(
        self, mock_pdf, api_client, admin_headers, project, deliverable_with_bp,
    ):
        """Returns a PDF response when proposal has an accepted status and tech PDF generates."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{deliverable_with_bp.id}/download/technical-document-pdf/'
        )
        resp = api_client.get(url, **admin_headers)

        assert resp.status_code == 200
        assert resp['Content-Type'] == 'application/pdf'
