### FLOW: `platform-legacy-route-redirects`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P2
- **Routes:** `/platform`, `/platform/dashboard`, `/platform/board`, `/platform/bugs`, `/platform/changes`, `/platform/deliverables`, `/platform/payments`, `/platform/access`, `/platform/collection-accounts`, `/platform/collection-accounts/:id`
- **Description:** Authenticated users opening a compatibility alias for a retired platform surface land on `/platform/projects` without returning to the legacy route or entering a redirect loop.
- **Outcome:** `success`
- **Coverage:** ✅ Covered in the five canonical responsive profiles.
- **E2E Spec:** `e2e/responsive/catalog-matrix.spec.js`
