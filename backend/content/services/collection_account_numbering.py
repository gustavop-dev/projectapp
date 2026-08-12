"""
Per-client collection-account numbering: PA-{CODE}-{NNN}.

The per-client series is continuous (never resets by year) and coexists with
the legacy per-issuer DocumentNumberSequence (PA-{year}-{NNNN}), which is now
only used by records with no client linked yet. Codes are derived from the
client profile on first use and stay editable from the clients module.
"""
import re
import unicodedata

from django.db import transaction
from django.db.models import F

from accounts.models import UserProfile
from content.models import ClientDocumentNumberSequence, Document
from content.services.collection_account_service import CollectionAccountError
from content.services.document_type_codes import COLLECTION_ACCOUNT

CODE_MAX_LENGTH = 8


def _issuer_prefix(issuer):
    return (issuer.public_number_prefix or 'PA').strip() or 'PA'


def derive_billing_code(profile):
    """
    Short uppercase code from the client's legal name, falling back to the
    email local part. Never purely numeric (a numeric code would make
    PA-{CODE}-{NNN} collide with the legacy PA-{year}-{NNNN} pattern); falls
    back to C{pk}; suffixes on collision.

    The base is the legal holder rather than `company_name`, which operators
    use for the brand — deriving from it turned a client series into a
    project one (`PA-MIMITTOS-001` for a client named Daniel). This is only
    ever the SUGGESTED default: `billing_code` is stored on first use and
    stays editable in /panel/clients, so codes already issued never move.
    """
    from content.services.collection_account_create_service import (
        legal_name_for,
    )

    user = profile.user
    base = (
        legal_name_for(profile)
        or (user.email or '').split('@')[0]
    )
    normalized = unicodedata.normalize('NFKD', base)
    code = re.sub(r'[^A-Z0-9]', '', normalized.upper())[:CODE_MAX_LENGTH]
    if not code:
        code = f'C{profile.pk}'
    elif code.isdigit():
        code = f'C{code}'[:CODE_MAX_LENGTH]

    candidate = code
    suffix = 2
    while (
        UserProfile.objects.exclude(pk=profile.pk)
        .filter(billing_code=candidate)
        .exists()
    ):
        candidate = f'{code}{suffix}'
        suffix += 1
    return candidate


def ensure_billing_code(profile):
    """Return the profile's billing code, deriving and saving it once."""
    if profile.billing_code:
        return profile.billing_code
    profile.billing_code = derive_billing_code(profile)
    profile.save(update_fields=['billing_code'])
    return profile.billing_code


def peek_next_client_number(profile, issuer):
    """(code, suggested_number) without consuming the counter."""
    code = ensure_billing_code(profile)
    seq = getattr(profile, 'collection_number_sequence', None)
    next_value = (seq.last_value if seq else 0) + 1
    return code, f'{_issuer_prefix(issuer)}-{code}-{next_value:03d}'


@transaction.atomic
def allocate_client_number(profile, issuer, *, manual_number=None):
    """
    Thread-safe next per-client public_number, or a validated manual
    override. The sequence row lock serializes all issues for the client,
    manual overrides included.
    """
    code = ensure_billing_code(profile)
    seq, _ = ClientDocumentNumberSequence.objects.select_for_update().get_or_create(
        client_profile=profile,
        defaults={'last_value': 0},
    )
    prefix = _issuer_prefix(issuer)

    if manual_number:
        manual_number = manual_number.strip()
        collision = (
            Document.objects.filter(
                document_type__code=COLLECTION_ACCOUNT,
                public_number=manual_number,
            ).exists()
        )
        if collision:
            raise CollectionAccountError(
                f'El consecutivo {manual_number} ya está en uso.'
            )
        # Keep future auto suggestions ahead of manual numbers in this
        # client's own series so they can never re-collide.
        match = re.fullmatch(
            rf'{re.escape(prefix)}-{re.escape(code)}-(\d+)', manual_number,
        )
        if match and int(match.group(1)) > seq.last_value:
            ClientDocumentNumberSequence.objects.filter(pk=seq.pk).update(
                last_value=int(match.group(1)),
            )
        return manual_number

    ClientDocumentNumberSequence.objects.filter(pk=seq.pk).update(
        last_value=F('last_value') + 1,
    )
    seq.refresh_from_db()
    return f'{prefix}-{code}-{seq.last_value:03d}'
