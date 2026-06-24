"""Tests for the proposal delete endpoint.

Covers the ProtectedError handling: proposals linked to a launched project
(via ProjectPhase, on_delete=PROTECT) must return a clear 409 instead of a
500, while unlinked proposals delete normally.
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from content.models import BusinessProposal

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_delete_proposal_without_links_returns_204(admin_client, proposal):
    url = reverse('delete-proposal', args=[proposal.id])
    response = admin_client.delete(url)
    assert response.status_code == 204
    assert not BusinessProposal.objects.filter(id=proposal.id).exists()


def test_delete_proposal_with_project_phase_returns_409(admin_client, proposal):
    from accounts.models import Project, ProjectPhase

    client_user = User.objects.create_user(
        username='client@example.com', email='client@example.com', password='x',
    )
    project = Project.objects.create(name='Launched project', client=client_user)
    ProjectPhase.objects.create(
        project=project, business_proposal=proposal, order=1,
    )

    url = reverse('delete-proposal', args=[proposal.id])
    response = admin_client.delete(url)

    assert response.status_code == 409
    assert 'error' in response.data
    assert 'Launched project' in response.data['error']
    # Proposal must survive the blocked delete.
    assert BusinessProposal.objects.filter(id=proposal.id).exists()


def test_delete_proposal_not_found_returns_404(admin_client):
    url = reverse('delete-proposal', args=[999999])
    response = admin_client.delete(url)
    assert response.status_code == 404
