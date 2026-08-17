### FLOW: `admin-proposal-client-no-email`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/create` (Manual tab)
- **API:** `POST /api/proposals/` (omitted `client_email`)
- **Description:** Admin creates a proposal without providing a client email. The backend generates a placeholder email (`cliente_<id>@temp.example.com`), flags the client as `is_email_placeholder=true`, and pauses all automations for that client (e.g., reminder / overdue stage notifications). A hint banner informs the admin that email-based automations will be paused until the email is filled in.
- **Steps:**
  1. Admin navigates to `/panel/proposals/create` (Manual tab).
  2. Admin fills `#create-client-name` and leaves `#create-client-email` blank.
  3. Placeholder hint text (e.g., "email temporal" / "automatizaciones pausadas") renders near the email input.
  4. Admin submits the form → `POST /api/proposals/` with `client_email=""`.
  5. Backend creates the proposal and a placeholder client profile with `automations_paused=true`.
  6. Admin is redirected to `/panel/proposals/:id/edit`; the client snapshot shows the placeholder email.
- **Branches:**
  - [Branch A — Fill email later] Admin edits the client email from the proposal edit page later → the placeholder flag clears and automations resume (handled by `admin-mini-crm-clients` or proposal edit).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-client-autocomplete.spec.js`
