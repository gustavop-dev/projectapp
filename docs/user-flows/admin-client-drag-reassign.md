### FLOW: `admin-client-drag-reassign`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`
- **Description:** Reassign a proposal or diagnostic to a different client by dragging its row (from an expanded client card) and dropping it on another client's card header, or on the matching zone of another expanded client: proposals on the proposals zone, diagnostics on the diagnostics zone (zones are type-matched — a zone of the other type ignores the drop; the header accepts both types). Native HTML5 DnD; every drop target highlights on hover. The drop PATCHes `client_id` on the item's update endpoint, then refreshes both affected clients + the list silently and in place (no loading skeleton — the page does not visually "reload"), and shows a success toast with a "Deshacer" action (reverse PATCH). Diagnostics also rebuild their client snapshot (`sync_diagnostic_snapshot`). Touch devices are not supported — fallback is the client picker on the edit pages.
- **Steps:**
  1. Admin expands a client card to reveal its proposals/diagnostics tables.
  2. Admin drags a row (data-testid: `client-proposal-row-<id>` / `client-diagnostic-row-<id>`).
  3. Hovering another client header (data-testid: `client-header-<id>`) highlights it; on an expanded client, the matching zone (data-testid: `client-proposals-zone-<id>` / `client-diagnostics-zone-<id>`) also highlights and accepts the drop. Dropping on the source client, or on a zone of the other item type, is a no-op.
  4. Drop → `PATCH /api/proposals/:id/update/` or `PATCH /api/diagnostics/:id/update/` with `{client_id}`.
  5. Both clients' expanded details refetch and overwrite in place, and the list refreshes silently (`fetchClients({silent:true})`, no skeleton) respecting the active tab; the toast offers "Deshacer".
- **Coverage:** ✅ Covered — proposal/diagnostic drops on headers and zones, same-client and type-mismatch no-ops, and the "Deshacer" toast action reassigning the item back to its source client (2026-07-23).
- **E2E Spec:** `e2e/admin/admin-clients-drag-reassign.spec.js`
- **Backend Tests:** `content/tests/views/test_diagnostic_views_gaps.py::test_update_diagnostic_with_client_id_reassigns_and_resyncs_snapshot`, `content/tests/views/test_proposal_clients_views.py::TestProposalCreateWithClientId::test_proposal_update_with_client_id_switches_profile_and_resyncs_snapshot`
