"""
Backfill BusinessProposal.client by creating/linking accounts.UserProfile rows
from the legacy denormalized client_name/client_email/client_phone fields.

Strategy
--------
- For each proposal without a `client` FK, normalize the email to lowercase.
- Look up an existing User by email (case-insensitive) or by username.
- If found:
    * If they have a UserProfile with role='client'  -> reuse.
    * If they have a UserProfile with role='admin'   -> do NOT hijack the
      admin account; fall through to creating a placeholder client.
    * If they have no UserProfile at all             -> create one (role=client).
- If not found, create a new User + UserProfile from the proposal's data.
- If the proposal has no email at all, generate a placeholder via two-step save:
    1. Create the user with a temporary unique email/username.
    2. After save, rewrite to `cliente_<profile.id>@temp.example.com`
       (matching the format used at runtime by ProposalClientService).
- Idempotent: re-running skips proposals that already have a client FK.
"""

import logging
import secrets

from django.contrib.auth.hashers import make_password
from django.db import migrations

logger = logging.getLogger(__name__)

PLACEHOLDER_DOMAIN = 'temp.example.com'
ROLE_CLIENT = 'client'
ROLE_ADMIN = 'admin'


def _split_name(full_name):
    """Split a free-form full name into (first, last). Both capped at 150 chars."""
    parts = (full_name or '').strip().split(maxsplit=1)
    first = parts[0] if parts else ''
    last = parts[1] if len(parts) > 1 else ''
    return first[:150], last[:150]


def _create_user(User, *, username, email, first_name, last_name):
    """Create an inactive User with an unusable password (historical model safe)."""
    user = User(
        username=username[:150],
        email=email[:254],
        first_name=first_name,
        last_name=last_name,
        is_active=False,
    )
    user.password = make_password(None)  # produces an unusable hash starting with '!'
    user.save()
    return user


def _generate_placeholder_user(User, UserProfile, *, name, phone):
    """
    Two-step placeholder creation:
    1. Create user with a temp token-based email so the unique constraint passes.
    2. Create the profile so we have an id.
    3. Rewrite the user's email/username to use that profile id.
    """
    first_name, last_name = _split_name(name)

    temp_token = secrets.token_hex(8)
    temp_username = f'pending_{temp_token}'
    temp_email = f'{temp_username}@{PLACEHOLDER_DOMAIN}'

    user = _create_user(
        User,
        username=temp_username,
        email=temp_email,
        first_name=first_name,
        last_name=last_name,
    )

    profile = UserProfile.objects.create(
        user=user,
        role=ROLE_CLIENT,
        is_onboarded=False,
        phone=(phone or '')[:30],
    )

    final_username = f'cliente_{profile.pk}'
    final_email = f'{final_username}@{PLACEHOLDER_DOMAIN}'
    user.username = final_username
    user.email = final_email
    user.save(update_fields=['username', 'email'])

    return profile


def _resolve_existing_user(User, normalized_email):
    """Find a user by email (case-insensitive) or username."""
    user = User.objects.filter(email__iexact=normalized_email).first()
    if user is not None:
        return user
    return User.objects.filter(username__iexact=normalized_email).first()


def forwards(apps, schema_editor):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    User = apps.get_model('auth', 'User')

    cache = {}  # normalized_email -> UserProfile.pk
    proposals = BusinessProposal.objects.filter(client__isnull=True).order_by('created_at')

    created_real = 0
    created_placeholder = 0
    reused_existing = 0

    for proposal in proposals.iterator():
        normalized = (proposal.client_email or '').strip().lower()
        profile = None

        # Try cache first (for emails seen earlier in this run).
        if normalized and normalized in cache:
            profile = UserProfile.objects.filter(pk=cache[normalized]).first()
            if profile is not None:
                reused_existing += 1

        # Try DB lookup by email.
        if profile is None and normalized:
            existing_user = _resolve_existing_user(User, normalized)
            if existing_user is not None:
                existing_profile = UserProfile.objects.filter(user=existing_user).first()
                if existing_profile is None:
                    # User row exists but has no profile yet — create one as client.
                    profile = UserProfile.objects.create(
                        user=existing_user,
                        role=ROLE_CLIENT,
                        is_onboarded=False,
                        phone=(proposal.client_phone or '')[:30],
                    )
                    created_real += 1
                elif existing_profile.role == ROLE_CLIENT:
                    profile = existing_profile
                    reused_existing += 1
                else:
                    # Admin (or any non-client) — do NOT hijack the account.
                    logger.warning(
                        'backfill_proposal_clients: skipping reuse of non-client user '
                        '(id=%s email=%s role=%s) for proposal id=%s; generating placeholder.',
                        existing_user.pk, normalized, existing_profile.role, proposal.pk,
                    )
                    profile = None

            if profile is None:
                # No matching user — create a fresh User + profile from the email.
                first_name, last_name = _split_name(proposal.client_name)
                user = _create_user(
                    User,
                    username=normalized,
                    email=normalized,
                    first_name=first_name,
                    last_name=last_name,
                )
                profile = UserProfile.objects.create(
                    user=user,
                    role=ROLE_CLIENT,
                    is_onboarded=False,
                    phone=(proposal.client_phone or '')[:30],
                )
                created_real += 1

            cache[normalized] = profile.pk

        # Empty email or admin collision — placeholder.
        if profile is None:
            profile = _generate_placeholder_user(
                User,
                UserProfile,
                name=proposal.client_name,
                phone=proposal.client_phone,
            )
            created_placeholder += 1

        BusinessProposal.objects.filter(pk=proposal.pk).update(client_id=profile.pk)

    logger.info(
        'backfill_proposal_clients done — created_real=%s created_placeholder=%s reused=%s',
        created_real, created_placeholder, reused_existing,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0079_add_business_proposal_client_fk'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop),
    ]
