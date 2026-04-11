"""Tests for content/utils.py.

Covers: send_whatsapp_notification, send_email_notification —
happy paths, missing config, API errors, email errors.
"""
from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import dns.exception
import dns.resolver
import pytest

from content.utils import (
    check_domain_mx,
    format_bogota_date,
    format_bogota_datetime,
    format_cop_email,
    now_bogota,
    send_email_notification,
    send_whatsapp_notification,
    to_bogota_date,
    today_bogota,
    validate_email_domain_mx,
)


@pytest.fixture(autouse=True)
def clear_domain_mx_cache():
    check_domain_mx.cache_clear()
    yield
    check_domain_mx.cache_clear()


class _FakeMxRecord:
    def __init__(self, exchange):
        self.exchange = exchange


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


class TestBogotaDateHelpers:
    @patch('content.utils.dj_timezone.now')
    def test_now_bogota_returns_current_datetime_in_bogota(self, mock_now):
        mock_now.return_value = datetime(2026, 4, 10, 17, 30, tzinfo=dt_timezone.utc)

        result = now_bogota()

        assert result.isoformat() == '2026-04-10T12:30:00-05:00'

    @patch('content.utils.now_bogota')
    def test_today_bogota_returns_calendar_date_from_bogota_now(self, mock_now_bogota):
        mock_now_bogota.return_value = datetime(2026, 4, 10, 23, 45, tzinfo=dt_timezone.utc)

        result = today_bogota()

        assert result == date(2026, 4, 10)

    def test_to_bogota_date_returns_none_for_falsy_value(self):
        assert to_bogota_date(None) is None

    def test_to_bogota_date_converts_aware_datetime_to_bogota_calendar_day(self):
        result = to_bogota_date(
            datetime(2026, 4, 10, 2, 30, tzinfo=dt_timezone.utc),
        )

        assert result == date(2026, 4, 9)

    def test_to_bogota_date_makes_naive_datetime_aware_before_conversion(self):
        result = to_bogota_date(datetime(2026, 4, 10, 3, 0))

        assert result == date(2026, 4, 9)

    def test_format_bogota_date_formats_aware_datetime(self):
        result = format_bogota_date(
            datetime(2026, 4, 10, 2, 30, tzinfo=dt_timezone.utc),
        )

        assert result == '9 de abril, 2026'

    def test_format_bogota_date_formats_plain_date(self):
        assert format_bogota_date(date(2026, 4, 8)) == '8 de abril, 2026'

    def test_format_bogota_date_returns_empty_string_for_invalid_type(self):
        assert format_bogota_date('2026-04-08') == ''

    def test_format_bogota_date_returns_empty_string_for_falsy_value(self):
        assert format_bogota_date(None) == ''

    @patch('content.utils.dj_timezone.make_aware')
    def test_format_bogota_date_makes_naive_datetime_aware_before_formatting(self, mock_make_aware):
        mock_make_aware.return_value = datetime(2026, 4, 8, 5, 30, tzinfo=dt_timezone.utc)

        result = format_bogota_date(datetime(2026, 4, 8, 5, 30))

        assert result == '8 de abril, 2026'

    @patch('content.utils.dj_timezone.make_aware')
    def test_format_bogota_datetime_formats_naive_datetime_in_bogota(self, mock_make_aware):
        mock_make_aware.return_value = datetime(2026, 4, 8, 19, 30, tzinfo=dt_timezone.utc)

        result = format_bogota_datetime(datetime(2026, 4, 8, 19, 30))

        assert result == '8 de abril, 2026 — 14:30'

    def test_format_bogota_datetime_returns_empty_string_for_falsy_value(self):
        assert format_bogota_datetime(None) == ''


class TestCheckDomainMx:
    @patch('content.utils._dns_resolver.resolve')
    def test_returns_true_when_domain_has_valid_mx_record(self, mock_resolve):
        mock_resolve.return_value = [_FakeMxRecord('mx.example.com.')]

        assert check_domain_mx('example.com') is True

    @patch('content.utils._dns_resolver.resolve')
    def test_returns_false_for_null_mx_record(self, mock_resolve):
        mock_resolve.return_value = [_FakeMxRecord('.')]

        assert check_domain_mx('example.com') is False

    @patch('content.utils._dns_resolver.resolve')
    def test_returns_true_when_mx_lookup_times_out(self, mock_resolve):
        mock_resolve.side_effect = dns.exception.Timeout

        assert check_domain_mx('example.com') is True

    @patch('content.utils._dns_resolver.resolve')
    def test_returns_true_when_a_record_exists_after_missing_mx(self, mock_resolve):
        mock_resolve.side_effect = [
            dns.resolver.NoAnswer(),
            [object()],
        ]

        assert check_domain_mx('example.com') is True

    @patch('content.utils._dns_resolver.resolve')
    def test_returns_false_when_domain_has_no_mx_or_a_record(self, mock_resolve):
        mock_resolve.side_effect = [
            dns.resolver.NXDOMAIN(),
            dns.resolver.NoAnswer(),
        ]

        assert check_domain_mx('example.com') is False


class TestValidateEmailDomainMx:
    def test_returns_true_for_blank_email(self):
        assert validate_email_domain_mx('') is True

    def test_returns_true_for_malformed_email_without_at_symbol(self):
        assert validate_email_domain_mx('not-an-email') is True

    def test_returns_true_for_email_with_blank_domain(self):
        assert validate_email_domain_mx('client@   ') is True

    @patch('content.utils.check_domain_mx', return_value=False)
    def test_returns_false_when_email_domain_has_no_mail_records(self, mock_check_domain_mx):
        result = validate_email_domain_mx('client@example.com')

        assert result is False
        mock_check_domain_mx.assert_called_once_with('example.com')

    @patch('content.utils.check_domain_mx', side_effect=RuntimeError('resolver exploded'))
    @patch('content.utils.logger.warning')
    def test_returns_true_when_dns_lookup_raises_unexpected_exception(
        self, mock_warning, mock_check_domain_mx,
    ):
        result = validate_email_domain_mx('client@example.com')

        assert result is True
        mock_check_domain_mx.assert_called_once_with('example.com')
        mock_warning.assert_called_once()


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
