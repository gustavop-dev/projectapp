"""Tests for the proposal audit-log helper.

Covers: log_proposal_change() field persistence, defaults, return value,
and behavior inside an atomic transaction.
"""
import pytest
from django.db import transaction

from content.models import ProposalChangeLog
from content.services.proposal_audit import log_proposal_change

pytestmark = pytest.mark.django_db


class TestLogProposalChange:
    def test_creates_row_with_all_fields(self, proposal):
        log_proposal_change(
            proposal,
            'updated',
            actor_type='client',
            description='Field changed by client.',
            field_name='title',
            old_value='Old title',
            new_value='New title',
        )
        log = ProposalChangeLog.objects.get(proposal=proposal)
        assert log.change_type == 'updated'
        assert log.actor_type == 'client'
        assert log.description == 'Field changed by client.'
        assert log.field_name == 'title'
        assert log.old_value == 'Old title'
        assert log.new_value == 'New title'

    def test_defaults_match_dominant_call_style(self, proposal):
        log = log_proposal_change(proposal, 'created')
        assert log.actor_type == 'seller'
        assert log.description == ''
        assert log.field_name == ''
        assert log.old_value == ''
        assert log.new_value == ''

    def test_returns_persisted_instance(self, proposal):
        log = log_proposal_change(proposal, 'note', description='A note.')
        assert isinstance(log, ProposalChangeLog)
        assert log.pk is not None
        assert ProposalChangeLog.objects.filter(pk=log.pk).exists()

    def test_works_inside_atomic_block(self, proposal):
        with transaction.atomic():
            log = log_proposal_change(
                proposal, 'sent', actor_type='system', description='Sent.',
            )
        assert ProposalChangeLog.objects.filter(pk=log.pk).exists()

    def test_rolls_back_with_enclosing_transaction(self, proposal):
        class Boom(Exception):
            pass

        with pytest.raises(Boom):
            with transaction.atomic():
                log_proposal_change(proposal, 'sent', description='Doomed.')
                raise Boom()
        assert not ProposalChangeLog.objects.filter(
            proposal=proposal, change_type='sent',
        ).exists()
