### FLOW: `admin-proposal-update-from-json`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (JSON re-import panel)
- **Description:** Re-import a complete JSON payload over an existing proposal — distinct from `admin-proposal-create-from-json` which creates a new proposal. The admin pastes/uploads JSON in the edit screen; the store calls `PUT /api/proposals/:id/update-from-json/` which replaces metadata and each known section's `content_json`. Unrecognized section keys come back as a `warnings` array; sections not present in the payload are left unchanged.
- **Steps:**
  1. Admin opens `/panel/proposals/:id/edit` and switches to the JSON re-import panel.
  2. Admin pastes (or uploads) a JSON payload that follows the `create-from-json` template shape.
  3. Admin clicks "Actualizar desde JSON".
  4. Frontend store calls `proposalStore.updateProposalFromJSON(id, payload)` → `PUT /api/proposals/:id/update-from-json/`.
  5. Backend validates via `ProposalFromJSONSerializer` (with the bound proposal in context, so an unchanged past `expires_at` is allowed), updates metadata fields, replaces section `content_json` for matching keys, and logs each changed field.
  6. Success toast "Propuesta actualizada desde JSON."; if the JSON contained unmapped section keys, the response includes a `warnings` array which the UI surfaces.
- **Branches:**
  - [Branch A — happy path] Valid JSON → 200 with refreshed proposal payload.
  - [Branch B — unknown section keys] Payload includes unrecognized keys → 200 + `warnings` listing them.
  - [Branch C — invalid `expires_at`] New value in the past → 400 from `validate_expires_at` (unless the value matches the proposal's stored `expires_at`).
- **Coverage:** ✅ Covered (happy path, unknown keys riding the PUT with a 200+warnings response, and the keep-expires_at-on-expired branch; asserted 2026-07-23). Note: the API's `warnings` array is pytest-covered but not currently surfaced by the JSON tab UI.
- **E2E Spec:** `e2e/admin/admin-proposal-update-from-json.spec.js`
