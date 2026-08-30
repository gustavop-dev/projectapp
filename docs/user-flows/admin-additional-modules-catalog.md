### FLOW: `admin-additional-modules-catalog`

- **Module:** admin / commercial
- **Role:** admin
- **Priority:** P1
- **Route:** `/panel/additional-modules`
- **Interaction:** Navigate from the panel sidebar, switch Spanish/English content, choose card/list/accordion presentation and retry a failed initial request. The chosen presentation is remembered for the panel surface.
- **Outcomes:** `success`, `display`, `failure`
- **Evidence:** `frontend/pages/panel/additional-modules/index.vue`, `GET /api/additional-modules/admin/`
