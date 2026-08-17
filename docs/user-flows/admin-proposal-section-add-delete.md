### FLOW: `admin-proposal-section-add-delete`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Secciones tab)
- **Description:** Admin adds a missing section type and deletes sections from the editor.
- **Steps:**
  1. Admin clicks «＋ Agregar sección»; the modal lists only the types not yet present.
  2. Picking a type calls `POST /api/proposals/:id/sections/create/` (seeded from language defaults) and the new section appears expanded at the end.
  3. The trash action on a section header asks for confirmation and calls `DELETE /api/proposals/sections/:id/delete/`.
  4. Deleting `functional_requirements` with a confirmed calculator selection is blocked by the backend (`fr_has_confirmed_selection`) and the error surfaces as a notification.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-section-add-delete.spec.js`
