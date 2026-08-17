### FLOW: `admin-blog-calendar`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/blog/calendar`
- **Description:** Weekly calendar view showing scheduled, published, and draft blog posts.
- **Steps:**
  1. Admin navigates to `/panel/blog/calendar`.
  2. Calendar loads current week posts from API (`GET /api/blog/admin/calendar/?start=YYYY-MM-DD&end=YYYY-MM-DD`).
  3. Week grid renders Mon–Sun with posts color-coded: green (published), blue (scheduled), gray (draft).
  4. Admin uses ← / → arrows to navigate weeks, "Hoy" button to return to current week.
  5. Clicking a post card navigates to its edit page.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-calendar.spec.js`
