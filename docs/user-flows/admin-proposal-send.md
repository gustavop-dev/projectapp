### FLOW: `admin-proposal-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/`, `/panel/proposals/:id/edit`
- **Description:** Send a proposal to a client via email. On edit page, a visual pre-send checklist modal replaces the native `confirm()` dialog, validating: client email, client name, investment > $0, future expiration date, at least 1 enabled section. The email body now interpolates the editable `email_intro` textarea (BusinessProposal.email_intro, persisted on the General tab) and the commercial PDF is attached automatically (`ProposalEmailService._attach_commercial_pdf`). The backend returns `email_delivery: { ok, reason, detail }`; when `ok=false`, the panel shows a red toast with the reason (`placeholder_email`, `template_disabled`, `send_failed`) instead of the generic "Propuesta enviada" toast, so the admin learns the email did not actually reach the client.
- **Steps:**
  1. Admin views the proposal edit page or the actions modal in the list page.
  2. Admin (optional) edits the "Texto introductorio del correo" textarea (`data-testid=edit-email-intro`) in the General tab and saves the form. Empty falls back to a default derived from the title.
  3. Admin clicks "Enviar al Cliente".
  4. Pre-send checklist modal opens showing pass/fail status for each item (✓/✗).
  5. "Enviar al Cliente" button is disabled until all checks pass.
  6. Admin clicks "Enviar al Cliente" in modal → API call to `POST /api/proposals/:id/send/`.
  7. Backend changes status to `sent`, generates the commercial PDF, attaches it, sends the email, and returns the proposal payload with `email_delivery`. `EmailLog.metadata.pdf_attached` records whether the attachment succeeded.
  8. If `email_delivery.ok === true`, success toast "Propuesta enviada al cliente". If `false`, error toast surfacing `email_delivery.detail || email_delivery.reason` with a hint to verify client email and use "Re-enviar".
- **Coverage:** ✅ Covered — checklist modal + send, distinct toasts for `email_delivery.ok` true/false, and `email_intro` asserted in the update PATCH payload (reconciled 2026-07-22: the spec already covered what this entry listed as pending). PDF-attached metadata (`EmailLog.metadata.pdf_attached`) and the per-reason variants (`placeholder_email`, `template_disabled`, `send_failed`) are pytest-covered; the list-page red toast lives under `admin-proposal-inline-status-change`/`admin-proposal-resend` (still partial).
- **E2E Spec:** `e2e/admin/admin-proposal-send.spec.js`
