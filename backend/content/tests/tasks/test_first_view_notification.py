"""Durable first-view email state-machine tests."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from content.models import BusinessProposal

pytestmark = pytest.mark.django_db


def _pending_proposal(**overrides):
    values = {
        'title': 'Tracked proposal',
        'client_name': 'Client',
        'client_email': 'client@example.com',
        'status': BusinessProposal.Status.VIEWED,
        'first_viewed_at': timezone.now(),
        'first_view_notification_status': 'pending',
    }
    values.update(overrides)
    return BusinessProposal.objects.create(**values)


@patch(
    'content.services.proposal_email_service.ProposalEmailService.send_first_view_notification',
    side_effect=RuntimeError('SMTP password rejected\nsecret detail'),
)
def test_failed_delivery_is_observable_and_reraised(mock_send):
    proposal = _pending_proposal()

    from content.tasks import notify_first_view

    with pytest.raises(RuntimeError, match='SMTP password rejected'):
        notify_first_view.call_local(proposal.id)

    proposal.refresh_from_db()
    assert proposal.first_view_notification_status == 'failed'
    assert proposal.first_view_notification_attempts == 1
    assert proposal.first_view_notification_attempted_at is not None
    assert proposal.first_view_notification_last_error == (
        'SMTP password rejected secret detail'
    )


@patch(
    'content.services.proposal_email_service.ProposalEmailService._is_template_active',
    return_value=False,
)
@patch(
    'content.services.proposal_email_service.ProposalEmailService.send_first_view_notification',
)
def test_disabled_template_becomes_skipped(mock_send, mock_active):
    proposal = _pending_proposal()

    from content.tasks import notify_first_view

    notify_first_view.call_local(proposal.id)

    proposal.refresh_from_db()
    assert proposal.first_view_notification_status == 'skipped'
    assert proposal.first_view_notification_last_error == 'Email template disabled.'
    mock_send.assert_not_called()


@patch(
    'content.services.proposal_email_service.ProposalEmailService.send_first_view_notification',
)
def test_legacy_view_never_sends_retroactively(mock_send):
    proposal = _pending_proposal(
        first_view_notification_status='legacy_unverified',
    )

    from content.tasks import notify_first_view

    notify_first_view.call_local(proposal.id)

    mock_send.assert_not_called()


@patch('content.tasks.notify_first_view')
def test_reconciler_requeues_pending_failed_and_stale_claims(mock_notify):
    pending = _pending_proposal()
    failed = _pending_proposal(
        title='Failed',
        first_view_notification_status='failed',
        first_view_notification_attempts=2,
    )
    stale = _pending_proposal(
        title='Stale',
        first_view_notification_status='sending',
        first_view_notification_attempts=1,
        first_view_notification_attempted_at=timezone.now() - timedelta(minutes=11),
    )

    from content.tasks import reconcile_first_view_notifications

    reconcile_first_view_notifications.call_local()

    assert {call.args[0] for call in mock_notify.call_args_list} == {
        pending.id,
        failed.id,
        stale.id,
    }
