"""Integrity and seeding behavior of the per-module technical requirements catalog.

The catalog must stay in lockstep with the DEFAULT_SECTIONS additionalModules
(names resolve to real item ids, flowKeys identical across languages), and the
seeder must fill only uncovered, visible, non-invite modules — idempotently.
"""

import copy
import re

import pytest

from content.services.module_requirements_catalog import (
    MODULE_REQUIREMENTS_CATALOG,
    seed_module_technical_requirements,
)
from content.services.proposal_module_links import (
    build_item_id,
    build_item_requirements_map,
)
from content.services.proposal_service import (
    DEFAULT_SECTIONS,
    DEFAULT_SECTIONS_EN,
    apply_proposal_json_update,
    build_proposal_from_json,
)

KEBAB_RE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')

# 14 catalog entries; gift_cards_module is excluded at runtime (is_visible=False)
EXPECTED_SEEDED_MODULE_IDS = {
    'integration_electronic_invoicing',
    'integration_regional_payments',
    'integration_international_payments',
    'pwa_module',
    'corporate_branding_module',
    'behavior_tracking_module',
    'reports_alerts_module',
    'email_marketing_module',
    'qr_generator_module',
    'content_generator_module',
    'i18n_module',
    'live_chat_module',
    'dark_mode_module',
}


def _default_fr_content(language='es'):
    source = DEFAULT_SECTIONS_EN if language == 'en' else DEFAULT_SECTIONS
    fr = next(s for s in source if s['section_type'] == 'functional_requirements')
    return copy.deepcopy(fr['content_json'])


def _sections_payload(fr_content):
    return [{'section_type': 'functional_requirements', 'content_json': fr_content}]


def _seeded_module_ids(doc):
    ids = set()
    for epic in doc.get('epics') or []:
        for raw in epic.get('linked_module_ids') or []:
            ids.add(raw.replace('module-', '', 1) if raw.startswith('module-') else raw)
    return ids


# ===========================================================================
# Catalog integrity
# ===========================================================================

def test_catalog_language_parity():
    """ES and EN cover the same modules with identical flowKeys in the same order."""
    es, en = MODULE_REQUIREMENTS_CATALOG['es'], MODULE_REQUIREMENTS_CATALOG['en']
    assert set(es.keys()) == set(en.keys())
    for module_id in es:
        es_keys = [r['flowKey'] for r in es[module_id]['requirements']]
        en_keys = [r['flowKey'] for r in en[module_id]['requirements']]
        assert es_keys == en_keys, f'flowKey drift in {module_id}'


@pytest.mark.parametrize('language', ['es', 'en'])
def test_catalog_items_resolve_against_default_modules(language):
    """Every catalog `item` matches a default item name of its module (per language)."""
    fr = _default_fr_content(language)
    default_items = {
        m['id']: {i['name'] for i in m.get('items') or []}
        for m in fr['additionalModules']
    }
    for module_id, entry in MODULE_REQUIREMENTS_CATALOG[language].items():
        assert module_id in default_items, f'{module_id} not in defaults'
        for req in entry['requirements']:
            assert req['item'] in default_items[module_id], (
                f'{language}:{module_id}: catalog item «{req["item"]}» '
                'does not match any default module item'
            )


@pytest.mark.parametrize('language', ['es', 'en'])
def test_catalog_flow_keys_unique_and_kebab(language):
    seen = set()
    for module_id, entry in MODULE_REQUIREMENTS_CATALOG[language].items():
        for req in entry['requirements']:
            flow_key = req['flowKey']
            assert KEBAB_RE.match(flow_key), f'{module_id}: non-kebab flowKey {flow_key}'
            assert flow_key not in seen, f'duplicate flowKey {flow_key}'
            seen.add(flow_key)


def test_catalog_covers_all_non_invite_default_modules():
    """Catalog has an entry for every default additionalModule that is not invite-only."""
    fr = _default_fr_content('es')
    non_invite = {m['id'] for m in fr['additionalModules'] if not m.get('is_invite')}
    assert set(MODULE_REQUIREMENTS_CATALOG['es'].keys()) == non_invite


# ===========================================================================
# Seeder behavior (pure function)
# ===========================================================================

def test_seed_adds_epics_for_all_visible_non_invite_modules():
    fr = _default_fr_content('es')
    out = seed_module_technical_requirements({}, _sections_payload(fr), 'es')

    assert _seeded_module_ids(out) == EXPECTED_SEEDED_MODULE_IDS
    for epic in out['epics']:
        assert KEBAB_RE.match(epic['epicKey']), epic['epicKey']
        assert epic['requirements'], f'{epic["epicKey"]} seeded empty'
        for req in epic['requirements']:
            assert req['title'] and req['description']
            assert req['linked_module_ids'] == epic['linked_module_ids']
            assert len(req['linked_item_ids']) == 1, (
                f'{req["flowKey"]}: expected one resolved linked item id'
            )


def test_seed_links_resolve_to_default_item_ids():
    fr = _default_fr_content('es')
    out = seed_module_technical_requirements({}, _sections_payload(fr), 'es')
    pwa_epic = next(e for e in out['epics'] if e['linked_module_ids'] == ['pwa_module'])
    expected = build_item_id('pwa_module', 'Instalación en dispositivo')
    linked = {i for r in pwa_epic['requirements'] for i in r['linked_item_ids']}
    assert expected in linked


def test_seed_skips_covered_module():
    fr = _default_fr_content('es')
    doc = {'epics': [{
        'epicKey': 'custom-pwa',
        'title': 'PWA hecha a mano',
        'linked_module_ids': ['module-pwa_module'],
        'requirements': [{'flowKey': 'custom-pwa-flujo', 'title': 'Propio'}],
    }]}
    out = seed_module_technical_requirements(doc, _sections_payload(fr), 'es')

    pwa_epics = [
        e for e in out['epics']
        if 'module-pwa_module' in (e.get('linked_module_ids') or [])
        or 'pwa_module' in (e.get('linked_module_ids') or [])
    ]
    assert len(pwa_epics) == 1
    assert pwa_epics[0]['epicKey'] == 'custom-pwa'
    assert len(pwa_epics[0]['requirements']) == 1


def test_seed_fills_matching_empty_epic_without_duplicating():
    fr = _default_fr_content('es')
    doc = {'epics': [{'epicKey': 'pwa_module', 'title': 'PWA', 'requirements': []}]}
    out = seed_module_technical_requirements(doc, _sections_payload(fr), 'es')

    pwa_epics = [e for e in out['epics'] if e['epicKey'] in ('pwa_module', 'mod-pwa-module')]
    assert len(pwa_epics) == 1
    assert pwa_epics[0]['epicKey'] == 'pwa_module'
    assert len(pwa_epics[0]['requirements']) == 6
    assert 'pwa_module' in pwa_epics[0]['linked_module_ids']


def test_seed_skips_invite_and_hidden_modules():
    fr = _default_fr_content('es')
    out = seed_module_technical_requirements({}, _sections_payload(fr), 'es')
    seeded = _seeded_module_ids(out)
    assert 'ai_module' not in seeded
    assert 'biometric_verification_module' not in seeded
    assert 'gift_cards_module' not in seeded


def test_seed_is_idempotent():
    fr = _default_fr_content('es')
    once = seed_module_technical_requirements({}, _sections_payload(fr), 'es')
    twice = seed_module_technical_requirements(once, _sections_payload(fr), 'es')
    assert twice == once


def test_seed_dedupes_colliding_flow_keys():
    fr = _default_fr_content('es')
    doc = {'epics': [{
        'epicKey': 'otras-notas',
        'title': 'Notas',
        'requirements': [{'flowKey': 'pwa-instalacion-dispositivo', 'title': 'Sin relación'}],
    }]}
    out = seed_module_technical_requirements(doc, _sections_payload(fr), 'es')
    pwa_epic = next(e for e in out['epics'] if e.get('linked_module_ids') == ['pwa_module'])
    flow_keys = [r['flowKey'] for r in pwa_epic['requirements']]
    assert 'pwa-instalacion-dispositivo-2' in flow_keys
    assert 'pwa-instalacion-dispositivo' not in flow_keys


# ===========================================================================
# Integration through the from-JSON create/update paths
# ===========================================================================

@pytest.mark.django_db
def test_build_proposal_from_json_seeds_with_canonical_links():
    proposal, _ = build_proposal_from_json({
        'title': 'Seeded', 'client_name': 'Cliente', 'language': 'es',
        'sections': {},
    })
    section = proposal.sections.get(section_type='technical_document')
    content = section.content_json

    seeded = _seeded_module_ids(content)
    assert EXPECTED_SEEDED_MODULE_IDS <= seeded
    pwa_epic = next(
        e for e in content['epics']
        if 'module-pwa_module' in (e.get('linked_module_ids') or [])
    )
    assert pwa_epic['requirements']

    item_map = build_item_requirements_map(content)
    pwa_item_id = build_item_id('pwa_module', 'Instalación en dispositivo')
    assert item_map.get(pwa_item_id), 'module item should list its seeded requirements'


@pytest.mark.django_db
def test_apply_proposal_json_update_reseeds_uncovered_technical_document():
    proposal, _ = build_proposal_from_json({
        'title': 'Reseed', 'client_name': 'Cliente', 'language': 'es',
        'sections': {},
    })
    apply_proposal_json_update(proposal, {'sections': {'technicalDocument': {}}})

    section = proposal.sections.get(section_type='technical_document')
    assert EXPECTED_SEEDED_MODULE_IDS <= _seeded_module_ids(section.content_json)
