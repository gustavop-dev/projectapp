### FLOW: `admin-portfolio-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/portfolio/:id/edit`
- **Description:** Edit an existing portfolio work including bilingual fields, cover image upload, content JSON, and SEO meta.
- **Steps:**
  1. Admin navigates to `/panel/portfolio/:id/edit`.
  2. Portfolio work data loads from API (`GET /api/portfolio/admin/:id/detail/`).
  3. Edit form renders pre-filled with current data.
  4. Admin modifies content.
  5. Admin saves changes.
  6. API call to `PATCH /api/portfolio/admin/:id/update/`.
  7. Success feedback displays.
- **Branches:**
  - [Branch A] Admin uploads a new cover image via `POST /api/portfolio/admin/:id/upload-cover/`.
  - [Branch B] "Ver en público" link opens the public page in a new tab.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-portfolio-edit.spec.js`
