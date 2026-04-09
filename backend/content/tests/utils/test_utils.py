"""Tests for content/utils.py.

Covers: send_whatsapp_notification, send_email_notification —
happy paths, missing config, API errors, email errors.
"""
from unittest.mock import MagicMock, patch

from decimal import Decimal

import pytest

from content.utils import (
    format_cop_email,
    send_email_notification,
    send_whatsapp_notification,
)


class TestFormatCopEmail:
    @pytest.mark.parametrize('value, expected', [
        (1490000, "1'490.000"),
        (15000000, "15'000.000"),
        (123456, '123.456'),
        (5000, '5.000'),
        (500, '500'),
        (0, '0'),
        (Decimal('1490000.00'), "1'490.000"),
        (Decimal('15000000'), "15'000.000"),
        ('1490000', "1'490.000"),
        ('15,000,000', "15'000.000"),
        (1234567890, "1'234'567.890"),
        (-1490000, "-1'490.000"),
        (None, ''),
        (99, '99'),
    ])
    def test_format_cop_email(self, value, expected):
        assert format_cop_email(value) == expected

    def test_non_numeric_returns_as_is(self):
        assert format_cop_email('N/A') == 'N/A'


class TestSendWhatsappNotification:
    @patch('content.utils.requests.get')
    @patch('content.utils.settings')
    def test_sends_whatsapp_with_configured_phone(self, mock_settings, mock_get):
        mock_settings.WHATSAPP_PHONE = '+573001234567'
        mock_settings.CALLMEBOT_API_KEY = 'test-key'
        mock_get.return_value = MagicMock(status_code=200)

        result = send_whatsapp_notification('Hello')

        assert result is True
        mock_get.assert_called_once()
        assert '+573001234567' in mock_get.call_args[0][0]

    @patch('content.utils.requests.get')
    @patch('content.utils.settings')
    def test_sends_whatsapp_with_explicit_phone(self, mock_settings, mock_get):
        mock_settings.CALLMEBOT_API_KEY = 'test-key'
        mock_get.return_value = MagicMock(status_code=200)

        result = send_whatsapp_notification('Hello', phone='+1234567890')

        assert result is True
        mock_get.assert_called_once()
        assert '+1234567890' in mock_get.call_args[0][0]

    @patch('content.utils.settings')
    def test_returns_false_when_phone_not_configured(self, mock_settings):
        mock_settings.WHATSAPP_PHONE = None
        del mock_settings.WHATSAPP_PHONE
        type(mock_settings).WHATSAPP_PHONE = property(lambda self: None)

        result = send_whatsapp_notification('Hello')

        assert result is False

    @patch('content.utils.settings')
    def test_returns_false_when_api_key_not_configured(self, mock_settings):
        mock_settings.WHATSAPP_PHONE = '+573001234567'
        mock_settings.CALLMEBOT_API_KEY = None
        del mock_settings.CALLMEBOT_API_KEY
        type(mock_settings).CALLMEBOT_API_KEY = property(lambda self: None)

        result = send_whatsapp_notification('Hello')

        assert result is False

    @patch('content.utils.requests.get')
    @patch('content.utils.settings')
    def test_returns_false_on_non_200_response(self, mock_settings, mock_get):
        mock_settings.WHATSAPP_PHONE = '+573001234567'
        mock_settings.CALLMEBOT_API_KEY = 'test-key'
        mock_get.return_value = MagicMock(status_code=500, text='Server Error')

        result = send_whatsapp_notification('Hello')

        assert result is False
        mock_get.assert_called_once()

    @patch('content.utils.requests.get')
    @patch('content.utils.settings')
    def test_returns_false_on_request_exception(self, mock_settings, mock_get):
        mock_settings.WHATSAPP_PHONE = '+573001234567'
        mock_settings.CALLMEBOT_API_KEY = 'test-key'
        mock_get.side_effect = Exception('Network error')

        result = send_whatsapp_notification('Hello')

        assert result is False


class TestSendEmailNotification:
    @patch('content.utils.send_mail')
    @patch('content.utils.settings')
    def test_sends_email_with_configured_recipient(self, mock_settings, mock_send_mail):
        """Verify send_email_notification uses NOTIFICATION_EMAIL from settings."""
        mock_settings.NOTIFICATION_EMAIL = 'team@test.com'
        mock_settings.DEFAULT_FROM_EMAIL = 'no-reply@test.com'
        mock_send_mail.return_value = 1

        result = send_email_notification('Subject', 'Body')

        assert result is True
        mock_send_mail.assert_called_once_with(
            subject='Subject',
            message='Body',
            from_email='no-reply@test.com',
            recipient_list=['team@test.com'],
            fail_silently=False,
        )

    @patch('content.utils.send_mail')
    @patch('content.utils.settings')
    def test_sends_email_with_explicit_recipient(self, mock_settings, mock_send_mail):
        mock_settings.DEFAULT_FROM_EMAIL = 'no-reply@test.com'
        mock_send_mail.return_value = 1

        result = send_email_notification('Subject', 'Body', recipient_email='custom@test.com')

        assert result is True
        assert mock_send_mail.call_args[1]['recipient_list'] == ['custom@test.com']

    @patch('content.utils.settings')
    def test_returns_false_when_recipient_not_configured(self, mock_settings):
        mock_settings.NOTIFICATION_EMAIL = None
        del mock_settings.NOTIFICATION_EMAIL
        type(mock_settings).NOTIFICATION_EMAIL = property(lambda self: None)

        result = send_email_notification('Subject', 'Body')

        assert result is False

    @patch('content.utils.settings')
    def test_returns_false_when_from_email_not_configured(self, mock_settings):
        mock_settings.NOTIFICATION_EMAIL = 'team@test.com'
        mock_settings.DEFAULT_FROM_EMAIL = None
        del mock_settings.DEFAULT_FROM_EMAIL
        type(mock_settings).DEFAULT_FROM_EMAIL = property(lambda self: None)

        result = send_email_notification('Subject', 'Body')

        assert result is False

    @patch('content.utils.send_mail')
    @patch('content.utils.settings')
    def test_returns_false_on_send_mail_exception(self, mock_settings, mock_send_mail):
        mock_settings.NOTIFICATION_EMAIL = 'team@test.com'
        mock_settings.DEFAULT_FROM_EMAIL = 'no-reply@test.com'
        mock_send_mail.side_effect = Exception('SMTP error')

        result = send_email_notification('Subject', 'Body')

        assert result is False
