### FLOW: `admin-accounting-history-filters`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P2
- **Routes:** `/panel/accounting/history`
- **Description:** Finding a send or a change takes one click on a predefined tab or a few filters, instead of scanning the list by eye. Each subtab runs its own `useAccountingFilters` instance (saved-tab views `accounting_history_sends` / `accounting_history_changes`) and, because Historial is the one accounting view that paginates server-side, the filter state is translated into query params by `buildExportParams` rather than filtering loaded rows. Under the filter row sits the strip (`ProposalFilterTabs`, the PA-44 standard): **Fallidos**, **Hoy** and **Últimos 7 días** are builtin — a stored date would freeze on the day it was seeded, and Fallidos has to sit second because it is where anyone goes when a notice did not arrive — while **Recordatorios de cobro**, **Cambios contables** and **Eliminaciones** are seeded rows that Configuración restores. Every tab carries its count, "Todas" and the honest (0) included, from `POST /api/accounting/history/tab-counts/`; the overflow collapses into a "+N" menu that hoists the selected tab back into view.
- **Steps:**
  1. Superuser opens `/panel/accounting/history`; the strip renders with a count per tab and the filter row collapsed behind its toggle.
  2. Clicking a predefined tab narrows the list and stamps both `?<subtab>Tab=` and the filter keys in the URL, so the query can be bookmarked and shared.
  3. Editing the controls under a builtin un-lights the tab; "Limpiar filtros" deselects it and clears the URL.
  4. "+" saves the active combination as an own tab (max 12 per view), which then behaves like any other tab and can be renamed, reordered, hidden or deleted.
  5. Arriving from a hosting, an income or a cuenta de cobro lands with `?tab=sends&entity_type=…&object_id=…` already applied.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-accounting-history-filters.spec.js`
