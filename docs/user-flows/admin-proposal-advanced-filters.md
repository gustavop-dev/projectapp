### FLOW: `admin-proposal-advanced-filters`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Admin uses advanced filter panel with 11 dimensions (status, project type, market type, currency, language, investment range, heat score range, view count range, created date range, last activity date range, active status) and saves filter combinations as named tabs (max 12) with localStorage persistence and URL sync.
- **Steps:**
  1. Admin navigates to `/panel/proposals/` and clicks "Filtros" toggle button.
  2. Filter panel expands with responsive grid of filter controls.
  3. Admin selects filter values (e.g., status pills, project type dropdown, date range).
  4. Proposal table updates in real-time (client-side filtering, single-pass).
  5. Admin clicks "+" tab button → inline input appears → types tab name → clicks "Guardar".
  6. New named tab appears in tab bar; filters are persisted to localStorage.
  7. Admin reloads page → saved tabs persist; clicking a tab restores its filters.
  8. Admin right-clicks tab context menu → "Renombrar" or "Eliminar".
  9. "Todas" tab resets all filters. "Limpiar filtros" button clears active filters.
  10. URL updates with `?tab=<tabId>` for deep-linking.
- **Branches:**
  - [Branch A — Tab limit] When 12 tabs exist, "+" button is disabled with tooltip.
  - [Branch B — Mobile] Tab bar collapses to `<select>` dropdown below `md` breakpoint.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-advanced-filters.spec.js`
