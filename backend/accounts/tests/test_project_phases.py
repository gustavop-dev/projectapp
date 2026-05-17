"""Tests for the ProjectPhase model, service, and REST endpoints."""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from accounts.models import Project, ProjectPhase, UserProfile

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def client_user(db):
    return User.objects.create_user(
        username='client@example.com', email='client@example.com', password='x',
    )


@pytest.fixture
def project(client_user):
    return Project.objects.create(name='Test project', client=client_user)


@pytest.fixture
def business_proposal(db):
    from content.models import BusinessProposal
    return BusinessProposal.objects.create(title='Proposal A', client_name='Test Client')


# =========================================================================
# Model tests
# =========================================================================


def test_phase_links_project_and_proposal_with_order(project, business_proposal):
    p = ProjectPhase.objects.create(
        project=project, business_proposal=business_proposal, order=1,
    )
    assert p.project == project
    assert p.business_proposal == business_proposal
    assert p.order == 1


def test_unique_constraint_blocks_same_proposal_twice_on_one_project(project, business_proposal):
    ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=1)
    with pytest.raises(IntegrityError):
        ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=2)


def test_ordering_by_order_field(project, business_proposal):
    from content.models import BusinessProposal
    p2 = BusinessProposal.objects.create(title='P2', client_name='X')
    ProjectPhase.objects.create(project=project, business_proposal=p2, order=2)
    ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=1)
    titles = [ph.business_proposal.title for ph in project.phases.all()]
    assert titles == ['Proposal A', 'P2']


def test_linked_business_proposal_returns_first_phase_proposal(project, business_proposal):
    ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=1)
    assert project.linked_business_proposal() == business_proposal


def test_linked_business_proposal_returns_none_when_no_phases(project):
    assert project.linked_business_proposal() is None
