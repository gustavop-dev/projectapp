### FLOW: `admin-proposal-actions-modal`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals`, `/panel/proposals/:id/edit`, `/proposal/:uuid?preview=1`
- **API:** `GET /api/proposals/:uuid/` when the public preview tab loads; the modal itself renders from proposal data already loaded by the edit/list view.
- **Description:** Admin opens an actions modal from a proposal row or the proposal edit page. The modal exposes the available actions for that context; public preview opens the client-facing proposal in a new tab without recording engagement. Send/Resend visibility is conditional on proposal status.
- **Steps:**
  1. Admin is on the proposal listing `/panel/proposals`.
  2. Admin clicks the actions icon (⋮) on a proposal row.
  3. Actions modal opens with buttons: Edit, Preview, Send/Resend, Copy, WhatsApp, Duplicate, Toggle, Delete.
  4. [Branch A — Draft] "Send" action visible; "Resend" hidden.
  5. [Branch B — Sent/Viewed] "Resend" action visible; "Send" hidden.
  6. [Branch C — Public preview] Admin opens the edit-page actions modal and clicks "Vista previa pública".
  7. A new tab renders the proposal with the preview banner and without tracking the visit.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-actions-modal.spec.js`
