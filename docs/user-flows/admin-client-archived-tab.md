### FLOW: `admin-client-archived-tab`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`
- **Description:** Archive a client (sets `UserProfile.archived_at` and `archived_by`) from the row toggle, and browse archived clients under the "Archivados" option of the transversal client-status selector (next to the search box since the Ago 2026 filter reorganisation, labelled with its own match count). "Archivado" is the entity-lifecycle word shared with projects, whose non-active bucket the panel already labels the same way; the per-item switches in Documentos and Comunicaciones say "Ver documentos archivados" / "Ver comunicaciones archivadas" so the two senses never collide. Archived clients are hidden from Todos/Activos/Huérfanos (backend default excludes `archived_at IS NOT NULL`); Archivados sends `?archived=true`, and the pre-rename `?inactive=` spelling is still accepted so bookmarked URLs keep working. Archiving is independent from `auth.User.is_active`, which is a separate axis owned by `/platform/clients`.
- **Steps:**
  1. Admin navigates to `/panel/clients/`.
  2. Admin clicks the archive icon (data-testid: `client-toggle-archived-<id>`) on an active client, or flips "Archivado" in the edit modal (`clients-edit-archived`). Both open the same modal (`client-archive-modal`); the identity `PATCH` refuses `is_archived` with `client_archive_transition_required`, so there is no shortcut past it.
  3. `GET /api/proposals/client-profiles/:id/archive-preview/` names the projects the cascade will move to "Suspendido" and what it costs (`client-archive-impact`): future incomes cancelled, future hosting charges archived, and that reactivating does not undo it. Confirm stays disabled until the impact is on screen.
  4. `POST /api/proposals/client-profiles/:id/archive/` echoes one `impact_token` per project; the backend answers 409 `projects_changed` if the set moved since the preview. Success toast shows; the row leaves the current status on reload.
  5. Admin picks "Archivados" in the status selector (data-testid: `clients-status-archived`) — list reloads with `?archived=true`, the URL gains `?status=archived` and rows show the "Archivado" badge.
  6. Clicking the icon again opens the same modal, which states that the projects stay suspended, and `POST .../unarchive/` clears `archived_at`/`archived_by` while leaving them alone.
- **Coverage:** ✅ Covered — status filtering, the archive preview with its impact copy, and the unarchive branch with its "projects stay suspended" warning are asserted (2026-08-15; vocabulary renamed and cascade added 2026-08-31).
- **E2E Spec:** `e2e/admin/admin-clients-archived-tab.spec.js`
- **Backend Tests:** `content/tests/views/test_proposal_clients_views.py::TestArchivedClients`, `content/tests/views/test_client_archive_views.py`, `accounts/tests/test_client_archive_service.py`
