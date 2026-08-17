### FLOW: `admin-proposal-multi-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit`
- **Description:** Send a single email referencing 2+ proposals from the same client. From the edit page, the lightning-bolt button opens `ProposalActionsModal`; the new action "Enviar varias propuestas como un solo correo" (visible whenever `client_email` is set) opens `ProposalMultiSendModal`. The modal lists every proposal of that client grouped by status: Borradores (draft), Enviadas/Vistas/Negociación (sent/viewed/negotiating), and Expiradas (status=`expired` or past `expires_at`). The current proposal is pre-selected and the checkbox is disabled to keep it always included. Selecting an "Expiradas" item shows a "Se reabrirá" badge. The send button stays disabled until ≥2 are selected and is capped at 10. Click → `POST /api/proposals/:id/send-multi/` with `{ proposal_ids: [...] }`. The backend dispatches a single email rendering each proposal as a numbered phase ("Propuesta N de M") and attaches one PDF per proposal. Per-proposal side effects: draft→sent + Huey reminders, expired/past expires_at→reopen + extend expires_at, sent/viewed/negotiating→resend timers (no status change). One `EmailLog` row per proposal sharing a `group_uuid` in metadata, plus a `ProposalChangeLog` entry per proposal.
- **Steps:**
  1. Admin opens `/panel/proposals/:id/edit` for a client that has another eligible proposal.
  2. Admin clicks the lightning-bolt button next to "Guardar cambios".
  3. `ProposalActionsModal` opens; admin clicks "Enviar varias propuestas como un solo correo" (`data-testid=proposal-action-send-multi`).
  4. `ProposalMultiSendModal` opens, listing the client's other proposals grouped by status. The current proposal is pre-checked and locked.
  5. Admin selects one or more additional proposals → "Enviar N propuestas" button enables.
  6. Admin clicks the send button → `POST /api/proposals/:id/send-multi/` with `proposal_ids`.
  7. Backend validates same-client, ≥2 proposals, ≤10 proposals, applies side effects, sends one email with N PDF attachments, returns the proposal payload + `email_delivery` + `transitions` map.
  8. Modal closes; success toast "Correo enviado al cliente con N propuestas." renders. Page data refreshes so updated statuses/expires_at show.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-multi-send.spec.js`
- **E2E Spec (suggested):** `e2e/admin/admin-proposal-multi-send.spec.js`. Mock `GET /api/proposals/?client_id=` to return ≥2 proposals across at least two of the status groups, click through the modal, mock `POST /api/proposals/:id/send-multi/` with `email_delivery.ok=true`, and assert the success toast.
