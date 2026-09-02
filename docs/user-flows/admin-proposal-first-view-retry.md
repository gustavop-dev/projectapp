### FLOW: `admin-proposal-first-view-retry`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (Analytics tab)
- **Description:** Recover a failed first-view email alert without fabricating another client view or resetting proposal analytics.
- **Steps:**
  1. Admin opens a proposal and navigates to the Analytics tab.
  2. The delivery card shows `Falló`, the attempt count, and the last sanitized error.
  3. Admin clicks `Reintentar alerta`.
  4. On success, the API resets the durable state to `Pendiente`, queues the task, and the card refreshes.
  5. On server failure, the card remains failed and the retry remains available.
- **Outcome classes:** success and failure covered; validation error is n/a because the retry action is hidden outside the failed state; delivery-state display is covered by `admin-proposal-analytics`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-analytics.spec.js`
