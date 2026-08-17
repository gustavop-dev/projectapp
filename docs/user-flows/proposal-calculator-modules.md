### FLOW: `proposal-calculator-modules`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** Calculator modal displays core calculator modules in order: PWA (40%), AI (invite-only), Conversiones Inteligentes (invite-only), Facturación Electrónica (60%), Pasarela Internacional (20%), Pasarela Regional (20%), Email Marketing (10%), Reportes y Alertas (20%, selected by default), Multi-idioma (15%). An informational badge at the **top** of the modal explains items are optional. Selecting a calculator module **adds** ~1 week to the timeline.
- **Steps:**
  1. Client navigates to the Investment section and clicks "Personalizar tu inversión".
  2. Calculator modal opens with informational badge at the top.
  3. Modules appear in the specified order: PWA, AI, Smart Conversions, Electronic Invoicing, International Payments, Regional Payments, Email Marketing, Reports & Alerts, Multi-idioma.
  4. PWA module appears unselected by default, with price as +40% of total.
  5. AI module appears with "Agendar llamada" label instead of price and a purple creative invite note.
  6. Reports & Alerts module appears selected by default with price as +20% of total.
  7. Selecting a module adds ~1 week to estimated timeline; deselecting an investment module reduces ~1 week.
  8. Client confirms selection → modal closes, total updates on Investment section.
- **Branches:**
  - [Branch A — AI invite] Client selects AI module → invite note visible, no cost added.
  - [Branch B — FR integration] Selected calculator modules appear in Functional Requirements section.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-calculator-modules.spec.js`
