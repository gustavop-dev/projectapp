"""API views for the accounting module (panel, superuser-only).

All endpoints require an authenticated superuser (IsSuperUser). Lists
return {'results': [...], 'meta': {...}} and are filtered server-side via
shared query params (date_from/date_to/year, amount_min/amount_max,
partner, q) plus per-entity choice filters; rich interactive filtering
happens client-side. The change log is the only paginated endpoint.
"""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from content.api_errors import error_response, error_response_from_exc
from content.models import (
    AccountingChangeLog,
    AccountingSettings,
    AdsSpendRecord,
    CardBalanceSnapshot,
    ExpenseRecord,
    HostingRecord,
    IncomeRecord,
    PocketMovement,
    RecurringPayment,
)
from content.permissions import IsSuperUser
from content.serializers.accounting import (
    TWO_PLACES,
    AccountingChangeLogSerializer,
    AccountingSettingsSerializer,
    AdsSpendRecordCreateUpdateSerializer,
    AdsSpendRecordSerializer,
    CardBalanceSnapshotCreateUpdateSerializer,
    CardBalanceSnapshotSerializer,
    ExpenseRecordCreateUpdateSerializer,
    ExpenseRecordSerializer,
    HostingCycleCreateSerializer,
    HostingCycleSerializer,
    HostingRecordCreateUpdateSerializer,
    HostingRecordSerializer,
    IncomeRecordCreateUpdateSerializer,
    IncomeRecordSerializer,
    PocketMovementCreateUpdateSerializer,
    PocketMovementSerializer,
    RecurringPaymentCreateUpdateSerializer,
    RecurringPaymentSerializer,
)
from content.services import accounting_service
from content.utils import today_bogota

EntityType = AccountingChangeLog.EntityType


def _parse_date(value, param):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"El parámetro '{param}' debe ser una fecha AAAA-MM-DD.")


def _parse_decimal(value, param):
    try:
        return Decimal(value)
    except (TypeError, InvalidOperation):
        raise ValueError(f"El parámetro '{param}' debe ser un número.")


def _money(value):
    return str(Decimal(value).quantize(TWO_PLACES))


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
        'received_pct': received_pct,
        'current_month_liquid': _money(totals['month_liquid'] or 0),
        'top_income': _top_record(year_qs.filter(kind='liquid')),
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
    return {
        'year_total': _money(totals['year_total'] or 0),
        'current_month_total': _money(month_total),
        'business_total': _money(totals['business_total'] or 0),
        'personal_total': _money(totals['personal_total'] or 0),
        'current_month_alert': alert,
        'top_expense': _top_record(year_qs),
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
    )
    return {
        'active_count': totals['active_count'] or 0,
        'monthly_income': _money(totals['monthly_income'] or 0),
        'total_paid': _money(totals['total_paid'] or 0),
        'expiring_soon_count': totals['expiring_soon_count'] or 0,
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
        'search_fields': ('concept', 'notes'),
        'choice_filters': ('kind', 'destination', 'ledger'),
        'has_split': True,
        'pocket_filter': Q(destination=IncomeRecord.Destination.POCKET),
        'meta': _income_meta,
    },
    'expense': {
        'entity_type': EntityType.EXPENSE,
        'model': ExpenseRecord,
        'read': ExpenseRecordSerializer,
        'write': ExpenseRecordCreateUpdateSerializer,
        'date_field': 'period_date',
        'amount_field': 'total_amount',
        'search_fields': ('concept', 'notes'),
        'choice_filters': ('category', 'ledger'),
        'has_split': True,
        'meta': _expense_meta,
    },
    'hosting': {
        'entity_type': EntityType.HOSTING,
        'model': HostingRecord,
        'read': HostingRecordSerializer,
        'write': HostingRecordCreateUpdateSerializer,
        'date_field': 'valid_from',
        'amount_field': 'monthly_value',
        'search_fields': ('client_name', 'domain_url', 'notes'),
        'choice_filters': ('payment_modality',),
        'bool_filters': ('is_active',),
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
            'frequency', 'cost_type', 'currency', 'payment_method',
        ),
        'bool_filters': ('is_active',),
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
}


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
    if params.get('amount_min'):
        queryset = queryset.filter(**{
            f'{amount_field}__gte': _parse_decimal(
                params['amount_min'], 'amount_min',
            ),
        })
    if params.get('amount_max'):
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
            if len(values) > 1:
                queryset = queryset.filter(**{f'{field}__in': values})
            elif values:
                queryset = queryset.filter(**{field: values[0]})

    for field in config.get('bool_filters', ()):
        value = params.get(field)
        if value in ('true', 'false'):
            queryset = queryset.filter(**{field: value == 'true'})

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
    queryset = config['model'].objects.all()
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


# ── Incomes ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_income_records(request):
    return _list_records(request, 'income')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_income_record(request):
    return _create_record(request, 'income')


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
    logs = AccountingChangeLog.objects.select_related('actor').all()
    params = request.query_params
    try:
        if params.get('entity_type'):
            logs = logs.filter(entity_type=params['entity_type'])
        if params.get('object_id'):
            logs = logs.filter(object_id=params['object_id'])
        if params.get('action'):
            logs = logs.filter(action=params['action'])
        if params.get('actor'):
            logs = logs.filter(actor_username__icontains=params['actor'])
        if params.get('date_from'):
            logs = logs.filter(
                created_at__date__gte=_parse_date(
                    params['date_from'], 'date_from',
                ),
            )
        if params.get('date_to'):
            logs = logs.filter(
                created_at__date__lte=_parse_date(
                    params['date_to'], 'date_to',
                ),
            )
    except ValueError as exc:
        return error_response_from_exc(exc)

    total = logs.count()
    try:
        page = max(1, int(params.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    page_size = 20
    offset = (page - 1) * page_size
    num_pages = max(1, -(-total // page_size))

    serializer = AccountingChangeLogSerializer(
        logs[offset:offset + page_size], many=True,
    )
    return Response({
        'results': serializer.data,
        'count': total,
        'page': page,
        'num_pages': num_pages,
    })


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
