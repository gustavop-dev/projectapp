### FLOW: `proposal-technical-view`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid?mode=technical`
- **Description:** Third gateway option when `technical_document` is enabled: carousel of synthetic panels from `content_json` (intro, stack, architecture, etc.) plus `proposal_closing`. PDF download uses `?doc=technical`. Tracking sends `view_mode: technical`.
- **Outcomes:**
  - `display` — the cover renders the purpose and one index card per section that carries content, each showing that section's weight (`7 capas`, `6 módulos · 38 requerimientos`).
  - `success` — clicking an index card jumps straight to that section, skipping the panels in between.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-technical-view.spec.js`
- **Components:** `ProposalViewGateway.vue`, `TechnicalDocumentPublicPanel.vue`, `[uuid]/index.vue`, `technicalProposalPanels.js`
