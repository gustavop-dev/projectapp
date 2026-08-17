### FLOW: `admin-proposal-slug-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (General tab → URL personalizada)
- **Description:** Admin sets or regenerates the human-friendly slug for the public proposal URL. The slug replaces the UUID in the shared link (`/proposal/<slug>/`) making it feel personal to the client. Includes format validation, uniqueness check, and one-click regeneration from client name.
- **Steps:**
  1. Admin opens a proposal and stays on the General tab.
  2. The slug input shows the current slug (auto-generated on creation from default pattern or client name).
  3. Admin types a new slug in the input field (lowercase, numbers, hyphens only).
  4. Client validates format with regex `/^[a-z0-9]+(?:-[a-z0-9]+)*$/`; red error shown for invalid format.
  5. Admin clicks "Guardar URL" → `PATCH /api/proposals/:id/update/` with `{ slug }`.
  6. Server validates uniqueness; 400 error surfaced in UI if taken.
  7. Success state (✓) shown; copy-link button and preview href update to use new slug.
  8. [Branch] Admin clicks "Regenerar" to reset slug from client name via `toSlug(clientName)`.
- **Branches:**
  - [Branch A — Valid format] Save succeeds, slug persists, public URL updates.
  - [Branch B — Invalid format] Red error message blocks save.
  - [Branch C — Duplicate slug] Server 400 → "Esa URL ya está en uso" message.
  - [Branch D — Regenerate] Slug input pre-filled with `toSlug(clientName)`; admin can still modify before saving.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-slug-edit.spec.js`
