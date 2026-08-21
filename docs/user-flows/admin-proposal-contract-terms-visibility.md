### FLOW: `admin-proposal-contract-terms-visibility`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/create`, `/panel/proposals/:id/edit`
- **Description:** Decide whether a Spanish proposal exposes the generic **Contrato y condiciones** mode. The switch defaults to visible for new and existing proposals, is unavailable for English proposals, and persists as top-level proposal metadata without changing the proposal prompt or section JSON.
- **Outcomes:**
  - `success` — the creation form submits the selected visibility and the edit switch persists an immediate visibility change.
  - `failure` — when the edit request fails, the switch returns to its previous state and the admin sees an error notification.
- **Non-applicable classes:** `error` has no independent invalid Boolean input. `display` is asserted as the precondition and final state of the success/failure interactions rather than a separate read-only flow.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-contract-terms-visibility.spec.js`
