### FLOW: `admin-proposal-section-dirty-guard`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Secciones tab)
- **Description:** Unsaved-changes protection in the section editor.
- **Steps:**
  1. Admin edits a field of an expanded section; a «Sin guardar» badge appears on the section header.
  2. Collapsing the dirty section opens a confirmation modal («Cerrar sin guardar» / «Seguir editando»).
  3. Cancelling keeps the editor open with the edits intact; confirming discards them and clears the badge.
  4. Route navigation, page unload and the panel refresh button also confirm before discarding dirty sections.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-section-dirty-guard.spec.js`
