"""Query-count and ordering guards for the proposal detail endpoints.

The detail serializer walks sections, requirement groups→items, change
logs and documents; the views prefetch those relations and the serializer
must consume them with plain .all() so the prefetch cache is actually
used. These tests pin that contract.
"""
import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.urls import reverse

from content.models import (
    BusinessProposal,
    ProposalRequirementGroup,
    ProposalRequirementItem,
    ProposalSection,
)

pytestmark = pytest.mark.django_db

# Measured with the prefetch in place (see commit); the pre-prefetch code
# issued one query per relation plus one per requirement group, so a
# regression pushes well past this ceiling.
MAX_ADMIN_DETAIL_QUERIES = 20


@pytest.fixture
def rich_proposal(db):
    prop = BusinessProposal.objects.create(
        title='Query Guard',
        client_name='Cliente',
        client_email='q@test.com',
        total_investment=1_000_000,
        currency='COP',
        language='es',
    )
    for i, st in enumerate(
        ['greeting', 'executive_summary', 'timeline', 'investment', 'final_note'],
        start=1,
    ):
        ProposalSection.objects.create(
            proposal=prop, section_type=st, title=st,
            content_json={'title': st}, order=i,
            is_enabled=(st != 'final_note'),
        )
    for g in range(3):
        group = ProposalRequirementGroup.objects.create(
            proposal=prop, group_id=f'g{g}', title=f'Grupo {g}', order=g,
        )
        for j in range(4):
            ProposalRequirementItem.objects.create(
                group=group, item_id=f'g{g}-i{j}', name=f'Item {j}', order=j,
            )
    return prop


class TestPublicProposalDetail:
    def test_public_view_filters_disabled_and_keeps_order(self, api_client, rich_proposal):
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': rich_proposal.uuid})
        response = api_client.get(url)
        assert response.status_code == 200
        types = [s['section_type'] for s in response.data['sections']]
        assert types == ['greeting', 'executive_summary', 'timeline', 'investment']


class TestAdminProposalDetailQueries:
    def test_admin_detail_query_count_is_bounded(self, admin_client, rich_proposal):
        url = reverse('retrieve-proposal', kwargs={'proposal_id': rich_proposal.id})
        with CaptureQueriesContext(connection) as ctx:
            response = admin_client.get(url)
        assert response.status_code == 200
        assert len(response.data['sections']) == 5  # admin sees disabled too
        assert len(response.data['requirement_groups']) == 3
        assert all(len(g['items']) == 4 for g in response.data['requirement_groups'])
        assert len(ctx) <= MAX_ADMIN_DETAIL_QUERIES, (
            f'{len(ctx)} queries (max {MAX_ADMIN_DETAIL_QUERIES}) — did a '
            f'serializer method stop using the prefetch cache?'
        )
