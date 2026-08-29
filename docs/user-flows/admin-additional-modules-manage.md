### FLOW: `admin-additional-modules-manage`

- **Module:** admin / commercial
- **Role:** admin
- **Priority:** P1
- **Route:** `/panel/additional-modules`
- **Interaction:** Create or edit bilingual module content; a successful edit sends a `PATCH` and closes the form, while incomplete content and API failures remain visible inside it.
- **Outcomes:** `success`, `error`, `failure`
- **Evidence:** `ModuleFormModal.vue`, module create/update endpoints.
