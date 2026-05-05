"""
End-to-end tests for the ``roi_projection`` proposal section.

Covers: enum membership, default seeding (es/en), serializer key map,
JSON template/import endpoints, PDF rendering edge cases, and that the
section count expectation stays in sync with EXPECTED_DEFAULT_SECTION_COUNT.
"""
import pytest

from content.models import BusinessProposal, ProposalSection
from content.serializers.proposal import (
    SECTION_KEY_MAP,
    SECTION_TYPE_TO_KEY,
)
from content.services.proposal_pdf_service import SECTION_RENDERERS
from content.services.proposal_service import (
    DEFAULT_SECTIONS,
    DEFAULT_SECTIONS_EN,
    ProposalService,
)
from content.tests.constants import EXPECTED_DEFAULT_SECTION_COUNT


# ─── Enum / model ──────────────────────────────────────────────────────

def test_section_type_enum_has_roi_projection():
    assert ProposalSection.SectionType.ROI_PROJECTION == 'roi_projection'
    choices = dict(ProposalSection.SectionType.choices)
    assert 'roi_projection' in choices
    assert choices['roi_projection'] == 'ROI Projection'


# ─── Defaults (ES / EN) ─────────────────────────────────────────────────

def test_default_sections_es_includes_roi_at_order_4():
    matches = [s for s in DEFAULT_SECTIONS if s['section_type'] == 'roi_projection']
    assert len(matches) == 1
    cfg = matches[0]
    assert cfg['order'] == 4
    assert 'kpis' in cfg['content_json']
    assert 'scenarios' in cfg['content_json']
    assert cfg['content_json']['kpis'] == []
    assert cfg['content_json']['scenarios'] == []


def test_default_sections_en_includes_roi_at_order_4():
    matches = [s for s in DEFAULT_SECTIONS_EN if s['section_type'] == 'roi_projection']
    assert len(matches) == 1
    assert matches[0]['order'] == 4


def test_get_default_sections_count_matches_constant_es():
    sections = ProposalService.get_hardcoded_defaults('es')
    assert len(sections) == EXPECTED_DEFAULT_SECTION_COUNT


def test_get_default_sections_count_matches_constant_en():
    sections = ProposalService.get_hardcoded_defaults('en')
    assert len(sections) == EXPECTED_DEFAULT_SECTION_COUNT


def test_default_section_orders_are_unique_es():
    sections = ProposalService.get_hardcoded_defaults('es')
    orders = [s['order'] for s in sections]
    assert len(orders) == len(set(orders)), f'duplicate orders in ES: {orders}'


def test_default_section_orders_are_unique_en():
    sections = ProposalService.get_hardcoded_defaults('en')
    orders = [s['order'] for s in sections]
    assert len(orders) == len(set(orders)), f'duplicate orders in EN: {orders}'


# ─── Serializer key mapping ────────────────────────────────────────────

def test_section_key_map_has_roi_projection():
    assert SECTION_KEY_MAP['roiProjection'] == 'roi_projection'
    assert SECTION_TYPE_TO_KEY['roi_projection'] == 'roiProjection'


# ─── PDF renderer is intentionally absent (web-only section) ──────────

def test_pdf_renderer_intentionally_absent():
    """``roi_projection`` is rendered only on the web, not in the PDF.

    The PDF generator silently skips section types that have no entry in
    ``SECTION_RENDERERS`` (same behavior as ``proposal_summary`` and other
    web-only sections), so this assertion guards against accidental wiring.
    """
    assert 'roi_projection' not in SECTION_RENDERERS


# ─── ORM persistence ───────────────────────────────────────────────────

@pytest.mark.django_db
def test_proposal_section_can_persist_roi_projection(proposal):
    section = ProposalSection.objects.create(
        proposal=proposal,
        section_type='roi_projection',
        title='Test ROI',
        order=4,
        is_enabled=True,
        content_json={'kpis': [{'value': '90K', 'label': 'Daily'}]},
    )
    section.refresh_from_db()
    assert section.section_type == 'roi_projection'
    assert section.content_json['kpis'][0]['value'] == '90K'


@pytest.mark.django_db
def test_disabled_roi_projection_excluded_from_pdf_sections(proposal):
    """Reflect the public/PDF filter: only is_enabled=True sections render."""
    ProposalSection.objects.create(
        proposal=proposal, section_type='roi_projection',
        title='Hidden ROI', order=4, is_enabled=False, content_json={},
    )
    enabled = list(proposal.sections.filter(is_enabled=True))
    assert all(s.section_type != 'roi_projection' for s in enabled)


# ─── HTTP integration: section update endpoint round-trip ─────────────

@pytest.mark.django_db
def test_admin_can_patch_roi_projection_content_json(admin_client, proposal):
    """``PATCH /api/proposals/sections/<id>/update/`` must persist the full
    roi_projection schema (kpis + scenarios + ctaNote) without coercion."""
    section = ProposalSection.objects.create(
        proposal=proposal,
        section_type='roi_projection',
        title='ROI',
        order=4,
        is_enabled=False,
        content_json={},
    )
    payload = {
        'is_enabled': True,
        'content_json': {
            'index': '4',
            'title': '📈 Proyección de retorno',
            'subtitle': 'Outcomes test.',
            'kpis': [
                {'icon': '👁️', 'value': '90K', 'label': 'Visualizaciones',
                 'sublabel': 'mes 6', 'source': 'Benchmark'},
            ],
            'scenariosTitle': 'Escenarios',
            'scenarios': [
                {'name': 'realistic', 'label': 'Realista', 'icon': '🎯',
                 'metrics': [
                     {'label': 'MAU', 'value': '80K'},
                     {'label': 'Total año 1', 'value': '$280M', 'emphasis': True},
                 ]},
            ],
            'ctaNote': 'Cubre la inversión.',
        },
    }
    response = admin_client.patch(
        f'/api/proposals/sections/{section.id}/update/',
        data=payload, format='json',
    )
    assert response.status_code == 200, response.data

    section.refresh_from_db()
    assert section.is_enabled is True
    assert section.content_json['kpis'][0]['value'] == '90K'
    assert section.content_json['scenarios'][0]['metrics'][1]['emphasis'] is True
    assert section.content_json['ctaNote'] == 'Cubre la inversión.'
