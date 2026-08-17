### FLOW: `admin-portfolio-delete`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/portfolio/`
- **Description:** Delete an existing portfolio work.
- **Steps:**
  1. Admin views the portfolio list.
  2. Admin clicks delete on a portfolio work.
  3. Confirmation dialog appears.
  4. Admin confirms deletion.
  5. API call to `DELETE /api/portfolio/admin/:id/delete/`.
  6. Portfolio work is removed from the list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-portfolio-delete.spec.js`
