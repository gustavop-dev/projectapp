### FLOW: `admin-diagnostic-prompt`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` (Prompt tab)
- **Description:** Admin copies / edits / downloads the two diagnostic prompts used with an LLM to draft content — "Propuesta comercial" (fills the 8-section JSON narrative) and "Detalle técnico" (fills the `categories` section with per-category findings at the 4 severity levels). State is persisted per browser via `localStorage` using `usePromptState({storageKey, defaultPrompt})`.
- **Steps:**
  1. Admin navigates to the Prompt tab.
  2. Selects a sub-tab (Comercial / Técnico).
  3. Clicks Copiar / Editar / Descargar / Restaurar — prompt text round-trips through `localStorage`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-prompt.spec.js` (5 tests: sub-tabs visible, edit mode, save custom, restore original, technical sub-tab).
