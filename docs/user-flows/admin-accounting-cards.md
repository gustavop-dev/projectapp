### FLOW: `admin-accounting-cards`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P2
- **Routes:** `/panel/accounting/cards`
- **Description:** Weekly credit-card balance snapshots (CardBalanceSnapshot): list with a latest-debt-per-card chip, filters (date range, debt range, card multi-select) and search; modal create (snapshot date defaults to today, card selected from a dropdown fed by the CreditCard catalog — see `admin-accounting-card-catalog`), edit prefill and ConfirmModal delete. Since Jul 2026 the Deuda input is gone: debt is server-computed as cupo − disponible for catalog cards (the form previews it and blocks disponible > cupo); legacy card names outside the catalog stay editable and keep their stored debt. Registering a snapshot dated on/after the cycle Friday silences the weekly card-debt reminder email. The card filter opens preselected with the active catalog cards (removable chips — clearing them surfaces historical card names again), and its options are the union of catalog names and names used by snapshots, so a registered card is filterable before its first snapshot. A saved tab in the URL wins over the preselection.
- **Steps:**
  1. Superuser opens `/panel/accounting/cards` (subnav "Tarjetas" or the dashboard "Ver historial de tarjetas" link). The card filter arrives preselected with the registered (active catalog) cards, shown as removable chips with the filter count at 1; the latest-debt chip covers only those cards.
  2. "Nuevo registro" opens the modal with today's date preselected; superuser picks the card from the catalog dropdown and fills the available amount — the computed debt (cupo − disponible) previews below the input.
  3. Submit POSTs `/api/accounting/card-snapshots/create/` without `debt_amount` (server computes it) → success toast + audit + email.
  4. Row edit prefills the modal (a legacy card name not in the catalog is injected as an extra option) and PATCHes `.../update/`; delete asks for confirmation.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-accounting-cards.spec.js`
