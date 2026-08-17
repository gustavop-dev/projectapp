### FLOW: `admin-proposal-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/create`
- **Description:** Create a new business proposal (manual mode) with 12 auto-generated default sections.
- **Steps:**
  1. Admin navigates to `/panel/proposals/create`.
  2. Page loads with Manual / Importar JSON tab toggle.
  3. Manual tab is active by default — form renders with Título, Nombre del cliente, Email del cliente, Idioma, etc.
  4. Admin fills in the fields and submits.
  5. API call to `POST /api/proposals/create/`.
  6. Backend auto-creates 12 default sections and returns the full proposal.
  7. Admin is redirected to `/panel/proposals/:id/edit`.
- **Branches:**
  - [Branch A — Validation error] Form shows errors, admin corrects and resubmits.
  - [Branch B — JSON import] Admin switches to "Importar JSON" tab (see `admin-proposal-create-from-json`).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-create.spec.js`
- **Known gaps:** Hosting defaults seeding on mount (hosting_percent + hosting_discount_* from GET `proposals/defaults`, 2026-07) is not asserted — the spec's defaults mock only carries `expiration_days`. The JSON-tab `total_investment` now uses `BaseCurrencyInput` (live thousand separators) and its formatting is not asserted.
