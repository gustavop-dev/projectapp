### FLOW: `proposal-comment-from-closing`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Client submits a written comment from the proposal closing panel via a comment modal. This is distinct from the full accept/reject/negotiate response flow.
- **Steps:**
  1. Client is viewing the proposal closing section.
  2. Client opens the comment modal from the closing panel.
  3. Client types a comment and submits.
  4. Comment is recorded; confirmation feedback shown.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-comment-flow.spec.js`
