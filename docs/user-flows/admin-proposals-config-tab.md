### FLOW: `admin-proposals-config-tab`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/proposals`
- **Description:** Fixed trailing "Configuraciones" tab in the proposals filter-tab bar swaps the list for the shared ViewSettingsPanel (saved-filter-tabs reset + proposals defaults link).
- **Steps:**
  1. Admin clicks the right-aligned "Configuraciones" tab (mobile: the "⚙ Configuraciones" option of the tabs select).
  2. The list area is replaced by the settings panel: "Restablecer" for the Propuestas view POSTs `accounts/saved-filter-tabs/reset/` (view=proposal) behind a ConfirmModal; tabs reload on success.
  3. "Abrir defaults de propuestas" links to `/panel/proposals/defaults`.
  4. Selecting any filter tab (or "Todas") closes the panel and restores the list.
- **Coverage:** ⚠️ Missing
- **E2E Spec:** _pending_
