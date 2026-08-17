### FLOW: `admin-diagnostic-activity`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` (Actividad tab)
- **Description:** Admin reviews the `DiagnosticChangeLog` timeline for a diagnostic and logs manual notes (note / call / meeting / followup). Automated entries are appended by the backend on creation, status transitions, section edits, email sends, and client responses.
- **Steps:**
  1. Admin navigates to the Actividad tab.
  2. Selects a change_type, types a description, clicks "Registrar" → POST `/activity/create/`.
  3. New entry appears at the top of the timeline with icon + color + timestamp.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-sections.spec.js`
