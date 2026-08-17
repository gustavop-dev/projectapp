### FLOW: `admin-diagnostic-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/diagnostics/create` → `/panel/diagnostics/:id/edit`
- **Description:** Admin creates a new WebAppDiagnostic by searching for an existing client via autocomplete (reuses `/api/proposals/client-profiles/search/`), selecting language, and submitting. The service seeds 8 JSON sections (`purpose`, `radiography`, `categories`, `delivery_structure`, `executive_summary`, `cost`, `timeline`, `scope`) from `content.seeds.diagnostic_template` and redirects to the edit page.
- **Steps:**
  1. Admin navigates to `/panel/diagnostics/create`.
  2. Types in the client search input (autocomplete fetches from `client-profiles/search`).
  3. Selects a client from the dropdown — submit button becomes enabled.
  4. Optionally sets a custom title.
  5. Clicks "Crear diagnóstico" → POST `/api/diagnostics/create/`.
  6. Redirected to `/panel/diagnostics/:id/edit`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-create.spec.js`
