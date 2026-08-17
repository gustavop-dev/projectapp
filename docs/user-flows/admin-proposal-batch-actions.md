### FLOW: `admin-proposal-batch-actions`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Admin selects multiple proposals via checkboxes and performs batch actions (re-send, expire, delete). A sticky action bar appears at the top when at least one proposal is selected. Includes a select-all checkbox in the table header.
- **Steps:**
  1. Admin navigates to `/panel/proposals/`.
  2. Admin clicks checkboxes on individual proposal rows (or the header checkbox to select all visible).
  3. Sticky batch action bar appears showing "{N} seleccionada(s)" with action buttons.
  4. Admin clicks a batch action (🔄 Re-enviar, ⏰ Expirar, or 🗑️ Eliminar).
  5. Confirmation dialog appears.
  6. Admin confirms → API call to `POST /api/proposals/bulk-action/` with `{ ids, action }`.
  7. On success, selection is cleared and proposal list refreshes.
- **Branches:**
  - [Branch A — Cancel] Admin clicks "Cancelar" → selection is cleared, action bar disappears.
  - [Branch B — Selected proposal deleted] (Ago 2026) La selección la posee `useRowSelection` y se reconcilia contra las propuestas cargadas: eliminar desde el menú de una fila seleccionada la descuenta de la barra —y sólo a ella— y la barra se va sola al quedar vacía. Antes era un `Set` en memoria que nadie revalidaba, el mismo defecto que tenía la barra de contabilidad.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-batch-actions.spec.js`
