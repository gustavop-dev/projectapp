### FLOW: `admin-proposal-duplicate`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Duplicate an existing proposal to create a new draft copy with the same sections and content.
- **Steps:**
  1. Admin views the proposal list or detail page.
  2. Admin clicks "Duplicar" on a proposal.
  3. API call to `POST /api/proposals/:id/duplicate/`.
  4. Backend creates a new proposal with status=draft, copying all sections and content.
  5. Admin is redirected to the new proposal's edit page.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-duplicate.spec.js`
