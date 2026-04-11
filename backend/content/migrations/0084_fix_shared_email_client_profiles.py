"""
Fix client profiles that were incorrectly merged during the 0080 backfill.

The original backfill matched proposals to UserProfiles by email only.
When different real-world clients shared the same email address (e.g. the
admin reused their own email, or a generic email like client@example.com),
all their proposals ended up under a single profile.

This migration splits each contaminated profile so every unique
``client_name`` gets its own UserProfile.  The original profile keeps the
proposals whose ``client_name`` matches the profile's current
``User.first_name + last_name``; all other names get a new placeholder
profile.
"""

import logging
import secrets
from collections import defaultdict

from django.contrib.auth.hashers import make_password
from django.db import migrations

logger = logging.getLogger(__name__)

PLACEHOLDER_DOMAIN = 'temp.example.com'
ROLE_CLIENT = 'client'


def _split_name(full_name):
    parts = (full_name or '').strip().split(maxsplit=1)
    first = parts[0] if parts else ''
    last = parts[1] if len(parts) > 1 else ''
    return first[:150], last[:150]


def _create_placeholder_profile(User, UserProfile, *, name, phone):
    """Create a fresh placeholder User + UserProfile for *name*."""
    first_name, last_name = _split_name(name)

    temp_token = secrets.token_hex(8)
    temp_username = f'pending_{temp_token}'
    temp_email = f'{temp_username}@{PLACEHOLDER_DOMAIN}'

    user = User(
        username=temp_username[:150],
        email=temp_email[:254],
        first_name=first_name,
        last_name=last_name,
        is_active=False,
    )
    user.password = make_password(None)
    user.save()

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


def forwards(apps, schema_editor):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    User = apps.get_model('auth', 'User')

    profiles = UserProfile.objects.filter(role=ROLE_CLIENT)
    fixed = 0

    for profile in profiles:
        proposals = BusinessProposal.objects.filter(client=profile)
        if not proposals.exists():
            continue

        # Group proposals by their snapshot client_name.
        by_name = defaultdict(list)
        for prop in proposals:
            by_name[(prop.client_name or '').strip()].append(prop)

        if len(by_name) <= 1:
            # Single client name — nothing to split.
            continue

        # Determine which name the existing profile should keep.
        # Prefer the name that matches the profile's current user name.
        current_name = f'{profile.user.first_name} {profile.user.last_name}'.strip()
        keeper_name = None
        if current_name in by_name:
            keeper_name = current_name

        if keeper_name is None:
            # Fall back to the name with the most proposals.
            keeper_name = max(by_name, key=lambda n: len(by_name[n]))

        logger.info(
            'fix_shared_email: profile %s (%s) — keeping "%s", splitting out %s other name(s)',
            profile.pk, profile.user.email, keeper_name,
            len(by_name) - 1,
        )

        for name, props in by_name.items():
            if name == keeper_name:
                continue

            # Create a new placeholder profile for this client name.
            phone = props[0].client_phone or ''
            new_profile = _create_placeholder_profile(
                User, UserProfile, name=name, phone=phone,
            )

            prop_ids = [p.pk for p in props]
            BusinessProposal.objects.filter(pk__in=prop_ids).update(
                client_id=new_profile.pk,
            )
            fixed += len(prop_ids)

            logger.info(
                '  -> "%s": created profile %s, reassigned proposals %s',
                name, new_profile.pk, prop_ids,
            )

    logger.info('fix_shared_email done — reassigned %s proposals', fixed)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0083_add_stage_change_types'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop),
    ]
