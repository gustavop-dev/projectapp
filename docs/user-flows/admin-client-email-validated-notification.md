### FLOW: `admin-client-email-validated-notification`

- **Module:** admin
- **Role:** system
- **Priority:** P2
- **Trigger:** `POST /api/accounts/email/verify/confirm/`
- **Description:** When a client confirms their email OTP from the documents portal, `client_flow_notifications` fires a team milestone alert (in-app to project admins + email). Best-effort; already-verified confirmations do not re-notify.
- **Coverage:** ⚠️ Backend-only
- **Evidence:** Backend service `accounts/services/client_flow_notifications.py` (out of browser-E2E scope; may be asserted as a branch of `platform-client-email-validation`).
