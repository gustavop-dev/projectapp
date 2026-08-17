### FLOW: `admin-hour-packages-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/hour-packages/:id/edit`
- **Description:** Edit an existing hour package; form prefilled from the detail endpoint, preview recalculates and a partial PATCH persists the changes.
- **Steps:**
  1. Admin navigates to `/panel/hour-packages/:id/edit`.
  2. Package data loads from API (`GET /api/hour-packages/admin/:id/detail/`).
  3. Admin edits rate/discount/fields; preview recalculates.
  4. Admin saves → `PATCH /api/hour-packages/admin/:id/update/`.
  5. On success, admin returns to the list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-hour-packages-edit.spec.js`
