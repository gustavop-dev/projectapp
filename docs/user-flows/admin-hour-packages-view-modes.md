### FLOW: `admin-hour-packages-view-modes`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/hour-packages`
- **Description:** Switch the catalog between Tabla, Tarjetas and Comparativa (pricing tiers with a "Mejor tarifa" highlight); the initial mode comes from the settings singleton.
- **Steps:**
  1. Admin opens `/panel/hour-packages` — `GET /api/hour-packages/admin/settings/` decides the initial view mode.
  2. Admin switches the view-mode segmented control (Tabla / Tarjetas / Comparativa).
  3. Tarjetas renders a card grid with effective rate, discount badge and totals; Comparativa renders side-by-side tiers highlighting the best effective rate.
  4. Edit/Eliminar remain available from every mode.
- **Coverage:** ⚠️ Missing
- **E2E Spec:** _pending_
