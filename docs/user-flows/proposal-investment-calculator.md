### FLOW: `proposal-investment-calculator`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **API:** (client-side only — no API call for toggling)
- **Description:** Client reviews readable payment rows in the Investment section, opens the calculator modal, toggles optional feature modules on/off, sees dynamic total investment and estimated timeline update in real time, and confirms or cancels the selection.
- **Outcomes:**
  - `display` — at laptop width, every payment keeps amount, currency, and `+ IVA` together on one line.
  - `success` — the client opens the calculator, changes optional modules, and confirms the resulting selection.
- **Steps:**
  1. Client views the proposal and navigates to the Investment section.
  2. The payment list leaves room for its labels and keeps each complete tax-qualified amount together.
  3. Client clicks "Personalizar tu inversión" to open the calculator modal.
  4. Client toggles optional feature modules — total investment and timeline update dynamically.
  5. Client clicks "Confirmar selección" → modal closes; closing section reflects updated total.
  6. [Branch B — Abandon] Client closes modal without confirming → selection reverts.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-investment-calculator.spec.js`
