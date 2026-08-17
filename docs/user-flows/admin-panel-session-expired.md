### FLOW: `admin-panel-session-expired`

- **Module:** auth
- **Role:** admin
- **Priority:** P1
- **Routes:** Any `/panel/*` route except `/panel/login` (guarded by `middleware/admin-auth.js`, registered on all 45 panel pages, e.g. `/panel/`, `/panel/proposals`)
- **Description:** A browser without a valid staff session requests a protected `/panel/*` route — either it never authenticated, or a previously valid session expired/was invalidated server-side.
- **Steps:**
  1. User (or a browser with a stale/expired cookie) navigates to a `/panel/*` route other than `/panel/login`.
  2. The `admin-auth` Nuxt middleware calls `GET /api/auth/check/` (`checkAdminAuth` action in `stores/proposals.js`).
  3. Backend `check_admin_auth` returns 401 (no authenticated user) or 403 (authenticated but not staff) instead of the user payload.
  4. Middleware hard-redirects the browser (`window.location.href`, a full page navigation, not `navigateTo`/SPA routing) to `/admin/login/?next=<originally requested path>` and aborts the SPA navigation (`abortNavigation()`).
  5. [Branch] Signing in again on the Django login form returns the user to the originally requested `/panel/*` page via `next`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/auth/auth-admin-login.spec.js` (describe "Admin Panel Session Guard": mocks `GET /api/auth/check/` → 401 and asserts the hard redirect to `/admin/login/?next=/en-us/panel/proposals`)
