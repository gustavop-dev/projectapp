### FLOW: `public-portfolio-detail`

- **Module:** public
- **Role:** guest
- **Priority:** P2
- **Routes:** `/portfolio-works/:slug`, `/en-us/portfolio-works/:slug`, `/es-co/portfolio-works/:slug`
- **Description:** View a single portfolio case study (Awwwards-style) with cover image, content sections, share button, project URL link, and back navigation.
- **Steps:**
  1. User clicks a project from the portfolio listing or navigates directly to `/portfolio-works/:slug`.
  2. Case study data loads from API (`GET /api/portfolio/:slug/`).
  3. Title, excerpt, cover image, and share button render.
  4. Content sections render (JSON-structured content or HTML fallback).
  5. Back link to `/portfolio-works` is visible.
  6. [Optional] "Visit project" link renders if `project_url` exists.
- **Branches:**
  - [Branch A — Not found] 404 page renders with "Back to portfolio" link.
  - [Branch B — Share] User clicks share button to share the case study.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-portfolio-detail.spec.js`

> **Archived Flows:** The following pages were moved to `_archived/` and are no longer accessible via navigation:
> `public-web-designs`, `public-3d-animations`, `public-hosting`, `public-ecommerce-prices`, `public-custom-software`.
> They were previously covered by `e2e/public/public-pages.spec.js`.
