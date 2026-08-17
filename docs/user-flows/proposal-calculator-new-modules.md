### FLOW: `proposal-calculator-new-modules`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The investment calculator displays additional default modules: Email Marketing (10%), i18n (15%), and Gift Cards (20%). KPI Dashboard has been removed from the calculator and is now included by default (like Analytics). Conversion Tracking moved to integrations (see `proposal-calculator-integrations`).
- **Steps:**
  1. Client opens the calculator modal.
  2. Email Marketing module appears unselected with price as +10% of total.
  3. i18n module appears unselected with price as +15% of total.
  4. Gift Cards module appears unselected with price as +20% of total.
  5. Client toggles modules → total investment and timeline update in real-time.
  6. KPI Dashboard is NOT shown in the modal (included by default like Analytics module).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-calculator-new-modules.spec.js`
