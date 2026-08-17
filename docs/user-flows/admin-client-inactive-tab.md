### FLOW: `admin-client-inactive-tab`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`
- **Description:** Manually mark a client as inactive (sets `UserProfile.deactivated_at`) via a pause/play toggle on the client row, and browse deactivated clients under the "Inactivos" option of the transversal client-status selector (next to the search box since the Ago 2026 filter reorganisation, labelled with its own match count). Inactive clients are hidden from Todos/Activos/Huérfanos (backend default excludes `deactivated_at IS NOT NULL`); Inactivos sends `?inactive=true`. Marking is reversible ("Reactivar cliente") and independent from `auth.User.is_active`.
- **Steps:**
  1. Admin navigates to `/panel/clients/`.
  2. Admin clicks the pause icon (data-testid: `client-toggle-inactive-<id>`) on an active client.
  3. `PATCH /api/proposals/client-profiles/:id/update/` with `{is_inactive: true}` sets `deactivated_at`; success toast shows; row leaves the current status on reload.
  4. Admin picks "Inactivos" in the status selector (data-testid: `clients-status-inactive`) — list reloads with `?inactive=true`, the URL gains `?status=inactive` and rows show the "Inactivo" badge.
  5. Clicking the play icon reactivates (`{is_inactive: false}` clears `deactivated_at`).
- **Coverage:** ✅ Covered — status filtering, marking inactive and the reactivate branch (play icon from the Inactivos list, PATCH `is_inactive:false` + toast) are asserted (2026-08-15).
- **E2E Spec:** `e2e/admin/admin-clients-inactive-tab.spec.js`
- **Backend Tests:** `content/tests/views/test_proposal_clients_views.py::TestInactiveClients`, `accounts/tests/test_proposal_client_service.py::TestUpdateClientProfile::test_toggling_is_inactive_does_not_cascade_snapshots`
