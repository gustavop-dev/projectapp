# Platform Password Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 3-step forgot-password flow to the `/platform` surface (email → OTP → new password) that mirrors the existing onboarding/verification pattern, mints a session JWT on success, and notifies the user by email that their password changed.

**Architecture:** Three new public DRF function-based endpoints under `/api/accounts/password-reset/`, glued by short-lived JWTs (`purpose` claim) that pass state between the three steps. State lives in tokens, not in DB — zero migrations. The `VerificationCode` model (already supports `PURPOSE_PASSWORD_RESET`) holds the OTP. Three new Nuxt pages drive the UI from `/platform/login`.

**Tech Stack:** Django 5 + DRF, SimpleJWT (`AccessToken` with custom claims), Nuxt 3 + Vue 3 + Pinia (Options API), Tailwind utility classes (matching `login.vue`'s inline style), Jest + Vue Test Utils for unit specs, Playwright for E2E.

**Spec:** `docs/superpowers/specs/2026-05-16-platform-password-recovery-design.md`

**Branch:** `feat/16052026-platform-password-recovery` (already created, based on `docs/16052026-claude-md-git-rules`).

---

## Spec deviations (intentional)

- **i18n:** The current `frontend/pages/platform/login.vue` hardcodes Spanish strings (`"Iniciar sesión"`, `"Ingresa con tu email..."`) — it does **not** use the global locale files. To keep the new pages consistent with `login.vue` and avoid a half-finished i18n migration, the new pages will **hardcode Spanish** the same way. The spec's `platform.passwordReset.*` keys are deferred to a future cleanup task that extracts both login and recovery copy together.
- Everything else follows the spec exactly.

---

## File Structure

**Backend — create:**
- `backend/accounts/services/password_reset.py` — business logic (3 entry points + email-notification helper + cooldown).
- `backend/content/templates/emails/password_reset_code.html` and `.txt` — OTP email body for password reset.
- `backend/content/templates/emails/password_reset_completed.html` and `.txt` — post-reset notification email.
- `backend/accounts/tests/test_password_reset.py` — 15 tests covering the service and views end-to-end.

**Backend — modify:**
- `backend/accounts/services/tokens.py` — add 3 token helpers + 1 shared decoder.
- `backend/accounts/services/verification.py` — pick the email template pair from a purpose→template mapping (default = `verification_code` so onboarding stays intact).
- `backend/accounts/serializers.py` — append 3 input serializers.
- `backend/accounts/views.py` — append 3 thin DRF views.
- `backend/accounts/urls.py` — append 3 routes under `password-reset/`.

**Frontend — create:**
- `frontend/pages/platform/forgot-password.vue` — step 1 (email).
- `frontend/pages/platform/verify-code.vue` — step 2 (OTP).
- `frontend/pages/platform/reset-password.vue` — step 3 (new password).
- `frontend/test/stores/platform-auth.password-reset.spec.js` — store actions.
- `frontend/test/pages/forgot-password.spec.js` — page unit.
- `frontend/test/pages/verify-code.spec.js` — page unit.
- `frontend/test/pages/reset-password.spec.js` — page unit.
- `frontend/e2e/platform/platform-password-reset.spec.js` — E2E happy path + recoverable wrong code.

**Frontend — modify:**
- `frontend/stores/platform-auth.js` — add `passwordReset` state slice + 3 actions (`startPasswordReset`, `markCodeVerified`, `clearPasswordReset`).
- `frontend/composables/usePlatformApi.js` — no change required (the generic `request/post` is enough; password reset wrappers live in the store).
- `frontend/pages/platform/login.vue` — append "¿Olvidaste tu contraseña?" link.

---

## Working conventions for each task

- Always activate the backend venv before running `pytest`:
  `cd backend && source venv/bin/activate`
- Use `pytest backend/accounts/tests/test_password_reset.py::<test_name> -v` for targeted runs. Never run the full suite.
- Frontend unit tests: `npm --prefix frontend test -- <path>`.
- Frontend E2E: `npm --prefix frontend run e2e -- frontend/e2e/platform/platform-password-reset.spec.js`.
- Commit messages follow `FEAT: ...` / `DOCS: ...` (project style). No `Co-Authored-By`, no Claude attribution footer.
- After every task: `cd backend && source venv/bin/activate && python manage.py check` to catch import or URL regressions early.

---

## Task 1 — Token helpers and shared decoder

**Files:**
- Modify: `backend/accounts/services/tokens.py`
- Test: `backend/accounts/tests/test_password_reset.py` (new file; this task seeds it)

- [ ] **Step 1: Write failing test for the three token helpers and the decoder**

Create `backend/accounts/tests/test_password_reset.py`:

```python
"""Tests for the platform password recovery flow."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from accounts.services.tokens import (
    PASSWORD_RESET_REQUEST_PURPOSE,
    PASSWORD_RESET_VERIFIED_PURPOSE,
    decode_password_reset_token,
    get_decoy_password_reset_request_token,
    get_password_reset_request_token,
    get_password_reset_verified_token,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def reset_user(db):
    return User.objects.create_user(
        username='reset@example.com',
        email='reset@example.com',
        password='OldPass123!',
    )


def test_request_token_contains_user_id_and_purpose(reset_user):
    raw = get_password_reset_request_token(reset_user)
    decoded = AccessToken(raw)
    assert decoded['purpose'] == PASSWORD_RESET_REQUEST_PURPOSE
    assert decoded['user_id'] == reset_user.pk


def test_verified_token_contains_user_id_and_purpose(reset_user):
    raw = get_password_reset_verified_token(reset_user)
    decoded = AccessToken(raw)
    assert decoded['purpose'] == PASSWORD_RESET_VERIFIED_PURPOSE
    assert decoded['user_id'] == reset_user.pk


def test_decoy_token_has_no_user_id_but_correct_purpose():
    raw = get_decoy_password_reset_request_token()
    decoded = AccessToken(raw)
    assert decoded['purpose'] == PASSWORD_RESET_REQUEST_PURPOSE
    assert decoded.payload.get('user_id') is None


def test_decoder_rejects_wrong_purpose(reset_user):
    raw = get_password_reset_request_token(reset_user)
    with pytest.raises(TokenError):
        decode_password_reset_token(raw, expected_purpose=PASSWORD_RESET_VERIFIED_PURPOSE)


def test_decoder_returns_payload_when_purpose_matches(reset_user):
    raw = get_password_reset_request_token(reset_user)
    payload = decode_password_reset_token(raw, expected_purpose=PASSWORD_RESET_REQUEST_PURPOSE)
    assert payload['user_id'] == reset_user.pk


def test_request_token_expires_after_10_minutes(reset_user):
    with freeze_time('2026-05-16 10:00:00'):
        raw = get_password_reset_request_token(reset_user)
    with freeze_time('2026-05-16 10:11:00'):
        with pytest.raises(TokenError):
            decode_password_reset_token(raw, expected_purpose=PASSWORD_RESET_REQUEST_PURPOSE)


def test_verified_token_expires_after_5_minutes(reset_user):
    with freeze_time('2026-05-16 10:00:00'):
        raw = get_password_reset_verified_token(reset_user)
    with freeze_time('2026-05-16 10:06:00'):
        with pytest.raises(TokenError):
            decode_password_reset_token(raw, expected_purpose=PASSWORD_RESET_VERIFIED_PURPOSE)
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_password_reset.py -v
```

Expected: `ImportError` for the helpers / decoder. All 7 tests error out, not just fail.

- [ ] **Step 3: Implement the helpers in `tokens.py`**

Append to `backend/accounts/services/tokens.py`:

```python
from datetime import timedelta

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


PASSWORD_RESET_REQUEST_PURPOSE = 'password_reset_request'
PASSWORD_RESET_VERIFIED_PURPOSE = 'password_reset_verified'

REQUEST_TOKEN_LIFETIME = timedelta(minutes=10)
VERIFIED_TOKEN_LIFETIME = timedelta(minutes=5)


def get_password_reset_request_token(user) -> str:
    token = AccessToken.for_user(user)
    token.set_exp(lifetime=REQUEST_TOKEN_LIFETIME)
    token['purpose'] = PASSWORD_RESET_REQUEST_PURPOSE
    return str(token)


def get_password_reset_verified_token(user) -> str:
    token = AccessToken.for_user(user)
    token.set_exp(lifetime=VERIFIED_TOKEN_LIFETIME)
    token['purpose'] = PASSWORD_RESET_VERIFIED_PURPOSE
    return str(token)


def get_decoy_password_reset_request_token() -> str:
    """Returned when the requested email does not match a registered user.
    Same shape and lifetime as the real token but without a `user_id` claim,
    so any follow-up step fails with the generic invalid_code response."""
    token = AccessToken()
    token.set_exp(lifetime=REQUEST_TOKEN_LIFETIME)
    token['purpose'] = PASSWORD_RESET_REQUEST_PURPOSE
    return str(token)


def decode_password_reset_token(token_str: str, expected_purpose: str) -> dict:
    """Decode a password-reset token. Raises rest_framework_simplejwt.TokenError
    when the signature is invalid, the token is expired, or the `purpose` claim
    does not match `expected_purpose`."""
    token = AccessToken(token_str)
    if token.get('purpose') != expected_purpose:
        raise TokenError('Token purpose mismatch.')
    return token.payload
```

- [ ] **Step 4: Run tests to confirm they pass**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_password_reset.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```
git add backend/accounts/services/tokens.py backend/accounts/tests/test_password_reset.py
git commit -m "FEAT: password-reset token helpers (request/verified/decoy + purpose-aware decoder)"
```

---

## Task 2 — Email templates (OTP variant and post-reset notification)

**Files:**
- Create: `backend/content/templates/emails/password_reset_code.html`
- Create: `backend/content/templates/emails/password_reset_code.txt`
- Create: `backend/content/templates/emails/password_reset_completed.html`
- Create: `backend/content/templates/emails/password_reset_completed.txt`

These templates do not have direct tests; they are exercised by the service-level tests in later tasks. We commit them first so subsequent tests have something to render.

- [ ] **Step 1: Create `password_reset_code.html`**

```html
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Tu código para restablecer la contraseña</title></head>
<body style="font-family: system-ui, sans-serif; background: #f6f7f8; padding: 24px;">
  <table role="presentation" cellpadding="0" cellspacing="0" style="max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px;">
    <tr><td>
      <h1 style="margin: 0 0 12px; font-size: 20px; color: #002921;">Restablece tu contraseña</h1>
      <p style="margin: 0 0 16px; color: #2a3540; line-height: 1.5;">
        Hola{% if user.first_name %} {{ user.first_name }}{% endif %}, recibimos una solicitud para restablecer la contraseña de tu cuenta en ProjectApp.
      </p>
      <p style="margin: 0 0 8px; color: #2a3540;">Tu código de verificación es:</p>
      <p style="font-size: 32px; letter-spacing: 6px; font-weight: 700; color: #002921; margin: 8px 0 16px;">{{ code }}</p>
      <p style="margin: 0 0 12px; color: #5a6470; font-size: 13px;">El código expira en {{ expiry_minutes }} minutos.</p>
      <p style="margin: 16px 0 0; color: #5a6470; font-size: 13px;">
        Si no fuiste tú quien solicitó este cambio, puedes ignorar este correo — tu contraseña actual sigue activa.
      </p>
    </td></tr>
  </table>
</body>
</html>
```

- [ ] **Step 2: Create `password_reset_code.txt`**

```
Restablece tu contraseña — ProjectApp

Hola{% if user.first_name %} {{ user.first_name }}{% endif %},

Recibimos una solicitud para restablecer la contraseña de tu cuenta.
Tu código de verificación es: {{ code }}

El código expira en {{ expiry_minutes }} minutos.

Si no fuiste tú, ignora este correo — tu contraseña actual sigue activa.
```

- [ ] **Step 3: Create `password_reset_completed.html`**

```html
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Se restableció la contraseña de tu cuenta</title></head>
<body style="font-family: system-ui, sans-serif; background: #f6f7f8; padding: 24px;">
  <table role="presentation" cellpadding="0" cellspacing="0" style="max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px;">
    <tr><td>
      <h1 style="margin: 0 0 12px; font-size: 20px; color: #002921;">Tu contraseña fue restablecida</h1>
      <p style="margin: 0 0 12px; color: #2a3540; line-height: 1.5;">
        Hola{% if user.first_name %} {{ user.first_name }}{% endif %}, la contraseña de tu cuenta en ProjectApp se restableció correctamente.
      </p>
      <p style="margin: 0 0 12px; color: #2a3540;">Fecha y hora (UTC): <strong>{{ changed_at|date:"Y-m-d H:i:s" }}</strong></p>
      <p style="margin: 16px 0 0; color: #b00020; font-size: 13px;">
        Si no fuiste tú quien hizo este cambio, contáctanos inmediatamente en <a href="mailto:{{ support_email }}">{{ support_email }}</a>.
      </p>
    </td></tr>
  </table>
</body>
</html>
```

- [ ] **Step 4: Create `password_reset_completed.txt`**

```
Tu contraseña fue restablecida — ProjectApp

Hola{% if user.first_name %} {{ user.first_name }}{% endif %},

La contraseña de tu cuenta en ProjectApp se restableció correctamente.
Fecha y hora (UTC): {{ changed_at|date:"Y-m-d H:i:s" }}

Si no fuiste tú quien hizo este cambio, contáctanos inmediatamente
en {{ support_email }}.
```

- [ ] **Step 5: Sanity-check that Django can load the templates**

```
cd backend && source venv/bin/activate && python -c "from django.template.loader import get_template; import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','projectapp.settings'); django.setup(); get_template('emails/password_reset_code.html'); get_template('emails/password_reset_completed.html'); print('templates OK')"
```

Expected: `templates OK` printed.

- [ ] **Step 6: Commit**

```
git add backend/content/templates/emails/password_reset_code.html \
        backend/content/templates/emails/password_reset_code.txt \
        backend/content/templates/emails/password_reset_completed.html \
        backend/content/templates/emails/password_reset_completed.txt
git commit -m "FEAT: password-reset email templates (OTP + post-reset confirmation)"
```

---

## Task 3 — Wire `verification.py` to pick template by purpose

**Files:**
- Modify: `backend/accounts/services/verification.py`
- Test: `backend/accounts/tests/test_password_reset.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `backend/accounts/tests/test_password_reset.py`:

```python
from django.core import mail

from accounts.models import VerificationCode
from accounts.services.verification import create_and_send_otp


def test_create_and_send_otp_uses_password_reset_template_for_reset_purpose(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    create_and_send_otp(reset_user, purpose=VerificationCode.PURPOSE_PASSWORD_RESET)
    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert 'restablecer' in sent.body.lower() or 'restablec' in sent.alternatives[0][0].lower()
    assert reset_user.email in sent.to


def test_create_and_send_otp_default_purpose_still_uses_onboarding_template(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    create_and_send_otp(reset_user)  # defaults to PURPOSE_ONBOARDING
    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    # the onboarding template contains the legacy subject — make sure we did NOT
    # accidentally swap it for the reset copy.
    assert 'restablecer' not in sent.body.lower()
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_password_reset.py::test_create_and_send_otp_uses_password_reset_template_for_reset_purpose -v
```

Expected: assertion failure — the body still contains the onboarding copy because the current `create_and_send_otp` hardcodes `verification_code.html`.

- [ ] **Step 3: Update `verification.py`**

Replace `backend/accounts/services/verification.py` entirely with:

```python
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from accounts.models import VerificationCode


# Map OTP purpose -> (template_base, subject)
_OTP_TEMPLATES = {
    VerificationCode.PURPOSE_ONBOARDING: (
        'emails/verification_code',
        'Tu código de verificación — ProjectApp',
    ),
    VerificationCode.PURPOSE_PASSWORD_RESET: (
        'emails/password_reset_code',
        'Tu código para restablecer la contraseña — ProjectApp',
    ),
}


def create_and_send_otp(user, purpose=VerificationCode.PURPOSE_ONBOARDING):
    """Create a new OTP for the user and send it via email."""
    otp = VerificationCode.create_for_user(user, purpose=purpose)

    template_base, subject = _OTP_TEMPLATES.get(
        purpose, _OTP_TEMPLATES[VerificationCode.PURPOSE_ONBOARDING],
    )
    context = {
        'user': user,
        'code': otp.code,
        'expiry_minutes': VerificationCode.EXPIRY_MINUTES,
    }
    html_message = render_to_string(f'{template_base}.html', context)
    try:
        plain_message = render_to_string(f'{template_base}.txt', context)
    except Exception:
        plain_message = f'Tu código es: {otp.code}'

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

    return otp


def validate_otp(user, code, purpose=VerificationCode.PURPOSE_ONBOARDING):
    """
    Validate an OTP code for the given user.
    Returns (success: bool, error_message: str | None).
    """
    latest = (
        VerificationCode.objects
        .filter(user=user, purpose=purpose, is_used=False)
        .order_by('-created_at')
        .first()
    )

    if not latest:
        return False, 'No hay código de verificación activo. Solicita uno nuevo.'

    if latest.is_expired:
        return False, 'El código ha expirado. Solicita uno nuevo.'

    if latest.attempts >= VerificationCode.MAX_ATTEMPTS:
        return False, 'Demasiados intentos fallidos. Solicita un nuevo código.'

    if latest.code != code:
        latest.increment_attempts()
        remaining = VerificationCode.MAX_ATTEMPTS - latest.attempts
        return False, f'Código incorrecto. Te quedan {remaining} intentos.'

    latest.mark_used()
    return True, None
```

The fallback `try/except` for `.txt` keeps backward compatibility with the existing `verification_code.html` (which has no `.txt` sibling in the repo today).

- [ ] **Step 4: Run targeted tests to confirm pass**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_password_reset.py::test_create_and_send_otp_uses_password_reset_template_for_reset_purpose accounts/tests/test_password_reset.py::test_create_and_send_otp_default_purpose_still_uses_onboarding_template -v
```

Expected: 2 passed.

- [ ] **Step 5: Run the existing onboarding/verification tests to confirm no regression**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_verification.py -v
```

Expected: all green. If any test referenced the exact onboarding subject string and now fails, fix it inline — but the subject did not change (we kept `'Tu código de verificación — ProjectApp'`), so it should be clean.

- [ ] **Step 6: Commit**

```
git add backend/accounts/services/verification.py backend/accounts/tests/test_password_reset.py
git commit -m "FEAT: route OTP template by purpose (onboarding stays, password-reset added)"
```

---

## Task 4 — Password-reset service module

**Files:**
- Create: `backend/accounts/services/password_reset.py`
- Test: `backend/accounts/tests/test_password_reset.py` (append)

- [ ] **Step 1: Write the failing service-level tests**

Append to `backend/accounts/tests/test_password_reset.py`:

```python
import hashlib

from accounts.services import password_reset as pr_service
from accounts.services.password_reset import (
    COOLDOWN_SECONDS,
    PasswordResetError,
    confirm_password_reset,
    request_password_reset,
    verify_reset_code,
)


def test_request_with_existing_email_creates_code_and_sends_email(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    token = request_password_reset(reset_user.email)
    assert token  # non-empty string
    assert len(mail.outbox) == 1
    assert VerificationCode.objects.filter(
        user=reset_user, purpose=VerificationCode.PURPOSE_PASSWORD_RESET, is_used=False,
    ).count() == 1


def test_request_with_nonexistent_email_returns_decoy_token(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    token = request_password_reset('ghost@example.com')
    assert token
    decoded = AccessToken(token)
    assert decoded.payload.get('user_id') is None
    assert len(mail.outbox) == 0


def test_request_cooldown_skips_resend(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_password_reset(reset_user.email)
    request_password_reset(reset_user.email)
    assert len(mail.outbox) == 1
    # Even on the second call we still hand back a valid token.
    second = request_password_reset(reset_user.email)
    assert AccessToken(second)['user_id'] == reset_user.pk


def test_request_cooldown_lapsed_resends(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    with freeze_time('2026-05-16 10:00:00'):
        request_password_reset(reset_user.email)
    with freeze_time('2026-05-16 10:01:30'):
        request_password_reset(reset_user.email)
    assert len(mail.outbox) == 2


def _request_and_extract_code(user):
    """Helper used by the next batch of tests."""
    request_password_reset(user.email)
    return VerificationCode.objects.filter(
        user=user, purpose=VerificationCode.PURPOSE_PASSWORD_RESET, is_used=False,
    ).latest('created_at')


def test_verify_with_valid_code_returns_verified_token(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    code = VerificationCode.objects.filter(
        user=reset_user, purpose=VerificationCode.PURPOSE_PASSWORD_RESET, is_used=False,
    ).latest('created_at').code
    verified_token = verify_reset_code(request_token, code)
    assert AccessToken(verified_token)['purpose'] == 'password_reset_verified'
    assert AccessToken(verified_token)['user_id'] == reset_user.pk


def test_verify_with_wrong_code_decrements_attempts(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    with pytest.raises(PasswordResetError) as exc:
        verify_reset_code(request_token, '000000')
    assert exc.value.code == 'invalid_code'
    assert exc.value.extra.get('attempts_left') == 4


def test_verify_with_wrong_code_5_times_returns_too_many_attempts(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    for _ in range(4):
        with pytest.raises(PasswordResetError):
            verify_reset_code(request_token, '000000')
    with pytest.raises(PasswordResetError) as exc:
        verify_reset_code(request_token, '000000')
    assert exc.value.code == 'too_many_attempts'


def test_verify_with_expired_code_returns_code_expired(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    with freeze_time('2026-05-16 10:00:00'):
        request_token = request_password_reset(reset_user.email)
        real_code = VerificationCode.objects.latest('created_at').code
    with freeze_time('2026-05-16 10:11:00'):
        with pytest.raises(PasswordResetError) as exc:
            verify_reset_code(request_token, real_code)
        # 10-min request token AND 10-min OTP both expire — either error is acceptable
        assert exc.value.code in {'code_expired', 'invalid_code'}


def test_verify_with_decoy_token_returns_invalid_code():
    decoy = pr_service.get_decoy_password_reset_request_token()
    with pytest.raises(PasswordResetError) as exc:
        verify_reset_code(decoy, '123456')
    assert exc.value.code == 'invalid_code'


def test_confirm_with_valid_token_sets_new_password_and_returns_tokens(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    real_code = VerificationCode.objects.latest('created_at').code
    verified_token = verify_reset_code(request_token, real_code)
    payload = confirm_password_reset(verified_token, 'NewStrongPass456!')
    reset_user.refresh_from_db()
    assert reset_user.check_password('NewStrongPass456!')
    assert 'access' in payload and 'refresh' in payload
    assert payload['user'] is None or payload['user']['email'] == reset_user.email


def test_confirm_with_weak_password_returns_validation_errors(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    real_code = VerificationCode.objects.latest('created_at').code
    verified_token = verify_reset_code(request_token, real_code)
    with pytest.raises(PasswordResetError) as exc:
        confirm_password_reset(verified_token, '12345')
    assert exc.value.code == 'weak_password'
    assert exc.value.extra.get('errors')


def test_confirm_rejects_request_token_used_as_verified(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    request_token = request_password_reset(reset_user.email)
    with pytest.raises(PasswordResetError) as exc:
        confirm_password_reset(request_token, 'NewStrongPass456!')
    assert exc.value.code == 'invalid_or_expired_token'
    assert exc.value.http_status == 401


def test_confirm_sends_confirmation_email_to_user(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    real_code = VerificationCode.objects.latest('created_at').code
    verified_token = verify_reset_code(request_token, real_code)
    confirm_password_reset(verified_token, 'NewStrongPass456!')
    confirmation_emails = [m for m in mail.outbox if 'restableci' in m.subject.lower()]
    assert len(confirmation_emails) == 1
    assert confirmation_emails[0].to == [reset_user.email]
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_password_reset.py -v
```

Expected: import error for `accounts.services.password_reset` — the next several tests don't even reach assertion.

- [ ] **Step 3: Create `password_reset.py`**

`backend/accounts/services/password_reset.py`:

```python
"""Business logic for the platform forgot-password flow.

State between the three HTTP steps is carried in short-lived JWTs (see
`accounts.services.tokens`). The OTP itself lives in `VerificationCode`.
"""
import hashlib
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError

from accounts.models import VerificationCode
from accounts.services.tokens import (
    PASSWORD_RESET_REQUEST_PURPOSE,
    PASSWORD_RESET_VERIFIED_PURPOSE,
    decode_password_reset_token,
    get_decoy_password_reset_request_token,
    get_password_reset_request_token,
    get_password_reset_verified_token,
    get_tokens_for_user,
)
from accounts.services.verification import create_and_send_otp

logger = logging.getLogger('accounts.services.password_reset')
User = get_user_model()

COOLDOWN_SECONDS = 60


class PasswordResetError(Exception):
    """Service-level error with a stable code + optional payload extras.

    Views map this to HTTP responses (see views.password_reset_*).
    """
    def __init__(self, code: str, http_status: int = 400, extra: dict | None = None):
        self.code = code
        self.http_status = http_status
        self.extra = extra or {}
        super().__init__(code)


def _email_hash(email: str) -> str:
    return hashlib.sha256(email.encode('utf-8')).hexdigest()[:12]


def request_password_reset(email: str) -> str:
    """Step 1. Always returns a request token (real or decoy)."""
    email_lower = (email or '').lower().strip()
    user = User.objects.filter(email__iexact=email_lower).first()

    if user is None:
        logger.info(
            'password_reset_requested',
            extra={'email_hash': _email_hash(email_lower), 'user_found': False, 'cooldown_hit': False},
        )
        return get_decoy_password_reset_request_token()

    cutoff = timezone.now() - timedelta(seconds=COOLDOWN_SECONDS)
    cooldown_hit = VerificationCode.objects.filter(
        user=user,
        purpose=VerificationCode.PURPOSE_PASSWORD_RESET,
        created_at__gte=cutoff,
    ).exists()

    if not cooldown_hit:
        create_and_send_otp(user, purpose=VerificationCode.PURPOSE_PASSWORD_RESET)

    logger.info(
        'password_reset_requested',
        extra={'email_hash': _email_hash(email_lower), 'user_found': True, 'cooldown_hit': cooldown_hit},
    )
    return get_password_reset_request_token(user)


def verify_reset_code(request_token: str, code: str) -> str:
    """Step 2. Validates the OTP and returns a verified token."""
    try:
        payload = decode_password_reset_token(request_token, expected_purpose=PASSWORD_RESET_REQUEST_PURPOSE)
    except TokenError:
        raise PasswordResetError('invalid_or_expired_token', http_status=401)

    user_id = payload.get('user_id')
    if not user_id:
        # decoy token — generic failure
        raise PasswordResetError('invalid_code')

    user = User.objects.filter(pk=user_id).first()
    if not user:
        raise PasswordResetError('invalid_code')

    latest = (
        VerificationCode.objects
        .filter(user=user, purpose=VerificationCode.PURPOSE_PASSWORD_RESET, is_used=False)
        .order_by('-created_at')
        .first()
    )

    if not latest:
        raise PasswordResetError('invalid_code')

    if latest.is_expired:
        raise PasswordResetError('code_expired')

    if latest.attempts >= VerificationCode.MAX_ATTEMPTS:
        raise PasswordResetError('too_many_attempts')

    if latest.code != code:
        latest.increment_attempts()
        remaining = VerificationCode.MAX_ATTEMPTS - latest.attempts
        if remaining <= 0:
            raise PasswordResetError('too_many_attempts')
        raise PasswordResetError('invalid_code', extra={'attempts_left': remaining})

    latest.mark_used()
    logger.info('password_reset_code_verified', extra={'user_id': user.pk})
    return get_password_reset_verified_token(user)


def confirm_password_reset(verified_token: str, new_password: str) -> dict:
    """Step 3. Sets the new password, fires the confirmation email, and returns
    a session payload identical in shape to a successful /login/ response."""
    try:
        payload = decode_password_reset_token(verified_token, expected_purpose=PASSWORD_RESET_VERIFIED_PURPOSE)
    except TokenError:
        raise PasswordResetError('invalid_or_expired_token', http_status=401)

    user_id = payload.get('user_id')
    if not user_id:
        raise PasswordResetError('invalid_or_expired_token', http_status=401)

    user = User.objects.filter(pk=user_id).first()
    if not user:
        raise PasswordResetError('invalid_or_expired_token', http_status=401)

    try:
        validate_password(new_password, user=user)
    except ValidationError as exc:
        raise PasswordResetError('weak_password', extra={'errors': list(exc.messages)})

    user.set_password(new_password)
    user.save(update_fields=['password'])

    try:
        send_password_changed_notification(user)
    except Exception as exc:  # noqa: BLE001 — email failures must not roll back password change
        logger.warning(
            'password_reset_email_failure',
            extra={'user_id': user.pk, 'reason': str(exc)},
        )

    logger.info('password_reset_completed', extra={'user_id': user.pk})

    tokens = get_tokens_for_user(user)
    profile = getattr(user, 'profile', None)
    # Lazy import: serializer pulls models that we want to keep out of the
    # service module's import graph for testability.
    from accounts.serializers import UserProfileSerializer
    return {
        'access': tokens['access'],
        'refresh': tokens['refresh'],
        'user': UserProfileSerializer(profile).data if profile else None,
    }


def send_password_changed_notification(user) -> None:
    """Renders and sends the post-reset confirmation email. Best-effort:
    callers are responsible for swallowing exceptions."""
    context = {
        'user': user,
        'changed_at': timezone.now(),
        'support_email': 'team@projectapp.co',
    }
    html_message = render_to_string('emails/password_reset_completed.html', context)
    text_message = render_to_string('emails/password_reset_completed.txt', context)
    send_mail(
        subject='Se restableció la contraseña de tu cuenta — ProjectApp',
        message=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
```

- [ ] **Step 4: Run all current tests in the file**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_password_reset.py -v
```

Expected: all 13 currently-written service/token tests pass. (The test count keeps growing across tasks — at this point it is 9 service tests + 7 token tests + 2 verification tests + 2 in step 3 above = 20. If pytest collects fewer because of import errors, fix the imports first.)

- [ ] **Step 5: Commit**

```
git add backend/accounts/services/password_reset.py backend/accounts/tests/test_password_reset.py
git commit -m "FEAT: password-reset service (request/verify/confirm + cooldown + notification email)"
```

---

## Task 5 — Input serializers

**Files:**
- Modify: `backend/accounts/serializers.py`

- [ ] **Step 1: Append serializers**

Append to `backend/accounts/serializers.py`:

```python
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetVerifyCodeSerializer(serializers.Serializer):
    reset_request_token = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)


class PasswordResetConfirmSerializer(serializers.Serializer):
    reset_verified_token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)
```

- [ ] **Step 2: Confirm `python manage.py check` is clean**

```
cd backend && source venv/bin/activate && python manage.py check
```

Expected: `System check identified no issues`.

- [ ] **Step 3: Commit**

```
git add backend/accounts/serializers.py
git commit -m "FEAT: serializers for password-reset request/verify/confirm payloads"
```

---

## Task 6 — Views and URL routes

**Files:**
- Modify: `backend/accounts/views.py`
- Modify: `backend/accounts/urls.py`
- Test: `backend/accounts/tests/test_password_reset.py` (append HTTP-level tests)

- [ ] **Step 1: Write the failing HTTP-level tests**

Append to `backend/accounts/tests/test_password_reset.py`:

```python
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


def test_request_view_returns_token_for_existing_email(api_client, reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    resp = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': reset_user.email}, format='json',
    )
    assert resp.status_code == 200
    assert resp.json()['reset_request_token']
    assert len(mail.outbox) == 1


def test_request_view_returns_decoy_token_for_unknown_email(api_client, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    resp = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': 'ghost@example.com'}, format='json',
    )
    assert resp.status_code == 200
    assert resp.json()['reset_request_token']
    assert len(mail.outbox) == 0


def test_request_view_rejects_malformed_email(api_client):
    resp = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': 'not-an-email'}, format='json',
    )
    assert resp.status_code == 400


def test_verify_view_happy_path(api_client, reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    r1 = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': reset_user.email}, format='json',
    )
    request_token = r1.json()['reset_request_token']
    code = VerificationCode.objects.latest('created_at').code
    r2 = api_client.post(
        '/api/accounts/password-reset/verify-code/',
        {'reset_request_token': request_token, 'code': code}, format='json',
    )
    assert r2.status_code == 200
    assert r2.json()['reset_verified_token']


def test_verify_view_wrong_code_surfaces_attempts_left(api_client, reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    r1 = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': reset_user.email}, format='json',
    )
    request_token = r1.json()['reset_request_token']
    r2 = api_client.post(
        '/api/accounts/password-reset/verify-code/',
        {'reset_request_token': request_token, 'code': '000000'}, format='json',
    )
    assert r2.status_code == 400
    body = r2.json()
    assert body['detail'] == 'invalid_code'
    assert body['attempts_left'] == 4


def test_confirm_view_completes_flow_and_returns_session(api_client, reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    r1 = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': reset_user.email}, format='json',
    )
    request_token = r1.json()['reset_request_token']
    code = VerificationCode.objects.latest('created_at').code
    r2 = api_client.post(
        '/api/accounts/password-reset/verify-code/',
        {'reset_request_token': request_token, 'code': code}, format='json',
    )
    verified_token = r2.json()['reset_verified_token']
    r3 = api_client.post(
        '/api/accounts/password-reset/confirm/',
        {'reset_verified_token': verified_token, 'new_password': 'NewStrongPass456!'}, format='json',
    )
    assert r3.status_code == 200
    body = r3.json()
    assert 'access' in body and 'refresh' in body
    reset_user.refresh_from_db()
    assert reset_user.check_password('NewStrongPass456!')


def test_confirm_view_weak_password_returns_errors(api_client, reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    r1 = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': reset_user.email}, format='json',
    )
    request_token = r1.json()['reset_request_token']
    code = VerificationCode.objects.latest('created_at').code
    r2 = api_client.post(
        '/api/accounts/password-reset/verify-code/',
        {'reset_request_token': request_token, 'code': code}, format='json',
    )
    verified_token = r2.json()['reset_verified_token']
    r3 = api_client.post(
        '/api/accounts/password-reset/confirm/',
        {'reset_verified_token': verified_token, 'new_password': '12345'}, format='json',
    )
    assert r3.status_code == 400
    body = r3.json()
    assert body['detail'] == 'weak_password'
    assert isinstance(body['errors'], list) and body['errors']
```

- [ ] **Step 2: Run tests to confirm they fail (no views yet)**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_password_reset.py -k 'view' -v
```

Expected: 404 from the URLs (routes not registered yet).

- [ ] **Step 3: Append views to `backend/accounts/views.py`**

Add the import at the top of the file (next to the existing service imports):

```python
from accounts.serializers import (
    # ... existing imports ...
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifyCodeSerializer,
)
from accounts.services.password_reset import (
    PasswordResetError,
    confirm_password_reset,
    request_password_reset,
    verify_reset_code,
)
```

Then append the three views at the end of the Auth section (after `token_refresh_view`):

```python
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """Step 1: receives `{email}`, always responds 200 with a request token."""
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = request_password_reset(serializer.validated_data['email'])
    return Response({'reset_request_token': token})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def password_reset_verify_view(request):
    """Step 2: receives `{reset_request_token, code}` and returns a verified token."""
    serializer = PasswordResetVerifyCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        verified_token = verify_reset_code(
            serializer.validated_data['reset_request_token'],
            serializer.validated_data['code'],
        )
    except PasswordResetError as exc:
        body = {'detail': exc.code, **exc.extra}
        return Response(body, status=exc.http_status)
    return Response({'reset_verified_token': verified_token})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """Step 3: sets the new password and returns a fresh session."""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        payload = confirm_password_reset(
            serializer.validated_data['reset_verified_token'],
            serializer.validated_data['new_password'],
        )
    except PasswordResetError as exc:
        body = {'detail': exc.code, **exc.extra}
        return Response(body, status=exc.http_status)
    return Response(payload)
```

- [ ] **Step 4: Wire the URLs**

In `backend/accounts/urls.py`, add the imports to the existing block:

```python
from accounts.views import (
    # ... existing imports ...
    password_reset_confirm_view,
    password_reset_request_view,
    password_reset_verify_view,
)
```

And append three lines right after `path('resend-code/', ..., name='platform-resend-code'),`:

```python
    path('password-reset/request/', password_reset_request_view, name='platform-password-reset-request'),
    path('password-reset/verify-code/', password_reset_verify_view, name='platform-password-reset-verify'),
    path('password-reset/confirm/', password_reset_confirm_view, name='platform-password-reset-confirm'),
```

- [ ] **Step 5: Run all the password-reset tests**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_password_reset.py -v
```

Expected: every test passes (target around 20 total in this file).

- [ ] **Step 6: Run `manage.py check` to catch wiring issues**

```
cd backend && source venv/bin/activate && python manage.py check
```

Expected: clean.

- [ ] **Step 7: Commit**

```
git add backend/accounts/views.py backend/accounts/urls.py backend/accounts/tests/test_password_reset.py
git commit -m "FEAT: password-reset views and routes (request/verify-code/confirm)"
```

---

## Task 7 — Frontend store extension

**Files:**
- Modify: `frontend/stores/platform-auth.js`
- Create: `frontend/test/stores/platform-auth.password-reset.spec.js`

- [ ] **Step 1: Write the failing store spec**

`frontend/test/stores/platform-auth.password-reset.spec.js`:

```js
import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, beforeEach, vi } from 'vitest'  // if the repo uses Jest, swap import to '@jest/globals' or just use jest globals.

// NOTE: project uses Jest, not Vitest. Replace the import line with:
//   import { describe, it, expect, beforeEach } from '@jest/globals'
// if Jest typings are missing; otherwise rely on globals.

import { usePlatformAuthStore } from '~/stores/platform-auth'

describe('platform-auth password reset state', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('starts with empty passwordReset slice', () => {
    const store = usePlatformAuthStore()
    expect(store.passwordReset).toEqual({
      email: null,
      requestToken: null,
      verifiedToken: null,
    })
  })

  it('startPasswordReset stores email + request token', () => {
    const store = usePlatformAuthStore()
    store.startPasswordReset({ email: 'a@b.co', requestToken: 'req-tok' })
    expect(store.passwordReset.email).toBe('a@b.co')
    expect(store.passwordReset.requestToken).toBe('req-tok')
    expect(store.passwordReset.verifiedToken).toBeNull()
  })

  it('markCodeVerified stores the verified token without losing email', () => {
    const store = usePlatformAuthStore()
    store.startPasswordReset({ email: 'a@b.co', requestToken: 'req-tok' })
    store.markCodeVerified({ verifiedToken: 'ver-tok' })
    expect(store.passwordReset).toEqual({
      email: 'a@b.co',
      requestToken: 'req-tok',
      verifiedToken: 'ver-tok',
    })
  })

  it('clearPasswordReset wipes all three fields', () => {
    const store = usePlatformAuthStore()
    store.startPasswordReset({ email: 'a@b.co', requestToken: 'req-tok' })
    store.markCodeVerified({ verifiedToken: 'ver-tok' })
    store.clearPasswordReset()
    expect(store.passwordReset).toEqual({
      email: null,
      requestToken: null,
      verifiedToken: null,
    })
  })

  it('logout also clears passwordReset', () => {
    const store = usePlatformAuthStore()
    store.startPasswordReset({ email: 'a@b.co', requestToken: 'req-tok' })
    store.logout()
    expect(store.passwordReset).toEqual({
      email: null,
      requestToken: null,
      verifiedToken: null,
    })
  })
})
```

**Note on test runner:** the project uses **Jest** (`frontend/jest.config.cjs`). If `vitest` is not installed, replace the first line with `// jest globals are used` (Jest exposes `describe/it/expect/beforeEach` globally). Drop the Vitest import.

- [ ] **Step 2: Run the spec to confirm it fails**

```
npm --prefix frontend test -- test/stores/platform-auth.password-reset.spec.js
```

Expected: error reading `store.passwordReset` (undefined) or "store.startPasswordReset is not a function".

- [ ] **Step 3: Extend `platform-auth.js`**

In `frontend/stores/platform-auth.js`:

1. Extend `initialState()` — add the slice:

   ```js
   function initialState() {
     return {
       user: null,
       accessToken: '',
       refreshToken: '',
       verificationToken: '',
       pendingEmail: '',
       isAuthenticated: false,
       role: '',
       isOnboarded: false,
       profileCompleted: false,
       isLoading: false,
       isVerifying: false,
       error: '',
       hasHydrated: false,
       hasValidatedSession: false,
       passwordReset: {
         email: null,
         requestToken: null,
         verifiedToken: null,
       },
     }
   }
   ```

2. Add three actions inside the `actions: {}` block (anywhere; group them near `clearVerificationState`):

   ```js
   startPasswordReset({ email, requestToken }) {
     this.passwordReset = {
       email: email || null,
       requestToken: requestToken || null,
       verifiedToken: null,
     }
   },

   markCodeVerified({ verifiedToken }) {
     this.passwordReset = {
       ...this.passwordReset,
       verifiedToken: verifiedToken || null,
     }
   },

   clearPasswordReset() {
     this.passwordReset = {
       email: null,
       requestToken: null,
       verifiedToken: null,
     }
   },
   ```

3. The existing `logout()` action calls `resetState()`, which reassigns from `initialState()`. Because `initialState()` now returns the empty `passwordReset` slice, logout already clears it — no extra wiring needed.

- [ ] **Step 4: Run the spec — confirm pass**

```
npm --prefix frontend test -- test/stores/platform-auth.password-reset.spec.js
```

Expected: all 5 tests pass.

- [ ] **Step 5: Commit**

```
git add frontend/stores/platform-auth.js frontend/test/stores/platform-auth.password-reset.spec.js
git commit -m "FEAT: platform-auth store — passwordReset state slice + start/markVerified/clear actions"
```

---

## Task 8 — Composable wrappers for the 3 endpoints (inside the store)

**Files:**
- Modify: `frontend/stores/platform-auth.js`

We keep `usePlatformApi.js` untouched (it already exposes a generic `post`) and add three new async actions on the store that call the endpoints and update state. This mirrors the existing `login()` / `verify()` / `resendCode()` actions.

- [ ] **Step 1: Append actions**

Inside `actions:` in `frontend/stores/platform-auth.js`, add (next to the password-reset actions from Task 7):

```js
async requestPasswordReset({ email }) {
  const trimmed = (email || '').trim().toLowerCase()
  if (!trimmed) {
    this.error = 'Ingresa tu email.'
    return { success: false, message: this.error }
  }
  this.isLoading = true
  this.error = ''
  try {
    const { post } = usePlatformApi()
    const response = await post(
      'password-reset/request/',
      { email: trimmed },
      { skipAuth: true, skipRefresh: true },
    )
    this.startPasswordReset({
      email: trimmed,
      requestToken: response.data.reset_request_token,
    })
    return { success: true }
  } catch (error) {
    const message = error.response?.data?.detail || 'No pudimos iniciar el flujo de recuperación.'
    this.error = message
    return { success: false, message }
  } finally {
    this.isLoading = false
  }
},

async verifyResetCode({ code }) {
  const value = `${code || ''}`.trim()
  if (!this.passwordReset.requestToken) {
    return { success: false, message: 'Empieza desde la página inicial de recuperación.' }
  }
  if (!/^\d{6}$/.test(value)) {
    this.error = 'Ingresa un código válido de 6 dígitos.'
    return { success: false, message: this.error }
  }
  this.isVerifying = true
  this.error = ''
  try {
    const { post } = usePlatformApi()
    const response = await post(
      'password-reset/verify-code/',
      { reset_request_token: this.passwordReset.requestToken, code: value },
      { skipAuth: true, skipRefresh: true },
    )
    this.markCodeVerified({ verifiedToken: response.data.reset_verified_token })
    return { success: true }
  } catch (error) {
    const data = error.response?.data || {}
    const message = data.detail || 'No pudimos verificar el código.'
    this.error = message
    return { success: false, message, code: data.detail, attemptsLeft: data.attempts_left }
  } finally {
    this.isVerifying = false
  }
},

async confirmPasswordReset({ newPassword }) {
  const value = newPassword || ''
  if (!this.passwordReset.verifiedToken) {
    return { success: false, message: 'Completa primero la verificación del código.' }
  }
  if (value.length < 8) {
    this.error = 'La contraseña debe tener al menos 8 caracteres.'
    return { success: false, message: this.error }
  }
  this.isLoading = true
  this.error = ''
  try {
    const { post } = usePlatformApi()
    const response = await post(
      'password-reset/confirm/',
      { reset_verified_token: this.passwordReset.verifiedToken, new_password: value },
      { skipAuth: true, skipRefresh: true },
    )
    const tokens = { access: response.data.access, refresh: response.data.refresh }
    this.applyAuthenticatedSession(tokens, response.data.user)
    this.clearPasswordReset()
    return { success: true, user: response.data.user }
  } catch (error) {
    const data = error.response?.data || {}
    const message = data.detail || 'No pudimos restablecer la contraseña.'
    this.error = message
    return { success: false, message, code: data.detail, errors: data.errors }
  } finally {
    this.isLoading = false
  }
},
```

- [ ] **Step 2: Spot-check imports**

The file already imports `usePlatformApi` from `~/composables/usePlatformApi`. No new imports are needed.

- [ ] **Step 3: Run the existing store spec to confirm no regression**

```
npm --prefix frontend test -- test/stores/platform-auth.password-reset.spec.js
```

Expected: all 5 still pass.

- [ ] **Step 4: Commit**

```
git add frontend/stores/platform-auth.js
git commit -m "FEAT: platform-auth store — request/verify/confirm async actions for password reset"
```

---

## Task 9 — Page: `forgot-password.vue`

**Files:**
- Create: `frontend/pages/platform/forgot-password.vue`
- Create: `frontend/test/pages/forgot-password.spec.js`

The visual style mirrors `frontend/pages/platform/login.vue` so the wizard feels continuous (same `BackgroundGradientAnimation` + white frosted card).

- [ ] **Step 1: Write a failing unit spec**

`frontend/test/pages/forgot-password.spec.js`:

```js
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import ForgotPasswordPage from '~/pages/platform/forgot-password.vue'

// Mock Nuxt composables the page uses.
const navigateToMock = jest.fn()
jest.mock('#app', () => ({
  navigateTo: (...args) => navigateToMock(...args),
  useLocalePath: () => (p) => p,
  useHead: () => {},
  definePageMeta: () => {},
}), { virtual: true })

describe('forgot-password page', () => {
  beforeEach(() => {
    navigateToMock.mockClear()
  })

  it('submits the email and navigates to verify-code on success', async () => {
    const wrapper = mount(ForgotPasswordPage, {
      global: {
        plugins: [createTestingPinia({
          createSpy: jest.fn,
          stubActions: false,
          initialState: { platformAuth: { passwordReset: { email: null, requestToken: null, verifiedToken: null } } },
        })],
      },
    })
    const store = (await import('~/stores/platform-auth')).usePlatformAuthStore()
    store.requestPasswordReset = jest.fn().mockResolvedValue({ success: true })

    await wrapper.find('input[type="email"]').setValue('user@example.com')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(store.requestPasswordReset).toHaveBeenCalledWith({ email: 'user@example.com' })
    expect(navigateToMock).toHaveBeenCalledWith('/platform/verify-code')
  })

  it('shows inline error when email is empty', async () => {
    const wrapper = mount(ForgotPasswordPage, {
      global: { plugins: [createTestingPinia({ createSpy: jest.fn })] },
    })
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(wrapper.text()).toMatch(/email/i)
  })
})
```

- [ ] **Step 2: Run spec — expect failure**

```
npm --prefix frontend test -- test/pages/forgot-password.spec.js
```

Expected: module not found / page does not exist.

- [ ] **Step 3: Implement the page**

`frontend/pages/platform/forgot-password.vue`:

```vue
<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12">
    <BackgroundGradientAnimation
      gradient-background-start="rgb(0, 41, 33)"
      gradient-background-end="rgb(0, 25, 20)"
      first-color="0, 120, 100"
      second-color="0, 80, 90"
      third-color="30, 80, 60"
      fourth-color="0, 60, 80"
      fifth-color="20, 100, 70"
      pointer-color="0, 100, 80"
      size="100%"
      blending-value="hard-light"
      :interactive="true"
      container-class-name="!w-full !h-full !absolute !inset-0"
    />
    <div class="relative z-10 w-full max-w-md">
      <div class="mb-10 text-center">
        <h1 class="font-bold text-2xl tracking-tight text-white">
          Project<span class="text-white/60">App.</span>
        </h1>
        <p class="mt-2 text-sm font-medium uppercase tracking-[0.25em] text-white/50">Recuperación</p>
      </div>

      <div class="rounded-3xl border border-white/[0.1] bg-white/95 p-8 shadow-2xl backdrop-blur-2xl">
        <h2 class="text-xl font-medium text-text-default">¿Olvidaste tu contraseña?</h2>
        <p class="mt-2 text-sm leading-6 text-green-light">
          Ingresa tu email y te enviaremos un código para restablecerla.
        </p>

        <div v-if="errorMessage" class="mt-6 rounded-2xl border border-red-500/20 bg-red-50 px-4 py-3 text-sm text-red-600">
          {{ errorMessage }}
        </div>

        <form class="mt-8 space-y-5" @submit.prevent="handleSubmit">
          <div>
            <label for="forgot-email" class="mb-2 block text-sm font-medium text-esmerald/70">Email</label>
            <input
              id="forgot-email"
              v-model="email"
              type="email"
              autocomplete="email"
              class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition placeholder:text-green-light/60 focus:border-border-default focus:ring-1 focus:ring-esmerald/10"
              placeholder="cliente@empresa.com"
            >
          </div>

          <button
            type="submit"
            class="w-full rounded-full bg-primary px-4 py-3 text-sm font-semibold text-white transition hover:bg-esmerald/90 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!canSubmit || authStore.isLoading"
          >
            {{ authStore.isLoading ? 'Enviando...' : 'Enviar código' }}
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-green-light">
          <NuxtLink :to="localePath('/platform/login')" class="underline">Volver al inicio de sesión</NuxtLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import BackgroundGradientAnimation from '~/components/ui/BackgroundGradientAnimation.vue'

definePageMeta({
  layout: false,
  middleware: ['platform-auth'],
})

useHead({ title: 'Recupera tu contraseña — ProjectApp' })

const authStore = usePlatformAuthStore()
const localePath = useLocalePath()

const email = ref('')
const localError = ref('')

const errorMessage = computed(() => localError.value || authStore.error)
const canSubmit = computed(() => Boolean(email.value.trim()))

async function handleSubmit() {
  localError.value = ''
  const trimmed = email.value.trim()
  if (!trimmed.includes('@')) {
    localError.value = 'Ingresa un email válido.'
    return
  }
  const result = await authStore.requestPasswordReset({ email: trimmed })
  if (!result.success) {
    localError.value = result.message
    return
  }
  await navigateTo(localePath('/platform/verify-code'))
}
</script>
```

- [ ] **Step 4: Run the spec — expect pass**

```
npm --prefix frontend test -- test/pages/forgot-password.spec.js
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```
git add frontend/pages/platform/forgot-password.vue frontend/test/pages/forgot-password.spec.js
git commit -m "FEAT: /platform/forgot-password page (step 1 of password recovery wizard)"
```

---

## Task 10 — Page: `verify-code.vue`

**Files:**
- Create: `frontend/pages/platform/verify-code.vue`
- Create: `frontend/test/pages/verify-code.spec.js`

- [ ] **Step 1: Write the failing spec**

`frontend/test/pages/verify-code.spec.js`:

```js
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import VerifyCodePage from '~/pages/platform/verify-code.vue'

const navigateToMock = jest.fn()
jest.mock('#app', () => ({
  navigateTo: (...args) => navigateToMock(...args),
  useLocalePath: () => (p) => p,
  useHead: () => {},
  definePageMeta: () => {},
}), { virtual: true })

describe('verify-code page', () => {
  beforeEach(() => { navigateToMock.mockClear() })

  it('redirects to forgot-password when no requestToken in store', async () => {
    mount(VerifyCodePage, {
      global: {
        plugins: [createTestingPinia({
          createSpy: jest.fn,
          initialState: { platformAuth: { passwordReset: { email: null, requestToken: null, verifiedToken: null } } },
        })],
      },
    })
    await flushPromises()
    expect(navigateToMock).toHaveBeenCalledWith('/platform/forgot-password')
  })

  it('shows attempts_left when verifyResetCode returns the error', async () => {
    const wrapper = mount(VerifyCodePage, {
      global: {
        plugins: [createTestingPinia({
          createSpy: jest.fn,
          stubActions: false,
          initialState: { platformAuth: { passwordReset: { email: 'a@b.co', requestToken: 'req-tok', verifiedToken: null } } },
        })],
      },
    })
    const store = (await import('~/stores/platform-auth')).usePlatformAuthStore()
    store.verifyResetCode = jest.fn().mockResolvedValue({ success: false, message: 'invalid_code', code: 'invalid_code', attemptsLeft: 3 })

    await wrapper.find('input[name="otp"]').setValue('000000')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(wrapper.text()).toMatch(/3 intentos/i)
  })
})
```

- [ ] **Step 2: Run — expect failure**

```
npm --prefix frontend test -- test/pages/verify-code.spec.js
```

- [ ] **Step 3: Implement the page**

`frontend/pages/platform/verify-code.vue`:

```vue
<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12">
    <BackgroundGradientAnimation
      gradient-background-start="rgb(0, 41, 33)"
      gradient-background-end="rgb(0, 25, 20)"
      first-color="0, 120, 100"
      second-color="0, 80, 90"
      third-color="30, 80, 60"
      fourth-color="0, 60, 80"
      fifth-color="20, 100, 70"
      pointer-color="0, 100, 80"
      size="100%"
      blending-value="hard-light"
      :interactive="true"
      container-class-name="!w-full !h-full !absolute !inset-0"
    />
    <div class="relative z-10 w-full max-w-md">
      <div class="mb-10 text-center">
        <h1 class="font-bold text-2xl tracking-tight text-white">
          Project<span class="text-white/60">App.</span>
        </h1>
        <p class="mt-2 text-sm font-medium uppercase tracking-[0.25em] text-white/50">Verificación</p>
      </div>
      <div class="rounded-3xl border border-white/[0.1] bg-white/95 p-8 shadow-2xl backdrop-blur-2xl">
        <h2 class="text-xl font-medium text-text-default">Ingresa el código</h2>
        <p class="mt-2 text-sm leading-6 text-green-light">
          Te enviamos un código de 6 dígitos a <strong>{{ authStore.passwordReset.email || 'tu email' }}</strong>.
        </p>
        <div v-if="errorMessage" class="mt-6 rounded-2xl border border-red-500/20 bg-red-50 px-4 py-3 text-sm text-red-600">
          {{ errorMessage }}
          <span v-if="attemptsLeft !== null"> Te quedan {{ attemptsLeft }} intentos.</span>
        </div>
        <form class="mt-8 space-y-5" @submit.prevent="handleSubmit">
          <div>
            <label for="otp" class="mb-2 block text-sm font-medium text-esmerald/70">Código</label>
            <input
              id="otp"
              name="otp"
              v-model="code"
              inputmode="numeric"
              maxlength="6"
              autocomplete="one-time-code"
              class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-center text-2xl tracking-[0.5em] text-text-default outline-none transition focus:border-border-default focus:ring-1 focus:ring-esmerald/10"
              placeholder="••••••"
            >
          </div>
          <button
            type="submit"
            class="w-full rounded-full bg-primary px-4 py-3 text-sm font-semibold text-white transition hover:bg-esmerald/90 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!canSubmit || authStore.isVerifying"
          >
            {{ authStore.isVerifying ? 'Verificando...' : 'Verificar' }}
          </button>
          <button
            type="button"
            class="w-full text-sm text-esmerald/70 underline transition disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="authStore.isLoading"
            @click="handleResend"
          >
            Reenviar código
          </button>
        </form>
        <p class="mt-6 text-center text-sm text-green-light">
          <NuxtLink :to="localePath('/platform/login')" class="underline">Volver al inicio de sesión</NuxtLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import BackgroundGradientAnimation from '~/components/ui/BackgroundGradientAnimation.vue'

definePageMeta({
  layout: false,
  middleware: ['platform-auth'],
})

useHead({ title: 'Verifica el código — ProjectApp' })

const authStore = usePlatformAuthStore()
const localePath = useLocalePath()
const code = ref('')
const localError = ref('')
const attemptsLeft = ref(null)

onMounted(() => {
  if (!authStore.passwordReset.requestToken) {
    navigateTo(localePath('/platform/forgot-password'))
  }
})

const errorMessage = computed(() => localError.value || authStore.error)
const canSubmit = computed(() => /^\d{6}$/.test(code.value.trim()))

async function handleSubmit() {
  localError.value = ''
  attemptsLeft.value = null
  const result = await authStore.verifyResetCode({ code: code.value.trim() })
  if (!result.success) {
    localError.value = result.message === 'invalid_code' ? 'Código incorrecto.' : result.message
    if (typeof result.attemptsLeft === 'number') attemptsLeft.value = result.attemptsLeft
    if (result.code === 'invalid_or_expired_token') {
      await navigateTo(localePath('/platform/forgot-password'))
    }
    return
  }
  await navigateTo(localePath('/platform/reset-password'))
}

async function handleResend() {
  if (!authStore.passwordReset.email) return
  await authStore.requestPasswordReset({ email: authStore.passwordReset.email })
}
</script>
```

- [ ] **Step 4: Run spec — expect pass**

```
npm --prefix frontend test -- test/pages/verify-code.spec.js
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```
git add frontend/pages/platform/verify-code.vue frontend/test/pages/verify-code.spec.js
git commit -m "FEAT: /platform/verify-code page (step 2 — OTP entry + resend)"
```

---

## Task 11 — Page: `reset-password.vue`

**Files:**
- Create: `frontend/pages/platform/reset-password.vue`
- Create: `frontend/test/pages/reset-password.spec.js`

- [ ] **Step 1: Write the failing spec**

`frontend/test/pages/reset-password.spec.js`:

```js
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import ResetPasswordPage from '~/pages/platform/reset-password.vue'

const navigateToMock = jest.fn()
jest.mock('#app', () => ({
  navigateTo: (...args) => navigateToMock(...args),
  useLocalePath: () => (p) => p,
  useHead: () => {},
  definePageMeta: () => {},
}), { virtual: true })

describe('reset-password page', () => {
  beforeEach(() => { navigateToMock.mockClear() })

  it('redirects to forgot-password when verifiedToken is missing', async () => {
    mount(ResetPasswordPage, {
      global: {
        plugins: [createTestingPinia({
          createSpy: jest.fn,
          initialState: { platformAuth: { passwordReset: { email: 'a@b.co', requestToken: 'req-tok', verifiedToken: null } } },
        })],
      },
    })
    await flushPromises()
    expect(navigateToMock).toHaveBeenCalledWith('/platform/forgot-password')
  })

  it('shows password-validation errors from the backend', async () => {
    const wrapper = mount(ResetPasswordPage, {
      global: {
        plugins: [createTestingPinia({
          createSpy: jest.fn,
          stubActions: false,
          initialState: { platformAuth: { passwordReset: { email: 'a@b.co', requestToken: 'req-tok', verifiedToken: 'ver-tok' } } },
        })],
      },
    })
    const store = (await import('~/stores/platform-auth')).usePlatformAuthStore()
    store.confirmPasswordReset = jest.fn().mockResolvedValue({
      success: false, message: 'weak_password', code: 'weak_password',
      errors: ['Esta contraseña es muy común', 'Debe contener letras y números'],
    })

    await wrapper.find('input[type="password"]').setValue('weakpass')
    await wrapper.findAll('input[type="password"]')[1].setValue('weakpass')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(wrapper.text()).toContain('Esta contraseña es muy común')
  })

  it('navigates to /platform on success', async () => {
    const wrapper = mount(ResetPasswordPage, {
      global: {
        plugins: [createTestingPinia({
          createSpy: jest.fn,
          stubActions: false,
          initialState: { platformAuth: { passwordReset: { email: 'a@b.co', requestToken: 'req-tok', verifiedToken: 'ver-tok' } } },
        })],
      },
    })
    const store = (await import('~/stores/platform-auth')).usePlatformAuthStore()
    store.confirmPasswordReset = jest.fn().mockResolvedValue({ success: true, user: { email: 'a@b.co' } })

    await wrapper.find('input[type="password"]').setValue('NewStrongPass456!')
    await wrapper.findAll('input[type="password"]')[1].setValue('NewStrongPass456!')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(navigateToMock).toHaveBeenCalledWith('/platform')
  })
})
```

- [ ] **Step 2: Run — expect failure**

```
npm --prefix frontend test -- test/pages/reset-password.spec.js
```

- [ ] **Step 3: Implement the page**

`frontend/pages/platform/reset-password.vue`:

```vue
<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12">
    <BackgroundGradientAnimation
      gradient-background-start="rgb(0, 41, 33)"
      gradient-background-end="rgb(0, 25, 20)"
      first-color="0, 120, 100"
      second-color="0, 80, 90"
      third-color="30, 80, 60"
      fourth-color="0, 60, 80"
      fifth-color="20, 100, 70"
      pointer-color="0, 100, 80"
      size="100%"
      blending-value="hard-light"
      :interactive="true"
      container-class-name="!w-full !h-full !absolute !inset-0"
    />
    <div class="relative z-10 w-full max-w-md">
      <div class="mb-10 text-center">
        <h1 class="font-bold text-2xl tracking-tight text-white">
          Project<span class="text-white/60">App.</span>
        </h1>
        <p class="mt-2 text-sm font-medium uppercase tracking-[0.25em] text-white/50">Nueva contraseña</p>
      </div>
      <div class="rounded-3xl border border-white/[0.1] bg-white/95 p-8 shadow-2xl backdrop-blur-2xl">
        <h2 class="text-xl font-medium text-text-default">Define tu nueva contraseña</h2>
        <p class="mt-2 text-sm leading-6 text-green-light">
          Al guardar quedarás conectado a la plataforma automáticamente.
        </p>

        <div v-if="errorMessage" class="mt-6 rounded-2xl border border-red-500/20 bg-red-50 px-4 py-3 text-sm text-red-600">
          {{ errorMessage }}
          <ul v-if="errorList.length" class="mt-2 list-disc space-y-1 pl-4">
            <li v-for="(err, i) in errorList" :key="i">{{ err }}</li>
          </ul>
        </div>

        <form class="mt-8 space-y-5" @submit.prevent="handleSubmit">
          <div>
            <label for="new-pass" class="mb-2 block text-sm font-medium text-esmerald/70">Nueva contraseña</label>
            <input
              id="new-pass"
              v-model="newPassword"
              type="password"
              autocomplete="new-password"
              minlength="8"
              class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition placeholder:text-green-light/60 focus:border-border-default focus:ring-1 focus:ring-esmerald/10"
              placeholder="Mínimo 8 caracteres"
            >
          </div>
          <div>
            <label for="confirm-pass" class="mb-2 block text-sm font-medium text-esmerald/70">Confirmar contraseña</label>
            <input
              id="confirm-pass"
              v-model="confirm"
              type="password"
              autocomplete="new-password"
              minlength="8"
              class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition placeholder:text-green-light/60 focus:border-border-default focus:ring-1 focus:ring-esmerald/10"
              placeholder="Repite la contraseña"
            >
          </div>
          <button
            type="submit"
            class="w-full rounded-full bg-primary px-4 py-3 text-sm font-semibold text-white transition hover:bg-esmerald/90 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!canSubmit || authStore.isLoading"
          >
            {{ authStore.isLoading ? 'Guardando...' : 'Guardar contraseña' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import BackgroundGradientAnimation from '~/components/ui/BackgroundGradientAnimation.vue'

definePageMeta({
  layout: false,
  middleware: ['platform-auth'],
})

useHead({ title: 'Restablece tu contraseña — ProjectApp' })

const authStore = usePlatformAuthStore()
const localePath = useLocalePath()
const newPassword = ref('')
const confirm = ref('')
const localError = ref('')
const errorList = ref([])

onMounted(() => {
  if (!authStore.passwordReset.verifiedToken) {
    navigateTo(localePath('/platform/forgot-password'))
  }
})

const errorMessage = computed(() => localError.value || authStore.error)
const canSubmit = computed(() => newPassword.value.length >= 8 && newPassword.value === confirm.value)

async function handleSubmit() {
  localError.value = ''
  errorList.value = []
  if (newPassword.value !== confirm.value) {
    localError.value = 'Las contraseñas no coinciden.'
    return
  }
  const result = await authStore.confirmPasswordReset({ newPassword: newPassword.value })
  if (!result.success) {
    localError.value = result.code === 'weak_password' ? 'La contraseña no cumple los requisitos.' : result.message
    if (Array.isArray(result.errors)) errorList.value = result.errors
    if (result.code === 'invalid_or_expired_token') {
      await navigateTo(localePath('/platform/forgot-password'))
    }
    return
  }
  await navigateTo(localePath('/platform'))
}
</script>
```

- [ ] **Step 4: Run spec — expect pass**

```
npm --prefix frontend test -- test/pages/reset-password.spec.js
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```
git add frontend/pages/platform/reset-password.vue frontend/test/pages/reset-password.spec.js
git commit -m "FEAT: /platform/reset-password page (step 3 — new password + auto-login)"
```

---

## Task 12 — Add "¿Olvidaste tu contraseña?" link on login

**Files:**
- Modify: `frontend/pages/platform/login.vue`

This is a copy-only edit (no test changes). The change is tiny enough that a regression run of the existing login spec is the verification.

- [ ] **Step 1: Insert the link**

In `frontend/pages/platform/login.vue`, locate the closing `</form>` (around the existing submit button) and add a small footer block immediately **after** the `</form>`:

Before (existing line ~75):

```html
          <button type="submit" ...>
            {{ authStore.isLoading ? 'Ingresando...' : 'Iniciar sesión' }}
          </button>
        </form>
      </div>
```

After:

```html
          <button type="submit" ...>
            {{ authStore.isLoading ? 'Ingresando...' : 'Iniciar sesión' }}
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-green-light">
          <NuxtLink :to="localePath('/platform/forgot-password')" class="underline">¿Olvidaste tu contraseña?</NuxtLink>
        </p>
      </div>
```

`localePath` is already available in the script setup (see existing `localePath` usage in `handleSubmit`). If it is only declared inside `handleSubmit`, lift the `const localePath = useLocalePath()` to the top of the `<script setup>` (just below the `const authStore = ...` line) so the template can use it.

- [ ] **Step 2: Run the existing login spec**

```
npm --prefix frontend test -- e2e/platform/platform-login.spec.js
```

(That path is the E2E spec, not a unit spec — there may be no unit spec for `login.vue`. If none exists, skip this step.)

Then run:

```
cd backend && source venv/bin/activate && python -c "from django.template.loader import get_template; import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','projectapp.settings'); django.setup(); print('OK')"
```

(Just sanity — backend should not be affected at all.)

- [ ] **Step 3: Commit**

```
git add frontend/pages/platform/login.vue
git commit -m "FEAT: forgot-password link on /platform/login"
```

---

## Task 13 — End-to-end Playwright spec

**Files:**
- Create: `frontend/e2e/platform/platform-password-reset.spec.js`

The E2E spec mocks the three new endpoints with `page.route()` so we never depend on SMTP or a populated database.

- [ ] **Step 1: Create the spec**

`frontend/e2e/platform/platform-password-reset.spec.js`:

```js
import { test, expect } from '@playwright/test'

test.setTimeout(60_000)

test.describe('platform password recovery', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/accounts/password-reset/request/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ reset_request_token: 'mock-request-token' }),
      })
    })
  })

  test('happy path — login link to forgot, code accepted, new password accepted, redirect to /platform', async ({ page }) => {
    await page.route('**/api/accounts/password-reset/verify-code/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ reset_verified_token: 'mock-verified-token' }),
      })
    })
    await page.route('**/api/accounts/password-reset/confirm/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access: 'mock-access',
          refresh: 'mock-refresh',
          user: { email: 'user@example.com', role: 'client', is_onboarded: true, profile_completed: true },
        }),
      })
    })
    // Mock the /me/ call the dashboard layout might hit.
    await page.route('**/api/accounts/me/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ email: 'user@example.com', role: 'client', is_onboarded: true, profile_completed: true }),
      })
    })

    await page.goto('/es-co/platform/login', { waitUntil: 'domcontentloaded' })
    await expect(page.getByRole('link', { name: /Olvidaste tu contraseña/i })).toBeVisible({ timeout: 10000 })
    await page.getByRole('link', { name: /Olvidaste tu contraseña/i }).click()

    await page.waitForURL(/\/platform\/forgot-password/, { waitUntil: 'domcontentloaded' })
    await page.locator('input[type="email"]').fill('user@example.com')
    await page.locator('button[type="submit"]').click()

    await page.waitForURL(/\/platform\/verify-code/, { waitUntil: 'domcontentloaded' })
    await page.locator('input[name="otp"]').fill('123456')
    await page.locator('button[type="submit"]').click()

    await page.waitForURL(/\/platform\/reset-password/, { waitUntil: 'domcontentloaded' })
    await page.locator('#new-pass').fill('NewStrongPass456!')
    await page.locator('#confirm-pass').fill('NewStrongPass456!')
    await page.locator('button[type="submit"]').click()

    await page.waitForURL(/\/platform(\?|$|\/)/, { waitUntil: 'domcontentloaded' })
  })

  test('wrong code surfaces attempts_left and stays on verify-code', async ({ page }) => {
    await page.route('**/api/accounts/password-reset/verify-code/', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'invalid_code', attempts_left: 3 }),
      })
    })

    await page.goto('/es-co/platform/forgot-password', { waitUntil: 'domcontentloaded' })
    await page.locator('input[type="email"]').fill('user@example.com')
    await page.locator('button[type="submit"]').click()
    await page.waitForURL(/\/platform\/verify-code/, { waitUntil: 'domcontentloaded' })

    await page.locator('input[name="otp"]').fill('000000')
    await page.locator('button[type="submit"]').click()

    await expect(page.getByText(/3 intentos/i)).toBeVisible({ timeout: 10000 })
    expect(page.url()).toContain('/platform/verify-code')
  })
})
```

- [ ] **Step 2: Run the spec**

Make sure both dev servers are running (host-only setup from earlier task):
- Backend at `0.0.0.0:8000`
- Frontend at `0.0.0.0:3000` with `.env_development`

Then:

```
npm --prefix frontend run e2e -- frontend/e2e/platform/platform-password-reset.spec.js
```

Expected: 2 passed.

- [ ] **Step 3: Commit**

```
git add frontend/e2e/platform/platform-password-reset.spec.js
git commit -m "FEAT: E2E coverage for /platform password recovery (happy path + wrong-code)"
```

---

## Task 14 — Manual smoke test on host-only network

**Files:** none

This is the final verification — the kind of feature check that test suites do not catch.

- [ ] **Step 1: Confirm both servers are running**

```
ss -ltnp 2>/dev/null | grep -E ':(3000|8000)\b'
```

Expected: two `LISTEN` lines on `0.0.0.0`.

- [ ] **Step 2: Open the login page from the host browser**

`http://192.168.56.10:3000/es-co/platform/login`

Expected: see the green gradient login card with the new "¿Olvidaste tu contraseña?" link at the bottom.

- [ ] **Step 3: Walk the full flow with a real test user**

You need an existing platform user. Create one via the Django shell if you don't have one ready:

```
cd backend && source venv/bin/activate && python manage.py shell -c "from django.contrib.auth import get_user_model; from accounts.models import UserProfile; U = get_user_model(); u, _ = U.objects.get_or_create(username='test@example.com', defaults={'email':'test@example.com'}); u.set_password('OldPass123!'); u.save(); UserProfile.objects.get_or_create(user=u, defaults={'role':'client','is_onboarded':True,'profile_completed':True}); print('ready')"
```

Then in the browser:

1. Click `¿Olvidaste tu contraseña?` → lands on `/platform/forgot-password`.
2. Enter `test@example.com`, submit → lands on `/platform/verify-code`.
3. The OTP email goes to console (dev EmailBackend). Run:
   ```
   cd backend && source venv/bin/activate && python manage.py shell -c "from accounts.models import VerificationCode; print(VerificationCode.objects.latest('created_at').code)"
   ```
   Take the 6-digit code from the output.
4. Enter the code → lands on `/platform/reset-password`.
5. Enter `NewStrongPass456!` twice → lands on `/platform`.

Expected: end-to-end flow succeeds and the user is signed in.

- [ ] **Step 4: Verify the confirmation email was rendered**

In the terminal running the backend `runserver`, scroll up — you should see the second email body containing "Tu contraseña fue restablecida".

- [ ] **Step 5: No commit (manual verification only)**

If everything passes, the feature is ready for review/PR.

---

## Self-review

**Spec coverage:**

| Spec section | Implemented by |
|---|---|
| §3.1 endpoints | Task 6 |
| §3.2 JWT claims | Task 1 |
| §3.3 frontend routes | Tasks 9–11 |
| §3.4 reuse (template tweak) | Task 3 |
| §4.1 backend components | Tasks 1, 3, 4, 5, 6 |
| §4.2 frontend components (minus i18n — see deviation) | Tasks 7, 8, 9, 10, 11, 12 |
| §5 data flow | Tasks 6 (backend), 7–11 (frontend) |
| §6 error matrix | Tasks 4 (service), 6 (views), 7–11 (UI handling) |
| §7 logging | Task 4 |
| §8 security notes | Tasks 1, 4 |
| §9.1 backend tests (15) | Tasks 1 (7), 3 (2), 4 (12), 6 (7) — ~28 total when summed; deliberate over-coverage |
| §9.2 frontend unit (4) | Tasks 7, 9, 10, 11 |
| §9.3 frontend E2E (2) | Task 13 |
| §10 out-of-scope | Respected (no JWT blacklist, no IP throttle, no captcha, no admin-side force-reset, no logged-in change-password) |
| §11 release | Task 14 (manual smoke) + the no-migration property is enforced by construction (the plan never adds a model field) |

**Placeholder scan:** none. Every step has the actual file path, the actual code, or the actual command to run.

**Type consistency check:** the function names, claim names (`purpose`, `user_id`), and action names (`startPasswordReset`, `markCodeVerified`, `clearPasswordReset`, `requestPasswordReset`, `verifyResetCode`, `confirmPasswordReset`) are consistent across tasks. The error code strings (`invalid_code`, `code_expired`, `too_many_attempts`, `invalid_or_expired_token`, `weak_password`) are consistent across service, views, and UI.

**Scope check:** focused enough for one implementation cycle. No sub-projects.

**Ambiguity check:** the only "either error is acceptable" branch is in `test_verify_with_expired_code_returns_code_expired` (the OTP and the request token both have 10-minute lifetimes, so either can be the one that fails first at +11min). The test explicitly accepts both — documented inline.
