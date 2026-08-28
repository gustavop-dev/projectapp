from io import StringIO

from django.test import override_settings

from content.management.commands.diagnose_proposal_notifications import Command


@override_settings(
    MAILERS={
        'default': {
            'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'OPTIONS': {
                'host': 'smtp.example.com',
                'port': 465,
                'use_ssl': True,
                'username': 'mailer@example.com',
                'password': 'secret',
            },
        },
    },
)
def test_email_settings_reports_mailers_configuration():
    output = StringIO()

    Command(stdout=output)._check_email_settings()

    rendered = output.getvalue()
    assert 'django.core.mail.backends.smtp.EmailBackend' in rendered
    assert 'SMTP = smtp.example.com:465 (SSL=True, TLS=False)' in rendered
    assert 'SMTP username set (mailer@example.com).' in rendered
    assert 'SMTP password set.' in rendered


@override_settings(
    MAILERS={
        'default': {
            'BACKEND': 'django.core.mail.backends.locmem.EmailBackend',
        },
    },
)
def test_email_settings_warns_for_non_delivery_backend():
    output = StringIO()

    Command(stdout=output)._check_email_settings()

    assert 'Non-SMTP backend — emails are not actually delivered.' in output.getvalue()
