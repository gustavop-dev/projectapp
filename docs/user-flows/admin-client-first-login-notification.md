### FLOW: `admin-client-first-login-notification`

- **Module:** admin
- **Role:** system
- **Priority:** P2
- **Trigger:** `POST /api/accounts/verify/` (first-time onboarding, `was_onboarded == False`)
- **Description:** On a client's first platform login (password set), `client_flow_notifications` fires a team milestone alert: an in-app notification to the project admins plus an email to the notification recipients. Best-effort; never blocks onboarding; fires only on the first login.
- **Coverage:** ⚠️ Backend-only
- **Evidence:** Backend service `accounts/services/client_flow_notifications.py` (out of browser-E2E scope; may be asserted as a branch of `platform-verify-onboarding`).
