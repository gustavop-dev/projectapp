"""Tests for migration 0156 (behavior_tracking_module backfill).

Covers the pure helpers (anchor insert, snapshot augment, idempotency,
customization preservation) and the DefaultConfig backfill against the DB.
"""
import importlib

import pytest
from django.apps import apps as django_apps

from content.models import ProposalDefaultConfig
from content.services.proposal_service import DEFAULT_SECTIONS

pytestmark = pytest.mark.django_db

_migration = importlib.import_module(
    'content.migrations.0156_behavior_tracking_module'
)


def _fr_modules(anchor=True):
    modules = [{'id': 'pwa_module'}]
    if anchor:
        modules.append({'id': 'reports_alerts_module'})
    modules.append({'id': 'email_marketing_module'})
    return modules


def _sample_sections(anchor=True):
    return [
        {'section_type': 'functional_requirements',
         'content_json': {'groups': [{'id': 'admin_module'}],
                          'additionalModules': _fr_modules(anchor=anchor)}},
        {'section_type': 'value_added_modules',
         'content_json': {'module_ids': ['admin_module'],
                          'justifications': {}, 'conditions': {}}},
    ]


class TestInsertBeforeAnchor:
    def test_inserts_immediately_before_reports_alerts(self):
        modules = _fr_modules()
        module = _migration._behavior_module(DEFAULT_SECTIONS)
        assert module is not None
        modules, changed = _migration._insert_before_anchor(modules, module)
        assert changed is True
        ids = [m['id'] for m in modules]
        assert ids.index('behavior_tracking_module') + 1 == ids.index('reports_alerts_module')

    def test_appends_when_anchor_missing(self):
        modules = _fr_modules(anchor=False)
        module = _migration._behavior_module(DEFAULT_SECTIONS)
        modules, changed = _migration._insert_before_anchor(modules, module)
        assert changed is True
        assert modules[-1]['id'] == 'behavior_tracking_module'

    def test_skips_existing_customized_module(self):
        custom = {'id': 'behavior_tracking_module', 'title': 'Custom title',
                  'price_percent': 45}
        modules = [custom] + _fr_modules()
        module = _migration._behavior_module(DEFAULT_SECTIONS)
        modules, changed = _migration._insert_before_anchor(modules, module)
        assert changed is False
        kept = [m for m in modules if m['id'] == 'behavior_tracking_module']
        assert kept == [custom]


class TestAugmentSectionsJson:
    def test_adds_module_and_missing_conditions(self):
        sections = _sample_sections()
        changed = _migration._augment_sections_json(sections, DEFAULT_SECTIONS)
        assert changed is True
        fr = next(s for s in sections
                  if s['section_type'] == 'functional_requirements')
        ids = [m['id'] for m in fr['content_json']['additionalModules']]
        assert 'behavior_tracking_module' in ids
        va = next(s for s in sections
                  if s['section_type'] == 'value_added_modules')
        assert 'ai_automation_module' in va['content_json']['conditions']

    def test_idempotent(self):
        sections = _sample_sections()
        _migration._augment_sections_json(sections, DEFAULT_SECTIONS)
        fr = next(s for s in sections
                  if s['section_type'] == 'functional_requirements')
        n_before = len(fr['content_json']['additionalModules'])
        changed = _migration._augment_sections_json(sections, DEFAULT_SECTIONS)
        assert changed is False
        assert len(fr['content_json']['additionalModules']) == n_before

    def test_does_not_overwrite_existing_conditions(self):
        sections = _sample_sections()
        va = next(s for s in sections
                  if s['section_type'] == 'value_added_modules')
        custom_cond = {'min_price_usd': 999, 'terms': 'custom terms'}
        va['content_json']['conditions']['ai_automation_module'] = custom_cond
        _migration._augment_sections_json(sections, DEFAULT_SECTIONS)
        assert va['content_json']['conditions']['ai_automation_module'] == custom_cond


class TestBackfillDefaultConfigs:
    def test_patches_populated_snapshot(self):
        config = ProposalDefaultConfig.objects.create(
            language='es', sections_json=_sample_sections())
        _migration.backfill_default_configs(django_apps)
        config.refresh_from_db()
        fr = next(s for s in config.sections_json
                  if s['section_type'] == 'functional_requirements')
        ids = [m['id'] for m in fr['content_json']['additionalModules']]
        assert ids.index('behavior_tracking_module') + 1 == ids.index('reports_alerts_module')

    def test_ignores_empty_snapshot(self):
        config = ProposalDefaultConfig.objects.create(
            language='es', sections_json=[])
        _migration.backfill_default_configs(django_apps)
        config.refresh_from_db()
        assert config.sections_json == []
