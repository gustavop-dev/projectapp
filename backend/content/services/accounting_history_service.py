"""One owner for the two querysets behind the Historial tab.

The list endpoints, the per-tab counts and the CSV/XLSX export all have to
mean exactly the same thing by "the filter that is applied right now", so
they build their queryset here instead of each re-parsing the parameters —
the same discipline that makes ``accounting_export`` reuse ``_apply_filters``
rather than re-implement the list's filtering.

The send log's record links live in ``EmailLogTarget``, one row per record
named by the email, because the digest notices cover several at once. Every
condition that reaches through that relation is collected into a single ``Q``
and applied in one ``.filter()`` call on purpose: split across calls, Django
would join the table once per call and "a hosting of this client" would
degrade into "some hosting, and separately something of this client".
"""

from datetime import date

from django.db.models import Q


def parse_date_param(value, param):
    """Coerce an ISO date, naming the offending parameter when it is not."""
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"El parámetro '{param}' debe ser una fecha AAAA-MM-DD.")


def _parse_int(value, param):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"El parámetro '{param}' debe ser un número entero.")


def _as_list(value):
    """Accept one value, a comma-separated string, or a real list.

    A preset like "Recordatorios de cobro" spans two notice types, and the
    same filter travels two ways: as a query param on the list endpoint
    (where the panel joins arrays with commas, like the export does) and as
    a JSON array in the tab-counts body.
    """
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = str(value).split(',')
    return [str(item).strip() for item in items if str(item).strip()]


def _client_target_q(client_id):
    """Targets belonging to a client, keyed by ``UserProfile`` id.

    The three entities that carry a client key it differently — incomes and
    hostings point at the ``UserProfile``, a cuenta de cobro at the ``User``
    behind it — so each is resolved on its own terms and the caller only ever
    speaks profile ids, which is what the client autocomplete carries.
    """
    from content.models import Document, HostingRecord, IncomeRecord

    return (
        Q(
            targets__entity_type='income',
            targets__object_id__in=IncomeRecord.objects.filter(
                client_id=client_id,
            ).values('id'),
        )
        | Q(
            targets__entity_type='hosting',
            targets__object_id__in=HostingRecord.objects.filter(
                client_id=client_id,
            ).values('id'),
        )
        | Q(
            targets__entity_type='collection_account',
            targets__object_id__in=Document.objects.filter(
                client_user__profile__id=client_id,
            ).values('id'),
        )
    )


def _project_target_q(project_id):
    """Targets belonging to a project. All three entities key it the same."""
    from content.models import Document, HostingRecord, IncomeRecord

    return (
        Q(
            targets__entity_type='income',
            targets__object_id__in=IncomeRecord.objects.filter(
                project_id=project_id,
            ).values('id'),
        )
        | Q(
            targets__entity_type='hosting',
            targets__object_id__in=HostingRecord.objects.filter(
                project_id=project_id,
            ).values('id'),
        )
        | Q(
            targets__entity_type='collection_account',
            targets__object_id__in=Document.objects.filter(
                project_id=project_id,
            ).values('id'),
        )
    )


def email_log_queryset(params):
    """The send log, scoped to the module and narrowed by ``params``.

    Raises ``ValueError`` with a user-facing message on a malformed value.
    """
    from content.models import EmailLog
    from content.serializers.accounting import EMAIL_TEMPLATE_LABELS

    logs = EmailLog.objects.filter(
        template_key__in=EMAIL_TEMPLATE_LABELS,
    ).select_related('body')

    if params.get('template_key'):
        logs = logs.filter(template_key__in=_as_list(params['template_key']))
    if params.get('status'):
        logs = logs.filter(status__in=_as_list(params['status']))
    if params.get('recipient'):
        logs = logs.filter(recipient__icontains=params['recipient'])
    if params.get('subject'):
        logs = logs.filter(subject__icontains=params['subject'])
    if params.get('origin_action'):
        logs = logs.filter(origin_action__in=_as_list(params['origin_action']))
    if params.get('date_from'):
        logs = logs.filter(
            sent_at__date__gte=parse_date_param(params['date_from'], 'date_from'),
        )
    if params.get('date_to'):
        logs = logs.filter(
            sent_at__date__lte=parse_date_param(params['date_to'], 'date_to'),
        )

    target_q = Q()
    joined = False
    if params.get('entity_type'):
        target_q &= Q(targets__entity_type__in=_as_list(params['entity_type']))
        joined = True
    if params.get('object_id'):
        target_q &= Q(
            targets__object_id=_parse_int(params['object_id'], 'object_id'),
        )
        joined = True
    if params.get('client'):
        target_q &= _client_target_q(_parse_int(params['client'], 'client'))
        joined = True
    if params.get('project'):
        target_q &= _project_target_q(_parse_int(params['project'], 'project'))
        joined = True

    if joined:
        # One call, so the conditions describe a single target row, and
        # distinct() because an email with several matching targets would
        # otherwise be listed once per match.
        logs = logs.filter(target_q).distinct()

    return logs


def change_log_queryset(params):
    """The audit trail, narrowed by ``params``.

    Raises ``ValueError`` with a user-facing message on a malformed value.
    """
    from content.models import AccountingChangeLog

    logs = AccountingChangeLog.objects.select_related('actor').all()

    if params.get('entity_type'):
        logs = logs.filter(entity_type__in=_as_list(params['entity_type']))
    if params.get('object_id'):
        logs = logs.filter(
            object_id=_parse_int(params['object_id'], 'object_id'),
        )
    if params.get('object_repr'):
        logs = logs.filter(object_repr__icontains=params['object_repr'])
    if params.get('action'):
        logs = logs.filter(action__in=_as_list(params['action']))
    if params.get('actor'):
        logs = logs.filter(actor_username__icontains=params['actor'])
    if params.get('date_from'):
        logs = logs.filter(
            created_at__date__gte=parse_date_param(
                params['date_from'], 'date_from',
            ),
        )
    if params.get('date_to'):
        logs = logs.filter(
            created_at__date__lte=parse_date_param(params['date_to'], 'date_to'),
        )

    return logs


# What the panel is allowed to say when it asks for a tab's count. Anything
# else in a saved tab's stored filters is ignored rather than trusted: the
# strip must not become a way to query arbitrary columns.
SENDS_FILTER_KEYS = frozenset({
    'template_key', 'status', 'recipient', 'subject', 'origin_action',
    'date_from', 'date_to', 'entity_type', 'object_id', 'client', 'project',
})
CHANGES_FILTER_KEYS = frozenset({
    'entity_type', 'object_id', 'object_repr', 'action', 'actor',
    'date_from', 'date_to',
})

QUERYSET_BY_SCOPE = {
    'sends': (email_log_queryset, SENDS_FILTER_KEYS),
    'changes': (change_log_queryset, CHANGES_FILTER_KEYS),
}


def queryset_for(scope, filters):
    """Build the scope's queryset from a saved tab's filter dict."""
    try:
        builder, allowed = QUERYSET_BY_SCOPE[scope]
    except KeyError:
        raise ValueError("El parámetro 'scope' debe ser 'sends' o 'changes'.")
    clean = {
        key: value
        for key, value in (filters or {}).items()
        if key in allowed and value not in ('', None, [])
    }
    return builder(clean)
