"""Tests for the panel add/delete proposal-section endpoints.

POST   /api/proposals/<proposal_id>/sections/create/
DELETE /api/proposals/sections/<section_id>/delete/
"""
import pytest
from django.urls import reverse

from content.models import (
    BusinessProposal,
    ProposalRequirementGroup,
    ProposalSection,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def prop(db):
    return BusinessProposal.objects.create(
        title='Section CRUD Test',
        client_name='Cliente Prueba',
        client_email='cliente@test.com',
        total_investment=3_200_000,
        currency='COP',
        language='es',
    )


def _create_url(proposal):
    return reverse('create-proposal-section', kwargs={'proposal_id': proposal.id})


def _delete_url(section):
    return reverse('delete-proposal-section', kwargs={'section_id': section.id})


class TestCreateProposalSection:
    def test_creates_section_seeded_from_defaults(self, admin_client, prop):
        response = admin_client.post(
            _create_url(prop), {'section_type': 'executive_summary'}, format='json',
        )
        assert response.status_code == 201
        assert response.data['section']['section_type'] == 'executive_summary'
        assert response.data['section']['content_json']  # seeded, not empty
        assert set(response.data['proposal_totals']) == {
            'total_investment', 'effective_total_investment',
        }
        assert prop.sections.filter(section_type='executive_summary').exists()

    def test_greeting_is_personalized(self, admin_client, prop):
        response = admin_client.post(
            _create_url(prop), {'section_type': 'greeting'}, format='json',
        )
        assert response.status_code == 201
        cj = response.data['section']['content_json']
        assert cj['proposalTitle'] == prop.title
        assert cj['clientName'] == prop.client_name

    def test_investment_is_personalized(self, admin_client, prop):
        response = admin_client.post(
            _create_url(prop), {'section_type': 'investment'}, format='json',
        )
        assert response.status_code == 201
        cj = response.data['section']['content_json']
        assert cj['currency'] == 'COP'
        assert '3,200,000' in cj['totalInvestment']
        assert len(cj['paymentOptions']) == 3

    def test_custom_title_overrides_default(self, admin_client, prop):
        response = admin_client.post(
            _create_url(prop),
            {'section_type': 'timeline', 'title': 'Cronograma custom'},
            format='json',
        )
        assert response.status_code == 201
        assert response.data['section']['title'] == 'Cronograma custom'

    def test_order_appends_at_the_end(self, admin_client, prop):
        for i, st in enumerate(['greeting', 'timeline'], start=1):
            ProposalSection.objects.create(
                proposal=prop, section_type=st, title=st, content_json={}, order=i,
            )
        response = admin_client.post(
            _create_url(prop), {'section_type': 'investment'}, format='json',
        )
        assert response.status_code == 201
        assert response.data['section']['order'] == 3

    def test_duplicate_type_rejected(self, admin_client, prop):
        ProposalSection.objects.create(
            proposal=prop, section_type='greeting', title='Saludo',
            content_json={}, order=1,
        )
        response = admin_client.post(
            _create_url(prop), {'section_type': 'greeting'}, format='json',
        )
        assert response.status_code == 400
        assert response.data['code'] == 'section_already_exists'

    def test_invalid_type_rejected(self, admin_client, prop):
        response = admin_client.post(
            _create_url(prop), {'section_type': 'not_a_real_type'}, format='json',
        )
        assert response.status_code == 400
        assert response.data['code'] == 'invalid_section_type'

    def test_missing_type_rejected(self, admin_client, prop):
        response = admin_client.post(_create_url(prop), {}, format='json')
        assert response.status_code == 400
        assert response.data['code'] == 'missing_section_type'

    def test_requires_admin(self, api_client, prop):
        response = api_client.post(
            _create_url(prop), {'section_type': 'greeting'}, format='json',
        )
        assert response.status_code in (401, 403)

    def test_writes_audit_log(self, admin_client, prop):
        admin_client.post(_create_url(prop), {'section_type': 'greeting'}, format='json')
        assert prop.change_logs.filter(description__icontains='agregada').exists()


class TestDeleteProposalSection:
    def test_deletes_section(self, admin_client, prop):
        section = ProposalSection.objects.create(
            proposal=prop, section_type='timeline', title='Cronograma',
            content_json={}, order=1,
        )
        response = admin_client.delete(_delete_url(section))
        assert response.status_code == 200
        assert response.data['deleted'] is True
        assert response.data['section_type'] == 'timeline'
        assert set(response.data['proposal_totals']) == {
            'total_investment', 'effective_total_investment',
        }
        assert not prop.sections.filter(id=section.id).exists()
        assert prop.change_logs.filter(description__icontains='eliminada').exists()

    def test_fr_delete_blocked_when_modules_confirmed(self, admin_client, prop):
        prop.selected_modules = ['module-pwa_module']
        prop.save(update_fields=['selected_modules'])
        section = ProposalSection.objects.create(
            proposal=prop, section_type='functional_requirements',
            title='Requerimientos', content_json={'groups': []}, order=1,
        )
        response = admin_client.delete(_delete_url(section))
        assert response.status_code == 400
        assert response.data['code'] == 'fr_has_confirmed_selection'
        assert prop.sections.filter(id=section.id).exists()

    def test_fr_delete_allowed_without_confirmation(self, admin_client, prop):
        section = ProposalSection.objects.create(
            proposal=prop, section_type='functional_requirements',
            title='Requerimientos', content_json={'groups': []}, order=1,
        )
        response = admin_client.delete(_delete_url(section))
        assert response.status_code == 200
        assert not prop.sections.filter(section_type='functional_requirements').exists()

    def test_requirement_groups_survive_fr_delete(self, admin_client, prop):
        group = ProposalRequirementGroup.objects.create(
            proposal=prop, group_id='g1', title='Grupo', order=1,
        )
        section = ProposalSection.objects.create(
            proposal=prop, section_type='functional_requirements',
            title='Requerimientos', content_json={'groups': []}, order=1,
        )
        response = admin_client.delete(_delete_url(section))
        assert response.status_code == 200
        assert ProposalRequirementGroup.objects.filter(id=group.id).exists()

    def test_requires_admin(self, api_client, prop):
        section = ProposalSection.objects.create(
            proposal=prop, section_type='timeline', title='Cronograma',
            content_json={}, order=1,
        )
        response = api_client.delete(_delete_url(section))
        assert response.status_code in (401, 403)
