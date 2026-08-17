### FLOW: `admin-accounting-stats-modals`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P2
- **Routes:** `/panel/accounting`
- **Description:** Descriptive-statistics modals on the Resumen. Triggers: "Ingresos líquidos", "Gastos {year}" (relabeled from "Costo operativo mensual"; now shows `expenses_total` with the recurring cost as sub) and "Deuda tarjetas" cards are clickable buttons, and the hero Utilidad card exposes an "Estadísticas" button. Modals (StatsModal + StatsSummaryStrip + chart primitives over useChartTheme): Ingresos (evolución esperado vs líquido área, % de cobro radial + mensual, top conceptos), Gastos (evolución con promedio anotado, donut Negocio/Personal, recurrente vs variable, top conceptos), Utilidad (evolución, márgenes, donut + detalle por socio) and Tarjetas (evolución de deuda por tarjeta, uso del cupo contra el catálogo, histórico de cortes). Income/expense tabs feed from `GET /api/accounting/stats/?year=` (lazy, cached per year in the store, reset on year change); utility/cards tabs compute client-side.
- **Steps:**
  1. Superuser clicks a stat card (or the hero "Estadísticas" button) on the Resumen.
  2. The modal opens; income/expense modals fetch `accounting/stats/` once per year (loading skeleton meanwhile).
  3. Tabs switch between chart views (v-if panels so ApexCharts mounts visible).
  4. Changing the page year drops the cached stats and the next open refetches.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-accounting-dashboard.spec.js`
