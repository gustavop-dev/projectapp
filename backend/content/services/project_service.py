"""Cross-module operations on a project's client relationship.

``accounts.Project`` owns the client (a User) while hostings, incomes and
documents point at the project AND at the client (a UserProfile)
independently. This service is the only writer allowed to move a project
between clients: the impact is computed first (preview), the apply runs in
one transaction with one audit row per touched record, and issued documents
are never rewritten — an emitted cuenta is a fact, not a pointer.

Modes (the operator chooses every time; there is no default):
- ``move``: the linked records follow the project to the new client. Incomes
  with an active (non-cancelled) cuenta de cobro never change client — they
  detach from the project instead and stay with the old one; the path for a
  wrongly-billed cuenta is anular y reemitir, not rewriting history.
- ``detach``: the records keep their client and lose the project.
"""
import logging

from content.models import AccountingChangeLog, Document, HostingRecord, IncomeRecord
from content.serializers.accounting import month_label
from content.services import accounting_service
from content.services.collection_account_create_service import (
    customer_snapshot_defaults,
)
from content.services.document_type_codes import COLLECTION_ACCOUNT
from django.db import transaction

logger = logging.getLogger(__name__)

EntityType = AccountingChangeLog.EntityType
Action = AccountingChangeLog.Action

MODE_MOVE = 'move'
MODE_DETACH = 'detach'
MODES = (MODE_MOVE, MODE_DETACH)


def _profile_payload(profile):
    from accounts.services.proposal_client_service import (
        build_client_display_name,
    )

    if profile is None:
        return None
    return {'profile_id': profile.pk, 'name': build_client_display_name(profile)}


def _income_label(income):
    return {
        'id': income.pk,
        'label': income.concept,
        'kind_label': income.get_kind_display(),
        'period_label': month_label(income.period_date),
    }


def _collection_documents_qs(project):
    return Document.objects.filter(
        project=project, document_type__code=COLLECTION_ACCOUNT,
    )


def linked_sets(project):
    """Everything pointing at the project, grouped by how the cascade treats it.

    ``blocked_income_pks``: incomes with a non-cancelled cuenta — their client
    is frozen by the emitted (or in-flight) document. ``draft_following`` are
    drafts with no income behind them (hosting-origin/standalone): they ride
    with the project. Income-backed drafts always belong to a blocked income
    (an active draft blocks it by definition), so they detach with it.
    """
    hostings = list(
        HostingRecord.objects.filter(project=project)
        .select_related('client__user'),
    )
    incomes = list(
        IncomeRecord.objects.filter(project=project)
        .select_related('client__user'),
    )
    blocked_income_pks = set(
        IncomeRecord.objects.filter(project=project)
        .filter(collection_documents__isnull=False)
        .exclude(
            collection_documents__commercial_status=(
                Document.CommercialStatus.CANCELLED
            ),
        )
        .values_list('pk', flat=True),
    )
    cuentas = _collection_documents_qs(project)
    drafts = list(
        cuentas.filter(commercial_status=Document.CommercialStatus.DRAFT)
        .select_related('collection_account'),
    )
    return {
        'hostings': hostings,
        'incomes': incomes,
        'blocked_income_pks': blocked_income_pks,
        'draft_following': [d for d in drafts if d.income_record_id is None],
        'draft_detaching': [d for d in drafts if d.income_record_id is not None],
        'issued_accounts': list(
            cuentas.filter(commercial_status__in=(
                Document.CommercialStatus.ISSUED,
                Document.CommercialStatus.PAID,
            )),
        ),
        # Contracts and other non-cuenta documents document the project and
        # travel with it implicitly; they are reported, never rewritten.
        'other_documents_count': (
            Document.objects.filter(project=project)
            .exclude(document_type__code=COLLECTION_ACCOUNT)
            .count()
        ),
    }


def change_client_preview(project, new_profile):
    """The full impact of moving ``project`` to ``new_profile``, labelled.

    This is the list the operator confirms against; the apply endpoint gets
    the hosting/income ids back as a staleness token, so the plan that runs
    is exactly the plan that was shown.
    """
    sets = linked_sets(project)
    blocked = sets['blocked_income_pks']
    current_profile = getattr(project.client, 'profile', None)

    def cuenta_row(document):
        return {
            'id': document.pk,
            'title': document.title,
            'public_number': document.public_number or '',
            'status_label': document.get_commercial_status_display(),
        }

    hostings_move = [
        {'id': record.pk, 'label': record.display_label}
        for record in sets['hostings'] if record.client_id is not None
    ]
    incomes_move = [
        _income_label(record) for record in sets['incomes']
        if record.client_id is not None and record.pk not in blocked
    ]
    incomes_blocked = [
        {
            **_income_label(record),
            'reason': 'Tiene una cuenta de cobro activa: se desvincula del '
                      'proyecto y conserva su cliente.',
        }
        for record in sets['incomes'] if record.pk in blocked
    ]
    clientless = (
        [
            {'id': record.pk, 'entity': 'hosting', 'label': record.display_label}
            for record in sets['hostings'] if record.client_id is None
        ]
        + [
            {'id': record.pk, 'entity': 'income', 'label': record.concept}
            for record in sets['incomes'] if record.client_id is None
        ]
    )
    return {
        'project': {'id': project.pk, 'name': project.name},
        'current_client': _profile_payload(current_profile),
        'new_client': _profile_payload(new_profile),
        'hostings_move': hostings_move,
        'incomes_move': incomes_move,
        'incomes_blocked': incomes_blocked,
        'clientless': clientless,
        'draft_accounts': [
            cuenta_row(d)
            for d in sets['draft_following'] + sets['draft_detaching']
        ],
        'issued_accounts': [cuenta_row(d) for d in sets['issued_accounts']],
        'other_documents_count': sets['other_documents_count'],
        'hosting_ids': [record.pk for record in sets['hostings']],
        'income_ids': [record.pk for record in sets['incomes']],
        'totals': {
            'move': len(hostings_move) + len(incomes_move),
            'blocked': len(incomes_blocked),
            'clientless': len(clientless),
            'drafts': len(sets['draft_following']) + len(sets['draft_detaching']),
            'issued': len(sets['issued_accounts']),
        },
    }


def _log_diff(entity_type, instance, old_values, user):
    return accounting_service.log_entity_diff(
        entity_type, instance, old_values, user,
    )


def _detach_record(entity_type, record, user):
    old_values = accounting_service.snapshot_values(record, entity_type)
    record.project = None
    record.save(update_fields=['project', 'updated_at'])
    _log_diff(entity_type, record, old_values, user)


def _detach_draft(document, user):
    old_values = accounting_service.snapshot_values(
        document, EntityType.COLLECTION_ACCOUNT,
    )
    document.project = None
    document.save(update_fields=['project', 'updated_at'])
    _log_diff(EntityType.COLLECTION_ACCOUNT, document, old_values, user)


def _move_draft(document, new_profile, user):
    """A project-only draft follows the project: new client, fresh snapshot.

    Only the provisional customer_* snapshot is rewritten — a draft has not
    been emitted, so there is no history to preserve; ``customer_project_name``
    stays, the project itself did not change.
    """
    old_values = accounting_service.snapshot_values(
        document, EntityType.COLLECTION_ACCOUNT,
    )
    document.client_user = new_profile.user
    document.save(update_fields=['client_user', 'updated_at'])
    account = getattr(document, 'collection_account', None)
    if account is not None:
        defaults = customer_snapshot_defaults(new_profile)
        account.customer_name = defaults['name'] or ''
        account.customer_email = defaults['email'] or ''
        account.customer_identification = defaults['identification'] or ''
        account.customer_identification_type = (
            defaults['identification_type'] or ''
        )
        account.customer_contact_name = defaults['contact_name'] or ''
        account.customer_address = defaults['address'] or ''
        account.save(update_fields=[
            'customer_name', 'customer_email', 'customer_identification',
            'customer_identification_type', 'customer_contact_name',
            'customer_address',
        ])
    _log_diff(EntityType.COLLECTION_ACCOUNT, document, old_values, user)


@transaction.atomic
def change_client_apply(project, new_profile, mode, user):
    """Move the project to ``new_profile`` and cascade per ``mode``.

    One transaction: a half-moved project would split every per-client
    figure across two owners. Audit rows ride inside it (a rolled-back move
    must not leave a log claiming it happened) and none of them notify by
    email — the bulk convention.
    """
    sets = linked_sets(project)
    blocked = sets['blocked_income_pks']
    # A liquid child whose expected parent is also linked rides with the
    # parent through the cascade helpers — processing it as its own row
    # could move it to the new client while a blocked parent stays behind,
    # splitting one deal across two clients.
    linked_income_pks = {record.pk for record in sets['incomes']}

    def follows_its_parent(record):
        return (
            record.expected_income_id is not None
            and record.expected_income_id in linked_income_pks
        )

    old_project_values = accounting_service.snapshot_values(
        project, EntityType.PROJECT,
    )
    project.client = new_profile.user
    project.save(update_fields=['client', 'updated_at'])
    _log_diff(EntityType.PROJECT, project, old_project_values, user)

    moved = {'hostings': 0, 'incomes': 0, 'draft_accounts': 0}
    detached = {'hostings': 0, 'incomes': 0, 'draft_accounts': 0}
    skipped = {
        'issued_accounts': len(sets['issued_accounts']),
        'clientless': 0,
        'other_documents': sets['other_documents_count'],
    }

    if mode == MODE_MOVE:
        for record in sets['hostings']:
            if record.client_id is None:
                # No client to move from; the row keeps the project and is
                # completed later via bulk-assign-client.
                skipped['clientless'] += 1
                continue
            old_values = accounting_service.snapshot_values(
                record, EntityType.HOSTING,
            )
            record.client = new_profile
            update_fields = ['client', 'updated_at']
            # A stale billing snapshot routes the next cuenta to the wrong
            # inbox — same rule as every client reassignment.
            update_fields += accounting_service._refresh_hosting_snapshot(record)
            record.save(update_fields=update_fields)
            _log_diff(EntityType.HOSTING, record, old_values, user)
            moved['hostings'] += 1
        for record in sets['incomes']:
            if follows_its_parent(record):
                continue
            if record.client_id is None:
                skipped['clientless'] += 1
                continue
            if record.pk in blocked:
                _detach_record(EntityType.INCOME, record, user)
                if record.kind == IncomeRecord.Kind.EXPECTED:
                    accounting_service._cascade_project_to_liquid_children(
                        record, user,
                    )
                detached['incomes'] += 1
                continue
            old_values = accounting_service.snapshot_values(
                record, EntityType.INCOME,
            )
            record.client = new_profile
            record.save(update_fields=['client', 'updated_at'])
            _log_diff(EntityType.INCOME, record, old_values, user)
            if record.kind == IncomeRecord.Kind.EXPECTED:
                accounting_service._cascade_client_to_liquid_children(
                    record, user,
                )
            moved['incomes'] += 1
        for document in sets['draft_following']:
            _move_draft(document, new_profile, user)
            moved['draft_accounts'] += 1
        for document in sets['draft_detaching']:
            _detach_draft(document, user)
            detached['draft_accounts'] += 1
    else:
        for record in sets['hostings']:
            _detach_record(EntityType.HOSTING, record, user)
            detached['hostings'] += 1
        for record in sets['incomes']:
            if follows_its_parent(record):
                continue
            _detach_record(EntityType.INCOME, record, user)
            if record.kind == IncomeRecord.Kind.EXPECTED:
                accounting_service._cascade_project_to_liquid_children(
                    record, user,
                )
            detached['incomes'] += 1
        for document in sets['draft_following'] + sets['draft_detaching']:
            _detach_draft(document, user)
            detached['draft_accounts'] += 1

    logger.info(
        'Project %s changed client to profile %s (mode=%s): moved=%s detached=%s',
        project.pk, new_profile.pk, mode, moved, detached,
    )
    return {'moved': moved, 'detached': detached, 'skipped': skipped}


def deletion_blockers(project):
    """Counts that must be zero before a hard delete is allowed.

    Every status counts — even a cancelled cuenta loses its reference on a
    hard delete, which is exactly the silent SET_NULL blanking this guard
    exists to stop (PA-29: archive, never delete).
    """
    return {
        'hostings': HostingRecord.objects.filter(project=project).count(),
        'incomes': IncomeRecord.objects.filter(project=project).count(),
        'documents': Document.objects.filter(project=project).count(),
    }


def project_snapshot(project):
    """Pre-mutation snapshot for :func:`log_project_event` callers."""
    return accounting_service.snapshot_values(project, EntityType.PROJECT)


def log_project_event(project, action, old_values, user):
    """One audit row for a project-level mutation.

    ``old_values`` is the pre-mutation snapshot (empty dict for CREATED).
    For DELETED the diff is every non-empty tracked field going to '' —
    written BEFORE the delete so the row still has a pk to reference.
    """
    if action == Action.DELETED:
        changes = accounting_service._deletion_changes(
            EntityType.PROJECT, old_values,
        )
    elif action == Action.CREATED:
        new_values = accounting_service.snapshot_values(
            project, EntityType.PROJECT,
        )
        changes = [
            {'field': field, 'label': label, 'old': '', 'new': new_values[field]}
            for field, label in accounting_service.TRACKED_FIELDS[
                EntityType.PROJECT
            ]
            if new_values[field] != ''
        ]
    else:
        changes = accounting_service.compute_changes(
            EntityType.PROJECT, old_values,
            accounting_service.snapshot_values(project, EntityType.PROJECT),
        )
        if not changes:
            return None
    return accounting_service.log_accounting_change(
        entity_type=EntityType.PROJECT,
        object_id=project.pk,
        object_repr=accounting_service.object_repr(EntityType.PROJECT, project),
        action=action,
        changes=changes,
        actor=user,
    )
