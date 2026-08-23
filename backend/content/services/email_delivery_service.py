"""Single outbound gateway for every email emitted by ProjectApp.

Only this module is allowed to call Django's ``EmailMessage.send``. Client
messages are delivered first. After a successful primary delivery, each
configured internal recipient receives a separate BCC-only envelope with the
same subject, bodies and attachments. Copy errors are captured for history
and never change or retry the primary delivery.
"""

from __future__ import annotations

import copy
import logging
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field

from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.utils import timezone

from content.services.client_email_inventory import client_email_family

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
    copies_recorded: bool = False
    body: object | None = None
    remaining_log_writes: int = 1


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
    from content.models import ClientEmailCopyRecipient

    # Keep this portable across MySQL (production) and SQLite (focused local
    # tests), whose JSON containment operators differ. This configuration
    # table is deliberately tiny, so filtering its active rows in Python is
    # both predictable and cheaper than backend-specific SQL branches.
    return [
        recipient.email
        for recipient in ClientEmailCopyRecipient.objects.filter(
            is_active=True,
        ).only('email', 'families').order_by('email')
        if family in (recipient.families or [])
    ]


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
        family = client_email_family(template_key)
        if classification is None:
            if not family:
                raise ValueError(
                    f'Email policy required for unregistered template {template_key!r}.'
                )
            classification = DeliveryClassification.CLIENT
        if classification not in DeliveryClassification.VALUES:
            raise ValueError(f'Unknown email classification: {classification!r}.')
        if classification == DeliveryClassification.CLIENT and not family:
            raise ValueError(
                f'Client email template {template_key!r} is missing from the inventory.'
            )

        primary_recipients = _normalized_recipients(message.recipients())
        trace = DeliveryTrace(
            delivery_id=uuid.uuid4(),
            template_key=template_key,
            classification=classification,
            family=family if classification == DeliveryClassification.CLIENT else None,
            primary_recipients=primary_recipients,
            remaining_log_writes=max(1, int(primary_log_writes)),
        )
        _CURRENT_DELIVERY.set(trace)

        # Clone before the primary call: a backend is free to mutate the
        # message while preparing MIME, and attachments must remain identical.
        copy_source = copy.deepcopy(message)
        try:
            sent_count = message.send(fail_silently=fail_silently)
        except Exception:
            _CURRENT_DELIVERY.set(
                trace if classification == DeliveryClassification.CLIENT else None,
            )
            raise

        if (
            not sent_count
            or classification != DeliveryClassification.CLIENT
        ):
            _CURRENT_DELIVERY.set(
                trace if classification == DeliveryClassification.CLIENT else None,
            )
            return sent_count

        try:
            recipients = _active_copy_recipients(family)
        except Exception:
            # A missing table during a rolling deploy or a transient database
            # error must never turn a successful customer send into a failure.
            logger.exception(
                'Could not resolve client email copy recipients for %s.',
                template_key,
            )
            recipients = []

        for recipient in recipients:
            normalized = (recipient or '').strip().lower()
            if not normalized or normalized in primary_recipients:
                continue
            attempt = CopyAttempt(
                recipient=normalized,
                status='sent',
                attempted_at=timezone.now().isoformat(),
            )
            copy_message = copy.deepcopy(copy_source)
            # BCC-only envelope: the internal address is absent from visible
            # headers and the client is not sent the same message twice.
            copy_message.to = []
            copy_message.cc = []
            copy_message.bcc = [normalized]
            try:
                copy_message.send(fail_silently=False)
            except Exception as exc:
                attempt.status = 'failed'
                attempt.error_message = str(exc)[:1000]
                logger.warning(
                    'Client email copy failed for %s to %s: %s',
                    template_key, normalized, exc,
                )
            trace.copy_attempts.append(attempt)

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
