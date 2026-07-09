"""
Admin status changes for business proposals.

Any known status can be set from the panel (admin mode). Side effects —
client email on draft→sent, finished-confirmation email, platform
onboarding on accept — fire ONLY when the old→new pair is a *natural*
transition per ``BusinessProposal.ALLOWED_TRANSITIONS``; forced jumps are
data corrections and just save + log. Every change lands in
``ProposalChangeLog``.

Shared by the panel endpoint (``update_proposal_status``) and the MCP tool
of the same name so both surfaces behave identically.
"""

import logging

from content.api_errors import ProposalActionError
from content.models import BusinessProposal, ProposalChangeLog

logger = logging.getLogger(__name__)


def change_status(proposal, new_status, *, source='inline', acting_user_id=None):
    """
    Change ``proposal.status`` to any known status.

    Returns ``(delivery, forced)`` where ``delivery`` is the email delivery
    report when the natural draft→sent path ran (``None`` otherwise) and
    ``forced`` says whether the jump was outside the natural flow.

    Raises :class:`ProposalActionError` on unknown status (``invalid_status``),
    no-op changes (``same_status``), or send failures propagated from
    ``ProposalService.send_proposal``.
    """
    new_status = (new_status or '').strip()
    valid_statuses = {choice[0] for choice in BusinessProposal.Status.choices}
    if new_status not in valid_statuses:
        raise ProposalActionError(
            f'Estado no válido: {new_status}.', code='invalid_status',
        )

    old_status = proposal.status
    if new_status == old_status:
        raise ProposalActionError(
            f'La propuesta ya está en estado «{BusinessProposal.status_label_es(old_status)}».',
            code='same_status',
            hint='Actualiza la página para ver el estado actual de la propuesta.',
        )

    natural = new_status in BusinessProposal.ALLOWED_TRANSITIONS.get(
        old_status, frozenset(),
    )

    if (
        natural
        and old_status == BusinessProposal.Status.DRAFT
        and new_status == BusinessProposal.Status.SENT
    ):
        from content.services.proposal_service import ProposalService

        delivery = ProposalService.send_proposal(proposal)  # may raise
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='sent',
            actor_type='seller',
            description=f'Proposal sent to {proposal.client_email} ({source}).',
        )
        return delivery, False

    proposal.status = new_status
    proposal.save(update_fields=['status'])
    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='status_change',
        field_name='status',
        old_value=old_status,
        new_value=new_status,
        actor_type='seller',
        description=(
            f'Status changed from {old_status} to {new_status} ({source}'
            f'{"" if natural else ", admin forced"}).'
        ),
    )

    if natural and new_status == BusinessProposal.Status.FINISHED:
        # Only reachable naturally from 'accepted'.
        try:
            from content.services.proposal_email_service import ProposalEmailService

            ProposalEmailService.send_finished_confirmation(proposal)
        except Exception:
            logger.exception(
                'Failed to send finished confirmation for proposal %s',
                proposal.id,
            )

    if natural and new_status == BusinessProposal.Status.ACCEPTED:
        # Only reachable naturally from 'negotiating'. Auto-provision the
        # client's platform project (idempotent, async).
        enqueue_onboarding_on_accept(proposal, acting_user_id=acting_user_id)

    return None, (not natural)


def enqueue_onboarding_on_accept(proposal, *, acting_user_id):
    """
    Fire idempotent platform onboarding when a proposal becomes accepted.

    The acceptance email is owned by the calling view (preserving existing
    per-path email behavior), so the onboarding task is told to suppress its
    own acceptance email (``send_email=False``). No-ops when the proposal was
    already onboarded (e.g. launched early during negotiation).
    """
    if proposal.platform_onboarding_completed_at is not None:
        return

    proposal.platform_onboarding_status = BusinessProposal.ONBOARDING_PENDING
    proposal.save(update_fields=['platform_onboarding_status'])
    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type=ProposalChangeLog.ChangeType.PLATFORM_LAUNCH,
        field_name='platform_onboarding_status',
        new_value='pending',
        actor_type='system',
        description='Auto-launch to platform on acceptance.',
    )
    try:
        from content.tasks import run_platform_onboarding

        run_platform_onboarding(
            proposal.id,
            acting_user_id=acting_user_id,
            is_relaunch=False,
            send_email=False,
        )
    except Exception:
        logger.exception(
            'Failed to auto-queue platform onboarding for proposal %s.', proposal.id,
        )
        proposal.platform_onboarding_status = BusinessProposal.ONBOARDING_FAILED
        proposal.save(update_fields=['platform_onboarding_status'])
