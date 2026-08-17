### FLOW: `admin-dashboard-stats-modals`

- **Module:** admin
- **Role:** admin (finance modal: superuser only)
- **Priority:** P2
- **Routes:** `/panel/`
- **Description:** The pulse tiles open descriptive-statistics modals (StatsModal: BaseModal 5xl + BaseTabs + ApexCharts). The "Pipeline activo" tile opens the proposals modal — tabs Tendencia (stacked trend), Embudo (horizontal funnel by status), Valor por etapa (avg value per stage) and Conversión (monthly conversion line + radial close rate) — which lazily fetches `GET /api/proposals/dashboard/` once per modal lifetime (heavy endpoint, cached in a local ref, never fetched on dashboard load). The superuser-gated "Utilidad líquida" tile opens the finance modal computed client-side from the finance block: Evolución (expected/liquid/expenses area), Utilidad (monthly utility bars + margin strip) and Deuda y compromisos (credit utilization radial + debt/pocket/recurring strip).
- **Steps:**
  1. Admin opens `/panel/` and clicks the "Pipeline activo" tile (button with hover/focus affordance).
  2. The proposals modal opens, fetches the proposals dashboard once and renders the Tendencia tab.
  3. Switching tabs (v-if panels) renders the funnel/value/conversion charts.
  4. Superuser clicks "Utilidad líquida" → finance modal renders from data already loaded.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-dashboard.spec.js`
