### FLOW: `admin-proposal-win-rate-dashboard`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Dashboard displays win rate segmented by project type, market type, and combination. Backend computes accepted/(accepted+rejected+expired) per type.
- **Steps:**
  1. Admin opens the KPI Dashboard on the proposals page.
  2. Dashboard loads data from `GET /api/proposals/dashboard/` including `win_rate_by_project_type`, `win_rate_by_market_type`, `win_rate_by_combination`.
  3. Two side-by-side bar charts show win rates by project type and market type (best type highlighted).
  4. Combination table shows project×market cross-tab for combos with ≥2 proposals.
- **Coverage:** ✅ Covered — `frontend/e2e/admin/admin-proposal-win-rate.spec.js`
