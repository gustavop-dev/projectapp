### FLOW: `admin-proposal-log-activity`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Activity tab)
- **Description:** Admin manually logs a seller activity on a proposal. Activity types include call, meeting, follow-up, and note. The activity is stored as a ProposalChangeLog entry and updates `last_activity_at`.
- **Steps:**
  1. Admin opens a proposal edit page and navigates to the Activity tab.
  2. Admin selects an activity type and enters a description.
  3. Admin submits → API call to `POST /api/proposals/:id/log-activity/`.
  4. Backend creates a ProposalChangeLog entry and updates `last_activity_at`.
  5. Activity timeline refreshes with the new entry.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-log-activity.spec.js`
