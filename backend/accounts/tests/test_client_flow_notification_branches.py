"""Branch coverage for accounts.services.client_flow_notifications.

Complements test_client_first_login_notification.py and
test_client_documents.py with the defensive branches: missing recipients,
email failures swallowed, unknown users/documents and signer-less docs.
"""
from unittest.mock import patch

import pytest
from django.core.mail import EmailMultiAlternatives

from accounts.services import client_flow_notifications as flow
from content.models import Document

pytestmark = pytest.mark.django_db


def _make_document(client_user, project=None, **overrides):
    defaults = {
        'title': 'Contrato',
        'status': Document.Status.PUBLISHED,
        'client_user': client_user,
        'project': project,
        'requires_signature': True,
        'content_json': {'blocks': [{'type': 'paragraph', 'text': 'Hola'}]},
    }
    defaults.update(overrides)
    return Document.objects.create(**defaults)


def test_first_project_is_none_for_objects_without_projects():
    assert flow._first_project(object()) is None


@patch.object(flow, '_team_recipients', return_value=[])
def test_team_email_skipped_without_recipients(
    _mock_recipients, client_user, mailoutbox,  # noqa: PT019
):
    result = flow.send_client_first_login_notification(client_user.id)
    assert result is False
    assert len(mailoutbox) == 0


@patch.object(EmailMultiAlternatives, 'send', side_effect=Exception('SMTP down'))
def test_team_email_failure_is_swallowed(
    _mock_send, client_user, project, mailoutbox,  # noqa: PT019
):
    result = flow.send_client_first_login_notification(client_user.id)
    assert result is False
    assert len(mailoutbox) == 0


@patch.object(flow, 'notify_project_admins', side_effect=Exception('DB error'))
def test_admin_notification_failure_does_not_block_the_email(
    _mock_notify, client_user, project, mailoutbox,  # noqa: PT019
):
    result = flow.send_client_first_login_notification(client_user.id)
    assert result is True
    assert len(mailoutbox) == 1


def test_email_validated_returns_false_for_unknown_user(mailoutbox):
    result = flow.send_client_email_validated_notification(999999)
    assert result is False
    assert len(mailoutbox) == 0


def test_signed_notification_skips_client_confirmation_without_email(
    client_user, project, mailoutbox,
):
    client_user.email = ''
    client_user.save(update_fields=['email'])
    document = _make_document(client_user, project)
    result = flow.send_document_signed_notification(document.id)
    assert result is True
    # Only the team milestone email went out; no client confirmation.
    assert len(mailoutbox) == 1


def test_signed_client_confirmation_failure_is_swallowed(
    client_user, project, mailoutbox,
):
    document = _make_document(client_user, project)
    real_render = flow.render_to_string

    def failing_client_template(template, context):
        if 'document_signed_client' in template:
            raise Exception('template roto')
        return real_render(template, context)

    with patch.object(flow, 'render_to_string', side_effect=failing_client_template):
        result = flow.send_document_signed_notification(document.id)
    assert result is True
    assert len(mailoutbox) == 1


def test_signed_notification_returns_false_for_unknown_document(mailoutbox):
    result = flow.send_document_signed_notification(999999)
    assert result is False
    assert len(mailoutbox) == 0


def test_signed_notification_returns_false_without_signer(project, mailoutbox):
    document = _make_document(None, project)
    result = flow.send_document_signed_notification(document.id)
    assert result is False
    assert len(mailoutbox) == 0
