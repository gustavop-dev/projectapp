### FLOW: `admin-portfolio-list`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/portfolio/`
- **Description:** View the list of all portfolio works with status badges, edit/duplicate/delete actions.
- **Steps:**
  1. Admin navigates to `/panel/portfolio/`.
  2. Portfolio works load from API (`GET /api/portfolio/admin/`).
  3. Table renders with title, slug, status (published/draft/archived), dates.
  4. Admin sees action links: edit, duplicate, delete.
  5. "Nuevo Proyecto" button links to create page.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-portfolio-list.spec.js`
