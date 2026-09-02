"""Focused regression coverage for durable proposal engagement tracking."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from content.models import (
    BusinessProposal,
    ProposalAlert,
    ProposalChangeLog,
    ProposalSectionView,
    ProposalViewEvent,
)

pytestmark = pytest.mark.django_db


def _track_url(proposal):
    return reverse(
        'track-proposal-engagement',
        kwargs={'proposal_uuid': proposal.uuid},
    )


def _payload(session_id='confirmed-session', **overrides):
    payload = {
        'session_id': session_id,
        'view_mode': 'detailed',
        'sections': [{
            'section_type': 'greeting',
            'section_title': 'Bienvenida',
            'time_spent_seconds': 5,
            'entered_at': '2026-09-02T10:00:00Z',
        }],
    }
    payload.update(overrides)
    return payload


@patch('content.tasks.notify_first_view')
def test_first_valid_heartbeat_creates_durable_commercial_view(
    mock_notify,
    api_client,
    sent_proposal,
):
    response = api_client.post(
        _track_url(sent_proposal),
        _payload(),
        format='json',
    )

    sent_proposal.refresh_from_db()
    assert response.status_code == 200
    assert sent_proposal.view_count == 1
    assert sent_proposal.status == BusinessProposal.Status.VIEWED
    assert sent_proposal.first_viewed_at is not None
    assert sent_proposal.first_view_notification_status == 'pending'
    assert ProposalViewEvent.objects.filter(proposal=sent_proposal).count() == 1
    assert ProposalSectionView.objects.filter(
        view_event__proposal=sent_proposal,
    ).count() == 1
    assert ProposalChangeLog.objects.filter(
        proposal=sent_proposal,
        change_type=ProposalChangeLog.ChangeType.VIEWED,
    ).count() == 1
    assert ProposalAlert.objects.filter(
        proposal=sent_proposal,
        alert_type='first_view',
    ).count() == 1
    mock_notify.assert_called_once_with(sent_proposal.id)


@patch('content.tasks.notify_first_view')
def test_duplicate_heartbeat_reuses_session_without_double_counting(
    mock_notify,
    api_client,
    sent_proposal,
):
    url = _track_url(sent_proposal)
    api_client.post(url, _payload(), format='json')
    api_client.post(
        url,
        _payload(sections=[{
            'section_type': 'greeting',
            'time_spent_seconds': 12,
            'entered_at': '2026-09-02T10:00:00Z',
        }]),
        format='json',
    )

    sent_proposal.refresh_from_db()
    assert sent_proposal.view_count == 1
    assert ProposalViewEvent.objects.filter(proposal=sent_proposal).count() == 1
    assert ProposalSectionView.objects.get().time_spent_seconds == 12
    assert mock_notify.call_count == 1


@pytest.mark.parametrize('invalid_sections', [
    [{'section_type': 'greeting', 'time_spent_seconds': -1}],
    [{'section_type': 'greeting', 'time_spent_seconds': 86_401}],
    [{'section_type': '', 'time_spent_seconds': 5}],
    [{'section_type': 'greeting', 'time_spent_seconds': 5, 'entered_at': 'bad'}],
])
def test_invalid_payload_never_partially_writes(
    invalid_sections,
    api_client,
    sent_proposal,
):
    response = api_client.post(
        _track_url(sent_proposal),
        _payload(sections=invalid_sections),
        format='json',
    )

    sent_proposal.refresh_from_db()
    assert response.status_code == 400
    assert sent_proposal.view_count == 0
    assert sent_proposal.first_viewed_at is None
    assert not ProposalViewEvent.objects.exists()
    assert not ProposalSectionView.objects.exists()


def test_payload_over_section_limit_never_writes(api_client, sent_proposal):
    sections = [
        {'section_type': f'section-{index}', 'time_spent_seconds': 1}
        for index in range(101)
    ]

    response = api_client.post(
        _track_url(sent_proposal),
        _payload(sections=sections),
        format='json',
    )

    assert response.status_code == 400
    assert not ProposalViewEvent.objects.exists()


def test_draft_heartbeat_is_skipped_without_commercial_metrics(
    api_client,
    sent_proposal,
):
    sent_proposal.status = BusinessProposal.Status.DRAFT
    sent_proposal.save(update_fields=['status'])

    response = api_client.post(
        _track_url(sent_proposal),
        _payload(),
        format='json',
    )

    sent_proposal.refresh_from_db()
    assert response.status_code == 200
    assert response.data == {'status': 'skipped'}
    assert sent_proposal.view_count == 0
    assert sent_proposal.first_viewed_at is None
    assert not ProposalViewEvent.objects.exists()


@patch('content.tasks.notify_first_view')
def test_final_heartbeat_marks_session_finalized(
    mock_notify,
    api_client,
    sent_proposal,
):
    response = api_client.post(
        _track_url(sent_proposal),
        _payload(is_final=True),
        format='json',
    )

    event = ProposalViewEvent.objects.get(proposal=sent_proposal)
    assert response.status_code == 200
    assert response.data['is_final'] is True
    assert event.finalized_at is not None


@patch('content.tasks.notify_first_view')
def test_admin_can_retry_only_failed_delivery(
    mock_notify,
    admin_client,
    sent_proposal,
):
    sent_proposal.first_viewed_at = timezone.now()
    sent_proposal.first_view_notification_status = 'failed'
    sent_proposal.first_view_notification_attempts = 4
    sent_proposal.first_view_notification_last_error = 'SMTP unavailable'
    sent_proposal.save(update_fields=[
        'first_viewed_at',
        'first_view_notification_status',
        'first_view_notification_attempts',
        'first_view_notification_last_error',
    ])

    response = admin_client.post(reverse(
        'retry-first-view-notification',
        kwargs={'proposal_id': sent_proposal.id},
    ))

    sent_proposal.refresh_from_db()
    assert response.status_code == 202
    assert sent_proposal.first_view_notification_status == 'pending'
    assert sent_proposal.first_view_notification_attempts == 0
    assert sent_proposal.first_view_notification_last_error == ''
    mock_notify.assert_called_once_with(sent_proposal.id)


def test_retry_rejects_non_failed_delivery(admin_client, sent_proposal):
    response = admin_client.post(reverse(
        'retry-first-view-notification',
        kwargs={'proposal_id': sent_proposal.id},
    ))

    assert response.status_code == 409


def test_public_proposal_never_exposes_notification_delivery_details(
    api_client,
    sent_proposal,
):
    sent_proposal.first_view_notification_status = 'failed'
    sent_proposal.first_view_notification_last_error = 'private SMTP detail'
    sent_proposal.save(update_fields=[
        'first_view_notification_status',
        'first_view_notification_last_error',
    ])

    response = api_client.get(reverse(
        'retrieve-public-proposal',
        kwargs={'proposal_uuid': sent_proposal.uuid},
    ))

    assert response.status_code == 200
    assert 'first_view_notification' not in response.data


def test_admin_analytics_exposes_retryable_delivery_state(
    admin_client,
    sent_proposal,
):
    sent_proposal.first_view_notification_status = 'failed'
    sent_proposal.first_view_notification_attempts = 4
    sent_proposal.first_view_notification_last_error = 'SMTP timeout'
    sent_proposal.save(update_fields=[
        'first_view_notification_status',
        'first_view_notification_attempts',
        'first_view_notification_last_error',
    ])

    response = admin_client.get(reverse(
        'proposal-analytics',
        kwargs={'proposal_id': sent_proposal.id},
    ))

    assert response.status_code == 200
    assert response.data['first_view_notification'] == {
        'status': 'failed',
        'attempts': 4,
        'attempted_at': None,
        'sent_at': None,
        'last_error': 'SMTP timeout',
        'can_retry': True,
    }
