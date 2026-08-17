### FLOW: `admin-dashboard-finance-gate`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/`
- **Description:** Financial KPIs (liquid utility pulse tile and Finanzas section) render only when the backend payload carries finance data; staff non-superusers receive `finance: null` and never see financial figures. The gate is enforced server-side in `panel_dashboard` view.
- **Steps:**
  1. Staff (non-superuser) admin opens `/panel/`.
  2. `GET /api/panel/dashboard/` responds with `finance: null` and no finance-derived attention items.
  3. The dashboard renders proposals and operations only; no utility tile or Finanzas section.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-dashboard.spec.js`
