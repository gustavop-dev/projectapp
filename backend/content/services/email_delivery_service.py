"""Single outbound gateway for every email emitted by ProjectApp.

Only this module may call Django's ``EmailMessage.send``. Every registered
message is delivered to its primary audience first and then copied through
independent BCC-only envelopes. The gateway also creates the baseline history
rows, so a future sender cannot accidentally bypass copying or traceability.
"""

from __future__ import annotations

import copy
import logging
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field

from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.utils import timezone

from content.services.client_email_inventory import CLIENT_EMAIL_CHANNELS
from content.services.outbound_email_inventory import outbound_email_family

logger = logging.getLogger(__name__)


class DeliveryClassification:
    CLIENT = 'client'
    INTERNAL = 'internal'
    SECURITY = 'security'

    VALUES = frozenset({CLIENT, INTERNAL, SECURITY})


@dataclass
class CopyAttempt:
    recipient: str
    status: str
    error_message: str = ''
    attempted_at: str = ''


@dataclass
class DeliveryTrace:
    delivery_id: uuid.UUID
    template_key: str
    classification: str
    family: str | None
    primary_recipients: tuple[str, ...]
    copy_attempts: list[CopyAttempt] = field(default_factory=list)
    copy_error_message: str = ''
    body: object | None = None
    remaining_log_writes: int = 1
    enrichment_count: int = 0
    gateway_primary_log_ids: list[int] = field(default_factory=list)
    gateway_copy_log_ids: list[int] = field(default_factory=list)


_CURRENT_DELIVERY = ContextVar('projectapp_current_email_delivery', default=None)


def _normalized_recipients(values):
    return tuple(sorted({
        (value or '').strip().lower() for value in values or () if value
    }))


def matching_delivery_trace(template_key, recipients):
    """The latest gateway trace when it belongs to this log write."""
    trace = _CURRENT_DELIVERY.get()
    if (
        trace is None
        or trace.remaining_log_writes < 1
        or trace.template_key != template_key
    ):
        return None
    if trace.primary_recipients != _normalized_recipients(recipients):
        return None
    return trace


def complete_delivery_log_write(trace):
    """Consume one expected primary log write from a gateway trace."""
    trace.remaining_log_writes = max(0, trace.remaining_log_writes - 1)
    if trace.remaining_log_writes == 0:
        _CURRENT_DELIVERY.set(None)


def _active_copy_recipients(family):
    from content.models import EmailCopyRecipient

    # Keep this portable across MySQL (production) and SQLite (focused local
    # tests), whose JSON containment operators differ. This configuration
    # table is deliberately tiny, so filtering its active rows in Python is
    # both predictable and cheaper than backend-specific SQL branches.
    return [
        recipient.email
        for recipient in EmailCopyRecipient.objects.filter(
            is_active=True,
        ).only('email', 'families').order_by('email')
        if family in (recipient.families or [])
    ]


def _message_bodies(message):
    """Return the plain and HTML bodies already rendered on the message."""
    text_body = str(getattr(message, 'body', '') or '')
    html_body = ''
    for alternative in getattr(message, 'alternatives', ()) or ():
        content = getattr(alternative, 'content', alternative[0])
        mimetype = getattr(alternative, 'mimetype', alternative[1])
        if mimetype == 'text/html':
            html_body = str(content or '')
            break
    return text_body, html_body


def _audience_for(classification):
    from content.models import EmailLog

    if classification == DeliveryClassification.CLIENT:
        return EmailLog.Audience.CLIENT
    if classification == DeliveryClassification.SECURITY:
        return EmailLog.Audience.SECURITY
    return EmailLog.Audience.INTERNAL


def _persist_gateway_history(
    trace,
    message,
    *,
    primary_status,
    primary_error='',
):
    """Persist a complete baseline trace without affecting delivery outcome."""
    from content.models import EmailBody, EmailLog

    try:
        text_body, html_body = _message_bodies(message)
        if text_body or html_body:
            trace.body = EmailBody.objects.create(
                text=text_body,
                html=html_body,
            )
        delivery_metadata = {
            'outbound_delivery': {
                'classification': trace.classification,
                'family': trace.family,
            },
        }
        if trace.copy_error_message:
            delivery_metadata['outbound_delivery']['copy_error'] = (
                trace.copy_error_message
            )
        audience = _audience_for(trace.classification)
        for recipient in trace.primary_recipients:
            log = EmailLog.objects.create(
                template_key=trace.template_key,
                recipient=recipient,
                subject=(getattr(message, 'subject', '') or '')[:500],
                status=primary_status,
                error_message=(primary_error or '')[:1000],
                metadata=delivery_metadata,
                body=trace.body,
                audience=audience,
                delivery_id=trace.delivery_id,
                delivery_role=EmailLog.DeliveryRole.PRIMARY,
            )
            trace.gateway_primary_log_ids.append(log.pk)

        for attempt in trace.copy_attempts:
            copy_metadata = {
                **delivery_metadata,
                'email_copy': {
                    'family': trace.family,
                    'primary_recipients': list(trace.primary_recipients),
                    'attempted_at': attempt.attempted_at,
                },
            }
            log = EmailLog.objects.create(
                template_key=trace.template_key,
                recipient=attempt.recipient,
                subject=(getattr(message, 'subject', '') or '')[:500],
                status=attempt.status,
                error_message=attempt.error_message,
                metadata=copy_metadata,
                body=trace.body,
                audience=EmailLog.Audience.INTERNAL,
                delivery_id=trace.delivery_id,
                delivery_role=EmailLog.DeliveryRole.COPY,
            )
            trace.gateway_copy_log_ids.append(log.pk)
    except Exception:
        # History is diagnostic. A database/logging failure after SMTP must
        # never reinterpret or retry a successful commercial send.
        logger.exception(
            'Could not persist outbound email history for %s.',
            trace.template_key,
        )


class EmailDeliveryGateway:
    """Execute one outbound email under an explicit delivery policy."""

    @classmethod
    def send(
        cls,
        message: EmailMessage,
        *,
        template_key: str,
        classification: str | None = None,
        fail_silently: bool = False,
        primary_log_writes: int = 1,
    ) -> int:
        family = outbound_email_family(template_key)
        if not family:
            raise ValueError(
                f'Outbound email template {template_key!r} is missing from the inventory.'
            )
        if classification is None:
            if template_key not in CLIENT_EMAIL_CHANNELS:
                raise ValueError(
                    f'Email policy required for non-client template {template_key!r}.'
                )
            classification = DeliveryClassification.CLIENT
        if classification not in DeliveryClassification.VALUES:
            raise ValueError(f'Unknown email classification: {classification!r}.')
        primary_recipients = _normalized_recipients(message.recipients())
        trace = DeliveryTrace(
            delivery_id=uuid.uuid4(),
            template_key=template_key,
            classification=classification,
            family=family,
            primary_recipients=primary_recipients,
            remaining_log_writes=max(1, int(primary_log_writes)),
        )
        _CURRENT_DELIVERY.set(trace)

        # Clone before the primary call: a backend is free to mutate the
        # message while preparing MIME, and attachments must remain identical.
        copy_source = copy.deepcopy(message)
        try:
            sent_count = message.send(fail_silently=fail_silently)
        except Exception as exc:
            _persist_gateway_history(
                trace,
                copy_source,
                primary_status='failed',
                primary_error=str(exc),
            )
            _CURRENT_DELIVERY.set(trace)
            raise

        if not sent_count:
            _persist_gateway_history(
                trace,
                copy_source,
                primary_status='failed',
                primary_error='El backend de correo no aceptó el envío.',
            )
            _CURRENT_DELIVERY.set(trace)
            return sent_count

        try:
            recipients = _active_copy_recipients(family)
        except Exception:
            # A missing table during a rolling deploy or a transient database
            # error must never turn a successful customer send into a failure.
            logger.exception(
                'Could not resolve email copy recipients for %s.',
                template_key,
            )
            trace.copy_error_message = (
                'No se pudo resolver la configuración de copias.'
            )
            recipients = []

        for recipient in recipients:
            normalized = (recipient or '').strip().lower()
            if not normalized:
                continue
            attempt = CopyAttempt(
                recipient=normalized,
                status='sent',
                attempted_at=timezone.now().isoformat(),
            )
            if normalized in primary_recipients:
                attempt.status = 'skipped'
                attempt.error_message = 'Ya era destinatario del envío principal.'
                trace.copy_attempts.append(attempt)
                continue
            copy_message = copy.deepcopy(copy_source)
            # BCC-only envelope: the internal address is absent from visible
            # headers and the client is not sent the same message twice.
            copy_message.to = []
            copy_message.cc = []
            copy_message.bcc = [normalized]
            try:
                copy_sent = copy_message.send(fail_silently=False)
                if not copy_sent:
                    attempt.status = 'failed'
                    attempt.error_message = (
                        'El backend de correo no aceptó la copia.'
                    )
            except Exception as exc:
                attempt.status = 'failed'
                attempt.error_message = str(exc)[:1000]
                logger.warning(
                    'Client email copy failed for %s to %s: %s',
                    template_key, normalized, exc,
                )
            trace.copy_attempts.append(attempt)

        _persist_gateway_history(
            trace,
            copy_source,
            primary_status='sent',
        )
        _CURRENT_DELIVERY.set(trace)
        return sent_count

    @classmethod
    def send_plain(
        cls,
        *,
        subject,
        body,
        from_email,
        recipients,
        template_key,
        classification,
        html_body=None,
        fail_silently=False,
    ):
        """Construct and deliver a text email, optionally with HTML."""
        message = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=from_email,
            to=list(recipients),
        )
        if html_body:
            message.attach_alternative(html_body, 'text/html')
        return cls.send(
            message,
            template_key=template_key,
            classification=classification,
            fail_silently=fail_silently,
        )
