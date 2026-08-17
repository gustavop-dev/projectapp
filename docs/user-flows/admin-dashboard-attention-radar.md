### FLOW: `admin-dashboard-attention-radar`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/`
- **Description:** Cross-module actionable list: overdue collection accounts, failed emails (7d), overdue tasks, proposals sent-unopened >7d and upcoming recurring payments, each with severity accent (danger/warning/info) and a deep-link to its module. Shows a positive state when nothing needs attention.
- **Steps:**
  1. Admin opens `/panel/` with pending items in the payload's `attention` list.
  2. Radar renders one row per item, ordered by severity, with Spanish copy and module label.
  3. Clicking a row navigates to the owning module (e.g. `/panel/tasks`).
  4. With an empty list, the radar shows "Nada requiere tu atención".
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-dashboard.spec.js`
