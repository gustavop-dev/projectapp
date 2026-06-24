"""Shared helpers for seed/demo management commands.

The leading underscore keeps Django's command loader from treating this as a
runnable management command.
"""

from accounts.models import ProjectPhase


def ensure_phase(project):
    """Return a ProjectPhase for the project, creating one if needed.

    Requirements / change-requests / bug-reports hang off a ProjectPhase (the
    model moved away from the legacy ``deliverable`` FK). A phase needs a
    BusinessProposal: reuse one tied to the project's client, else any existing
    proposal, else create a minimal placeholder so the FK is satisfiable.
    """
    phase = ProjectPhase.objects.filter(project=project).order_by('order').first()
    if phase:
        return phase

    from content.models import BusinessProposal

    client = project.client
    proposal = None
    if client is not None:
        proposal = (
            BusinessProposal.objects.filter(client_email__iexact=client.email)
            .order_by('id').first()
        )
    proposal = proposal or BusinessProposal.objects.order_by('id').first()
    if proposal is None:
        proposal = BusinessProposal.objects.create(
            title=f'Proyecto {project.name}',
            client_name=getattr(client, 'get_full_name', lambda: '')() or project.name,
            client_email=getattr(client, 'email', '') or '',
        )
    return ProjectPhase.objects.create(project=project, business_proposal=proposal, order=0)
