### FLOW: `admin-client-delete-protected`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`
- **Description:** Active clients (those with linked proposals or platform projects) do NOT show the delete trash icon. The backend also enforces this with a 400 + `client_has_proposals` / `client_has_projects` error code if the API is called directly.
- **Steps:**
  1. Admin navigates to `/panel/clients/`.
  2. Clients with `is_orphan: false` render WITHOUT a trash icon.
  3. Attempting DELETE via API returns `400 { error: 'client_has_proposals', count: N }`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-mini-crm-clients.spec.js`
- **Backend Tests:** `content/tests/views/test_proposal_clients_views.py::TestDeleteProposalClient::test_delete_with_proposals_returns_400_with_error_code`
