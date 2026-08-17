### FLOW: `admin-proposal-json-import-warnings`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/create` (JSON import tab)
- **Description:** When importing a proposal from JSON, the backend validates the payload and returns warnings for any section keys that don't map to known section types. Warnings are non-blocking — the proposal is still created, but the admin is informed of unmapped keys that were ignored.
- **Steps:**
  1. Admin switches to "Importar JSON" tab on the create page.
  2. Admin pastes a JSON payload containing extra or misspelled section keys.
  3. Admin submits → API call to `POST /api/proposals/create-from-json/`.
  4. Backend validates with `ProposalFromJSONSerializer`, identifies unmapped keys.
  5. Proposal is created successfully with known sections populated.
  6. Response includes `warnings` array listing unmapped section keys.
  7. Frontend displays warnings to the admin.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-create.spec.js`
