"""refresh_proposal_default_config re-injects default FR entries a stored
config predates, without clobbering per-module customizations.

Regression for the prod drift where modules added to code after the stored
snapshot (qr_generator, content_generator, biometric) silently vanished from
every new ES proposal: the command only patched listed modules and never
noticed missing ones.
"""

import copy
import json

import pytest
from django.core.management import call_command

from content.management.commands.refresh_proposal_default_config import _patch
from content.models import ProposalDefaultConfig
from content.services.proposal_service import DEFAULT_SECTIONS


def _sections_without_module(module_id):
    sections = copy.deepcopy(DEFAULT_SECTIONS)
    fr = next(s for s in sections if s['section_type'] == 'functional_requirements')
    fr['content_json']['additionalModules'] = [
        m for m in fr['content_json']['additionalModules'] if m['id'] != module_id
    ]
    return sections


def _fr_module_ids(sections):
    fr = next(s for s in sections if s['section_type'] == 'functional_requirements')
    return [m['id'] for m in fr['content_json']['additionalModules']]


def _fr_module(sections, module_id):
    fr = next(s for s in sections if s['section_type'] == 'functional_requirements')
    return next(m for m in fr['content_json']['additionalModules'] if m['id'] == module_id)


def test_reinject_adds_missing_module_in_code_order():
    stored = _sections_without_module('qr_generator_module')
    code = copy.deepcopy(DEFAULT_SECTIONS)

    changes = _patch(stored, code)

    assert _fr_module_ids(stored) == _fr_module_ids(code)
    assert any('qr_generator_module' in c for c in changes)


def test_reinject_preserves_stored_customizations_of_existing_modules():
    stored = _sections_without_module('content_generator_module')
    pwa = _fr_module(stored, 'pwa_module')
    pwa['title'] = 'PWA personalizada del operador'
    code = copy.deepcopy(DEFAULT_SECTIONS)

    _patch(stored, code)

    assert _fr_module(stored, 'pwa_module')['title'] == 'PWA personalizada del operador'
    assert _fr_module(stored, 'content_generator_module')['items']


def test_reinject_keeps_stored_only_extras_at_the_end():
    stored = _sections_without_module('qr_generator_module')
    fr = next(s for s in stored if s['section_type'] == 'functional_requirements')
    fr['content_json']['additionalModules'].append({
        'id': 'custom_operator_module', 'title': 'Custom', 'items': [],
    })
    code = copy.deepcopy(DEFAULT_SECTIONS)

    _patch(stored, code)

    ids = _fr_module_ids(stored)
    assert ids[-1] == 'custom_operator_module'
    assert ids[:-1] == _fr_module_ids(code)


def test_reinject_noop_when_nothing_is_missing():
    stored = copy.deepcopy(DEFAULT_SECTIONS)
    fr = next(s for s in stored if s['section_type'] == 'functional_requirements')
    fr['content_json']['additionalModules'].reverse()
    reversed_ids = _fr_module_ids(stored)
    code = copy.deepcopy(DEFAULT_SECTIONS)

    changes = _patch(stored, code)

    assert _fr_module_ids(stored) == reversed_ids
    assert not any('re-injected' in c for c in changes)


@pytest.mark.django_db
def test_command_apply_reinjects_missing_module_into_stored_config(tmp_path):
    ProposalDefaultConfig.objects.create(
        language='es',
        sections_json=_sections_without_module('qr_generator_module'),
    )

    call_command(
        'refresh_proposal_default_config', '--apply', '--language', 'es',
        '--backup-dir', str(tmp_path),
    )

    cfg = ProposalDefaultConfig.objects.get(language='es')
    assert 'qr_generator_module' in _fr_module_ids(cfg.sections_json)
    backup = tmp_path / 'proposal_default_config_es.backup.json'
    assert backup.exists()
    assert 'qr_generator_module' not in _fr_module_ids(json.loads(backup.read_text()))
