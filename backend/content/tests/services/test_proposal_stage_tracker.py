"""Tests for ProposalStageTracker — format helper + decision logic."""
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from content.models import ProposalChangeLog, ProposalProjectStage
from content.services.proposal_stage_tracker import ProposalStageTracker

pytestmark = pytest.mark.django_db


# ──────────────────────────────────────────────────────────────────────
# format_remaining_time — pure unit tests
# ──────────────────────────────────────────────────────────────────────

class TestFormatRemainingTime:
    def test_zero_days_returns_hoy(self):
        assert ProposalStageTracker.format_remaining_time(0) == 'hoy'

    def test_one_day_returns_singular(self):
        assert ProposalStageTracker.format_remaining_time(1) == '1 día'

    def test_two_days_returns_plural(self):
        assert ProposalStageTracker.format_remaining_time(2) == '2 días'

    def test_six_days_returns_six_dias(self):
        assert ProposalStageTracker.format_remaining_time(6) == '6 días'

    def test_seven_days_returns_one_week(self):
        assert ProposalStageTracker.format_remaining_time(7) == '1 semana'

    def test_eight_days_returns_one_week_one_day(self):
        assert ProposalStageTracker.format_remaining_time(8) == '1 semana 1 día'

    def test_twelve_days_returns_one_week_five_days(self):
        assert ProposalStageTracker.format_remaining_time(12) == '1 semana 5 días'

    def test_fourteen_days_returns_two_weeks(self):
        assert ProposalStageTracker.format_remaining_time(14) == '2 semanas'

    def test_fifteen_days_returns_two_weeks_one_day(self):
        assert ProposalStageTracker.format_remaining_time(15) == '2 semanas 1 día'

    def test_twentyone_days_returns_three_weeks(self):
        assert ProposalStageTracker.format_remaining_time(21) == '3 semanas'

    def test_negative_value_treated_as_absolute(self):
        assert ProposalStageTracker.format_remaining_time(-12) == '1 semana 5 días'


# ──────────────────────────────────────────────────────────────────────
# _process_stage — decision tree
#
# All tests freeze time at 2026-04-09 12:00 UTC = 2026-04-09 07:00 Bogotá
# (still on the same calendar day in Bogotá), so `today` = date(2026,4,9).
# ──────────────────────────────────────────────────────────────────────

FROZEN = '2026-04-09 12:00:00'


def _make_stage(proposal, **kwargs):
    return ProposalProjectStage.objects.create(
        proposal=proposal,
        stage_key=kwargs.pop('stage_key', 'design'),
        order=kwargs.pop('order', 0),
        **kwargs,
    )


@freeze_time(FROZEN)
class TestProcessStageGuards:
    def test_skips_when_completed(self, accepted_proposal):
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 10),
            completed_at=timezone.now(),
        )
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_stage_warning',
        ) as mock_send:
            result = ProposalStageTracker._process_stage(accepted_proposal, stage)
        assert result == 'skip:completed'
        mock_send.assert_not_called()

    def test_skips_when_dates_missing(self, accepted_proposal):
        stage = _make_stage(accepted_proposal)
        result = ProposalStageTracker._process_stage(accepted_proposal, stage)
        assert result == 'skip:no_dates'

    def test_skips_when_start_after_end(self, accepted_proposal):
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 4, 20),
            end_date=date(2026, 4, 10),
        )
        result = ProposalStageTracker._process_stage(accepted_proposal, stage)
        assert result == 'skip:invalid_range'

    def test_skips_when_start_in_future(self, accepted_proposal):
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 4, 15),
            end_date=date(2026, 4, 30),
        )
        result = ProposalStageTracker._process_stage(accepted_proposal, stage)
        assert result == 'skip:not_started'


@freeze_time(FROZEN)
class TestProcessStageWarning:
    def test_skips_warning_when_total_under_two_days(self, accepted_proposal):
        # 1-day stage — under MIN_DURATION_DAYS_FOR_WARNING
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 4, 9),
            end_date=date(2026, 4, 9),  # zero duration
        )
        result = ProposalStageTracker._process_stage(accepted_proposal, stage)
        assert result == 'skip:before_threshold'

    def test_skips_when_below_70_percent(self, accepted_proposal):
        # start=Apr 1, end=Apr 21, today=Apr 9 → 8/20 = 40% elapsed
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 21),
        )
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_stage_warning',
        ) as mock_send:
            result = ProposalStageTracker._process_stage(accepted_proposal, stage)
        assert result == 'skip:before_threshold'
        mock_send.assert_not_called()

    def test_sends_warning_when_70_percent_elapsed(self, accepted_proposal):
        # start=Apr 1, end=Apr 11, today=Apr 9 → 8/10 = 80% elapsed
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 11),
        )
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_stage_warning',
        ) as mock_send:
            result = ProposalStageTracker._process_stage(accepted_proposal, stage)

        assert result == 'sent:warning'
        mock_send.assert_called_once()
        args, _ = mock_send.call_args
        assert args[0] == accepted_proposal
        assert args[1] == stage
        assert args[2] == 2  # 2 days remaining (Apr 11 - Apr 9)

    def test_does_not_resend_warning_when_already_sent(self, accepted_proposal):
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 11),
            warning_sent_at=timezone.now() - timedelta(days=1),
        )
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_stage_warning',
        ) as mock_send:
            result = ProposalStageTracker._process_stage(accepted_proposal, stage)
        assert result == 'skip:warning_sent'
        mock_send.assert_not_called()

    def test_warning_updates_warning_sent_at_timestamp(self, accepted_proposal):
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 11),
        )
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_stage_warning',
            return_value=True,
        ):
            ProposalStageTracker._process_stage(accepted_proposal, stage)
        stage.refresh_from_db()
        assert stage.warning_sent_at is not None

    def test_warning_creates_changelog_entry(self, accepted_proposal):
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 11),
        )
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_stage_warning',
            return_value=True,
        ):
            ProposalStageTracker._process_stage(accepted_proposal, stage)
        log = ProposalChangeLog.objects.get(
            proposal=accepted_proposal,
            change_type='stage_warning_sent',
        )
        assert log.actor_type == 'system'


@freeze_time(FROZEN)
class TestProcessStageOverdue:
    def test_sends_overdue_alert_on_first_day_past_end(self, accepted_proposal):
        # end_date = yesterday → 1 day overdue, no prior reminder
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 3, 20),
            end_date=date(2026, 4, 8),
        )
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_stage_overdue',
        ) as mock_send:
            result = ProposalStageTracker._process_stage(accepted_proposal, stage)

        assert result == 'sent:overdue'
        mock_send.assert_called_once()
        _, _, days_overdue = mock_send.call_args.args
        assert days_overdue == 1

    def test_does_not_resend_overdue_within_3_days(self, accepted_proposal):
        # last reminder yesterday → only 1 day ago, must skip
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 3, 20),
            end_date=date(2026, 4, 5),
            last_overdue_reminder_at=timezone.now() - timedelta(days=1),
        )
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_stage_overdue',
        ) as mock_send:
            result = ProposalStageTracker._process_stage(accepted_proposal, stage)
        assert result == 'skip:overdue_recent'
        mock_send.assert_not_called()

    def test_resends_overdue_after_3_days(self, accepted_proposal):
        # last reminder 4 days ago → must send
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 3, 20),
            end_date=date(2026, 4, 1),
            last_overdue_reminder_at=timezone.now() - timedelta(days=4),
        )
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_stage_overdue',
        ) as mock_send:
            result = ProposalStageTracker._process_stage(accepted_proposal, stage)
        assert result == 'sent:overdue'
        mock_send.assert_called_once()

    def test_overdue_updates_last_overdue_reminder_at(self, accepted_proposal):
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 3, 20),
            end_date=date(2026, 4, 1),
        )
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_stage_overdue',
            return_value=True,
        ):
            ProposalStageTracker._process_stage(accepted_proposal, stage)
        stage.refresh_from_db()
        assert stage.last_overdue_reminder_at is not None

    def test_overdue_creates_changelog_entry(self, accepted_proposal):
        stage = _make_stage(
            accepted_proposal,
            start_date=date(2026, 3, 20),
            end_date=date(2026, 4, 1),
        )
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_stage_overdue',
            return_value=True,
        ):
            ProposalStageTracker._process_stage(accepted_proposal, stage)
        log = ProposalChangeLog.objects.get(
            proposal=accepted_proposal,
            change_type='stage_overdue_sent',
        )
        assert log.actor_type == 'system'
