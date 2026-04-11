"""
Proposal-time client lifecycle for ``UserProfile`` (role=client).

This module is the silent counterpart to ``accounts.services.onboarding`` —
it creates / reuses / updates / deletes ``UserProfile`` rows for the
proposal admin panel WITHOUT sending invitation emails.

Key invariants
--------------
- Every ``BusinessProposal.client`` points to a ``UserProfile`` with
  ``role=ROLE_CLIENT``. Admin accounts are never reused.
- ``BusinessProposal`` keeps the legacy ``client_name`` / ``client_email`` /
  ``client_phone`` columns as **write-through snapshots** synced via
  ``sync_snapshot``. Reads should still work even if Profile is later edited.
- Empty client emails get a placeholder ``cliente_<id>@temp.example.com``,
  generated via a 2-step save so the id is part of the address. The
  ``UserProfile.is_email_placeholder`` property is the runtime check used by
  email automations to skip sending.
- Deleting a client requires it to be a true orphan: zero proposals AND
  zero platform projects. The ``BusinessProposal.client`` FK uses
  ``on_delete=PROTECT`` as a database-level safety net.
"""

import logging
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q

from accounts.models import UserProfile

logger = logging.getLogger(__name__)

User = get_user_model()


def generate_placeholder_email(profile_id):
    """Return the canonical placeholder email for a given profile id."""
    return f'cliente_{profile_id}{UserProfile.PLACEHOLDER_EMAIL_DOMAIN}'


def _split_name(full_name):
    """Split a free-form full name into (first, last). Both capped at 150 chars."""
    parts = (full_name or '').strip().split(maxsplit=1)
    first = parts[0] if parts else ''
    last = parts[1] if len(parts) > 1 else ''
    return first[:150], last[:150]


def build_client_display_name(profile):
    """Best-effort full name for a client profile (falls back to email/company)."""
    user = profile.user
    full = user.get_full_name().strip()
    if full:
        return full
    if profile.company_name:
        return profile.company_name
    return user.email or 'Cliente'


def _create_user_shell(*, username, email, first_name, last_name):
    """Create an inactive ``User`` with an unusable password."""
    user = User(
        username=username[:150],
        email=email[:254],
        first_name=first_name,
        last_name=last_name,
        is_active=False,
    )
    user.password = make_password(None)
    user.save()
    return user


def _resolve_existing_user(normalized_email):
    """Find a user by case-insensitive email match, then by username fallback."""
    user = User.objects.filter(email__iexact=normalized_email).first()
    if user is not None:
        return user
    return User.objects.filter(username__iexact=normalized_email).first()


@transaction.atomic
def get_or_create_client_for_proposal(*, name='', email='', phone='', company=''):
    """
    Get-or-create a ``UserProfile`` (role=client) used as the FK target of a
    ``BusinessProposal``. Never sends invitation emails.

    Resolution order:
    1. If ``email`` is non-empty:
        a. Match an existing ``User`` (case-insensitive on ``email`` then
           ``username``). Reuse the linked client profile, or create one if
           the user has none yet.
        b. If the matched user is an admin, log a warning and fall through
           to placeholder creation (admin accounts are never hijacked).
        c. Otherwise create a fresh ``User`` + ``UserProfile``.
    2. If ``email`` is empty, create a placeholder profile via 2-step save.

    Returns the resolved ``UserProfile`` instance.
    """
    normalized = (email or '').strip().lower()
    first_name, last_name = _split_name(name)
    company = (company or '').strip()
    phone = (phone or '').strip()[:30]

    if normalized:
        existing_user = _resolve_existing_user(normalized)
        if existing_user is not None:
            existing_profile = UserProfile.objects.filter(user=existing_user).first()
            if existing_profile is None:
                # Bare User with no profile — adopt as client.
                profile = UserProfile.objects.create(
                    user=existing_user,
                    role=UserProfile.ROLE_CLIENT,
                    is_onboarded=False,
                    company_name=company,
                    phone=phone,
                )
                _maybe_fill_user_names(existing_user, first_name, last_name)
                return profile
            if existing_profile.role == UserProfile.ROLE_CLIENT:
                # Reuse — opportunistically fill missing fields.
                _fill_missing_fields(existing_profile, company=company, phone=phone)
                _maybe_fill_user_names(existing_user, first_name, last_name)
                return existing_profile
            logger.warning(
                'proposal_client_service: refusing to reuse non-client user '
                '(id=%s email=%s role=%s); generating placeholder.',
                existing_user.pk, normalized, existing_profile.role,
            )
            # Fall through to placeholder.
        else:
            # No matching user — create a fresh shell + profile from this email.
            user = _create_user_shell(
                username=normalized,
                email=normalized,
                first_name=first_name,
                last_name=last_name,
            )
            profile = UserProfile.objects.create(
                user=user,
                role=UserProfile.ROLE_CLIENT,
                is_onboarded=False,
                company_name=company,
                phone=phone,
            )
            return profile

    # Empty email or admin collision → placeholder.
    return _create_placeholder_profile(
        first_name=first_name,
        last_name=last_name,
        company=company,
        phone=phone,
    )


def _create_placeholder_profile(*, first_name, last_name, company, phone):
    """Two-step save to embed the new profile id in the placeholder email."""
    temp_token = secrets.token_hex(8)
    temp_username = f'pending_{temp_token}'
    temp_email = f'{temp_username}{UserProfile.PLACEHOLDER_EMAIL_DOMAIN}'

    user = _create_user_shell(
        username=temp_username,
        email=temp_email,
        first_name=first_name,
        last_name=last_name,
    )
    profile = UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        is_onboarded=False,
        company_name=company,
        phone=phone,
    )

    final_username = f'cliente_{profile.pk}'
    final_email = generate_placeholder_email(profile.pk)
    user.username = final_username
    user.email = final_email
    user.save(update_fields=['username', 'email'])
    return profile


def _fill_missing_fields(profile, *, company, phone):
    """Fill empty profile fields without overwriting existing data."""
    dirty = []
    if company and not profile.company_name:
        profile.company_name = company
        dirty.append('company_name')
    if phone and not profile.phone:
        profile.phone = phone
        dirty.append('phone')
    if dirty:
        dirty.append('updated_at')
        profile.save(update_fields=dirty)


def _maybe_fill_user_names(user, first_name, last_name):
    """Fill empty first/last name on the User without overwriting existing values."""
    dirty = []
    if first_name and not user.first_name:
        user.first_name = first_name
        dirty.append('first_name')
    if last_name and not user.last_name:
        user.last_name = last_name
        dirty.append('last_name')
    if dirty:
        user.save(update_fields=dirty)


@transaction.atomic
def update_client_profile(profile, *, name=None, email=None, phone=None, company=None):
    """
    Update the canonical client identity (User + UserProfile) and cascade
    the new values to all linked proposals' snapshots.

    Any argument left as ``None`` is preserved. Pass an empty string to
    explicitly clear a field.
    """
    user = profile.user
    user_dirty = []
    profile_dirty = []

    if name is not None:
        first_name, last_name = _split_name(name)
        if user.first_name != first_name:
            user.first_name = first_name
            user_dirty.append('first_name')
        if user.last_name != last_name:
            user.last_name = last_name
            user_dirty.append('last_name')

    if email is not None:
        normalized = email.strip().lower()
        if normalized and normalized != (user.email or '').lower():
            # Guard against hijacking another existing user.
            collision = (
                User.objects
                .filter(Q(email__iexact=normalized) | Q(username__iexact=normalized))
                .exclude(pk=user.pk)
                .first()
            )
            if collision is not None:
                raise ValueError(
                    f'Otro usuario ya está usando el email {normalized}.'
                )
            user.email = normalized
            user.username = normalized[:150]
            user_dirty.extend(['email', 'username'])
        elif not normalized and user.email and not (user.email or '').endswith(UserProfile.PLACEHOLDER_EMAIL_DOMAIN):
            # Caller explicitly cleared the email — fall back to placeholder.
            user.email = generate_placeholder_email(profile.pk)
            user.username = f'cliente_{profile.pk}'
            user_dirty.extend(['email', 'username'])

    if phone is not None:
        if profile.phone != phone[:30]:
            profile.phone = phone[:30]
            profile_dirty.append('phone')

    if company is not None:
        if profile.company_name != company:
            profile.company_name = company
            profile_dirty.append('company_name')

    if user_dirty:
        user.save(update_fields=user_dirty)
    if profile_dirty:
        profile_dirty.append('updated_at')
        profile.save(update_fields=profile_dirty)

    # Cascade snapshots to all linked proposals (raw bulk update — no signals).
    # Bump updated_at by hand because .update() bypasses auto_now.
    if user_dirty or profile_dirty:
        from django.utils import timezone

        from content.models import BusinessProposal

        BusinessProposal.objects.filter(client=profile).update(
            client_name=build_client_display_name(profile),
            client_email=user.email,
            client_phone=profile.phone,
            updated_at=timezone.now(),
        )

    return profile


def sync_snapshot(proposal):
    """
    Mirror the canonical client identity onto the legacy snapshot fields of
    a single proposal. Called from serializers right after assigning
    ``proposal.client``. Saves the proposal in-place.
    """
    profile = proposal.client
    if profile is None:
        return proposal
    user = profile.user
    proposal.client_name = build_client_display_name(profile)
    proposal.client_email = user.email or ''
    proposal.client_phone = profile.phone or ''
    proposal.save(update_fields=['client_name', 'client_email', 'client_phone'])
    return proposal


@transaction.atomic
def delete_orphan_client(profile):
    """
    Delete a client profile (and its underlying ``User``) **only** if it has
    no proposals and no platform projects. Raises ``ValueError`` with a
    machine-readable code otherwise.

    Error codes:
        - ``client_has_proposals``: linked to one or more BusinessProposals.
        - ``client_has_projects``: linked to one or more platform Projects
          (which transitively cover deliverables, requirements, etc.).
    """
    proposals_count = profile.proposals.count()
    if proposals_count > 0:
        raise ValueError(f'client_has_proposals:{proposals_count}')

    projects_count = profile.user.projects.count()
    if projects_count > 0:
        raise ValueError(f'client_has_projects:{projects_count}')

    user = profile.user
    profile.delete()
    user.delete()
