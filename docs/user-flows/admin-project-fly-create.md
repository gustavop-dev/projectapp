### FLOW: `admin-project-fly-create`
- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/accounting/hostings`, `/panel/accounting/incomes`, `/panel/accounting/collections` (transitively, via the stacked income modal)
- **API:** `GET /api/accounting/projects/?client=<profile>`, `POST /api/projects/create/`
- **Description:** `ProjectSelect` is a combobox over the client's already-fetched projects (local filtering — a client has a handful, not a catalog) that mirrors the client selector so both are learned once. With no matches it offers "Crear proyecto «term»" (Enter included) opening an inline panel embedded in the component itself — ONE reusable selector, not a per-modal solution: hosting and income modals gained the flow without changes, and the cuenta de cobro inherits it through its stacked income modal. The panel pre-fills the typed name, shows the inherited client, warns without blocking on a same-name collision, stays open on a 400 with the backend message, and on success auto-selects the new project, appending it to the per-client picker cache (`projectsByClient`, `all` bucket dropped). Cancelling the outer form leaves the project standing — a record of its own, immediately visible in `/panel/projects`. The module store invalidates the whole picker cache after any create/update/archive/restore so renamed or archived projects never linger in forms.
- **Steps:** open hosting/income modal → pick client → type a project that does not exist → create it inline → the id travels in the outer form's payload.
- **Branches:** 400 keeps the inline panel open; cancelling the outer form afterwards preserves the project; re-opening the picker lists it without refetching.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-project-fly-create.spec.js`

### Section 27 Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-panel-projects` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-panel-projects.spec.js` |
| `admin-project-fly-create` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-project-fly-create.spec.js` |
