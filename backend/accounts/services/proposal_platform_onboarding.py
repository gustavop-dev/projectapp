"""
When a BusinessProposal becomes accepted (client response or admin panel), provision
platform resources if needed, sync Kanban from technical_document, and send welcome email (via ProposalEmailService).
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Deliverable, Project, UserProfile
from accounts.services.technical_requirements_sync import (
    sync_technical_requirements_for_deliverable,
)

logger = logging.getLogger(__name__)

User = get_user_model()

Source = Literal['client_response', 'admin_panel']


def _acting_user_for_sync(acting_user):
    if acting_user is not None and getattr(acting_user, 'is_authenticated', False):
        return acting_user
    return User.objects.filter(is_staff=True, is_active=True).order_by('id').first()


def _find_client_user_by_email(email: str):
    if not (email or '').strip():
        return None
    return User.objects.filter(email__iexact=email.strip()).select_related('profile').first()


def ensure_deliverable_for_accepted_proposal(
    proposal,
    acting_user,
) -> Deliverable | None:
    """
    Return deliverable linked to proposal, creating project/deliverable if needed.
    """
    if proposal.deliverable_id:
        return proposal.deliverable

    email = (proposal.client_email or '').strip()
    user = _find_client_user_by_email(email)

    if not user and getattr(settings, 'AUTO_PROVISION_CLIENT_FROM_PROPOSAL', False) and email:
        from accounts.services.onboarding import create_client

        raw = (proposal.client_name or 'Cliente').strip()
        parts = raw.split(None, 1)
        first = parts[0] if parts else 'Cliente'
        last = parts[1] if len(parts) > 1 else ''
        try:
            user, _temp_pw = create_client(
                email=email,
                first_name=first[:150],
                last_name=last[:150],
                company_name='',
            )
        except ValueError:
            logger.warning('Could not auto-provision client for proposal %s (duplicate email).', proposal.pk)
            user = _find_client_user_by_email(email)

    if not user:
        logger.info(
            'Proposal %s accepted without platform deliverable: no client user for email %s',
            proposal.pk, email or '(empty)',
        )
        return None

    profile = getattr(user, 'profile', None)
    if not profile or profile.role != UserProfile.ROLE_CLIENT:
        logger.info('Proposal %s: user %s is not a platform client; skipping auto project.', proposal.pk, user.pk)
        return None

    from accounts.views import _extract_proposal_financial_data

    payment_milestones, hosting_tiers = _extract_proposal_financial_data(proposal)

    uploader = acting_user if acting_user and getattr(acting_user, 'is_authenticated', False) else user

    project = Project.objects.create(
        name=(proposal.title or 'Nuevo proyecto')[:200],
        description='',
        client=user,
        payment_milestones=payment_milestones,
        hosting_tiers=hosting_tiers,
    )
    d = Deliverable.objects.create(
        project=project,
        category=Deliverable.CATEGORY_DOCUMENTS,
        title=(proposal.title or 'Propuesta comercial')[:300],
        description='',
        file=None,
        uploaded_by=uploader,
    )
    proposal.deliverable = d
    proposal.save(update_fields=['deliverable_id'])
    return d


def handle_proposal_accepted_for_platform(
    proposal,
    *,
    source: Source = 'client_response',
    acting_user=None,
) -> dict[str, Any]:
    """
    Idempotent: skips if platform_onboarding_completed_at is set.
    Ensures deliverable (optional), runs technical sync, sends acceptance email with PDFs.
    """
    _ = source  # reserved for logging / future policy

    if proposal.platform_onboarding_completed_at:
        return {'skipped': True, 'reason': 'already_completed'}

    d = ensure_deliverable_for_accepted_proposal(proposal, acting_user)
    proposal.refresh_from_db(fields=['deliverable_id'])
    sync_result: dict[str, Any] = {'ok': True, 'detail': 'no_deliverable_skip_sync'}

    actor = _acting_user_for_sync(acting_user)
    if d and actor:
        sync_result = sync_technical_requirements_for_deliverable(d, actor)
        if not sync_result.get('ok'):
            logger.warning(
                'Technical sync after acceptance failed for proposal %s: %s',
                proposal.pk, sync_result.get('detail'),
            )

    from content.services.proposal_email_service import ProposalEmailService

    ProposalEmailService.send_acceptance_confirmation(proposal)

    proposal.platform_onboarding_completed_at = timezone.now()
    proposal.save(update_fields=['platform_onboarding_completed_at'])

    return {
        'skipped': False,
        'deliverable_id': d.id if d else None,
        'sync': sync_result,
    }
