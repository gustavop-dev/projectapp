### FLOW: `admin-dashboard-error-retry`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/`
- **Description:** A failed `GET /api/panel/dashboard/` load replaces the dashboard with a global error state; the Reintentar button refetches and restores the full dashboard once the API recovers.
- **Steps:**
  1. Admin opens `/panel/` while the dashboard endpoint fails (5xx).
  2. The error state renders with a Reintentar button and a panel notification fires.
  3. Clicking Reintentar refetches; on success the pulse/radar/sections render.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-dashboard.spec.js`
