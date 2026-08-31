"""Read-side query contract for the communications registry.

REST and MCP both consume this module so a filter has one meaning everywhere.
In particular, message dimensions are correlated through one ``Exists``
queryset: channel, direction, status, reply state and date must belong to the
same outgoing message when the derived reply filter is active.
"""

from dataclasses import dataclass

from django.db.models import Count, Exists, OuterRef, Prefetch, Q, Subquery
from django.db.models.functions import Lower
from django.utils.dateparse import parse_date, parse_datetime

from accounts.models import Project, UserProfile
from accounts.services.project_catalog_service import project_catalog_bucket
from accounts.services.proposal_client_service import build_client_display_name
from content.models import CommunicationMessage, CommunicationThread


REPLY_STATUS_CHOICES = (
    ('answered', 'Respondido'),
    ('unanswered', 'Sin respuesta'),
)

MESSAGE_FILTER_FIELDS = frozenset({
    'channel', 'direction', 'message_status', 'reply_status', 'date_from', 'date_to',
})


class CommunicationFilterError(ValueError):
    """Validated query-string error safe to expose to panel and MCP clients."""

    def __init__(self, errors):
        super().__init__(str(errors))
        self.errors = errors


def _managed_thread_id(entity, related_name):
    """Id de la comunicación madre de la entidad, o None si no tiene.

    El inverso de un OneToOne levanta `RelatedObjectDoesNotExist` en vez de
    devolver None, y la mayoría de las entidades no tiene madre: el acceso va
    con guarda para no pagar una excepción por fila.
    """
    thread = getattr(entity, related_name, None)
    return thread.pk if thread else None


def _state_payload(project):
    """Estado del proyecto para el subtítulo de la fila, o None."""
    state = getattr(project, 'current_state', None)
    if state is None:
        return None
    return {'id': state.pk, 'name': state.name, 'system_key': state.system_key}


class _ParamsRequest:
    """Adaptador mínimo para reusar `archive_scope`, que lee `query_params`.

    `parse_filters` recibe el QueryDict pelado, y `archive_scope` espera un
    request. Envolver es preferible a duplicar el vocabulario del scope: si
    mañana se agrega un valor o cambia el alias legacy, hay un solo sitio.
    """

    __slots__ = ('query_params',)

    def __init__(self, params):
        self.query_params = params


@dataclass(frozen=True)
class CommunicationFilters:
    client_id: int | None = None
    project_id: int | None = None
    without_project: bool = False
    statuses: tuple[str, ...] = ()
    channels: tuple[str, ...] = ()
    directions: tuple[str, ...] = ()
    message_statuses: tuple[str, ...] = ()
    reply_statuses: tuple[str, ...] = ()
    date_from: tuple[str, object] | None = None
    date_to: tuple[str, object] | None = None
    query: str = ''
    order: str = 'recent'
    # Eje de visibilidad, independiente de `statuses` (abierto/cerrado). Mismo
    # vocabulario que el gestor documental: active | archived | all.
    scope: str = 'active'


def message_queryset():
    active_replies = CommunicationMessage.objects.filter(
        reply_to_id=OuterRef('pk'), voided_at__isnull=True,
    )
    return (
        CommunicationMessage.objects
        .select_related('created_by', 'reply_to')
        .prefetch_related('documents', 'date_corrections__corrected_by')
        .annotate(has_reply=Exists(active_replies))
    )


def thread_queryset():
    return (
        CommunicationThread.objects
        .select_related('client__user', 'project')
        .annotate(
            messages_count=Count('messages', distinct=True),
            draft_count=Count(
                'messages',
                filter=Q(
                    messages__status=CommunicationMessage.Status.DRAFT,
                    messages__voided_at__isnull=True,
                ),
                distinct=True,
            ),
        )
        .prefetch_related(Prefetch('messages', queryset=message_queryset()))
    )


def _raw_values(params, key):
    if hasattr(params, 'getlist'):
        values = params.getlist(key)
    else:
        value = params.get(key)
        values = value if isinstance(value, (list, tuple)) else [value]

    tokens = []
    for value in values:
        if value in (None, ''):
            continue
        tokens.extend(part.strip() for part in str(value).split(','))
    return [token for token in tokens if token]


def _positive_id(params, key):
    values = _raw_values(params, key)
    if not values:
        return None
    if len(values) != 1:
        raise CommunicationFilterError({key: 'Selecciona un solo valor.'})
    try:
        value = int(values[0])
    except (TypeError, ValueError) as exc:
        raise CommunicationFilterError({key: 'Debe ser un número entero.'}) from exc
    if value < 1:
        raise CommunicationFilterError({key: 'Debe ser mayor que cero.'})
    return value


def _choice_values(params, key, choices):
    values = _raw_values(params, key)
    valid = {value for value, _label in choices}
    invalid = sorted(set(values) - valid)
    if invalid:
        raise CommunicationFilterError({
            key: f'Valor de filtro inválido: {", ".join(invalid)}.',
        })
    # Keep a stable order and collapse repeated query tokens.
    return tuple(dict.fromkeys(values))


def _date_lookup(params, key, *, end=False):
    values = _raw_values(params, key)
    if not values:
        return None
    if len(values) != 1:
        raise CommunicationFilterError({key: 'Usa una sola fecha ISO.'})
    raw_value = values[0]
    parsed_datetime = parse_datetime(raw_value)
    if parsed_datetime:
        lookup = 'occurred_at__lte' if end else 'occurred_at__gte'
        return lookup, parsed_datetime
    parsed_date = parse_date(raw_value)
    if parsed_date:
        lookup = 'occurred_at__date__lte' if end else 'occurred_at__date__gte'
        return lookup, parsed_date
    raise CommunicationFilterError({key: 'Usa una fecha ISO válida.'})


def parse_filters(params):
    """Parse scalar legacy values and comma/repeated multi-value parameters."""
    project_values = _raw_values(params, 'project')
    without_project = project_values == ['none']
    if 'none' in project_values and not without_project:
        raise CommunicationFilterError({
            'project': '“Sin proyecto” no se puede combinar con otro proyecto.',
        })
    project_id = None if without_project else _positive_id(params, 'project')

    order_values = _raw_values(params, 'order')
    if len(order_values) > 1:
        raise CommunicationFilterError({'order': 'Selecciona un solo orden.'})
    order = order_values[0] if order_values else 'recent'
    if order not in {'recent', 'oldest', 'title'}:
        raise CommunicationFilterError({'order': 'Orden inválido.'})

    # `archive_scope` vive en views/document.py pero no es de documentos: es el
    # vocabulario compartido del panel, y document_folder.py ya lo importa. Esto
    # trae de arriba el default 'active', el alias legacy `?archived=1` y el
    # None que distingue un valor inválido.
    from content.views.document import archive_scope

    scope = archive_scope(_ParamsRequest(params))
    if scope is None:
        raise CommunicationFilterError({
            'scope': 'El estado solicitado no es válido. Usa active, archived o all.',
        })

    return CommunicationFilters(
        scope=scope,
        client_id=_positive_id(params, 'client'),
        project_id=project_id,
        without_project=without_project,
        statuses=_choice_values(params, 'status', CommunicationThread.Status.choices),
        channels=_choice_values(params, 'channel', CommunicationMessage.Channel.choices),
        directions=_choice_values(
            params, 'direction', CommunicationMessage.Direction.choices,
        ),
        message_statuses=_choice_values(
            params, 'message_status', CommunicationMessage.Status.choices,
        ),
        reply_statuses=_choice_values(
            params, 'reply_status', REPLY_STATUS_CHOICES,
        ),
        date_from=_date_lookup(params, 'date_from'),
        date_to=_date_lookup(params, 'date_to', end=True),
        query=str(params.get('q') or '').strip(),
        order=order,
    )


def _message_predicate(filters, exclude=frozenset()):
    predicate = Q()
    active = False
    for key, values, model_field in (
        ('channel', filters.channels, 'channel'),
        ('direction', filters.directions, 'direction'),
        ('message_status', filters.message_statuses, 'status'),
    ):
        if key in exclude or not values:
            continue
        predicate &= Q(**{f'{model_field}__in': values})
        active = True
    for key, parsed in (
        ('date_from', filters.date_from), ('date_to', filters.date_to),
    ):
        if key in exclude or not parsed:
            continue
        predicate &= Q(**{parsed[0]: parsed[1]})
        active = True
    return predicate, active


def _apply_reply_status(messages, reply_statuses):
    """Narrow sent outgoing messages by their explicit active reply relation."""
    active_replies = CommunicationMessage.objects.filter(
        reply_to_id=OuterRef('pk'),
        voided_at__isnull=True,
    )
    messages = messages.filter(
        direction=CommunicationMessage.Direction.OUTGOING,
        status=CommunicationMessage.Status.SENT,
        voided_at__isnull=True,
    ).annotate(_communication_has_reply=Exists(active_replies))

    predicate = Q()
    if 'answered' in reply_statuses:
        predicate |= Q(_communication_has_reply=True)
    if 'unanswered' in reply_statuses:
        predicate |= Q(_communication_has_reply=False)
    return messages.filter(predicate)


def _filtered_messages(filters, exclude=frozenset()):
    """Build the one message queryset shared by every message dimension."""
    exclude = frozenset(exclude)
    predicate, active = _message_predicate(filters, exclude)
    messages = CommunicationMessage.objects.all()
    if active:
        messages = messages.filter(predicate)
    if 'reply_status' not in exclude and filters.reply_statuses:
        messages = _apply_reply_status(messages, filters.reply_statuses)
        active = True
    return messages, active


def apply_filters(queryset, filters, *, exclude=frozenset()):
    """Apply navigation, thread, correlated-message and text filters."""
    exclude = frozenset(exclude)
    # El scope va PRIMERO y no admite exclusión por faceta: no es una dimensión
    # de navegación sino el ámbito en que se mira todo. Las facetas se recalculan
    # dentro de él, que es justo lo que hace que sus conteos digan la verdad al
    # encender el interruptor de archivados.
    from content.views.document import apply_archive_scope

    queryset = apply_archive_scope(queryset, filters.scope)
    if 'client' not in exclude and filters.client_id is not None:
        queryset = queryset.filter(client_id=filters.client_id)
    if 'project' not in exclude:
        if filters.without_project:
            queryset = queryset.filter(project_id__isnull=True)
        elif filters.project_id is not None:
            queryset = queryset.filter(project_id=filters.project_id)
    if 'status' not in exclude and filters.statuses:
        queryset = queryset.filter(status__in=filters.statuses)

    matching_messages, has_message_filter = _filtered_messages(filters, exclude)
    if has_message_filter:
        matching_messages = matching_messages.filter(thread_id=OuterRef('pk'))
        queryset = queryset.annotate(
            _communication_message_match=Exists(matching_messages),
        ).filter(_communication_message_match=True)

    if 'q' not in exclude and filters.query:
        query = filters.query
        matching_text = CommunicationMessage.objects.filter(
            thread_id=OuterRef('pk'),
        ).filter(Q(subject__icontains=query) | Q(content__icontains=query))
        queryset = queryset.annotate(
            _communication_text_match=Exists(matching_text),
        ).filter(
            Q(title__icontains=query)
            | Q(project__name__icontains=query)
            | Q(client__company_name__icontains=query)
            | Q(client__user__first_name__icontains=query)
            | Q(client__user__last_name__icontains=query)
            | Q(client__user__email__icontains=query)
            | Q(_communication_text_match=True)
        )
    return queryset


def order_threads(queryset, order):
    if order == 'oldest':
        return queryset.order_by('last_activity_at', 'id')
    if order == 'title':
        return queryset.order_by(Lower('title'), 'id')
    return queryset.order_by('-last_activity_at', '-id')


def _choice_count_dict(rows, choices):
    counts = {value: 0 for value, _label in choices}
    for row in rows:
        counts[row['value']] = row['count']
    return counts


def _message_dimension_counts(filters, dimension, choices):
    # Navigation, text and thread status narrow the candidate threads. The
    # remaining message dimensions then share one predicate on each message.
    thread_candidates = apply_filters(
        CommunicationThread.objects.all(),
        filters,
        exclude=MESSAGE_FILTER_FIELDS,
    )
    model_field = 'status' if dimension == 'message_status' else dimension
    messages, _active = _filtered_messages(filters, {dimension})
    messages = messages.filter(
        thread_id__in=Subquery(thread_candidates.values('pk')),
    )
    rows = (
        messages.values(value=Lower(model_field))
        .annotate(count=Count('thread_id', distinct=True))
    )
    return _choice_count_dict(rows, choices)


def _reply_status_counts(filters):
    """Count the two derived reply states over the same candidate messages."""
    thread_candidates = apply_filters(
        CommunicationThread.objects.all(),
        filters,
        exclude=MESSAGE_FILTER_FIELDS,
    )
    messages, _active = _filtered_messages(filters, {'reply_status'})
    messages = messages.filter(
        thread_id__in=Subquery(thread_candidates.values('pk')),
    )
    return {
        value: _apply_reply_status(messages, (value,))
        .values('thread_id')
        .distinct()
        .count()
        for value, _label in REPLY_STATUS_CHOICES
    }


def build_facets(filters):
    """Return navigation and option counts without per-entity queries."""
    fully_filtered = apply_filters(CommunicationThread.objects.all(), filters)
    navigation_threads = apply_filters(
        CommunicationThread.objects.all(), filters, exclude={'client', 'project'},
    )

    project_counts = {
        row['project_id']: row['count']
        for row in navigation_threads.values('project_id').annotate(count=Count('id'))
    }
    client_counts = {
        row['client_id']: row['count']
        for row in navigation_threads.values('client_id').annotate(count=Count('id'))
    }

    projects = list(
        Project.objects.select_related(
            'client__profile', 'current_state', 'communication_root_thread',
        ).all()
    )

    client_ids = set(client_counts)
    if filters.client_id is not None:
        client_ids.add(filters.client_id)
    clients = UserProfile.objects.clients().filter(pk__in=client_ids).in_bulk()

    project_rows = []
    project_ids = set()
    for project in projects:
        project_ids.add(project.pk)
        profile = getattr(project.client, 'profile', None)
        project_rows.append({
            'id': project.pk,
            'name': project.name,
            'client_id': profile.pk if profile else None,
            'client_name': (
                build_client_display_name(profile) if profile else project.client.email
            ),
            'catalog_bucket': project_catalog_bucket(project),
            # Sin este id el panel no puede fijar la comunicación madre arriba
            # de su grupo ni suprimirla de la lista de hermanas.
            'managed_root_id': _managed_thread_id(project, 'communication_root_thread'),
            'state': _state_payload(project),
            'count': project_counts.get(project.pk, 0),
            'unavailable': False,
        })
    if filters.project_id is not None and filters.project_id not in project_ids:
        project_rows.append({
            'id': filters.project_id,
            'name': 'Proyecto no disponible',
            'client_id': None,
            'client_name': '',
            'catalog_bucket': 'active',
            'managed_root_id': None,
            'state': None,
            'count': 0,
            'unavailable': True,
        })
    project_rows.sort(key=lambda row: row['name'].casefold())

    client_rows = [
        {
            'id': client_id,
            'name': (
                build_client_display_name(clients[client_id])
                if client_id in clients else 'Cliente no disponible'
            ),
            # `is_archived` + `catalog_bucket`: los mismos dos campos con que el
            # gestor documental arma el grupo «Clientes inactivos».
            'is_archived': (
                clients[client_id].is_archived_client if client_id in clients else False
            ),
            'catalog_bucket': (
                'archived'
                if client_id in clients and clients[client_id].is_archived_client
                else 'active'
            ),
            'managed_root_id': (
                _managed_thread_id(clients[client_id], 'client_communication_root_thread')
                if client_id in clients else None
            ),
            'count': client_counts.get(client_id, 0),
            'unavailable': client_id not in clients,
        }
        for client_id in client_ids
    ]
    client_rows.sort(key=lambda row: row['name'].casefold())

    status_rows = (
        apply_filters(
            CommunicationThread.objects.all(), filters, exclude={'status'},
        )
        .values(value=Lower('status'))
        .annotate(count=Count('id'))
    )

    return {
        'total': fully_filtered.count(),
        'navigation_total': navigation_threads.count(),
        'without_project_count': project_counts.get(None, 0),
        'projects': project_rows,
        'clients': client_rows,
        'filters': {
            'status': _choice_count_dict(status_rows, CommunicationThread.Status.choices),
            'channel': _message_dimension_counts(
                filters, 'channel', CommunicationMessage.Channel.choices,
            ),
            'direction': _message_dimension_counts(
                filters, 'direction', CommunicationMessage.Direction.choices,
            ),
            'message_status': _message_dimension_counts(
                filters, 'message_status', CommunicationMessage.Status.choices,
            ),
            'reply_status': _reply_status_counts(filters),
        },
    }
