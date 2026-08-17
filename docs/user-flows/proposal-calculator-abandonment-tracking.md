### FLOW: `proposal-calculator-abandonment-tracking`

- **Module:** proposal
- **Role:** guest (via shared UUID link) / system
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The calculator modal tracks whether the client confirms or abandons their module selection. On close without confirming, an `abandoned` event is sent. On confirm, a `confirmed` event is sent. Both are stored as `ProposalChangeLog` entries and aggregated in the admin dashboard as `calc_abandonment_rate` and `dropped_modules`.
- **Steps:**
  1. Client opens the calculator modal in the Investment section.
  2. Client toggles modules (selects/deselects).
  3. [Branch A — Confirm] Client clicks "Confirmar selección" → `confirmed` event sent via `POST /api/proposals/:uuid/track-calculator/`.
  4. [Branch B — Abandon] Client closes modal without confirming → `abandoned` event sent automatically.
  5. Backend creates `ProposalChangeLog` with `calc_confirmed` or `calc_abandoned` change type.
  6. Dashboard aggregates data: `calc_abandonment_rate` = abandoned / (abandoned + confirmed), `dropped_modules` = most frequently deselected modules.
- **Coverage:** ⚠️ Backend-only
- **Backend Tests:** `content/tests/views/test_proposal_views.py`
