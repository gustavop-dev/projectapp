### FLOW: `admin-proposal-client-autocomplete`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/create` (Manual tab), `/panel/proposals/:id/edit`
- **API:** `GET /api/proposals/client-profiles/search/?q=<term>`
- **Description:** Client picker autocomplete in the proposal create/edit form. Admin types a search term; backend returns matching clients (by name, email, or company) from the mini-CRM. Selecting a client auto-fills the snapshot fields (name, email, phone, company). When no match is found, a "Crear nuevo" button sets the typed value as a brand-new client name without triggering another search.
- **Steps:**
  1. Admin navigates to `/panel/proposals/create` and activates the Manual tab (or opens `/panel/proposals/:id/edit`).
  2. The autocomplete input (`[data-testid="client-autocomplete-input"]`) is visible.
  3. Admin types 2+ characters → `GET /api/proposals/client-profiles/search/?q=...` fires (debounced).
  4. Matching results render as a dropdown (`[data-testid="client-autocomplete-option-:id"]`) showing name, email, company, and total proposals count.
  5. Admin clicks a result → `#create-client-name`, `#create-client-email`, phone and company snapshot fields auto-populate.
- **Branches:**
  - [Branch A — No match] Dropdown shows "Crear nuevo" button (`[data-testid="client-autocomplete-create-new"]`) → clicking it sets the typed value as the client name and clears the dropdown.
  - [Branch B — Placeholder client] When the selected client has `is_email_placeholder=true`, the email field remains empty and the placeholder hint is shown (see `admin-proposal-client-no-email`).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-client-autocomplete.spec.js`
