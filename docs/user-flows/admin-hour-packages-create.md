### FLOW: `admin-hour-packages-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/hour-packages/create`
- **Description:** Create an hour package with nationality, bilingual name/note, hours, hourly rate, discount, order and active flag; the currency is derived from the nationality and a live preview shows effective rate and total.
- **Steps:**
  1. Admin navigates to `/panel/hour-packages/create` (nationality preselected from query param).
  2. Admin fills the form; the preview recalculates effective rate/total.
  3. Admin submits.
  4. API call to `POST /api/hour-packages/admin/create/`.
  5. On success, admin is redirected to the list; validation errors render per field.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-hour-packages-create.spec.js`
