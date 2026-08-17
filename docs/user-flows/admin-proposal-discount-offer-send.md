### FLOW: `admin-proposal-discount-offer-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit`
- **API:** `POST /api/proposals/:id/email-preview/` (template `proposal_urgency`), `POST /api/proposals/:id/discount-offer/send/`
- **Description:** From the proposal actions menu the seller picks "Enviar oferta de descuento" — only shown when `discount_percent > 0` and the client has an email. A modal renders the server-side email preview; confirming sends the offer (`ProposalEmailService.send_urgency_email(force=True)`) and shows a success toast. Never auto-sent.
- **Steps:**
  1. Admin opens `/panel/proposals/:id/edit` and clicks the actions menu.
  2. Picks "Enviar oferta de descuento" → discount modal opens and loads the email preview.
  3. Clicks "Enviar oferta" → offer is emailed to the client → success toast.
- **Branches:**
  - [Branch A — no discount] `discount_percent = 0` → the action is hidden.
  - [Branch B — no email] Client without an email → the action is hidden.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-discount-offer.spec.js`
