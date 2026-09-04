### FLOW: `admin-proposal-resend`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`, `/panel/proposals/:id/edit`
- **Description:** Resend an already-sent proposal with its saved personalized message. The resend modal preloads `email_intro` and allows editing it. A nonblank message is mandatory; "Guardar y re-enviar" persists the edit, creates an audit entry, keeps `expires_at`, resets send/reminder timers, and dispatches the email again. The new delivery gets the new text while previous delivery snapshots remain immutable.
- **Steps:**
  1. Admin opens the actions modal for a proposal whose status is `sent`/`viewed`.
  2. Admin clicks "Re-enviar".
  3. The editor opens with the previously saved message. Admin may add or remove content.
  4. If the result is blank, the action remains disabled and no request is made.
  5. Admin clicks "Guardar y re-enviar" → `POST /api/proposals/:id/resend/` with `{ email_intro }`.
  6. Backend validates before persistence/side effects, saves the changed message, resets timers, and re-sends.
  7. Success toast says "Propuesta re-enviada al cliente"; delivery failure keeps the editor available and surfaces `email_delivery.detail || email_delivery.reason`.
- **Coverage:** ✅ Covered — retained-message preload/edit payload, blank-message error, success and email-delivery failure are E2E-covered; persistence, audit log, no-side-effect validation and historical immutability are pytest-covered.
- **E2E Spec:** `e2e/admin/admin-proposal-resend.spec.js`
