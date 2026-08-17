### FLOW: `admin-accounting-expected-detail`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P2
- **Routes:** `/panel/accounting`
- **Description:** The "Pendiente por cobrar · {mes}" stat card is a clickable button that opens a read-only modal with the company expected incomes of the real current month (`GET /api/accounting/incomes/?kind=expected&ledger=company&date_from&date_to`, range derived from `expected_current_month.period` — not the year selector). Table: concepto, período, total, abonado, pendiente (per-row clamped) and payment-status pill; the footer's Pendiente sum equals the card total. No row actions.
- **Steps:**
  1. Superuser clicks the expected-month card on the Resumen.
  2. The modal fetches the month's expected incomes and renders the detail table with loading/empty/error states.
  3. "Cerrar" dismisses the modal.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-accounting-dashboard.spec.js`
