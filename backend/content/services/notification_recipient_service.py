"""Who receives the accounting module's automated email.

Single source of truth: every internal notification of the module resolves
its destinations through here, so no inbox is hardcoded anywhere.

The master switch (``AccountingSettings.notifications_enabled``) is
deliberately NOT checked in this module. Each sender already guards on it
with its own log line, and folding it in here would collapse "the operator
paused everything" and "nobody is active" into the same silent empty list —
which is exactly the difference you need when diagnosing why an email never
arrived.
"""

from content.models import NotificationRecipient


def active_recipient_emails():
    """Return the active recipient addresses, alphabetically."""
    return list(
        NotificationRecipient.objects.filter(is_active=True)
        .order_by('email')
        .values_list('email', flat=True)
    )
