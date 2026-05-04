import copy
import logging
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from content.throttles import TrackingAnonThrottle
from content.utils import get_client_ip

from content.models import (
    BusinessProposal, ProposalAlert, ProposalSection,
    ProposalViewEvent, ProposalSectionView,
    ProposalChangeLog, ProposalShareLink,
    ProposalDefaultConfig,
)
from content.serializers.proposal import (
    ContractParamsSerializer,
    ProposalAlertSerializer,
    ProposalCreateUpdateSerializer,
    ProposalDefaultConfigSerializer,
    ProposalDetailSerializer,
    ProposalFromJSONSerializer,
    ProposalListSerializer,
    ProposalProjectStageSerializer,
    ProposalSectionUpdateSerializer,
    ProposalShareLinkSerializer,
    SECTION_KEY_MAP,
    SECTION_TYPE_TO_KEY,
    serialize_proposal_document,
)
from content.views._email_attachment import render_markdown_pdf_response

logger = logging.getLogger(__name__)

# Public technical mode tracks synthetic panels as technical_document_public;
# the DB section is technical_document. Metrics union both.
TECHNICAL_DOCUMENT_TRACKING_TYPES = frozenset({
    'technical_document',
    'technical_document_public',
})

# Sections that signal commercial intent — used to detect skipped key content.
_KEY_PROPOSAL_SECTIONS = frozenset({
    'investment', 'timeline', 'functional_requirements', 'final_note',
})

# Spanish labels for the three client-selectable view modes.
VIEW_MODE_LABELS = {'executive': 'ejecutiva', 'detailed': 'completa', 'technical': 'técnica'}

# Ordered fragments of the technical document panel, matching frontend utils/technicalProposalPanels.js
_TECHNICAL_FRAGMENT_ORDER = [
    'intro', 'stack', 'architecture', 'dataModel', 'growthReadiness',
    'epics', 'api', 'integrations', 'environments', 'security',
    'performance', 'backups', 'quality', 'decisions',
]
_TECHNICAL_FRAGMENT_TITLES = {
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


def _proposal_admin_response(request, proposal, delivery=None):
    """Serialize a proposal for the admin panel, optionally with delivery info."""
    payload = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': True}
    ).data
    if delivery is not None:
        payload['email_delivery'] = delivery
    return Response(payload, status=status.HTTP_200_OK)


def _row_has(row, keys):
    """True if *row* is a dict with at least one non-empty string among *keys*."""
    if not isinstance(row, dict):
        return False
    return any(_ne(row.get(k)) for k in keys)


def _technical_fragment_has_content(fragment, doc):
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


_COMPUTED_ALERT_TYPES = frozenset({
    'not_viewed',
    'not_responded',
    'expiring_soon',
    'seller_inactive',
    'zombie',
    'zombie_draft',
    'zombie_sent_stale',
    'late_return',
})
_COMPUTED_ALERT_DISMISS_PREFIX = '__computed_dismissed__:'


def _computed_alert_key(proposal_id, alert_type, ref_date):
    return f'{proposal_id}-{alert_type}-{ref_date or ""}'


def _dashboard_top_dropoff_allowlist():
    """Section types used for global top_dropoff KPI (excludes technical doc)."""
    return frozenset(
        c for c, _ in ProposalSection.SectionType.choices
        if c != 'technical_document'
    )


def _csv_analytics_section_group(section_type):
    """Human-readable group for CSV export (technical variants align)."""
    if section_type == 'technical_document_public':
        return 'Detalle técnico (vista pública)'
    if section_type == 'technical_document':
        return 'Detalle técnico'
    return ''


def _safe_decimal(value, default=Decimal('0')):
    """Safely coerce unknown numeric input to Decimal."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


# Canonical prefixes used by the frontend calculator to distinguish
# calculator modules (additive, priced) from regular grouped requirements.
# Persisted ``selected_modules`` payloads must round-trip through these.
_CALC_MODULE_PREFIX = 'module-'
_REGULAR_GROUP_PREFIX = 'group-'


def _selected_group_ids_from_modules(selected_modules):
    """Normalize selected module ids to bare group ids."""
    if not isinstance(selected_modules, list):
        return set()

    group_ids = set()
    for raw in selected_modules:
        if raw in (None, ''):
            continue
        mod_id = str(raw).strip()
        if not mod_id:
            continue
        if mod_id.startswith(_CALC_MODULE_PREFIX):
            group_ids.add(mod_id[len(_CALC_MODULE_PREFIX):])
        elif mod_id.startswith(_REGULAR_GROUP_PREFIX):
            group_ids.add(mod_id[len(_REGULAR_GROUP_PREFIX):])
        else:
            group_ids.add(mod_id)
    return group_ids


def _normalize_selected_module_ids(selected, fr_content_json):
    """Thin wrapper around the shared normalizer in ``proposal_service``."""
    from content.services.proposal_service import normalize_selected_module_ids
    return normalize_selected_module_ids(selected, fr_content_json)


def _calculator_price_percent_by_group_id(fr_content_json):
    """
    Extract calculator-module price percentages from functional requirements JSON.
    """
    if not isinstance(fr_content_json, dict):
        return {}

    groups = list(fr_content_json.get('groups') or [])
    additional = list(fr_content_json.get('additionalModules') or [])
    price_by_group = {}

    for group in groups + additional:
        if not isinstance(group, dict):
            continue
        if not group.get('is_calculator_module'):
            continue
        group_id = str(group.get('id') or '').strip()
        if not group_id:
            continue
        pct = _safe_decimal(group.get('price_percent'), default=None)
        if pct is None or pct <= 0:
            continue
        price_by_group[group_id] = pct

    return price_by_group


def _calculate_effective_total_investment(
    base_total,
    selected_modules,
    fr_content_json,
    has_confirmed,
):
    """
    Compute effective investment shown in panel metrics:
    base investment + selected additional calculator modules.

    The ``has_confirmed`` flag determines whether ``selected_modules`` is the
    source of truth. When ``True``, the persisted list is used literally
    (an empty list means "client confirmed zero modules"). When ``False``,
    the list is ignored and the admin's ``selected`` / ``default_selected``
    flags in the FR content JSON are used as the initial scope — the client
    has not customized yet, so they will see the admin-configured defaults.
    """
    base = _safe_decimal(base_total).quantize(Decimal('0.01'))

    if has_confirmed:
        selected_group_ids = _selected_group_ids_from_modules(selected_modules)
    else:
        from content.services.proposal_service import (
            admin_default_calculator_group_ids,
        )
        selected_group_ids = admin_default_calculator_group_ids(fr_content_json)

    if not selected_group_ids:
        return base

    price_by_group = _calculator_price_percent_by_group_id(fr_content_json)
    if not price_by_group:
        return base

    extras = Decimal('0')
    for group_id in selected_group_ids:
        pct = price_by_group.get(group_id)
        if pct is None:
            continue
        extras += (base * pct / Decimal('100')).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP,
        )

    return (base + extras).quantize(Decimal('0.01'))


def _effective_total_for_proposal(proposal):
    """Single-proposal version of :func:`_build_effective_totals_map`."""
    fr_section = proposal.sections.filter(
        section_type=ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS,
    ).only('content_json').first()
    fr_content = fr_section.content_json if fr_section else None
    return _calculate_effective_total_investment(
        proposal.total_investment,
        proposal.selected_modules,
        fr_content,
        has_confirmed=proposal.has_confirmed_module_selection,
    )


def _build_effective_totals_map(proposals):
    """Return {proposal_id: effective_total_decimal} for a proposal iterable."""
    proposal_list = list(proposals)
    if not proposal_list:
        return {}

    proposal_ids = [p.id for p in proposal_list]
    fr_content_by_proposal = dict(
        ProposalSection.objects
        .filter(
            proposal_id__in=proposal_ids,
            section_type='functional_requirements',
        )
        .values_list('proposal_id', 'content_json')
    )
    # Batch the confirmed-selection check so the per-proposal property
    # access below does not issue one EXISTS query per row.
    confirmed_ids = set(
        ProposalChangeLog.objects
        .filter(proposal_id__in=proposal_ids, change_type='calc_confirmed')
        .values_list('proposal_id', flat=True)
        .distinct()
    )

    return {
        p.id: _calculate_effective_total_investment(
            p.total_investment,
            p.selected_modules,
            fr_content_by_proposal.get(p.id),
            has_confirmed=p.id in confirmed_ids,
        )
        for p in proposal_list
    }


def _resync_investment_from_modules(proposal, fr_content_json):
    """Keep the investment section in sync with ``proposal.total_investment``.

    ``content_json.totalInvestment`` must always reflect the BASE investment
    (the number the admin typed in the General tab). It is used downstream
    as the basis for hosting calculations and other percent-derived values,
    so it must never be overwritten with the client's personalized total.

    ``paymentOptions`` descriptions *do* scale on the effective total,
    because those strings represent the actual amounts the client will pay
    after customizing their module selection.
    """
    effective = _calculate_effective_total_investment(
        proposal.total_investment,
        proposal.selected_modules,
        fr_content_json,
        has_confirmed=proposal.has_confirmed_module_selection,
    )
    inv_section = proposal.sections.filter(section_type=ProposalSection.SectionType.INVESTMENT).first()
    if not inv_section or not inv_section.content_json:
        return
    base_total = int(_safe_decimal(proposal.total_investment))
    base_formatted = f'${base_total:,}'.replace(',', '.')
    cj = dict(inv_section.content_json)
    currency_changed = cj.get('currency') != proposal.currency
    total_changed = cj.get('totalInvestment') != base_formatted

    # paymentOptions descriptions depend on the effective total; rebuild
    # unconditionally when paymentOptions exist so outdated amounts from a
    # prior selection do not leak through.
    payment_changed = False
    if cj.get('paymentOptions'):
        for opt in cj['paymentOptions']:
            pct_match = re.search(r'(\d+)%', opt.get('label', ''))
            if not pct_match:
                continue
            pct = Decimal(pct_match.group(1)) / Decimal(100)
            amount = int(effective * pct)
            new_desc = f'${amount:,}'.replace(',', '.') + f' {proposal.currency}'
            if opt.get('description') != new_desc:
                opt['description'] = new_desc
                payment_changed = True

    if not currency_changed and not total_changed and not payment_changed:
        return
    cj['totalInvestment'] = base_formatted
    cj['currency'] = proposal.currency
    inv_section.content_json = cj
    inv_section.save(update_fields=['content_json'])


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------

def _serve_public_proposal(request, proposal):
    """Shared handler for the public proposal endpoint.

    Implements the full view-count / expired / alerts / analytics pipeline.
    """
    if not proposal.is_active:
        return Response(
            {'error': 'This proposal is not available.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    is_expired = proposal.is_expired
    expired_meta = None

    if is_expired:
        if proposal.status != BusinessProposal.Status.EXPIRED:
            proposal.status = BusinessProposal.Status.EXPIRED
            proposal.save(update_fields=['status'])

        # Post-expiration visit alert — high-intent signal
        if not proposal.post_expiration_alert_sent_at:
            try:
                ProposalAlert.objects.create(
                    proposal=proposal,
                    alert_type='post_expiration_visit',
                    message=(
                        f'{proposal.client_name} abrió la propuesta expirada '
                        f'"{proposal.title}". Señal de alto interés.'
                    ),
                    alert_date=timezone.now(),
                )
                from content.services.proposal_email_service import (
                    ProposalEmailService,
                )
                ProposalEmailService.send_post_expiration_visit_alert(proposal)
                proposal.post_expiration_alert_sent_at = timezone.now()
                proposal.save(update_fields=['post_expiration_alert_sent_at'])
            except Exception:
                logger.exception(
                    'Failed to send post-expiration alert for proposal %s',
                    proposal.uuid,
                )

        # Build WhatsApp link for recovery CTA
        from urllib.parse import quote as _url_quote
        wa_number = getattr(settings, 'WHATSAPP_CONTACT_NUMBER', '')
        wa_msg = _url_quote(
            f'Hola, me interesa retomar la propuesta "{proposal.title}". '
            f'Link: {proposal.public_url}'
        )
        wa_url = f'https://wa.me/{wa_number}?text={wa_msg}' if wa_number else ''
        seller_name = getattr(settings, 'SELLER_DISPLAY_NAME', 'nuestro equipo')

        expired_meta = {
            'expired_at': (
                proposal.expires_at.isoformat()
                if proposal.expires_at else None
            ),
            'seller_name': seller_name,
            'whatsapp_url': wa_url,
        }

    # Admin preview detection — skip all analytics when staff views
    # Detects by Django session cookie (automatic, no query param needed)
    is_preview = (
        request.user.is_authenticated
        and request.user.is_staff
    )

    # Only record views/metrics for proposals that have been sent (not drafts)
    # Skip entirely for admin previews to avoid polluting analytics
    is_first_view = False
    if proposal.status != BusinessProposal.Status.DRAFT and not is_preview:
        proposal.view_count += 1
        update_fields = ['view_count']

        is_first_view = proposal.first_viewed_at is None
        if is_first_view:
            proposal.first_viewed_at = timezone.now()
            update_fields.append('first_viewed_at')

        if proposal.status == BusinessProposal.Status.SENT:
            proposal.status = BusinessProposal.Status.VIEWED
            update_fields.append('status')

        proposal.save(update_fields=update_fields)

    # Send real-time notification to sales team on first view (async)
    if is_first_view and not is_preview:
        try:
            from content.tasks import notify_first_view
            notify_first_view(proposal.id)
        except Exception:
            logger.exception(
                'Failed to queue first-view notification for proposal %s',
                proposal.uuid,
            )

    # 3.4 — Post-rejection revisit alert (high-intent signal)
    #        Enhanced: only fire when rejection happened 7+ days ago
    is_reengagement = request.query_params.get('ref') == 'reengagement'
    if (
        not is_preview
        and proposal.status == BusinessProposal.Status.REJECTED
        and not is_reengagement
        and not getattr(proposal, '_post_rejection_alert_sent', False)
    ):
        from datetime import timedelta as _td
        rejection_gap_ok = (
            proposal.responded_at
            and proposal.responded_at + _td(days=7) < timezone.now()
        )
        if rejection_gap_ok:
            existing = ProposalAlert.objects.filter(
                proposal=proposal, alert_type='post_rejection_revisit',
            ).exists()
            if not existing:
                try:
                    ProposalAlert.objects.create(
                        proposal=proposal,
                        alert_type='post_rejection_revisit',
                        message=(
                            f'{proposal.client_name} revisitó la propuesta rechazada '
                            f'"{proposal.title}" después de 7+ días. Posible reconsideración.'
                        ),
                        alert_date=timezone.now(),
                    )
                    from content.services.proposal_email_service import (
                        ProposalEmailService,
                    )
                    ProposalEmailService.send_post_rejection_revisit_alert(
                        proposal
                    )
                except Exception:
                    logger.exception(
                        'Failed to create post-rejection revisit alert for %s',
                        proposal.uuid,
                    )

    serializer = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': False}
    )
    response_data = serializer.data
    if is_preview:
        response_data['is_admin_preview'] = True
    if expired_meta:
        response_data['expired_meta'] = expired_meta
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_public_proposal(request, proposal_uuid):
    """Retrieve a proposal by UUID for client viewing."""
    proposal = get_object_or_404(
        BusinessProposal.objects.select_related('client__user'),
        uuid=proposal_uuid,
    )
    return _serve_public_proposal(request, proposal)


@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_public_proposal_by_slug(request, proposal_slug):
    """Retrieve a proposal by its editable slug for client viewing."""
    proposal = get_object_or_404(
        BusinessProposal.objects.select_related('client__user'),
        slug=proposal_slug,
    )
    return _serve_public_proposal(request, proposal)


@api_view(['GET'])
@permission_classes([AllowAny])
def download_proposal_pdf(request, proposal_uuid):
    """
    Generate and download a PDF of the proposal using ReportLab.
    """
    proposal = get_object_or_404(BusinessProposal, uuid=proposal_uuid)

    if proposal.is_expired:
        return Response(
            {'error': 'This proposal has expired.'},
            status=status.HTTP_410_GONE,
        )

    from content.services.proposal_pdf_service import (
        ProposalPdfService,
        default_selected_modules_from_content,
    )

    doc_variant = (request.query_params.get('doc') or '').strip().lower()
    selected_modules_param = request.query_params.get('selected_modules', '')
    selected_modules = (
        [m.strip() for m in selected_modules_param.split(',') if m.strip()]
        if selected_modules_param
        else None
    )
    # Derive defaults from current content_json so admin toggles of
    # additionalModules[i].selected propagate to the PDF even when the
    # client never opened the calculator (localStorage empty).
    if selected_modules is None:
        selected_modules = default_selected_modules_from_content(proposal)
    else:
        # Legacy query payloads may arrive with bare group ids — match the
        # canonical prefixed form the renderer uses.
        from content.services.proposal_service import normalize_selected_module_ids
        fr_section = proposal.sections.filter(
            section_type=ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS,
        ).only('content_json').first()
        selected_modules = normalize_selected_module_ids(
            selected_modules,
            fr_section.content_json if fr_section else None,
        )

    if doc_variant == 'technical':
        from content.services.technical_document_pdf import generate_technical_document_pdf

        pdf_bytes = generate_technical_document_pdf(
            proposal, selected_modules=selected_modules
        )
        if not pdf_bytes:
            return Response(
                {'error': 'Technical document is not available for this proposal.'},
                status=status.HTTP_404_NOT_FOUND,
            )
    else:
        pdf_bytes = ProposalPdfService.generate(
            proposal, selected_modules=selected_modules
        )

        if not pdf_bytes:
            return Response(
                {'error': 'PDF generation failed. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    from django.http import HttpResponse
    from content.services.pdf_utils import safe_pdf_filename
    _created = proposal.created_at or timezone.now()
    date_suffix = _created.strftime('%d-%m-%y')
    prefix = 'Detalle_Tecnico' if doc_variant == 'technical' else 'Propuesta_Comercial'
    filename = safe_pdf_filename(prefix, proposal.title or proposal.client_name, date_suffix)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ---------------------------------------------------------------------------
# Admin endpoints (staff only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_proposals(request):
    """
    List all proposals with lightweight serializer.
    Supports ?status= query parameter for filtering.
    Includes heat_score (1-10) for active non-draft proposals.
    """
    qs = BusinessProposal.objects.select_related('client__user').all()
    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    proposals = list(qs)
    effective_totals = _build_effective_totals_map(proposals)

    serializer = ProposalListSerializer(proposals, many=True)
    data = serializer.data

    # Use pre-computed cached_heat_score from the model instead of
    # computing on-the-fly (avoids N+1 queries on every list load).
    for item in data:
        eff_total = effective_totals.get(item['id'])
        item['effective_total_investment'] = (
            str(eff_total) if eff_total is not None else item['total_investment']
        )
        if item['status'] in ('accepted', 'finished'):
            item['heat_score'] = 10
        elif item['status'] in ('sent', 'viewed') and item['is_active']:
            item['heat_score'] = item.get('cached_heat_score', 0) or 0
        else:
            item['heat_score'] = 0
        item['engagement_summary'] = None

    # Batch-compute engagement summaries for active sent/viewed proposals
    # using 3 aggregated queries instead of N*5 individual queries.
    active_ids = [
        item['id'] for item in data
        if item['status'] in ('sent', 'viewed') and item['is_active'] and item.get('heat_score', 0) > 0
    ]
    if active_ids:
        from django.db.models import Count, Q, Sum
        now = timezone.now()

        # Single query: investment + technical time aggregated together via conditional Sum.
        section_agg = {
            pid: (inv_t or 0, tech_t or 0)
            for pid, inv_t, tech_t in ProposalSectionView.objects
            .filter(view_event__proposal_id__in=active_ids)
            .values('view_event__proposal_id')
            .annotate(
                inv_t=Sum('time_spent_seconds', filter=Q(section_type='investment')),
                tech_t=Sum(
                    'time_spent_seconds',
                    filter=Q(section_type__in=TECHNICAL_DOCUMENT_TRACKING_TYPES),
                ),
            )
            .values_list('view_event__proposal_id', 'inv_t', 'tech_t')
        }
        unique_ips_map = dict(
            ProposalViewEvent.objects
            .filter(proposal_id__in=active_ids)
            .exclude(ip_address__isnull=True).exclude(ip_address='')
            .values('proposal_id')
            .annotate(cnt=Count('ip_address', distinct=True))
            .values_list('proposal_id', 'cnt')
        )
        # Only fetch rows for key sections — avoids loading unrelated section data.
        viewed_sections: dict[int, set] = {}
        for pid, stype in ProposalSectionView.objects.filter(
            view_event__proposal_id__in=active_ids,
            section_type__in=_KEY_PROPOSAL_SECTIONS,
        ).values_list('view_event__proposal_id', 'section_type').distinct():
            viewed_sections.setdefault(pid, set()).add(stype)

        summaries_map = {}
        for pid in active_ids:
            inv_t, tech_t = section_agg.get(pid, (0, 0))
            uniq = unique_ips_map.get(pid, 0)
            skipped = [s for s in _KEY_PROPOSAL_SECTIONS if s not in viewed_sections.get(pid, set())]
            summaries_map[pid] = {
                'investment_time_sec': round(inv_t),
                'technical_time_sec': round(tech_t),
                'technical_viewed': tech_t >= 5,
                'unique_devices': uniq,
                'skipped_sections': skipped,
            }

        for item in data:
            pid = item['id']
            if pid not in summaries_map:
                continue
            s = summaries_map[pid]
            last_activity = item.get('last_activity_at')
            last_activity_str = None
            if last_activity:
                try:
                    la_dt = (
                        last_activity if hasattr(last_activity, 'tzinfo')
                        else parse_datetime(last_activity)
                    )
                    if la_dt:
                        delta = now - la_dt
                        if delta.days == 0:
                            hours = delta.seconds // 3600
                            last_activity_str = f"hace {hours}h" if hours > 0 else "hace menos de 1h"
                        else:
                            last_activity_str = f"hace {delta.days}d"
                except Exception:
                    pass
            item['engagement_summary'] = {
                'views': item.get('view_count', 0),
                'last_activity': last_activity_str,
                **s,
            }

    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_proposal(request, proposal_id):
    """
    Retrieve full proposal detail for admin editing.
    Returns all sections (including disabled ones).
    """
    proposal = get_object_or_404(
        BusinessProposal.objects
        .select_related('client__user')
        .prefetch_related('project_stages'),
        pk=proposal_id,
    )
    serializer = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': True}
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_proposal(request):
    """
    Create a new proposal.
    Auto-generates 12 default sections with content_json populated
    from the existing component defaults.
    """
    serializer = ProposalCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    proposal = serializer.save()
    from content.services.proposal_service import ProposalService

    if not proposal.expires_at:
        proposal.expires_at = ProposalService.compute_default_expires_at(proposal.language)
        proposal.save(update_fields=['expires_at'])

    # Log creation
    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='created',
        actor_type='seller',
        description=(
            f'Proposal created: "{proposal.title}" for {proposal.client_name}. '
            f'Investment: ${proposal.total_investment} {proposal.currency}.'
        ),
    )

    # Auto-create default sections
    default_sections = ProposalService.get_default_sections(proposal.language)
    for section_cfg in default_sections:
        if section_cfg['section_type'] == 'greeting':
            section_cfg['content_json']['proposalTitle'] = proposal.title
            section_cfg['content_json']['clientName'] = proposal.client_name
        if section_cfg['section_type'] == 'investment' and proposal.total_investment:
            total = float(proposal.total_investment)
            cur = proposal.currency or 'COP'
            fmt = '${:,.0f}'.format
            section_cfg['content_json']['totalInvestment'] = fmt(total)
            section_cfg['content_json']['currency'] = cur
            section_cfg['content_json']['paymentOptions'] = [
                {
                    'label': '40% al firmar el contrato ✍️',
                    'description': f'{fmt(total * 0.4)} {cur}',
                },
                {
                    'label': '30% al aprobar el diseño final ✅',
                    'description': f'{fmt(total * 0.3)} {cur}',
                },
                {
                    'label': '30% al desplegar el sitio web 🚀',
                    'description': f'{fmt(total * 0.3)} {cur}',
                },
            ]
        ProposalSection.objects.create(proposal=proposal, **section_cfg)

    # Return the full detail
    detail = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': True}
    )
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_proposal_from_json(request):
    """
    Create a proposal from a complete JSON payload.

    The payload includes metadata (title, client_name, etc.) and a
    ``sections`` dict whose keys are camelCase section names with their
    full content_json.  Missing sections fall back to DEFAULT_SECTIONS.
    """
    serializer = ProposalFromJSONSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    sections_data = data.pop('sections')

    from content.services.proposal_service import ProposalService

    expires_at = data.get('expires_at')
    if not expires_at:
        expires_at = ProposalService.compute_default_expires_at(
            data.get('language', 'es'),
        )

    # Resolve the canonical client (UserProfile, role=client) — auto-creates
    # via placeholder when no email is provided so the FK is always populated.
    from accounts.services import proposal_client_service

    client_profile = proposal_client_service.get_or_create_client_for_proposal(
        name=data.get('client_name', ''),
        email=data.get('client_email', ''),
        phone=data.get('client_phone', ''),
        company=data.get('client_company', ''),
    )

    # Create the BusinessProposal
    proposal = BusinessProposal.objects.create(
        title=data['title'],
        client_name=data['client_name'],
        client_email=data.get('client_email', ''),
        client_phone=data.get('client_phone', ''),
        project_type=data.get('project_type', ''),
        market_type=data.get('market_type', ''),
        language=data.get('language', 'es'),
        total_investment=data.get('total_investment', 0),
        currency=data.get('currency', 'COP'),
        expires_at=expires_at,
        reminder_days=data.get('reminder_days', 10),
        urgency_reminder_days=data.get('urgency_reminder_days', 15),
        discount_percent=data.get('discount_percent', 0),
        client=client_profile,
    )
    proposal_client_service.sync_snapshot(proposal)

    # Use DEFAULT_SECTIONS as a template for title/order/is_wide_panel
    default_sections = ProposalService.get_default_sections(proposal.language)
    from content.services.proposal_module_links import (
        normalize_technical_document_module_links,
    )

    resolved_sections = []

    for section_cfg in default_sections:
        section_type = section_cfg['section_type']
        json_key = SECTION_TYPE_TO_KEY.get(section_type)

        if json_key and json_key in sections_data:
            content_json = copy.deepcopy(sections_data[json_key])
        else:
            content_json = copy.deepcopy(section_cfg['content_json'])

        # Special handling for greeting — ensure clientName and proposalTitle are set
        if section_type == 'greeting':
            general = sections_data.get('general', {})
            content_json.setdefault('proposalTitle', proposal.title)
            content_json.setdefault('clientName', proposal.client_name)
            if general.get('inspirationalQuote'):
                content_json['inspirationalQuote'] = general['inspirationalQuote']

        # Protect default groups/modules in functional_requirements:
        # merge JSON groups with defaults so the AI cannot remove them.
        if section_type == 'functional_requirements' and json_key in sections_data:
            default_cj = copy.deepcopy(section_cfg['content_json'])
            default_groups = default_cj.get('groups', [])
            default_modules = default_cj.get('additionalModules', [])
            json_groups = content_json.get('groups', [])
            json_modules = content_json.get('additionalModules', [])

            # Build lookup of JSON groups by id for merging
            json_groups_by_id = {
                g['id']: g for g in json_groups if isinstance(g, dict) and g.get('id')
            }
            json_modules_by_id = {
                m['id']: m for m in json_modules if isinstance(m, dict) and m.get('id')
            }

            # Merge: keep all default groups, update with JSON content if provided
            merged_groups = []
            for dg in default_groups:
                gid = dg.get('id')
                if gid and gid in json_groups_by_id:
                    # Use JSON version but preserve the id and is_visible from default
                    merged = json_groups_by_id.pop(gid)
                    merged['id'] = gid
                    merged.setdefault('is_visible', dg.get('is_visible', True))
                    merged_groups.append(merged)
                else:
                    merged_groups.append(dg)
            # Append any new groups from JSON that don't exist in defaults
            for gid, g in json_groups_by_id.items():
                merged_groups.append(g)

            merged_modules = []
            for dm in default_modules:
                mid = dm.get('id')
                if mid and mid in json_modules_by_id:
                    merged = json_modules_by_id.pop(mid)
                    merged['id'] = mid
                    merged.setdefault('is_visible', dm.get('is_visible', True))
                    merged_modules.append(merged)
                else:
                    merged_modules.append(dm)
            for mid, m in json_modules_by_id.items():
                merged_modules.append(m)

            content_json['groups'] = merged_groups
            content_json['additionalModules'] = merged_modules

            # Normalize: move any group with is_calculator_module=True
            # from groups[] to additionalModules[] (AI sometimes merges them)
            final_groups = []
            existing_mod_ids = {m.get('id') for m in content_json['additionalModules']}
            for g in content_json['groups']:
                if g.get('is_calculator_module'):
                    if g.get('id') not in existing_mod_ids:
                        content_json['additionalModules'].append(g)
                else:
                    final_groups.append(g)
            content_json['groups'] = final_groups

        resolved_sections.append({
            'section_type': section_type,
            'title': section_cfg['title'],
            'order': section_cfg['order'],
            'is_wide_panel': section_cfg.get('is_wide_panel', False),
            'content_json': content_json,
        })

    technical_section = next(
        (
            section
            for section in resolved_sections
            if section['section_type'] == ProposalSection.SectionType.TECHNICAL_DOCUMENT
        ),
        None,
    )
    if technical_section:
        technical_section['content_json'] = normalize_technical_document_module_links(
            technical_section['content_json'],
            resolved_sections,
        )

    for section in resolved_sections:
        ProposalSection.objects.create(proposal=proposal, **section)

    # Detect unrecognized section keys (silent bug prevention)
    known_keys = set(SECTION_KEY_MAP.keys()) | {'_meta', '_seller_prompt'}
    provided_keys = set(sections_data.keys())
    unmapped_keys = sorted(provided_keys - known_keys)

    detail = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': True}
    )
    response_data = detail.data
    if unmapped_keys:
        response_data['warnings'] = [
            f'Unknown section keys ignored: {", ".join(unmapped_keys)}. '
            f'Valid keys: {", ".join(sorted(SECTION_KEY_MAP.keys()))}.'
        ]
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_proposal_json_template(request):
    """
    Return a downloadable JSON template with all default sections
    (commercial + technicalDocument) pre-populated with placeholder content.

    Query params:
        lang: 'es' (default) or 'en'
    """
    lang = request.query_params.get('lang', 'es')

    from content.services.proposal_service import ProposalService
    default_sections = ProposalService.get_default_sections(lang)

    template = {}
    for section_cfg in default_sections:
        section_type = section_cfg['section_type']
        json_key = SECTION_TYPE_TO_KEY.get(section_type, section_type)
        template[json_key] = copy.deepcopy(section_cfg['content_json'])

    template['_meta'] = {
        'description': 'Proposal JSON template — fill in each section and import via the panel',
        'required_fields': ['general.clientName'],
        'optional_metadata': {
            'title': 'Propuesta de ... — Client Name',
            'client_email': 'client@example.com',
            'language': 'es | en',
            'total_investment': 0,
            'currency': 'COP | USD',
            'expires_at': '2026-04-06T00:00:00Z',
        },
    }

    # Add _do_not_remove annotations to functionalRequirements groups
    fr_key = SECTION_TYPE_TO_KEY.get('functional_requirements', 'functionalRequirements')
    if fr_key in template:
        fr = template[fr_key]
        for group in fr.get('groups', []):
            group['_do_not_remove'] = True
        for mod in fr.get('additionalModules', []):
            mod['_do_not_remove'] = True

    template['_seller_prompt'] = {
        'role': (
            'You are an expert sales consultant crafting a business proposal. '
            'Your goal is to persuade the client by demonstrating deep understanding '
            'of their industry, challenges, and opportunities.'
        ),
        'tone': (
            'Business-oriented but approachable. Avoid overly technical jargon. '
            'Write as if speaking directly to the decision-maker. Use confident, '
            'results-focused language.'
        ),
        'personalization': [
            'Always mention the client name and company name.',
            'Reference the client\'s specific industry, sector, and market.',
            'Include at least 2-3 metrics or statistics relevant to their sector (cite reliable sources).',
            'Tailor examples and case studies to their business type.',
        ],
        'investment_anchoring': [
            'Present ROI and value BEFORE mentioning price.',
            'Frame the investment as a business decision, not a cost.',
            'Compare the investment to the cost of inaction or lost opportunity.',
            'If applicable, show projected revenue impact or efficiency gains.',
        ],
        'structure_tips': [
            'Greeting: warm, personal, mention how/why you connected.',
            'Executive Summary: 3-4 sentences max, outcome-focused.',
            'Context/Diagnostic: show you understand their current situation.',
            'Strategy: actionable and specific to their goals.',
            'Investment: lead with value, break down modules clearly.',
            'Timeline: realistic milestones tied to business outcomes.',
        ],
        'bold_formatting': (
            'In the following sections, wrap important words, key phrases, and '
            'mini-titles with <b>…</b> tags to highlight relevant information '
            'and improve scannability. Apply bold sparingly — only to the most '
            'impactful fragments (e.g. client benefits, metrics, key outcomes, '
            'action verbs). Do NOT bold entire paragraphs or sentences. '
            'Sections that MUST include bold highlights: '
            'executiveSummary (paragraphs, highlights), '
            'contextDiagnostic (paragraphs, issues, opportunity), '
            'conversionStrategy (intro, bullets, result), '
            'designUX (paragraphs, focusItems, objective), '
            'creativeSupport (paragraphs, includes, closing).'
        ),
        'CRITICAL_functionalRequirements': (
            'Do NOT remove any groups or modules from the functionalRequirements section. '
            'All base groups in "groups" and all optional modules in "additionalModules" '
            'MUST remain in their respective arrays, in their original order. '
            'Do NOT move modules between arrays. '
            'You may modify content (title, description, items) and add new entries, '
            'but NEVER delete or relocate existing ones. The seller will remove them manually '
            'after the proposal is created if needed.'
        ),
        'CRITICAL_additionalModules_autoselect': (
            'Scan the project requirements, brief, and notes provided by the seller. '
            'For EACH module in functionalRequirements.additionalModules, decide whether '
            'the requirements explicitly or implicitly describe that capability. '
            'Detection hints: DIAN, electronic invoicing or e-invoicing, Siigo, Alegra -> '
            '"integration_electronic_invoicing". PSE, Wompi, PayU, ePayco, Nequi, Daviplata, '
            'Bancolombia or Colombian payments -> "integration_regional_payments". Stripe, '
            'PayPal, cross-border or international payments -> '
            '"integration_international_payments". Installable app, PWA, offline mode, push '
            'notifications -> "pwa_module". AI, intelligent automation, chatbot, assistants '
            '-> "ai_module". Meta Ads, Facebook Ads, Google Ads, Conversions API, CAPI, ROAS, '
            'Enhanced Conversions -> "integration_conversion_tracking". Reports, notifications '
            'or alerts via email/WhatsApp/Telegram, sales/stock alerts -> '
            '"reports_alerts_module". Email marketing, Mailchimp, Brevo, SendGrid, lead '
            'capture -> "email_marketing_module". Multi-language, i18n, multiple countries, '
            'translations, per-country pricing -> "i18n_module". Live chat, real-time '
            'support, in-house chat widget -> "live_chat_module". Dark mode, theme '
            'switching -> "dark_mode_module". '
            'When a module matches the brief, set BOTH "default_selected": true AND '
            '"selected": true on that module object, and ADAPT its "description" and reorder '
            'or rewrite its "items" so the wording reflects the exact terminology, providers '
            'and nuances mentioned in the requirements (e.g. if the brief says "I want to '
            'receive reports via WhatsApp", make sure the WhatsApp item in '
            'reports_alerts_module leads the list and the description names WhatsApp as the '
            'primary channel). '
            'Never invent a match that is not supported by the requirements. When in doubt, '
            'leave default_selected as false. Do NOT change the module id, icon, price_percent, '
            'is_invite, or its position in the array.'
        ),
    }

    return Response(template, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def export_proposal_json(request, proposal_id):
    """
    Export an existing proposal as a JSON object compatible with
    the ``create-from-json`` / ``update-from-json`` import format.

    Returns a dict with camelCase section keys and a ``_meta`` block
    containing proposal metadata.
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    result = {}
    for section in proposal.sections.all().order_by('order'):
        json_key = SECTION_TYPE_TO_KEY.get(section.section_type)
        if json_key:
            result[json_key] = copy.deepcopy(section.content_json or {})

    result['_meta'] = {
        'title': proposal.title,
        'client_name': proposal.client_name,
        'client_email': proposal.client_email or '',
        'client_phone': proposal.client_phone or '',
        'project_type': proposal.project_type or '',
        'market_type': proposal.market_type or '',
        'project_type_custom': proposal.project_type_custom or '',
        'market_type_custom': proposal.market_type_custom or '',
        'language': proposal.language or 'es',
        'total_investment': str(proposal.total_investment),
        'currency': proposal.currency or 'COP',
        'hosting_percent': proposal.hosting_percent,
        'hosting_discount_semiannual': proposal.hosting_discount_semiannual,
        'hosting_discount_quarterly': proposal.hosting_discount_quarterly,
        'expires_at': (
            proposal.expires_at.isoformat() if proposal.expires_at else None
        ),
        'reminder_days': proposal.reminder_days,
        'urgency_reminder_days': proposal.urgency_reminder_days,
        'discount_percent': proposal.discount_percent,
    }

    return Response(result, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_proposal_from_json(request, proposal_id):
    """
    Update an existing proposal from a complete JSON payload.

    Accepts the same structure as ``create-from-json``: metadata fields
    at the top level and a ``sections`` dict whose keys are camelCase
    section names mapped to content_json dicts.

    Metadata fields are updated on the proposal, and each section's
    content_json is replaced by the matching key from the payload.
    Sections not present in the payload are left unchanged.
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    serializer = ProposalFromJSONSerializer(
        data=request.data, context={'proposal': proposal}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    sections_data = data.pop('sections')

    old_status = proposal.status

    # --- Update metadata fields ---
    metadata_fields = [
        'title', 'client_name', 'client_email', 'client_phone',
        'project_type', 'market_type', 'project_type_custom',
        'market_type_custom', 'language', 'total_investment', 'currency',
        'reminder_days', 'urgency_reminder_days', 'discount_percent',
    ]
    tracked_old = {}
    for field in metadata_fields:
        tracked_old[field] = str(getattr(proposal, field, ''))
        if field in data:
            setattr(proposal, field, data[field])

    if 'expires_at' in data:
        tracked_old['expires_at'] = str(proposal.expires_at or '')
        proposal.expires_at = data['expires_at']

    from accounts.services import proposal_client_service
    from content.services.proposal_service import ProposalService

    # When the JSON import includes client identity fields, route them through
    # the service so we reuse/create a UserProfile and keep the FK consistent.
    if data.get('client_name') or data.get('client_email'):
        client_profile = proposal_client_service.get_or_create_client_for_proposal(
            name=data.get('client_name', '') or proposal.client_name,
            email=data.get('client_email', ''),
            phone=data.get('client_phone', ''),
            company=data.get('client_company', ''),
        )
        proposal.client = client_profile

    reopened_status = ProposalService.reopen_if_unexpired(
        proposal, old_status=old_status
    )

    proposal.save()
    if proposal.client_id:
        proposal_client_service.sync_snapshot(proposal)

    if reopened_status:
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='updated',
            field_name='status',
            old_value=old_status,
            new_value=reopened_status,
            actor_type='seller',
            description=(
                f'Auto-reopened from expired after expires_at moved to the future '
                f'({old_status} → {reopened_status}).'
            ),
        )

    # Log field-level changes
    for field in list(metadata_fields) + ['expires_at']:
        new_val = str(getattr(proposal, field, ''))
        old_val = tracked_old.get(field, '')
        if old_val != new_val:
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='updated',
                field_name=field,
                old_value=old_val,
                new_value=new_val,
                actor_type='seller',
                description=f'JSON import — {field}: {old_val} → {new_val}',
            )

    # --- Update section content_json ---
    updated_sections = []
    for section in proposal.sections.all():
        json_key = SECTION_TYPE_TO_KEY.get(section.section_type)
        if json_key and json_key in sections_data:
            new_content = sections_data[json_key]

            # Special handling for greeting
            if section.section_type == 'greeting':
                general = sections_data.get('general', {})
                new_content.setdefault('proposalTitle', proposal.title)
                new_content.setdefault('clientName', proposal.client_name)
                if general.get('inspirationalQuote'):
                    new_content['inspirationalQuote'] = general['inspirationalQuote']

            # Normalize functional_requirements: move calculator modules
            # from groups[] to additionalModules[]
            if section.section_type == 'functional_requirements':
                final_groups = []
                new_content.setdefault('additionalModules', [])
                existing_mod_ids = {m.get('id') for m in new_content['additionalModules']}
                for g in new_content.get('groups', []):
                    if g.get('is_calculator_module'):
                        if g.get('id') not in existing_mod_ids:
                            new_content['additionalModules'].append(g)
                    else:
                        final_groups.append(g)
                new_content['groups'] = final_groups

            section.content_json = new_content
            section.save(update_fields=['content_json'])
            updated_sections.append(json_key)

    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='updated',
        actor_type='seller',
        description=(
            f'Proposal updated from JSON import. '
            f'Sections updated: {", ".join(updated_sections) if updated_sections else "none"}.'
        ),
    )

    # Detect unrecognized section keys
    known_keys = set(SECTION_KEY_MAP.keys()) | {'_meta', '_seller_prompt'}
    provided_keys = set(sections_data.keys())
    unmapped_keys = sorted(provided_keys - known_keys)

    detail = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': True}
    )
    response_data = detail.data
    if unmapped_keys:
        response_data['warnings'] = [
            f'Unknown section keys ignored: {", ".join(unmapped_keys)}. '
            f'Valid keys: {", ".join(sorted(SECTION_KEY_MAP.keys()))}.'
        ]
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_proposal(request, proposal_id):
    """
    Update proposal metadata (title, client_name, etc.).
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    # Snapshot tracked fields before update
    tracked_fields = [
        'title', 'total_investment', 'currency', 'client_name',
        'client_email', 'client_phone', 'discount_percent', 'status',
        'language', 'project_type', 'market_type', 'slug',
        'expires_at', 'reminder_days', 'urgency_reminder_days',
    ]
    old_values = {f: str(getattr(proposal, f, '')) for f in tracked_fields}

    serializer = ProposalCreateUpdateSerializer(
        proposal, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    from content.services.proposal_service import ProposalService
    reopened_status = ProposalService.reopen_if_unexpired(
        proposal, old_status=old_values['status'],
    )
    if reopened_status:
        proposal.save(update_fields=['status'])

    # Log field-level changes
    for field in tracked_fields:
        new_val = str(getattr(proposal, field, ''))
        if old_values[field] != new_val:
            description = f'{field}: {old_values[field]} → {new_val}'
            if field == 'status' and reopened_status:
                description = (
                    f'Auto-reopened from expired after expires_at moved to the future '
                    f'({old_values[field]} → {new_val}).'
                )
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='updated',
                field_name=field,
                old_value=old_values[field],
                new_value=new_val,
                actor_type='seller',
                description=description,
            )

    # Sync total_investment / currency into the investment section's content_json
    investment_changed = (
        old_values.get('total_investment') != str(proposal.total_investment)
        or old_values.get('currency') != str(proposal.currency)
    )
    if investment_changed:
        fr_section = proposal.sections.filter(
            section_type=ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS
        ).first()
        _resync_investment_from_modules(
            proposal, fr_section.content_json if fr_section else None
        )

    detail = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': True}
    )
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_proposal(request, proposal_id):
    """
    Delete a proposal and all related sections/groups (CASCADE).
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    proposal.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_action(request):
    """
    Perform a batch action on multiple proposals.

    Payload: { "ids": [1, 2, 3], "action": "delete"|"expire"|"resend" }
    """
    ids = request.data.get('ids', [])
    action_type = request.data.get('action', '')

    if not ids or not isinstance(ids, list):
        return Response(
            {'detail': 'ids must be a non-empty list.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if action_type not in ('delete', 'expire', 'resend'):
        return Response(
            {'detail': 'action must be one of: delete, expire, resend.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    proposals = BusinessProposal.objects.filter(pk__in=ids)
    affected = 0

    if action_type == 'delete':
        affected = proposals.count()
        proposals.delete()

    elif action_type == 'expire':
        affected = proposals.exclude(status='expired').update(
            status='expired',
            expires_at=timezone.now(),
        )

    elif action_type == 'resend':
        from content.services.proposal_service import ProposalService
        for p in proposals.filter(status__in=['sent', 'viewed'], client_email__gt=''):
            try:
                ProposalService.resend_proposal(p)
                affected += 1
            except Exception:
                logger.exception('Bulk resend failed for proposal %s', p.id)

    return Response({'affected': affected, 'action': action_type})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def duplicate_proposal(request, proposal_id):
    """
    Duplicate a proposal: creates a deep copy with all its sections.
    The copy is reset to draft status with a clean lifecycle.
    """
    from django.db import transaction as _tx
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    with _tx.atomic():
        new_proposal = BusinessProposal.objects.create(
            title=f'{proposal.title.removesuffix(" (copia)")} (copia)',
            client_name=proposal.client_name,
            client_email=proposal.client_email,
            client_phone=proposal.client_phone,
            slug='',
            language=proposal.language,
            total_investment=proposal.total_investment,
            currency=proposal.currency,
            hosting_percent=proposal.hosting_percent,
            hosting_discount_semiannual=proposal.hosting_discount_semiannual,
            hosting_discount_quarterly=proposal.hosting_discount_quarterly,
            project_type=proposal.project_type,
            market_type=proposal.market_type,
            project_type_custom=proposal.project_type_custom,
            market_type_custom=proposal.market_type_custom,
            selected_modules=copy.deepcopy(proposal.selected_modules),
            contract_params=copy.deepcopy(proposal.contract_params),
            status=BusinessProposal.Status.DRAFT,
            expires_at=proposal.expires_at,
            reminder_days=proposal.reminder_days,
            urgency_reminder_days=proposal.urgency_reminder_days,
            discount_percent=proposal.discount_percent,
            is_active=True,
            view_count=0,
            first_viewed_at=None,
            sent_at=None,
            reminder_sent_at=None,
            urgency_email_sent_at=None,
        )

        for section in proposal.sections.all().order_by('order'):
            ProposalSection.objects.create(
                proposal=new_proposal,
                section_type=section.section_type,
                title=section.title,
                order=section.order,
                is_enabled=section.is_enabled,
                is_wide_panel=section.is_wide_panel,
                content_json=copy.deepcopy(section.content_json),
            )

        ProposalChangeLog.objects.create(
            proposal=new_proposal,
            change_type='duplicated',
            actor_type='seller',
            description=f'Duplicated from proposal "{proposal.title}" (ID {proposal.id}).',
        )

    detail = ProposalDetailSerializer(
        new_proposal, context={'request': request, 'is_admin': True}
    )
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_proposal(request, proposal_id):
    """
    Mark proposal as SENT, set sent_at, schedule Huey reminder task.
    Requires client_email to be set.
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    from content.services.proposal_service import ProposalService
    try:
        delivery = ProposalService.send_proposal(proposal)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='sent',
        actor_type='seller',
        description=f'Proposal sent to {proposal.client_email}.',
    )

    return _proposal_admin_response(request, proposal, delivery)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def toggle_proposal_active(request, proposal_id):
    """
    Toggle a proposal's is_active flag.
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    proposal.is_active = not proposal.is_active
    proposal.save(update_fields=['is_active'])

    detail = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': True}
    )
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_proposal_status(request, proposal_id):
    """
    Inline status change from the proposals table.
    Body: { "status": "expired" }

    Validates allowed transitions and logs the change. The ``draft → sent``
    transition is delegated to ``ProposalService.send_proposal`` so the
    client email is dispatched and Huey reminders are scheduled.
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    new_status = (request.data.get('status') or '').strip()

    valid_statuses = {c[0] for c in BusinessProposal.Status.choices}
    if new_status not in valid_statuses:
        return Response(
            {'error': f'Invalid status: {new_status}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Enforce whitelist-based transitions
    allowed = BusinessProposal.ALLOWED_TRANSITIONS.get(proposal.status, frozenset())
    if new_status not in allowed:
        return Response(
            {'error': f'Cannot transition from {proposal.status} to {new_status}.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    old_status = proposal.status
    delivery = None

    if (
        old_status == BusinessProposal.Status.DRAFT
        and new_status == BusinessProposal.Status.SENT
    ):
        from content.services.proposal_service import ProposalService
        try:
            delivery = ProposalService.send_proposal(proposal)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='sent',
            actor_type='seller',
            description=(
                f'Proposal sent to {proposal.client_email} (inline).'
            ),
        )
    else:
        proposal.status = new_status
        proposal.save(update_fields=['status'])

        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='status_change',
            field_name='status',
            old_value=old_status,
            new_value=new_status,
            actor_type='seller',
            description=f'Status changed from {old_status} to {new_status} (inline).',
        )

        if new_status == BusinessProposal.Status.FINISHED:
            try:
                from content.services.proposal_email_service import (
                    ProposalEmailService,
                )

                ProposalEmailService.send_finished_confirmation(proposal)
            except Exception:
                logger.exception(
                    'Failed to send finished confirmation for proposal %s',
                    proposal.id,
                )

    return _proposal_admin_response(request, proposal, delivery)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def launch_to_platform(request, proposal_id):
    """
    Manually trigger platform onboarding for an accepted proposal.
    Body: { "force": true }  (required for re-launch when already onboarded)

    Creates project, deliverable, requirements, syncs documents, and sends
    acceptance email on first launch. Re-launch deletes existing data first
    and skips the email.
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    if proposal.status != BusinessProposal.Status.ACCEPTED:
        return Response(
            {'error': 'La propuesta debe estar aceptada para lanzar a plataforma.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    already_onboarded = proposal.platform_onboarding_completed_at is not None

    if already_onboarded and not request.data.get('force'):
        return Response(
            {
                'warning': 'already_onboarded',
                'onboarded_at': str(proposal.platform_onboarding_completed_at),
            },
            status=status.HTTP_409_CONFLICT,
        )

    from django.db import transaction

    with transaction.atomic():
        if already_onboarded:
            from accounts.services.proposal_platform_onboarding import (
                teardown_platform_for_proposal,
            )

            teardown_platform_for_proposal(proposal)
            proposal.refresh_from_db()

        proposal.platform_onboarding_status = BusinessProposal.ONBOARDING_PENDING
        proposal.save(update_fields=['platform_onboarding_status'])

        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type=ProposalChangeLog.ChangeType.PLATFORM_LAUNCH,
            field_name='platform_onboarding_status',
            new_value='pending',
            actor_type='seller',
            description='Re-launched to platform.' if already_onboarded else 'Launched to platform.',
        )

    from content.tasks import run_platform_onboarding

    try:
        run_platform_onboarding(
            proposal.id,
            acting_user_id=request.user.id,
            is_relaunch=already_onboarded,
        )
    except Exception:
        logger.exception('Failed to queue platform onboarding for proposal %s.', proposal_id)
        proposal.platform_onboarding_status = BusinessProposal.ONBOARDING_FAILED
        proposal.save(update_fields=['platform_onboarding_status'])

    proposal.refresh_from_db()
    detail = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': True}
    )
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def proposal_scorecard(request, proposal_id):
    """
    Pre-send scorecard: returns a 1-10 completeness score with
    individual checks and blockers for a proposal.
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    checks = []

    # 1. Client email
    has_email = bool(proposal.client_email)
    checks.append({
        'key': 'client_email',
        'label': 'Email del cliente',
        'passed': has_email,
        'blocker': True,
    })

    # 2. Client name
    has_name = bool(proposal.client_name)
    checks.append({
        'key': 'client_name',
        'label': 'Nombre del cliente',
        'passed': has_name,
        'blocker': True,
    })

    # 3. Investment > 0
    has_investment = bool(proposal.total_investment and proposal.total_investment > 0)
    checks.append({
        'key': 'total_investment',
        'label': 'Inversión total > $0',
        'passed': has_investment,
        'blocker': True,
    })

    # 4. Expiration date in the future
    has_expiration = bool(
        proposal.expires_at and proposal.expires_at > timezone.now()
    )
    checks.append({
        'key': 'expires_at',
        'label': 'Fecha de expiración futura',
        'passed': has_expiration,
        'blocker': True,
    })

    # 5. At least 1 enabled section
    enabled_sections = proposal.sections.filter(is_enabled=True).count()
    has_sections = enabled_sections >= 1
    checks.append({
        'key': 'enabled_sections',
        'label': 'Al menos 1 sección habilitada',
        'passed': has_sections,
        'blocker': True,
    })

    # 6. Title set
    has_title = bool(proposal.title and proposal.title.strip())
    checks.append({
        'key': 'title',
        'label': 'Título de la propuesta',
        'passed': has_title,
        'blocker': False,
    })

    # 7. Sections with content (non-empty content_json)
    import json as _json
    sections_with_content = 0
    for sec in proposal.sections.filter(is_enabled=True):
        cj = sec.content_json
        if isinstance(cj, str):
            try:
                cj = _json.loads(cj)
            except (ValueError, TypeError):
                cj = {}
        if cj and cj != {}:
            sections_with_content += 1
    content_ratio = (
        sections_with_content / enabled_sections if enabled_sections > 0 else 0
    )
    checks.append({
        'key': 'sections_content',
        'label': f'Secciones con contenido ({sections_with_content}/{enabled_sections})',
        'passed': content_ratio >= 0.5,
        'blocker': False,
    })

    # 8. Client phone (useful for WhatsApp follow-ups)
    has_phone = bool(proposal.client_phone and proposal.client_phone.strip())
    checks.append({
        'key': 'client_phone',
        'label': 'Teléfono del cliente (para WhatsApp)',
        'passed': has_phone,
        'blocker': False,
    })

    # 9. Language configured
    has_language = bool(proposal.language)
    checks.append({
        'key': 'language',
        'label': 'Idioma configurado',
        'passed': has_language,
        'blocker': False,
    })

    # 10. Discount configured (optional quality check)
    has_discount_or_na = True  # Not a blocker
    checks.append({
        'key': 'discount_review',
        'label': 'Descuento revisado',
        'passed': has_discount_or_na,
        'blocker': False,
    })

    # 11. Payment options set (read from investment section content_json)
    investment_section = proposal.sections.filter(
        section_type='investment', is_enabled=True
    ).first()
    inv_cj = {}
    if investment_section:
        inv_cj = investment_section.content_json or {}
        if isinstance(inv_cj, str):
            try:
                inv_cj = _json.loads(inv_cj)
            except (ValueError, TypeError):
                inv_cj = {}
    has_payment = bool(inv_cj.get('paymentOptions'))
    checks.append({
        'key': 'payment_options',
        'label': 'Opciones de pago definidas',
        'passed': has_payment,
        'blocker': False,
    })

    # 10. Timeline / estimated weeks (read from investment section content_json)
    estimated_weeks = inv_cj.get('estimatedWeeks', 0)
    try:
        estimated_weeks = int(estimated_weeks)
    except (ValueError, TypeError):
        estimated_weeks = 0
    has_timeline = estimated_weeks > 0
    checks.append({
        'key': 'estimated_weeks',
        'label': 'Tiempo estimado definido',
        'passed': has_timeline,
        'blocker': False,
    })

    # Compute score (1-10)
    passed_count = sum(1 for c in checks if c['passed'])
    score = max(1, round(passed_count / len(checks) * 10))
    blockers = [c for c in checks if c['blocker'] and not c['passed']]

    return Response({
        'score': score,
        'checks': checks,
        'blockers': blockers,
        'can_send': len(blockers) == 0,
        'total_checks': len(checks),
        'passed_checks': passed_count,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def resend_proposal(request, proposal_id):
    """
    Re-send a proposal: reset lifecycle timers, keep existing expires_at,
    and re-schedule reminder emails.
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    from content.services.proposal_service import ProposalService
    try:
        delivery = ProposalService.resend_proposal(proposal)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='resent',
        actor_type='seller',
        description=f'Proposal re-sent to {proposal.client_email}.',
    )

    return _proposal_admin_response(request, proposal, delivery)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_proposal_section(request, section_id):
    """
    Update a section's content_json, title, order, is_enabled, etc.

    Response shape (admin panel only):
        {
          "section": <ProposalSectionDetailSerializer>,
          "proposal_totals": {
              "total_investment": "...",
              "effective_total_investment": "..."
          },
          "investment_section": <ProposalSectionDetailSerializer>  # only when
              # the saved section is functional_requirements and the auto
              # resync mutated the investment section's content_json
        }

    The proposal-level totals are recomputed here so the admin's General tab
    badge "Cliente ve: $X" stays in sync without an extra refetch round-trip.
    """
    section = get_object_or_404(ProposalSection.objects.select_related('proposal'), pk=section_id)
    serializer = ProposalSectionUpdateSerializer(
        section, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    investment_section = None
    if section.section_type == ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS:
        _resync_investment_from_modules(section.proposal, section.content_json)
        investment_section = section.proposal.sections.filter(
            section_type=ProposalSection.SectionType.INVESTMENT,
        ).first()

    section.proposal.refresh_from_db()

    from content.serializers.proposal import ProposalSectionDetailSerializer
    payload = {
        'section': ProposalSectionDetailSerializer(section).data,
        'proposal_totals': {
            'total_investment': str(section.proposal.total_investment),
            'effective_total_investment': str(_effective_total_for_proposal(section.proposal)),
        },
    }
    if investment_section is not None:
        payload['investment_section'] = ProposalSectionDetailSerializer(investment_section).data
    return Response(payload, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def preview_sync_section(request, section_id):
    """
    Compute a read-only diff between the submitted content_json and the current
    project state. Does not save anything.

    Returns has_project=False if the proposal has no linked project yet.
    """
    from django.db import transaction as _tx
    from accounts.models import Project
    from accounts.services.technical_requirements_sync import compute_sync_diff

    section = get_object_or_404(ProposalSection, pk=section_id)
    if section.section_type != ProposalSection.SectionType.TECHNICAL_DOCUMENT:
        return Response({'detail': 'Not a technical_document section.'}, status=status.HTTP_400_BAD_REQUEST)

    content_json = request.data.get('content_json')
    if not isinstance(content_json, dict):
        return Response({'detail': 'content_json must be a dict.'}, status=status.HTTP_400_BAD_REQUEST)

    proposal = section.proposal
    if not proposal.platform_onboarding_completed_at or not proposal.deliverable_id:
        return Response({'ok': True, 'has_project': False})

    deliverable = proposal.deliverable
    project = Project.objects.select_related('client').get(pk=deliverable.project_id)

    diff = compute_sync_diff(project, content_json)

    return Response({
        'ok': True,
        'has_project': True,
        'project': {
            'id': project.id,
            'name': project.name,
            'client_email': project.client.email,
        },
        'deliverable': {
            'id': deliverable.id,
            'title': deliverable.title,
        },
        'diff': diff,
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def apply_sync_section(request, section_id):
    """
    Save the submitted content_json to the section and sync project requirements
    (with soft-deletion of records removed from the JSON). Transactional.
    """
    from django.db import transaction as _tx
    from accounts.services.technical_requirements_sync import sync_technical_requirements_for_deliverable

    section = get_object_or_404(ProposalSection, pk=section_id)
    if section.section_type != ProposalSection.SectionType.TECHNICAL_DOCUMENT:
        return Response({'detail': 'Not a technical_document section.'}, status=status.HTTP_400_BAD_REQUEST)

    content_json = request.data.get('content_json')
    if not isinstance(content_json, dict):
        return Response({'detail': 'content_json must be a dict.'}, status=status.HTTP_400_BAD_REQUEST)

    proposal = section.proposal
    if not proposal.platform_onboarding_completed_at or not proposal.deliverable_id:
        return Response(
            {'detail': 'Esta propuesta no tiene proyecto asociado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from content.serializers.proposal import ProposalSectionDetailSerializer

    with _tx.atomic():
        serializer = ProposalSectionUpdateSerializer(
            section, data={'content_json': content_json}, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        deliverable = proposal.deliverable
        sync_result = sync_technical_requirements_for_deliverable(
            deliverable, request.user, delete_removed=True,
        )

    return Response({
        **sync_result,
        'section': ProposalSectionDetailSerializer(section).data,
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_reorder_sections(request, proposal_id):
    """
    Reorder sections for a proposal.
    Body: { "sections": [{"id": 1, "order": 0}, {"id": 2, "order": 1}, ...] }
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    sections_data = request.data.get('sections', [])

    if not isinstance(sections_data, list):
        return Response(
            {'error': '"sections" must be a list of {id, order} objects.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    section_ids = {s['id'] for s in sections_data if 'id' in s}
    sections_qs = proposal.sections.filter(id__in=section_ids)
    sections_map = {s.id: s for s in sections_qs}

    updated = []
    for item in sections_data:
        section = sections_map.get(item.get('id'))
        if section and 'order' in item:
            section.order = item['order']
            updated.append(section)

    if updated:
        ProposalSection.objects.bulk_update(updated, ['order'])

    return Response({'reordered': len(updated)}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Auth check endpoint (for Nuxt admin middleware)
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def respond_to_proposal(request, proposal_uuid):
    """
    Client accepts, rejects, or negotiates a proposal.
    Body: { "action": "accepted" | "rejected" | "negotiating", "reason": "...", "comment": "..." }

    Updates proposal status, stores rejection feedback, and sends emails:
    - Acceptance: confirmation to client + notification to team
    - Rejection: thank-you to client + notification with reason to team
    - Negotiating: confirmation to client + notification to team with comment
    """
    proposal = get_object_or_404(BusinessProposal, uuid=proposal_uuid)

    if proposal.status not in ('sent', 'viewed'):
        return Response(
            {'error': 'This proposal cannot be responded to in its current state.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    action = request.data.get('action')
    if action not in ('accepted', 'rejected', 'negotiating'):
        return Response(
            {'error': 'Invalid action. Must be "accepted", "rejected", or "negotiating".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    proposal.status = action
    proposal.responded_at = timezone.now()
    update_fields = ['status', 'responded_at']

    if action == 'rejected':
        proposal.rejection_reason = request.data.get('reason', '')
        proposal.rejection_comment = request.data.get('comment', '')
        update_fields.extend(['rejection_reason', 'rejection_comment'])

    # 3.6 — Auto-pause follow-ups on client response
    if not proposal.automations_paused:
        proposal.automations_paused = True
        update_fields.append('automations_paused')

    proposal.save(update_fields=update_fields)

    # Log the response event
    change_type = action
    comment = request.data.get('comment', '')
    condition = request.data.get('condition', '').strip()
    description = f'Client {action} the proposal.'
    if action == 'rejected' and proposal.rejection_reason:
        description += f' Reason: {proposal.rejection_reason}'
    if action == 'negotiating' and comment:
        description += f' Comment: {comment[:500]}'
    if action == 'accepted' and condition:
        description += f' Condition: {condition[:500]}'
    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type=change_type,
        actor_type='client',
        description=description,
    )

    # Log conditional acceptance separately for easy querying
    if action == 'accepted' and condition:
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='cond_accepted',
            actor_type='client',
            description=f'Conditional acceptance: {condition[:500]}',
        )

    # Log automation pause
    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='note',
        actor_type='system',
        description=f'Automations paused: client responded with "{action}".',
    )

    from content.services.proposal_email_service import ProposalEmailService
    ProposalEmailService.send_response_notification(proposal, action)

    if action == 'rejected':
        ProposalEmailService.send_rejection_thank_you(proposal)
        # Schedule re-engagement email 48h later if rejection is budget-related
        _schedule_reengagement_if_budget(proposal)
    elif action == 'negotiating':
        ProposalEmailService.send_negotiation_notification(proposal, comment)
        ProposalEmailService.send_negotiation_confirmation(proposal)
    elif action == 'accepted':
        ProposalEmailService.send_acceptance_confirmation(proposal)

    return Response(
        {'status': action, 'message': f'Proposal {action} successfully.'},
        status=status.HTTP_200_OK,
    )


def _schedule_reengagement_if_budget(proposal):
    """
    Schedule a re-engagement email 48h after rejection when the reason
    is budget-related. Uses Huey's delay scheduling via the tasks module.
    """
    budget_keywords = (
        'presupuesto', 'budget', 'alto', 'precio', 'price', 'costo', 'cost',
    )
    reason = (proposal.rejection_reason or '').lower()
    if not any(kw in reason for kw in budget_keywords):
        return
    try:
        from content.tasks import send_rejection_reengagement
        send_rejection_reengagement.schedule(args=[proposal.id], delay=172800)
        logger.info(
            'Scheduled re-engagement email for proposal %s in 48h',
            proposal.uuid,
        )
    except Exception:
        logger.exception(
            'Failed to schedule re-engagement for proposal %s',
            proposal.uuid,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def comment_on_proposal(request, proposal_uuid):
    """
    Client submits a negotiation comment before deciding.
    Body: { "comment": "..." }

    Logs the comment in ProposalChangeLog and notifies the sales team.
    Does not change proposal status — client is in negotiation, not rejecting.
    """
    proposal = get_object_or_404(BusinessProposal, uuid=proposal_uuid)

    if proposal.status not in ('sent', 'viewed', 'rejected'):
        return Response(
            {'error': 'Comments cannot be submitted for this proposal.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    comment = (request.data.get('comment') or '').strip()
    if not comment:
        return Response(
            {'error': 'Comment cannot be empty.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='commented',
        actor_type='client',
        description=f'Client left a comment: {comment[:500]}',
    )

    from content.services.proposal_email_service import ProposalEmailService
    ProposalEmailService.send_comment_notification(proposal, comment)

    return Response(
        {'message': 'Comment received. We will be in touch soon.'},
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_admin_auth(request):
    """
    Returns 200 if user is authenticated staff, 403 otherwise.
    Used by the Nuxt admin middleware to verify session auth.
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Not authorized'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return Response(
        {'user': {'username': request.user.username, 'is_staff': True}},
        status=status.HTTP_200_OK,
    )


# ---------------------------------------------------------------------------
# Section engagement tracking (public)
# ---------------------------------------------------------------------------

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([TrackingAnonThrottle])
def track_proposal_engagement(request, proposal_uuid):
    """
    Record section-level engagement data from the client's browser.

    Accepts:
        {
            "session_id": "abc123",
            "sections": [
                {
                    "section_type": "greeting",
                    "section_title": "👋 Saludo",
                    "time_spent_seconds": 12.5,
                    "entered_at": "2024-01-15T10:30:00Z"
                },
                ...
            ]
        }

    Creates or updates a ProposalViewEvent for the session and bulk-creates
    ProposalSectionView rows.
    """
    proposal = get_object_or_404(
        BusinessProposal, uuid=proposal_uuid, is_active=True
    )

    # Don't track engagement for draft proposals
    if proposal.status == BusinessProposal.Status.DRAFT:
        return Response({'status': 'skipped'}, status=status.HTTP_200_OK)

    # Skip tracking for admin staff (detect via Django session cookie)
    from django.contrib.auth import get_user
    _user = get_user(request._request)
    if _user.is_authenticated and _user.is_staff:
        return Response({'status': 'skipped'}, status=status.HTTP_200_OK)

    session_id = request.data.get('session_id', '')
    sections = request.data.get('sections', [])

    if not session_id:
        return Response(
            {'error': 'session_id is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(sections, list) or not sections:
        return Response(
            {'error': 'sections must be a non-empty list.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get or create the view event for this session
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    view_mode = request.data.get('view_mode', 'unknown')
    if view_mode not in VIEW_MODE_LABELS:
        view_mode = 'unknown'

    view_event, _created = ProposalViewEvent.objects.get_or_create(
        proposal=proposal,
        session_id=session_id,
        defaults={
            'ip_address': ip_address,
            'user_agent': user_agent,
            'view_mode': view_mode,
        },
    )
    # Update view_mode if it was unknown and now we have a value
    if not _created and view_event.view_mode == 'unknown' and view_mode != 'unknown':
        view_event.view_mode = view_mode
        view_event.save(update_fields=['view_mode'])

    if _created:
        # UniqueConstraint on (proposal, session_id) prevents same-session floods,
        # so every _created=True is a distinct session worth logging.
        mode_label = VIEW_MODE_LABELS.get(view_mode)
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type=ProposalChangeLog.ChangeType.VIEWED,
            actor_type=ProposalChangeLog.ActorType.CLIENT,
            description=(
                f'Vista en modo {mode_label}.'
                if mode_label
                else 'El cliente visitó la propuesta.'
            ),
        )

    # --- Stakeholder detection ---
    # If this is a new session from a different IP than previous sessions,
    # it may indicate a secondary decision-maker is reviewing the proposal.
    if _created and not proposal.stakeholder_alert_sent_at and proposal.first_viewed_at:
        known_ips = set(
            ProposalViewEvent.objects
            .filter(proposal=proposal)
            .exclude(session_id=session_id)
            .values_list('ip_address', flat=True)
        )
        current_ip = ip_address or ''
        known_non_empty = {ip for ip in known_ips if ip}
        if known_non_empty and current_ip and current_ip not in known_non_empty:
            try:
                from content.services.proposal_email_service import (
                    ProposalEmailService,
                )
                sent = ProposalEmailService.send_stakeholder_detected_notification(
                    proposal, len(known_non_empty) + 1
                )
                if sent:
                    proposal.stakeholder_alert_sent_at = timezone.now()
                    proposal.save(update_fields=['stakeholder_alert_sent_at'])
            except Exception:
                logger.exception(
                    'Failed to send stakeholder alert for proposal %s',
                    proposal.uuid,
                )

    # Upsert section views: update time if exists, create if new
    for section_data in sections:
        section_type = section_data.get('section_type', '')
        if not section_type:
            continue

        entered_at_raw = section_data.get('entered_at')
        try:
            entered_at = parse_datetime(entered_at_raw) or timezone.now()
        except (TypeError, ValueError):
            entered_at = timezone.now()

        time_spent = float(section_data.get('time_spent_seconds', 0))
        section_title = section_data.get('section_title', '')[:255]
        subsection_key = section_data.get('subsection_key', '')[:50]

        existing = ProposalSectionView.objects.filter(
            view_event=view_event,
            section_type=section_type,
            entered_at=entered_at,
        ).first()

        if existing:
            existing.time_spent_seconds = time_spent
            existing.section_title = section_title
            existing.subsection_key = subsection_key
            existing.view_mode = view_mode
            existing.save(update_fields=['time_spent_seconds', 'section_title', 'subsection_key', 'view_mode'])
        else:
            ProposalSectionView.objects.create(
                view_event=view_event,
                section_type=section_type,
                section_title=section_title,
                subsection_key=subsection_key,
                time_spent_seconds=time_spent,
                entered_at=entered_at,
                view_mode=view_mode,
            )

    # --- 3.5 Engagement decay between sessions ---
    if proposal.status in ('sent', 'viewed'):
        current_section_count = len([s for s in sections if s.get('section_type')])
        # Get previous sessions' section counts
        prev_events = (
            ProposalViewEvent.objects
            .filter(proposal=proposal)
            .exclude(session_id=session_id)
        )
        if prev_events.exists():
            from django.db.models import Count
            prev_counts = list(
                ProposalSectionView.objects
                .filter(view_event__in=prev_events)
                .values('view_event')
                .annotate(cnt=Count('id'))
                .values_list('cnt', flat=True)
            )
            if prev_counts:
                avg_prev = sum(prev_counts) / len(prev_counts)
                if avg_prev > 0 and current_section_count < avg_prev * 0.5:
                    # Set persistent declining flag
                    if not proposal.engagement_declining:
                        proposal.engagement_declining = True
                        proposal.save(update_fields=['engagement_declining'])
                    # Check if we already created this alert recently
                    from datetime import timedelta as _td
                    recent_decay = ProposalAlert.objects.filter(
                        proposal=proposal,
                        alert_type='engagement_decay',
                        alert_date__gte=timezone.now() - _td(days=3),
                    ).exists()
                    if not recent_decay:
                        try:
                            ProposalAlert.objects.create(
                                proposal=proposal,
                                alert_type='engagement_decay',
                                message=(
                                    f'{proposal.client_name} vio {current_section_count} secciones '
                                    f'vs promedio anterior de {avg_prev:.0f}. Posible pérdida de interés.'
                                ),
                                alert_date=timezone.now(),
                            )
                        except Exception:
                            logger.exception(
                                'Failed to create engagement_decay alert for %s',
                                proposal.uuid,
                            )
                elif proposal.engagement_declining:
                    # Normal engagement restored — reset flag
                    proposal.engagement_declining = False
                    proposal.save(update_fields=['engagement_declining'])

    # --- Smart follow-up alert ---
    # Trigger if: ≥3 unique sessions AND 3+ day gap between first and latest view
    if not proposal.revisit_alert_sent_at and proposal.status in ('sent', 'viewed'):
        unique_sessions = (
            ProposalViewEvent.objects
            .filter(proposal=proposal)
            .values('session_id').distinct().count()
        )
        # Check temporal gap: latest view must be ≥3 days after first view
        from datetime import timedelta
        first_view = proposal.first_viewed_at
        latest_event = (
            ProposalViewEvent.objects
            .filter(proposal=proposal)
            .order_by('-viewed_at')
            .values_list('viewed_at', flat=True)
            .first()
        )
        has_temporal_gap = (
            first_view and latest_event
            and (latest_event - first_view) >= timedelta(days=3)
        )
        if unique_sessions >= 3 and has_temporal_gap:
            # Find top section by total time across all sessions
            from django.db.models import Sum
            top = (
                ProposalSectionView.objects
                .filter(view_event__proposal=proposal)
                .values('section_type', 'section_title')
                .annotate(total_time=Sum('time_spent_seconds'))
                .order_by('-total_time')
                .first()
            )
            top_section = top['section_title'] if top else ''
            top_time = top['total_time'] if top else 0
            try:
                from content.services.proposal_email_service import (
                    ProposalEmailService,
                )
                ProposalEmailService.send_revisit_alert(
                    proposal, unique_sessions, top_section, top_time,
                )
                proposal.revisit_alert_sent_at = timezone.now()
                proposal.save(update_fields=['revisit_alert_sent_at'])
            except Exception:
                logger.exception(
                    'Failed to send revisit alert for proposal %s',
                    proposal.uuid,
                )

    # --- Update cached heat score ---
    try:
        new_score = _compute_heat_score_for_proposal(proposal.id, timezone.now())
        if new_score != proposal.cached_heat_score:
            proposal.cached_heat_score = new_score
            proposal.save(update_fields=['cached_heat_score'])
    except Exception:
        logger.exception(
            'Failed to update cached_heat_score for proposal %s',
            proposal.uuid,
        )

    return Response({'status': 'ok'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([TrackingAnonThrottle])
def track_calculator_interaction(request, proposal_uuid):
    """
    Track calculator interactions: confirmed selections or abandonment.

    Payload:
        {
            "event": "confirmed" | "abandoned",
            "selected": [module_id, ...],
            "deselected": [module_id, ...],
            "total": 3500000
        }
    """
    import json as _json

    proposal = get_object_or_404(
        BusinessProposal, uuid=proposal_uuid, is_active=True,
    )

    # Skip tracking for admin staff
    from django.contrib.auth import get_user
    _user = get_user(request._request)
    if _user.is_authenticated and _user.is_staff:
        return Response({'status': 'skipped'}, status=status.HTTP_200_OK)

    event = request.data.get('event', '')
    if event not in ('confirmed', 'abandoned'):
        return Response(
            {'error': 'event must be "confirmed" or "abandoned".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    selected = request.data.get('selected', [])
    deselected = request.data.get('deselected', [])
    total = request.data.get('total', 0)
    elapsed_seconds = request.data.get('elapsed_seconds', 0)

    change_type = (
        ProposalChangeLog.ChangeType.CALCULATOR_CONFIRMED
        if event == 'confirmed'
        else ProposalChangeLog.ChangeType.CALCULATOR_ABANDONED
    )

    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type=change_type,
        actor_type='client',
        description=_json.dumps({
            'selected': selected,
            'deselected': deselected,
            'total': total,
            'elapsed_seconds': elapsed_seconds,
        }),
    )

    # Persist confirmed selections so PDF can use them as fallback
    if event == 'confirmed' and isinstance(selected, list):
        fr_section = proposal.sections.filter(
            section_type=ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS
        ).first()
        fr_content = fr_section.content_json if fr_section else None
        proposal.selected_modules = _normalize_selected_module_ids(
            selected, fr_content,
        )
        proposal.save(update_fields=['selected_modules', 'updated_at'])
        _resync_investment_from_modules(proposal, fr_content)

    return Response({'status': 'ok'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([TrackingAnonThrottle])
def track_requirement_click(request, proposal_uuid):
    """
    Track when a client clicks on a functional requirements group card.

    Payload: { "group_id": "...", "group_title": "..." }
    """
    import json as _json
    from datetime import timedelta

    proposal = get_object_or_404(
        BusinessProposal, uuid=proposal_uuid, is_active=True,
    )

    # Skip tracking for admin staff
    from django.contrib.auth import get_user
    _user = get_user(request._request)
    if _user.is_authenticated and _user.is_staff:
        return Response({'status': 'skipped'}, status=status.HTTP_200_OK)

    group_id = request.data.get('group_id', '')
    group_title = request.data.get('group_title', '')

    if not group_id and not group_title:
        return Response(
            {'error': 'group_id or group_title is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Deduplicate: skip if same group clicked in last 60 seconds
    recent = ProposalChangeLog.objects.filter(
        proposal=proposal,
        change_type='req_clicked',
        created_at__gte=timezone.now() - timedelta(seconds=60),
        description__contains=str(group_id),
    ).exists()

    if not recent:
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='req_clicked',
            actor_type='client',
            description=_json.dumps({
                'group_id': group_id,
                'group_title': group_title,
            }),
        )

    return Response({'status': 'ok'}, status=status.HTTP_200_OK)


def _compute_engagement_score(proposal, view_events, sections_data, unique_sessions):
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


def _compute_heat_score_for_proposal(proposal_id, now=None):
    """
    Compute heat score (1-10) for a single proposal for the list view.
    Lightweight version of engagement score.
    """
    result = _compute_heat_score_with_summary(proposal_id, now)
    return result['score']


def _compute_heat_score_with_summary(proposal_id, now=None):
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
    skipped = [s for s in _KEY_PROPOSAL_SECTIONS if s not in viewed_types]

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


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def request_magic_link(request):
    """
    Magic link re-access: client provides their email and receives
    a link to their most recent active proposal.

    Rate-limited: 1 request per email per 5 minutes (via simple DB check).
    Body: { "email": "client@example.com" }
    """
    from datetime import timedelta

    email = (request.data.get('email') or '').strip().lower()
    if not email:
        return Response(
            {'error': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Rate limiting: check EmailLog for recent magic_link sends to this email
    five_min_ago = timezone.now() - timedelta(minutes=5)
    try:
        from content.models import EmailLog
        recent = EmailLog.objects.filter(
            template_key='magic_link',
            recipient=email,
            sent_at__gte=five_min_ago,
        ).exists()
        if recent:
            # Still return 200 to avoid email enumeration
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)
    except Exception:
        pass

    # Find proposals for this email
    proposals = BusinessProposal.objects.filter(
        client_email__iexact=email,
        is_active=True,
    ).order_by('-created_at')[:5]

    if proposals.exists():
        try:
            from content.services.proposal_email_service import (
                ProposalEmailService,
            )
            ProposalEmailService.send_magic_link_email(email, list(proposals))
        except Exception:
            logger.exception(
                'Failed to send magic link email to %s', email,
            )

    # Always return 200 to prevent email enumeration
    return Response({'status': 'ok'}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Proposal sharing (public)
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def create_share_link(request, proposal_uuid):
    """
    Create a tracked share link for a proposal.
    Body: { "name": "...", "email": "..." }

    Returns the share link UUID for constructing the shared URL.
    Notifies the sales team about the sharing event.
    """
    proposal = get_object_or_404(
        BusinessProposal, uuid=proposal_uuid, is_active=True
    )

    name = request.data.get('name', '').strip()
    email = request.data.get('email', '').strip()

    if not name:
        return Response(
            {'error': 'Name is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    share_link = ProposalShareLink.objects.create(
        proposal=proposal,
        shared_by_name=name,
        shared_by_email=email,
    )

    try:
        from content.services.proposal_email_service import ProposalEmailService
        ProposalEmailService.send_share_notification(proposal, share_link)
    except Exception:
        logger.exception(
            'Failed to send share notification for proposal %s',
            proposal.uuid,
        )

    serializer = ProposalShareLinkSerializer(share_link)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_shared_proposal(request, share_uuid):
    """
    Retrieve a proposal via a share link UUID.
    Optionally records viewer info from query params: ?name=&email=

    Increments the share link's view_count and sets first_viewed_at.
    Returns the full proposal detail (same as public view).
    """
    share_link = get_object_or_404(ProposalShareLink, uuid=share_uuid)
    proposal = share_link.proposal

    if not proposal.is_active:
        return Response(
            {'error': 'This proposal is not available.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if proposal.is_expired:
        return Response(
            {'error': 'This proposal has expired.'},
            status=status.HTTP_410_GONE,
        )

    # Record viewer info
    viewer_name = request.query_params.get('name', '').strip()
    viewer_email = request.query_params.get('email', '').strip()
    update_fields = ['view_count']

    share_link.view_count += 1
    if not share_link.first_viewed_at:
        share_link.first_viewed_at = timezone.now()
        update_fields.append('first_viewed_at')
    if viewer_name and not share_link.recipient_name:
        share_link.recipient_name = viewer_name
        update_fields.append('recipient_name')
    if viewer_email and not share_link.recipient_email:
        share_link.recipient_email = viewer_email
        update_fields.append('recipient_email')

    share_link.save(update_fields=update_fields)

    serializer = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': False}
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Schedule follow-up (public — for rejected proposals)
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def schedule_followup(request, proposal_uuid):
    """
    Schedule a follow-up reminder for a rejected proposal.
    Body: { "months": 3 }

    The client requests to be contacted again after N months.
    Schedules a Huey task for the follow-up email.
    """
    proposal = get_object_or_404(BusinessProposal, uuid=proposal_uuid)

    if proposal.status != 'rejected':
        return Response(
            {'error': 'Follow-up can only be scheduled for rejected proposals.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if proposal.followup_scheduled_at:
        return Response(
            {'error': 'A follow-up is already scheduled for this proposal.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    months = request.data.get('months', 3)
    try:
        months = int(months)
        if months < 1 or months > 12:
            raise ValueError
    except (TypeError, ValueError):
        return Response(
            {'error': 'months must be an integer between 1 and 12.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from datetime import timedelta
    followup_at = timezone.now() + timedelta(days=months * 30)
    proposal.followup_scheduled_at = followup_at
    proposal.save(update_fields=['followup_scheduled_at'])

    # Schedule the Huey task
    try:
        from content.tasks import send_scheduled_followup
        delay_seconds = int((followup_at - timezone.now()).total_seconds())
        send_scheduled_followup.schedule(
            args=(proposal.id,), delay=delay_seconds
        )
        logger.info(
            'Scheduled followup for proposal %s in %d months',
            proposal.uuid, months,
        )
    except Exception:
        logger.exception(
            'Failed to schedule followup task for proposal %s',
            proposal.uuid,
        )

    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='updated',
        field_name='followup_scheduled_at',
        new_value=followup_at.isoformat(),
        actor_type='client',
        description=f'Client requested follow-up in {months} months.',
    )

    return Response(
        {'status': 'scheduled', 'followup_at': followup_at.isoformat()},
        status=status.HTTP_200_OK,
    )


# ---------------------------------------------------------------------------
# Proposal analytics (admin only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_proposal_analytics(request, proposal_id):
    """
    Return aggregated section engagement analytics for a proposal.

    Includes: time-to-first-view, time-to-response, skipped sections,
    device breakdown, per-section engagement, session history, and
    change log timeline.
    """
    from django.db.models import Sum, Count, Avg, Subquery, OuterRef

    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

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

    # Enrich with section_title from most recent entry
    visited_types = set()
    sections_data = []
    for stat in section_stats:
        visited_types.add(stat['section_type'])
        latest = (
            ProposalSectionView.objects
            .filter(
                view_event__proposal=proposal,
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
                subsection_key__in=_TECHNICAL_FRAGMENT_ORDER,
            )
            .values('subsection_key')
            .annotate(reached_count=Count('view_event__session_id', distinct=True))
        )
    }
    tech_section = proposal.sections.filter(section_type='technical_document').first()
    tech_doc = (tech_section.content_json if tech_section and tech_section.content_json else {})
    for fragment_key in _TECHNICAL_FRAGMENT_ORDER:
        if not _technical_fragment_has_content(fragment_key, tech_doc):
            continue
        tech_reached = tech_reached_map.get(fragment_key, 0)
        tech_drop_off = round(
            (1 - tech_reached / technical_sessions_reached) * 100, 1
        ) if technical_sessions_reached > 0 else 0
        funnel_data.append({
            'section_type': 'technical_document_public',
            'section_title': _TECHNICAL_FRAGMENT_TITLES[fragment_key],
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
    engagement_score = _compute_engagement_score(
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

    return Response({
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
    }, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Global KPI Dashboard (admin only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def proposal_dashboard(request):
    """
    Return aggregated KPIs across all proposals for the admin dashboard.

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
    effective_totals = _build_effective_totals_map(totals_input)
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
        dropoff_allow = _dashboard_top_dropoff_allowlist()
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

    return Response({
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
    }, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# CSV Export (admin only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def export_proposal_analytics_csv(request, proposal_id):
    """
    Export proposal analytics as a CSV file.

    Includes two sheets combined:
    1. Section engagement summary
    2. Session history
    """
    import csv
    from django.http import HttpResponse as DjangoHttpResponse
    from django.db.models import Sum, Count, Avg

    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    response = DjangoHttpResponse(content_type='text/csv')
    filename = f'analytics_{proposal.client_name}_{proposal.id}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    # Header
    writer.writerow([f'Analytics Report: {proposal.title}'])
    writer.writerow([f'Client: {proposal.client_name}'])
    writer.writerow([f'Status: {proposal.status}'])
    writer.writerow([f'Total Views: {proposal.view_count}'])
    writer.writerow([])

    # Section engagement
    writer.writerow(['--- SECTION ENGAGEMENT ---'])
    writer.writerow([
        'Note: technical_document + technical_document_public both belong to '
        '”detalle técnico” (vista panel vs vista pública).',
    ])
    writer.writerow([
        'Section Type', 'Metric group', 'Section Title', 'Visit Count',
        'Total Time (s)', 'Avg Time (s)',
    ])

    section_stats = (
        ProposalSectionView.objects
        .filter(view_event__proposal=proposal)
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
            ProposalSectionView.objects
            .filter(view_event__proposal=proposal, section_type=stat['section_type'])
            .order_by('-entered_at')
            .values_list('section_title', flat=True)
            .first()
        ) or stat['section_type']
        stype = stat['section_type']
        writer.writerow([
            stype,
            _csv_analytics_section_group(stype),
            latest_title,
            stat['visit_count'],
            round(stat['total_time'] or 0, 1),
            round(stat['avg_time'] or 0, 1),
        ])

    writer.writerow([])

    # Session history
    writer.writerow(['--- SESSION HISTORY ---'])
    writer.writerow(['Session ID', 'IP Address', 'Viewed At', 'Sections Viewed', 'Total Time (s)'])

    for event in proposal.view_events.order_by('-viewed_at')[:100]:
        sv = event.section_views.all()
        writer.writerow([
            event.session_id,
            event.ip_address or '',
            event.viewed_at.isoformat(),
            sv.count(),
            round(sum(s.time_spent_seconds for s in sv), 1),
        ])

    writer.writerow([])

    # Change log
    writer.writerow(['--- CHANGE LOG ---'])
    writer.writerow(['Date', 'Type', 'Field', 'Old Value', 'New Value', 'Description'])
    for log in proposal.change_logs.order_by('-created_at')[:100]:
        writer.writerow([
            log.created_at.isoformat(),
            log.change_type,
            log.field_name,
            log.old_value,
            log.new_value,
            log.description,
        ])

    return response


# ---------------------------------------------------------------------------
# Mini-CRM: client history (admin only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_clients(request):
    """
    Return a list of unique clients with their full proposal history.

    Groups by a compound (resolved_email, client_name) key so that two
    different clients sharing the same contact email stay separated, while
    proposals with a blank email still merge into the email group of the
    same client_name.  When no email exists anywhere for a name, the email
    component of the key is empty and grouping falls back to name alone.
    Each client entry contains:
    - client_name, client_email
    - total_proposals, accepted, rejected, pending counts
    - last_status, last_sent_at
    - proposals: list of lightweight proposal summaries
    """
    proposals_qs = (
        BusinessProposal.objects
        .order_by('client_email', '-created_at')
        .values(
            'id', 'uuid', 'title', 'client_name', 'client_email',
            'status', 'total_investment', 'currency',
            'project_type', 'market_type',
            'sent_at', 'created_at', 'responded_at',
            'rejection_reason', 'rejection_comment',
            'view_count', 'expires_at',
        )
    )

    proposals_list = list(proposals_qs)

    # Pass 1: map each client name to its primary (first non-blank) email
    name_to_email: dict[str, str] = {}
    for p in proposals_list:
        email = (p['client_email'] or '').strip().lower()
        name = p['client_name'].strip().lower()
        if email and name not in name_to_email:
            name_to_email[name] = email

    # Pass 2: group by (resolved_email, name) — see docstring for rationale.
    clients: dict = {}
    for p in proposals_list:
        email = (p['client_email'] or '').strip().lower()
        name = p['client_name'].strip().lower()
        resolved_email = email if email else name_to_email.get(name, '')
        key = (resolved_email, name)

        if key not in clients:
            clients[key] = {
                'client_name': p['client_name'],
                'client_email': p['client_email'] or '',
                'proposals': [],
            }
        if email and not clients[key]['client_email']:
            clients[key]['client_email'] = p['client_email']
        clients[key]['proposals'].append(p)

    result = []
    for key, client in clients.items():
        props = client['proposals']
        statuses = [p['status'] for p in props]
        last = props[0]
        result.append({
            'client_key': f"{key[0]}|{key[1]}",
            'client_name': client['client_name'],
            'client_email': client['client_email'],
            'total_proposals': len(props),
            'accepted': statuses.count('accepted') + statuses.count('finished'),
            'rejected': statuses.count('rejected'),
            'pending': sum(1 for s in statuses if s in ('draft', 'sent', 'viewed')),
            'last_status': last['status'],
            'last_sent_at': last['sent_at'].isoformat() if last['sent_at'] else None,
            'proposals': [
                {
                    'id': p['id'],
                    'uuid': str(p['uuid']),
                    'title': p['title'],
                    'status': p['status'],
                    'project_type': p['project_type'] or '',
                    'market_type': p['market_type'] or '',
                    'total_investment': str(p['total_investment']),
                    'currency': p['currency'],
                    'view_count': p['view_count'],
                    'sent_at': p['sent_at'].isoformat() if p['sent_at'] else None,
                    'created_at': p['created_at'].isoformat() if p['created_at'] else None,
                    'responded_at': p['responded_at'].isoformat() if p['responded_at'] else None,
                    'rejection_reason': p['rejection_reason'] or '',
                    'rejection_comment': p['rejection_comment'] or '',
                    'expires_at': p['expires_at'].isoformat() if p['expires_at'] else None,
                }
                for p in props
            ],
        })

    # Sort by most recent activity first
    result.sort(key=lambda c: c['last_sent_at'] or '', reverse=True)

    return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def log_activity(request, proposal_id):
    """
    Manually log a seller activity (call, meeting, follow-up, note) on a proposal.

    Body:
        change_type: one of 'call', 'meeting', 'followup', 'note'
        description: free-text description of the activity
    """
    proposal = get_object_or_404(BusinessProposal, id=proposal_id)
    change_type = request.data.get('change_type', '')
    description = request.data.get('description', '')

    allowed_types = ['call', 'meeting', 'followup', 'note']
    if change_type not in allowed_types:
        return Response(
            {'error': f'change_type must be one of: {", ".join(allowed_types)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not description.strip():
        return Response(
            {'error': 'description is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    log = ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type=change_type,
        actor_type='seller',
        description=description.strip(),
    )
    proposal.last_activity_at = timezone.now()
    proposal.save(update_fields=['last_activity_at'])

    return Response({
        'id': log.id,
        'change_type': log.change_type,
        'description': log.description,
        'created_at': log.created_at.isoformat(),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def proposal_alerts(request):
    """
    Return proposals that need attention:
    - Sent but not viewed after reminder_days
    - Viewed but not responded after urgency_reminder_days
    - Expiring within 3 days
    """
    now = timezone.now()
    from datetime import timedelta

    alerts = []
    dismissed_computed_keys = {
        marker.removeprefix(_COMPUTED_ALERT_DISMISS_PREFIX)
        for marker in ProposalAlert.objects.filter(
            is_dismissed=True,
            message__startswith=_COMPUTED_ALERT_DISMISS_PREFIX,
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

    # Manual alerts (not dismissed, alert_date <= now)
    manual_qs = ProposalAlert.objects.filter(
        is_dismissed=False,
        alert_date__lte=now,
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
            key = _computed_alert_key(
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

    return Response(alerts, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_proposal_alert(request):
    """
    Create a manual alert/reminder for a proposal.

    Payload: { proposal, alert_type, message, alert_date }
    """
    serializer = ProposalAlertSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def dismiss_proposal_alert(request, alert_id):
    """
    Dismiss an alert.

    - Manual alert: pass only path param `alert_id` (ProposalAlert ID).
    - Computed alert: pass payload
      { computed_alert_type, ref_date } and path param `alert_id` as proposal ID.
    """
    computed_alert_type = request.data.get('computed_alert_type')
    if computed_alert_type:
        if computed_alert_type not in _COMPUTED_ALERT_TYPES:
            return Response(
                {'error': 'Invalid computed_alert_type.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        proposal = get_object_or_404(BusinessProposal, pk=alert_id)
        ref_date = request.data.get('ref_date', '')
        marker_key = _computed_alert_key(proposal.id, computed_alert_type, ref_date)
        marker_message = f'{_COMPUTED_ALERT_DISMISS_PREFIX}{marker_key}'
        if not ProposalAlert.objects.filter(
            proposal=proposal,
            is_dismissed=True,
            message=marker_message,
        ).exists():
            ProposalAlert.objects.create(
                proposal=proposal,
                alert_type='custom',
                message=marker_message,
                alert_date=timezone.now(),
                is_dismissed=True,
            )
        return Response(
            {'status': 'dismissed', 'computed_alert_key': marker_key},
            status=status.HTTP_200_OK,
        )

    alert = get_object_or_404(ProposalAlert, pk=alert_id)
    alert.is_dismissed = True
    alert.save(update_fields=['is_dismissed'])
    return Response({'status': 'dismissed'}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Proposal Default Config
# ---------------------------------------------------------------------------


@api_view(['GET', 'PUT'])
@permission_classes([IsAdminUser])
def proposal_defaults(request):
    """
    GET  — Retrieve the default section config for a language.
           Falls back to the hardcoded defaults when no DB config exists.
    PUT  — Save (create or update) the default section config for a language.
    """
    from content.services.proposal_service import ProposalService

    lang = request.query_params.get('lang', request.data.get('language', 'es'))
    if lang not in ('es', 'en'):
        return Response(
            {'detail': 'lang must be "es" or "en".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if request.method == 'GET':
        config = ProposalDefaultConfig.objects.filter(language=lang).first()
        if config:
            serializer = ProposalDefaultConfigSerializer(config)
            return Response(serializer.data)
        # Return hardcoded defaults wrapped in the same shape
        hardcoded = ProposalService.get_hardcoded_defaults(lang)
        return Response({
            'id': None,
            'language': lang,
            'sections_json': hardcoded,
            'default_currency': ProposalDefaultConfig.Currency.COP,
            'default_total_investment': '0.00',
            'hosting_percent': 40,
            'hosting_discount_semiannual': 20,
            'hosting_discount_quarterly': 10,
            'expiration_days': ProposalService.DEFAULT_EXPIRATION_DAYS,
            'reminder_days': 3,
            'urgency_reminder_days': 7,
            'default_discount_percent': 0,
            'default_slug_pattern': '{client_name}',
            'created_at': None,
            'updated_at': None,
        })

    # PUT
    config = ProposalDefaultConfig.objects.filter(language=lang).first()
    payload = dict(request.data)
    payload['language'] = lang
    if 'sections_json' not in payload:
        if config:
            payload['sections_json'] = config.sections_json
        else:
            payload['sections_json'] = ProposalService.get_hardcoded_defaults(lang)
    if 'default_slug_pattern' not in payload and config:
        # Preserve the previously saved pattern when caller only updates
        # other fields (e.g. general form submits without touching the pattern).
        payload['default_slug_pattern'] = config.default_slug_pattern

    if config:
        serializer = ProposalDefaultConfigSerializer(config, data=payload)
    else:
        serializer = ProposalDefaultConfigSerializer(data=payload)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reset_proposal_defaults(request):
    """
    Delete the DB-backed default config for a language, reverting to hardcoded defaults.
    """
    lang = request.data.get('language', 'es')
    if lang not in ('es', 'en'):
        return Response(
            {'detail': 'language must be "es" or "en".'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    deleted_count, _ = ProposalDefaultConfig.objects.filter(language=lang).delete()
    return Response(
        {'status': 'reset', 'deleted': deleted_count > 0},
        status=status.HTTP_200_OK,
    )


# ---------------------------------------------------------------------------
# F11: Email Deliverability Dashboard
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def email_deliverability_dashboard(request):
    """
    Return aggregated email deliverability stats for the admin dashboard.

    Includes: total sent, success rate, per-template breakdown,
    daily trend (last 30 days), and recent failures.
    """
    from datetime import timedelta
    from django.db.models import Count, Q
    from django.db.models.functions import TruncDate
    from content.models import EmailLog

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    all_logs = EmailLog.objects.all()
    recent_logs = all_logs.filter(sent_at__gte=thirty_days_ago)

    # Overall counts
    total = recent_logs.count()
    by_status = dict(
        recent_logs.values('status')
        .annotate(count=Count('id'))
        .values_list('status', 'count')
    )
    sent_count = by_status.get('sent', 0) + by_status.get('delivered', 0)
    failed_count = by_status.get('failed', 0) + by_status.get('bounced', 0)
    success_rate = round((sent_count / total) * 100, 1) if total > 0 else 0

    # Per-template breakdown
    template_stats = list(
        recent_logs
        .values('template_key')
        .annotate(
            total=Count('id'),
            sent=Count('id', filter=Q(status__in=['sent', 'delivered'])),
            failed=Count('id', filter=Q(status__in=['failed', 'bounced'])),
        )
        .order_by('-total')
    )
    for stat in template_stats:
        stat['success_rate'] = (
            round((stat['sent'] / stat['total']) * 100, 1)
            if stat['total'] > 0 else 0
        )

    # Daily trend (last 30 days)
    daily_trend = list(
        recent_logs
        .annotate(date=TruncDate('sent_at'))
        .values('date')
        .annotate(
            total=Count('id'),
            sent=Count('id', filter=Q(status__in=['sent', 'delivered'])),
            failed=Count('id', filter=Q(status__in=['failed', 'bounced'])),
        )
        .order_by('date')
    )
    for entry in daily_trend:
        entry['date'] = entry['date'].isoformat()

    # Recent failures
    recent_failures = list(
        recent_logs.filter(status__in=['failed', 'bounced'])
        .order_by('-sent_at')[:20]
        .values(
            'template_key', 'recipient', 'status',
            'error_message', 'sent_at',
        )
    )
    for f in recent_failures:
        f['sent_at'] = f['sent_at'].isoformat()

    return Response({
        'total_emails_30d': total,
        'success_rate': success_rate,
        'sent_count': sent_count,
        'failed_count': failed_count,
        'by_template': template_stats,
        'daily_trend': daily_trend,
        'recent_failures': recent_failures,
    }, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Contract & document management endpoints
# ---------------------------------------------------------------------------

def _generate_and_save_contract_pdf(proposal):
    """Generate contract PDF from proposal.contract_params and save as ProposalDocument."""
    from content.services.contract_pdf_service import generate_contract_pdf

    pdf_bytes = generate_contract_pdf(proposal)
    if not pdf_bytes:
        return
    from django.core.files.base import ContentFile
    from content.models import ProposalDocument
    from content.services.pdf_utils import safe_pdf_filename

    filename = safe_pdf_filename(
        'Contrato_Desarrollo_Software',
        proposal.title or proposal.client_name,
        (proposal.created_at or timezone.now()).strftime('%Y-%m-%d'),
    )
    doc, _created = ProposalDocument.objects.get_or_create(
        proposal=proposal,
        document_type=ProposalDocument.DOC_TYPE_CONTRACT,
        defaults={'title': 'Contrato de desarrollo de software', 'is_generated': True},
    )
    doc.file.save(filename, ContentFile(pdf_bytes), save=True)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def save_contract_and_negotiate(request, proposal_id):
    """Save contract params, generate contract PDF, and move status to negotiating."""
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    allowed = BusinessProposal.ALLOWED_TRANSITIONS.get(proposal.status, frozenset())
    if 'negotiating' not in allowed:
        return Response(
            {'error': f'Cannot transition from {proposal.status} to negotiating.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ContractParamsSerializer(data=request.data.get('contract_params', {}))
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    old_status = proposal.status
    proposal.contract_params = serializer.validated_data
    proposal.status = BusinessProposal.Status.NEGOTIATING
    proposal.save(update_fields=['contract_params', 'status', 'updated_at'])

    _generate_and_save_contract_pdf(proposal)

    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='negotiating',
        field_name='status',
        old_value=old_status,
        new_value='negotiating',
        actor_type='seller',
        description='Status changed to negotiating with contract generation.',
    )

    detail = ProposalDetailSerializer(proposal, context={'request': request, 'is_admin': True})
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_contract_params(request, proposal_id):
    """Update contract params and regenerate contract PDF."""
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    serializer = ContractParamsSerializer(data=request.data.get('contract_params', {}))
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    proposal.contract_params = serializer.validated_data
    proposal.save(update_fields=['contract_params', 'updated_at'])

    _generate_and_save_contract_pdf(proposal)

    detail = ProposalDetailSerializer(proposal, context={'request': request, 'is_admin': True})
    return Response(detail.data, status=status.HTTP_200_OK)


def _get_contract_doc(proposal):
    """Return the contract ProposalDocument for *proposal*, or None."""
    from content.models import ProposalDocument
    return ProposalDocument.objects.filter(
        proposal=proposal,
        document_type=ProposalDocument.DOC_TYPE_CONTRACT,
    ).first()


def _contract_pdf_response(pdf_bytes, proposal, prefix):
    """Build an HttpResponse with a branded PDF filename."""
    from django.http import HttpResponse
    from content.services.pdf_utils import safe_pdf_filename

    filename = safe_pdf_filename(
        prefix,
        proposal.title or proposal.client_name,
        (proposal.created_at or timezone.now()).strftime('%Y-%m-%d'),
    )
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@api_view(['GET'])
@permission_classes([IsAdminUser])
def download_contract_pdf(request, proposal_id):
    """Download the generated contract PDF for a proposal."""
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    doc = _get_contract_doc(proposal)
    if not doc or not doc.file:
        return Response(
            {'error': 'Contract PDF not found. Generate it first.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return _contract_pdf_response(doc.file.read(), proposal, 'Contrato_Desarrollo_Software')


@api_view(['GET'])
@permission_classes([IsAdminUser])
def download_draft_contract_pdf(request, proposal_id):
    """Download the contract PDF with a diagonal BORRADOR watermark and no signature."""
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    from content.services.contract_pdf_service import generate_contract_pdf
    from content.services.pdf_utils import add_watermark_to_pdf

    pdf_bytes = generate_contract_pdf(proposal, draft=True)
    if not pdf_bytes:
        return Response(
            {'error': 'Could not generate draft contract PDF.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    draft_bytes = add_watermark_to_pdf(pdf_bytes)
    return _contract_pdf_response(draft_bytes, proposal, 'Borrador_Contrato')


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_company_settings(request):
    """Return company settings defaults for contract modal pre-fill."""
    from content.models import CompanySettings
    settings = CompanySettings.load()
    return Response(settings.to_dict(), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_default_contract_template(request):
    """Return the default contract template markdown for preview/editing."""
    from content.models import ContractTemplate
    template = ContractTemplate.get_default()
    if not template:
        return Response(
            {'error': 'No default contract template configured.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response({
        'id': template.id,
        'name': template.name,
        'content_markdown': template.content_markdown,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_proposal_documents(request, proposal_id):
    """List all documents attached to a proposal."""
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    docs = proposal.proposal_documents.all().order_by('-created_at')
    return Response([serialize_proposal_document(d) for d in docs], status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def upload_proposal_document(request, proposal_id):
    """Upload an additional document to a proposal (annexes, client docs, etc.)."""
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    from content.models import ProposalDocument

    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate file type and size
    from pathlib import Path
    ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg'}
    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
    ext = Path(file.name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return Response(
            {'error': f'File type {ext} not allowed. Allowed: {", ".join(sorted(ALLOWED_EXTENSIONS))}'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if file.size > MAX_FILE_SIZE:
        return Response(
            {'error': 'File too large. Maximum size is 15 MB.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    title = request.data.get('title', file.name)
    document_type = request.data.get('document_type', ProposalDocument.DOC_TYPE_OTHER)

    valid_types = {c[0] for c in ProposalDocument.DOC_TYPE_CHOICES}
    if document_type not in valid_types or document_type == ProposalDocument.DOC_TYPE_CONTRACT:
        return Response(
            {'error': f'Invalid document_type: {document_type}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    custom_type_label = (request.data.get('custom_type_label') or '').strip()[:100]

    doc = ProposalDocument.objects.create(
        proposal=proposal,
        document_type=document_type,
        custom_type_label=custom_type_label if document_type == ProposalDocument.DOC_TYPE_OTHER else '',
        title=title,
        file=file,
        is_generated=False,
    )
    return Response(serialize_proposal_document(doc), status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_proposal_document(request, proposal_id, doc_id):
    """Delete a user-uploaded proposal document. Generated docs cannot be deleted."""
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    from content.models import ProposalDocument

    doc = get_object_or_404(ProposalDocument, pk=doc_id, proposal=proposal)
    if doc.is_generated:
        return Response(
            {'error': 'Cannot delete system-generated documents.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    doc.file.delete(save=False)
    doc.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_documents_to_client(request, proposal_id):
    """Send selected proposal documents to the client via email.

    Expects JSON body::

        {
            "documents": ["draft_contract", "commercial", "technical"],
            "additional_doc_ids": [12, 15],
            "subject": "...",
            "greeting": "...",
            "body": "...",
            "footer": "...",
            "document_descriptions": [
                {"name": "Contrato", "description": "..."},
            ]
        }
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    if not proposal.client_email:
        return Response(
            {'error': 'No hay email del cliente configurado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ALLOWED_DOC_KEYS = {'draft_contract', 'commercial', 'technical'}
    doc_keys = request.data.get('documents', [])
    additional_ids = request.data.get('additional_doc_ids', [])
    invalid_keys = set(doc_keys) - ALLOWED_DOC_KEYS
    if invalid_keys:
        return Response(
            {'error': f'Claves de documento no reconocidas: {invalid_keys}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not doc_keys and not additional_ids:
        return Response(
            {'error': 'Debes seleccionar al menos un documento.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from content.models import ProposalDocument
    from content.services.pdf_utils import add_watermark_to_pdf, safe_pdf_filename

    date_str = (proposal.created_at or timezone.now()).strftime('%Y-%m-%d')
    client_title = proposal.client_name or proposal.title

    attachments = []

    if 'draft_contract' in doc_keys:
        from content.services.contract_pdf_service import generate_contract_pdf
        contract_bytes = generate_contract_pdf(proposal, draft=True)
        if contract_bytes:
            draft_bytes = add_watermark_to_pdf(contract_bytes)
            attachments.append((
                safe_pdf_filename('Borrador_Contrato', client_title, date_str),
                draft_bytes,
                'application/pdf',
            ))

    if 'commercial' in doc_keys:
        from content.services.proposal_pdf_service import ProposalPdfService
        pdf_bytes = ProposalPdfService.generate(proposal)
        if pdf_bytes:
            attachments.append((
                safe_pdf_filename('Propuesta_Comercial', client_title, date_str),
                pdf_bytes,
                'application/pdf',
            ))

    if 'technical' in doc_keys:
        from content.services.technical_document_pdf import (
            generate_technical_document_pdf,
        )
        tech_bytes = generate_technical_document_pdf(proposal)
        if tech_bytes:
            attachments.append((
                safe_pdf_filename('Detalle_Tecnico', client_title, date_str),
                tech_bytes,
                'application/pdf',
            ))

    if additional_ids:
        import mimetypes
        extra_docs = ProposalDocument.objects.filter(
            proposal=proposal, pk__in=additional_ids,
        )
        for doc in extra_docs:
            if doc.file:
                ext = doc.file.name.rsplit('.', 1)[-1] if '.' in doc.file.name else 'pdf'
                mime = mimetypes.guess_type(doc.file.name)[0] or 'application/octet-stream'
                safe_title = safe_pdf_filename(
                    'Documento', doc.title or 'documento', date_str,
                ).rsplit('.', 1)[0]  # strip the .pdf suffix
                with doc.file.open('rb') as f:
                    file_data = f.read()
                attachments.append((
                    f'{safe_title}.{ext}',
                    file_data,
                    mime,
                ))

    if not attachments:
        return Response(
            {'error': 'No se pudieron generar los documentos seleccionados.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Email content from the compose modal
    email_subject = request.data.get('subject', '') or None
    email_greeting = request.data.get('greeting', '') or None
    email_body = request.data.get('body', '') or None
    email_footer = request.data.get('footer', '') or None
    document_descriptions = request.data.get('document_descriptions', [])

    from content.services.proposal_email_service import ProposalEmailService
    sent = ProposalEmailService.send_documents_to_client(
        proposal, attachments,
        subject=email_subject,
        greeting=email_greeting,
        body=email_body,
        footer=email_footer,
        document_descriptions=document_descriptions,
    )

    if sent:
        return Response(
            {'message': f'Documentos enviados a {proposal.client_email}.'},
            status=status.HTTP_200_OK,
        )
    return Response(
        {'error': 'Error al enviar el correo. Intenta de nuevo.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# ── User-composed emails (branded & proposal) ────────────────────

_COMPOSED_EMAIL_ALLOWED_EXT = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg'}
_COMPOSED_EMAIL_MAX_FILE = 15 * 1024 * 1024  # 15 MB


def _resolve_proposal_doc_refs(proposal, doc_refs):
    """
    Resolve a list of doc_refs into email attachment tuples.

    Each ref is ``{'source': str, 'id'?: int}``. Supported sources:
      - ``contract_pdf``    → generated contract (final PDF)
      - ``contract_draft``  → freshly generated draft with watermark
      - ``commercial_pdf``  → commercial proposal PDF (ProposalPdfService)
      - ``technical_pdf``   → technical document PDF
      - ``proposal_document`` (with ``id``) → uploaded ProposalDocument file
    """
    import mimetypes

    from content.models import ProposalDocument
    from content.services.contract_pdf_service import generate_contract_pdf
    from content.services.pdf_utils import add_watermark_to_pdf, safe_pdf_filename
    from content.services.proposal_pdf_service import ProposalPdfService
    from content.services.technical_document_pdf import generate_technical_document_pdf
    from content.views._doc_refs import DocRefError

    doc_ids = [r.get('id') for r in doc_refs
               if isinstance(r, dict) and r.get('source') == 'proposal_document']
    docs_by_id = {
        doc.pk: doc
        for doc in ProposalDocument.objects.filter(proposal=proposal, pk__in=doc_ids)
    } if doc_ids else {}

    out = []
    date_str = (proposal.created_at or timezone.now()).strftime('%Y-%m-%d')
    client_title = proposal.client_name or proposal.title or 'cliente'

    for ref in doc_refs:
        if not isinstance(ref, dict):
            raise DocRefError('Cada doc_ref debe ser un objeto.')
        source = ref.get('source')

        if source == 'contract_pdf':
            pdf_bytes = generate_contract_pdf(proposal, draft=False)
            if not pdf_bytes:
                raise DocRefError('El contrato aún no ha sido generado.')
            out.append((
                safe_pdf_filename('Contrato', client_title, date_str),
                pdf_bytes,
                'application/pdf',
            ))
        elif source == 'contract_draft':
            pdf_bytes = generate_contract_pdf(proposal, draft=True)
            if not pdf_bytes:
                raise DocRefError('No se pudo generar el borrador del contrato.')
            out.append((
                safe_pdf_filename('Borrador_Contrato', client_title, date_str),
                add_watermark_to_pdf(pdf_bytes),
                'application/pdf',
            ))
        elif source == 'commercial_pdf':
            pdf_bytes = ProposalPdfService.generate(proposal)
            if not pdf_bytes:
                raise DocRefError('No se pudo generar la propuesta comercial.')
            out.append((
                safe_pdf_filename('Propuesta_Comercial', client_title, date_str),
                pdf_bytes,
                'application/pdf',
            ))
        elif source == 'technical_pdf':
            pdf_bytes = generate_technical_document_pdf(proposal)
            if not pdf_bytes:
                raise DocRefError('No se pudo generar el detalle técnico.')
            out.append((
                safe_pdf_filename('Detalle_Tecnico', client_title, date_str),
                pdf_bytes,
                'application/pdf',
            ))
        elif source == 'proposal_document':
            doc_id = ref.get('id')
            doc = docs_by_id.get(doc_id)
            if doc is None:
                raise DocRefError(f'Documento {doc_id} no existe.')
            if not doc.file:
                raise DocRefError(f'Documento "{doc.title}" no tiene archivo.')
            with doc.file.open('rb') as fh:
                data = fh.read()
            name = doc.file.name.rsplit('/', 1)[-1]
            mime = mimetypes.guess_type(name)[0] or 'application/octet-stream'
            out.append((name, data, mime))
        else:
            raise DocRefError(f'Fuente de documento desconocida: {source!r}.')

    return out


def _parse_composed_email(request, proposal, template_key):
    """
    Validate and parse a composed-email request.

    Returns ``(parsed_data, None)`` on success or ``(None, Response)`` on error.
    """
    import json
    import mimetypes
    from datetime import timedelta
    from pathlib import Path

    from django.core.exceptions import ValidationError as DjangoValidationError
    from django.core.validators import validate_email

    from content.models import EmailLog

    # ── Rate limit: 1 email per minute per proposal per type ──
    one_min_ago = timezone.now() - timedelta(minutes=1)
    if EmailLog.objects.filter(
        proposal=proposal, template_key=template_key,
        sent_at__gte=one_min_ago,
    ).exists():
        return None, Response(
            {'error': 'Espera al menos 1 minuto entre envíos.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # ── Required text fields ──
    recipient_email = (request.data.get('recipient_email') or '').strip()
    if not recipient_email:
        return None, Response(
            {'error': 'El campo destinatario es obligatorio.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        validate_email(recipient_email)
    except DjangoValidationError:
        return None, Response(
            {'error': 'El correo del destinatario no es válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    subject = (request.data.get('subject') or '').strip()
    if not subject:
        return None, Response(
            {'error': 'El asunto es obligatorio.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    greeting = (request.data.get('greeting') or '').strip()
    footer = (request.data.get('footer') or '').strip()

    # ── Sections (JSON-encoded string in multipart) ──
    raw_sections = request.data.get('sections', '[]')
    try:
        sections = json.loads(raw_sections) if isinstance(raw_sections, str) else raw_sections
    except (json.JSONDecodeError, TypeError):
        return None, Response(
            {'error': 'Las secciones deben ser un JSON válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(sections, list) or not any(s.strip() for s in sections if isinstance(s, str)):
        return None, Response(
            {'error': 'Debe incluir al menos una sección con contenido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    sections = [s for s in sections if isinstance(s, str) and s.strip()]

    # ── File attachments ──
    attachments = []
    for f in request.FILES.getlist('attachments'):
        ext = Path(f.name).suffix.lower()
        if ext not in _COMPOSED_EMAIL_ALLOWED_EXT:
            return None, Response(
                {'error': f'Tipo de archivo {ext} no permitido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if f.size > _COMPOSED_EMAIL_MAX_FILE:
            return None, Response(
                {'error': f'El archivo "{f.name}" excede el límite de 15 MB.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mime_type = mimetypes.guess_type(f.name)[0] or 'application/octet-stream'
        attachments.append((f.name, f.read(), mime_type))

    # ── References to existing documents (contract, PDFs, templates, uploads) ──
    from content.views._doc_refs import DocRefError, parse_doc_refs_field

    doc_refs, error_response = parse_doc_refs_field(request)
    if error_response:
        return None, error_response
    try:
        attachments.extend(_resolve_proposal_doc_refs(proposal, doc_refs))
    except DocRefError as err:
        return None, Response(
            {'error': str(err)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return {
        'recipient_email': recipient_email,
        'subject': subject,
        'greeting': greeting,
        'sections': sections,
        'footer': footer,
        'attachments': attachments or None,
    }, None


def _send_composed_email_view(request, proposal_id, send_method, template_key):
    """Shared handler for branded-email and proposal-email send views."""
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    parsed, error_response = _parse_composed_email(request, proposal, template_key)
    if error_response:
        return error_response

    sent = send_method(
        proposal=proposal,
        recipient_email=parsed['recipient_email'],
        subject=parsed['subject'],
        greeting=parsed['greeting'],
        sections=parsed['sections'],
        footer=parsed['footer'],
        attachments=parsed['attachments'],
    )

    if sent:
        return Response(
            {'message': f'Correo enviado a {parsed["recipient_email"]}.'},
            status=status.HTTP_200_OK,
        )
    return Response(
        {'error': 'Error al enviar el correo. Intenta de nuevo.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _get_email_defaults_view(request, proposal_id, template_key):
    """Shared handler for branded-email and proposal-email defaults views."""
    from content.services.proposal_email_service import ProposalEmailService

    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    context = {
        'client_name': proposal.client_name or '',
        'title': proposal.title or '',
    }
    field_values = ProposalEmailService._resolve_content(template_key, context)

    return Response(field_values, status=status.HTTP_200_OK)


def _list_emails_view(request, proposal_id, template_key):
    """Shared handler for branded-email and proposal-email history views."""
    from content.models import EmailLog

    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    logs = EmailLog.objects.filter(
        proposal=proposal,
        template_key=template_key,
    ).order_by('-sent_at')

    total = logs.count()
    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    page_size = 20
    offset = (page - 1) * page_size

    data = [
        {
            'id': log.pk,
            'recipient': log.recipient,
            'subject': log.subject,
            'status': log.status,
            'sent_at': log.sent_at.isoformat(),
            'metadata': log.metadata,
        }
        for log in logs[offset:offset + page_size]
    ]
    return Response({
        'results': data,
        'total': total,
        'page': page,
        'page_size': page_size,
        'has_next': offset + page_size < total,
    }, status=status.HTTP_200_OK)


# ── Branded email endpoints ──

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_branded_email(request, proposal_id):
    """Send a user-composed branded email with dynamic body sections."""
    from content.services.proposal_email_service import ProposalEmailService
    return _send_composed_email_view(request, proposal_id, ProposalEmailService.send_branded_email, 'branded_email')


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_branded_email_defaults(request, proposal_id):
    """Return admin-configurable defaults for the branded email composer."""
    return _get_email_defaults_view(request, proposal_id, 'branded_email')


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_branded_emails(request, proposal_id):
    """List branded emails sent for a proposal (paginated, 20 per page)."""
    return _list_emails_view(request, proposal_id, 'branded_email')


# ── Proposal email endpoints (logged as activity) ──

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_proposal_email(request, proposal_id):
    """Send a user-composed proposal email and log it as proposal activity."""
    from content.services.proposal_email_service import ProposalEmailService
    return _send_composed_email_view(request, proposal_id, ProposalEmailService.send_proposal_email, 'proposal_email')


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_proposal_email_defaults(request, proposal_id):
    """Return admin-configurable defaults for the proposal email composer."""
    return _get_email_defaults_view(request, proposal_id, 'proposal_email')


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_proposal_emails(request, proposal_id):
    """List proposal emails sent for a proposal (paginated, 20 per page)."""
    return _list_emails_view(request, proposal_id, 'proposal_email')


@api_view(['POST'])
@permission_classes([IsAdminUser])
def generate_email_markdown_attachment(request, proposal_id):
    """Generate a transient PDF from markdown for email attachment (not persisted)."""
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    return render_markdown_pdf_response(request, client_name=proposal.client_name or '')


# ── Project schedule endpoints (Cronograma admin tab) ──
#
# Two endpoints power the admin "Cronograma" tab:
#  - update_project_stage: PUT to set/update start_date + end_date for a stage
#  - complete_project_stage: POST to mark a stage as completed (silences alerts)


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_project_stage(request, proposal_id, stage_key):
    """
    Set or update start_date / end_date for a project stage.

    The row is created lazily if it doesn't exist (first time the admin
    schedules this stage). Date validation enforces start_date <= end_date.
    """
    from content.services.proposal_stage_tracker import ProposalStageTracker

    if stage_key not in dict(ProposalStageTracker.STAGE_DEFINITIONS):
        return Response(
            {'detail': f'Etapa desconocida: {stage_key}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    stage = ProposalStageTracker.get_or_create_stage(proposal, stage_key)

    serializer = ProposalProjectStageSerializer(
        stage,
        data=request.data,
        partial=True,
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    ProposalStageTracker.maybe_reset_warning_on_date_change(stage)

    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type=ProposalChangeLog.ChangeType.UPDATED,
        actor_type=ProposalChangeLog.ActorType.SELLER,
        description=(
            f'Cronograma — etapa "{stage.get_stage_key_display()}" '
            f'actualizada (inicio={stage.start_date}, fin={stage.end_date}).'
        ),
    )

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def complete_project_stage(request, proposal_id, stage_key):
    """
    Mark a project stage as completed.

    Sets `completed_at = now()` and clears the alert timestamps so future
    runs of the daily Huey task skip this stage entirely.
    """
    from content.services.proposal_stage_tracker import ProposalStageTracker

    if stage_key not in dict(ProposalStageTracker.STAGE_DEFINITIONS):
        return Response(
            {'detail': f'Etapa desconocida: {stage_key}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    stage = ProposalStageTracker.get_or_create_stage(proposal, stage_key)

    stage.completed_at = timezone.now()
    stage.warning_sent_at = None
    stage.last_overdue_reminder_at = None
    stage.save(update_fields=[
        'completed_at', 'warning_sent_at', 'last_overdue_reminder_at',
        'updated_at',
    ])

    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type=ProposalChangeLog.ChangeType.STAGE_COMPLETED,
        actor_type=ProposalChangeLog.ActorType.SELLER,
        description=(
            f'Cronograma — etapa "{stage.get_stage_key_display()}" '
            f'marcada como completada.'
        ),
    )

    return Response(
        ProposalProjectStageSerializer(stage).data,
        status=status.HTTP_200_OK,
    )
