"""Proposal analytics, dashboard KPIs, and alerts computation.

Extracted verbatim from ``content/views/proposal.py`` so the view module
keeps only request/response wiring. This module must not import from
``content.views.*`` — views import this service, not the other way around.
"""

from decimal import Decimal

from django.utils import timezone

from content.models import (
    BusinessProposal,
    ProposalAlert,
    ProposalChangeLog,
    ProposalSection,
    ProposalSectionView,
    ProposalViewEvent,
)
from content.serializers.proposal import ProposalShareLinkSerializer
from content.services.proposal_totals_service import build_effective_totals_map

# Public technical mode tracks synthetic panels as technical_document_public;
# the DB section is technical_document. Metrics union both.
TECHNICAL_DOCUMENT_TRACKING_TYPES = frozenset({
    'technical_document',
    'technical_document_public',
})

# Sections that signal commercial intent — used to detect skipped key content.
KEY_PROPOSAL_SECTIONS = frozenset({
    'investment', 'timeline', 'functional_requirements', 'final_note',
})

# Spanish labels for the three client-selectable view modes.
VIEW_MODE_LABELS = {'executive': 'ejecutiva', 'detailed': 'completa', 'technical': 'técnica'}

# Ordered fragments of the technical document panel, matching frontend utils/technicalProposalPanels.js
TECHNICAL_FRAGMENT_ORDER = [
    'intro', 'stack', 'architecture', 'dataModel', 'growthReadiness',
    'epics', 'api', 'integrations', 'environments', 'security',
    'performance', 'backups', 'quality', 'decisions',
]
TECHNICAL_FRAGMENT_TITLES = {
    'intro': 'Detalle técnico',
    'stack': 'Stack tecnológico',
    'architecture': 'Arquitectura',
    'dataModel': 'Modelo de datos',
    'growthReadiness': 'Preparación para el crecimiento',
    'epics': 'Módulos del producto',
    'api': 'API y endpoints',
    'integrations': 'Integraciones',
    'environments': 'Ambientes',
    'security': 'Seguridad',
    'performance': 'Rendimiento y prácticas',
    'backups': 'Backups',
    'quality': 'Calidad y pruebas',
    'decisions': 'Decisiones técnicas',
}


def _ne(v):
    """Non-empty string check (mirrors JS _nonEmptyStr)."""
    return isinstance(v, str) and v.strip() != ''


def _row_has(row, keys):
    """True if *row* is a dict with at least one non-empty string among *keys*."""
    if not isinstance(row, dict):
        return False
    return any(_ne(row.get(k)) for k in keys)


def technical_fragment_has_content(fragment, doc):
    """Python port of frontend technicalFragmentHasContent().

    Returns True when *fragment* has real data inside the technical
    document *doc* (content_json of the technical_document section).
    """
    d = doc if isinstance(doc, dict) else {}

    if fragment == 'intro':
        return True

    if fragment == 'stack':
        rows = d.get('stack')
        return isinstance(rows, list) and any(
            _row_has(r, ('layer', 'technology', 'rationale')) for r in rows
        )

    if fragment == 'architecture':
        arch = d.get('architecture') or {}
        if _ne(arch.get('summary')) or _ne(arch.get('diagramNote')):
            return True
        return any(
            _row_has(r, ('component', 'pattern', 'description'))
            for r in (arch.get('patterns') or [])
        )

    if fragment == 'dataModel':
        dm = d.get('dataModel') or {}
        if _ne(dm.get('summary')) or _ne(dm.get('relationships')):
            return True
        return any(
            _row_has(r, ('name', 'description', 'keyFields'))
            for r in (dm.get('entities') or [])
        )

    if fragment == 'growthReadiness':
        gr = d.get('growthReadiness') or {}
        if _ne(gr.get('summary')):
            return True
        return any(
            _row_has(r, ('dimension', 'preparation', 'evolution'))
            for r in (gr.get('strategies') or [])
        )

    if fragment == 'epics':
        epics = d.get('epics')
        if not isinstance(epics, list):
            return False
        for ep in epics:
            if not isinstance(ep, dict):
                continue
            if _ne(ep.get('title')) or _ne(ep.get('description')) or _ne(ep.get('epicKey')):
                return True
            if any(
                _row_has(rq, ('title', 'description', 'configuration', 'usageFlow', 'flowKey'))
                for rq in (ep.get('requirements') or [])
            ):
                return True
        return False

    if fragment == 'api':
        if _ne(d.get('apiSummary')):
            return True
        domains = d.get('apiDomains')
        return isinstance(domains, list) and any(
            _row_has(r, ('domain', 'summary')) for r in domains
        )

    if fragment == 'integrations':
        integ = d.get('integrations') or {}
        if _ne(integ.get('notes')):
            return True
        return (
            any(_row_has(r, ('service', 'provider', 'connection', 'dataExchange', 'accountOwner'))
                for r in (integ.get('included') or []))
            or any(_row_has(r, ('service', 'reason', 'availability'))
                   for r in (integ.get('excluded') or []))
        )

    if fragment == 'environments':
        if _ne(d.get('environmentsNote')):
            return True
        envs = d.get('environments')
        return isinstance(envs, list) and any(
            _row_has(r, ('name', 'purpose', 'url', 'database', 'whoAccesses')) for r in envs
        )

    if fragment == 'security':
        sec = d.get('security')
        return isinstance(sec, list) and any(
            _row_has(r, ('aspect', 'implementation')) for r in sec
        )

    if fragment == 'performance':
        pq = d.get('performanceQuality') or {}
        return (
            any(_row_has(r, ('metric', 'target', 'howMeasured'))
                for r in (pq.get('metrics') or []))
            or any(_row_has(r, ('strategy', 'description'))
                   for r in (pq.get('practices') or []))
        )

    if fragment == 'backups':
        return _ne(d.get('backupsNote'))

    if fragment == 'quality':
        q = d.get('quality') or {}
        if _ne(q.get('criticalFlowsNote')):
            return True
        return (
            any(_row_has(r, ('dimension', 'evaluates', 'standard'))
                for r in (q.get('dimensions') or []))
            or any(_row_has(r, ('type', 'validates', 'tool', 'whenRun'))
                   for r in (q.get('testTypes') or []))
        )

    if fragment == 'decisions':
        decs = d.get('decisions')
        return isinstance(decs, list) and any(
            _row_has(r, ('decision', 'alternative', 'reason')) for r in decs
        )

    return False


COMPUTED_ALERT_TYPES = frozenset({
    'not_viewed',
    'not_responded',
    'expiring_soon',
    'seller_inactive',
    'zombie',
    'zombie_draft',
    'zombie_sent_stale',
    'late_return',
})
COMPUTED_ALERT_DISMISS_PREFIX = '__computed_dismissed__:'


def computed_alert_key(proposal_id, alert_type, ref_date):
    return f'{proposal_id}-{alert_type}-{ref_date or ""}'


def dashboard_top_dropoff_allowlist():
    """Section types used for global top_dropoff KPI (excludes technical doc)."""
    return frozenset(
        c for c, _ in ProposalSection.SectionType.choices
        if c != 'technical_document'
    )


def csv_analytics_section_group(section_type):
    """Human-readable group for CSV export (technical variants align)."""
    if section_type == 'technical_document_public':
        return 'Detalle técnico (vista pública)'
    if section_type == 'technical_document':
        return 'Detalle técnico'
    return ''


def compute_engagement_score(proposal, view_events, sections_data, unique_sessions):
    """
    Compute engagement score (0-100) for a proposal based on:
    - Recent sessions (last 7 days): 0-25 pts
    - Time on investment section / total time: 0-25 pts
    - Time on technical doc (technical_document + technical_document_public): max 12 pts
    - Number of unique stakeholders (IPs): 0-20 pts
    - Inverse days-without-response: 0-15 pts
    - Re-visits (sessions > 1): 0-15 pts
    """
    from datetime import timedelta
    score = 0

    # 1. Recent sessions (last 7 days) — max 25 pts
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_sessions = view_events.filter(viewed_at__gte=seven_days_ago).count()
    score += min(25, recent_sessions * 8)

    # 2. Time on investment section / total time — max 25 pts
    total_time = sum(s.get('total_time_seconds', 0) for s in sections_data)
    inv_time = sum(
        s.get('total_time_seconds', 0)
        for s in sections_data if s.get('section_type') == 'investment'
    )
    if total_time > 0:
        inv_ratio = inv_time / total_time
        score += min(25, round(inv_ratio * 100))

    # 2b. Technical document reading — max 12 pts (public mode uses synthetic types)
    tech_time = sum(
        s.get('total_time_seconds', 0)
        for s in sections_data
        if s.get('section_type') in TECHNICAL_DOCUMENT_TRACKING_TYPES
    )
    if total_time > 0 and tech_time > 0:
        tech_ratio = tech_time / total_time
        score += min(12, round(tech_ratio * 55))

    # 3. Unique stakeholders (IPs) — max 20 pts
    unique_ips = view_events.exclude(
        ip_address__isnull=True
    ).exclude(ip_address='').values('ip_address').distinct().count()
    score += min(20, unique_ips * 10)

    # 4. Inverse days-without-response — max 15 pts
    if proposal.status in ('sent', 'viewed') and proposal.first_viewed_at:
        days_since = (timezone.now() - proposal.first_viewed_at).days
        if days_since <= 1:
            score += 15
        elif days_since <= 3:
            score += 10
        elif days_since <= 7:
            score += 5
    elif proposal.status in ('accepted', 'finished'):
        score += 15

    # 5. Re-visits (sessions > 1) — max 15 pts
    if unique_sessions > 1:
        score += min(15, (unique_sessions - 1) * 5)

    return min(100, score)


def compute_heat_score_for_proposal(proposal_id, now=None):
    """
    Compute heat score (1-10) for a single proposal for the list view.
    Lightweight version of engagement score.
    """
    result = compute_heat_score_with_summary(proposal_id, now)
    return result['score']


def compute_heat_score_with_summary(proposal_id, now=None):
    """
    Compute heat score (1-10) and engagement summary for the tooltip.
    Returns dict with 'score' and 'engagement_summary'.
    """
    from datetime import timedelta
    from django.db.models import Sum, Max
    if now is None:
        now = timezone.now()

    score = 0
    seven_days_ago = now - timedelta(days=7)

    # Recent sessions (7d) — max 3 pts
    recent = (
        ProposalViewEvent.objects
        .filter(proposal_id=proposal_id, viewed_at__gte=seven_days_ago)
        .count()
    )
    score += min(3, recent)

    # Time on investment section — max 2 pts
    inv_time = (
        ProposalSectionView.objects
        .filter(
            view_event__proposal_id=proposal_id,
            section_type='investment',
        )
        .aggregate(t=Sum('time_spent_seconds'))
    )['t'] or 0
    if inv_time >= 60:
        score += 2
    elif inv_time >= 15:
        score += 1

    # Time on technical document (panel + public synthetic) — max 1 pt
    tech_time = (
        ProposalSectionView.objects
        .filter(
            view_event__proposal_id=proposal_id,
            section_type__in=TECHNICAL_DOCUMENT_TRACKING_TYPES,
        )
        .aggregate(t=Sum('time_spent_seconds'))
    )['t'] or 0
    if tech_time >= 20:
        score += 1

    # Unique IPs — max 2 pts
    unique_ips = (
        ProposalViewEvent.objects
        .filter(proposal_id=proposal_id)
        .exclude(ip_address__isnull=True).exclude(ip_address='')
        .values('ip_address').distinct().count()
    )
    score += min(2, unique_ips)

    # Total views — max 2 pts
    from content.models import BusinessProposal as _BP
    try:
        p = _BP.objects.values(
            'view_count', 'first_viewed_at', 'last_activity_at',
            'engagement_declining',
        ).get(pk=proposal_id)
    except _BP.DoesNotExist:
        return {'score': 1, 'engagement_summary': None}
    if p['view_count'] >= 5:
        score += 2
    elif p['view_count'] >= 2:
        score += 1

    # Recency of last view — max 1 pt
    if p['first_viewed_at'] and (now - p['first_viewed_at']).days <= 3:
        score += 1

    # Engagement declining penalty — -1 pt
    if p.get('engagement_declining'):
        score -= 1

    # Build engagement summary for tooltip
    last_activity = p.get('last_activity_at')
    last_activity_str = None
    if last_activity:
        delta = now - last_activity
        if delta.days == 0:
            hours = delta.seconds // 3600
            last_activity_str = f"hace {hours}h" if hours > 0 else "hace menos de 1h"
        else:
            last_activity_str = f"hace {delta.days}d"

    # Sections viewed vs total enabled
    viewed_types = set(
        ProposalSectionView.objects
        .filter(view_event__proposal_id=proposal_id)
        .values_list('section_type', flat=True)
        .distinct()
    )
    skipped = [s for s in KEY_PROPOSAL_SECTIONS if s not in viewed_types]

    engagement_summary = {
        'views': p['view_count'],
        'last_activity': last_activity_str,
        'investment_time_sec': round(inv_time),
        'technical_time_sec': round(tech_time),
        'technical_viewed': tech_time >= 5,
        'unique_devices': unique_ips,
        'skipped_sections': skipped,
    }

    return {
        'score': max(1, min(10, score)),
        'engagement_summary': engagement_summary,
    }


def build_proposal_analytics(proposal):
    """
    Build aggregated section engagement analytics for a proposal.

    Includes: time-to-first-view, time-to-response, skipped sections,
    device breakdown, per-section engagement, session history, and
    change log timeline.
    """
    from django.db.models import Sum, Count, Avg, Subquery, OuterRef

    view_events = proposal.view_events.all()
    total_views = proposal.view_count
    unique_sessions = view_events.values('session_id').distinct().count()

    # Time-to-first-view (hours)
    time_to_first_view = None
    if proposal.sent_at and proposal.first_viewed_at:
        delta = (proposal.first_viewed_at - proposal.sent_at).total_seconds()
        time_to_first_view = round(delta / 3600, 1)

    # Time-to-response (hours)
    time_to_response = None
    if proposal.first_viewed_at and proposal.responded_at:
        delta = (proposal.responded_at - proposal.first_viewed_at).total_seconds()
        time_to_response = round(delta / 3600, 1)

    # Per-section aggregation
    section_stats = (
        ProposalSectionView.objects
        .filter(view_event__proposal=proposal)
        .values('section_type')
        .annotate(
            visit_count=Count('id'),
            total_time_seconds=Sum('time_spent_seconds'),
            avg_time_seconds=Avg('time_spent_seconds'),
        )
        .order_by('section_type')
    )

    # Enrich with section_title from most recent entry.
    # Single query ordered by -entered_at; first row seen per section_type
    # is its latest title (replaces one query per section type).
    latest_titles = {}
    for section_type, section_title in (
        ProposalSectionView.objects
        .filter(view_event__proposal=proposal)
        .order_by('-entered_at')
        .values_list('section_type', 'section_title')
    ):
        if section_type not in latest_titles:
            latest_titles[section_type] = section_title

    visited_types = set()
    sections_data = []
    for stat in section_stats:
        visited_types.add(stat['section_type'])
        latest = latest_titles.get(stat['section_type'])
        sections_data.append({
            'section_type': stat['section_type'],
            'section_title': latest or stat['section_type'],
            'visit_count': stat['visit_count'],
            'total_time_seconds': round(stat['total_time_seconds'] or 0, 1),
            'avg_time_seconds': round(stat['avg_time_seconds'] or 0, 1),
        })

    technical_reached = bool(
        visited_types & TECHNICAL_DOCUMENT_TRACKING_TYPES
    )
    tech_time_total = sum(
        s.get('total_time_seconds', 0)
        for s in sections_data
        if s.get('section_type') in TECHNICAL_DOCUMENT_TRACKING_TYPES
    )
    technical_sessions_reached = (
        ProposalSectionView.objects
        .filter(
            view_event__proposal=proposal,
            section_type__in=TECHNICAL_DOCUMENT_TRACKING_TYPES,
        )
        .values('view_event__session_id')
        .distinct()
        .count()
    )
    technical_engagement = {
        'total_time_seconds': round(tech_time_total, 1),
        'sessions_reached': technical_sessions_reached,
    }

    # Skipped sections — enabled sections not in tracking data
    enabled_sections = (
        proposal.sections
        .filter(is_enabled=True)
        .values_list('section_type', 'title')
    )
    skipped_sections = []
    for st, title in enabled_sections:
        if st == 'technical_document' and technical_reached:
            continue
        if st not in visited_types:
            skipped_sections.append({
                'section_type': st,
                'section_title': title,
            })

    # Device breakdown from user_agent
    # Check tablet FIRST because iPad UA strings contain "mobile"
    device_counts = {'desktop': 0, 'mobile': 0, 'tablet': 0}
    for ua in view_events.values_list('user_agent', flat=True):
        ua_lower = (ua or '').lower()
        if 'tablet' in ua_lower or 'ipad' in ua_lower:
            device_counts['tablet'] += 1
        elif 'mobile' in ua_lower or 'android' in ua_lower:
            device_counts['mobile'] += 1
        else:
            device_counts['desktop'] += 1

    # Per-session summary
    sessions_data = []
    for event in view_events.order_by('-viewed_at')[:50]:
        sv = event.section_views.all()
        sections_viewed = sv.count()
        total_time = sum(s.time_spent_seconds for s in sv)
        sessions_data.append({
            'session_id': event.session_id,
            'ip_address': event.ip_address or '',
            'viewed_at': event.viewed_at.isoformat(),
            'sections_viewed': sections_viewed,
            'total_time_seconds': round(total_time, 1),
            'view_mode': event.view_mode,
        })

    # Build module name lookup from functional_requirements section
    import json as _json
    module_name_map = {}
    fr_section = proposal.sections.filter(
        section_type='functional_requirements',
    ).first()
    if fr_section and fr_section.content_json:
        _cj = fr_section.content_json
        for _grp in list(_cj.get('groups') or []) + list(_cj.get('additionalModules') or []):
            if _grp.get('id'):
                module_name_map[str(_grp['id'])] = _grp.get('title', f'Module {_grp["id"]}')

    # Change log timeline
    change_logs = proposal.change_logs.order_by('-created_at')[:50]
    timeline = []
    for log in change_logs:
        entry = {
            'change_type': log.change_type,
            'field_name': log.field_name,
            'old_value': log.old_value,
            'new_value': log.new_value,
            'description': log.description,
            'actor_type': log.actor_type,
            'created_at': log.created_at.isoformat(),
        }
        # Enrich calculator events with module names
        if log.change_type in ('calc_confirmed', 'calc_abandoned') and log.description:
            try:
                data = _json.loads(log.description)
                data['selected_names'] = [
                    module_name_map.get(str(mid), f'ID {mid}')
                    for mid in data.get('selected', [])
                ]
                data['deselected_names'] = [
                    module_name_map.get(str(mid), f'ID {mid}')
                    for mid in data.get('deselected', [])
                ]
                entry['description'] = _json.dumps(data)
            except (ValueError, KeyError):
                pass
        timeline.append(entry)

    # --- Funnel: how many sessions reached each section in order ---
    EXECUTIVE_SECTION_TYPES = {
        'greeting', 'executive_summary', 'proposal_summary',
        'functional_requirements', 'investment', 'timeline',
        'proposal_closing',
    }
    ordered_sections = list(
        proposal.sections
        .filter(is_enabled=True)
        .order_by('order')
        .values_list('section_type', 'title')
    )
    funnel_data = []
    for section_type, section_title in ordered_sections:
        if section_type == 'technical_document':
            reached = technical_sessions_reached
        else:
            reached = (
                ProposalSectionView.objects
                .filter(
                    view_event__proposal=proposal,
                    section_type=section_type,
                )
                .values('view_event__session_id')
                .distinct()
                .count()
            )
        drop_off = round(
            (1 - reached / unique_sessions) * 100, 1
        ) if unique_sessions > 0 else 0
        funnel_data.append({
            'section_type': section_type,
            'section_title': section_title,
            'reached_count': reached,
            'drop_off_percent': drop_off,
            'in_executive_mode': section_type in EXECUTIVE_SECTION_TYPES,
        })

    # --- Funnel técnico granular (tab técnico en analytics) ---
    tech_reached_map = {
        row['subsection_key']: row['reached_count']
        for row in (
            ProposalSectionView.objects
            .filter(
                view_event__proposal=proposal,
                section_type='technical_document_public',
                subsection_key__in=TECHNICAL_FRAGMENT_ORDER,
            )
            .values('subsection_key')
            .annotate(reached_count=Count('view_event__session_id', distinct=True))
        )
    }
    tech_section = proposal.sections.filter(section_type='technical_document').first()
    tech_doc = (tech_section.content_json if tech_section and tech_section.content_json else {})
    for fragment_key in TECHNICAL_FRAGMENT_ORDER:
        if not technical_fragment_has_content(fragment_key, tech_doc):
            continue
        tech_reached = tech_reached_map.get(fragment_key, 0)
        tech_drop_off = round(
            (1 - tech_reached / technical_sessions_reached) * 100, 1
        ) if technical_sessions_reached > 0 else 0
        funnel_data.append({
            'section_type': 'technical_document_public',
            'section_title': TECHNICAL_FRAGMENT_TITLES[fragment_key],
            'subsection_key': fragment_key,
            'reached_count': tech_reached,
            'drop_off_percent': tech_drop_off,
            'in_executive_mode': False,
        })

    # --- Comparison with global averages ---
    all_proposals = BusinessProposal.objects.all()
    ttfv_qs = all_proposals.filter(
        sent_at__isnull=False, first_viewed_at__isnull=False
    )
    avg_ttfv_global = None
    if ttfv_qs.exists():
        total_secs = sum(
            (p.first_viewed_at - p.sent_at).total_seconds()
            for p in ttfv_qs
        )
        avg_ttfv_global = round(total_secs / ttfv_qs.count() / 3600, 1)

    ttr_qs = all_proposals.filter(
        first_viewed_at__isnull=False, responded_at__isnull=False
    )
    avg_ttr_global = None
    if ttr_qs.exists():
        total_secs = sum(
            (p.responded_at - p.first_viewed_at).total_seconds()
            for p in ttr_qs
        )
        avg_ttr_global = round(total_secs / ttr_qs.count() / 3600, 1)

    avg_views_global = None
    viewed_proposals = all_proposals.filter(view_count__gt=0)
    if viewed_proposals.exists():
        avg_views_global = round(
            viewed_proposals.aggregate(avg=Avg('view_count'))['avg'], 1
        )

    comparison = {
        'avg_time_to_first_view_hours': avg_ttfv_global,
        'avg_time_to_response_hours': avg_ttr_global,
        'avg_views': avg_views_global,
    }

    # --- Share links ---
    share_links = ProposalShareLinkSerializer(
        proposal.share_links.all(), many=True
    ).data

    # --- Engagement score (0-100) ---
    engagement_score = compute_engagement_score(
        proposal, view_events, sections_data, unique_sessions,
    )

    # --- F6: View mode breakdown (executive / detailed / technical) ---
    # Group by (section_type, subsection_key) so technical_document_public
    # fragments stay split per subsection instead of collapsing into one row.
    by_view_mode = {}
    for mode in VIEW_MODE_LABELS:
        mode_sessions = (
            view_events.filter(view_mode=mode)
            .values('session_id').distinct().count()
        )
        latest_title_sq = (
            ProposalSectionView.objects
            .filter(
                view_event__proposal=proposal,
                view_mode=mode,
                section_type=OuterRef('section_type'),
                subsection_key=OuterRef('subsection_key'),
            )
            .order_by('-entered_at')
            .values('section_title')[:1]
        )
        mode_section_stats = (
            ProposalSectionView.objects
            .filter(view_event__proposal=proposal, view_mode=mode)
            .values('section_type', 'subsection_key')
            .annotate(
                visit_count=Count('id'),
                total_time_seconds=Sum('time_spent_seconds'),
                latest_title=Subquery(latest_title_sq),
            )
            .order_by('section_type', 'subsection_key')
        )
        by_view_mode[mode] = {
            'sessions': mode_sessions,
            'sections': [
                {
                    'section_type': s['section_type'],
                    'subsection_key': s['subsection_key'],
                    'section_title': s['latest_title'] or s['section_type'],
                    'visit_count': s['visit_count'],
                    'total_time_seconds': round(s['total_time_seconds'] or 0, 1),
                }
                for s in mode_section_stats
            ],
        }

    last_viewed_at = (
        view_events.order_by('-viewed_at')
        .values_list('viewed_at', flat=True)
        .first()
    )

    return {
        'total_views': total_views,
        'unique_sessions': unique_sessions,
        'first_viewed_at': (
            proposal.first_viewed_at.isoformat()
            if proposal.first_viewed_at else None
        ),
        'last_viewed_at': (
            last_viewed_at.isoformat()
            if last_viewed_at else None
        ),
        'responded_at': (
            proposal.responded_at.isoformat()
            if proposal.responded_at else None
        ),
        'time_to_first_view_hours': time_to_first_view,
        'time_to_response_hours': time_to_response,
        'sections': sections_data,
        'skipped_sections': skipped_sections,
        'device_breakdown': device_counts,
        'sessions': sessions_data,
        'timeline': timeline,
        'funnel': funnel_data,
        'comparison': comparison,
        'share_links': share_links,
        'engagement_score': engagement_score,
        'by_view_mode': by_view_mode,
        'technical_engagement': technical_engagement,
    }


def build_dashboard():
    """
    Build aggregated KPIs across all proposals for the admin dashboard.

    Includes: total counts by status, conversion rate, avg time metrics,
    avg proposal value by status, top rejection reasons, monthly trend.
    """
    from django.db.models import Avg, Count, Q, Sum
    from django.db.models.functions import TruncMonth

    all_proposals = BusinessProposal.objects.all()
    totals_input = list(
        all_proposals.only(
            'id', 'status', 'total_investment', 'selected_modules', 'is_active',
        )
    )
    effective_totals = build_effective_totals_map(totals_input)
    total = len(totals_input)

    # Pipeline value: sum of effective investment for active sent + viewed proposals
    pipeline_ids = {
        p.id for p in totals_input
        if p.status in ('sent', 'viewed') and p.is_active
    }
    pipeline_value = float(sum(
        (effective_totals[pid] for pid in pipeline_ids if pid in effective_totals),
        Decimal('0'),
    ))
    pipeline_count = len(pipeline_ids)

    # Counts by status (single aggregated query)
    status_counts = dict(
        all_proposals.values_list('status')
        .annotate(c=Count('id'))
        .values_list('status', 'c')
    )
    by_status = {
        choice_val: status_counts.get(choice_val, 0)
        for choice_val, _label in BusinessProposal.Status.choices
    }

    # Conversion rate — 'finished' is a post-acceptance terminal state and
    # counts as a successful conversion alongside 'accepted'.
    won_count = by_status.get('accepted', 0) + by_status.get('finished', 0)
    terminal = won_count + by_status.get('rejected', 0) + by_status.get('expired', 0)
    conversion_rate = round(
        (won_count / terminal * 100) if terminal > 0 else 0, 1
    )

    # Avg time-to-first-view (hours) — only proposals that have both timestamps
    ttfv_qs = all_proposals.filter(
        sent_at__isnull=False, first_viewed_at__isnull=False
    )
    avg_ttfv = None
    if ttfv_qs.exists():
        total_seconds = sum(
            (p.first_viewed_at - p.sent_at).total_seconds()
            for p in ttfv_qs
        )
        avg_ttfv = round(total_seconds / ttfv_qs.count() / 3600, 1)

    # Avg time-to-response (hours)
    ttr_qs = all_proposals.filter(
        first_viewed_at__isnull=False, responded_at__isnull=False
    )
    avg_ttr = None
    if ttr_qs.exists():
        total_seconds = sum(
            (p.responded_at - p.first_viewed_at).total_seconds()
            for p in ttr_qs
        )
        avg_ttr = round(total_seconds / ttr_qs.count() / 3600, 1)

    # Avg proposal value by status (single pass)
    _status_buckets = {s: [] for s in ('accepted', 'finished', 'rejected', 'expired', 'sent', 'viewed')}
    for p in totals_input:
        if p.status in _status_buckets and p.id in effective_totals:
            _status_buckets[p.status].append(effective_totals[p.id])
    avg_value_by_status = {}
    for s, vals in _status_buckets.items():
        if vals:
            avg_value_by_status[s] = round(float(sum(vals, Decimal('0')) / Decimal(len(vals))), 2)
        else:
            avg_value_by_status[s] = 0

    # Top rejection reasons
    rejection_reasons = (
        all_proposals
        .filter(status='rejected', rejection_reason__gt='')
        .values('rejection_reason')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Monthly trend (last 6 months)
    from datetime import timedelta
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_qs = (
        all_proposals
        .filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(
            created=Count('id'),
            sent=Count('id', filter=Q(status__in=['sent', 'viewed', 'accepted', 'finished', 'rejected', 'expired'])),
            accepted=Count('id', filter=Q(status__in=['accepted', 'finished'])),
            finished=Count('id', filter=Q(status='finished')),
            rejected=Count('id', filter=Q(status='rejected')),
        )
        .order_by('month')
    )
    monthly_trend = [
        {
            'month': row['month'].isoformat() if row['month'] else '',
            'created': row['created'],
            'sent': row['sent'],
            'accepted': row['accepted'],
            'finished': row['finished'],
            'rejected': row['rejected'],
        }
        for row in monthly_qs
    ]

    # --- New metrics ---

    # Proposals that have been meaningfully viewed (status advanced past sent)
    viewed_statuses = ('viewed', 'accepted', 'finished', 'rejected', 'expired')
    viewed_proposals = all_proposals.filter(status__in=viewed_statuses)
    viewed_count = viewed_proposals.count()

    # % that reached the investment section
    investment_reached_count = (
        BusinessProposal.objects
        .filter(
            status__in=viewed_statuses,
            view_events__section_views__section_type='investment',
        )
        .distinct()
        .count()
    )
    pct_reaching_investment = (
        round(investment_reached_count / viewed_count * 100, 1)
        if viewed_count > 0 else None
    )

    # % that re-opened the proposal (unique_sessions > 1)
    revisit_count = (
        BusinessProposal.objects
        .filter(status__in=viewed_statuses)
        .annotate(session_count=Count('view_events__session_id', distinct=True))
        .filter(session_count__gt=1)
        .count()
    )
    pct_revisit = (
        round(revisit_count / viewed_count * 100, 1)
        if viewed_count > 0 else None
    )

    # Discount vs no-discount close rate
    def _close_rate(qs):
        t = qs.filter(status__in=('accepted', 'finished', 'rejected', 'expired')).count()
        a = qs.filter(status__in=('accepted', 'finished')).count()
        return round(a / t * 100, 1) if t > 0 else None

    with_discount_qs = all_proposals.filter(discount_percent__gt=0)
    without_discount_qs = all_proposals.filter(discount_percent=0)
    discount_close_rate = _close_rate(with_discount_qs)
    no_discount_close_rate = _close_rate(without_discount_qs)

    # Detailed discount analysis — finished proposals are accepted-and-delivered,
    # so they count as 'accepted' for win/close-rate calculations.
    avg_discount_all = with_discount_qs.aggregate(
        avg=Avg('discount_percent')
    )['avg']
    avg_discount_accepted = with_discount_qs.filter(
        status__in=['accepted', 'finished']
    ).aggregate(avg=Avg('discount_percent'))['avg']
    discount_analysis = {
        'with_discount_count': with_discount_qs.filter(
            status__in=['accepted', 'finished', 'rejected', 'expired']
        ).count(),
        'with_discount_accepted': with_discount_qs.filter(
            status__in=['accepted', 'finished']
        ).count(),
        'without_discount_count': without_discount_qs.filter(
            status__in=['accepted', 'finished', 'rejected', 'expired']
        ).count(),
        'without_discount_accepted': without_discount_qs.filter(
            status__in=['accepted', 'finished']
        ).count(),
        'avg_discount_percent': round(float(avg_discount_all), 1) if avg_discount_all else None,
        'avg_discount_accepted': round(float(avg_discount_accepted), 1) if avg_discount_accepted else None,
    }

    # % viewed within 24 hours of sending
    within_24h = sum(
        1 for p in ttfv_qs
        if (p.first_viewed_at - p.sent_at).total_seconds() <= 86400
    )
    pct_viewed_within_24h = (
        round(within_24h / ttfv_qs.count() * 100, 1)
        if ttfv_qs.exists() else None
    )

    # Top drop-off section (cross-portfolio)
    # Drop-off % per section = sessions that never saw that section / all sessions
    from content.models import ProposalSectionView as _PSV, ProposalViewEvent as _PVE
    total_sessions_global = _PVE.objects.values('session_id').distinct().count()
    top_dropoff_section = None
    if total_sessions_global > 0:
        dropoff_allow = dashboard_top_dropoff_allowlist()
        section_types_qs = (
            _PSV.objects.values_list('section_type', flat=True).distinct()
        )
        dropoff_by_section = {}
        for sec_type in section_types_qs:
            if sec_type not in dropoff_allow:
                continue
            sessions_reached = (
                _PSV.objects
                .filter(section_type=sec_type)
                .values('view_event__session_id')
                .distinct()
                .count()
            )
            dropoff_by_section[sec_type] = round(
                (1 - sessions_reached / total_sessions_global) * 100, 1
            )
        if dropoff_by_section:
            top_sec = max(dropoff_by_section, key=lambda k: dropoff_by_section[k])
            top_dropoff_section = {
                'section_type': top_sec,
                'dropoff_percent': dropoff_by_section[top_sec],
            }

    # --- Win rate by project_type ---
    def _win_rate_breakdown(field_name):
        results = []
        values = (
            all_proposals
            .filter(**{f'{field_name}__gt': ''})
            .values(field_name)
            .annotate(
                total=Count('id', filter=Q(status__in=['accepted', 'finished', 'rejected', 'expired'])),
                accepted=Count('id', filter=Q(status__in=['accepted', 'finished'])),
            )
            .order_by(f'-accepted')
        )
        for row in values:
            t = row['total']
            a = row['accepted']
            rate = round(a / t * 100, 1) if t > 0 else 0
            results.append({
                'type': row[field_name],
                'accepted': a,
                'total': t,
                'win_rate': rate,
            })
        return results

    win_rate_by_project_type = _win_rate_breakdown('project_type')
    win_rate_by_market_type = _win_rate_breakdown('market_type')

    # Win rate by combination (only combos with ≥2 terminal proposals)
    combo_qs = (
        all_proposals
        .filter(project_type__gt='', market_type__gt='')
        .values('project_type', 'market_type')
        .annotate(
            total=Count('id', filter=Q(status__in=['accepted', 'finished', 'rejected', 'expired'])),
            accepted=Count('id', filter=Q(status__in=['accepted', 'finished'])),
        )
        .filter(total__gte=2)
        .order_by('-accepted')
    )
    win_rate_by_combination = [
        {
            'project_type': row['project_type'],
            'market_type': row['market_type'],
            'accepted': row['accepted'],
            'total': row['total'],
            'win_rate': round(row['accepted'] / row['total'] * 100, 1) if row['total'] > 0 else 0,
        }
        for row in combo_qs
    ]

    # --- 3.3 Engagement / close-value correlation ---
    # Compare avg investment for high-engagement vs low-engagement accepted proposals
    # (finished proposals were also accepted, so include them)
    engagement_value_insight = None
    accepted_proposals = all_proposals.filter(status__in=['accepted', 'finished'])
    if accepted_proposals.count() >= 4:
        # Compute total engagement time per accepted proposal
        engagement_data = []
        for p in accepted_proposals:
            total_time = (
                _PSV.objects
                .filter(view_event__proposal=p)
                .aggregate(t=Sum('time_spent_seconds'))
            )['t'] or 0
            engagement_data.append({
                'investment': float(p.total_investment or 0),
                'time': total_time,
            })
        if engagement_data:
            median_time = sorted(d['time'] for d in engagement_data)[len(engagement_data) // 2]
            high_eng = [d['investment'] for d in engagement_data if d['time'] >= median_time]
            low_eng = [d['investment'] for d in engagement_data if d['time'] < median_time]
            avg_high = round(sum(high_eng) / len(high_eng)) if high_eng else 0
            avg_low = round(sum(low_eng) / len(low_eng)) if low_eng else 0
            diff = avg_high - avg_low
            engagement_value_insight = {
                'avg_high_engagement_value': avg_high,
                'avg_low_engagement_value': avg_low,
                'difference': diff,
                'high_count': len(high_eng),
                'low_count': len(low_eng),
            }

    # --- 3.1 Most dropped calculator modules ---
    import json as _json
    calc_logs = (
        ProposalChangeLog.objects
        .filter(change_type='calc_confirmed')
        .values_list('description', flat=True)
    )
    drop_counts = {}
    for desc in calc_logs:
        try:
            data = _json.loads(desc)
            for mod_id in data.get('deselected', []):
                drop_counts[mod_id] = drop_counts.get(mod_id, 0) + 1
        except (ValueError, TypeError):
            pass
    top_dropped_modules = sorted(
        [{'module_id': k, 'drop_count': v} for k, v in drop_counts.items()],
        key=lambda x: x['drop_count'], reverse=True,
    )[:10]

    # Calculator abandonment rate
    calc_confirmed = ProposalChangeLog.objects.filter(change_type='calc_confirmed').count()
    calc_abandoned = ProposalChangeLog.objects.filter(change_type='calc_abandoned').count()
    calc_total = calc_confirmed + calc_abandoned
    calc_abandonment_rate = round(calc_abandoned / calc_total * 100, 1) if calc_total > 0 else None

    # --- Win rate by predominant view_mode (executive / detailed / technical) ---
    from content.models import ProposalViewEvent as _PVE_dm
    terminal_proposals = all_proposals.filter(
        status__in=['accepted', 'finished', 'rejected', 'expired'],
    )
    view_mode_stats = {
        'executive': {'total': 0, 'accepted': 0},
        'detailed': {'total': 0, 'accepted': 0},
        'technical': {'total': 0, 'accepted': 0},
    }
    for p in terminal_proposals:
        mode_counts = (
            _PVE_dm.objects
            .filter(proposal=p, view_mode__in=list(VIEW_MODE_LABELS))
            .values('view_mode')
            .annotate(cnt=Count('id'))
        )
        if not mode_counts:
            continue
        predominant = max(mode_counts, key=lambda m: m['cnt'])['view_mode']
        view_mode_stats[predominant]['total'] += 1
        if p.status in ('accepted', 'finished'):
            view_mode_stats[predominant]['accepted'] += 1
    win_rate_by_view_mode = {}
    for mode, stats in view_mode_stats.items():
        win_rate_by_view_mode[mode] = {
            'total': stats['total'],
            'accepted': stats['accepted'],
            'win_rate': round(stats['accepted'] / stats['total'] * 100, 1) if stats['total'] > 0 else None,
        }

    return {
        'total_proposals': total,
        'by_status': by_status,
        'conversion_rate': conversion_rate,
        'pipeline_value': pipeline_value,
        'pipeline_count': pipeline_count,
        'avg_time_to_first_view_hours': avg_ttfv,
        'avg_time_to_response_hours': avg_ttr,
        'avg_value_by_status': avg_value_by_status,
        'top_rejection_reasons': list(rejection_reasons),
        'monthly_trend': monthly_trend,
        'pct_reaching_investment': pct_reaching_investment,
        'pct_revisit': pct_revisit,
        'discount_close_rate': discount_close_rate,
        'no_discount_close_rate': no_discount_close_rate,
        'discount_analysis': discount_analysis,
        'pct_viewed_within_24h': pct_viewed_within_24h,
        'top_dropoff_section': top_dropoff_section,
        'win_rate_by_project_type': win_rate_by_project_type,
        'win_rate_by_market_type': win_rate_by_market_type,
        'win_rate_by_combination': win_rate_by_combination,
        'engagement_value_insight': engagement_value_insight,
        'top_dropped_modules': top_dropped_modules,
        'calc_abandonment_rate': calc_abandonment_rate,
        'win_rate_by_view_mode': win_rate_by_view_mode,
    }


def build_proposal_alerts():
    """
    Build the list of proposals that need attention:
    - Sent but not viewed after reminder_days
    - Viewed but not responded after urgency_reminder_days
    - Expiring within 3 days

    Includes computed alerts, manual alerts, dismissed-computed filtering,
    default priorities, and priority sorting.
    """
    now = timezone.now()
    from datetime import timedelta

    alerts = []
    dismissed_computed_keys = {
        marker.removeprefix(COMPUTED_ALERT_DISMISS_PREFIX)
        for marker in ProposalAlert.objects.filter(
            is_dismissed=True,
            message__startswith=COMPUTED_ALERT_DISMISS_PREFIX,
        ).values_list('message', flat=True)
    }

    # Sent but not viewed — stale
    stale = BusinessProposal.objects.filter(
        status=BusinessProposal.Status.SENT,
        is_active=True,
        first_viewed_at__isnull=True,
    )
    for p in stale:
        if p.sent_at and (now - p.sent_at).days >= p.reminder_days:
            alerts.append({
                'id': p.id, 'uuid': str(p.uuid),
                'title': p.title, 'client_name': p.client_name,
                'alert_type': 'not_viewed',
                'days_since': (now - p.sent_at).days,
                'ref_date': p.sent_at.isoformat(),
                'message': f'Enviada hace {(now - p.sent_at).days} días, aún no abierta.',
            })

    # Viewed but not responded — urgency
    viewed = BusinessProposal.objects.filter(
        status=BusinessProposal.Status.VIEWED,
        is_active=True,
        responded_at__isnull=True,
    )
    for p in viewed:
        if p.first_viewed_at and (now - p.first_viewed_at).days >= p.urgency_reminder_days:
            alerts.append({
                'id': p.id, 'uuid': str(p.uuid),
                'title': p.title, 'client_name': p.client_name,
                'alert_type': 'not_responded',
                'days_since': (now - p.first_viewed_at).days,
                'ref_date': p.first_viewed_at.isoformat(),
                'message': f'Vista hace {(now - p.first_viewed_at).days} días, sin respuesta.',
            })

    # Expiring soon (within 3 days)
    expiring = BusinessProposal.objects.filter(
        is_active=True,
        expires_at__isnull=False,
        expires_at__lte=now + timedelta(days=3),
        expires_at__gt=now,
    ).exclude(status__in=[
        BusinessProposal.Status.ACCEPTED,
        BusinessProposal.Status.FINISHED,
        BusinessProposal.Status.REJECTED,
        BusinessProposal.Status.EXPIRED,
    ])
    for p in expiring:
        days_left = (p.expires_at - now).days
        alerts.append({
            'id': p.id, 'uuid': str(p.uuid),
            'title': p.title, 'client_name': p.client_name,
            'alert_type': 'expiring_soon',
            'days_remaining': days_left,
            'ref_date': p.expires_at.isoformat(),
            'message': f'Expira en {days_left} día{"s" if days_left != 1 else ""}.',
        })

    # Seller inactivity: sent/viewed, client has viewed, but seller has no
    # activity logged in >3 days
    seller_inactive_qs = BusinessProposal.objects.filter(
        status__in=[BusinessProposal.Status.SENT, BusinessProposal.Status.VIEWED],
        is_active=True,
        first_viewed_at__isnull=False,
    )
    seller_activity_types = {'call', 'meeting', 'followup', 'note'}
    # Pre-fetch IDs with recent seller activity to avoid N+1 queries
    seller_inactive_ids = [p.id for p in seller_inactive_qs]
    ids_with_recent_seller_activity = set(
        ProposalChangeLog.objects.filter(
            proposal_id__in=seller_inactive_ids,
            change_type__in=seller_activity_types,
            created_at__gte=now - timedelta(days=3),
        ).values_list('proposal_id', flat=True).distinct()
    ) if seller_inactive_ids else set()
    for p in seller_inactive_qs:
        ref_date = p.last_activity_at or p.sent_at
        if ref_date and (now - ref_date).days >= 3:
            if p.id not in ids_with_recent_seller_activity:
                days = (now - ref_date).days
                alerts.append({
                    'id': p.id, 'uuid': str(p.uuid),
                    'title': p.title, 'client_name': p.client_name,
                    'alert_type': 'seller_inactive',
                    'days_since': days,
                    'ref_date': ref_date.isoformat(),
                    'message': f'Sin follow-up del vendedor hace {days} días.',
                })

    # Zombie proposals: sent >7 days ago, no views, no seller activity
    zombie_qs = BusinessProposal.objects.filter(
        status=BusinessProposal.Status.SENT,
        is_active=True,
        view_count=0,
        first_viewed_at__isnull=True,
        sent_at__isnull=False,
        sent_at__lte=now - timedelta(days=7),
    )
    # Pre-fetch IDs with any seller activity to avoid N+1 queries
    zombie_ids = [p.id for p in zombie_qs]
    ids_with_any_seller_activity = set(
        ProposalChangeLog.objects.filter(
            proposal_id__in=zombie_ids,
            change_type__in=seller_activity_types,
        ).values_list('proposal_id', flat=True).distinct()
    ) if zombie_ids else set()
    for p in zombie_qs:
        if p.id not in ids_with_any_seller_activity:
            days = (now - p.sent_at).days
            alerts.append({
                'id': p.id, 'uuid': str(p.uuid),
                'title': p.title, 'client_name': p.client_name,
                'alert_type': 'zombie',
                'days_since': days,
                'ref_date': p.sent_at.isoformat(),
                'message': f'Propuesta zombie — sin vista ni actividad en {days} días.',
            })

    # Zombie drafts: draft >5 days without edit
    zombie_draft_qs = BusinessProposal.objects.filter(
        status=BusinessProposal.Status.DRAFT,
        is_active=True,
        updated_at__lte=now - timedelta(days=5),
    )
    for p in zombie_draft_qs:
        days = (now - p.updated_at).days
        alerts.append({
            'id': p.id, 'uuid': str(p.uuid),
            'title': p.title, 'client_name': p.client_name,
            'alert_type': 'zombie_draft',
            'days_since': days,
            'ref_date': p.updated_at.isoformat(),
            'message': f'Borrador abandonado — sin edición en {days} días.',
        })

    # Zombie sent stale: sent >10 days, no views (exclude already-alerted zombies)
    zombie_alerted_ids = {a['id'] for a in alerts if a['alert_type'] == 'zombie'}
    zombie_sent_stale_qs = BusinessProposal.objects.filter(
        status=BusinessProposal.Status.SENT,
        is_active=True,
        view_count=0,
        first_viewed_at__isnull=True,
        sent_at__isnull=False,
        sent_at__lte=now - timedelta(days=10),
    ).exclude(id__in=zombie_alerted_ids)
    for p in zombie_sent_stale_qs:
        days = (now - p.sent_at).days
        alerts.append({
            'id': p.id, 'uuid': str(p.uuid),
            'title': p.title, 'client_name': p.client_name,
            'alert_type': 'zombie_sent_stale',
            'days_since': days,
            'ref_date': p.sent_at.isoformat(),
            'message': f'Enviada hace {days} días — nunca vista.',
        })

    # Late return: client didn't visit for ≥5 days then came back in last 24h
    # Pre-filter: only candidates with a recent view (last 24h) to reduce scope
    late_return_candidates = BusinessProposal.objects.filter(
        status__in=[BusinessProposal.Status.SENT, BusinessProposal.Status.VIEWED],
        is_active=True,
    ).filter(
        id__in=ProposalViewEvent.objects.filter(
            viewed_at__gte=now - timedelta(hours=24),
        ).values_list('proposal_id', flat=True).distinct()
    )
    # Batch-fetch the last 2 events per candidate
    late_return_candidate_ids = [p.id for p in late_return_candidates]
    candidate_events = {}
    if late_return_candidate_ids:
        all_events = (
            ProposalViewEvent.objects
            .filter(proposal_id__in=late_return_candidate_ids)
            .order_by('proposal_id', '-viewed_at')
            .values_list('proposal_id', 'viewed_at')
        )
        for pid, viewed_at in all_events:
            lst = candidate_events.setdefault(pid, [])
            if len(lst) < 2:
                lst.append(viewed_at)
    for p in late_return_candidates:
        events = candidate_events.get(p.id, [])
        if len(events) >= 2:
            latest, previous = events[0], events[1]
            gap_days = (latest - previous).days
            recency_hours = (now - latest).total_seconds() / 3600
            if gap_days >= 5 and recency_hours <= 24:
                alerts.append({
                    'id': p.id, 'uuid': str(p.uuid),
                    'title': p.title, 'client_name': p.client_name,
                    'alert_type': 'late_return',
                    'days_since': gap_days,
                    'ref_date': latest.isoformat(),
                    'message': f'El cliente volvió después de {gap_days} días — posible comparación con competencia.',
                })

    # Manual alerts (not dismissed, alert_date <= now). Accepted/finished
    # proposals are closed deals and never "need attention".
    manual_qs = ProposalAlert.objects.filter(
        is_dismissed=False,
        alert_date__lte=now,
    ).exclude(
        proposal__status__in=[
            BusinessProposal.Status.ACCEPTED,
            BusinessProposal.Status.FINISHED,
        ],
    ).select_related('proposal')
    for a in manual_qs:
        alerts.append({
            'id': a.proposal.id, 'uuid': str(a.proposal.uuid),
            'title': a.proposal.title, 'client_name': a.proposal.client_name,
            'alert_type': f'manual_{a.alert_type}',
            'message': a.message,
            'manual_alert_id': a.id,
            'alert_date': a.alert_date.isoformat(),
            'priority': a.priority,
        })

    if dismissed_computed_keys:
        kept_alerts = []
        for alert in alerts:
            if alert.get('manual_alert_id'):
                kept_alerts.append(alert)
                continue
            key = computed_alert_key(
                alert.get('id'),
                alert.get('alert_type'),
                alert.get('ref_date') or alert.get('alert_date'),
            )
            if key in dismissed_computed_keys:
                continue
            kept_alerts.append(alert)
        alerts = kept_alerts

    # Assign default priority to computed alerts that don't have one
    COMPUTED_PRIORITY = {
        'expiring_soon': 'critical',
        'late_return': 'critical',
        'not_responded': 'high',
        'seller_inactive': 'high',
        'not_viewed': 'normal',
        'zombie': 'normal',
        'zombie_draft': 'normal',
        'zombie_sent_stale': 'normal',
    }
    for a in alerts:
        if 'priority' not in a:
            a['priority'] = COMPUTED_PRIORITY.get(a['alert_type'], 'normal')

    # Sort by priority: critical > high > normal
    PRIORITY_ORDER = {'critical': 0, 'high': 1, 'normal': 2}
    alerts.sort(key=lambda a: PRIORITY_ORDER.get(a.get('priority', 'normal'), 2))

    return alerts
