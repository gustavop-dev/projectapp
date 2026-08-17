### FLOW: `admin-clients-documents-section`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`, `/panel/documents`
- **Description:** The expanded client row (ficha) lists the client's **five most recent active documents** — title linking into `/panel/documents/:id/edit`, project, status and created date (data-testid `client-document-row-<id>`) — fed by the `documents` + `documents_total` keys the detail endpoint nests next to proposals/projects/hostings/incomes. "Ver todos (N)" (data-testid `client-documents-all-<id>`) jumps into `/panel/documents?client=<profileId>`: a client's documents are reachable from their ficha without touching the filters. The relation also works backwards — the document editor's "Ver cliente" link lands here with `?highlight=<profileId>`, a single-use param that expands that client's ficha and scrolls to the row (mirror of `/panel/projects?highlight=`), degrading silently if the client is not among the loaded rows.
- **Steps:**
  1. Admin expands a client row in `/panel/clients` → the ficha loads the detail payload.
  2. The "Documentos" section renders the last 5 documents with project, status and date; half-linked ones show a dash in Proyecto.
  3. Clicking a document title opens `/panel/documents/:id/edit`.
  4. Clicking "Ver todos (N)" opens `/panel/documents?client=<id>` with the association filter seeded.
- **Branches:**
  - [Branch A — Sin documentos] A client with no active documents renders no section (the ficha stays as before).
  - [Branch B — highlight] Arriving with `?highlight=<profileId>` expands that ficha, scrolls to the row and strips the param from the URL.
- **Coverage:** ✅ Covered — section rows with project + editor link, and the pre-filtered "Ver todos" handoff (2026-08-16).
- **E2E Spec:** `e2e/admin/admin-clients-documents-section.spec.js`
- **Backend Tests:** `content/tests/views/test_proposal_clients_views.py::TestDocumentsModuleAnnotations`
