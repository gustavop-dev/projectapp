"""Tests for open-notification suppression.

"Client opened the proposal" notifications must be skipped when the proposal
is already closed (accepted/finished), so revisiting an old won proposal does
not spam the sales team.
"""
from unittest.mock import patch

import pytest

from content.models import BusinessProposal
from content.services.proposal_service import ProposalService

pytestmark = pytest.mark.django_db


def _make_proposal(status):
    return BusinessProposal.objects.create(
        title='P', client_name='C', status=status,
    )


@pytest.mark.parametrize('status,expected', [
    ('accepted', True),
    ('finished', True),
    ('sent', False),
    ('viewed', False),
    ('negotiating', False),
    ('expired', False),
])
def test_open_notifications_suppressed_by_status(status, expected):
    proposal = _make_proposal(status)
    assert ProposalService.open_notifications_suppressed(proposal) is expected


def test_notify_first_view_task_skips_closed_proposal():
    proposal = _make_proposal('accepted')
    with patch(
        'content.services.proposal_email_service.ProposalEmailService'
        '.send_first_view_notification'
    ) as mock_send:
        from content.tasks import notify_first_view
        notify_first_view.call_local(proposal.id)
    mock_send.assert_not_called()


def test_notify_first_view_task_runs_for_open_proposal():
    proposal = _make_proposal('viewed')
    with patch(
        'content.services.proposal_email_service.ProposalEmailService'
        '.send_first_view_notification'
    ) as mock_send:
        from content.tasks import notify_first_view
        notify_first_view.call_local(proposal.id)
    mock_send.assert_called_once()


def test_send_first_view_notification_returns_false_for_closed():
    from content.services.proposal_email_service import ProposalEmailService
    proposal = _make_proposal('finished')
    # Should bail out on status before even checking the template.
    assert ProposalEmailService.send_first_view_notification(proposal) is False
