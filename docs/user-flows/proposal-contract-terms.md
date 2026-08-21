### FLOW: `proposal-contract-terms`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`, `/proposal/:uuid?mode=legal`
- **Description:** Fourth gateway option, named **Contrato y condiciones**, available only when the proposal is in Spanish and its visibility flag is enabled. It renders two panels from the current global contract template: an introduction with a clause index and one continuous contract document inside a bordered, layered paper surface. This content is independent from the proposal section JSON and from any proposal-specific contract attachment.
- **Outcomes:**
  - `display` — the client reaches the mode through the gateway and sees the generic explanation, draft notice, and real clause titles inside one accessible document surface returned by `GET /api/proposals/:uuid/contract-terms/`.
  - `success` — selecting a clause in the index opens the document panel and scrolls to that clause's stable anchor.
  - `error` — `?mode=legal` cannot bypass the Spanish-language and per-proposal visibility gates; the regular gateway remains visible without the legal option.
  - `failure` — if the global template is temporarily unavailable, the introduction explains the failure and lets the client retry.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-contract-terms.spec.js`
- **Components:** `ProposalViewGateway.vue`, `ContractTermsOverview.vue`, `ContractTermsDocument.vue`, `[uuid]/index.vue`
