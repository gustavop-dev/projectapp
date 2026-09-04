### FLOW: `admin-accounting-receivables`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P1
- **Routes:** `/panel/accounting`, `/panel/accounting/incomes`
- **Description:** The “Pendiente por cobrar” card is a global, manually curated forecast. Its value is the sum of the original amounts of open expected company incomes that are both selected and green/high. The modal reads `GET /api/accounting/receivables/` and has three tabs: detail and totals grouped by traffic-light state (green/high, orange/medium, red/low and unclassified), a flat selected summary, and candidate management. Candidate management opens grouped by client, can regroup by project or switch to a classic flat list, and shows count, original total, paid amount and open balance for each group. Closing and reopening the modal restores grouped-by-client without persisting the previous presentation. Toggles and colors save immediately with `PATCH /api/accounting/incomes/:id/update/`; choosing a color also selects the row. The help legend floats inside the modal overlay so it remains fully readable. The same control and its accessible legend appear only for expected rows in the Ingresos table. Closing an income by collecting it fully, writing it off or moving it outside the company ledger removes it from the selection while preserving its last color.
- **Steps:**
  1. Superuser opens the accounting summary and sees the green selected total on “Pendiente por cobrar”.
  2. Superuser opens the card and reviews totals and rows by state.
  3. Superuser opens “Gestionar candidatos” and sees the rows grouped by client with totals per group.
  4. Superuser can regroup the filtered rows by project or switch to the classic flat list.
  5. Superuser changes a toggle or traffic-light state and the row saves immediately.
  6. Superuser can make the same change directly from an expected row in Ingresos.
- **Branches:**
  - [Display] The modal exposes all three tabs, keeps selected rows without a color under “Sin clasificar”, and renders its help legend above the modal content.
  - [Display] Candidate management defaults to client grouping on every open, supports project grouping and a classic flat list, and recalculates group totals after filtering.
  - [Success] A saved color automatically selects the expected income and updates the summary/card locally.
  - [Failure] A failed load leaves a visible retry action; a failed update preserves the previous row and raises an error notification.
  - [Error n/a] The controls only emit catalog values and booleans, so there is no user-entered validation state; invalid payloads are covered at the serializer/API layer.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-accounting-dashboard.spec.js`, `e2e/admin/admin-accounting-incomes.spec.js`
