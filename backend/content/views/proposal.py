import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from content.models import BusinessProposal, ProposalSection
from content.serializers.proposal import (
    ProposalCreateUpdateSerializer,
    ProposalDetailSerializer,
    ProposalListSerializer,
    ProposalSectionUpdateSerializer,
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
        return Response(
            {'error': 'This proposal has expired.'},
            status=status.HTTP_410_GONE,
        )

    # Record the view
    proposal.view_count += 1
    update_fields = ['view_count']

    if proposal.first_viewed_at is None:
        proposal.first_viewed_at = timezone.now()
        update_fields.append('first_viewed_at')

    if proposal.status == BusinessProposal.Status.SENT:
        proposal.status = BusinessProposal.Status.VIEWED
        update_fields.append('status')

    proposal.save(update_fields=update_fields)

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

    from content.services.proposal_pdf_service import ProposalPdfService
    pdf_bytes = ProposalPdfService.generate(proposal)

    if not pdf_bytes:
        return Response(
            {'error': 'PDF generation failed. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    from django.http import HttpResponse
    filename = f'Propuesta_{proposal.client_name}.pdf'
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
    """
    qs = BusinessProposal.objects.all()
    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    serializer = ProposalListSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


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

    # Auto-create default sections
    from content.services.proposal_service import ProposalService
    default_sections = ProposalService.get_default_sections(proposal.language)
    for section_cfg in default_sections:
        if section_cfg['section_type'] == 'greeting':
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


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_proposal(request, proposal_id):
    """
    Update proposal metadata (title, client_name, etc.).
    """
    proposal = get_object_or_404(BusinessProposal, pk=proposal_id)
    serializer = ProposalCreateUpdateSerializer(
        proposal, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
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
    Client accepts or rejects a proposal.
    Body: { "action": "accepted" | "rejected", "reason": "...", "comment": "..." }

    Updates proposal status, stores rejection feedback, and sends emails:
    - Acceptance: confirmation to client + notification to team
    - Rejection: thank-you to client + notification with reason to team
    """
    proposal = get_object_or_404(BusinessProposal, uuid=proposal_uuid)

    if proposal.status not in ('sent', 'viewed'):
        return Response(
            {'error': 'This proposal cannot be responded to in its current state.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    action = request.data.get('action')
    if action not in ('accepted', 'rejected'):
        return Response(
            {'error': 'Invalid action. Must be "accepted" or "rejected".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    proposal.status = action
    update_fields = ['status']

    if action == 'rejected':
        proposal.rejection_reason = request.data.get('reason', '')
        proposal.rejection_comment = request.data.get('comment', '')
        update_fields.extend(['rejection_reason', 'rejection_comment'])

    proposal.save(update_fields=update_fields)

    from content.services.proposal_email_service import ProposalEmailService
    ProposalEmailService.send_response_notification(proposal, action)

    if action == 'accepted':
        ProposalEmailService.send_acceptance_confirmation(proposal)
    elif action == 'rejected':
        ProposalEmailService.send_rejection_thank_you(proposal)

    return Response(
        {'status': action, 'message': f'Proposal {action} successfully.'},
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
