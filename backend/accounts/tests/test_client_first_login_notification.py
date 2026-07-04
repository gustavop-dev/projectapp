"""Tests for the first-login client-flow notification.

`send_client_first_login_notification` fires from verify_view on a client's
initial onboarding. It notifies project admins in-app and emails the team,
best-effort (never raises). The email_validated / document_signed events are
covered in test_client_documents.py; this closes the first_login gap.
"""
import pytest

from accounts.models import Notification
from accounts.services.client_flow_notifications import (
    send_client_first_login_notification,
)

pytestmark = pytest.mark.django_db


def test_first_login_notifies_admins_and_emails_team(
    client_user, admin_user, project, mailoutbox,
):
    send_client_first_login_notification(client_user.id)

    assert Notification.objects.filter(
        user=admin_user, type=Notification.TYPE_GENERAL,
    ).exists()
    assert len(mailoutbox) == 1  # team milestone email


def test_first_login_returns_false_for_unknown_user(mailoutbox):
    result = send_client_first_login_notification(999999)

    assert result is False
    assert len(mailoutbox) == 0
