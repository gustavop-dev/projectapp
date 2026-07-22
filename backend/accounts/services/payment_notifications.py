"""Team-facing email notifications for hosting payment outcomes.

Whenever a Payment transitions to PAID or FAILED, the team inbox
(``settings.TEAM_PAYMENTS_EMAIL``) receives a summary so payment status can be
tracked outside the in-app notifications. Best-effort: never raises.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

# Human-readable labels per payment status (keys are Payment.STATUS_* values).
_STATUS_LABELS = {
    'paid': 'Pago aprobado',
    'failed': 'Pago fallido',
    'overdue': 'Pago vencido',
    'pending': 'Pago pendiente',
    'processing': 'Pago en proceso',
}


def build_payment_status_context(payment, to_status, source=''):
    """Build the template context for a payment-status team email."""
    sub = payment.subscription
    project = sub.project
    client = getattr(project, 'client', None)
    client_name = ''
    client_email = ''
    if client is not None:
        client_name = (
            f'{client.first_name} {client.last_name}'.strip()
            or client.email
            or ''
        )
        client_email = client.email or ''

    return {
        'status_label': _STATUS_LABELS.get(to_status, to_status),
        'is_paid': to_status == 'paid',
        'is_failed': to_status == 'failed',
        'client_name': client_name,
        'client_email': client_email,
        'project_name': project.name,
        'project_id': project.id,
        'amount': payment.amount,
        'currency': 'COP',
        'billing_period_start': payment.billing_period_start,
        'billing_period_end': payment.billing_period_end,
        'due_date': payment.due_date,
        'transaction_id': payment.wompi_transaction_id or '',
        'source': source or '',
        'payment_id': payment.id,
        'last_charge_error': payment.last_charge_error or '',
    }


def send_payment_status_team_email(payment_id, to_status, source=''):
    """
    Render and send the team notification for a payment outcome.
    Returns True if the email was sent, False otherwise. Never raises.
    """
    from accounts.models import Payment

    recipient = getattr(settings, 'TEAM_PAYMENTS_EMAIL', '') or ''
    if not recipient:
        logger.warning('TEAM_PAYMENTS_EMAIL not configured; skipping payment email')
        return False

    try:
        payment = Payment.objects.select_related(
            'subscription__project__client',
        ).get(id=payment_id)
    except Payment.DoesNotExist:
        logger.warning('Payment %s not found for team status email', payment_id)
        return False

    from content.utils import format_cop_email

    context = build_payment_status_context(payment, to_status, source)
    subject = (
        f'{context["status_label"]} · {context["project_name"]} · '
        f'${format_cop_email(context["amount"])} COP'
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'team@projectapp.co')

    try:
        text_body = render_to_string('emails/payment_status_team.txt', context)
        html_body = render_to_string('emails/payment_status_team.html', context)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[recipient],
        )
        email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=False)
        logger.info(
            'Sent payment status email (%s) for payment %s to %s',
            to_status, payment_id, recipient,
        )
        return True
    except Exception as exc:
        logger.warning(
            'Failed to send payment status email for payment %s: %s',
            payment_id, exc,
        )
        return False
