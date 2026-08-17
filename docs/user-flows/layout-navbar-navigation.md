### FLOW: `layout-navbar-navigation`

- **Module:** layout
- **Role:** guest/admin
- **Priority:** P2
- **Routes:** All pages
- **Description:** Navigate between pages using the glassmorphism pill navbar with sliding lemon indicator.
- **Steps:**
  1. User sees the glassmorphism pill navbar fixed at the top of the page.
  2. User clicks a navigation link (Custom Software, App Development, Our work, Blog, Contact/WhatsApp).
  3. Page navigates to the selected route.
  4. Lemon pill indicator slides to highlight the active section.
- **Branches:**
  - [Branch A] User toggles language via EN/ES button → page reloads in selected locale (`/en-us/` or `/es-co/`).
  - [Branch B] User clicks Contact (WhatsApp) → external link opens.
  - [Branch C — Mobile] Hamburger menu opens with navigation links + WhatsApp CTA button.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/layout/layout-navbar.spec.js`
