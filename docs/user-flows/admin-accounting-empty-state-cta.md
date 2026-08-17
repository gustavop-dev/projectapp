### FLOW: `admin-accounting-empty-state-cta`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P4
- **Routes:** `/panel/accounting/*` (list subviews)
- **Description:** With zero records, lists render `BaseEmptyState` with a primary "Nuevo <entidad>" action that opens the create modal; with active filters and zero matches, the action becomes "Limpiar filtros" and resets the filter panel.
- **Coverage:** ❌ Missing
- **E2E Spec:** —

### 23.1 Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-accounting-dashboard` | admin | superuser | P1 | ✅ Covered | `e2e/admin/admin-accounting-dashboard.spec.js` |
| `admin-accounting-expected-detail` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-dashboard.spec.js` |
| `admin-accounting-stats-modals` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-dashboard.spec.js` |
| `admin-accounting-income-crud` | admin | superuser | P1 | ✅ Covered | `e2e/admin/admin-accounting-incomes.spec.js` |
| `admin-accounting-income-client` | admin | superuser | P1 | ✅ Covered | `e2e/admin/admin-accounting-incomes.spec.js` |
| `admin-accounting-filters` | admin | superuser | P1 | ✅ Covered | `e2e/admin/admin-accounting-filters.spec.js` |
| `admin-accounting-expenses-crud` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-expenses-hostings.spec.js` |
| `admin-accounting-hostings` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-expenses-hostings.spec.js` |
| `admin-accounting-hosting-client` | admin | superuser | P1 | ✅ Covered | `e2e/admin/admin-accounting-expenses-hostings.spec.js` |
| `admin-accounting-pocket` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-pocket-recurring.spec.js` |
| `admin-accounting-recurring` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-pocket-recurring.spec.js` |
| `admin-accounting-history` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-ads-history-settings.spec.js` |
| `admin-accounting-history-filters` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-history-filters.spec.js` |
| `admin-accounting-history-diagnosis` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-history-filters.spec.js` |
| `admin-accounting-cards` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-cards.spec.js` |
| `admin-accounting-export` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-export.spec.js` |
| `admin-accounting-settings` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-ads-history-settings.spec.js` |
| `admin-accounting-card-catalog` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-statements-card-catalog.spec.js` |
| `admin-accounting-ads` | admin | superuser | P3 | ✅ Covered | `e2e/admin/admin-accounting-ads-history-settings.spec.js` |
| `admin-accounting-hosting-billing` | admin | superuser | P1 | ✅ Covered | `e2e/admin/admin-accounting-hosting-billing-cycles.spec.js` |
| `admin-accounting-collections` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-collections.spec.js` |
| `admin-accounting-collection-detail` | admin | superuser | P1 | ✅ Covered | `e2e/admin/admin-accounting-collections.spec.js` |
| `admin-accounting-collection-create` | admin | superuser | P1 | ✅ Covered | `e2e/admin/admin-accounting-collections.spec.js`, `e2e/admin/admin-accounting-incomes.spec.js` |
| `admin-accounting-hosting-cycles` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-accounting-hosting-billing-cycles.spec.js` |
| `admin-accounting-hosting-inline-edit` | admin | superuser | P3 | ❌ Missing | — |
| `admin-accounting-settings-reset-tabs` | admin | superuser | P3 | ❌ Missing | — |
| `admin-accounting-list-error-retry` | admin | superuser | P3 | ✅ Covered | `e2e/admin/admin-accounting-error-retry.spec.js` |
| `admin-accounting-empty-state-cta` | admin | superuser | P4 | ✅ Covered | `e2e/admin/admin-accounting-empty-state.spec.js` |
