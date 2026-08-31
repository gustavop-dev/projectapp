### FLOW: `admin-client-archived-tab`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`
- **Description:** Archive a client (sets `UserProfile.archived_at` and `archived_by`) from the row toggle, and browse archived clients under the "Archivados" option of the transversal client-status selector (next to the search box since the Ago 2026 filter reorganisation, labelled with its own match count). "Archivado" is the entity-lifecycle word shared with projects, whose non-active bucket the panel already labels the same way; the per-item switches in Documentos and Comunicaciones say "Ver documentos archivados" / "Ver comunicaciones archivadas" so the two senses never collide. Archived clients are hidden from Todos/Activos/Huérfanos (backend default excludes `archived_at IS NOT NULL`); Archivados sends `?archived=true`, and the pre-rename `?inactive=` spelling is still accepted so bookmarked URLs keep working. Archiving is independent from `auth.User.is_active`, which is a separate axis owned by `/platform/clients`.
- **Steps:**
  1. Admin navigates to `/panel/clients/`.
  2. Admin clicks the archive icon (data-testid: `client-toggle-archived-<id>`) on an active client.
  3. `PATCH /api/proposals/client-profiles/:id/update/` with `{is_archived: true}` sets `archived_at`; success toast shows; row leaves the current status on reload.
  4. Admin picks "Archivados" in the status selector (data-testid: `clients-status-archived`) — list reloads with `?archived=true`, the URL gains `?status=archived` and rows show the "Archivado" badge.
  5. Clicking the icon again brings the client back (`{is_archived: false}` clears `archived_at`).
- **Coverage:** ✅ Covered — status filtering, archiving and the unarchive branch (icon from the Archivados list, PATCH `is_archived:false` + toast) are asserted (2026-08-15; vocabulary renamed 2026-08-31).
- **E2E Spec:** `e2e/admin/admin-clients-archived-tab.spec.js`
- **Backend Tests:** `content/tests/views/test_proposal_clients_views.py::TestArchivedClients`, `accounts/tests/test_proposal_client_service.py::TestUpdateClientProfile::test_toggling_is_archived_does_not_cascade_snapshots`
