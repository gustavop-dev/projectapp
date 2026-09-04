### FLOW: `admin-proposal-multi-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit`
- **Description:** Send one email containing 2–10 same-client proposals. The modal groups eligible proposals by status and requires a nonblank personalized message on every selected item. Missing items show "Falta mensaje" plus a link to that proposal's **Correos** tab; an aggregate warning disables the send. The email renders each proposal as a numbered phase with that proposal's own `email_intro` and PDF. Backend prevalidates the complete set before any snapshot or state transition.
- **Steps:**
  1. Admin opens `/panel/proposals/:id/edit` for a client that has another eligible proposal.
  2. Admin clicks the lightning-bolt button next to "Guardar cambios".
  3. `ProposalActionsModal` opens; admin clicks "Enviar varias propuestas como un solo correo" (`data-testid=proposal-action-send-multi`).
  4. `ProposalMultiSendModal` opens, listing the client's other proposals grouped by status. The current proposal is pre-checked and locked.
  5. Admin selects one or more additional proposals. If any selected item lacks a message, the modal identifies it and keeps the action disabled.
  6. With 2–10 valid selections, admin clicks send → `POST /api/proposals/:id/send-multi/` with `proposal_ids`.
  7. Backend validates same client, count, and every message before side effects; then it renders each phase's message, attaches N PDFs, and applies draft→sent, expired→reopen, or resend timer transitions.
  8. Modal closes on success and shows "Correo enviado al cliente con N propuestas." A server failure keeps the modal open with an error.
- **Coverage:** ✅ Covered — success, missing-message validation, and server failure are E2E-covered; per-phase rendering and all-or-nothing validation are pytest-covered.
- **E2E Spec:** `e2e/admin/admin-proposal-multi-send.spec.js`
