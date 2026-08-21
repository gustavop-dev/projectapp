from importlib import import_module

import pytest
from django.apps import apps

from content.models import BusinessProposal, ProposalSection


pytestmark = pytest.mark.django_db
migration = import_module('content.migrations.0206_proposal_intro_emphasis')


def make_proposal(slug):
    return BusinessProposal.objects.create(
        title='Visor meteorológico',
        client_name='Ramon',
        slug=slug,
    )


def test_forward_adds_emphasis_to_exact_ramon_intro_copy():
    proposal = make_proposal('ramon-emiliani')
    section = ProposalSection.objects.create(
        proposal=proposal,
        section_type='development_stages',
        title='Etapas',
        content_json={
            'intro': 'El proyecto avanza mediante hitos verificables y aprobaciones consolidadas:',
        },
    )

    migration.add_ramon_intro_emphasis(apps, None)

    section.refresh_from_db()
    assert section.content_json['intro'] == (
        'El proyecto avanza mediante '
        '<b>hitos verificables y aprobaciones consolidadas</b>:'
    )


def test_forward_does_not_change_another_proposal():
    proposal = make_proposal('otra-propuesta')
    section = ProposalSection.objects.create(
        proposal=proposal,
        section_type='roi_projection',
        title='Beneficios',
        content_json={
            'subtitle': 'Indicadores verificables del producto, sin atribuir retornos financieros no sustentados.',
        },
    )

    migration.add_ramon_intro_emphasis(apps, None)

    section.refresh_from_db()
    assert section.content_json['subtitle'] == (
        'Indicadores verificables del producto, sin atribuir retornos financieros no sustentados.'
    )


def test_forward_does_not_add_a_missing_intro_field():
    proposal = make_proposal('ramon-emiliani')
    section = ProposalSection.objects.create(
        proposal=proposal,
        section_type='development_stages',
        title='Etapas',
        content_json={'items': []},
    )

    migration.add_ramon_intro_emphasis(apps, None)

    section.refresh_from_db()
    assert section.content_json == {'items': []}


def test_reverse_preserves_copy_edited_after_forward_migration():
    proposal = make_proposal('ramon-emiliani')
    section = ProposalSection.objects.create(
        proposal=proposal,
        section_type='roi_projection',
        title='Beneficios',
        content_json={
            'subtitle': '<b>Texto editado posteriormente</b> por el vendedor.',
        },
    )

    migration.remove_ramon_intro_emphasis(apps, None)

    section.refresh_from_db()
    assert section.content_json['subtitle'] == (
        '<b>Texto editado posteriormente</b> por el vendedor.'
    )
