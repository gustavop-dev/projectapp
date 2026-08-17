### FLOW: `admin-proposal-reopen-from-expired`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (General tab — date picker, and JSON re-import panel)
- **Description:** Recover an `expired` proposal by extending `expires_at` to a future date. The validator no longer blocks re-saving when the date is left unchanged, so admins can fix any other field on an expired proposal; when the date does move into the future, `ProposalService.reopen_if_unexpired` auto-reverts `status` from `expired` to `viewed` (when `view_count > 0`) or `sent`, and logs an "Auto-reopened from expired…" entry in `ProposalChangeLog`. Same behavior on both update paths (form PATCH and JSON re-import PUT).
- **Steps:**
  1. Admin opens an expired proposal at `/panel/proposals/:id/edit`. The status badge reads "Expirada".
  2. Admin moves the `expires_at` datetime input to a future date (or pastes a JSON with a future `expires_at` in the JSON re-import panel).
  3. Admin clicks Save.
  4. PATCH `/api/proposals/:id/update/` (form) or PUT `/api/proposals/:id/update-from-json/` (JSON path).
  5. Backend persists `expires_at` and `status` in a single save; `ProposalChangeLog` records the auto-reopen.
  6. UI refreshes — the status badge no longer shows "Expirada"; the proposal returns to `sent`/`viewed`.
- **Branches:**
  - [Branch A — form path] PATCH `/update/`. Status reverts to `viewed` if `view_count > 0`, else `sent`.
  - [Branch B — JSON path] PUT `/update-from-json/`. Same reopen logic; `ProposalFromJSONSerializer` reads the bound proposal via `context={'proposal': proposal}` to skip the future-only check when `expires_at` is unchanged.
  - [Branch C — keep `expires_at` unchanged] Admin edits other fields on an expired proposal without touching the date. Save succeeds (no longer blocked by validator); `status` stays `expired`.
- **Coverage:** ✅ Covered (JSON path + the General-tab PATCH `/update/` reopen with the header status reverting from expired; asserted 2026-07-23)
- **E2E Spec:** `e2e/admin/admin-proposal-reopen-from-expired.spec.js`
