### FLOW: `proposal-download-pdf`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Download a proposal as PDF.
- **Steps:**
  1. User views the proposal.
  2. User clicks the download PDF button.
  3. API call to `GET /api/proposals/:uuid/pdf/`.
  4. PDF file downloads to user's device.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-pdf.spec.js`
