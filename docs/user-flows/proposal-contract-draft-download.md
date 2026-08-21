### FLOW: `proposal-contract-draft-download`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid?mode=legal`
- **Description:** Download the current global contract as an informational draft. The server forces the default template, masks personal data, omits signatures, adds the `BORRADOR` watermark, and returns it from `GET /api/proposals/:uuid/contract/draft-pdf/`.
- **Outcomes:**
  - `success` — clicking **Descargar borrador** starts a PDF download from the dedicated draft endpoint.
- **Non-applicable classes:** `error` and `failure` are handled by the browser's native download surface; the proposal does not expose a separate form or recoverable download-error state. `display` is covered by the parent `proposal-contract-terms` flow.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-contract-terms.spec.js`
