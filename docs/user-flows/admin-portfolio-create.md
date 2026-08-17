### FLOW: `admin-portfolio-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/portfolio/create`
- **Description:** Create a new portfolio work via manual form (bilingual fields, cover image, project URL, content JSON, SEO) or JSON import.
- **Steps:**
  1. Admin navigates to `/panel/portfolio/create`.
  2. Page loads with Manual / Importar JSON tab toggle.
  3. Manual tab is active by default — form renders with ES/EN fieldsets.
  4. Admin fills title, tagline, project URL, cover image, content JSON, SEO fields.
  5. Admin submits.
  6. API call to `POST /api/portfolio/admin/create/`.
  7. On success, admin is redirected to portfolio list.
- **Branches:**
  - [Branch A — JSON import] Admin switches to "Importar JSON" tab, pastes JSON, submits via `POST /api/portfolio/admin/create-from-json/`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-portfolio-create.spec.js`
