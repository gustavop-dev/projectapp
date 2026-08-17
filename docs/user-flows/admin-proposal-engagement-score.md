### FLOW: `admin-proposal-engagement-score`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Analytics tab)
- **Description:** ProposalAnalytics displays an engagement score (0-100) per proposal, computed from recent sessions, investment section time, unique stakeholders, response recency, and revisits.
- **Steps:**
  1. Admin opens the Analytics tab for a proposal.
  2. Analytics loads from `GET /api/proposals/:id/analytics/` including `engagement_score`.
  3. Engagement score card renders with color-coded level (green ≥70, yellow ≥40, red <40) and contextual recommendation text.
- **Coverage:** ✅ Covered — `frontend/e2e/admin/admin-proposal-analytics.spec.js`
