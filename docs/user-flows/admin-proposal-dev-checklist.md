### FLOW: `admin-proposal-dev-checklist`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/proposals/:id/edit` (Desarrollo tab, accepted proposals only)
- **Description:** Admin generates, copies and downloads a Markdown developer checklist from the Desarrollo tab (`DevChecklistTab.vue`, client-side `buildDevChecklistMarkdown`). The tab only appears when the proposal status is `accepted`.
- **Steps:**
  1. Admin opens an accepted proposal's edit page; the Desarrollo tab is visible.
  2. Admin refreshes, copies or downloads the checklist markdown.
- **Coverage:** ❌ Missing
- **E2E Spec:** — (suggested: `e2e/admin/admin-proposal-dev-checklist.spec.js`)
- **E2E Spec (suggested):** `e2e/admin/admin-proposal-update-from-json.spec.js`
