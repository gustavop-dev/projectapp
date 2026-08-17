### FLOW: `proposal-view`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** View a business proposal shared via unique UUID link with horizontal scroll navigation.
- **Steps:**
  1. User opens the proposal URL with UUID.
  2. Proposal data loads from API (`GET /api/proposals/:uuid/`).
  3. Proposal index page renders with title, client info, expiration badge.
  4. User navigates through proposal sections using horizontal scroll (GSAP).
  5. Section counter updates as user navigates.
  6. User reads requirement groups and items within sections.
- **Branches:**
  - [Branch A — Proposal expired] Expired proposal page renders with expiration message.
  - [Branch B — Proposal not found] 404 or error page renders.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-view.spec.js`
