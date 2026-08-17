### FLOW: `admin-accounting-dashboard`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P1
- **Routes:** `/panel/accounting`
- **Description:** Annual financial overview fed by `GET /api/accounting/dashboard/?year=`: expected vs liquid income, expenses, expected/liquid utility, pocket balance, per-partner cards, 12-month breakdown, operative cost cards and latest card snapshots. The hero "Utilidad líquida" card embeds a full-width "Utilidad por mes" ApexCharts line (axes + money tooltips) filling the card body (replaced the tiny corner sparkline, Jul 2026). Company totals aggregate the company ledger only (personal-ledger records are excluded); the "ProjectApp (Empresa)" card shows the full company ledger, and Gustavo/Carlos cards combine their company participation with their personal ledger (breakdown line shown when personal activity exists). Year selector re-fetches the summary and persists as a query param. The "Evolución" section renders two ApexCharts — expected vs liquid vs expenses per month, and card-debt evolution from snapshots — filtered by the year plus a client-side month-range selector; a "Exportar Excel" button downloads the full workbook and the Tarjetas table links to the cards history. The subnav orders Bolsillo second, right after Resumen.
- **Steps:**
  1. Superuser opens `/panel/accounting`.
  2. Stat cards render the summary totals; partner cards show Gustavo/Carlos (participation + personal) and ProjectApp (Empresa) company totals.
  3. Monthly table lists the 12 months with a totals row.
  4. Superuser switches the year → summary re-fetches.
  5. "Nuevo ingreso" opens the income modal from the dashboard.
- **Branches:**
  - [Branch A — gating] Staff non-superuser navigating to any `/panel/accounting*` route is redirected to `/panel`; the Accounting sidebar section is hidden.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-accounting-dashboard.spec.js`
