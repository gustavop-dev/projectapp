### FLOW: `proposal-share`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Client shares the proposal with a team member or stakeholder via the share button. A tracked share link is created, and the recipient receives an email notification.
- **Steps:**
  1. User views the proposal.
  2. User clicks the share button (ShareProposalButton component).
  3. User fills in recipient name and email.
  4. API call to `POST /api/proposals/:uuid/share/`.
  5. Backend creates a ProposalShareLink record.
  6. Share notification email is sent to the recipient.
  7. Success feedback displays.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-share.spec.js`
