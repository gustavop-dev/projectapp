### FLOW: `admin-client-delete-orphan`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`
- **Description:** Delete an orphan client (zero proposals, platform projects, diagnostics, accounting incomes and hostings — the five-block guard) via the trash icon that appears only on orphan rows. A confirm modal prevents accidental deletion.
- **Steps:**
  1. Admin navigates to `/panel/clients/` (or switches to Huérfanos tab).
  2. Orphan client rows show a trash icon (data-testid: `client-delete-<id>`).
  3. Admin clicks the trash icon.
  4. ConfirmModal appears with warning text.
  5. Admin confirms → `DELETE /api/proposals/client-profiles/:id/delete/`.
  6. Client row is removed from the list (store filters it out client-side).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-mini-crm-clients.spec.js`
- **Backend Tests:** `content/tests/views/test_proposal_clients_views.py::TestDeleteProposalClient`, `content/tests/views/test_proposal_clients_views.py::TestOrphanFlagTransitionsAfterProposalDelete`
