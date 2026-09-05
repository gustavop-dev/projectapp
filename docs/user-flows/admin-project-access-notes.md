### FLOW: `admin-project-access-notes`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/projects` (project detail modal)
- **API:** note create/update/delete/reveal endpoints under `/api/projects/:id/access/notes/`
- **Interaction:** Inspect notes or open “Agregar nota”, enter title/content, choose sensitivity, and save.
- **Display outcome:** Existing titled notes render; sensitive content stays masked.
- **Success outcome:** A valid note is added to the project response and appears in the list.
- **Error outcome:** Missing title/content is rejected locally without a request.
- **Failure outcome:** A backend rejection preserves the entered content and shows an actionable error.
- **Coverage:** `e2e/admin/admin-project-access-detail.spec.js`.
