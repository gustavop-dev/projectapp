"""Single entry point for proposal audit-log writes.

Views and services should log proposal lifecycle events through
:func:`log_proposal_change` instead of calling
``ProposalChangeLog.objects.create`` directly, so the audit-trail write
path stays consistent and easy to evolve (e.g. adding validation or
side-channel notifications later touches one place only).
"""

from content.models import ProposalChangeLog


def log_proposal_change(
    proposal,
    change_type,
    *,
    actor_type='seller',
    description='',
    field_name='',
    old_value='',
    new_value='',
) -> ProposalChangeLog:
    """Single entry point for proposal audit-log writes.

    Args:
        proposal: BusinessProposal the event belongs to.
        change_type: One of ``ProposalChangeLog.ChangeType`` values.
        actor_type: One of ``ProposalChangeLog.ActorType`` values
            (defaults to ``'seller'``, the dominant caller).
        description: Human-readable event description.
        field_name: Optional field the change refers to.
        old_value: Optional previous value (stringified).
        new_value: Optional new value (stringified).

    Returns:
        The created ProposalChangeLog instance.
    """
    return ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type=change_type,
        actor_type=actor_type,
        description=description,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
    )
