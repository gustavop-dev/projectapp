### FLOW: `public-route-not-found`

- **Module:** public
- **Role:** guest
- **Priority:** P3
- **Routes:** `/:slug*`
- **Description:** A guest reaches the public catch-all route after navigating to an unmatched URL. The terminal fallback renders “Page not found”.
- **Steps:**
  1. Guest opens an unmatched public URL.
  2. The catch-all route renders the terminal not-found message.
- **Branches:**
  - [n/a — success] The view has no recovery action or successful completion.
  - [n/a — error] It performs no request or validation that can display an error branch.
  - [failure] An unmatched route resolves to the explicit not-found state.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/responsive/public.spec.js`
