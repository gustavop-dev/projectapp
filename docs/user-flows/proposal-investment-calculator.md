### FLOW: `proposal-investment-calculator`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **API:** (client-side only — no API call for toggling)
- **Description:** Client opens investment calculator modal from the closing/investment section, toggles optional feature modules on/off, sees dynamic total investment and estimated timeline update in real time, and confirms or cancels the selection.
- **Steps:**
  1. Client views the proposal and navigates to the Investment section.
  2. Client clicks "Personalizar tu inversión" to open the calculator modal.
  3. Client toggles optional feature modules — total investment and timeline update dynamically.
  4. Client clicks "Confirmar selección" → modal closes; closing section reflects updated total.
  5. [Branch B — Abandon] Client closes modal without confirming → selection reverts.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-investment-calculator.spec.js`
