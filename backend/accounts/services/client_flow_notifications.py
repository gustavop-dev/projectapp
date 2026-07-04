"""Team-facing notifications for client portal milestones.

Fires when a client reaches a milestone in the document portal flow:
first platform login, email validation, and document signing. Each event
creates in-app notifications for project admins and emails the team inbox
(``settings.NOTIFICATION_EMAIL``). Best-effort: never raises.
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from accounts.models import Notification
from accounts.services.notifications import notify_project_admins

logger = logging.getLogger(__name__)

User = get_user_model()

EVENT_FIRST_LOGIN = 'first_login'
EVENT_EMAIL_VALIDATED = 'email_validated'
EVENT_DOCUMENT_SIGNED = 'document_signed'

_EVENT_LABELS = {
    EVENT_FIRST_LOGIN: 'Primer ingreso a la plataforma',
    EVENT_EMAIL_VALIDATED: 'Correo validado',
    EVENT_DOCUMENT_SIGNED: 'Documento firmado',
}


def _client_display_name(user):
    full = f'{user.first_name} {user.last_name}'.strip()
    return full or user.email or 'Cliente'


def _first_project(user):
    """Return the client's most recent project, or None."""
    manager = getattr(user, 'projects', None)
    if manager is None:
        return None
    return manager.order_by('-id').first()


def _team_recipients():
    from content.services.proposal_email_service import ProposalEmailService

    return ProposalEmailService._get_notification_recipients()


def _send_team_email(event, user, project=None, document=None):
    """Render and send the team milestone email. Never raises."""
    recipients = _team_recipients()
    if not recipients:
        logger.warning('No team recipients configured; skipping client-flow email')
        return False

    label = _EVENT_LABELS.get(event, event)
    client_name = _client_display_name(user)
    context = {
        'event_label': label,
        'client_name': client_name,
        'client_email': user.email or '',
        'project_name': getattr(project, 'name', '') or '',
        'project_id': getattr(project, 'id', None),
        'document_title': getattr(document, 'title', '') or '',
        'signed_at': getattr(document, 'signed_at', None),
    }
    subject = f'{label} · {client_name} · ProjectApp'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'team@projectapp.co')

    try:
        text_body = render_to_string('emails/client_activity_team.txt', context)
        html_body = render_to_string('emails/client_activity_team.html', context)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=recipients,
        )
        email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=False)
        logger.info('Sent client-flow email (%s) for user %s', event, user.id)
        return True
    except Exception as exc:
        logger.warning('Failed to send client-flow email (%s): %s', event, exc)
        return False


def _notify_admins(event, user, project=None, document=None):
    """Create in-app notifications for project admins. Never raises."""
    if project is None:
        return
    label = _EVENT_LABELS.get(event, event)
    client_name = _client_display_name(user)
    if event == EVENT_DOCUMENT_SIGNED and document is not None:
        message = f'{client_name} firmó "{document.title}" en {project.name}.'
    else:
        message = f'{client_name} · {label} en {project.name}.'
    try:
        notify_project_admins(
            project=project,
            type=Notification.TYPE_GENERAL,
            title=label,
            message=message,
            related_object_type='document' if document is not None else 'project',
            related_object_id=getattr(document, 'id', None) or project.id,
        )
    except Exception as exc:
        logger.warning('Failed to create in-app client-flow notification (%s): %s', event, exc)


def send_client_first_login_notification(user_id):
    """Notify the team that a client completed their first platform login."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning('User %s not found for first-login notification', user_id)
        return False
    project = _first_project(user)
    _notify_admins(EVENT_FIRST_LOGIN, user, project=project)
    return _send_team_email(EVENT_FIRST_LOGIN, user, project=project)


def send_client_email_validated_notification(user_id):
    """Notify the team that a client validated their email address."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning('User %s not found for email-validated notification', user_id)
        return False
    project = _first_project(user)
    _notify_admins(EVENT_EMAIL_VALIDATED, user, project=project)
    return _send_team_email(EVENT_EMAIL_VALIDATED, user, project=project)


def _send_client_signed_confirmation(user, document):
    """Email the client a confirmation that their signature was recorded. Never raises."""
    if not user.email:
        return False
    context = {
        'client_name': _client_display_name(user),
        'document_title': document.title,
        'signed_at': document.signed_at,
    }
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'team@projectapp.co')
    try:
        text_body = render_to_string('emails/document_signed_client.txt', context)
        html_body = render_to_string('emails/document_signed_client.html', context)
        email = EmailMultiAlternatives(
            subject=f'Firma registrada · {document.title} · ProjectApp',
            body=text_body,
            from_email=from_email,
            to=[user.email],
        )
        email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=False)
        return True
    except Exception as exc:
        logger.warning('Failed to send client signed confirmation for doc %s: %s', document.id, exc)
        return False


def send_document_signed_notification(document_id):
    """Notify the team (and confirm to the client) that a document was signed."""
    from content.models import Document

    try:
        document = Document.objects.select_related('project', 'client_user', 'signed_by').get(
            id=document_id,
        )
    except Document.DoesNotExist:
        logger.warning('Document %s not found for signed notification', document_id)
        return False
    user = document.signed_by or document.client_user
    if user is None:
        logger.warning('Document %s has no signer for notification', document_id)
        return False
    project = document.project or _first_project(user)
    _notify_admins(EVENT_DOCUMENT_SIGNED, user, project=project, document=document)
    _send_client_signed_confirmation(user, document)
    return _send_team_email(EVENT_DOCUMENT_SIGNED, user, project=project, document=document)
