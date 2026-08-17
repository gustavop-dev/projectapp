### FLOW: `admin-accounting-list-error-retry`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P3
- **Routes:** `/panel/accounting/*` (all subviews)
- **Description:** When a `GET /api/accounting/<entity>/` (or `dashboard/`, `change-logs/`, `settings/`) fails, the page replaces the table/summary with `AccountingErrorState` (`data-testid=accounting-error-retry`): a Spanish danger alert plus a "Reintentar" button that re-fires the page's load function. CRUD errors keep using toasts and never hide the table. Mirrors `admin-diagnostic-list-error-retry`.
- **Coverage:** ❌ Missing
- **E2E Spec:** —
