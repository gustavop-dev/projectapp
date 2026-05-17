# Platform Password Recovery — Design Spec

- **Status:** Approved (pending implementation plan)
- **Date:** 2026-05-16
- **Surface:** `/platform/*` (JWT auth via SimpleJWT, app `accounts`)
- **Branch:** `feat/16052026-platform-password-recovery`

## 1. Goal

Let a platform user who forgot their password regain access through an
email-delivered 6-digit code, mirroring the existing onboarding/verification
flow. No schema changes. No impact on production deployments.

## 2. Decisions (from brainstorming)

| Topic | Decision |
|---|---|
| UI flow | 3-step wizard (request email → verify code → set new password) |
| Email disclosure | Generic response in step 1 (no enumeration of registered accounts) |
| Post-reset UX | Auto-login + redirect to `/platform` |
| Anti-abuse | 60-second cooldown per email on step 1 |
| State machine | JWTs with `purpose` claim between steps (no DB migration) |
| Post-reset confirmation email | Yes — included in scope |
| Invalidate other JWT sessions | No (out of scope) |
| Rate-limit by IP | No (out of scope) |
| Captcha on forgot-password | No (out of scope) |

## 3. Architecture

### 3.1 Backend endpoints (new, all under `accounts/`)

| Method | Route | Body | Response |
|---|---|---|---|
| POST | `/api/accounts/password-reset/request/` | `{ email }` | 200 `{ reset_request_token }` (always 200 — decoy token returned when the email does not exist) |
| POST | `/api/accounts/password-reset/verify-code/` | `{ reset_request_token, code }` | 200 `{ reset_verified_token }` |
| POST | `/api/accounts/password-reset/confirm/` | `{ reset_verified_token, new_password }` | 200 `{ access, refresh, user }` (same shape as login) |

### 3.2 JWT claims

- `reset_request_token`
  - `purpose='password_reset_request'`, `user_id` (or `null` for decoys), `exp=now+10min`
- `reset_verified_token`
  - `purpose='password_reset_verified'`, `user_id`, `exp=now+5min`
- Both signed with the same `SECRET_KEY` as SimpleJWT. The `purpose` claim is
  the only thing preventing cross-step token reuse, so the decoder must
  reject mismatches.

### 3.3 Frontend routes (new)

- `frontend/pages/platform/forgot-password.vue` — step 1
- `frontend/pages/platform/verify-code.vue` — step 2
- `frontend/pages/platform/reset-password.vue` — step 3
- Update `frontend/pages/platform/login.vue` to render an
  `¿Olvidaste tu contraseña?` link that navigates to step 1.

### 3.4 Reuse (no changes)

- `accounts.models.VerificationCode` (already exposes `PURPOSE_PASSWORD_RESET`).
- `accounts.services.verification.create_and_send_otp(user, purpose)`
  (already accepts a purpose argument).
- `accounts.services.tokens.get_tokens_for_user(user)` for the final login
  payload.
- Email template `content/templates/emails/verification_code.html` for the
  6-digit code, **with a small tweak**: the helper will pick a different
  HTML/TXT pair based on `purpose` so onboarding copy doesn't leak into reset
  copy.

## 4. Components

### 4.1 Backend

`backend/accounts/services/tokens.py` — extend with:

```python
def get_password_reset_request_token(user) -> str
def get_password_reset_verified_token(user) -> str
def get_decoy_password_reset_request_token() -> str
def decode_password_reset_token(token: str, expected_purpose: str) -> dict
```

The decoder is the single place that enforces `purpose` matching and
expiration, so each view stays a one-liner.

`backend/accounts/services/password_reset.py` — **new file**, business
logic. Three public functions:

```python
def request_password_reset(email: str) -> str:
    """Always returns a request token. Sends an OTP only when the user exists
    and no other code was created in the last 60 seconds.
    """

def verify_reset_code(request_token: str, code: str) -> str:
    """Returns a verified token. Raises VerificationFailed for decoy tokens,
    invalid codes, expired codes, or too many attempts."""

def confirm_password_reset(verified_token: str, new_password: str) -> dict:
    """Validates the new password against AUTH_PASSWORD_VALIDATORS, sets it,
    fires send_password_changed_notification(user) best-effort, and returns
    {access, refresh, user}."""
```

`backend/accounts/services/password_reset.py` also owns:

```python
def send_password_changed_notification(user) -> None:
    """Renders password_reset_completed.{html,txt} and sends it.
    Failure is logged at WARNING and swallowed — the password change is
    already committed and we do not roll back on email errors."""
```

`backend/accounts/views.py` — three thin function-based DRF views:

```python
@api_view(['POST'])
def password_reset_request_view(request): ...
@api_view(['POST'])
def password_reset_verify_view(request): ...
@api_view(['POST'])
def password_reset_confirm_view(request): ...
```

Each parses the payload through a serializer, calls the service, and maps
service exceptions to HTTP responses. Same shape as `verify_view`.

`backend/accounts/serializers.py` — three new input serializers
(`PasswordResetRequestSerializer`, `PasswordResetVerifyCodeSerializer`,
`PasswordResetConfirmSerializer`). The confirm serializer runs the new
password through `django.contrib.auth.password_validation.validate_password`
and surfaces the validator messages.

`backend/accounts/urls.py` — three new entries grouped under
`password-reset/`.

`backend/content/templates/emails/` — new pair
`password_reset_code.html` + `.txt` (used by `create_and_send_otp` when
`purpose=PASSWORD_RESET`) and `password_reset_completed.html` + `.txt`
(post-reset confirmation; subject `"Se restableció la contraseña de tu
cuenta"` / `"Your password was reset"`; body includes UTC timestamp and a
"si no fuiste tú, contacta team@projectapp.co" line).

`backend/accounts/services/verification.py` — small change: pick the
template pair from a mapping keyed by `purpose` instead of hard-coding
`verification_code.html`.

### 4.2 Frontend

`frontend/stores/platform-auth.js` — add to `state`:

```js
passwordReset: {
  email: null,         // displayed in steps 2 and 3
  requestToken: null,  // step 1 → step 2
  verifiedToken: null, // step 2 → step 3
}
```

Actions: `startPasswordReset({email, requestToken})`,
`markCodeVerified({verifiedToken})`, `clearPasswordReset()`. **Memory only**
— no `localStorage` persistence, so a page refresh resets the wizard.

`frontend/composables/usePlatformApi.js` — three wrappers
(`requestPasswordReset`, `verifyResetCode`, `confirmPasswordReset`). They
reuse the existing Axios instance without auth headers since these
endpoints are public.

`frontend/pages/platform/forgot-password.vue` — `BaseInput` (email) +
`BaseButton`. On success: store the email + request token, navigate to
`verify-code`.

`frontend/pages/platform/verify-code.vue` — numeric OTP input (single
`BaseInput inputmode="numeric"` with length 6 is enough for MVP).
Server-driven error display, including `attempts_left`. Has a
`Reenviar código` link that re-calls
`requestPasswordReset(stored email)`. If `requestToken` is missing in
the store, redirects to `forgot-password`.

`frontend/pages/platform/reset-password.vue` — `BaseInput` password +
confirm. On success: receive the auth payload, call
`applyAuthenticatedSession(payload)`, `clearPasswordReset()`,
`navigateTo('/platform')`. If `verifiedToken` is missing, redirects to
`forgot-password`.

`frontend/pages/platform/login.vue` — append a `¿Olvidaste tu contraseña?`
link below the password input that points to `/platform/forgot-password`.

`frontend/locales/global/{es,en}.js` — new strings under
`platform.passwordReset.*`. English copy can be a literal translation for
MVP, flagged with `// TODO: review copy`.

## 5. Data flow

```
Login.vue ──"olvidé"──▶ Forgot.vue ──POST /request──▶ accounts API
                                                          │
                                                          ├ exists ? create OTP + send mail (unless <60s cooldown)
                                                          └ always returns reset_request_token
Forgot.vue ──store.startPasswordReset─▶ Verify.vue ──POST /verify-code──▶ accounts API
                                                          │
                                                          ├ decode request token
                                                          ├ check VerificationCode
                                                          └ returns reset_verified_token
Verify.vue ──store.markCodeVerified──▶ Reset.vue ──POST /confirm──▶ accounts API
                                                          │
                                                          ├ decode verified token
                                                          ├ validate password
                                                          ├ user.set_password() + user.save()
                                                          ├ send_password_changed_notification(user)   (best effort)
                                                          └ returns {access, refresh, user}
Reset.vue ──applyAuthenticatedSession──▶ /platform
```

## 6. Error matrix

| Step | Scenario | Backend response | Frontend behavior |
|---|---|---|---|
| 1 | malformed email | 400 `{detail: 'invalid_email'}` | inline error |
| 1 | email not registered | 200 + decoy token | proceeds to step 2; fails there with the generic invalid_code message |
| 1 | within 60s cooldown | 200 + token (no new mail) | indistinguishable from happy path; debug log on backend |
| 2 | expired or wrong-purpose token | 401 `{detail: 'invalid_or_expired_token'}` | redirect to forgot-password with toast |
| 2 | wrong code, attempts<5 | 400 `{detail: 'invalid_code', attempts_left: N}` | inline error with remaining attempts |
| 2 | wrong code, attempts=5 | 400 `{detail: 'too_many_attempts'}` | banner + button to step 1 |
| 2 | code expired (>10 min) | 400 `{detail: 'code_expired'}` | banner + button to step 1 |
| 2 | decoy token | 400 `{detail: 'invalid_code'}` (same as the real failure) | inline error |
| 3 | expired or wrong-purpose token | 401 `{detail: 'invalid_or_expired_token'}` | redirect to forgot-password |
| 3 | weak password | 400 `{detail: 'weak_password', errors: [...]}` | list of reasons under the input |
| 3 | success | 200 `{access, refresh, user}` | toast + navigate to /platform |

## 7. Logging

`accounts.services.password_reset` logger, INFO level. Events:

- `password_reset_requested(email_hash=…, user_found=bool, cooldown_hit=bool)`
- `password_reset_code_verified(user_id=…)`
- `password_reset_completed(user_id=…)`
- `password_reset_email_failure(user_id=…, reason=…)` (WARNING)

`email_hash` is a SHA-256 of the email truncated to 12 chars so logs can be
correlated without storing PII in plain text.

## 8. Security notes

- `purpose` claim distinct per step ⇒ a `request_token` cannot reach
  `/confirm`.
- Decoy tokens have `user_id=None` ⇒ step 2 fails with the generic
  `invalid_code` response, indistinguishable from a real wrong code.
- `VerificationCode` auto-invalidates previous unused codes on creation and
  limits each code to 5 attempts.
- `user.set_password()` re-hashes with the configured Django hasher.
- Existing JWT sessions on other devices are **not** invalidated. Documented
  as out of scope.
- Timing-attack note: in the decoy branch we **accept** a small timing
  differential rather than introducing artificial sleeps. The diff is
  typically <50ms and is not practically exploitable for the threat model of
  a small platform.

## 9. Testing

### 9.1 Backend (`backend/accounts/tests/test_password_reset.py`, new)

| Test | Verifies |
|---|---|
| `test_request_with_existing_email_creates_code_and_sends_email` | VerificationCode(PASSWORD_RESET) created, `mail.outbox` len=1, subject contains code marker, returns request_token |
| `test_request_with_nonexistent_email_returns_decoy_token` | 200, request_token returned, no VerificationCode, no email |
| `test_request_cooldown_skips_resend` | two requests <60s ⇒ only one email; second still returns a token |
| `test_request_cooldown_lapsed_resends` | freezegun +61s ⇒ second email is sent |
| `test_verify_with_valid_code_returns_verified_token` | decoded token has `purpose='password_reset_verified'` and the right `user_id` |
| `test_verify_with_wrong_code_decrements_attempts` | `attempts_left` decreases, code still active |
| `test_verify_with_wrong_code_5_times_returns_too_many_attempts` | fifth attempt ⇒ 400 `too_many_attempts` |
| `test_verify_with_expired_code_returns_code_expired` | freezegun +11min ⇒ 400 `code_expired` |
| `test_verify_with_decoy_token_returns_invalid_code` | same generic message |
| `test_verify_rejects_wrong_purpose_token` | passing an access token or a verified token to verify ⇒ 401 |
| `test_confirm_with_valid_token_sets_new_password_and_returns_jwt` | `user.check_password(new)` is True, response shape matches login |
| `test_confirm_with_weak_password_returns_validation_errors` | weak password ⇒ 400 + validator messages |
| `test_confirm_rejects_request_token_used_as_verified` | request_token at `/confirm` ⇒ 401 |
| `test_confirm_sends_confirmation_email_to_user` | `mail.outbox[-1]` subject and recipient match the user |
| `test_full_flow_end_to_end` | request → verify → confirm → login with new password works |

15 tests, in one file. Fits the repo's 20-per-batch testing rule.

### 9.2 Frontend unit

| Spec | Verifies |
|---|---|
| `stores/platform-auth.password-reset.spec.js` | actions mutate state correctly; `clearPasswordReset` wipes all three fields |
| `pages/platform/forgot-password.spec.js` | valid submit calls API + stores tokens + navigates; empty email shows inline error |
| `pages/platform/verify-code.spec.js` | missing requestToken ⇒ redirect; wrong code shows `attempts_left`; resend calls API |
| `pages/platform/reset-password.spec.js` | missing verifiedToken ⇒ redirect; weak password shows errors; success clears store + sets JWT + navigates |

### 9.3 Frontend E2E (`frontend/e2e/platform/platform-password-reset.spec.js`, new)

Two tests, both mock `/request/`, `/verify-code/`, `/confirm/` via
`page.route()` so the SMTP layer never runs in CI:

- **happy path with mocked email** — login → "olvidé" → forgot-password →
  email → verify-code → code → reset-password → new password → reaches
  `/platform` authenticated.
- **wrong code shows attempts left and recoverable** — second step mock
  returns `attempts_left: 3`; UI surfaces it; next mock returns success and
  the flow continues.

Per repo rules: no `networkidle` waits; use `domcontentloaded` plus
`expect(...).toBeVisible({timeout: 10000})`; keep `test.setTimeout(60_000)`.

## 10. Out of scope

- Invalidating active JWT sessions on other devices when password changes.
  (No `SimpleJWT` blacklist app installed today.)
- Rate-limit per IP via DRF throttles.
- reCAPTCHA on `forgot-password`.
- Admin-side "force password reset for user X".
- Password-change endpoint for users who are already logged in (different
  flow, different endpoint).

## 11. Release

- No database migrations.
- No changes to `settings.py` or `settings_prod.py`.
- Backend deploy: restart `projectapp.service` after pulling the new code.
- Frontend deploy: rebuild via the standard Nuxt build pipeline.
- No feature flag — the new pages are unreachable until the
  `forgot-password` link lands in `login.vue`; toggling that line gives a
  manual rollout switch.
- Update `tasks/active_context.md` with one line announcing the flow once
  merged.

## 12. Final scope summary

- **Backend:** 3 views, 1 new service file, 3 new token helpers + 1 shared
  decoder, 3 new serializers, 1 template-selection tweak in
  `verification.py`, 2 new email-template pairs, 1 new test file with 15
  tests.
- **Frontend:** 3 new pages, store extension (3 actions + 1 state slice), 3
  new composable wrappers, i18n strings × 2 locales, 1 link in `login.vue`,
  4 new unit specs, 1 new E2E spec with 2 cases.
- **No** DB migrations. **No** changes to base settings. **No** prod
  configuration changes.
