### FLOW: `admin-proposal-dashboard-auto-refresh`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/proposals/`
- **Description:** The ProposalDashboard KPI panel auto-refreshes every 60 seconds when open. A manual "Actualizar" button and "last updated" label are also available. Auto-refresh pauses when the dashboard is collapsed.
- **Steps:**
  1. Admin views the proposals list with the dashboard open.
  2. Dashboard fetches data on first open.
  3. Every 60 seconds, data refreshes automatically if the panel is open.
  4. "Actualizar" button triggers manual refresh with spin animation.
  5. "justo ahora" / "hace Xs" label shows time since last refresh.
  6. Collapsing the dashboard stops auto-refresh; expanding resumes it.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-dashboard-auto-refresh.spec.js`
