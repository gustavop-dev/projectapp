### FLOW: `layout-locale-switch`

- **Module:** layout
- **Role:** guest/admin
- **Priority:** P2
- **Routes:** All pages with locale prefix (`/en-us/`, `/es-co/`)
- **Description:** Switch the application language between English and Spanish.
- **Steps:**
  1. User clicks the locale switcher component in the navbar.
  2. User selects a different language.
  3. URL updates with the new locale prefix.
  4. Page content re-renders in the selected language.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/layout/layout-locale.spec.js`
