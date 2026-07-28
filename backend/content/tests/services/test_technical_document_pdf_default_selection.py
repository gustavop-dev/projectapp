"""The technical PDF derives the proposal's module selection when none is given.

Regression for the leak where ``generate_technical_document_pdf(proposal)``
(email attachment, document flows, platform onboarding) rendered epics of
optional modules the client never selected.
"""

import io

import pytest
from pypdf import PdfReader

from content.models import ProposalSection
from content.services.technical_document_pdf import generate_technical_document_pdf


def _fr_section(proposal, module):
    return ProposalSection.objects.create(
        proposal=proposal,
        section_type='functional_requirements',
        title='Requerimientos',
        order=0,
        is_enabled=True,
        content_json={
            'title': 'Requerimientos Funcionales',
            'groups': [],
            'additionalModules': [module],
        },
    )


def _technical_section(proposal, module_id):
    return ProposalSection.objects.create(
        proposal=proposal,
        section_type='technical_document',
        title='Detalle técnico',
        order=1,
        is_enabled=True,
        content_json={
            'epics': [
                {
                    'epicKey': 'views',
                    'title': 'Vistas',
                    'requirements': [{
                        'flowKey': 'base-alcance',
                        'title': 'Panel principal navegable',
                        'description': 'Alcance base.',
                        'priority': 'high',
                    }],
                },
                {
                    'epicKey': 'mod-pwa-module',
                    'title': 'Alcance ampliado: PWA',
                    'linked_module_ids': [f'module-{module_id}'],
                    'requirements': [{
                        'flowKey': 'pwa-instalacion',
                        'title': 'Instalable como aplicacion',
                        'description': 'Manifest y service worker.',
                        'priority': 'high',
                        'linked_module_ids': [f'module-{module_id}'],
                    }],
                },
            ],
        },
    )


def _pdf_text(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return '\n'.join((page.extract_text() or '') for page in reader.pages)


@pytest.mark.django_db
def test_unselected_module_epic_excluded_without_explicit_selection(sent_proposal):
    _fr_section(sent_proposal, {
        'id': 'pwa_module', 'title': 'PWA', 'is_calculator_module': True,
        'is_visible': True, 'selected': False, 'default_selected': False,
        'price_percent': 40, 'items': [],
    })
    _technical_section(sent_proposal, 'pwa_module')

    pdf = generate_technical_document_pdf(sent_proposal)

    assert pdf and pdf[:4] == b'%PDF'
    text = _pdf_text(pdf)
    assert 'navegable' in text
    assert 'Instalable' not in text


@pytest.mark.django_db
def test_admin_selected_module_epic_included_without_explicit_selection(sent_proposal):
    _fr_section(sent_proposal, {
        'id': 'pwa_module', 'title': 'PWA', 'is_calculator_module': True,
        'is_visible': True, 'selected': True, 'default_selected': True,
        'price_percent': 40, 'items': [],
    })
    _technical_section(sent_proposal, 'pwa_module')

    pdf = generate_technical_document_pdf(sent_proposal)

    assert pdf and pdf[:4] == b'%PDF'
    text = _pdf_text(pdf)
    assert 'navegable' in text
    assert 'Instalable' in text
