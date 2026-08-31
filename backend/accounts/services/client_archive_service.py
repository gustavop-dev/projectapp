"""Archiving a client, and the project cascade it drags behind it.

Archiving is the client-side twin of a project leaving its active states: the
operator puts the whole relationship away. Leaving the client's projects
"active" while the client is filed away is the incoherence this service exists
to close — the projects module, the billing calendar and the hosting notices
all read the PROJECT's state, never the client's, so a client archived on its
own keeps charging and reminding as if nothing happened.

The cascade is preview-first, following ``content.services.project_service``:
the operator sees every project the archive will touch, and what it costs,
before confirming. That is not ceremony. Moving a project to "suspended" runs
``_cancel_future_billing``, which marks future unpaid incomes CANCELLED and
archives future hosting payments — and **nothing reverses it**. Unarchiving the
client later brings the client back; it does not bring those rows back, which
is why :func:`unarchive_client` deliberately leaves the projects suspended
instead of guessing a state that would make the figures lie.

Target state is resolved by ``system_key='suspended'`` and never by walking
operational effects: ``LEGACY_STATUS_BY_EFFECT`` has no entry for the empty
effect, so a user-made state with "Sin efecto automático" would raise KeyError
deep inside ``apply_transition``.
"""
from django.db import transaction
from django.utils import timezone

from accounts.models import Project, UserProfile
from content.models import DocumentState
from content.models.accounting_change_log import AccountingChangeLog
from content.models.document_state import DocumentStateGroup
from content.services import accounting_service
from content.services.project_state_service import (
    apply_transition,
    preview_transition,
)

# The three effects that already mean "not active". A project sitting on any of
# them needs no cascade, and asking for a preview would raise
# ``state_already_active``.
NON_ACTIVE_EFFECTS = (
    DocumentState.OperationalEffect.SUSPENDED,
    DocumentState.OperationalEffect.COMPLETED,
    DocumentState.OperationalEffect.DECOMMISSIONED,
)

SUSPENDED_SYSTEM_KEY = 'suspended'


class ClientArchiveError(Exception):
    """Archive/unarchive refused, with a code the view maps to a status."""

    def __init__(self, message, *, code=''):
        super().__init__(message)
        self.message = message
        self.code = code


def suspended_state():
    """The catalog state the cascade moves projects to."""
    state = DocumentState.objects.filter(
        catalog=DocumentStateGroup.Catalog.PROJECTS,
        system_key=SUSPENDED_SYSTEM_KEY,
        is_active=True,
        merged_into__isnull=True,
    ).first()
    if state is None:
        raise ClientArchiveError(
            'El estado "Suspendido" no está disponible en el catálogo de '
            'proyectos.',
            code='suspended_state_missing',
        )
    return state


def cascade_projects(profile):
    """Projects of ``profile`` that the cascade would move.

    Excludes the ones already parked on a non-active state and the ones with no
    ``current_state`` at all: that gap is the pre-lifecycle legacy data the repo
    treats as fail-closed, and guessing a transition for it here would write a
    history that never happened.
    """
    return list(
        Project.objects.filter(client=profile.user)
        .exclude(current_state__operational_effect__in=NON_ACTIVE_EFFECTS)
        .exclude(current_state__isnull=True)
        .select_related('current_state')
        .order_by('id')
    )


def _skipped_projects(profile):
    """Projects the cascade will NOT touch, with the reason.

    The modal names them instead of leaving the operator to wonder why the
    count of affected projects is smaller than the client's project list.
    """
    skipped = []
    projects = (
        Project.objects.filter(client=profile.user)
        .select_related('current_state')
        .order_by('id')
    )
    for project in projects:
        state = project.current_state
        if state is None:
            skipped.append({
                'project_id': project.pk,
                'project_name': project.name,
                'reason': 'sin_estado',
                'label': 'Sin estado registrado — revísalo a mano.',
            })
        elif state.operational_effect in NON_ACTIVE_EFFECTS:
            skipped.append({
                'project_id': project.pk,
                'project_name': project.name,
                'reason': 'ya_no_activo',
                'label': 'Ya está en "%s".' % state.name,
            })
    return skipped


def archive_client_preview(profile):
    """What archiving ``profile`` would do. Writes nothing.

    Every eligible project carries its OWN ``impact_token``: ``apply_transition``
    validates one token per project, so a single aggregate token would let a
    concurrent change on project B ride in under project A's approval.
    """
    if profile.archived_at is not None:
        raise ClientArchiveError(
            'El cliente ya está archivado.', code='client_already_archived',
        )

    target = suspended_state()
    projects = []
    future_incomes = 0
    future_payments = 0
    active_hostings = 0

    for project in cascade_projects(profile):
        impact = preview_transition(project, target)
        projects.append({
            'project_id': project.pk,
            'project_name': project.name,
            'current_state': (
                project.current_state.name if project.current_state else ''
            ),
            'impact_token': impact['impact_token'],
            'future_incomes': impact['future_incomes'],
            'future_payments': impact['future_payments'],
            'active_hostings': impact['active_hostings'],
            'blockers': impact['blockers'],
        })
        future_incomes += len(impact['future_incomes'])
        future_payments += len(impact['future_payments'])
        active_hostings += len(impact['active_hostings'])

    return {
        'client_id': profile.pk,
        'client_name': profile.user.get_full_name() or profile.user.username,
        'target_state_id': target.pk,
        'target_state_name': target.name,
        'projects': projects,
        'skipped': _skipped_projects(profile),
        'totals': {
            'future_incomes': future_incomes,
            'future_payments': future_payments,
            'active_hostings': active_hostings,
        },
    }


def _log(profile, changes, actor):
    return accounting_service.log_accounting_change(
        entity_type=AccountingChangeLog.EntityType.CLIENT,
        object_id=profile.pk,
        object_repr=profile.user.get_full_name() or profile.user.username,
        action=AccountingChangeLog.Action.UPDATED,
        changes=changes,
        actor=actor,
    )


@transaction.atomic
def archive_client(profile, *, transitions, actor):
    """Archive ``profile`` and suspend its still-active projects.

    ``transitions`` is ``[{'project_id': int, 'impact_token': str}]`` — the
    operator's confirmation of the preview they actually saw. One transaction: a
    client archived while half its projects stayed active would split every
    per-client figure between two realities.
    """
    locked = UserProfile.objects.select_for_update().get(pk=profile.pk)
    if locked.archived_at is not None:
        raise ClientArchiveError(
            'El cliente ya está archivado.', code='client_already_archived',
        )

    target = suspended_state()
    tokens = {}
    for item in transitions:
        tokens[item['project_id']] = item['impact_token']

    eligible = cascade_projects(locked)
    eligible_ids = set()
    for project in eligible:
        eligible_ids.add(project.pk)

    # Staleness by SET, not only by token: a project that became eligible
    # between the preview and the confirm would otherwise be suspended without
    # ever having been shown to the operator.
    if eligible_ids != set(tokens):
        raise ClientArchiveError(
            'La lista de proyectos cambió desde la vista previa. Revísala de '
            'nuevo.',
            code='projects_changed',
        )

    suspended = []
    for project in eligible:
        apply_transition(
            project,
            target,
            actor=actor,
            impact_token=tokens[project.pk],
            note='Cascada por archivado del cliente.',
        )
        suspended.append(project.pk)

    locked.archived_at = timezone.now()
    locked.archived_by = (
        actor if getattr(actor, 'is_authenticated', False) else None
    )
    locked.save(update_fields=['archived_at', 'archived_by', 'updated_at'])

    _log(
        locked,
        [
            {
                'field': 'archived_at',
                'label': 'Archivado',
                'old': '',
                'new': locked.archived_at.isoformat(),
            },
            {
                'field': 'cascaded_projects',
                'label': 'Proyectos suspendidos por la cascada',
                'old': '',
                'new': ', '.join(str(pk) for pk in suspended) or '—',
            },
        ],
        actor,
    )
    return {
        'archived_at': locked.archived_at,
        'suspended_projects': suspended,
    }


@transaction.atomic
def unarchive_client(profile, *, actor):
    """Bring ``profile`` back. Its projects are deliberately left alone.

    The cascade cancelled future incomes and archived future hosting payments on
    the way in, and nothing un-cancels them. Returning the projects to "active"
    here would restore the label without restoring the figures, so reactivating
    each project stays an explicit decision.
    """
    locked = UserProfile.objects.select_for_update().get(pk=profile.pk)
    if locked.archived_at is None:
        raise ClientArchiveError(
            'El cliente no está archivado.', code='client_not_archived',
        )

    was = locked.archived_at.isoformat()
    locked.archived_at = None
    locked.archived_by = None
    locked.save(update_fields=['archived_at', 'archived_by', 'updated_at'])

    _log(
        locked,
        [{
            'field': 'archived_at',
            'label': 'Archivado',
            'old': was,
            'new': '',
        }],
        actor,
    )

    still_suspended = []
    projects = Project.objects.filter(
        client=locked.user,
        current_state__operational_effect__in=NON_ACTIVE_EFFECTS,
    ).order_by('id')
    for project in projects:
        still_suspended.append(project.pk)

    return {'still_suspended': still_suspended}
