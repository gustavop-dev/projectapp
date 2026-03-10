import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from content.models import (
    BusinessProposal, ProposalAlert, ProposalSection,
    ProposalViewEvent, ProposalSectionView,
    ProposalChangeLog, ProposalShareLink,
)
from content.serializers.proposal import (
    ProposalAlertSerializer,
    ProposalCreateUpdateSerializer,
    ProposalDetailSerializer,
    ProposalFromJSONSerializer,
    ProposalListSerializer,
    ProposalSectionUpdateSerializer,
    ProposalShareLinkSerializer,
    SECTION_KEY_MAP,
    SECTION_TYPE_TO_KEY,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_public_proposal(request, proposal_uuid):
    """
    Retrieve a proposal by UUID for client viewing.

    Increments view_count, sets first_viewed_at on first visit,
    updates status to VIEWED if currently SENT.
    Returns 410 Gone if expired.
    """
    proposal = get_object_or_404(BusinessProposal, uuid=proposal_uuid)

    if not proposal.is_active:
        return Response(
            {'error': 'This proposal is not available.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if proposal.is_expired:
        if proposal.status != BusinessProposal.Status.EXPIRED:
            proposal.status = BusinessProposal.Status.EXPIRED
            proposal.save(update_fields=['status'])

        # Post-expiration visit alert — high-intent signal
        if not proposal.post_expiration_alert_sent_at:
            try:
                from content.models import ProposalAlert
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

        return Response(
            {'error': 'This proposal has expired.'},
            status=status.HTTP_410_GONE,
        )

    # Only record views/metrics for proposals that have been sent (not drafts)
    is_first_view = False
    if proposal.status != BusinessProposal.Status.DRAFT:
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
    if is_first_view:
        try:
            from content.tasks import notify_first_view
            notify_first_view(proposal.id)
        except Exception:
            logger.exception(
                'Failed to queue first-view notification for proposal %s',
                proposal.uuid,
            )

    serializer = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': False}
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


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

    selected_modules_param = request.query_params.get('selected_modules', '')
    selected_modules = (
        [m.strip() for m in selected_modules_param.split(',') if m.strip()]
        if selected_modules_param
        else None
    )

    from content.services.proposal_pdf_service import ProposalPdfService
    pdf_bytes = ProposalPdfService.generate(
        proposal, selected_modules=selected_modules
    )

    if not pdf_bytes:
        return Response(
            {'error': 'PDF generation failed. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    from django.http import HttpResponse
    from django.utils import timezone as _tz
    _created = proposal.created_at or _tz.now()
    date_suffix = _created.strftime('%Y-%m-%d')
    filename = f'Propuesta_{proposal.client_name}_{date_suffix}.pdf'
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
    qs = BusinessProposal.objects.all()
    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    serializer = ProposalListSerializer(qs, many=True)
    data = serializer.data

    # Compute heat scores for non-draft active proposals
    now = timezone.now()
    for item in data:
        if item['status'] in ('sent', 'viewed') and item['is_active']:
            item['heat_score'] = _compute_heat_score_for_proposal(item['id'], now)
        else:
            item['heat_score'] = 0

    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_proposal(request, proposal_id):
    """
    Retrieve full proposal detail for admin editing.
    Returns all sections (including disabled ones).
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
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

    # Log creation
    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='created',
        description=(
            f'Proposal created: "{proposal.title}" for {proposal.client_name}. '
            f'Investment: ${proposal.total_investment} {proposal.currency}.'
        ),
    )

    # Auto-create default sections
    from content.services.proposal_service import ProposalService
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
        expires_at=data.get('expires_at'),
        reminder_days=data.get('reminder_days', 10),
        urgency_reminder_days=data.get('urgency_reminder_days', 15),
        discount_percent=data.get('discount_percent', 0),
    )

    # Use DEFAULT_SECTIONS as a template for title/order/is_wide_panel
    from content.services.proposal_service import ProposalService
    default_sections = ProposalService.get_default_sections(proposal.language)
    defaults_by_type = {s['section_type']: s for s in default_sections}

    for section_cfg in default_sections:
        section_type = section_cfg['section_type']
        json_key = SECTION_TYPE_TO_KEY.get(section_type)

        if json_key and json_key in sections_data:
            content_json = sections_data[json_key]
        else:
            content_json = section_cfg['content_json']

        # Special handling for greeting — ensure clientName and proposalTitle are set
        if section_type == 'greeting':
            general = sections_data.get('general', {})
            content_json.setdefault('proposalTitle', proposal.title)
            content_json.setdefault('clientName', proposal.client_name)
            if general.get('inspirationalQuote'):
                content_json['inspirationalQuote'] = general['inspirationalQuote']

        ProposalSection.objects.create(
            proposal=proposal,
            section_type=section_type,
            title=section_cfg['title'],
            order=section_cfg['order'],
            is_wide_panel=section_cfg.get('is_wide_panel', False),
            content_json=content_json,
        )

    detail = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': True}
    )
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_proposal_json_template(request):
    """
    Return a downloadable JSON template with all 12 sections
    pre-populated with default placeholder content.

    Query params:
        lang: 'es' (default) or 'en'
    """
    import copy
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

    return Response(template, status=status.HTTP_200_OK)


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
        'language', 'project_type', 'market_type',
        'expires_at', 'reminder_days', 'urgency_reminder_days',
    ]
    old_values = {f: str(getattr(proposal, f, '')) for f in tracked_fields}

    serializer = ProposalCreateUpdateSerializer(
        proposal, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    # Log field-level changes
    for field in tracked_fields:
        new_val = str(getattr(proposal, field, ''))
        if old_values[field] != new_val:
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='updated',
                field_name=field,
                old_value=old_values[field],
                new_value=new_val,
                description=f'{field}: {old_values[field]} → {new_val}',
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
def duplicate_proposal(request, proposal_id):
    """
    Duplicate a proposal: creates a deep copy with all its sections.
    The copy is reset to draft status with a clean lifecycle.
    """
    import copy as _copy
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)

    new_proposal = BusinessProposal.objects.create(
        title=f'{proposal.title} (copia)',
        client_name=proposal.client_name,
        client_email=proposal.client_email,
        slug='',
        language=proposal.language,
        total_investment=proposal.total_investment,
        currency=proposal.currency,
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
            content_json=_copy.deepcopy(section.content_json),
        )

    ProposalChangeLog.objects.create(
        proposal=new_proposal,
        change_type='duplicated',
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
        ProposalService.send_proposal(proposal)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='sent',
        description=f'Proposal sent to {proposal.client_email}.',
    )

    detail = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': True}
    )
    return Response(detail.data, status=status.HTTP_200_OK)


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
        ProposalService.resend_proposal(proposal)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type='resent',
        description=f'Proposal re-sent to {proposal.client_email}.',
    )

    detail = ProposalDetailSerializer(
        proposal, context={'request': request, 'is_admin': True}
    )
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_proposal_section(request, section_id):
    """
    Update a section's content_json, title, order, is_enabled, etc.
    """
    section = get_object_or_404(ProposalSection, pk=section_id)
    serializer = ProposalSectionUpdateSerializer(
        section, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    from content.serializers.proposal import ProposalSectionDetailSerializer
    detail = ProposalSectionDetailSerializer(section)
    return Response(detail.data, status=status.HTTP_200_OK)


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

    proposal.save(update_fields=update_fields)

    # Log the response event
    change_type = action
    comment = request.data.get('comment', '')
    description = f'Client {action} the proposal.'
    if action == 'rejected' and proposal.rejection_reason:
        description += f' Reason: {proposal.rejection_reason}'
    if action == 'negotiating' and comment:
        description += f' Comment: {comment[:500]}'
    ProposalChangeLog.objects.create(
        proposal=proposal,
        change_type=change_type,
        description=description,
    )

    from content.services.proposal_email_service import ProposalEmailService
    ProposalEmailService.send_response_notification(proposal, action)

    if action == 'accepted':
        ProposalEmailService.send_acceptance_confirmation(proposal)
    elif action == 'rejected':
        ProposalEmailService.send_rejection_thank_you(proposal)
        # Schedule re-engagement email 48h later if rejection is budget-related
        _schedule_reengagement_if_budget(proposal)
    elif action == 'negotiating':
        ProposalEmailService.send_negotiation_notification(proposal, comment)
        ProposalEmailService.send_negotiation_confirmation(proposal)

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
    ip_address = _get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

    view_event, _created = ProposalViewEvent.objects.get_or_create(
        proposal=proposal,
        session_id=session_id,
        defaults={
            'ip_address': ip_address,
            'user_agent': user_agent,
        },
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

        existing = ProposalSectionView.objects.filter(
            view_event=view_event,
            section_type=section_type,
            entered_at=entered_at,
        ).first()

        if existing:
            existing.time_spent_seconds = time_spent
            existing.section_title = section_title
            existing.save(update_fields=['time_spent_seconds', 'section_title'])
        else:
            ProposalSectionView.objects.create(
                view_event=view_event,
                section_type=section_type,
                section_title=section_title,
                time_spent_seconds=time_spent,
                entered_at=entered_at,
            )

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

    return Response({'status': 'ok'}, status=status.HTTP_200_OK)


def _compute_engagement_score(proposal, view_events, sections_data, unique_sessions):
    """
    Compute engagement score (0-100) for a proposal based on:
    - Recent sessions (last 7 days): 0-25 pts
    - Time on investment section / total time: 0-25 pts
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
    elif proposal.status == 'accepted':
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
    from datetime import timedelta
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
    from django.db.models import Sum
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
        p = _BP.objects.values('view_count', 'first_viewed_at').get(pk=proposal_id)
    except _BP.DoesNotExist:
        return 1
    if p['view_count'] >= 5:
        score += 2
    elif p['view_count'] >= 2:
        score += 1

    # Recency of last view — max 1 pt
    if p['first_viewed_at'] and (now - p['first_viewed_at']).days <= 3:
        score += 1

    return max(1, min(10, score))


def _get_client_ip(request):
    """Extract client IP from request, checking X-Forwarded-For first."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


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
    from django.db.models import Sum, Count, Avg

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

    # Skipped sections — enabled sections not in tracking data
    enabled_sections = (
        proposal.sections
        .filter(is_enabled=True)
        .values_list('section_type', 'title')
    )
    skipped_sections = [
        {'section_type': st, 'section_title': title}
        for st, title in enabled_sections
        if st not in visited_types
    ]

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
        })

    # Change log timeline
    change_logs = proposal.change_logs.order_by('-created_at')[:50]
    timeline = [
        {
            'change_type': log.change_type,
            'field_name': log.field_name,
            'old_value': log.old_value,
            'new_value': log.new_value,
            'description': log.description,
            'created_at': log.created_at.isoformat(),
        }
        for log in change_logs
    ]

    # --- Funnel: how many sessions reached each section in order ---
    ordered_sections = list(
        proposal.sections
        .filter(is_enabled=True)
        .order_by('order')
        .values_list('section_type', 'title')
    )
    funnel_data = []
    for section_type, section_title in ordered_sections:
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

    return Response({
        'total_views': total_views,
        'unique_sessions': unique_sessions,
        'first_viewed_at': (
            proposal.first_viewed_at.isoformat()
            if proposal.first_viewed_at else None
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
    total = all_proposals.count()

    # Pipeline value: sum of total_investment for active sent + viewed proposals
    pipeline_qs = all_proposals.filter(
        status__in=['sent', 'viewed'], is_active=True,
    )
    pipeline_agg = pipeline_qs.aggregate(total=Sum('total_investment'))
    pipeline_value = float(pipeline_agg['total'] or 0)
    pipeline_count = pipeline_qs.count()

    # Counts by status
    by_status = {}
    for choice_val, _label in BusinessProposal.Status.choices:
        by_status[choice_val] = all_proposals.filter(status=choice_val).count()

    # Conversion rate
    terminal = by_status.get('accepted', 0) + by_status.get('rejected', 0) + by_status.get('expired', 0)
    conversion_rate = round(
        (by_status.get('accepted', 0) / terminal * 100) if terminal > 0 else 0, 1
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

    # Avg proposal value by status
    avg_value_by_status = {}
    for s in ('accepted', 'rejected', 'expired', 'sent', 'viewed'):
        agg = all_proposals.filter(status=s).aggregate(avg=Avg('total_investment'))
        val = agg['avg']
        avg_value_by_status[s] = round(float(val), 2) if val else 0

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
            sent=Count('id', filter=Q(status__in=['sent', 'viewed', 'accepted', 'rejected', 'expired'])),
            accepted=Count('id', filter=Q(status='accepted')),
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
            'rejected': row['rejected'],
        }
        for row in monthly_qs
    ]

    # --- New metrics ---

    # Proposals that have been meaningfully viewed (status advanced past sent)
    viewed_statuses = ('viewed', 'accepted', 'rejected', 'expired')
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
        t = qs.filter(status__in=('accepted', 'rejected', 'expired')).count()
        a = qs.filter(status='accepted').count()
        return round(a / t * 100, 1) if t > 0 else None

    with_discount_qs = all_proposals.filter(discount_percent__gt=0)
    without_discount_qs = all_proposals.filter(discount_percent=0)
    discount_close_rate = _close_rate(with_discount_qs)
    no_discount_close_rate = _close_rate(without_discount_qs)

    # Detailed discount analysis
    avg_discount_all = with_discount_qs.aggregate(
        avg=Avg('discount_percent')
    )['avg']
    avg_discount_accepted = with_discount_qs.filter(
        status='accepted'
    ).aggregate(avg=Avg('discount_percent'))['avg']
    discount_analysis = {
        'with_discount_count': with_discount_qs.filter(
            status__in=['accepted', 'rejected', 'expired']
        ).count(),
        'with_discount_accepted': with_discount_qs.filter(
            status='accepted'
        ).count(),
        'without_discount_count': without_discount_qs.filter(
            status__in=['accepted', 'rejected', 'expired']
        ).count(),
        'without_discount_accepted': without_discount_qs.filter(
            status='accepted'
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
        section_types_qs = (
            _PSV.objects.values_list('section_type', flat=True).distinct()
        )
        dropoff_by_section = {}
        for sec_type in section_types_qs:
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
                total=Count('id', filter=Q(status__in=['accepted', 'rejected', 'expired'])),
                accepted=Count('id', filter=Q(status='accepted')),
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
            total=Count('id', filter=Q(status__in=['accepted', 'rejected', 'expired'])),
            accepted=Count('id', filter=Q(status='accepted')),
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
    writer.writerow(['Section Type', 'Section Title', 'Visit Count', 'Total Time (s)', 'Avg Time (s)'])

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
        writer.writerow([
            stat['section_type'],
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

    Groups BusinessProposal records by client_email (falling back to
    client_name when email is blank).  Each client entry contains:
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
            'sent_at', 'created_at', 'responded_at',
            'rejection_reason', 'rejection_comment',
            'view_count', 'expires_at',
        )
    )

    # Group by client key (email preferred, else name)
    clients: dict = {}
    for p in proposals_qs:
        key = (p['client_email'] or '').strip().lower() or p['client_name'].strip().lower()
        if key not in clients:
            clients[key] = {
                'client_name': p['client_name'],
                'client_email': p['client_email'] or '',
                'proposals': [],
            }
        clients[key]['proposals'].append(p)

    result = []
    for _key, client in clients.items():
        props = client['proposals']
        statuses = [p['status'] for p in props]
        last = props[0]
        result.append({
            'client_name': client['client_name'],
            'client_email': client['client_email'],
            'total_proposals': len(props),
            'accepted': statuses.count('accepted'),
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
    for p in seller_inactive_qs:
        ref_date = p.last_activity_at or p.sent_at
        if ref_date and (now - ref_date).days >= 3:
            # Check there's no recent seller activity
            has_recent = ProposalChangeLog.objects.filter(
                proposal=p,
                change_type__in=seller_activity_types,
                created_at__gte=now - timedelta(days=3),
            ).exists()
            if not has_recent:
                days = (now - ref_date).days
                alerts.append({
                    'id': p.id, 'uuid': str(p.uuid),
                    'title': p.title, 'client_name': p.client_name,
                    'alert_type': 'seller_inactive',
                    'days_since': days,
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
    for p in zombie_qs:
        has_activity = ProposalChangeLog.objects.filter(
            proposal=p,
            change_type__in=seller_activity_types,
        ).exists()
        if not has_activity:
            days = (now - p.sent_at).days
            alerts.append({
                'id': p.id, 'uuid': str(p.uuid),
                'title': p.title, 'client_name': p.client_name,
                'alert_type': 'zombie',
                'days_since': days,
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
            'message': f'Borrador abandonado — sin edición en {days} días.',
        })

    # Zombie sent stale: sent >10 days, no views
    zombie_sent_stale_qs = BusinessProposal.objects.filter(
        status=BusinessProposal.Status.SENT,
        is_active=True,
        view_count=0,
        first_viewed_at__isnull=True,
        sent_at__isnull=False,
        sent_at__lte=now - timedelta(days=10),
    )
    for p in zombie_sent_stale_qs:
        days = (now - p.sent_at).days
        alerts.append({
            'id': p.id, 'uuid': str(p.uuid),
            'title': p.title, 'client_name': p.client_name,
            'alert_type': 'zombie_sent_stale',
            'days_since': days,
            'message': f'Enviada hace {days} días — nunca vista.',
        })

    # Late return: client didn't visit for ≥5 days then came back in last 24h
    late_return_candidates = BusinessProposal.objects.filter(
        status__in=[BusinessProposal.Status.SENT, BusinessProposal.Status.VIEWED],
        is_active=True,
    )
    for p in late_return_candidates:
        events = list(
            ProposalViewEvent.objects
            .filter(proposal=p)
            .order_by('-viewed_at')
            .values_list('viewed_at', flat=True)[:2]
        )
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
        })

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
    Dismiss (hide) a manual alert by marking it as dismissed.
    """
    alert = get_object_or_404(ProposalAlert, pk=alert_id)
    alert.is_dismissed = True
    alert.save(update_fields=['is_dismissed'])
    return Response({'status': 'dismissed'}, status=status.HTTP_200_OK)
