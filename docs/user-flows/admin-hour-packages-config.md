### FLOW: `admin-hour-packages-config`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/hour-packages`
- **Description:** Configuración section: per-nationality base hourly rates (propagate to the whole catalog on save), default view mode, and restore a nationality's catalog to the canonical defaults ladder.
- **Steps:**
  1. Admin switches the page section segmented to "Configuración" — the three base-rate inputs (Colombia COP, Extranjero USD, USA USD) come prefilled from `GET /api/hour-packages/admin/settings/`.
  2. "Guardar tarifas" PATCHes `/api/hour-packages/admin/settings/update/`; the backend propagates each changed rate to every package of that nationality (active and inactive) and responds with `updated_packages` counts, surfaced in the success toast. The Catálogo table reflects the new rates. Rates `<= 0` are rejected client-side; a server failure surfaces an error toast. Existing proposals keep their snapshot — only new proposals seed the updated rates.
  3. Saving a default view mode PATCHes the same settings endpoint and toasts.
  4. "Restablecer" per nationality opens a ConfirmModal and POSTs `/api/hour-packages/admin/restore-defaults/`; the catalog of that country is replaced with the default ladder (1h/20h/60h/180h) and the base rate in settings resets to the default.
- **Coverage:** ✅ Covered (base rates: display prefill, success save + propagation reflected in catalog, client-side error, server failure toast; asserted 2026-07-28. Default view mode and restore-defaults remain unasserted in E2E — backend covered in `test_hour_package_views.py`.)
- **E2E Spec:** `e2e/admin/admin-hour-packages-config.spec.js`
