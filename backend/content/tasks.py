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


@periodic_task(crontab(hour='8', minute='0'))
def send_urgency_emails():
    """
    Daily task: send urgency email with 20% discount offer
    to proposals expiring within 2 days.

    Only affects proposals with status SENT or VIEWED,
    that have not already received the urgency email.
    """
    from content.models import BusinessProposal
    from content.services.proposal_email_service import ProposalEmailService

    now = timezone.now()
    two_days_later = now + timezone.timedelta(days=2)

    proposals = BusinessProposal.objects.filter(
        status__in=['sent', 'viewed'],
        expires_at__lte=two_days_later,
        expires_at__gt=now,
        urgency_email_sent_at__isnull=True,
    ).exclude(client_email='')

    count = 0
    for proposal in proposals:
        if ProposalEmailService.send_urgency_email(proposal):
            count += 1

    if count > 0:
        logger.info('Sent %d urgency emails.', count)


@periodic_task(crontab(hour='0', minute='30'))
def expire_stale_proposals():
    """
    Daily task: mark proposals as EXPIRED when expires_at < now().

    Only affects proposals with status SENT or VIEWED.
    """
    from content.models import BusinessProposal

    now = timezone.now()
    expired_qs = BusinessProposal.objects.filter(
        status__in=['sent', 'viewed'],
        expires_at__lt=now,
    )
    count = expired_qs.update(status='expired')

    if count > 0:
        logger.info('Expired %d stale proposals.', count)
