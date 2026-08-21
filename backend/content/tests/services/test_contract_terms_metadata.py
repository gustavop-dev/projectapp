from decimal import Decimal

import pytest

from content.models import BusinessProposal
from content.services.proposal_service import (
    apply_proposal_json_update,
    build_proposal_from_json,
)

pytestmark = pytest.mark.django_db


def test_json_creation_stores_contract_visibility_outside_sections():
    proposal, _ = build_proposal_from_json({
        'title': 'Contrato oculto',
        'client_name': 'Cliente',
        'language': 'es',
        'show_contract_terms': False,
        'sections': {'general': {'clientName': 'Cliente'}},
    })

    assert proposal.show_contract_terms is False
    assert all(
        'show_contract_terms' not in section.content_json
        for section in proposal.sections.all()
    )


def test_json_update_persists_contract_visibility_metadata():
    proposal = BusinessProposal.objects.create(
        title='Contrato visible',
        client_name='Cliente',
        client_email='cliente@example.com',
        language='es',
        total_investment=Decimal('5000000'),
        currency='COP',
    )

    apply_proposal_json_update(proposal, {
        'show_contract_terms': False,
        'sections': {},
    })

    proposal.refresh_from_db()
    assert proposal.show_contract_terms is False
