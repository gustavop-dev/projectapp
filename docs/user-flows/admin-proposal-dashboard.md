### FLOW: `admin-proposal-dashboard`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/` (Dashboard KPI section)
- **Description:** View global KPI dashboard for all proposals: total proposals, conversion rate, average time to first view, average time to response, average value by status, status distribution, top rejection reasons, monthly trends, discount vs no-discount close rates, win rate by predominant tracking view mode (ejecutiva / completa / técnica), and top drop-off section scoped to commercial section types (excluye doc. técnico y paneles sintéticos).
- **Steps:**
  1. Admin navigates to `/panel/`.
  2. ProposalDashboard component loads data from `GET /api/proposals/dashboard/`.
  3. KPI cards render with total proposals, conversion rate, avg time metrics.
  4. Status distribution chart renders.
  5. Top rejection reasons list renders.
  6. Monthly trend data renders.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-dashboard.spec.js`
