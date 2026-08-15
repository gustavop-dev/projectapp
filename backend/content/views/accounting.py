"""API views for the accounting module (panel, superuser-only).

All endpoints require an authenticated superuser (IsSuperUser). Lists
return {'results': [...], 'meta': {...}} and are filtered server-side via
shared query params (date_from/date_to/year, amount_min/amount_max,
partner, q) plus per-entity choice filters; rich interactive filtering
happens client-side. The change log is the only paginated endpoint.
"""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import Project
from content.api_errors import error_response, error_response_from_exc
from content.models import (
    AccountingChangeLog,
    AccountingSettings,
    AdsSpendRecord,
    CardBalanceSnapshot,
    CreditCard,
    CreditCardStatement,
    Document,
    EmailLog,
    ExpenseRecord,
    HostingRecord,
    IncomeRecord,
    MerchantAlias,
    NotificationRecipient,
    PocketMovement,
    RecurringCategory,
    RecurringPayment,
)
from content.permissions import IsSuperUser
from content.serializers.accounting import (
    TWO_PLACES,
    money_str,
    AccountingChangeLogSerializer,
    AccountingSettingsSerializer,
    AdsSpendRecordCreateUpdateSerializer,
    AdsSpendRecordSerializer,
    CardBalanceSnapshotCreateUpdateSerializer,
    CardBalanceSnapshotSerializer,
    CreditCardCreateUpdateSerializer,
    CreditCardSerializer,
    EMAIL_TEMPLATE_LABELS,
    EmailLogSerializer,
    ExpenseRecordCreateUpdateSerializer,
    ExpenseRecordSerializer,
    HostingCycleCreateSerializer,
    HostingCycleSerializer,
    HostingClientBulkAssignSerializer,
    HostingRecordCreateUpdateSerializer,
    HostingRecordSerializer,
    IncomeRecordCreateUpdateSerializer,
    IncomeRecordSerializer,
    IncomeClientBulkAssignSerializer,
    IncomeReminderMuteSerializer,
    IncomeSettlementSerializer,
    NotificationRecipientCreateUpdateSerializer,
    NotificationRecipientSerializer,
    PocketMovementCreateUpdateSerializer,
    PocketMovementSerializer,
    RecurringPaymentCreateUpdateSerializer,
    RecurringPaymentSerializer,
)
from content.serializers.accounting_statement import (
    CreditCardStatementSerializer,
    CreditCardStatementWriteSerializer,
    MerchantAliasSerializer,
    MerchantAliasWriteSerializer,
)
from content.services import (
    accounting_email_retry_service,
    accounting_history_service,
    accounting_income_duplicate_service,
    accounting_income_mute_service,
    accounting_service,
    accounting_settlement_service,
)
from content.utils import today_bogota

EntityType = AccountingChangeLog.EntityType


# The history service owns the parsing so its querysets and these views
# reject a malformed date with the same message.
_parse_date = accounting_history_service.parse_date_param

# Builtin presets plus the per-user ceiling of saved tabs, with room to spare.
MAX_TAB_COUNT_SPECS = 24
HISTORY_PAGE_SIZE = 20


def _paginated_history_response(queryset, params, serializer_class):
    """Serialize one 20-row page of a history queryset."""
    total = queryset.count()
    try:
        page = max(1, int(params.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    offset = (page - 1) * HISTORY_PAGE_SIZE
    num_pages = max(1, -(-total // HISTORY_PAGE_SIZE))

    serializer = serializer_class(
        queryset[offset:offset + HISTORY_PAGE_SIZE], many=True,
    )
    return Response({
        'results': serializer.data,
        'count': total,
        'page': page,
        'num_pages': num_pages,
    })


def _parse_decimal(value, param):
    try:
        return Decimal(value)
    except (TypeError, InvalidOperation):
        raise ValueError(f"El parámetro '{param}' debe ser un número.")


# The serializers module owns the canonical money-string format.
_money = money_str


def _top_record(queryset, concept_field='concept'):
    top = (
        queryset.order_by('-total_amount')
        .values(concept_field, 'total_amount')
        .first()
    )
    if not top:
        return None
    return {
        'concept': top[concept_field],
        'amount': _money(top['total_amount'] or 0),
    }


def _income_meta(queryset, params):
    today = today_bogota()
    year_qs = queryset.filter(period_date__year=today.year)
    totals = year_qs.aggregate(
        expected_total=Sum('total_amount', filter=Q(kind='expected')),
        liquid_total=Sum('total_amount', filter=Q(kind='liquid')),
        lost_total=Sum('total_amount', filter=Q(kind='lost')),
        month_liquid=Sum(
            'total_amount',
            filter=Q(kind='liquid', period_date__month=today.month),
        ),
    )
    expected = totals['expected_total'] or 0
    liquid = totals['liquid_total'] or 0
    received_pct = int(round(liquid / expected * 100)) if expected else None
    return {
        'expected_total': _money(expected),
        'liquid_total': _money(liquid),
        'lost_total': _money(totals['lost_total'] or 0),
        'received_pct': received_pct,
        'current_month_liquid': _money(totals['month_liquid'] or 0),
        'top_income': _top_record(year_qs.filter(kind='liquid')),
        # Completion debt of the client link over the whole filtered set —
        # legacy rows live in past years, so the year window would hide them.
        'without_client_count': queryset.filter(client__isnull=True).count(),
        # Same backlog definition as /panel/projects: only client-linked rows
        # can be proposed a project, so both counters compose without overlap.
        'without_project_count': queryset.filter(
            client__isnull=False, project__isnull=True,
        ).count(),
    }


def _expense_meta(queryset, params):
    today = today_bogota()
    year_qs = queryset.filter(period_date__year=today.year)
    totals = year_qs.aggregate(
        year_total=Sum('total_amount'),
        month_total=Sum(
            'total_amount', filter=Q(period_date__month=today.month),
        ),
        business_total=Sum('total_amount', filter=Q(category='business')),
        personal_total=Sum('total_amount', filter=Q(category='personal')),
    )
    month_total = totals['month_total'] or 0
    # Alert: current month >= 1.5x the average of the year's prior months.
    prior_months = (
        year_qs.filter(period_date__month__lt=today.month)
        .values_list('period_date__month')
        .annotate(total=Sum('total_amount'))
    )
    prior_totals = [row[1] for row in prior_months]
    alert = False
    if prior_totals:
        average = sum(prior_totals) / len(prior_totals)
        alert = average > 0 and month_total >= average * Decimal('1.5')
    deduction_rows = list(
        year_qs.exclude(deduction_type='')
        .values_list('deduction_type')
        .annotate(total=Sum('total_amount'))
    )
    deductions_by_type = {row[0]: _money(row[1] or 0) for row in deduction_rows}
    return {
        'year_total': _money(totals['year_total'] or 0),
        'current_month_total': _money(month_total),
        'business_total': _money(totals['business_total'] or 0),
        'personal_total': _money(totals['personal_total'] or 0),
        'current_month_alert': alert,
        'top_expense': _top_record(year_qs),
        # Year deductions, whole and by type: the answer to "cuánto se fue
        # en comisiones y cuánto acumuló la retención".
        'deductions_total': _money(
            sum((row[1] or 0 for row in deduction_rows), Decimal('0')),
        ),
        'deductions_by_type': deductions_by_type,
    }


def _hosting_meta(queryset, params):
    today = today_bogota()
    totals = queryset.aggregate(
        active_count=Count('id', filter=Q(is_active=True)),
        monthly_income=Sum('monthly_value', filter=Q(is_active=True)),
        total_paid=Sum('total_paid'),
        expiring_soon_count=Count(
            'id',
            filter=Q(
                is_active=True,
                valid_to__gte=today,
                valid_to__lte=today + timedelta(days=30),
            ),
        ),
        without_client_count=Count('id', filter=Q(client__isnull=True)),
        # Same backlog definition as /panel/projects: only client-linked rows
        # can be proposed a project, so both counters compose without overlap.
        without_project_count=Count(
            'id', filter=Q(client__isnull=False, project__isnull=True),
        ),
    )
    return {
        'active_count': totals['active_count'] or 0,
        'monthly_income': _money(totals['monthly_income'] or 0),
        'total_paid': _money(totals['total_paid'] or 0),
        'expiring_soon_count': totals['expiring_soon_count'] or 0,
        'without_client_count': totals['without_client_count'] or 0,
        'without_project_count': totals['without_project_count'] or 0,
    }


def _pocket_meta(queryset, params):
    as_of = None
    if params.get('date_to'):
        as_of = _parse_date(params['date_to'], 'date_to')
    return {'balance': _money(accounting_service.pocket_balance(as_of=as_of))}


def _recurring_meta(queryset, params):
    active = queryset.filter(is_active=True)
    total = accounting_service.recurring_monthly_cost(active)
    rate = AccountingSettings.load().usd_exchange_rate or 0
    monthly_usd = (
        _money((Decimal(total) / rate).quantize(TWO_PLACES)) if rate else None
    )
    usd_native = active.filter(currency='USD').aggregate(
        total=Sum('price'),
    )['total']
    return {
        'monthly_cop_total': _money(total),
        'monthly_usd_total': monthly_usd,
        'usd_native_total': _money(usd_native or 0),
        'usd_exchange_rate': _money(rate) if rate else None,
    }


_ENTITIES = {
    'income': {
        'entity_type': EntityType.INCOME,
        'model': IncomeRecord,
        'read': IncomeRecordSerializer,
        'write': IncomeRecordCreateUpdateSerializer,
        'date_field': 'period_date',
        'amount_field': 'total_amount',
        'search_fields': (
            'concept', 'notes', 'client__company_name',
            'client__user__first_name', 'client__user__last_name',
            'project__name',
        ),
        'choice_filters': ('kind', 'destination', 'ledger', 'origin'),
        # `expected_income` is here so the liquid children of one expected
        # record are finally queryable (?expected_income=<id>); nothing could
        # reach them from the panel before.
        'null_filters': ('client', 'project', 'expected_income'),
        'select_related': ('client', 'client__user', 'project'),
        'has_split': True,
        'pocket_filter': Q(destination=IncomeRecord.Destination.POCKET),
        'payment_status_filter': True,
        'meta': _income_meta,
        # Safe to share across requests: annotate() resolves a copy of the
        # expression, never the expression itself.
        'annotations': {
            'paid_amount': accounting_service.paid_amount_subquery(),
            **accounting_service.collection_account_subqueries(),
        },
    },
    'expense': {
        'entity_type': EntityType.EXPENSE,
        'model': ExpenseRecord,
        'read': ExpenseRecordSerializer,
        'write': ExpenseRecordCreateUpdateSerializer,
        'date_field': 'period_date',
        'amount_field': 'total_amount',
        'search_fields': ('concept', 'notes'),
        'choice_filters': ('category', 'ledger', 'deduction_type'),
        'has_split': True,
        'meta': _expense_meta,
        'annotations': {
            'source_income_concept':
                accounting_service.source_income_concept_subquery(),
        },
    },
    'hosting': {
        'entity_type': EntityType.HOSTING,
        'model': HostingRecord,
        'read': HostingRecordSerializer,
        'write': HostingRecordCreateUpdateSerializer,
        'date_field': 'valid_from',
        'amount_field': 'monthly_value',
        'search_fields': (
            'client_name', 'domain_url', 'notes',
            'client__company_name', 'client__user__first_name',
            'client__user__last_name', 'project__name',
        ),
        # No `project` choice filter: the project is a relation, so the
        # Proyecto multi-select narrows the loaded rows client-side and the
        # 'sin proyecto' sentinel rides `null_filters` below.
        'choice_filters': ('payment_modality',),
        'bool_filters': ('is_active',),
        'null_filters': ('client', 'project'),
        'select_related': ('client', 'client__user', 'project'),
        'meta': _hosting_meta,
    },
    'pocket': {
        'entity_type': EntityType.POCKET,
        'model': PocketMovement,
        'read': PocketMovementSerializer,
        'write': PocketMovementCreateUpdateSerializer,
        'date_field': 'movement_date',
        'amount_field': 'amount',
        'search_fields': ('concept', 'notes'),
        'choice_filters': ('direction',),
        'select_related': ('income_record', 'expense_record'),
        'meta': _pocket_meta,
    },
    'recurring': {
        'entity_type': EntityType.RECURRING,
        'model': RecurringPayment,
        'read': RecurringPaymentSerializer,
        'write': RecurringPaymentCreateUpdateSerializer,
        'date_field': None,
        'amount_field': 'price',
        'search_fields': ('name', 'notes'),
        'choice_filters': (
            'frequency', 'cost_type', 'currency', 'payment_method', 'category',
        ),
        'bool_filters': ('is_active',),
        'select_related': ('category',),
        'meta': _recurring_meta,
    },
    'ads': {
        'entity_type': EntityType.ADS,
        'model': AdsSpendRecord,
        'read': AdsSpendRecordSerializer,
        'write': AdsSpendRecordCreateUpdateSerializer,
        'date_field': 'spend_date',
        'amount_field': 'amount',
        'search_fields': ('origin_card', 'notes'),
        'choice_filters': ('platform', 'origin_card'),
        'with_accumulated': True,
    },
    'credit_card': {
        'entity_type': EntityType.CREDIT_CARD,
        'model': CreditCard,
        'read': CreditCardSerializer,
        'write': CreditCardCreateUpdateSerializer,
        'date_field': None,
        'amount_field': 'credit_limit',
        'search_fields': ('name', 'notes'),
        'bool_filters': ('is_active',),
    },
    'card_snapshot': {
        'entity_type': EntityType.CARD_SNAPSHOT,
        'model': CardBalanceSnapshot,
        'read': CardBalanceSnapshotSerializer,
        'write': CardBalanceSnapshotCreateUpdateSerializer,
        'date_field': 'snapshot_date',
        'amount_field': 'debt_amount',
        'search_fields': ('card_name', 'notes'),
        'choice_filters': ('card_name',),
    },
    'statement': {
        'entity_type': EntityType.STATEMENT,
        'model': CreditCardStatement,
        'read': CreditCardStatementSerializer,
        'write': CreditCardStatementWriteSerializer,
        'date_field': 'period_date',
        'amount_field': 'purchases_total',
        'search_fields': ('card_name', 'notes'),
        'choice_filters': ('status', 'card_name'),
    },
    'merchant_alias': {
        'entity_type': EntityType.MERCHANT_ALIAS,
        'model': MerchantAlias,
        'read': MerchantAliasSerializer,
        'write': MerchantAliasWriteSerializer,
        'date_field': None,
        'amount_field': None,
        'search_fields': ('match_text', 'merchant_name', 'notes'),
        'choice_filters': ('default_category',),
    },
    'notification_recipient': {
        'entity_type': EntityType.NOTIFICATION_RECIPIENT,
        'model': NotificationRecipient,
        'read': NotificationRecipientSerializer,
        'write': NotificationRecipientCreateUpdateSerializer,
        'date_field': None,
        'amount_field': None,
        'search_fields': ('email', 'notes'),
        'bool_filters': ('is_active',),
    },
}


def base_queryset(config):
    """Entity queryset with its read annotations applied.

    Shared with the export views so a column computed for the table can
    never go missing from the CSV.
    """
    queryset = config['model'].objects.all()
    annotations = config.get('annotations')
    if annotations:
        queryset = queryset.annotate(**annotations)
    return queryset


def _apply_filters(queryset, params, config):
    date_field = config['date_field']
    if date_field:
        if params.get('year'):
            try:
                year = int(params['year'])
            except (TypeError, ValueError):
                raise ValueError("El parámetro 'year' debe ser un año válido.")
            queryset = queryset.filter(**{f'{date_field}__year': year})
        if params.get('date_from'):
            queryset = queryset.filter(**{
                f'{date_field}__gte': _parse_date(
                    params['date_from'], 'date_from',
                ),
            })
        if params.get('date_to'):
            queryset = queryset.filter(**{
                f'{date_field}__lte': _parse_date(
                    params['date_to'], 'date_to',
                ),
            })

    amount_field = config['amount_field']
    if amount_field and params.get('amount_min'):
        queryset = queryset.filter(**{
            f'{amount_field}__gte': _parse_decimal(
                params['amount_min'], 'amount_min',
            ),
        })
    if amount_field and params.get('amount_max'):
        queryset = queryset.filter(**{
            f'{amount_field}__lte': _parse_decimal(
                params['amount_max'], 'amount_max',
            ),
        })

    for field in config.get('choice_filters', ()):
        value = params.get(field)
        if value:
            # Comma-separated values filter as OR (multi-select filters).
            values = [item for item in value.split(',') if item]
            # 'none' isolates the rows whose choice was never set, so a
            # multi-select can mix real values with "sin clasificar". No
            # choice in the module uses 'none' as a real value.
            include_blank = 'none' in values
            values = [item for item in values if item != 'none']
            if include_blank:
                condition = Q(**{field: ''})
                if values:
                    condition |= Q(**{f'{field}__in': values})
                queryset = queryset.filter(condition)
            elif len(values) > 1:
                queryset = queryset.filter(**{f'{field}__in': values})
            elif values:
                queryset = queryset.filter(**{field: values[0]})

    for field in config.get('bool_filters', ()):
        value = params.get(field)
        if value in ('true', 'false'):
            queryset = queryset.filter(**{field: value == 'true'})

    # Nullable FK filters: 'none' isolates the unassigned rows as a group,
    # 'all'/empty means no filter, ids (comma-separated) filter as OR.
    # Same sentinel vocabulary as the documents `folder` param.
    for field in config.get('null_filters', ()):
        value = (params.get(field) or '').strip()
        if not value or value == 'all':
            continue
        tokens = [item for item in value.split(',') if item]
        include_null = 'none' in tokens
        try:
            ids = [int(item) for item in tokens if item != 'none']
        except ValueError:
            raise ValueError(
                f"El parámetro '{field}' debe ser 'none', 'all' o uno o "
                'varios ids separados por coma.'
            )
        condition = Q()
        if include_null:
            condition |= Q(**{f'{field}__isnull': True})
        if ids:
            condition |= Q(**{f'{field}__in': ids})
        if condition:
            queryset = queryset.filter(condition)

    if config.get('has_split') and params.get('partner'):
        partner = params['partner']
        if partner == 'gustavo':
            queryset = queryset.filter(gustavo_amount__gt=0)
        elif partner == 'carlos':
            queryset = queryset.filter(carlos_amount__gt=0)
        elif partner == 'projectapp':
            # Pocket-bound records or records with an unassigned remainder.
            partner_q = Q(
                total_amount__gt=F('gustavo_amount') + F('carlos_amount'),
            )
            pocket_q = config.get('pocket_filter')
            if pocket_q is not None:
                partner_q = pocket_q | partner_q
            queryset = queryset.filter(partner_q)
        elif partner != 'all':
            raise ValueError(
                "El parámetro 'partner' debe ser gustavo, carlos, "
                'projectapp o all.'
            )

    if config.get('payment_status_filter') and params.get('payment_status'):
        # Mirrors IncomeRecordSerializer.get_payment_status over the
        # `paid_amount` annotation: keep both sides in sync.
        value = params['payment_status']
        expected = Q(kind=IncomeRecord.Kind.EXPECTED)
        if value == 'pending':
            queryset = queryset.filter(expected, paid_amount__lte=0)
        elif value == 'partial':
            queryset = queryset.filter(
                expected,
                paid_amount__gt=0,
                paid_amount__lt=F('total_amount'),
            )
        elif value == 'paid':
            queryset = queryset.filter(
                expected, paid_amount__gte=F('total_amount'),
            )
        else:
            raise ValueError(
                "El parámetro 'payment_status' debe ser pending, partial "
                'o paid.'
            )

    search = (params.get('q') or '').strip()
    if search:
        search_q = Q()
        for field in config['search_fields']:
            search_q |= Q(**{f'{field}__icontains': search})
        queryset = queryset.filter(search_q)

    return queryset


# ── Generic handlers ──

def _list_records(request, key):
    config = _ENTITIES[key]
    queryset = base_queryset(config)
    if config.get('select_related'):
        queryset = queryset.select_related(*config['select_related'])
    try:
        queryset = _apply_filters(queryset, request.query_params, config)
        meta = config.get('meta', lambda qs, params: {})(
            queryset, request.query_params,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    if config.get('with_accumulated'):
        records = accounting_service.ads_with_accumulated(queryset)
    else:
        records = queryset
    serializer = config['read'](records, many=True)
    return Response({'results': serializer.data, 'meta': meta})


def _create_record(request, key):
    config = _ENTITIES[key]
    serializer = config['write'](data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        instance = accounting_service.create_record(
            config['entity_type'], serializer, request.user,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    return Response(
        config['read'](instance).data, status=status.HTTP_201_CREATED,
    )


def _retrieve_record(request, key, record_id):
    config = _ENTITIES[key]
    instance = get_object_or_404(config['model'], pk=record_id)
    return Response(config['read'](instance).data)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_income_detail(request, record_id):
    """One income with everything needed to inspect it without leaving the row.

    Its own endpoint rather than a fatter `read` serializer: `config['read']`
    is shared with the list, the create/update responses and the MCP
    get_income handler, so nesting three lists there would weigh down every
    one of them.

    The shape deliberately mirrors the settle endpoint's, so the UI renders
    one structure for both "just settled" and "opened the detail".
    """
    config = _ENTITIES['income']
    income = get_object_or_404(
        config['model'].objects.select_related(
            'client', 'client__user', 'project',
        ).annotate(**config['annotations']),
        pk=record_id,
    )
    children = income.liquid_records.filter(
        kind=IncomeRecord.Kind.LIQUID,
    ).select_related('client', 'client__user', 'project').order_by(
        'period_date', 'id',
    )
    # Deductions credit the gross total without ever arriving as a liquid
    # child, so the history is incomplete without them.
    deductions = income.deduction_records.exclude(
        deduction_type='',
    ).order_by('period_date', 'id')
    cuenta = (
        income.collection_documents
        .exclude(commercial_status=Document.CommercialStatus.CANCELLED)
        .order_by('-created_at')
        .first()
    )
    return Response({
        'income': config['read'](income).data,
        'liquid': IncomeRecordSerializer(children, many=True).data,
        'expenses': ExpenseRecordSerializer(deductions, many=True).data,
        'collection_account': {
            'id': cuenta.pk,
            'public_number': cuenta.public_number,
            'commercial_status': cuenta.commercial_status,
            'total': cuenta.total,
            'issue_date': cuenta.issue_date,
            'due_date': cuenta.due_date,
        } if cuenta else None,
    })


@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_client_projects(request):
    """Projects to pick from, optionally scoped to one client.

    A panel endpoint of its own instead of reusing /api/accounts/projects/:
    that one speaks User ids while the accounting module speaks UserProfile
    ids everywhere, it is IsAuthenticated rather than IsSuperUser, and its
    serializer runs several per-row aggregates that a dropdown has no use for.
    """
    qs = Project.objects.all().order_by('name')
    client_profile_id = request.query_params.get('client')
    if client_profile_id:
        # The picker is scoped by UserProfile, the project by User.
        qs = qs.filter(client__profile__id=client_profile_id)
    return Response({'results': [
        {
            'id': project.pk,
            'name': project.name,
            'status': project.status,
            'status_label': project.status_display,
        }
        for project in qs
    ]})


def _update_record(request, key, record_id):
    config = _ENTITIES[key]
    instance = get_object_or_404(config['model'], pk=record_id)
    serializer = config['write'](
        instance, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        instance = accounting_service.update_record(
            config['entity_type'], instance, serializer, request.user,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    return Response(config['read'](instance).data)


def _delete_record(request, key, record_id):
    config = _ENTITIES[key]
    instance = get_object_or_404(config['model'], pk=record_id)
    try:
        accounting_service.delete_record(
            config['entity_type'], instance, request.user,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Dashboard ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def accounting_dashboard(request):
    """Aggregated summary feeding the accounting dashboard."""
    year_param = request.query_params.get('year') or ''
    try:
        year = int(year_param) if year_param else today_bogota().year
    except (TypeError, ValueError):
        return error_response("El parámetro 'year' debe ser un año válido.")
    return Response(accounting_service.dashboard_summary(year))


@api_view(['GET'])
@permission_classes([IsSuperUser])
def accounting_stats(request):
    """Descriptive statistics feeding the analytics modals."""
    year_param = request.query_params.get('year') or ''
    try:
        year = int(year_param) if year_param else today_bogota().year
    except (TypeError, ValueError):
        return error_response("El parámetro 'year' debe ser un año válido.")
    return Response(accounting_service.year_descriptive_stats(year))


# ── Incomes ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_income_records(request):
    return _list_records(request, 'income')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_income_record(request):
    return _create_record(request, 'income')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def settle_income_record(request, record_id):
    """Liquidate an expected income and resolve its shortfall in one step.

    With empty `deductions`/`expected_incomes` this behaves exactly like
    creating a liquid child through the plain create endpoint.
    """
    income = get_object_or_404(IncomeRecord, pk=record_id)
    serializer = IncomeSettlementSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        result = accounting_settlement_service.settle_expected_income(
            income, serializer.validated_data, request.user,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    # Explicit None: DRF serializes a None instance as {} via get_initial().
    return Response({
        'income': IncomeRecordSerializer(result['income']).data,
        'liquid': (
            IncomeRecordSerializer(result['liquid']).data
            if result['liquid'] is not None else None
        ),
        'expenses': ExpenseRecordSerializer(result['expenses'], many=True).data,
        'expected_incomes': IncomeRecordSerializer(
            result['expected_incomes'], many=True,
        ).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def mute_income_reminders(request, record_id):
    """Silence (or resume) the payment-calendar notices of one expected income.

    For the cases where the delay is already known and the daily reminder is
    only noise. `until` schedules the resume, so nothing gets silenced and
    forgotten; without it the mute lasts until it is lifted by hand.
    """
    income = get_object_or_404(IncomeRecord, pk=record_id)
    if income.kind != IncomeRecord.Kind.EXPECTED:
        return error_response(
            'Solo se pueden silenciar los avisos de un ingreso esperado.',
        )
    serializer = IncomeReminderMuteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    income = accounting_income_mute_service.set_income_reminder_mute(
        income,
        muted=serializer.validated_data['muted'],
        until=serializer.validated_data.get('until'),
        user=request.user,
    )
    return Response(IncomeRecordSerializer(income).data)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def duplicate_income_draft(request, record_id):
    """Prefill for duplicating an income, so the next period is one click.

    Persists nothing: the panel opens its form with this payload and the
    record is created through the ordinary create endpoint after the date and
    the amount are confirmed.
    """
    income = get_object_or_404(IncomeRecord, pk=record_id)
    return Response(
        accounting_income_duplicate_service.build_income_duplicate_draft(income),
    )


def _missing_records_error(entity_type, record_ids, *, noun):
    """409 naming every id that vanished, or ``None`` when they all exist.

    A mass edit is confirmed against a named scope, so it runs on that scope
    or not at all: writing the surviving half of a batch the operator never
    agreed to is worse than asking them to look again. Runs BEFORE the
    service, so its atomic block never opens.

    The panel cannot close this window on its own — the confirmation dialog
    freezes the plan when it opens, and the list can be refetched (or another
    session can delete a row) while it sits there. `missing_ids` is what lets
    the UI drop exactly those ids instead of guessing.
    """
    missing = accounting_service.missing_record_ids(entity_type, record_ids)
    if not missing:
        return None
    count = len(missing)
    verb = 'existe' if count == 1 else 'existen'
    return error_response(
        f'{count} de los {noun} seleccionados ya no {verb}.',
        code='records_not_found',
        hint='La lista se actualizó. Revisa la selección y vuelve a intentarlo.',
        status=status.HTTP_409_CONFLICT,
        errors={'missing_ids': missing},
    )


@api_view(['POST'])
@permission_classes([IsSuperUser])
def bulk_assign_income_client(request):
    """Assign one client to several incomes at once (or clear it with null).

    The completion tool for records created before the client link existed:
    filter by "sin cliente", select the rows and assign in one step.
    """
    serializer = IncomeClientBulkAssignSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    income_ids = serializer.validated_data['income_ids']
    # Before reading `client`, so unlinking is held to the same contract.
    vanished = _missing_records_error(
        EntityType.INCOME, income_ids, noun='ingresos',
    )
    if vanished:
        return vanished
    updated = accounting_service.bulk_assign_client(
        EntityType.INCOME,
        income_ids,
        serializer.validated_data.get('client'),
        request.user,
    )
    return Response({
        'updated': len(updated),
        'results': IncomeRecordSerializer(updated, many=True).data,
    })


@api_view(['POST'])
@permission_classes([IsSuperUser])
def bulk_assign_hosting_client(request):
    """Assign one client to several hostings at once (or clear it with null).

    Same completion path as incomes: filter by "sin cliente", select the
    rows and assign in one step.
    """
    serializer = HostingClientBulkAssignSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    hosting_ids = serializer.validated_data['hosting_ids']
    vanished = _missing_records_error(
        EntityType.HOSTING, hosting_ids, noun='hostings',
    )
    if vanished:
        return vanished
    updated = accounting_service.bulk_assign_client(
        EntityType.HOSTING,
        hosting_ids,
        serializer.validated_data.get('client'),
        request.user,
    )
    return Response({
        'updated': len(updated),
        'results': HostingRecordSerializer(updated, many=True).data,
    })


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_income_record(request, record_id):
    return _retrieve_record(request, 'income', record_id)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_income_record(request, record_id):
    return _update_record(request, 'income', record_id)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_income_record(request, record_id):
    return _delete_record(request, 'income', record_id)


# ── Expenses ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_expense_records(request):
    return _list_records(request, 'expense')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_expense_record(request):
    return _create_record(request, 'expense')


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_expense_record(request, record_id):
    return _retrieve_record(request, 'expense', record_id)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_expense_record(request, record_id):
    return _update_record(request, 'expense', record_id)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_expense_record(request, record_id):
    return _delete_record(request, 'expense', record_id)


# ── Hostings ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_hosting_records(request):
    return _list_records(request, 'hosting')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_hosting_record(request):
    return _create_record(request, 'hosting')


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_hosting_record(request, record_id):
    return _retrieve_record(request, 'hosting', record_id)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_hosting_record(request, record_id):
    return _update_record(request, 'hosting', record_id)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_hosting_record(request, record_id):
    return _delete_record(request, 'hosting', record_id)


# ── Hosting cycles (payment history) ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_hosting_cycles(request, record_id):
    hosting = get_object_or_404(HostingRecord, pk=record_id)
    serializer = HostingCycleSerializer(hosting.cycles.all(), many=True)
    return Response({'results': serializer.data})


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_hosting_cycle(request, record_id):
    from content.services import hosting_cycle_service

    hosting = get_object_or_404(HostingRecord, pk=record_id)
    serializer = HostingCycleCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    cycle = hosting_cycle_service.register_cycle_payment(
        hosting, data=serializer.validated_data, user=request.user,
    )
    return Response(
        {
            'cycle': HostingCycleSerializer(cycle).data,
            'hosting': HostingRecordSerializer(hosting).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_hosting_cycle(request, record_id, cycle_id):
    from content.services import hosting_cycle_service

    hosting = get_object_or_404(HostingRecord, pk=record_id)
    cycle = get_object_or_404(hosting.cycles, pk=cycle_id)
    hosting_cycle_service.delete_cycle(hosting, cycle, user=request.user)
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Pocket movements ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_pocket_movements(request):
    return _list_records(request, 'pocket')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_pocket_movement(request):
    return _create_record(request, 'pocket')


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_pocket_movement(request, record_id):
    return _retrieve_record(request, 'pocket', record_id)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_pocket_movement(request, record_id):
    return _update_record(request, 'pocket', record_id)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_pocket_movement(request, record_id):
    return _delete_record(request, 'pocket', record_id)


# ── Recurring payments ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_recurring_payments(request):
    return _list_records(request, 'recurring')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_recurring_payment(request):
    return _create_record(request, 'recurring')


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_recurring_payment(request, record_id):
    return _retrieve_record(request, 'recurring', record_id)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_recurring_payment(request, record_id):
    return _update_record(request, 'recurring', record_id)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_recurring_payment(request, record_id):
    return _delete_record(request, 'recurring', record_id)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def reorder_recurring_payments(request):
    """Persist the manual order the operator dragged into place.

    Body: {"items": [{"id": 5, "category": 3, "order": 0}, ...]}

    Each item carries its category because a drag can move a row *between*
    groups, not just within one. Unknown ids are ignored so a stale tab
    cannot 404 the whole batch.

    Deliberately does not write an AccountingChangeLog entry: dragging rows
    around is presentation, and logging it would bury the real edits.
    """
    items = request.data.get('items', [])
    if not isinstance(items, list):
        return error_response(
            'Debe ser una lista.',
            code='invalid_reorder_payload',
            status=status.HTTP_400_BAD_REQUEST,
        )

    by_id = {}
    for item in items:
        if not isinstance(item, dict):
            return error_response(
                'Cada elemento debe ser un objeto con id, category y order.',
                code='invalid_reorder_payload',
                status=status.HTTP_400_BAD_REQUEST,
            )
        by_id[item.get('id')] = item

    payments = RecurringPayment.objects.filter(pk__in=[k for k in by_id if k is not None])
    valid_category_ids = set(
        RecurringCategory.objects.values_list('pk', flat=True)
    )

    updated = []
    for payment in payments:
        item = by_id[payment.pk]
        try:
            payment.order = int(item.get('order') or 0)
        except (TypeError, ValueError):
            return error_response(
                'El orden debe ser un número entero.',
                code='invalid_reorder_payload',
                status=status.HTTP_400_BAD_REQUEST,
            )
        if 'category' in item:
            category_id = item['category']
            if category_id is not None and category_id not in valid_category_ids:
                return error_response(
                    'La categoría indicada no existe.',
                    code='unknown_category',
                    status=status.HTTP_400_BAD_REQUEST,
                )
            payment.category_id = category_id
        updated.append(payment)

    with transaction.atomic():
        RecurringPayment.objects.bulk_update(updated, ['category', 'order'])

    return Response({'reordered': len(updated)})


# ── Ads spend ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_ads_spend_records(request):
    return _list_records(request, 'ads')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_ads_spend_record(request):
    return _create_record(request, 'ads')


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_ads_spend_record(request, record_id):
    return _retrieve_record(request, 'ads', record_id)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_ads_spend_record(request, record_id):
    return _update_record(request, 'ads', record_id)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_ads_spend_record(request, record_id):
    return _delete_record(request, 'ads', record_id)


# ── Credit-card catalog ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_credit_cards(request):
    return _list_records(request, 'credit_card')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_credit_card(request):
    return _create_record(request, 'credit_card')


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_credit_card(request, record_id):
    return _retrieve_record(request, 'credit_card', record_id)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_credit_card(request, record_id):
    return _update_record(request, 'credit_card', record_id)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_credit_card(request, record_id):
    """Delete a catalog card unless history references its name.

    Snapshots/statements keep plain-string card names; deleting a card
    they reference would orphan that history in the UI filters, so the
    card must be deactivated instead.
    """
    instance = get_object_or_404(CreditCard, pk=record_id)
    referenced = (
        CardBalanceSnapshot.objects.filter(card_name=instance.name).exists()
        or CreditCardStatement.objects.filter(card_name=instance.name).exists()
    )
    if referenced:
        return error_response(
            'La tarjeta tiene registros o extractos asociados; '
            'desactívala en lugar de eliminarla.',
            code='credit_card_referenced',
        )
    return _delete_record(request, 'credit_card', record_id)


# ── Card snapshots ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_card_snapshots(request):
    return _list_records(request, 'card_snapshot')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_card_snapshot(request):
    return _create_record(request, 'card_snapshot')


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_card_snapshot(request, record_id):
    return _retrieve_record(request, 'card_snapshot', record_id)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_card_snapshot(request, record_id):
    return _update_record(request, 'card_snapshot', record_id)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_card_snapshot(request, record_id):
    return _delete_record(request, 'card_snapshot', record_id)


# ── Change log (paginated) ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_accounting_change_logs(request):
    """Audit trail, paginated 20 per page (it grows unbounded)."""
    params = request.query_params
    try:
        logs = accounting_history_service.change_log_queryset(params)
    except ValueError as exc:
        return error_response_from_exc(exc)

    return _paginated_history_response(
        logs, params, AccountingChangeLogSerializer,
    )


# ── Notification recipients ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_notification_recipients(request):
    return _list_records(request, 'notification_recipient')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_notification_recipient(request):
    return _create_record(request, 'notification_recipient')


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_notification_recipient(request, record_id):
    return _retrieve_record(request, 'notification_recipient', record_id)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_notification_recipient(request, record_id):
    return _update_record(request, 'notification_recipient', record_id)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_notification_recipient(request, record_id):
    return _delete_record(request, 'notification_recipient', record_id)


# ── Email send log (paginated) ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_accounting_email_logs(request):
    """Which addresses each automated email of the module went out to.

    Scoped to the module's own template keys so the proposal traffic that
    shares the EmailLog table stays out. Paginated 20 per page like the
    change log — it grows unbounded.
    """
    params = request.query_params
    try:
        logs = accounting_history_service.email_log_queryset(params)
    except ValueError as exc:
        return error_response_from_exc(exc)

    return _paginated_history_response(
        logs.prefetch_related('targets'), params, EmailLogSerializer,
    )


@api_view(['GET'])
@permission_classes([IsSuperUser])
def accounting_email_log_body(request, log_id):
    """The message as it went out.

    The history exists to diagnose, and without the body it can only confirm
    that something was sent, not what. Scoped to the module's own notices so
    this never becomes a reader for the proposal traffic sharing the table.
    """
    log = get_object_or_404(
        EmailLog.objects.select_related('body'),
        id=log_id,
        template_key__in=EMAIL_TEMPLATE_LABELS,
    )
    if log.body is None:
        return error_response(
            'Este envío es anterior a que se guardara el cuerpo de los '
            'correos, así que no hay nada que mostrar.',
            code='body_not_stored',
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response({
        'id': log.id,
        'subject': log.subject,
        'recipient': log.recipient,
        'sent_at': log.sent_at,
        'html': log.body.html,
        'text': log.body.text,
    })


@api_view(['POST'])
@permission_classes([IsSuperUser])
def retry_accounting_email_log(request, log_id):
    """Re-send a failed notice to the address on the row, and only to it."""
    log = get_object_or_404(
        EmailLog, id=log_id, template_key__in=EMAIL_TEMPLATE_LABELS,
    )
    try:
        attempt = accounting_email_retry_service.retry_send(log)
    except accounting_email_retry_service.RetryError as exc:
        return error_response(str(exc))
    return Response(EmailLogSerializer(attempt).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def accounting_history_tab_counts(request):
    """How many rows each tab of the strip would show.

    The other accounting views count their tabs in the browser over the rows
    they already loaded; Historial is the one that paginates server-side, so
    an honest badge — including the (0) — has to be asked for.

    One COUNT per tab rather than a single conditional aggregate: the send
    log joins its targets, so a digest naming fifty records would fan the
    joined rowset out fifty times under a shared aggregate. Each count is an
    indexed lookup, and the specs are capped.
    """
    scope = request.data.get('scope')
    tabs = request.data.get('tabs')
    if not isinstance(tabs, list):
        return error_response("El parámetro 'tabs' debe ser una lista.")
    if len(tabs) > MAX_TAB_COUNT_SPECS:
        return error_response(
            f'Máximo {MAX_TAB_COUNT_SPECS} pestañas por consulta.',
        )

    counts = {}
    for spec in tabs:
        if not isinstance(spec, dict) or spec.get('id') in (None, ''):
            continue
        try:
            queryset = accounting_history_service.queryset_for(
                scope, spec.get('filters') or {},
            )
        except ValueError as exc:
            return error_response_from_exc(exc)
        counts[str(spec['id'])] = queryset.count()

    return Response({'counts': counts})


# ── Settings ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def get_accounting_settings(request):
    return Response(
        AccountingSettingsSerializer(AccountingSettings.load()).data,
    )


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_accounting_settings(request):
    instance = AccountingSettings.load()
    serializer = AccountingSettingsSerializer(
        instance, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        instance = accounting_service.update_record(
            EntityType.SETTINGS, instance, serializer, request.user,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    return Response(AccountingSettingsSerializer(instance).data)
