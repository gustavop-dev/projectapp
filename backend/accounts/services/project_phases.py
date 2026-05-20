"""Business logic for managing ProjectPhase rows."""
from django.db import transaction
from django.db.models import Max

from accounts.models import ProjectPhase


class PhaseError(Exception):
    """Service-level error with a stable code + optional payload extras."""

    def __init__(self, code: str, http_status: int = 400, extra: dict | None = None):
        self.code = code
        self.http_status = http_status
        self.extra = extra or {}
        super().__init__(code)


def list_phases(project):
    """Returns the project's phases as a QuerySet ordered by ``order``."""
    return project.phases.select_related('business_proposal').order_by('order')


def add_phase(project, proposal, order: int | None = None) -> ProjectPhase:
    """Attach a proposal as a new phase. Appends at end when ``order`` omitted.
    Raises ``PhaseError(code='duplicate_proposal')`` if the proposal is already
    in this project."""
    if project.phases.filter(business_proposal=proposal).exists():
        raise PhaseError('duplicate_proposal')
    if order is None:
        max_order = project.phases.aggregate(m=Max('order'))['m'] or 0
        order = max_order + 1
    return ProjectPhase.objects.create(
        project=project, business_proposal=proposal, order=order,
    )


def remove_phase(project, phase_id: int) -> None:
    """Detach a phase. Renumbers remaining phases to 1..N."""
    try:
        phase = project.phases.get(id=phase_id)
    except ProjectPhase.DoesNotExist:
        raise PhaseError('phase_not_found', http_status=404)
    with transaction.atomic():
        phase.delete()
        for new_order, ph in enumerate(project.phases.order_by('order'), start=1):
            if ph.order != new_order:
                ph.order = new_order
                ph.save(update_fields=['order'])


def reorder_phases(project, items: list[dict]) -> None:
    """Bulk-rewrite phase ordering. ``items`` is a list of ``{id, order}`` pairs
    covering every existing phase of the project. Atomic."""
    given_ids = {item['id'] for item in items}
    existing_ids = set(project.phases.values_list('id', flat=True))
    if given_ids != existing_ids:
        raise PhaseError('invalid_phase_id', extra={
            'expected': sorted(existing_ids), 'received': sorted(given_ids),
        })
    with transaction.atomic():
        for item in items:
            ProjectPhase.objects.filter(id=item['id']).update(order=item['order'])
