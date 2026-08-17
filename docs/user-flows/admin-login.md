### FLOW: `admin-login`

- **Module:** auth
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/login` → `/panel/`
- **Description:** Admin authenticates to access the management panel.
- **Steps:**
  1. User navigates to `/panel/login`.
  2. Login page renders with link to Django Admin.
  3. User authenticates via Django Admin (`/admin/`).
  4. Auth check verifies session (`GET /api/auth/check/`).
  5. User is redirected to `/panel/` dashboard.
- **Coverage:** ✅ Covered (hand-off only)
- **E2E Spec:** `e2e/auth/auth-admin-login.spec.js`
- **E2E scope / abstention:** The E2E asserts only the SPA hand-off (the page renders and links to `/admin/` with the correct href). Steps 3–5 (credential entry, session auth, redirect) are **Django-native** — there is no SPA credential form to drive — so they are a declared abstention, marked `quality: allow-no-interaction` in the spec.
