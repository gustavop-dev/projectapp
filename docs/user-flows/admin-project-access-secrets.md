### FLOW: `admin-project-access-secrets`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/projects` (project detail modal)
- **API:** dedicated password/note reveal endpoints under `/api/projects/:id/access/`
- **Interaction:** Reveal, hide, or copy a password or sensitive note through its icon control.
- **Display outcome:** Secret values are absent from the initial payload and appear as a mask.
- **Success outcome:** Reveal shows the requested secret until hidden or closed; copy writes it without first placing it in the modal.
- **Failure outcome:** A failed reveal reports the API error while the value remains masked.
- **Error:** n/a — there is no user-authored value to validate in reveal/copy.
- **Coverage:** `e2e/admin/admin-project-access-detail.spec.js`.
