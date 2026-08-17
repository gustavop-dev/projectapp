### FLOW: `admin-proposal-resend`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Resend an already-sent proposal via the "Re-enviar" action in the proposals list actions modal. Keeps the existing `expires_at`, resets `sent_at`, `reminder_sent_at`, `urgency_email_sent_at`, re-schedules Huey reminders, and dispatches the proposal email again. The endpoint returns `email_delivery`; the panel toast surfaces success or failure with the reason — symmetric to `admin-proposal-send`.
- **Steps:**
  1. Admin opens the actions modal for a proposal whose status is `sent`/`viewed`.
  2. Admin clicks "Re-enviar".
  3. Confirmation dialog "¿Re-enviar esta propuesta? Se mantendrá la misma fecha de expiración." is shown.
  4. On confirm → `POST /api/proposals/:id/resend/`.
  5. Backend resets timers and re-sends the email, returning `email_delivery`.
  6. Success toast "Propuesta re-enviada al cliente" or error toast with `email_delivery.detail || email_delivery.reason`.
- **Coverage:** ✅ Covered (happy path + email_delivery failure detail surfaced instead of the success toast; asserted 2026-07-23)
- **E2E Spec:** `e2e/admin/admin-proposal-resend.spec.js`
- **E2E Spec (suggested):** `e2e/admin/admin-proposal-resend.spec.js`
