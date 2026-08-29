"""Reusable traceability setup for proposal endpoint tests."""

from content.models import BusinessProposal, ProposalSection

TRACEABILITY_ITEM_ID = 'item-views-login'


def technical_document(linked_item_ids: list[str]) -> dict:
    return {
        'epics': [{
            'title': 'Acceso',
            'epicKey': 'acceso',
            'requirements': [{
                'title': 'Entrar',
                'flowKey': 'entrar',
                'linked_item_ids': linked_item_ids,
            }],
        }],
    }


def create_traced_proposal_sections(proposal: BusinessProposal) -> ProposalSection:
    ProposalSection.objects.create(
        proposal=proposal,
        section_type='functional_requirements',
        title='Requerimientos',
        order=10,
        content_json={
            'groups': [{
                'id': 'views',
                'title': 'Vistas',
                'items': [{
                    'id': TRACEABILITY_ITEM_ID,
                    'name': 'Inicio de sesión',
                }],
            }],
            'additionalModules': [],
        },
    )
    return ProposalSection.objects.create(
        proposal=proposal,
        section_type='technical_document',
        title='Detalle técnico',
        order=16,
        content_json=technical_document([TRACEABILITY_ITEM_ID]),
    )
