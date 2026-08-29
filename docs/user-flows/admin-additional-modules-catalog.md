### FLOW: `admin-additional-modules-catalog`

- **Module:** admin / commercial
- **Role:** admin
- **Priority:** P1
- **Route:** `/panel/additional-modules`
- **Interaction:** Navigate from the panel sidebar, read the grouped catalog and retry a failed initial request.
- **Outcomes:** `display`, `failure`
- **Evidence:** `frontend/pages/panel/additional-modules/index.vue`, `GET /api/additional-modules/admin/`
