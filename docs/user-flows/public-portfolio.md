### FLOW: `public-portfolio`

- **Module:** public
- **Role:** guest
- **Priority:** P2
- **Routes:** `/portfolio-works`, `/en-us/portfolio-works`, `/es-co/portfolio-works`
- **Description:** Browse portfolio works listing page (Awwwards-style) with hero section, animated gradient, and project cards linking to case study detail pages.
- **Steps:**
  1. User navigates to the portfolio page.
  2. Hero section renders with animated gradient background.
  3. Portfolio works load from API (`GET /api/portfolio/`).
  4. Project cards render with title, excerpt, cover image, and "View" link.
  5. User clicks a project card.
  6. Page navigates to `/portfolio-works/:slug`.
- **Branches:**
  - [Branch A] Empty state renders when no projects are published.
  - [Branch B] Loading spinner renders while data is being fetched.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-pages.spec.js`
