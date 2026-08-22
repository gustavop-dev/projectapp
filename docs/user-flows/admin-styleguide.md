### FLOW: `admin-styleguide`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/styleguide`
- **Description:** Admin browses the executable base-component/design-token catalog and verifies the canonical responsive behavior at compact, portrait, landscape, desktop and wide widths.
- **Interaction matrix:**
  - `display` — the admin reaches the catalog, sees the matching responsive profile, navigation mode, tabs/filters, priority table and capped content shell.
  - `success` — n/a: the page is a reference catalog and does not persist product data.
  - `error` — n/a: component validation belongs to unit tests; there is no user-submitted payload.
  - `failure` — n/a: the examples are local and make no product mutation request.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/visual/styleguide.spec.js`
