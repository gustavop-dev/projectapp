"""Engagement analytics for the WebAppDiagnostic feature.

Extracted verbatim from ``content/views/diagnostic.py`` so the view layer stays
thin. This module must NOT import from ``content.views.*``; the views import
this service. The response shape of :func:`build_diagnostic_analytics` is a
contract guarded by ``content/tests/views/test_diagnostic_analytics.py`` — do
not reorder or rename keys.
"""

from datetime import timedelta

from django.db.models import Avg, Count, Min, Sum
from django.utils import timezone

from content.models import (
    DiagnosticSectionView,
    DiagnosticViewEvent,
    WebAppDiagnostic,
)


# ── Engagement score weights (were inline magic numbers in the view) ─────────
# Values are locked by test_diagnostic_analytics.py — changing them changes the
# score contract.
ENGAGEMENT_RECENT_WINDOW_DAYS = 7
ENGAGEMENT_RECENT_PER_SESSION = 8
ENGAGEMENT_RECENT_CAP = 25
ENGAGEMENT_COVERAGE_CAP = 20
ENGAGEMENT_COST_SECTION_TYPE = 'cost'
ENGAGEMENT_COST_TIME_HIGH = 30
ENGAGEMENT_COST_TIME_MID = 10
ENGAGEMENT_TOTAL_TIME_HIGH = 120
ENGAGEMENT_TOTAL_TIME_MID = 40
ENGAGEMENT_IP_PER_STAKEHOLDER = 8
ENGAGEMENT_IP_CAP = 15
ENGAGEMENT_REVISIT_PER_SESSION = 4
ENGAGEMENT_REVISIT_CAP = 10
ENGAGEMENT_ACTIVE_STATUS_BONUS = 15

_ACTIVE_ENGAGEMENT_STATUSES = frozenset({
    WebAppDiagnostic.Status.ACCEPTED,
    WebAppDiagnostic.Status.FINISHED,
    WebAppDiagnostic.Status.NEGOTIATING,
})


def _latest_section_titles(diagnostic):
    """Map section_type → most recent section_title in ONE pass.

    Replaces the per-section title subquery (an N+1). A single
    ``order_by('-entered_at')`` scan means the first value seen per type is the
    latest, so ``setdefault`` keeps it.
    """
    latest = {}
    rows = (
        DiagnosticSectionView.objects
        .filter(view_event__diagnostic=diagnostic)
        .order_by('-entered_at')
        .values_list('section_type', 'section_title')
    )
    for section_type, section_title in rows:
        latest.setdefault(section_type, section_title)
    return latest


def section_engagement(diagnostic, *, with_reach=False):
    """Per-section aggregation with resolved (non-N+1) titles.

    Returns a list of dicts ``{section_type, section_title, visit_count,
    total_time_seconds, avg_time_seconds}``. When *with_reach* is True each row
    also carries ``reached_sessions`` (distinct sessions) — used by the funnel.
    Shared by both the analytics endpoint and the CSV export.
    """
    annotations = {
        'visit_count': Count('id'),
        'total_time_seconds': Sum('time_spent_seconds'),
        'avg_time_seconds': Avg('time_spent_seconds'),
    }
    if with_reach:
        annotations['reached_sessions'] = Count(
            'view_event__session_id', distinct=True,
        )
    stats = (
        DiagnosticSectionView.objects
        .filter(view_event__diagnostic=diagnostic)
        .values('section_type')
        .annotate(**annotations)
        .order_by('section_type')
    )
    latest_titles = _latest_section_titles(diagnostic)

    rows = []
    for stat in stats:
        row = {
            'section_type': stat['section_type'],
            'section_title': (
                latest_titles.get(stat['section_type'])
                or stat['section_type']
            ),
            'visit_count': stat['visit_count'],
            'total_time_seconds': round(stat['total_time_seconds'] or 0, 1),
            'avg_time_seconds': round(stat['avg_time_seconds'] or 0, 1),
        }
        if with_reach:
            row['reached_sessions'] = stat['reached_sessions']
        rows.append(row)
    return rows


def session_history(diagnostic, *, limit):
    """Recent sessions with their section counts (parametrized limit)."""
    events = (
        diagnostic.view_events.order_by('-viewed_at')
        .prefetch_related('section_views')[:limit]
    )
    history = []
    for event in events:
        section_views = list(event.section_views.all())
        history.append({
            'session_id': event.session_id,
            'ip_address': event.ip_address or '',
            'viewed_at': event.viewed_at.isoformat(),
            'sections_viewed': len(section_views),
            'total_time_seconds': round(
                sum(sv.time_spent_seconds for sv in section_views), 1,
            ),
        })
    return history


def compute_engagement_score(
    diagnostic, view_events, sections_data, unique_sessions,
    first_viewed_at, coverage_ratio,
):
    """Engagement score (0-100) for a diagnostic.

    Distribution:
    - Recent sessions (last 7 days): 0-25 pts
    - Section coverage ratio (visited / total enabled): 0-20 pts
    - Time on cost section + total reading time: 0-15 pts
    - Unique stakeholders (IPs): 0-15 pts
    - Inverse days-without-response: 0-15 pts
    - Re-visits (sessions > 1): 0-10 pts
    """
    score = 0

    seven_days_ago = timezone.now() - timedelta(days=ENGAGEMENT_RECENT_WINDOW_DAYS)
    recent = view_events.filter(viewed_at__gte=seven_days_ago).count()
    score += min(ENGAGEMENT_RECENT_CAP, recent * ENGAGEMENT_RECENT_PER_SESSION)

    score += round(min(ENGAGEMENT_COVERAGE_CAP, (coverage_ratio or 0) * 20))

    total_time = sum(s.get('total_time_seconds', 0) for s in sections_data)
    cost_time = sum(
        s.get('total_time_seconds', 0)
        for s in sections_data
        if s.get('section_type') == ENGAGEMENT_COST_SECTION_TYPE
    )
    if total_time > 0:
        if cost_time >= ENGAGEMENT_COST_TIME_HIGH:
            score += 10
        elif cost_time >= ENGAGEMENT_COST_TIME_MID:
            score += 5
        if total_time >= ENGAGEMENT_TOTAL_TIME_HIGH:
            score += 5
        elif total_time >= ENGAGEMENT_TOTAL_TIME_MID:
            score += 3

    unique_ips = (
        view_events.exclude(ip_address__isnull=True)
        .exclude(ip_address='')
        .values('ip_address').distinct().count()
    )
    score += min(ENGAGEMENT_IP_CAP, unique_ips * ENGAGEMENT_IP_PER_STAKEHOLDER)

    if diagnostic.status == WebAppDiagnostic.Status.SENT and first_viewed_at:
        days_since = (timezone.now() - first_viewed_at).days
        if days_since <= 1:
            score += 15
        elif days_since <= 3:
            score += 10
        elif days_since <= 7:
            score += 5
    elif diagnostic.status in _ACTIVE_ENGAGEMENT_STATUSES:
        score += ENGAGEMENT_ACTIVE_STATUS_BONUS

    if unique_sessions > 1:
        score += min(
            ENGAGEMENT_REVISIT_CAP,
            (unique_sessions - 1) * ENGAGEMENT_REVISIT_PER_SESSION,
        )

    return min(100, score)


def _global_comparison(diagnostic):
    """Averages across all OTHER diagnostics (single aggregate map, no N+1)."""
    other_qs = WebAppDiagnostic.objects.exclude(pk=diagnostic.pk)
    first_views_map = dict(
        DiagnosticViewEvent.objects
        .filter(diagnostic__in=other_qs)
        .values_list('diagnostic_id')
        .annotate(first_viewed=Min('viewed_at'))
        .values_list('diagnostic_id', 'first_viewed')
    )

    ttfv_values = []
    ttr_values = []
    for diag_id, initial_sent, responded in other_qs.values_list(
        'id', 'initial_sent_at', 'responded_at',
    ):
        first = first_views_map.get(diag_id)
        if first and initial_sent:
            ttfv_values.append((first - initial_sent).total_seconds())
        if first and responded:
            ttr_values.append((responded - first).total_seconds())

    avg_ttfv = (
        round(sum(ttfv_values) / len(ttfv_values) / 3600, 1)
        if ttfv_values else None
    )
    avg_ttr = (
        round(sum(ttr_values) / len(ttr_values) / 3600, 1)
        if ttr_values else None
    )
    avg_views_agg = (
        other_qs.filter(view_count__gt=0).aggregate(avg=Avg('view_count'))['avg']
    )
    avg_views = round(avg_views_agg, 1) if avg_views_agg is not None else None

    return {
        'avg_time_to_first_view_hours': avg_ttfv,
        'avg_time_to_response_hours': avg_ttr,
        'avg_views': avg_views,
    }


def _device_breakdown(view_events):
    """Classify sessions by device. Tablet is checked before mobile because
    iPad user-agents contain "Mobile"."""
    counts = {'desktop': 0, 'mobile': 0, 'tablet': 0}
    for ua in view_events.values_list('user_agent', flat=True):
        ua_lower = (ua or '').lower()
        if 'tablet' in ua_lower or 'ipad' in ua_lower:
            counts['tablet'] += 1
        elif 'mobile' in ua_lower or 'android' in ua_lower:
            counts['mobile'] += 1
        else:
            counts['desktop'] += 1
    return counts


def build_diagnostic_analytics(diagnostic):
    """Aggregated engagement analytics dict for a diagnostic.

    Shape mirrors ``build_proposal_analytics`` minus view modes, technical
    subsections and share links (no equivalent data model for diagnostics).
    """
    view_events = diagnostic.view_events.all()
    unique_sessions = view_events.values('session_id').distinct().count()

    first_viewed_at = (
        view_events.order_by('viewed_at')
        .values_list('viewed_at', flat=True)
        .first()
    )
    last_viewed_at = (
        view_events.order_by('-viewed_at')
        .values_list('viewed_at', flat=True)
        .first()
    )

    time_to_first_view = None
    if diagnostic.initial_sent_at and first_viewed_at:
        delta = (first_viewed_at - diagnostic.initial_sent_at).total_seconds()
        time_to_first_view = round(delta / 3600, 1)

    time_to_response = None
    if first_viewed_at and diagnostic.responded_at:
        delta = (diagnostic.responded_at - first_viewed_at).total_seconds()
        time_to_response = round(delta / 3600, 1)

    sections_data = section_engagement(diagnostic, with_reach=True)
    visited_types = {s['section_type'] for s in sections_data}
    section_reach = {
        s['section_type']: s['reached_sessions'] for s in sections_data
    }
    # The public analytics payload does not expose reached_sessions per row.
    for row in sections_data:
        row.pop('reached_sessions', None)

    enabled_sections = list(
        diagnostic.sections
        .filter(is_enabled=True)
        .order_by('order')
        .values_list('section_type', 'title')
    )
    skipped_sections = [
        {'section_type': st, 'section_title': title}
        for st, title in enabled_sections
        if st not in visited_types
    ]

    device_counts = _device_breakdown(view_events)
    sessions_data = session_history(diagnostic, limit=50)

    timeline = [
        {
            'change_type': log.change_type,
            'field_name': log.field_name,
            'old_value': log.old_value,
            'new_value': log.new_value,
            'description': log.description,
            'actor_type': log.actor_type,
            'created_at': log.created_at.isoformat(),
        }
        for log in diagnostic.change_logs.order_by('-created_at')[:50]
    ]

    funnel_data = []
    for section_type, section_title in enabled_sections:
        reached = section_reach.get(section_type, 0)
        drop_off = round(
            (1 - reached / unique_sessions) * 100, 1,
        ) if unique_sessions > 0 else 0
        funnel_data.append({
            'section_type': section_type,
            'section_title': section_title,
            'reached_count': reached,
            'drop_off_percent': drop_off,
        })

    total_enabled = len(enabled_sections)
    coverage_ratio = (
        len(visited_types) / total_enabled if total_enabled > 0 else 0
    )

    engagement_score = compute_engagement_score(
        diagnostic, view_events, sections_data, unique_sessions,
        first_viewed_at, coverage_ratio,
    )

    return {
        'total_views': diagnostic.view_count,
        'unique_sessions': unique_sessions,
        'first_viewed_at': (
            first_viewed_at.isoformat() if first_viewed_at else None
        ),
        'last_viewed_at': (
            last_viewed_at.isoformat() if last_viewed_at else None
        ),
        'time_to_first_view_hours': time_to_first_view,
        'time_to_response_hours': time_to_response,
        'responded_at': (
            diagnostic.responded_at.isoformat()
            if diagnostic.responded_at else None
        ),
        'sections': sections_data,
        'skipped_sections': skipped_sections,
        'device_breakdown': device_counts,
        'sessions': sessions_data,
        'timeline': timeline,
        'funnel': funnel_data,
        'comparison': _global_comparison(diagnostic),
        'engagement_score': engagement_score,
    }
