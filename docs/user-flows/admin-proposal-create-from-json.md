### FLOW: `admin-proposal-create-from-json`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/create` (JSON import tab)
- **Description:** Admin creates a proposal by importing a pre-filled JSON payload. Alongside section data, `_meta.optional_metadata.email_intro` carries a generated plain-text message explaining the client's problem, this proposal's solution, and the expected outcome. The UI flattens that value to the API `email_intro` field; it remains editable later in **Correos**. Missing sections still fall back to defaults, while an omitted message is allowed only for a saved draft and blocks direct send.
- **Steps:**
  1. Admin navigates to `/panel/proposals/create`.
  2. Admin clicks "Importar JSON" tab.
  3. JSON textarea/file input appears.
  4. Admin pastes or loads a valid JSON payload (must include `sections.general.clientName`; generated artifacts should also include `_meta.optional_metadata.email_intro`).
  5. Admin submits.
  6. API call to `POST /api/proposals/create-from-json/` with `ProposalFromJSONSerializer` validation.
  7. Backend creates the proposal, persists `email_intro`, and creates all section records with the provided `content_json`.
  8. Admin is redirected to `/panel/proposals/:id/edit`.
- **Branches:**
  - [Branch A — Missing general key] Validation error `sections.general required`.
  - [Branch B — Past expires_at] Validation error on date.
  - [Branch C — Partial sections] Unspecified sections default to template defaults.
  - [Branch D — `_meta` key] Stripped from sections before saving.
  - [Branch E — Missing message] Draft creation remains valid, but "Crear y Enviar" stays unavailable until a message is provided.
- **Coverage:** ✅ Covered — JSON flattening/persistence and direct-send gating are exercised in the create E2E spec; serializer/API persistence are pytest-covered.
- **E2E Spec:** `e2e/admin/admin-proposal-create.spec.js`
