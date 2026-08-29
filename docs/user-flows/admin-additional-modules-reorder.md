### FLOW: `admin-additional-modules-reorder`

- **Module:** admin / commercial
- **Role:** admin
- **Priority:** P2
- **Route:** `/panel/additional-modules`
- **Interaction:** Reorder categories/modules by controls or drag and save the complete optimistic-lock payload.
- **Outcomes:** `success`, `failure` (stale revision reloads the catalog)
- **Evidence:** `CatalogOrderModal.vue`, `POST /api/additional-modules/admin/reorder/`.
