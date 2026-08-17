### FLOW: `admin-proposal-quick-log`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Admin registers a seller activity (call, meeting, follow-up, note) directly from the proposals list via the actions modal, without entering the proposal detail. Opens a quick-log modal with activity type selector and description field.
- **Steps:**
  1. Admin opens the actions modal (⋮) for a proposal.
  2. Admin clicks "📝 Registrar actividad".
  3. Quick-log modal opens showing client name and proposal title.
  4. Admin selects activity type (call, meeting, follow-up, note).
  5. Admin enters a description.
  6. Admin clicks "Registrar" → API call to `POST /api/proposals/:id/log-activity/`.
  7. Success: modal closes, proposal list refreshes with updated `last_activity_at`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-quick-log.spec.js`
