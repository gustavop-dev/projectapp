### FLOW: `admin-proposal-diagnostic-templates`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` → "Documentos & Plantillas" tab
- **Description:** Admin accesses 3 static markdown diagnostic templates (Diagnóstico de Aplicación, Diagnóstico Técnico, Anexo — Dimensionamiento) from the proposal edit page. Tab is visible when `proposal.status ∈ {sent, viewed, negotiating, accepted, rejected}` — the same condition as the Correos tab. Each template card shows the title, filename, and last-modified date. Three actions are available per card: **Copiar contenido** (fetches `GET /api/diagnostic-templates/:slug/` and writes to clipboard via `navigator.clipboard.writeText`; shows "¡Copiado!" feedback for 2 s; per-slug response cached in component `ref` to avoid duplicate requests), **Descargar .md** (Blob + temporary `<a download>` link click), and **Vista previa** (toggles an inline `<pre>` block with raw markdown).
- **Steps:**
  1. Admin opens a proposal in `sent` or later status via `/panel/proposals/:id/edit`.
  2. Admin clicks the "Documentos & Plantillas" tab.
  3. Template list fetches `GET /api/diagnostic-templates/` → 3 cards render.
  4. Admin clicks "Copiar contenido" on a card → detail fetch → clipboard write → "¡Copiado!" appears.
  5. Admin clicks "Descargar .md" → Blob download triggers.
  6. Admin clicks "Vista previa" → inline `<pre>` block expands; "Ocultar" collapses it.
- **Branches:**
  - [Tab hidden] When `proposal.status === 'draft'`, the tab is not rendered.
  - [Proposal documents sub-section] `ProposalDocumentsTab` (contract, generated PDFs) is only shown within this tab for `negotiating|accepted|rejected` — not for `sent|viewed`.
- **API:** `GET /api/diagnostic-templates/` (list), `GET /api/diagnostic-templates/:slug/` (detail + content_markdown)
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-diagnostic-templates.spec.js`
- **Unit Tests:** `frontend/test/components/ProposalDiagnosticTemplatesSection.test.js`
- **Backend Tests:** `backend/content/tests/views/test_diagnostic_template_views.py`
