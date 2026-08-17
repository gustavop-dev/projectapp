### FLOW: `admin-proposal-defaults-config`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/defaults?mode=proposal` (old `/panel/proposals/defaults` redirects here)
- **Description:** Admin manages the default section configurations used when creating new proposals. Supports both ES and EN languages. Changes are saved to a DB-backed config and applied to all future proposals. Includes reset-to-hardcoded functionality.
- **Steps:**
  1. Admin navigates to `/panel/defaults?mode=proposal` via the "Defaults" sidebar item or the "Valores por Defecto" button on the proposals list page.
  2. Default sections load from API (`GET /api/proposals/defaults/?lang=es`).
  3. Language selector allows switching between Español and English.
  4. Section accordion list renders with all default sections (same structure as proposal edit).
  5. Admin expands a section and edits its content using SectionEditor (form or paste mode).
  6. Section is marked as "Modificado" locally.
  7. Admin clicks "Guardar Todos los Cambios".
  8. API call to `PUT /api/proposals/defaults/` with the full sections_json array plus `base_updated_at`, the version loaded in step 2.
  9. Success feedback displays.
- **Branches:**
  - [Branch A — Reset] Admin clicks "Restaurar valores originales" → confirmation modal → `POST /api/proposals/defaults/reset/` → sections reload from hardcoded defaults.
  - [Branch B — Language switch with unsaved changes] Confirmation prompt warns about losing changes.
  - [Branch C — Stale snapshot (failure)] The stored config moved on since step 2 (a migration, or another admin saving) → `PUT` answers `409 stale_defaults` → the panel shows "Los valores por defecto cambiaron desde que abriste esta página." and **keeps the pending edits on screen**, so the admin chooses between refreshing and re-applying them. Without this the snapshot would rewind the stored defaults and every proposal created afterwards would inherit the rewound content.
- **Coverage:** ⚠️ Partial — `display` covered; `success` and `failure` have no qualifying E2E test.
- **E2E Spec:** `e2e/admin/admin-proposal-defaults.spec.js` (5 tests, all `@outcome:display`)
- **Backend Tests:** `content/tests/views/test_proposal_defaults_views.py`, `content/tests/models/test_proposal_default_config.py`, `content/tests/services/test_proposal_service.py::TestGetDefaultSectionsFromDB`
