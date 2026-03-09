"""
Huey tasks for the business proposal feature.

Tasks:
  - send_proposal_reminder: Send reminder email N days after proposal was sent.
  - expire_stale_proposals: Daily task to mark expired proposals.
"""

import logging

from django.utils import timezone
from huey import crontab
from huey.contrib.djhuey import periodic_task, task

logger = logging.getLogger(__name__)


@task()
def send_proposal_reminder(proposal_id):
    """
    Huey task: send reminder email N days after proposal was sent.

    Skips if:
    - Proposal not found
    - Status is not SENT or VIEWED
    - No client_email set
    - Reminder already sent (reminder_sent_at is not null)
    """
    from content.models import BusinessProposal
    from content.services.proposal_email_service import ProposalEmailService

    try:
        proposal = BusinessProposal.objects.get(pk=proposal_id)
    except BusinessProposal.DoesNotExist:
        logger.warning('Proposal %s not found for reminder task.', proposal_id)
        return

    if proposal.status not in ('sent', 'viewed'):
        logger.info(
            'Skipping reminder for proposal %s: status is %s',
            proposal.uuid, proposal.status,
        )
        return

    if not proposal.client_email:
        logger.warning(
            'Skipping reminder for proposal %s: no client_email',
            proposal.uuid,
        )
        return

    if proposal.reminder_sent_at is not None:
        logger.info(
            'Skipping reminder for proposal %s: already sent at %s',
            proposal.uuid, proposal.reminder_sent_at,
        )
        return

    ProposalEmailService.send_reminder(proposal)


@task()
def send_urgency_reminder(proposal_id):
    """
    Huey task: send urgency/discount email at day 15 after proposal was sent.

    Skips if:
    - Proposal not found
    - Status is not SENT or VIEWED
    - No client_email set
    - Urgency email already sent (urgency_email_sent_at is not null)
    """
    from content.models import BusinessProposal
    from content.services.proposal_email_service import ProposalEmailService

    try:
        proposal = BusinessProposal.objects.get(pk=proposal_id)
    except BusinessProposal.DoesNotExist:
        logger.warning('Proposal %s not found for urgency task.', proposal_id)
        return

    if proposal.status not in ('sent', 'viewed'):
        logger.info(
            'Skipping urgency for proposal %s: status is %s',
            proposal.uuid, proposal.status,
        )
        return

    if not proposal.client_email:
        logger.warning(
            'Skipping urgency for proposal %s: no client_email',
            proposal.uuid,
        )
        return

    if proposal.urgency_email_sent_at is not None:
        logger.info(
            'Skipping urgency for proposal %s: already sent at %s',
            proposal.uuid, proposal.urgency_email_sent_at,
        )
        return

    ProposalEmailService.send_urgency_email(proposal)


@task()
def send_rejection_reengagement(proposal_id):
    """
    Huey task: send re-engagement email 48h after a budget-related rejection.

    Skips if:
    - Proposal not found
    - Status is not REJECTED
    - No client_email set
    - Re-engagement email already sent (ProposalChangeLog entry exists)
    """
    from content.models import BusinessProposal, ProposalChangeLog
    from content.services.proposal_email_service import ProposalEmailService

    try:
        proposal = BusinessProposal.objects.get(pk=proposal_id)
    except BusinessProposal.DoesNotExist:
        logger.warning(
            'Proposal %s not found for re-engagement task.', proposal_id
        )
        return

    if proposal.status != 'rejected':
        logger.info(
            'Skipping re-engagement for proposal %s: status is %s',
            proposal.uuid, proposal.status,
        )
        return

    if not proposal.client_email:
        logger.warning(
            'Skipping re-engagement for proposal %s: no client_email',
            proposal.uuid,
        )
        return

    already_sent = ProposalChangeLog.objects.filter(
        proposal=proposal,
        change_type='reengagement',
    ).exists()
    if already_sent:
        logger.info(
            'Skipping re-engagement for proposal %s: already sent',
            proposal.uuid,
        )
        return

    success = ProposalEmailService.send_rejection_reengagement(proposal)
    if success:
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='reengagement',
            description='Re-engagement email sent 48h after budget rejection.',
        )


@periodic_task(crontab(hour='8', minute='0'))
def suggest_pre_expiration_discount():
    """
    Daily task: for proposals expiring within 5 days that were viewed but
    not responded and have no discount, create a discount_suggestion alert
    (if one doesn't already exist).
    """
    from datetime import timedelta

    from content.models import BusinessProposal, ProposalAlert

    now = timezone.now()
    candidates = BusinessProposal.objects.filter(
        status='viewed',
        is_active=True,
        discount_percent=0,
        responded_at__isnull=True,
        expires_at__isnull=False,
        expires_at__gt=now,
        expires_at__lte=now + timedelta(days=5),
    )

    created_count = 0
    for proposal in candidates:
        already_exists = ProposalAlert.objects.filter(
            proposal=proposal,
            alert_type='discount_suggestion',
            is_dismissed=False,
        ).exists()
        if not already_exists:
            days_left = (proposal.expires_at - now).days
            ProposalAlert.objects.create(
                proposal=proposal,
                alert_type='discount_suggestion',
                message=(
                    f'Expira en {days_left}d, vista pero sin respuesta. '
                    f'Considera activar descuento o re-enviar con nota personalizada.'
                ),
                alert_date=now,
            )
            created_count += 1

    if created_count > 0:
        logger.info(
            'Created %d pre-expiration discount suggestions.', created_count
        )


@periodic_task(crontab(hour='0', minute='30'))
def expire_stale_proposals():
    """
    Daily task: mark proposals as EXPIRED when expires_at < now().

    Only affects active proposals with status SENT or VIEWED.
    """
    from content.models import BusinessProposal

    now = timezone.now()
    expired_qs = BusinessProposal.objects.filter(
        status__in=['sent', 'viewed'],
        is_active=True,
        expires_at__lt=now,
    )
    count = expired_qs.update(status='expired')

    if count > 0:
        logger.info('Expired %d stale proposals.', count)


@periodic_task(crontab(hour='9', minute='0'))
def escalate_seller_inactivity():
    """
    Daily task: if a proposal has had no seller activity for >=5 days
    (sent/viewed, client has viewed), send an escalation email to the
    sales team. Only sends once per proposal (tracked via ProposalChangeLog).
    """
    from datetime import timedelta

    from content.models import BusinessProposal, ProposalChangeLog
    from content.services.proposal_email_service import ProposalEmailService

    now = timezone.now()
    five_days_ago = now - timedelta(days=5)
    seller_activity_types = {'call', 'meeting', 'followup', 'note'}

    candidates = BusinessProposal.objects.filter(
        status__in=['sent', 'viewed'],
        is_active=True,
        first_viewed_at__isnull=False,
    )

    escalated = 0
    for p in candidates:
        ref_date = p.last_activity_at or p.sent_at
        if not ref_date or ref_date > five_days_ago:
            continue

        has_recent = ProposalChangeLog.objects.filter(
            proposal=p,
            change_type__in=seller_activity_types,
            created_at__gte=five_days_ago,
        ).exists()
        if has_recent:
            continue

        already_escalated = ProposalChangeLog.objects.filter(
            proposal=p,
            change_type='seller_inactivity_escalation',
        ).exists()
        if already_escalated:
            continue

        days = (now - ref_date).days
        try:
            ProposalEmailService.send_seller_inactivity_escalation(p, days)
            ProposalChangeLog.objects.create(
                proposal=p,
                change_type='seller_inactivity_escalation',
                description=f'Seller inactivity escalation sent after {days} days.',
            )
            escalated += 1
        except Exception:
            logger.exception(
                'Failed seller inactivity escalation for proposal %s',
                p.uuid,
            )

    if escalated > 0:
        logger.info('Escalated %d seller-inactive proposals.', escalated)


@periodic_task(crontab(hour='*/2', minute='15'))
def check_engagement_followups():
    """
    Periodic task (every 2 hours): check viewed proposals for
    engagement-based follow-up email triggers.

    1. Abandonment: client viewed but never reached investment section,
       and first view was >4h ago.
    2. Investment interest: client spent >60s on investment section,
       and last view was >2h ago.
    """
    from datetime import timedelta

    from django.db.models import Sum

    from content.models import (
        BusinessProposal, ProposalSectionView, ProposalViewEvent,
    )
    from content.services.proposal_email_service import ProposalEmailService

    now = timezone.now()
    four_hours_ago = now - timedelta(hours=4)
    two_hours_ago = now - timedelta(hours=2)

    # --- Abandonment follow-up ---
    abandonment_candidates = BusinessProposal.objects.filter(
        status='viewed',
        is_active=True,
        client_email__gt='',
        abandonment_email_sent_at__isnull=True,
        first_viewed_at__isnull=False,
        first_viewed_at__lt=four_hours_ago,
    )

    for proposal in abandonment_candidates:
        visited_types = set(
            ProposalSectionView.objects
            .filter(view_event__proposal=proposal)
            .values_list('section_type', flat=True)
            .distinct()
        )
        if 'investment' not in visited_types:
            try:
                ProposalEmailService.send_abandonment_followup(proposal)
                logger.info(
                    'Sent abandonment followup for proposal %s',
                    proposal.uuid,
                )
            except Exception:
                logger.exception(
                    'Failed abandonment followup for proposal %s',
                    proposal.uuid,
                )

    # --- Investment interest follow-up ---
    interest_candidates = BusinessProposal.objects.filter(
        status='viewed',
        is_active=True,
        client_email__gt='',
        investment_interest_email_sent_at__isnull=True,
        first_viewed_at__isnull=False,
    )

    for proposal in interest_candidates:
        last_event = (
            ProposalViewEvent.objects
            .filter(proposal=proposal)
            .order_by('-viewed_at')
            .first()
        )
        if not last_event or last_event.viewed_at > two_hours_ago:
            continue

        investment_time = (
            ProposalSectionView.objects
            .filter(
                view_event__proposal=proposal,
                section_type='investment',
            )
            .aggregate(total=Sum('time_spent_seconds'))
        )['total'] or 0

        if investment_time >= 60:
            try:
                ProposalEmailService.send_investment_interest_followup(
                    proposal, investment_time,
                )
                logger.info(
                    'Sent investment interest followup for proposal %s '
                    '(time=%ds)',
                    proposal.uuid, investment_time,
                )
            except Exception:
                logger.exception(
                    'Failed investment interest followup for proposal %s',
                    proposal.uuid,
                )


@task()
def send_scheduled_followup(proposal_id):
    """
    Huey task: send a scheduled follow-up email for a previously
    rejected proposal (client asked to be reminded later).

    Skips if:
    - Proposal not found
    - No client_email set
    - No followup_scheduled_at set
    """
    from content.models import BusinessProposal
    from content.services.proposal_email_service import ProposalEmailService

    try:
        proposal = BusinessProposal.objects.get(pk=proposal_id)
    except BusinessProposal.DoesNotExist:
        logger.warning(
            'Proposal %s not found for scheduled followup task.',
            proposal_id,
        )
        return

    if not proposal.client_email:
        logger.warning(
            'Skipping scheduled followup for proposal %s: no client_email',
            proposal.uuid,
        )
        return

    if not proposal.followup_scheduled_at:
        logger.info(
            'Skipping scheduled followup for proposal %s: no scheduled date',
            proposal.uuid,
        )
        return

    ProposalEmailService.send_scheduled_followup(proposal)


@periodic_task(crontab(minute='*/15'))
def publish_scheduled_blog_posts():
    """
    Periodic task (every 15 minutes): publish blog posts whose
    published_at datetime has passed but are still marked as drafts.

    This enables scheduled/future publishing from the admin panel.
    """
    from content.models import BlogPost

    now = timezone.now()
    scheduled_qs = BlogPost.objects.filter(
        is_published=False,
        published_at__isnull=False,
        published_at__lte=now,
    )
    count = scheduled_qs.update(is_published=True)

    if count > 0:
        logger.info('Published %d scheduled blog post(s).', count)


@task()
def notify_first_view(proposal_id):
    """
    Huey task: send real-time notification to the sales team when a
    client opens a proposal for the first time.

    Called asynchronously from retrieve_public_proposal so the client's
    page load is not blocked by email delivery.
    """
    from content.models import BusinessProposal
    from content.services.proposal_email_service import ProposalEmailService

    try:
        proposal = BusinessProposal.objects.get(pk=proposal_id)
    except BusinessProposal.DoesNotExist:
        logger.warning(
            'Proposal %s not found for first-view notification task.',
            proposal_id,
        )
        return

    ProposalEmailService.send_first_view_notification(proposal)
