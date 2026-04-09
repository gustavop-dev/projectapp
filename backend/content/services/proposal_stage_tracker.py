"""
ProposalStageTracker — daily logic for project-stage email notifications.

For each `ProposalProjectStage` row, decide whether to:
1. Send a 70%-elapsed pre-deadline warning (once)
2. Send an overdue alert (first day past end_date, then every 3 days)

This service is invoked by the daily Huey periodic task
`notify_proposal_stage_deadlines` in `content/tasks.py`.

Design decisions
----------------
- Day-level arithmetic in Bogotá timezone (UTC-5, no DST). Reuses
  `_BOGOTA_TZ` from `content.utils`.
- Edge cases (missing dates, start>end, future start, zero-day stage)
  are guarded by silent skips (or one warning log for data errors).
- Editing `start_date` / `end_date` after a warning was sent re-fires the
  warning **only if** the new dates put the elapsed percentage back below
  the 70% threshold. This is handled by `maybe_reset_warning_on_date_change`,
  called from the `update_project_stage` view. Shortening the stage does
  nothing (elapsed% stays high); extending it clears `warning_sent_at` so
  the daily task can fire again once the new 70% mark is crossed.
- Per-stage dedup is handled by the `warning_sent_at` and
  `last_overdue_reminder_at` timestamp fields on `ProposalProjectStage`.
"""

import logging

from django.utils import timezone

from content.utils import to_bogota_date, today_bogota

logger = logging.getLogger(__name__)


class ProposalStageTracker:
    """Day-by-day decision logic for project-stage email notifications."""

    WARNING_THRESHOLD_PCT = 70
    OVERDUE_REMINDER_INTERVAL_DAYS = 3
    MIN_DURATION_DAYS_FOR_WARNING = 2  # skip 70% warning on 0-1 day stages

    # Single source of truth for the stage catalog. Tuples of (stage_key, order).
    # Used by ensure_stages, get_or_create_stage, and the periodic task.
    STAGE_DEFINITIONS = (
        ('design', 0),
        ('development', 1),
    )

    @classmethod
    def ensure_stages(cls, proposal):
        """
        Idempotently create empty `ProposalProjectStage` rows (one per
        entry in `STAGE_DEFINITIONS`) for the given proposal. Used by the
        platform onboarding flow when a proposal becomes accepted.
        """
        from content.models import ProposalProjectStage
        for stage_key, order in cls.STAGE_DEFINITIONS:
            ProposalProjectStage.objects.get_or_create(
                proposal=proposal,
                stage_key=stage_key,
                defaults={'order': order},
            )

    @classmethod
    def get_or_create_stage(cls, proposal, stage_key):
        """
        Fetch the stage row for `proposal` + `stage_key`, lazily creating
        it (with the canonical order) if it doesn't exist yet.
        """
        from content.models import ProposalProjectStage
        order_map = dict(cls.STAGE_DEFINITIONS)
        stage, _ = ProposalProjectStage.objects.get_or_create(
            proposal=proposal,
            stage_key=stage_key,
            defaults={'order': order_map.get(stage_key, 0)},
        )
        return stage

    @classmethod
    def maybe_reset_warning_on_date_change(cls, stage):
        """
        Reset ``warning_sent_at`` to ``None`` when the current stage dates
        put the elapsed percentage back below ``WARNING_THRESHOLD_PCT``.

        Called by ``update_project_stage`` after the admin saves new dates.
        If an admin extends ``end_date`` (or pushes ``start_date`` forward)
        far enough that elapsed% drops under 70%, the next run of the daily
        periodic task will be allowed to re-fire the 70% warning when the
        new threshold is crossed again.

        Returns True when the timestamp was reset, False otherwise.
        """
        if stage.warning_sent_at is None:
            return False
        if stage.completed_at is not None:
            return False
        if stage.start_date is None or stage.end_date is None:
            return False
        if stage.start_date > stage.end_date:
            return False

        total_days = (stage.end_date - stage.start_date).days
        if total_days < cls.MIN_DURATION_DAYS_FOR_WARNING:
            return False

        elapsed_pct = cls._compute_elapsed_pct(stage, today_bogota(), total_days)
        if elapsed_pct < cls.WARNING_THRESHOLD_PCT:
            stage.warning_sent_at = None
            stage.save(update_fields=['warning_sent_at', 'updated_at'])
            return True

        return False

    @classmethod
    def _compute_elapsed_pct(cls, stage, today, total_days):
        """
        Elapsed percentage from ``start_date`` to ``today`` vs. total duration.

        Caller must have validated dates and ensured ``total_days`` is ≥
        ``MIN_DURATION_DAYS_FOR_WARNING`` (avoids ZeroDivisionError).
        """
        elapsed_days = max(0, (today - stage.start_date).days)
        return (elapsed_days / total_days) * 100

    # ------------------------------------------------------------------
    # Public formatting helper — used by both this tracker AND the email
    # templates / view layer for consistent "1 semana 5 días" output.
    # ------------------------------------------------------------------

    @classmethod
    def format_remaining_time(cls, days: int) -> str:
        """
        Format a number of days as 'X semanas Y días' / 'X días' / 'hoy'.

        Examples:
            0  -> 'hoy'
            1  -> '1 día'
            2  -> '2 días'
            6  -> '6 días'
            7  -> '1 semana'
            8  -> '1 semana 1 día'
            12 -> '1 semana 5 días'
            14 -> '2 semanas'
            15 -> '2 semanas 1 día'
            21 -> '3 semanas'

        Negative values are formatted as their absolute value (the caller
        is responsible for adding "hace" / "faltan" prefixes in templates).
        """
        days = abs(int(days))
        if days == 0:
            return 'hoy'
        if days < 7:
            return '1 día' if days == 1 else f'{days} días'

        weeks, remaining = divmod(days, 7)
        weeks_label = '1 semana' if weeks == 1 else f'{weeks} semanas'
        if remaining == 0:
            return weeks_label
        days_label = '1 día' if remaining == 1 else f'{remaining} días'
        return f'{weeks_label} {days_label}'

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    @classmethod
    def process(cls, proposal):
        """
        Iterate `proposal.project_stages` and run decision logic per stage.

        Stages are evaluated independently — failure on one does not
        affect the others. Caller (the Huey task) handles the per-proposal
        try/except.
        """
        for stage in proposal.project_stages.all():
            try:
                cls._process_stage(proposal, stage)
            except Exception:
                logger.exception(
                    'Stage tracker failed for proposal=%s stage=%s',
                    proposal.uuid, stage.stage_key,
                )

    @classmethod
    def _process_stage(cls, proposal, stage):
        """
        Decide what (if anything) to send for a single stage.

        Returns the action taken as a string, mostly for testing visibility:
            'skip:completed', 'skip:no_dates', 'skip:invalid_range',
            'skip:not_started', 'skip:before_threshold', 'skip:warning_sent',
            'skip:overdue_recent', 'sent:warning', 'sent:overdue'
        """
        # ---- Guards ------------------------------------------------------
        if stage.completed_at is not None:
            return 'skip:completed'

        if stage.start_date is None or stage.end_date is None:
            return 'skip:no_dates'

        if stage.start_date > stage.end_date:
            logger.warning(
                'ProposalProjectStage %s has start_date > end_date '
                '(start=%s end=%s) — skipping',
                stage.pk, stage.start_date, stage.end_date,
            )
            return 'skip:invalid_range'

        today = today_bogota()

        if today < stage.start_date:
            return 'skip:not_started'

        # ---- Branch A: overdue ------------------------------------------
        if today > stage.end_date:
            return cls._handle_overdue(proposal, stage, today)

        # ---- Branch B: 70% warning --------------------------------------
        return cls._handle_warning(proposal, stage, today)

    # ------------------------------------------------------------------
    # Branches
    # ------------------------------------------------------------------

    @classmethod
    def _handle_overdue(cls, proposal, stage, today):
        """First overdue alert + reminders every 3 days."""
        last_at = stage.last_overdue_reminder_at
        if last_at is not None:
            days_since_last = (today - to_bogota_date(last_at)).days
            if days_since_last < cls.OVERDUE_REMINDER_INTERVAL_DAYS:
                return 'skip:overdue_recent'

        days_overdue = (today - stage.end_date).days

        # Lazy import to avoid circular dependency.
        from content.services.proposal_email_service import ProposalEmailService

        ProposalEmailService.send_stage_overdue(proposal, stage, days_overdue)

        stage.last_overdue_reminder_at = timezone.now()
        stage.save(update_fields=['last_overdue_reminder_at', 'updated_at'])

        from content.models import ProposalChangeLog
        cls._log_change(
            proposal,
            change_type=ProposalChangeLog.ChangeType.STAGE_OVERDUE_SENT,
            description=(
                f'Stage "{stage.get_stage_key_display()}" overdue alert sent '
                f'({days_overdue} day(s) past end_date {stage.end_date}).'
            ),
        )
        return 'sent:overdue'

    @classmethod
    def _handle_warning(cls, proposal, stage, today):
        """70%-elapsed pre-deadline warning, sent at most once."""
        if stage.warning_sent_at is not None:
            return 'skip:warning_sent'

        total_days = (stage.end_date - stage.start_date).days
        if total_days < cls.MIN_DURATION_DAYS_FOR_WARNING:
            return 'skip:before_threshold'

        elapsed_pct = cls._compute_elapsed_pct(stage, today, total_days)
        if elapsed_pct < cls.WARNING_THRESHOLD_PCT:
            return 'skip:before_threshold'

        days_remaining = (stage.end_date - today).days

        from content.services.proposal_email_service import ProposalEmailService

        ProposalEmailService.send_stage_warning(proposal, stage, days_remaining)

        stage.warning_sent_at = timezone.now()
        stage.save(update_fields=['warning_sent_at', 'updated_at'])

        from content.models import ProposalChangeLog
        cls._log_change(
            proposal,
            change_type=ProposalChangeLog.ChangeType.STAGE_WARNING_SENT,
            description=(
                f'Stage "{stage.get_stage_key_display()}" 70% warning sent '
                f'({days_remaining} day(s) until end_date {stage.end_date}).'
            ),
        )
        return 'sent:warning'

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _log_change(cls, proposal, *, change_type, description):
        """Create a system-actor ProposalChangeLog entry."""
        from content.models import ProposalChangeLog
        try:
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type=change_type,
                actor_type=ProposalChangeLog.ActorType.SYSTEM,
                description=description,
            )
        except Exception:
            logger.exception(
                'Failed to create ProposalChangeLog for proposal=%s type=%s',
                proposal.uuid, change_type,
            )
