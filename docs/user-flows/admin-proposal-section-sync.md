### FLOW: `admin-proposal-section-sync`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Secciones tab → SyncPreviewModal)
- **Description:** Admin reconciles a section's `content_json` against the canonical default for that `section_type`. The SyncPreviewModal shows a server-computed diff (added / removed / changed keys), and on apply the section is overwritten with the merged payload. Mounted at `frontend/components/BusinessProposal/admin/SyncPreviewModal.vue` from `pages/panel/proposals/[id]/edit.vue:42`.
- **Steps:**
  1. Admin opens the proposal edit page and selects a section.
  2. Admin triggers "Sincronizar con default" → `GET /api/proposals/sections/:id/sync-preview/` returns the diff payload.
  3. SyncPreviewModal renders the diff (keys to add / overwrite / drop) with side-by-side preview.
  4. Admin clicks "Aplicar" → `POST /api/proposals/sections/:id/apply-sync/` overwrites `content_json` and returns the updated section.
  5. UI refreshes the section in place (no page reload).
- **Branches:**
  - [Branch A — No drift] Diff is empty; modal shows "Sin cambios" and the apply button is disabled.
  - [Branch B — Cancel] Admin closes the modal without applying; section unchanged.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-section-sync.spec.js`
- **Note:** The modal only appears when saving a `technical_document` section on a proposal whose platform project already exists (`has_project: true`). An E2E would need to mock the full proposal detail with a launched project, simulate the section editor save flow, and intercept both `sync-preview/` and `apply-sync/`. The cost outweighs the P2 value; component-level coverage of `SyncPreviewModal.vue` would be a better fit.
- **Suggested E2E Spec:** `e2e/admin/admin-proposal-section-sync.spec.js`
