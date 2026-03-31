"""Tests for proposal acceptance → platform onboarding (sync + idempotency)."""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Deliverable, Project, UserProfile
from accounts.services.proposal_platform_onboarding import (
    handle_proposal_accepted_for_platform,
)
from accounts.services.technical_requirements_sync import (
    sync_technical_requirements_for_deliverable,
)
from content.models import BusinessProposal, ProposalSection

User = get_user_model()


@pytest.fixture
def admin_user(db):
    u = User.objects.create_user(
        username='admin-onb@test.com',
        email='admin-onb@test.com',
        password='pass',
        is_staff=True,
    )
    UserProfile.objects.create(user=u, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return u


@pytest.fixture
def client_user(db):
    u = User.objects.create_user(
        username='client-onb@test.com',
        email='client-onb@test.com',
        password='pass',
    )
    UserProfile.objects.create(user=u, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    return u


@pytest.fixture
def proposal_with_deliverable(db, client_user, admin_user):
    proj = Project.objects.create(name='P1', client=client_user)
    d = Deliverable.objects.create(
        project=proj,
        category=Deliverable.CATEGORY_DOCUMENTS,
        title='Entrega',
        uploaded_by=admin_user,
    )
    bp = BusinessProposal.objects.create(
        title='Prop',
        client_name='Test Client',
        client_email='client-onb@test.com',
        status=BusinessProposal.Status.ACCEPTED,
        deliverable=d,
    )
    ProposalSection.objects.create(
        proposal=bp,
        section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
        title='Técnico',
        is_enabled=True,
        order=1,
        content_json={
            'epics': [
                {
                    'epicKey': 'e1',
                    'title': 'Epic One',
                    'requirements': [
                        {
                            'flowKey': 'f1',
                            'title': 'Req 1',
                            'description': '',
                            'configuration': '',
                            'usageFlow': 'flow',
                        },
                    ],
                },
            ],
        },
    )
    return bp


@pytest.mark.django_db
def test_handle_proposal_accepted_skips_when_already_completed(proposal_with_deliverable, admin_user):
    proposal_with_deliverable.platform_onboarding_completed_at = timezone.now()
    proposal_with_deliverable.save(update_fields=['platform_onboarding_completed_at'])

    out = handle_proposal_accepted_for_platform(
        proposal_with_deliverable, source='admin_panel', acting_user=admin_user,
    )
    assert out['skipped'] is True


@pytest.mark.django_db
def test_sync_technical_requirements_for_deliverable_creates_requirement(
    proposal_with_deliverable, admin_user,
):
    d = proposal_with_deliverable.deliverable
    result = sync_technical_requirements_for_deliverable(d, admin_user)
    assert result['ok'] is True
    assert result['requirements_created'] >= 1


@pytest.mark.django_db
@patch(
    'content.services.proposal_email_service.ProposalEmailService.send_acceptance_confirmation',
    return_value=True,
)
def test_handle_first_run_sets_platform_onboarding_timestamp(
    _mock_send, proposal_with_deliverable, admin_user,
):
    proposal_with_deliverable.platform_onboarding_completed_at = None
    proposal_with_deliverable.save(update_fields=['platform_onboarding_completed_at'])

    handle_proposal_accepted_for_platform(
        proposal_with_deliverable, source='admin_panel', acting_user=admin_user,
    )
    proposal_with_deliverable.refresh_from_db()
    assert proposal_with_deliverable.platform_onboarding_completed_at is not None
