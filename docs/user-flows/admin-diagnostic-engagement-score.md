### FLOW: `admin-diagnostic-engagement-score`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` (Analytics tab — Engagement Score card)
- **Description:** Engagement score card renders with the correct color-coded label based on score value: ≥70 → "Alto engagement — prioridad de follow-up" (emerald), 40–69 → "Engagement moderado" (yellow), <40 → "Bajo engagement — necesita atención" (red). Card is hidden when `engagement_score` is null.
- **Steps:**
  1. Admin opens Analytics tab with score ≥70 → sees "Alto engagement" in emerald.
  2. Admin opens Analytics tab with score <40 → sees "Bajo engagement" in red.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-analytics.spec.js`
