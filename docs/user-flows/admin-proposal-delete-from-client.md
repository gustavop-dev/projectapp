### FLOW: `admin-proposal-delete-from-client`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`
- **Description:** Delete a specific proposal from a client's expanded row in the Mini-CRM clients view.
- **Steps:**
  1. Admin opens `/panel/clients` and expands a client row to see its linked proposals.
  2. Admin clicks delete on a specific proposal.
  3. A confirmation modal appears requiring the admin to type `DELETE`.
  4. Admin confirms → `DELETE /api/proposals/:id/delete/`.
  5. On success: the client detail is refetched (proposal disappears) and a success toast shows.
  6. On `409 Conflict` (linked to a launched project): the proposal stays and an error toast shows.
- **Coverage:** ❌ Missing
- **E2E Spec:** _none yet (suggested: `e2e/admin/admin-proposal-delete-from-client.spec.js`)_
