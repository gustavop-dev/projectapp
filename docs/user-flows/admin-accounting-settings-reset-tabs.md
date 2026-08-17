### FLOW: `admin-accounting-settings-reset-tabs`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P3
- **Routes:** `/panel/accounting/settings`
- **Description:** Restore the seeded default filter tabs per accounting view: the "Pestañas de filtros guardados" card lists the 6 views (Ingresos/Gastos/Hostings/Bolsillo/Recurrentes/Ads), each with a "Restablecer" button that, after a ConfirmModal warning that custom tabs will be deleted, POSTs `accounts/saved-filter-tabs/reset/` (atomic delete + re-seed from `DEFAULT_FILTER_TABS`) and toasts the result. New users get the defaults automatically on first GET.
- **Coverage:** ❌ Missing
- **E2E Spec:** —
