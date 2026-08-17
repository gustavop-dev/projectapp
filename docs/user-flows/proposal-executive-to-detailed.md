### FLOW: `proposal-executive-to-detailed`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Client switches from executive view to the full detailed proposal view via the "Ver Propuesta Completa" button in the ProposalIndex sidebar, or via the teaser button in the executive Investment section. A branded transition overlay (esmerald background with lemon icon + loading text) plays during the mode switch. The page scrolls to top and renders all sections.
- **Steps:**
  1. Client is viewing the proposal in executive mode (filtered sections).
  2. Client opens the ProposalIndex sidebar menu.
  3. Client clicks "Ver Propuesta Completa" button at the bottom of the sidebar.
  4. ProposalIndex emits `switchToDetailed` event and closes.
  5. Branded transition overlay appears (esmerald bg, lemon bouncing icon, "Cargando propuesta completa…").
  6. After ~1s, `viewMode` switches from `'executive'` to `'detailed'`, all sections render.
  7. Overlay fades out, page scrolls to top.
  8. Client can now navigate all proposal sections.
- **Branches:**
  - [Branch A — From sidebar] Client clicks "Ver Propuesta Completa" in ProposalIndex.
  - [Branch B — From Investment teaser] Executive Investment section has a teaser button that also triggers `switchToDetailed`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-executive-to-detailed.spec.js`
- **Components:** `ProposalIndex.vue` (`switchToDetailed` emit), `[uuid]/index.vue` (`handleSwitchToDetailed`)
