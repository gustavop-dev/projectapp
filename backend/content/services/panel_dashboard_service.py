"""Global panel dashboard: consolidated KPIs across modules.

Single payload for ``GET /api/panel/dashboard/`` combining finance
(accounting, superuser-gated by the caller), proposals (cheap core) and
operations (tasks, documents, diagnostics, emails, hour packages), plus
the cross-module "attention" list that powers the dashboard radar.
"""

from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from content.models import (
    BusinessProposal,
    Document,
    EmailLog,
    HostingRecord,
    HourPackage,
    RecurringPayment,
    Task,
    WebAppDiagnostic,
)
from content.services import accounting_service
from content.services.proposal_analytics_service import build_dashboard_core
from content.utils import today_bogota

EMAIL_FAILED_STATUSES = (EmailLog.Status.FAILED, EmailLog.Status.BOUNCED)
EMAIL_OK_STATUSES = (EmailLog.Status.SENT, EmailLog.Status.DELIVERED)

# Proposals sent this long ago without a first view feed the attention radar.
STALE_PROPOSAL_DAYS = 7
# Recurring payments billed within this window feed the attention radar.
RECURRING_DUE_DAYS = 7

_SEVERITY_RANK = {'danger': 0, 'warning': 1, 'info': 2}


def _finance_block(year):
    hostings = HostingRecord.objects.aggregate(
        active_count=Count('id', filter=Q(is_active=True)),
        monthly_income=Sum('monthly_value', filter=Q(is_active=True)),
        total_paid=Sum('total_paid'),
    )
    return {
        'year': year,
        **accounting_service.year_totals(year),
        'pocket_balance': accounting_service.pocket_balance(),
        'expected_current_month': accounting_service.expected_current_month(),
        'card_debt': accounting_service.card_debt_total(),
        'recurring_monthly_cost': accounting_service.recurring_monthly_cost(),
        'hostings': {
            'active_count': hostings['active_count'] or 0,
            'monthly_income': hostings['monthly_income'] or 0,
            'total_paid': hostings['total_paid'] or 0,
        },
        'monthly': accounting_service.monthly_breakdown(year),
    }


def _tasks_summary(today):
    not_done = ~Q(status=Task.Status.DONE)
    return Task.objects.filter(is_archived=False).aggregate(
        open=Count('id', filter=not_done),
        overdue=Count('id', filter=Q(due_date__lt=today) & not_done),
        overdue_high=Count(
            'id',
            filter=Q(due_date__lt=today, priority=Task.Priority.HIGH) & not_done,
        ),
        blocked=Count('id', filter=Q(status=Task.Status.BLOCKED)),
        high_priority_open=Count(
            'id', filter=Q(priority=Task.Priority.HIGH) & not_done,
        ),
    )


def _status_counts(model, queryset=None):
    counts = dict(
        (queryset if queryset is not None else model.objects.all())
        .values_list('status')
        .annotate(c=Count('id'))
        .values_list('status', 'c')
    )
    return {value: counts.get(value, 0) for value, _label in model.Status.choices}


def _documents_summary(today):
    collection = Document.objects.filter(
        commercial_status=Document.CommercialStatus.ISSUED,
    ).aggregate(
        issued_count=Count('id'),
        overdue_issued=Count('id', filter=Q(due_date__lt=today)),
        outstanding_total=Sum('total'),
    )
    return {
        'by_status': _status_counts(Document),
        'collection_accounts': {
            'issued_count': collection['issued_count'] or 0,
            'overdue_issued': collection['overdue_issued'] or 0,
            'outstanding_total': collection['outstanding_total'] or 0,
        },
    }


def _diagnostics_summary():
    by_status = _status_counts(WebAppDiagnostic)
    active_pipeline = (
        by_status.get('sent', 0)
        + by_status.get('viewed', 0)
        + by_status.get('negotiating', 0)
    )
    accepted_value = WebAppDiagnostic.objects.filter(
        status__in=(
            WebAppDiagnostic.Status.ACCEPTED,
            WebAppDiagnostic.Status.FINISHED,
        ),
    ).aggregate(total=Sum('investment_amount'))['total'] or 0
    return {
        'by_status': by_status,
        'active_pipeline': active_pipeline,
        'accepted_value': accepted_value,
    }


def _emails_summary(now):
    last_30d = EmailLog.objects.filter(sent_at__gte=now - timedelta(days=30))
    totals = last_30d.aggregate(
        total=Count('id'),
        sent_count=Count('id', filter=Q(status__in=EMAIL_OK_STATUSES)),
        failed_count=Count('id', filter=Q(status__in=EMAIL_FAILED_STATUSES)),
    )
    success_rate = (
        round(totals['sent_count'] / totals['total'] * 100, 1)
        if totals['total'] else None
    )
    trend_rows = (
        EmailLog.objects.filter(sent_at__gte=now - timedelta(days=14))
        .annotate(day=TruncDate('sent_at'))
        .values('day')
        .annotate(
            total=Count('id'),
            failed=Count('id', filter=Q(status__in=EMAIL_FAILED_STATUSES)),
        )
        .order_by('day')
    )
    return {
        'total_30d': totals['total'],
        'sent_count': totals['sent_count'],
        'failed_count': totals['failed_count'],
        'success_rate': success_rate,
        'daily_trend': [
            {
                'date': row['day'].isoformat() if row['day'] else '',
                'total': row['total'],
                'failed': row['failed'],
            }
            for row in trend_rows
        ],
    }


def _operations_block(today, now):
    return {
        'tasks': _tasks_summary(today),
        'documents': _documents_summary(today),
        'diagnostics': _diagnostics_summary(),
        'emails': _emails_summary(now),
        'hour_packages': {
            'active_count': HourPackage.objects.filter(is_active=True).count(),
        },
    }


def _days_until_billing(billing_day, today):
    """Days until the next monthly occurrence of ``billing_day``."""
    import calendar

    def _clamped(year, month):
        return min(billing_day, calendar.monthrange(year, month)[1])

    if today.day <= _clamped(today.year, today.month):
        due_day = _clamped(today.year, today.month)
        return due_day - today.day
    next_month = today.month % 12 + 1
    next_year = today.year + (1 if today.month == 12 else 0)
    due_day = _clamped(next_year, next_month)
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    return days_in_month - today.day + due_day


def _recurring_due_soon(today):
    """Active monthly payments billed within RECURRING_DUE_DAYS."""
    due = []
    payments = RecurringPayment.objects.filter(
        is_active=True,
        frequency=RecurringPayment.Frequency.MONTHLY,
        billing_day__isnull=False,
    )
    for payment in payments:
        days = _days_until_billing(payment.billing_day, today)
        if days <= RECURRING_DUE_DAYS:
            due.append(days)
    return due


def _attention_block(operations, today, now, *, include_finance):
    items = []

    overdue_docs = operations['documents']['collection_accounts']['overdue_issued']
    if overdue_docs:
        items.append({
            'type': 'documents_overdue',
            'severity': 'danger',
            'count': overdue_docs,
            'meta': {},
        })

    failed_emails_7d = EmailLog.objects.filter(
        sent_at__gte=now - timedelta(days=7),
        status__in=EMAIL_FAILED_STATUSES,
    ).count()
    if failed_emails_7d:
        items.append({
            'type': 'emails_failed',
            'severity': 'danger',
            'count': failed_emails_7d,
            'meta': {},
        })

    overdue_tasks = operations['tasks']['overdue']
    if overdue_tasks:
        items.append({
            'type': 'tasks_overdue',
            'severity': 'danger' if operations['tasks']['overdue_high'] else 'warning',
            'count': overdue_tasks,
            'meta': {'high_priority': operations['tasks']['overdue_high']},
        })

    stale_proposals = BusinessProposal.objects.filter(
        status='sent',
        is_active=True,
        first_viewed_at__isnull=True,
        sent_at__lt=now - timedelta(days=STALE_PROPOSAL_DAYS),
    ).count()
    if stale_proposals:
        items.append({
            'type': 'proposals_stale',
            'severity': 'warning',
            'count': stale_proposals,
            'meta': {'days': STALE_PROPOSAL_DAYS},
        })

    if include_finance:
        due_days = _recurring_due_soon(today)
        if due_days:
            next_days = min(due_days)
            items.append({
                'type': 'recurring_due',
                'severity': 'warning' if next_days <= 3 else 'info',
                'count': len(due_days),
                'meta': {'next_days': next_days},
            })

    items.sort(key=lambda item: (_SEVERITY_RANK[item['severity']], -item['count']))
    return items


def build_panel_dashboard(*, include_finance):
    """Consolidated dashboard payload; finance only when the caller allows it."""
    today = today_bogota()
    now = timezone.now()
    operations = _operations_block(today, now)
    return {
        'generated_at': now.isoformat(),
        'finance': _finance_block(today.year) if include_finance else None,
        'proposals': build_dashboard_core(),
        'operations': operations,
        'attention': _attention_block(
            operations, today, now, include_finance=include_finance,
        ),
    }
