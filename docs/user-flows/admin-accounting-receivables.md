### FLOW: `admin-accounting-receivables`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P1
- **Routes:** `/panel/accounting`, `/panel/accounting/incomes`
- **Description:** The “Pendiente por cobrar” card is a global, manually curated forecast. Its value is the sum of the original amounts of open expected company incomes that are both selected and green/high. The modal reads `GET /api/accounting/receivables/` and has three tabs: detail and totals grouped by traffic-light state (green/high, orange/medium, red/low and unclassified), a flat selected summary, and candidate management. Toggle and color save independently with `PATCH /api/accounting/incomes/:id/update/`: choosing a level never activates the switch. A soft semantic circle accompanies the full level label, and an unassigned level renders a neutral circle with “Sin clasificar”. The same contract appears in the Ingresos list, create/edit form and income detail. Closing an income by collecting it fully, writing it off or moving it outside the company ledger removes it from the selection while preserving its last color; existing states are not rewritten.
- **Steps:**
  1. Superuser opens the accounting summary and sees the green selected total on “Pendiente por cobrar”.
  2. Superuser opens the card and reviews totals and rows by state.
  3. Superuser reviews the flat selection or opens “Gestionar candidatos”.
  4. Superuser changes a toggle or traffic-light state and the row saves immediately.
  5. Superuser can make the same change directly from an expected row in Ingresos.
- **Branches:**
  - [Display] The modal exposes all three tabs and keeps selected rows without a color under “Sin clasificar”.
  - [Success] A saved color leaves the manual switch unchanged; only toggling inclusion changes the forecast and its green summary/card.
  - [Failure] A failed load leaves a visible retry action; a failed update preserves the previous row and raises an error notification.
  - [Error n/a] The controls only emit catalog values and booleans, so there is no user-entered validation state; invalid payloads are covered at the serializer/API layer.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-accounting-dashboard.spec.js`, `e2e/admin/admin-accounting-incomes.spec.js`
