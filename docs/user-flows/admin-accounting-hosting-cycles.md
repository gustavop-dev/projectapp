### FLOW: `admin-accounting-hosting-cycles`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P2
- **Routes:** `/panel/accounting/hostings`
- **Description:** Cycle payment history per hosting (clock row action → `HostingCyclesModal`): history table (modality + amount snapshotted per paid period; consolidated "histórico" backfill rows flagged with their `cycles_represented`) plus a register form prefilled from the contract (amount = `payment_per_cycle`, current modality, paid_at = today) with an "Extender vigencia" toggle (on by default: `valid_to` advances one modality period, which re-arms the expiry notices). `total_paid`/`cycles_count` recompute from the history; deleting a cycle (ConfirmModal) recalculates but never rolls back `valid_to`.
- **Coverage:** ✅ Covered (backfill badge history, register payment with advance_validity, delete with confirm)
- **E2E Spec:** `e2e/admin/admin-accounting-hosting-billing-cycles.spec.js`
