### FLOW: `proposal-calculator-selected-first`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** When the calculator modal opens, groups containing pre-selected (`default_selected`) modules are sorted to the top so the client sees included modules first without scrolling.
- **Steps:**
  1. Client opens the proposal and navigates to the Investment section.
  2. Client clicks "Personalizar tu inversión".
  3. Calculator modal opens with selected module groups sorted to the top.
  4. Unselected module groups appear below.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-calculator-modules.spec.js`
