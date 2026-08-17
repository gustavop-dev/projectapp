### FLOW: `admin-proposal-defaults-slug-pattern`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/defaults?mode=proposal` (General tab)
- **Description:** Admin configures the default slug pattern used when new proposals are created. The pattern supports `{client_name}`, `{project_type}`, and `{year}` placeholders. A live preview below the input shows the slugified result (e.g., `{client_name}` → `/proposal/empresa-demo`). Saved to `ProposalDefaultConfig.default_slug_pattern`.
- **Steps:**
  1. Admin navigates to `/panel/defaults?mode=proposal`.
  2. General tab renders. Slug pattern input shows current value (default: `{client_name}`).
  3. Live preview below input updates reactively as admin types, showing the `toSlug()` result.
  4. Admin edits the pattern (e.g., `{client_name}-{year}`).
  5. Admin clicks "Guardar" → `PUT /api/proposals/defaults/` with `{ default_slug_pattern }`.
  6. Future proposals auto-generate slugs using the new pattern.
- **Branches:**
  - [Branch A — Valid pattern] Pattern saved; new proposals use the pattern.
  - [Branch B — Custom text] Any free-text pattern (no placeholders) works; becomes a fixed prefix with collision suffix appended.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-defaults-slug-pattern.spec.js`
