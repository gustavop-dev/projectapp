"""Shared validation and client attribution for manual email recipients."""

from __future__ import annotations

import json
from dataclasses import dataclass

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db.models.functions import Lower

from accounts.models import UserProfile


MAX_MANUAL_RECIPIENTS = 10


@dataclass(frozen=True)
class EmailRecipientValidationError(ValueError):
    message: str
    code: str
    field: str = ''

    def __str__(self):
        return self.message


def _raw_list(value, *, field):
    if value is None or value == '':
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith('['):
            try:
                value = json.loads(stripped)
            except (json.JSONDecodeError, TypeError) as exc:
                raise EmailRecipientValidationError(
                    'La lista de destinatarios no es un JSON válido.',
                    'invalid_recipient_list',
                    field,
                ) from exc
        else:
            value = [stripped]
    if not isinstance(value, (list, tuple)):
        raise EmailRecipientValidationError(
            'Los destinatarios deben enviarse como una lista.',
            'invalid_recipient_list',
            field,
        )
    return list(value)


def _normalize_list(values, *, field, label):
    normalized = []
    seen = set()
    for raw_value in values:
        if not isinstance(raw_value, str):
            raise EmailRecipientValidationError(
                f'Cada dirección de {label} debe ser un correo válido.',
                'invalid_recipient_email',
                field,
            )
        email = raw_value.strip().lower()
        if len(email) > 254:
            raise EmailRecipientValidationError(
                f'El correo "{raw_value}" no es válido.',
                'invalid_recipient_email',
                field,
            )
        try:
            validate_email(email)
        except DjangoValidationError as exc:
            raise EmailRecipientValidationError(
                f'El correo del destinatario "{raw_value}" no es válido.',
                'invalid_recipient_email',
                field,
            ) from exc
        if email.endswith(UserProfile.PLACEHOLDER_EMAIL_DOMAIN):
            raise EmailRecipientValidationError(
                'Los correos temporales de clientes no pueden recibir mensajes.',
                'placeholder_recipient_email',
                field,
            )
        if email in seen:
            raise EmailRecipientValidationError(
                f'El correo {email} está repetido en {label}.',
                'duplicate_recipient_email',
                field,
            )
        seen.add(email)
        normalized.append(email)
    return normalized


def parse_email_recipients(
    data,
    *,
    legacy_to_fields=('recipient_email',),
):
    """Return validated ``(to, cc)`` lists from JSON or multipart data."""
    raw_to = data.get('recipient_emails')
    if raw_to in (None, ''):
        for legacy_field in legacy_to_fields:
            raw_to = data.get(legacy_field)
            if raw_to not in (None, ''):
                break
    raw_cc = data.get('cc_emails')

    to_recipients = _normalize_list(
        _raw_list(raw_to, field='recipient_emails'),
        field='recipient_emails',
        label='Para',
    )
    cc_recipients = _normalize_list(
        _raw_list(raw_cc, field='cc_emails'),
        field='cc_emails',
        label='CC',
    )
    if not to_recipients:
        raise EmailRecipientValidationError(
            'Agrega al menos un destinatario en Para.',
            'recipient_required',
            'recipient_emails',
        )

    overlap = set(to_recipients) & set(cc_recipients)
    if overlap:
        duplicate = sorted(overlap)[0]
        raise EmailRecipientValidationError(
            f'El correo {duplicate} no puede estar en Para y CC al mismo tiempo.',
            'duplicate_recipient_email',
            'cc_emails',
        )
    if len(to_recipients) + len(cc_recipients) > MAX_MANUAL_RECIPIENTS:
        raise EmailRecipientValidationError(
            f'Puedes agregar máximo {MAX_MANUAL_RECIPIENTS} destinatarios entre Para y CC.',
            'recipient_limit_exceeded',
        )
    return to_recipients, cc_recipients


def recipient_log_contexts(to_recipients, cc_recipients, *, contextual_client=None):
    """Build one per-address log context, resolving registered clients in bulk."""
    from content.models import EmailLog

    addresses = list(to_recipients) + list(cc_recipients)
    profiles = (
        UserProfile.objects.clients()
        .select_related('user')
        .annotate(_recipient_email=Lower('user__email'))
        .filter(_recipient_email__in=addresses)
    )
    profiles_by_email = {
        (profile.user.email or '').strip().lower(): profile
        for profile in profiles
    }
    if contextual_client is not None:
        contextual_email = (
            getattr(getattr(contextual_client, 'user', None), 'email', '') or ''
        ).strip().lower()
        if contextual_email:
            profiles_by_email.setdefault(contextual_email, contextual_client)

    contexts = []
    for kind, recipients in (
        (EmailLog.RecipientKind.TO, to_recipients),
        (EmailLog.RecipientKind.CC, cc_recipients),
    ):
        for email in recipients:
            profile = profiles_by_email.get(email)
            contexts.append({
                'email': email,
                'recipient_kind': kind,
                'client_id': profile.pk if profile else None,
                'audience': (
                    EmailLog.Audience.CLIENT
                    if profile else EmailLog.Audience.INTERNAL
                ),
            })
    return contexts
