### FLOW: `admin-dashboard`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/`
- **Description:** View the redesigned global dashboard: pulse KPIs (liquid utility, active pipeline, attention count), cross-module attention radar, and finance / proposals / operations sections fed by one request to `GET /api/panel/dashboard/`.
- **Steps:**
  1. Authenticated admin navigates to `/panel/`.
  2. The page fetches `GET /api/panel/dashboard/` (single consolidated payload) and shows skeletons while loading.
  3. Pulse tiles, attention radar and the module sections render; section headers deep-link to each module.
  4. The "+ Crear" dropdown offers quick creation shortcuts (propuesta, documento, tarea, gasto).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-dashboard.spec.js`
