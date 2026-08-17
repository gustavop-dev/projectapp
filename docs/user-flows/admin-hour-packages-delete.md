### FLOW: `admin-hour-packages-delete`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/hour-packages`
- **Description:** Delete an hour package from the list with a confirmation modal; already-created proposals are not affected.
- **Steps:**
  1. Admin views the hour-packages list.
  2. Admin clicks delete on a package.
  3. ConfirmModal appears.
  4. Admin confirms → `DELETE /api/hour-packages/admin/:id/delete/`.
  5. The row disappears from the list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-hour-packages-delete.spec.js`
