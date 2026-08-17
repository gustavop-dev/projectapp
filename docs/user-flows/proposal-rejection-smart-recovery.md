### FLOW: `proposal-rejection-smart-recovery`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** After a client rejects a proposal, context-specific recovery cards render based on the rejection reason, each with appropriate CTAs (e.g., schedule call, adjust budget, revisit later).
- **Steps:**
  1. Client rejects the proposal and sees the rejection confirmation screen.
  2. Recovery cards render based on the rejection reason provided.
  3. Each card shows a relevant CTA (schedule a call, request changes, revisit later).
  4. Client can click a CTA to take the suggested recovery action.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-rejection-recovery.spec.js`
