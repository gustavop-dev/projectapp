### FLOW: `admin-project-access-field-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/projects` (project detail modal)
- **API:** `PATCH /api/projects/:id/access/`
- **Interaction:** Activate one field's edit icon, change its value, and explicitly save it.
- **Success outcome:** The API receives exactly one mutable field (plus environment when applicable) and the returned value replaces the read view.
- **Error outcome:** A serializer validation message remains beside the field and the draft stays editable.
- **Failure outcome:** A server failure remains inline and does not discard the draft.
- **Display:** n/a — the read-only values belong to `admin-project-access-detail`.
- **Coverage:** `e2e/admin/admin-project-access-detail.spec.js`.
