### FLOW: `admin-clients-config-tab`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/clients`
- **Description:** Trailing "Configuraciones" pill swaps the client list for the shared ViewSettingsPanel (saved-filter-tabs reset + defaults link).
- **Steps:**
  1. Admin clicks the right-aligned "Configuraciones" pill in the status-tab row.
  2. The list area is replaced by the settings panel: "Restablecer" for the Clientes view opens a ConfirmModal and POSTs `accounts/saved-filter-tabs/reset/` (view=client); saved tabs reload on success.
  3. "Abrir defaults" links to `/panel/defaults`.
  4. Clicking any status pill returns to the list.
- **Coverage:** ⚠️ Missing
- **E2E Spec:** _pending_
