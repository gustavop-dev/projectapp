"""Provider failures have bounded, redacted errors; no permissive fallback."""
import pytest
from requests.exceptions import ConnectionError

from projectapp.checks import check_login_captcha
from projectapp.recaptcha import CaptchaError, verify_captcha


@pytest.mark.parametrize('payload', [
    b'not-json', b'[]', b'null', b'{}', b'{"success":"true"}',
    b'{"success":false,"error-codes":"bad-request"}',
    b'{"success":false,"error-codes":["invalid-input-secret"]}',
])
def test_invalid_provider_response_is_unavailable(google_response, payload):
    google_response.return_value._content = payload

    with pytest.raises(CaptchaError) as error:
        verify_captcha('submitted-token')

    assert error.value.status == 503
    assert error.value.code == 'captcha_unavailable'


@pytest.mark.parametrize('status', [429, 500, 502])
def test_provider_http_error_is_unavailable(google_response, status):
    google_response.return_value.status_code = status

    with pytest.raises(CaptchaError) as error:
        verify_captcha('submitted-token')

    assert error.value.code == 'captcha_unavailable'


def test_network_error_does_not_log_sensitive_payload(google_response, caplog):
    google_response.side_effect = ConnectionError('secret-for-tests submitted-token')

    with pytest.raises(CaptchaError):
        verify_captcha('submitted-token')

    assert 'verification unavailable' in caplog.text
    assert 'secret-for-tests' not in caplog.text
    assert 'submitted-token' not in caplog.text


def test_verification_posts_token_with_bounded_timeout(google_response):
    verify_captcha('submitted-token')

    google_response.assert_called_once_with(
        'https://www.google.com/recaptcha/api/siteverify',
        data={'secret': 'secret-for-tests', 'response': 'submitted-token'}, timeout=5,
    )


def test_production_cannot_disable_captcha(captcha_settings, google_response):
    captcha_settings.IS_PRODUCTION = True
    captcha_settings.RECAPTCHA_ENABLED = False

    with pytest.raises(CaptchaError) as error:
        verify_captcha('')

    assert error.value.code == 'captcha_required'


def test_local_opt_out_skips_provider(captcha_settings, google_response):
    captcha_settings.RECAPTCHA_ENABLED = False

    verify_captcha('')

    google_response.assert_not_called()


@pytest.mark.parametrize('hosts', [[], ['*'], ['https://example.com'], ['example.com:443']])
def test_deploy_check_rejects_unsafe_hostnames(captcha_settings, hosts):
    captcha_settings.RECAPTCHA_ALLOWED_HOSTNAMES = hosts

    errors = check_login_captcha(None)

    assert [error.id for error in errors] == ['projectapp.E001']
    assert 'RECAPTCHA_ALLOWED_HOSTNAMES' in errors[0].msg
