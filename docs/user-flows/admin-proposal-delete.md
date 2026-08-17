### FLOW: `admin-proposal-delete`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Delete an existing business proposal from the proposals list.
- **Steps:**
  1. Admin views the proposal list.
  2. Admin clicks delete on a proposal.
  3. A confirmation modal appears requiring the admin to type `DELETE`.
  4. Admin confirms deletion.
  5. API call to `DELETE /api/proposals/:id/delete/`.
  6. On success: proposal is removed (list refreshed) and a success toast shows.
  7. On `409 Conflict` (proposal linked to a launched project via `ProjectPhase`, `on_delete=PROTECT`): the proposal stays and an error toast shows the backend message.
- **Coverage:** ⚠️ Partial
- **E2E Spec:** `e2e/admin/admin-proposal-delete.spec.js`
- **Known gaps:** The existing spec only navigates + mocks the endpoint; it does not exercise the confirm modal (type `DELETE`), the success toast + list refresh, or the `409` blocked-delete path for project-linked proposals.
