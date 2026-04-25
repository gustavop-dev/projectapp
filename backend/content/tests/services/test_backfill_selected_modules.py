"""Tests for content/migrations/0113_backfill_selected_modules.py.

The migration populates `BusinessProposal.selected_modules` for legacy
rows that have a `calc_confirmed` log but an empty list — preserving their
effective-total behaviour once the fallback heuristic is removed.
"""
from decimal import Decimal
from importlib import import_module

import pytest
from django.apps import apps as django_apps
from django.utils import timezone
from freezegun import freeze_time

from content.models import (
    BusinessProposal,
    ProposalChangeLog,
    ProposalSection,
)

pytestmark = pytest.mark.django_db


FR_CONTENT = {
    'additionalModules': [
        {
            'id': 'reports_alerts_module',
            'title': 'Reports',
            'is_visible': True,
            'is_calculator_module': True,
            'default_selected': True,
            'price_percent': 20,
        },
        {
            'id': 'pwa_module',
            'title': 'PWA',
            'is_visible': True,
            'is_calculator_module': True,
            'default_selected': False,
            'price_percent': 40,
        },
        {
            'id': 'ai_module',
            'title': 'AI',
            'is_visible': True,
            'is_calculator_module': True,
            'selected': True,
            'price_percent': 0,
        },
    ],
    'groups': [],
}


def _make_proposal(title, selected_modules, with_confirmed_log):
    proposal = BusinessProposal.objects.create(
        title=title,
        client_name=title,
        client_email=f'{title}@test.com',
        language='es',
        total_investment=Decimal('1800000'),
        currency='COP',
        status='sent',
        expires_at=timezone.now() + timezone.timedelta(days=15),
        selected_modules=selected_modules,
    )
    ProposalSection.objects.create(
        proposal=proposal,
        section_type='functional_requirements',
        title='FR', order=1, is_enabled=True,
        content_json=FR_CONTENT,
    )
    if with_confirmed_log:
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type=ProposalChangeLog.ChangeType.CALCULATOR_CONFIRMED,
        )
    return proposal


@pytest.fixture
def backfill_fn():
    """Return the migration's `backfill` callable."""
    module = import_module('content.migrations.0113_backfill_selected_modules')
    return module.backfill


class TestBackfillSelectedModules:
    def test_confirmed_proposal_with_empty_list_is_populated(self, backfill_fn):
        """The flagship case: confirmed + empty → populate with canonical
        IDs derived from content defaults."""
        proposal = _make_proposal('Target', selected_modules=[], with_confirmed_log=True)

        backfill_fn(django_apps, schema_editor=None)
        proposal.refresh_from_db()

        # Both reports_alerts (default_selected=True) and ai (selected=True)
        # pass the filter; pwa (default_selected=False) does not.
        assert set(proposal.selected_modules) == {
            'module-reports_alerts_module', 'module-ai_module',
        }

    def test_confirmed_proposal_with_existing_list_is_untouched(self, backfill_fn):
        """Must never overwrite an already-populated list."""
        proposal = _make_proposal(
            'Preserved',
            selected_modules=['module-pwa_module'],
            with_confirmed_log=True,
        )

        backfill_fn(django_apps, schema_editor=None)
        proposal.refresh_from_db()

        assert proposal.selected_modules == ['module-pwa_module']

    def test_unconfirmed_proposal_is_untouched(self, backfill_fn):
        """Without a confirmation log we can't distinguish "empty deliberate"
        from "never configured", so we leave the row alone."""
        proposal = _make_proposal(
            'Unconfirmed',
            selected_modules=[],
            with_confirmed_log=False,
        )

        backfill_fn(django_apps, schema_editor=None)
        proposal.refresh_from_db()

        assert proposal.selected_modules == []

    @freeze_time('2026-01-15 12:00:00')
    def test_confirmed_proposal_without_FR_section_is_untouched(self, backfill_fn):
        """Degenerate case: no FR section → nothing to derive, leave empty."""
        proposal = BusinessProposal.objects.create(
            title='NoFR', client_name='NoFR', client_email='nofr@test.com',
            language='es', total_investment=Decimal('1800000'), currency='COP',
            status='sent',
            expires_at=timezone.now() + timezone.timedelta(days=15),
            selected_modules=[],
        )
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type=ProposalChangeLog.ChangeType.CALCULATOR_CONFIRMED,
        )

        backfill_fn(django_apps, schema_editor=None)
        proposal.refresh_from_db()

        assert proposal.selected_modules == []
