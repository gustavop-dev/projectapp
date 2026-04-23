"""Admin + public DRF views for the WebAppDiagnostic feature.

Admin endpoints use Django session auth + IsAdminUser. The 3 public endpoints
(`retrieve`, `track`, `respond`) use AllowAny + UUID lookup.
"""

import logging

from django.db.models import Avg, Count, Min, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from content.throttles import TrackingAnonThrottle

from accounts.models import UserProfile
from accounts.services.proposal_client_service import update_client_profile
from content.services.diagnostic_pdf_service import DiagnosticPdfService
from content.services.pdf_utils import safe_pdf_filename
from content.models import (
    DiagnosticAttachment,
    DiagnosticChangeLog,
    DiagnosticDefaultConfig,
    DiagnosticSection,
    DiagnosticSectionView,
    DiagnosticViewEvent,
    WebAppDiagnostic,
)
from content.serializers.diagnostic import (
    ConfidentialityParamsSerializer,
    DiagnosticChangeLogSerializer,
    DiagnosticDefaultConfigSerializer,
    DiagnosticDetailSerializer,
    DiagnosticListSerializer,
    DiagnosticSectionSerializer,
    DiagnosticSectionUpdateSerializer,
    DiagnosticUpdateSerializer,
    PublicDiagnosticSerializer,
    serialize_diagnostic_attachment,
)
from content.services import diagnostic_service
from content.views._email_attachment import (
    inline_pdf_response,
    render_markdown_pdf_response,
)
from content.utils import get_client_ip

logger = logging.getLogger(__name__)


def _admin_qs(include_attachments=False):
    qs = (
        WebAppDiagnostic.objects
        .select_related('client__user')
        .prefetch_related('sections', 'change_logs')
    )
    if include_attachments:
        qs = qs.prefetch_related('attachments')
    return qs


# ──────────────────────────────────────────────────────────────────────────
# Admin — list / create / detail / update
# ──────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_diagnostics(request):
    qs = _admin_qs()
    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)
    client_id = request.query_params.get('client')
    if client_id:
        qs = qs.filter(client_id=client_id)
    return Response(DiagnosticListSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_diagnostic(request):
    client_id = request.data.get('client_id')
    if not client_id:
        return Response(
            {'error': 'client_id_required'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    client = UserProfile.objects.filter(
        pk=client_id, role=UserProfile.ROLE_CLIENT,
    ).first()
    if client is None:
        return Response(
            {'error': 'client_not_found'},
            status=http_status.HTTP_404_NOT_FOUND,
        )

    language = (request.data.get('language') or 'es').lower()
    if language not in ('es', 'en'):
        language = 'es'
    title = (request.data.get('title') or '').strip()

    diagnostic = diagnostic_service.create_diagnostic(
        client=client,
        language=language,
        title=title,
        created_by=request.user if request.user.is_authenticated else None,
    )
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    return Response(
        DiagnosticDetailSerializer(diagnostic).data,
        status=http_status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_diagnostic(request, diagnostic_id):
    diagnostic = get_object_or_404(_admin_qs(include_attachments=True), pk=diagnostic_id)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_diagnostic(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    serializer = DiagnosticUpdateSerializer(
        diagnostic, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors,
                        status=http_status.HTTP_400_BAD_REQUEST)
    propagate = serializer.validated_data.get('propagate_client_updates', False)
    serializer.save()
    if propagate:
        update_client_profile(
            diagnostic.client,
            name=diagnostic.client_name or None,
            email=diagnostic.client_email or None,
            phone=diagnostic.client_phone or None,
            company=diagnostic.client_company or None,
        )
    diagnostic_service.log_change(
        diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.UPDATED,
        description='Datos generales actualizados.',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_diagnostic(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    diagnostic.delete()
    return Response(status=http_status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────
# Admin — sections CRUD
# ──────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_diagnostic_sections(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    return Response(DiagnosticSectionSerializer(
        diagnostic.sections.all(), many=True,
    ).data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_diagnostic_section(request, diagnostic_id, section_id):
    section = get_object_or_404(
        DiagnosticSection.objects.select_related('diagnostic'),
        pk=section_id, diagnostic_id=diagnostic_id,
    )
    serializer = DiagnosticSectionUpdateSerializer(
        section, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors,
                        status=http_status.HTTP_400_BAD_REQUEST)
    serializer.save()
    diagnostic_service.log_change(
        section.diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.SECTION_UPDATED,
        field_name=section.section_type,
        description=f'Sección «{section.title}» actualizada.',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    return Response(DiagnosticSectionSerializer(section).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_update_diagnostic_sections(request, diagnostic_id):
    """Accept a list of ``{id, ...fields}`` entries and update in one call."""
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    payload = request.data.get('sections') or []
    if not isinstance(payload, list):
        return Response(
            {'error': 'sections_must_be_list'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    updated_ids = []
    for entry in payload:
        if not isinstance(entry, dict) or 'id' not in entry:
            continue
        section = DiagnosticSection.objects.filter(
            pk=entry['id'], diagnostic_id=diagnostic.id,
        ).first()
        if section is None:
            continue
        serializer = DiagnosticSectionUpdateSerializer(
            section, data=entry, partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            updated_ids.append(section.id)

    if updated_ids:
        diagnostic_service.log_change(
            diagnostic,
            change_type=DiagnosticChangeLog.ChangeType.SECTION_UPDATED,
            description=f'{len(updated_ids)} secciones actualizadas en bloque.',
            actor_type=DiagnosticChangeLog.ActorType.SELLER,
        )

    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reset_diagnostic_section(request, diagnostic_id, section_id):
    section = get_object_or_404(
        DiagnosticSection.objects.select_related('diagnostic'),
        pk=section_id, diagnostic_id=diagnostic_id,
    )
    diagnostic_service.reset_section(section)
    diagnostic_service.log_change(
        section.diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.SECTION_UPDATED,
        field_name=section.section_type,
        description=f'Sección «{section.title}» restaurada al contenido por defecto.',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    return Response(DiagnosticSectionSerializer(section).data)


# ──────────────────────────────────────────────────────────────────────────
# Admin — activity (change log)
# ──────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_diagnostic_activity(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    logs = diagnostic.change_logs.all()
    return Response(DiagnosticChangeLogSerializer(logs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_diagnostic_activity(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    change_type = (request.data.get('change_type') or 'note').strip()
    valid = {c[0] for c in DiagnosticChangeLog.ChangeType.choices}
    if change_type not in valid:
        return Response(
            {'error': 'invalid_change_type'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    description = (request.data.get('description') or '').strip()
    if not description:
        return Response(
            {'error': 'description_required'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    log = diagnostic_service.log_change(
        diagnostic,
        change_type=change_type,
        description=description,
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    return Response(
        DiagnosticChangeLogSerializer(log).data,
        status=http_status.HTTP_201_CREATED,
    )


# ──────────────────────────────────────────────────────────────────────────
# Admin — analytics
# ──────────────────────────────────────────────────────────────────────────

_ACTIVE_ENGAGEMENT_STATUSES = frozenset({
    WebAppDiagnostic.Status.ACCEPTED,
    WebAppDiagnostic.Status.FINISHED,
    WebAppDiagnostic.Status.NEGOTIATING,
})


def _compute_diagnostic_engagement_score(
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
    from datetime import timedelta

    score = 0

    seven_days_ago = timezone.now() - timedelta(days=7)
    recent = view_events.filter(viewed_at__gte=seven_days_ago).count()
    score += min(25, recent * 8)

    score += round(min(20, (coverage_ratio or 0) * 20))

    total_time = sum(s.get('total_time_seconds', 0) for s in sections_data)
    cost_time = sum(
        s.get('total_time_seconds', 0)
        for s in sections_data if s.get('section_type') == 'cost'
    )
    if total_time > 0:
        if cost_time >= 30:
            score += 10
        elif cost_time >= 10:
            score += 5
        if total_time >= 120:
            score += 5
        elif total_time >= 40:
            score += 3

    unique_ips = (
        view_events.exclude(ip_address__isnull=True)
        .exclude(ip_address='')
        .values('ip_address').distinct().count()
    )
    score += min(15, unique_ips * 8)

    if diagnostic.status == WebAppDiagnostic.Status.SENT and first_viewed_at:
        days_since = (timezone.now() - first_viewed_at).days
        if days_since <= 1:
            score += 15
        elif days_since <= 3:
            score += 10
        elif days_since <= 7:
            score += 5
    elif diagnostic.status in _ACTIVE_ENGAGEMENT_STATUSES:
        score += 15

    if unique_sessions > 1:
        score += min(10, (unique_sessions - 1) * 4)

    return min(100, score)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def diagnostic_analytics(request, diagnostic_id):
    """Aggregated engagement analytics for a diagnostic.

    Shape mirrors ``retrieve_proposal_analytics`` with the exceptions of
    view modes, technical subsections and share links (no equivalent data
    model for diagnostics).
    """
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)

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

    section_stats = (
        DiagnosticSectionView.objects
        .filter(view_event__diagnostic=diagnostic)
        .values('section_type')
        .annotate(
            visit_count=Count('id'),
            total_time_seconds=Sum('time_spent_seconds'),
            avg_time_seconds=Avg('time_spent_seconds'),
            reached_sessions=Count('view_event__session_id', distinct=True),
        )
        .order_by('section_type')
    )

    visited_types = set()
    sections_data = []
    section_reach = {}
    for stat in section_stats:
        visited_types.add(stat['section_type'])
        section_reach[stat['section_type']] = stat['reached_sessions']
        latest = (
            DiagnosticSectionView.objects
            .filter(
                view_event__diagnostic=diagnostic,
                section_type=stat['section_type'],
            )
            .order_by('-entered_at')
            .values_list('section_title', flat=True)
            .first()
        )
        sections_data.append({
            'section_type': stat['section_type'],
            'section_title': latest or stat['section_type'],
            'visit_count': stat['visit_count'],
            'total_time_seconds': round(stat['total_time_seconds'] or 0, 1),
            'avg_time_seconds': round(stat['avg_time_seconds'] or 0, 1),
        })

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

    # Tablet check must precede mobile because iPad UAs contain "Mobile".
    device_counts = {'desktop': 0, 'mobile': 0, 'tablet': 0}
    for ua in view_events.values_list('user_agent', flat=True):
        ua_lower = (ua or '').lower()
        if 'tablet' in ua_lower or 'ipad' in ua_lower:
            device_counts['tablet'] += 1
        elif 'mobile' in ua_lower or 'android' in ua_lower:
            device_counts['mobile'] += 1
        else:
            device_counts['desktop'] += 1

    sessions_data = []
    recent_events = (
        view_events.order_by('-viewed_at')
        .prefetch_related('section_views')[:50]
    )
    for event in recent_events:
        sv = list(event.section_views.all())
        sessions_data.append({
            'session_id': event.session_id,
            'ip_address': event.ip_address or '',
            'viewed_at': event.viewed_at.isoformat(),
            'sections_viewed': len(sv),
            'total_time_seconds': round(
                sum(s.time_spent_seconds for s in sv), 1,
            ),
        })

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

    # Global comparison — single aggregated query over all other diagnostics
    # (per-diagnostic queries here would be N+1 on every admin page load).
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

    avg_ttfv_global = (
        round(sum(ttfv_values) / len(ttfv_values) / 3600, 1)
        if ttfv_values else None
    )
    avg_ttr_global = (
        round(sum(ttr_values) / len(ttr_values) / 3600, 1)
        if ttr_values else None
    )

    avg_views_agg = (
        other_qs.filter(view_count__gt=0).aggregate(avg=Avg('view_count'))['avg']
    )
    avg_views_global = round(avg_views_agg, 1) if avg_views_agg is not None else None

    engagement_score = _compute_diagnostic_engagement_score(
        diagnostic, view_events, sections_data, unique_sessions,
        first_viewed_at, coverage_ratio,
    )

    return Response({
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
        'comparison': {
            'avg_time_to_first_view_hours': avg_ttfv_global,
            'avg_time_to_response_hours': avg_ttr_global,
            'avg_views': avg_views_global,
        },
        'engagement_score': engagement_score,
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def export_diagnostic_analytics_csv(request, diagnostic_id):
    """Export diagnostic analytics as a CSV file.

    Sections combined: summary, per-section engagement, session history,
    change log. Mirrors ``export_proposal_analytics_csv`` without view_mode
    or share-links.
    """
    import csv

    from django.http import HttpResponse as DjangoHttpResponse

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)

    response = DjangoHttpResponse(content_type='text/csv')
    filename = (
        f'analytics_diagnostic_{diagnostic.client_name or "cliente"}_'
        f'{diagnostic.id}.csv'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    writer.writerow([f'Diagnostic Analytics: {diagnostic.title}'])
    writer.writerow([f'Client: {diagnostic.client_name or ""}'])
    writer.writerow([f'Status: {diagnostic.status}'])
    writer.writerow([f'Total Views: {diagnostic.view_count}'])
    writer.writerow([])

    # Section engagement
    writer.writerow(['--- SECTION ENGAGEMENT ---'])
    writer.writerow([
        'Section Type', 'Section Title', 'Visit Count',
        'Total Time (s)', 'Avg Time (s)',
    ])
    section_stats = (
        DiagnosticSectionView.objects
        .filter(view_event__diagnostic=diagnostic)
        .values('section_type')
        .annotate(
            visit_count=Count('id'),
            total_time=Sum('time_spent_seconds'),
            avg_time=Avg('time_spent_seconds'),
        )
        .order_by('section_type')
    )
    for stat in section_stats:
        latest_title = (
            DiagnosticSectionView.objects
            .filter(
                view_event__diagnostic=diagnostic,
                section_type=stat['section_type'],
            )
            .order_by('-entered_at')
            .values_list('section_title', flat=True)
            .first()
        ) or stat['section_type']
        writer.writerow([
            stat['section_type'],
            latest_title,
            stat['visit_count'],
            round(stat['total_time'] or 0, 1),
            round(stat['avg_time'] or 0, 1),
        ])

    writer.writerow([])
    writer.writerow(['--- SESSION HISTORY ---'])
    writer.writerow([
        'Session ID', 'IP Address', 'Viewed At',
        'Sections Viewed', 'Total Time (s)',
    ])
    recent_events = (
        diagnostic.view_events.order_by('-viewed_at')
        .prefetch_related('section_views')[:100]
    )
    for event in recent_events:
        sv = list(event.section_views.all())
        writer.writerow([
            event.session_id,
            event.ip_address or '',
            event.viewed_at.isoformat(),
            len(sv),
            round(sum(s.time_spent_seconds for s in sv), 1),
        ])

    writer.writerow([])
    writer.writerow(['--- CHANGE LOG ---'])
    writer.writerow([
        'Date', 'Type', 'Field', 'Old Value', 'New Value', 'Description',
    ])
    for log in diagnostic.change_logs.order_by('-created_at')[:100]:
        writer.writerow([
            log.created_at.isoformat(),
            log.change_type,
            log.field_name,
            log.old_value,
            log.new_value,
            log.description,
        ])

    return response


# ──────────────────────────────────────────────────────────────────────────
# Admin — send actions
# ──────────────────────────────────────────────────────────────────────────

def _send_and_transition(diagnostic, kind: str):
    from content.services.diagnostic_email_service import (
        DiagnosticEmailService,
    )

    if kind == 'initial':
        target = WebAppDiagnostic.Status.SENT
        email_fn = DiagnosticEmailService.send_initial_to_client
    elif kind == 'final':
        target = WebAppDiagnostic.Status.SENT
        email_fn = DiagnosticEmailService.send_final_to_client
    else:
        return False, Response({'error': 'unknown_kind'},
                               status=http_status.HTTP_400_BAD_REQUEST)

    try:
        diagnostic_service.transition_status(
            diagnostic, target,
            actor_type=DiagnosticChangeLog.ActorType.SELLER,
        )
    except ValueError as exc:
        return False, Response(
            {'error': str(exc).split(':')[0], 'message': str(exc)},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    try:
        email_ok = email_fn(diagnostic)
    except Exception:
        logger.exception('Email send failed for diagnostic %s (%s)',
                         diagnostic.uuid, kind)
        email_ok = False

    if email_ok:
        diagnostic_service.log_change(
            diagnostic,
            change_type=DiagnosticChangeLog.ChangeType.EMAIL_SENT,
            description=f'Email «{kind}» enviado al cliente.',
            actor_type=DiagnosticChangeLog.ActorType.SYSTEM,
        )
    return True, email_ok


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_initial(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    ok, email_ok = _send_and_transition(diagnostic, 'initial')
    if not ok:
        return email_ok
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    body = DiagnosticDetailSerializer(diagnostic).data
    body['email_ok'] = bool(email_ok)
    return Response(body)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def mark_in_analysis(request, diagnostic_id):
    """Manual transition SENT → NEGOTIATING once the client authorized."""
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    try:
        diagnostic_service.transition_status(
            diagnostic, WebAppDiagnostic.Status.NEGOTIATING,
            actor_type=DiagnosticChangeLog.ActorType.SELLER,
        )
    except ValueError as exc:
        return Response(
            {'error': str(exc).split(':')[0], 'message': str(exc)},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    return Response(DiagnosticDetailSerializer(diagnostic).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_final(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    ok, email_ok = _send_and_transition(diagnostic, 'final')
    if not ok:
        return email_ok
    diagnostic = _admin_qs(include_attachments=True).get(pk=diagnostic.pk)
    body = DiagnosticDetailSerializer(diagnostic).data
    body['email_ok'] = bool(email_ok)
    return Response(body)


# ──────────────────────────────────────────────────────────────────────────
# Public — view / track / respond
# ──────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_public_diagnostic(request, diagnostic_uuid):
    diagnostic = get_object_or_404(
        WebAppDiagnostic.objects.select_related('client__user')
        .prefetch_related('sections'),
        uuid=diagnostic_uuid,
    )
    # view_count is bumped only by POST /track/ to avoid double-counting.
    return Response(PublicDiagnosticSerializer(diagnostic).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_public_diagnostic_by_slug(request, diagnostic_slug):
    """Retrieve a diagnostic by its editable slug for client viewing."""
    diagnostic = get_object_or_404(
        WebAppDiagnostic.objects.select_related('client__user')
        .prefetch_related('sections'),
        slug=diagnostic_slug,
    )
    return Response(PublicDiagnosticSerializer(diagnostic).data)


def _ensure_view_event(diagnostic, request, session_id):
    """Return the existing ViewEvent for (diagnostic, session) or create one.

    Safe under concurrency: (diagnostic, session_id) has a UniqueConstraint,
    so get_or_create collapses racing requests to a single row.
    """
    event, _ = DiagnosticViewEvent.objects.get_or_create(
        diagnostic=diagnostic,
        session_id=session_id,
        defaults={
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:2000],
        },
    )
    return event


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([TrackingAnonThrottle])
def track_public_diagnostic(request, diagnostic_uuid):
    """Create (or reuse) a DiagnosticViewEvent for this public visit."""
    diagnostic = get_object_or_404(WebAppDiagnostic, uuid=diagnostic_uuid)
    session_id = (request.data.get('session_id') or '')[:64] or 'anonymous'
    _ensure_view_event(diagnostic, request, session_id)
    diagnostic_service.register_view(diagnostic)
    return Response({'view_count': diagnostic.view_count})


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([TrackingAnonThrottle])
def track_diagnostic_section_view(request, diagnostic_uuid):
    """Record per-section time spent during a public visit."""
    diagnostic = get_object_or_404(WebAppDiagnostic, uuid=diagnostic_uuid)
    session_id = (request.data.get('session_id') or '')[:64]
    section_type = (request.data.get('section_type') or '')[:50]
    section_title = (request.data.get('section_title') or '')[:255]

    try:
        time_spent = float(request.data.get('time_spent_seconds') or 0)
    except (TypeError, ValueError):
        return Response(
            {'error': 'invalid_time_spent_seconds'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    if not session_id or not section_type:
        return Response(
            {'error': 'session_id_and_section_type_required'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    entered_at = None
    raw_entered_at = request.data.get('entered_at')
    if raw_entered_at:
        entered_at = parse_datetime(raw_entered_at)
    if entered_at is None:
        entered_at = timezone.now()

    view_event = _ensure_view_event(diagnostic, request, session_id)
    DiagnosticSectionView.objects.create(
        view_event=view_event,
        section_type=section_type,
        section_title=section_title,
        time_spent_seconds=max(0.0, time_spent),
        entered_at=entered_at,
    )
    return Response({'ok': True})


@api_view(['GET'])
@permission_classes([AllowAny])
def download_public_diagnostic_pdf(request, diagnostic_uuid):
    """Stream a PDF of the diagnostic's enabled sections."""
    diagnostic = get_object_or_404(
        WebAppDiagnostic.objects.select_related('client__user'),
        uuid=diagnostic_uuid,
    )
    if diagnostic.status not in diagnostic_service.PUBLIC_VISIBLE_STATUSES:
        return Response(
            {'error': 'not_available'},
            status=http_status.HTTP_404_NOT_FOUND,
        )

    pdf_bytes = DiagnosticPdfService.generate(diagnostic)
    if not pdf_bytes:
        return Response(
            {'error': 'pdf_generation_failed'},
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    created = diagnostic.created_at or timezone.now()
    filename = safe_pdf_filename(
        'Diagnostico',
        diagnostic.client_name or diagnostic.title or 'diagnostico',
        created.strftime('%d-%m-%y'),
    )

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def respond_public_diagnostic(request, diagnostic_uuid):
    diagnostic = get_object_or_404(WebAppDiagnostic, uuid=diagnostic_uuid)
    decision = (request.data.get('decision') or '').strip().lower()
    if decision not in ('accept', 'reject'):
        return Response(
            {'error': 'invalid_decision'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    target = (
        WebAppDiagnostic.Status.ACCEPTED
        if decision == 'accept'
        else WebAppDiagnostic.Status.REJECTED
    )
    try:
        diagnostic_service.transition_status(
            diagnostic, target,
            actor_type=DiagnosticChangeLog.ActorType.CLIENT,
        )
    except ValueError as exc:
        return Response(
            {'error': str(exc).split(':')[0], 'message': str(exc)},
            status=http_status.HTTP_409_CONFLICT,
        )
    return Response(PublicDiagnosticSerializer(diagnostic).data)


# ──────────────────────────────────────────────────────────────────────────
# Admin — attachments (files uploaded to a diagnostic)
# ──────────────────────────────────────────────────────────────────────────

_ATTACHMENT_ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg',
}
_ATTACHMENT_MAX_SIZE = 15 * 1024 * 1024  # 15 MB


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_diagnostic_attachments(request, diagnostic_id):
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    return Response(
        [serialize_diagnostic_attachment(a)
         for a in diagnostic.attachments.all()],
    )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def upload_diagnostic_attachment(request, diagnostic_id):
    from pathlib import Path

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file provided.'},
                        status=http_status.HTTP_400_BAD_REQUEST)

    ext = Path(file.name).suffix.lower()
    if ext not in _ATTACHMENT_ALLOWED_EXTENSIONS:
        allowed = ', '.join(sorted(_ATTACHMENT_ALLOWED_EXTENSIONS))
        return Response(
            {'error': f'File type {ext} not allowed. Allowed: {allowed}'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    if file.size > _ATTACHMENT_MAX_SIZE:
        return Response(
            {'error': 'File too large. Maximum size is 15 MB.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    document_type = request.data.get(
        'document_type', DiagnosticAttachment.DOC_TYPE_OTHER,
    )
    valid_types = {c[0] for c in DiagnosticAttachment.DOC_TYPE_CHOICES}
    if document_type not in valid_types:
        return Response(
            {'error': f'Invalid document_type: {document_type}'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    title = (request.data.get('title') or file.name).strip()[:300] or file.name
    custom_type_label = (request.data.get('custom_type_label') or '').strip()[:100]

    attachment = DiagnosticAttachment.objects.create(
        diagnostic=diagnostic,
        document_type=document_type,
        title=title,
        file=file,
        custom_type_label=(
            custom_type_label
            if document_type == DiagnosticAttachment.DOC_TYPE_OTHER
            else ''
        ),
        uploaded_by=request.user if request.user.is_authenticated else None,
    )
    return Response(
        serialize_diagnostic_attachment(attachment),
        status=http_status.HTTP_201_CREATED,
    )


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_diagnostic_attachment(request, diagnostic_id, attachment_id):
    attachment = get_object_or_404(
        DiagnosticAttachment,
        pk=attachment_id, diagnostic_id=diagnostic_id,
    )
    if attachment.is_generated:
        return Response(
            {'error': 'No se puede eliminar un documento generado por el sistema; regénerelo desde Editar parámetros.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    if attachment.file:
        attachment.file.delete(save=False)
    attachment.delete()
    return Response(status=http_status.HTTP_204_NO_CONTENT)


_SEND_ALLOWED_DOC_KEYS = {DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY}


def _diagnostic_pdf_meta(diagnostic):
    """Return ``(client_label, date_str)`` used to build PDF filenames."""
    client_label = (
        getattr(diagnostic.client, 'company_name', None)
        or diagnostic.title
        or 'cliente'
    )
    date_str = (diagnostic.created_at or timezone.now()).strftime('%Y-%m-%d')
    return client_label, date_str


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_diagnostic_attachments(request, diagnostic_id):
    """Email selected DiagnosticAttachments + system-generated docs to the client."""
    from content.services import diagnostic_documents_service
    from content.services.confidentiality_pdf_service import generate_confidentiality_pdf
    from content.services.pdf_utils import add_watermark_to_pdf, safe_pdf_filename

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)

    attachment_ids = request.data.get('attachment_ids') or []
    documents = request.data.get('documents') or []
    if not isinstance(attachment_ids, list):
        attachment_ids = []
    if not isinstance(documents, list):
        documents = []

    invalid = set(documents) - _SEND_ALLOWED_DOC_KEYS
    if invalid:
        return Response(
            {'error': f'Claves de documento no reconocidas: {sorted(invalid)}'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    if not attachment_ids and not documents:
        return Response(
            {'error': 'Debes seleccionar al menos un documento.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    extra_files = []
    if DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY in documents:
        has_params = bool(diagnostic.confidentiality_params)
        has_generated = diagnostic.attachments.filter(
            document_type=DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY,
            is_generated=True,
        ).exists()
        if not has_params and not has_generated:
            return Response(
                {'error': 'Debes generar el Acuerdo de Confidencialidad antes de enviarlo (Documentos → Generar acuerdo).'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        nda_bytes = generate_confidentiality_pdf(diagnostic, draft=True)
        if not nda_bytes:
            return Response(
                {'error': 'No se pudo generar el Acuerdo de Confidencialidad.'},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        watermarked = add_watermark_to_pdf(nda_bytes)
        client_label, date_str = _diagnostic_pdf_meta(diagnostic)
        extra_files.append((
            safe_pdf_filename('Acuerdo_Confidencialidad', client_label, date_str),
            watermarked,
            'application/pdf',
        ))

    ok, error = diagnostic_documents_service.send_attachments_to_client(
        diagnostic,
        attachment_ids=attachment_ids,
        subject=request.data.get('subject') or '',
        greeting=request.data.get('greeting') or '',
        body=request.data.get('body') or '',
        footer=request.data.get('footer') or '',
        document_descriptions=request.data.get('document_descriptions') or [],
        extra_files=extra_files,
    )
    if not ok:
        return Response(
            {'error': error or 'Error al enviar.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    diagnostic_service.log_change(
        diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.EMAIL_SENT,
        description='Adjuntos enviados al cliente.',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    return Response({'message': 'Documentos enviados.'})


# ──────────────────────────────────────────────────────────────────────────
# Acuerdo de Confidencialidad (NDA) PDF
# ──────────────────────────────────────────────────────────────────────────


def _generate_and_save_confidentiality_pdf(diagnostic):
    """Generate the NDA PDF for *diagnostic* and persist it as a generated
    DiagnosticAttachment. Replaces any prior generated NDA in place.
    """
    from django.core.files.base import ContentFile

    from content.services.confidentiality_pdf_service import generate_confidentiality_pdf
    from content.services.pdf_utils import safe_pdf_filename

    pdf_bytes = generate_confidentiality_pdf(diagnostic)
    if not pdf_bytes:
        return None

    client_label, date_str = _diagnostic_pdf_meta(diagnostic)
    filename = safe_pdf_filename('Acuerdo_Confidencialidad', client_label, date_str)

    existing = diagnostic.attachments.filter(
        document_type=DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY,
        is_generated=True,
    ).first()
    if existing:
        if existing.file:
            existing.file.delete(save=False)
        existing.file.save(filename, ContentFile(pdf_bytes), save=False)
        existing.title = 'Acuerdo de Confidencialidad'
        existing.save()
        return existing

    return DiagnosticAttachment.objects.create(
        diagnostic=diagnostic,
        document_type=DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY,
        title='Acuerdo de Confidencialidad',
        file=ContentFile(pdf_bytes, name=filename),
        is_generated=True,
        uploaded_by=None,
    )


@api_view(['POST', 'PATCH'])
@permission_classes([IsAdminUser])
def update_confidentiality_params(request, diagnostic_id):
    """Update NDA params on the diagnostic and (re)generate the stored PDF."""
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    serializer = ConfidentialityParamsSerializer(
        data=request.data.get('confidentiality_params', request.data),
    )
    serializer.is_valid(raise_exception=True)

    diagnostic.confidentiality_params = serializer.validated_data
    diagnostic.save(update_fields=['confidentiality_params', 'updated_at'])

    attachment = _generate_and_save_confidentiality_pdf(diagnostic)
    if not attachment:
        return Response(
            {'error': 'Parámetros guardados pero no se pudo generar el PDF.'},
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    diagnostic_service.log_change(
        diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.UPDATED,
        field_name='confidentiality_agreement',
        description='Acuerdo de Confidencialidad generado/actualizado.',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    return Response({
        'confidentiality_params': diagnostic.confidentiality_params,
        'attachment': serialize_diagnostic_attachment(attachment),
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def generate_confidentiality_pdf_view(request, diagnostic_id):
    """Force-regenerate the NDA PDF using the currently stored params."""
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    attachment = _generate_and_save_confidentiality_pdf(diagnostic)
    if not attachment:
        return Response(
            {'error': 'No se pudo generar el PDF.'},
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response({'attachment': serialize_diagnostic_attachment(attachment)})


def _confidentiality_filename(diagnostic, prefix):
    from content.services.pdf_utils import safe_pdf_filename

    client_label, date_str = _diagnostic_pdf_meta(diagnostic)
    return safe_pdf_filename(prefix, client_label, date_str)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def download_confidentiality_pdf(request, diagnostic_id):
    from django.http import FileResponse

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    attachment = diagnostic.attachments.filter(
        document_type=DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY,
        is_generated=True,
    ).first()
    if not attachment or not attachment.file:
        return Response(
            {'error': 'El acuerdo aún no ha sido generado.'},
            status=http_status.HTTP_404_NOT_FOUND,
        )
    return FileResponse(
        attachment.file.open('rb'),
        content_type='application/pdf',
        filename=_confidentiality_filename(diagnostic, 'Acuerdo_Confidencialidad'),
    )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def download_draft_confidentiality_pdf(request, diagnostic_id):
    from content.services.confidentiality_pdf_service import generate_confidentiality_pdf
    from content.services.pdf_utils import add_watermark_to_pdf

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    pdf_bytes = generate_confidentiality_pdf(diagnostic, draft=True)
    if not pdf_bytes:
        return Response(
            {'error': 'No se pudo generar el borrador.'},
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    filename = _confidentiality_filename(diagnostic, 'Borrador_Acuerdo_Confidencialidad')
    return inline_pdf_response(add_watermark_to_pdf(pdf_bytes), filename)


# ──────────────────────────────────────────────────────────────────────────
# Admin — email composer (history + send)
# ──────────────────────────────────────────────────────────────────────────

_COMPOSED_EMAIL_ALLOWED_EXT = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg',
}
_COMPOSED_EMAIL_MAX_FILE = 15 * 1024 * 1024  # 15 MB


def _resolve_diagnostic_doc_refs(diagnostic, doc_refs):
    """
    Resolve diagnostic doc_refs into email attachment tuples.

    Supported sources:
      - ``nda_final``            → NDA PDF (final, from DiagnosticAttachment)
      - ``nda_draft``            → NDA draft PDF (watermarked, freshly generated)
      - ``template`` (slug)      → static markdown diagnostic template
      - ``attachment`` (id)      → uploaded DiagnosticAttachment file
    """
    import mimetypes

    from content.services.confidentiality_pdf_service import generate_confidentiality_pdf
    from content.services.pdf_utils import add_watermark_to_pdf
    from content.views._doc_refs import DocRefError
    from content.views.diagnostic_template import TEMPLATES as DIAGNOSTIC_TEMPLATES
    from content.views.diagnostic_template import TEMPLATES_DIR as DIAGNOSTIC_TEMPLATES_DIR

    attachment_ids = [r.get('id') for r in doc_refs
                      if isinstance(r, dict) and r.get('source') == 'attachment']
    attachments_by_id = {
        att.pk: att
        for att in diagnostic.attachments.filter(pk__in=attachment_ids)
    } if attachment_ids else {}

    out = []

    for ref in doc_refs:
        if not isinstance(ref, dict):
            raise DocRefError('Cada doc_ref debe ser un objeto.')
        source = ref.get('source')

        if source == 'nda_final':
            pdf_bytes = generate_confidentiality_pdf(diagnostic)
            if not pdf_bytes:
                raise DocRefError(
                    'No se pudo generar el acuerdo de confidencialidad. '
                    'Completa los parámetros en la pestaña Documentos.',
                )
            out.append((
                _confidentiality_filename(diagnostic, 'Acuerdo_Confidencialidad'),
                pdf_bytes,
                'application/pdf',
            ))
        elif source == 'nda_draft':
            pdf_bytes = generate_confidentiality_pdf(diagnostic, draft=True)
            if not pdf_bytes:
                raise DocRefError(
                    'No se pudo generar el borrador del acuerdo.',
                )
            out.append((
                _confidentiality_filename(diagnostic, 'Borrador_Acuerdo_Confidencialidad'),
                add_watermark_to_pdf(pdf_bytes),
                'application/pdf',
            ))
        elif source == 'template':
            slug = ref.get('slug')
            meta = DIAGNOSTIC_TEMPLATES.get(slug)
            if meta is None:
                raise DocRefError(f'Plantilla {slug!r} no existe.')
            path = DIAGNOSTIC_TEMPLATES_DIR / meta['filename']
            try:
                content_bytes = path.read_bytes()
            except (FileNotFoundError, OSError):
                raise DocRefError(f'No se pudo leer la plantilla {slug!r}.')
            out.append((meta['filename'], content_bytes, 'text/markdown'))
        elif source == 'attachment':
            attachment_id = ref.get('id')
            attachment = attachments_by_id.get(attachment_id)
            if attachment is None:
                raise DocRefError(f'Adjunto {attachment_id} no existe.')
            if not attachment.file:
                raise DocRefError(f'Adjunto "{attachment.title}" no tiene archivo.')
            with attachment.file.open('rb') as fh:
                data = fh.read()
            name = attachment.file.name.rsplit('/', 1)[-1]
            mime = mimetypes.guess_type(name)[0] or 'application/octet-stream'
            out.append((name, data, mime))
        else:
            raise DocRefError(f'Fuente de documento desconocida: {source!r}.')

    return out


def _parse_diagnostic_email(request, diagnostic):
    import json
    import mimetypes
    from datetime import timedelta
    from pathlib import Path

    from django.core.exceptions import ValidationError as DjangoValidationError
    from django.core.validators import validate_email

    from content.models import EmailLog
    from content.services.diagnostic_email_service import DiagnosticEmailService

    one_min_ago = timezone.now() - timedelta(minutes=1)
    recent = EmailLog.objects.filter(
        template_key=DiagnosticEmailService.TEMPLATE_CUSTOM,
        metadata__diagnostic_uuid=str(diagnostic.uuid),
        sent_at__gte=one_min_ago,
    ).exists()
    if recent:
        return None, Response(
            {'error': 'Espera al menos 1 minuto entre envíos.'},
            status=http_status.HTTP_429_TOO_MANY_REQUESTS,
        )

    recipient_email = (request.data.get('recipient_email') or '').strip()
    if not recipient_email:
        return None, Response(
            {'error': 'El campo destinatario es obligatorio.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    try:
        validate_email(recipient_email)
    except DjangoValidationError:
        return None, Response(
            {'error': 'El correo del destinatario no es válido.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    subject = (request.data.get('subject') or '').strip()
    if not subject:
        return None, Response(
            {'error': 'El asunto es obligatorio.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    greeting = (request.data.get('greeting') or '').strip()
    footer = (request.data.get('footer') or '').strip()

    raw_sections = request.data.get('sections', '[]')
    try:
        sections = (
            json.loads(raw_sections) if isinstance(raw_sections, str)
            else raw_sections
        )
    except (json.JSONDecodeError, TypeError):
        return None, Response(
            {'error': 'Las secciones deben ser un JSON válido.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(sections, list) or not any(
        s.strip() for s in sections if isinstance(s, str)
    ):
        return None, Response(
            {'error': 'Debe incluir al menos una sección con contenido.'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    sections = [s for s in sections if isinstance(s, str) and s.strip()]

    attachments = []
    for f in request.FILES.getlist('attachments'):
        ext = Path(f.name).suffix.lower()
        if ext not in _COMPOSED_EMAIL_ALLOWED_EXT:
            return None, Response(
                {'error': f'Tipo de archivo {ext} no permitido.'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        if f.size > _COMPOSED_EMAIL_MAX_FILE:
            return None, Response(
                {'error': f'El archivo "{f.name}" excede el límite de 15 MB.'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        mime_type = mimetypes.guess_type(f.name)[0] or 'application/octet-stream'
        attachments.append((f.name, f.read(), mime_type))

    attach_confidentiality = str(
        request.data.get('attach_confidentiality', '')
    ).strip().lower() in ('1', 'true', 'yes', 'on')
    if attach_confidentiality:
        from content.services.confidentiality_pdf_service import generate_confidentiality_pdf

        pdf_bytes = generate_confidentiality_pdf(diagnostic)
        if not pdf_bytes:
            return None, Response(
                {'error': 'No se pudo generar el acuerdo de confidencialidad. '
                          'Completa los parámetros en la pestaña Documentos.'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        nda_filename = _confidentiality_filename(diagnostic, 'Acuerdo_Confidencialidad')
        attachments.append((nda_filename, pdf_bytes, 'application/pdf'))

    # ── References to existing documents (NDA, MD templates, uploads) ──
    from content.views._doc_refs import DocRefError, parse_doc_refs_field

    doc_refs, error_response = parse_doc_refs_field(request)
    if error_response:
        return None, error_response
    try:
        attachments.extend(_resolve_diagnostic_doc_refs(diagnostic, doc_refs))
    except DocRefError as err:
        return None, Response(
            {'error': str(err)},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    return {
        'recipient_email': recipient_email,
        'subject': subject,
        'greeting': greeting,
        'sections': sections,
        'footer': footer,
        'attachments': attachments or None,
    }, None


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_diagnostic_email(request, diagnostic_id):
    from content.services.diagnostic_email_service import DiagnosticEmailService

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    parsed, error = _parse_diagnostic_email(request, diagnostic)
    if error:
        return error

    ok = DiagnosticEmailService.send_custom_email(
        diagnostic,
        recipient_email=parsed['recipient_email'],
        subject=parsed['subject'],
        greeting=parsed['greeting'],
        sections=parsed['sections'],
        footer=parsed['footer'],
        attachments=parsed['attachments'],
    )
    if ok:
        diagnostic_service.log_change(
            diagnostic,
            change_type=DiagnosticChangeLog.ChangeType.EMAIL_SENT,
            description=f'Correo enviado a {parsed["recipient_email"]}.',
            actor_type=DiagnosticChangeLog.ActorType.SELLER,
        )
        return Response({'message': f'Correo enviado a {parsed["recipient_email"]}.'})
    return Response(
        {'error': 'Error al enviar el correo. Intenta de nuevo.'},
        status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_diagnostic_email_defaults(request, diagnostic_id):
    from content.services.diagnostic_email_service import DiagnosticEmailService

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    return Response(DiagnosticEmailService.get_defaults(diagnostic))


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_diagnostic_emails(request, diagnostic_id):
    from content.services.diagnostic_email_service import DiagnosticEmailService

    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    try:
        page = int(request.query_params.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    return Response(DiagnosticEmailService.list_emails(diagnostic, page=page))


@api_view(['POST'])
@permission_classes([IsAdminUser])
def generate_diagnostic_email_markdown_attachment(request, diagnostic_id):
    """Generate a transient PDF from markdown for diagnostic email attachment."""
    diagnostic = get_object_or_404(WebAppDiagnostic, pk=diagnostic_id)
    return render_markdown_pdf_response(request, client_name=diagnostic.client_name or '')


# ---------------------------------------------------------------------------
# Diagnostic Default Config
# ---------------------------------------------------------------------------

@api_view(['GET', 'PUT'])
@permission_classes([IsAdminUser])
def diagnostic_defaults(request):
    """GET — DB config for *lang* or hardcoded fallback. PUT — upsert."""
    lang = request.query_params.get('lang', request.data.get('language', 'es'))
    if lang not in ('es', 'en'):
        return Response(
            {'detail': 'lang must be "es" or "en".'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    if request.method == 'GET':
        config = DiagnosticDefaultConfig.objects.filter(language=lang).first()
        if config:
            return Response(DiagnosticDefaultConfigSerializer(config).data)
        return Response({
            'id': None,
            'language': lang,
            'sections_json': diagnostic_service.get_hardcoded_section_specs(),
            'payment_initial_pct': diagnostic_service.DEFAULT_PAYMENT_INITIAL_PCT,
            'payment_final_pct': diagnostic_service.DEFAULT_PAYMENT_FINAL_PCT,
            'default_currency': WebAppDiagnostic.Currency.COP,
            'default_investment_amount': None,
            'default_duration_label': '',
            'expiration_days': diagnostic_service.DEFAULT_EXPIRATION_DAYS,
            'reminder_days': diagnostic_service.DEFAULT_REMINDER_DAYS,
            'urgency_reminder_days': diagnostic_service.DEFAULT_URGENCY_REMINDER_DAYS,
            'created_at': None,
            'updated_at': None,
        })

    config = DiagnosticDefaultConfig.objects.filter(language=lang).first()
    payload = dict(request.data)
    payload['language'] = lang
    if 'sections_json' not in payload:
        if config and config.sections_json:
            payload['sections_json'] = config.sections_json
        else:
            payload['sections_json'] = diagnostic_service.get_hardcoded_section_specs()

    serializer = (
        DiagnosticDefaultConfigSerializer(config, data=payload)
        if config
        else DiagnosticDefaultConfigSerializer(data=payload)
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=http_status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reset_diagnostic_defaults(request):
    """Delete the DB-backed defaults for a language; reverts to hardcoded seed."""
    lang = request.data.get('language', 'es')
    if lang not in ('es', 'en'):
        return Response(
            {'detail': 'language must be "es" or "en".'},
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    deleted_count, _ = DiagnosticDefaultConfig.objects.filter(language=lang).delete()
    return Response(
        {'status': 'reset', 'deleted': deleted_count > 0},
        status=http_status.HTTP_200_OK,
    )
