### FLOW: `admin-accounting-income-reminder-mute`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P1
- **Routes:** `/panel/accounting/incomes`
- **API:** `POST /api/accounting/incomes/:id/mute/`
- **Description:** An uncollected expected income exposes **Silenciar avisos** in its row menu. The modal defaults to a dated silence with a future date prefilled, also offers an explicit indefinite mode, and refuses empty or non-future resume dates. A successful write updates the row in place: **Silenciado** or **Silenciado hasta {fecha}** appears beside its collection state. Opening the same menu then offers **Reactivar avisos**, which clears both mute fields without a confirmation. API failures leave the modal open and the row unchanged. The dedicated endpoint writes the accounting audit trail but deliberately sends no accounting-change email.
- **Steps:** navigate from the panel to Ingresos → open one pending expected income's actions → Silenciar avisos → choose a future date or Indefinidamente → save → verify the visible badge; reopen the row and reactivate when follow-up should resume.
- **Branches:** a date that is empty, today or earlier is blocked inline; a failed request preserves the prior state; paid, liquid and lost rows do not expose the action.
- **Coverage:** ✅ Covered — display, dated and indefinite success, manual reactivation, validation error and server failure.
- **E2E Spec:** `e2e/admin/admin-accounting-incomes.spec.js`
