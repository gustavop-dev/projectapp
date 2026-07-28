"""Tests for the refresh_proposal_default_config _patch extension.

The command must copy the free-module scope-cap copy (title/description/items)
and the value_added_modules conditions from code into a drifted snapshot.
"""
import copy

import pytest

from content.management.commands.refresh_proposal_default_config import _patch
from content.services.proposal_service import DEFAULT_SECTIONS

pytestmark = pytest.mark.django_db


def _drifted_snapshot():
    """Code defaults with the analytics description and one condition reverted
    to a pre-caps value, simulating a stale DB snapshot."""
    snapshot = copy.deepcopy(DEFAULT_SECTIONS)
    fr = next(s for s in snapshot
              if s['section_type'] == 'functional_requirements')
    analytics = next(g for g in fr['content_json']['groups']
                     if g['id'] == 'analytics_dashboard')
    analytics['description'] = 'Old description without caps.'
    va = next(s for s in snapshot
              if s['section_type'] == 'value_added_modules')
    va['content_json']['conditions']['manual_module'] = {
        'min_price_usd': None, 'min_price_cop': None,
        'duration_months': None, 'discretionary_note': 'old',
        'terms': 'Old terms without caps.',
    }
    return snapshot


class TestPatchFreeModuleCaps:
    def test_copies_free_module_description_from_code(self):
        snapshot = _drifted_snapshot()
        changes = _patch(snapshot, copy.deepcopy(DEFAULT_SECTIONS))
        assert 'analytics_dashboard.description -> code' in changes
        fr = next(s for s in snapshot
                  if s['section_type'] == 'functional_requirements')
        analytics = next(g for g in fr['content_json']['groups']
                         if g['id'] == 'analytics_dashboard')
        assert 'hasta 6 reportes estándar' in analytics['description']

    def test_overwrites_drifted_conditions_from_code(self):
        snapshot = _drifted_snapshot()
        changes = _patch(snapshot, copy.deepcopy(DEFAULT_SECTIONS))
        assert 'conditions.manual_module -> code' in changes
        va = next(s for s in snapshot
                  if s['section_type'] == 'value_added_modules')
        terms = va['content_json']['conditions']['manual_module']['terms']
        assert '**15 artículos**' in terms

    def test_noop_when_snapshot_matches_code(self):
        snapshot = copy.deepcopy(DEFAULT_SECTIONS)
        changes = _patch(snapshot, copy.deepcopy(DEFAULT_SECTIONS))
        assert changes == []


class TestPatchLegalTerms:
    """The scope clause and the general provisions had no sync path before.

    That is why the corrected scope wording never reached the generated PDF:
    _patch simply did not know about commercial_conditions.
    """

    def test_repairs_a_stale_scope_clause(self):
        snapshot = copy.deepcopy(DEFAULT_SECTIONS)
        cc = next(s for s in snapshot
                  if s['section_type'] == 'commercial_conditions')
        cc['content_json']['scopeParagraphs'] = [
            'Cualquier solicitud que surja durante el proyecto no aplica.',
        ]

        changes = _patch(snapshot, copy.deepcopy(DEFAULT_SECTIONS))

        assert 'commercial_conditions.scopeParagraphs -> code' in changes
        paragraphs = cc['content_json']['scopeParagraphs']
        assert any('**antes o durante**' in p for p in paragraphs)
        assert any('correo electrónico' in p for p in paragraphs)

    def test_restores_missing_general_terms(self):
        snapshot = copy.deepcopy(DEFAULT_SECTIONS)
        va = next(s for s in snapshot
                  if s['section_type'] == 'value_added_modules')
        del va['content_json']['general_terms']

        changes = _patch(snapshot, copy.deepcopy(DEFAULT_SECTIONS))

        assert 'general_terms -> code' in changes
        clauses = va['content_json']['general_terms']['clauses']
        labels = [c['label'] for c in clauses]
        assert 'Fuerza mayor y caso fortuito' in labels
