### FLOW: `proposal-schedule-followup-reminder`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** After rejecting with reason "not the right time", the client clicks the "🔔 remind me later" CTA in the recovery card (`ProposalClosing.vue` `scheduleReminder`), which POSTs `proposals/:uuid/schedule-followup/` and flips the button to a scheduled-confirmation state. The only recovery CTA that mutates server state.
- **Steps:**
  1. Client rejects the proposal choosing "not the right time".
  2. Recovery card renders with the reminder CTA.
  3. Client clicks it → `POST /api/proposals/:uuid/schedule-followup/`.
  4. Button flips to the scheduled ✅ state.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-rejection-recovery.spec.js` (schedule-followup test)
