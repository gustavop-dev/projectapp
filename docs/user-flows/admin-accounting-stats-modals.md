### FLOW: `admin-accounting-stats-modals`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P2
- **Routes:** `/panel/accounting`
- **Description:** Descriptive-statistics surfaces on the Resumen. “Ingresos líquidos”, “Gastos {year}” and “Deuda tarjetas” remain clickable cards that open StatsModal with their tabbed charts. Utility statistics moved into the “Utilidad líquida” hero as a default-open accordion, so there is no utility statistics icon or modal. All charts share `useChartTheme`, including foreground, legend, tooltip and center-label colors for dark mode. Income/expense views read `GET /api/accounting/stats/?year=` lazily and cache per year; utility and card views compute client-side.
- **Steps:**
  1. Superuser clicks the income, expense or card-debt stat card on the Resumen.
  2. The modal opens; income/expense modals fetch `accounting/stats/` once per year (loading skeleton meanwhile).
  3. Tabs switch between chart views (v-if panels so ApexCharts mounts visible).
  4. Utility tabs are immediately available inside the default-open hero accordion and can be collapsed.
  5. Changing the page year drops the cached stats and the next modal open refetches.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-accounting-dashboard.spec.js`
