### FLOW: `admin-hour-packages-list`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/hour-packages`
- **Description:** View the hour-package catalog filtered by nationality tabs (COL/EXT/USA); prices show in the currency derived from the nationality (COL→COP, EXT/USA→USD) with computed effective rate and total.
- **Steps:**
  1. Admin navigates to `/panel/hour-packages`.
  2. Packages load from API (`GET /api/hour-packages/admin/?nationality=COL`) — Colombia tab is active by default.
  3. Table renders name, hours, rate/h, discount, effective rate, total and active badge.
  4. Admin switches nationality tab → list refetches with that nationality and prices change currency.
  5. Empty tabs show a hint that proposal creation falls back to default packages.
  6. "Nuevo paquete" button links to the create page carrying the active nationality.
- **Coverage:** ✅ Covered (list, nationality tabs, empty state, pagination across pages and the mobile card variant; asserted 2026-07-23. View modes tracked in `admin-hour-packages-view-modes`.)
- **E2E Spec:** `e2e/admin/admin-hour-packages-list.spec.js`
