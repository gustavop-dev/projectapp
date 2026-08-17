### FLOW: `proposal-magic-link-request`

- **Module:** proposal
- **Role:** guest (on expired proposal view)
- **Priority:** P1
- **Routes:** `/proposal/:uuid` or `/proposal/:slug` (when expired)
- **Description:** A guest who lands on an expired proposal submits their email through the form in `ProposalExpired.vue:160` to receive a fresh magic-link. Backend looks up active proposals by client email and sends a new email with the link(s). This is the recovery path that complements `proposal-expired-graceful` (which only covers the expired-state visuals).
- **Steps:**
  1. Guest opens an expired proposal URL → `ProposalExpired` component renders.
  2. Guest types their email into the input and submits the form.
  3. Frontend calls `proposalStore.requestMagicLink(email)` → `POST /api/proposals/request-link/` with `{ email }`.
  4. Backend looks up non-finished proposals belonging to the email; if found, sends a new email with the magic link(s).
  5. UI shows a success confirmation ("Te enviamos un enlace nuevo a tu correo").
- **Branches:**
  - [Branch A — Email not found] Backend returns 404 / generic message; UI shows neutral feedback (avoid leaking which emails are clients).
  - [Branch B — Network error] Submit fails; UI surfaces a retry message.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-magic-link-request.spec.js`
