### FLOW: `admin-impersonate-user`

- **Module:** admin
- **Role:** admin (superuser only)
- **Priority:** P2
- **Routes:** `/panel/admins/` (or Django `/admin/` user page) → `/platform/admin-login` → `/platform/dashboard`
- **Description:** A superuser starts an impersonation session ("Login with this user") to access the platform as the target user for support/QA.
- **Steps:**
  1. Superuser opens `/panel/admins/` and clicks "Login with this user" on a user row (or opens the Django admin user page and clicks the "Log in as this user" button).
  2. Backend `POST /api/accounts/admins/<id>/login-as/` (or the admin `login_as` view) validates the policy, mints JWT tokens, and stores them behind a short-lived single-use exchange code.
  3. A new tab opens `/platform/admin-login?code=...&redirect=/platform` (no tokens on the URL).
  4. The callback page POSTs the code to `POST /api/accounts/impersonation/exchange/`, receives the tokens, and hydrates the session (`GET /api/accounts/me/`).
  5. User lands authenticated on `/platform/dashboard` as the impersonated user.
- **Security:** only active superusers; cannot impersonate another superuser; cannot impersonate inactive users; target must have a platform profile.
- **Coverage:** ⚠️ Pending (registered, E2E spec not yet implemented)
- **E2E Spec:** _suggested:_ `e2e/admin/admin-impersonate-user.spec.js`
