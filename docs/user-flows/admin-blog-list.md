### FLOW: `admin-blog-list`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/blog/`
- **Description:** View the paginated list of all blog posts (admin view with both languages).
- **Steps:**
  1. Admin navigates to `/panel/blog/`.
  2. Blog posts load from API (`GET /api/blog/admin/?page=1&page_size=15`).
  3. Blog table renders with title_es, title_en, status, dates.
  4. Pagination controls appear if total pages > 1 (prev/next + page numbers).
  5. "Calendario" button links to calendar view.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-list.spec.js`
