### FLOW: `admin-accounting-dashboard`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P1
- **Routes:** `/panel/accounting`
- **Description:** Annual financial overview fed by `GET /api/accounting/dashboard/?year=`: expected vs liquid income, expenses, expected/liquid utility, pocket balance, per-partner cards, 12-month breakdown, operative cost cards and latest card snapshots. The hero “Utilidad líquida” embeds the former utility-statistics modal as a default-open accordion with evolution, margin and partner tabs; the old “Utilidad por mes” mini-chart and statistics icon/modal are gone. Hero cards align at their natural height so the statistics content no longer leaves a large blank column. Company totals aggregate the company ledger only (personal-ledger records are excluded); the “ProjectApp (Empresa)” card shows the full company ledger, and Gustavo/Carlos cards combine their company participation with their personal ledger. Year selector re-fetches the summary and persists as a query param. The “Evolución” section renders two theme-aware ApexCharts — expected vs liquid vs expenses per month, and card-debt evolution from snapshots — filtered by the year plus a client-side month-range selector; a “Exportar Excel” button downloads the workbook and the Tarjetas table links to card history. The subnav orders Bolsillo second, right after Resumen. The Contabilidad quick-access group links to Cuentas de cobro instead of Ads; Ads remains available in the internal accounting subnav.
- **Steps:**
  1. Superuser opens `/panel/accounting`.
  2. Stat cards render the summary totals; partner cards show Gustavo/Carlos (participation + personal) and ProjectApp (Empresa) company totals.
  3. Monthly table lists the 12 months with a totals row.
  4. The default-open utility accordion exposes evolution, margin and partner views and can be collapsed.
  5. Superuser switches the year → summary re-fetches.
  6. “Nuevo ingreso” opens the income modal from the dashboard.
  7. “Cuentas de cobro” in the accounting quick-access menu opens `/panel/accounting/collections`, and no Ads shortcut is rendered there.
- **Branches:**
  - [Branch A — gating] Staff non-superuser navigating to any `/panel/accounting*` route is redirected to `/panel`; the Accounting sidebar section is hidden.
  - [Success] Superuser uses the accounting quick-access link to reach Cuentas de cobro.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-accounting-dashboard.spec.js`
