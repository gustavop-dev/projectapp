### FLOW: `proposal-engagement-tracking`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Automatic tracking of client engagement while viewing a proposal. The frontend composable `useProposalTracking` sends section-level time data to the backend, which records view events and section views, detects stakeholders by IP, and triggers smart follow-up alerts.
- **Steps:**
  1. User opens a proposal page.
  2. `useProposalTracking` composable initializes and generates a session ID.
  3. As user navigates sections, time spent per section is recorded.
  4. Periodically, engagement data is sent via `POST /api/proposals/:uuid/track/`.
  5. Backend creates/updates ProposalViewEvent and ProposalSectionView records.
  6. [Optional] If ≥3 unique sessions detected, a revisit alert email is sent to the admin.
  7. [Optional] If a new IP is detected, a stakeholder detection alert is sent.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-engagement-tracking.spec.js`
