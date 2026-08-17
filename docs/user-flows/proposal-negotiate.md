### FLOW: `proposal-negotiate`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** Client clicks "Necesito ajustes" from the ProposalClosing panel to open a negotiation flow. The response is sent to the backend with `decision: negotiating`, which pauses automations and logs the event.
- **Steps:**
  1. Client navigates to the closing panel.
  2. Client clicks "Necesito ajustes" (amber button).
  3. Confirmation modal opens.
  4. Client confirms → API call to `POST /api/proposals/:uuid/respond/` with `decision: negotiating`.
  5. Backend sets `automations_paused = True` and status to `negotiating`.
  6. Success message displays with WhatsApp CTA for further discussion.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-negotiate.spec.js`
