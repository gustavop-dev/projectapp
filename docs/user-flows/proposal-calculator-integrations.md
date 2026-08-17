### FLOW: `proposal-calculator-integrations`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The investment calculator displays integration groups as individually toggleable calculator modules: International Payments (20%), Regional Payments Colombia (20%), Electronic Invoicing / DIAN (60%), and Conversion Tracking Meta & Google Ads (invite-only, 0%). Each was previously grouped under a single `integrations_api` group and now has its own pricing, selection state, and invite attributes.
- **Steps:**
  1. Client opens the calculator modal.
  2. International Payments integration appears unselected with price as +20% of total.
  3. Regional Payments (Colombia) integration appears unselected with price as +20% of total.
  4. Electronic Invoicing integration appears unselected with price as +60% of total.
  5. Conversion Tracking integration appears with "Agendar llamada" invite-only label and invite note.
  6. Client selects International Payments → total investment increases by 20%.
  7. Client selects Electronic Invoicing → total investment increases by 60%.
- **Branches:**
  - [Branch A — Conversion Tracking invite] Client sees invite note, no cost added.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-calculator-integrations.spec.js`
