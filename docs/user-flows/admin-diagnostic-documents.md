### FLOW: `admin-diagnostic-documents`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` → Documentos tab
- **Description:** Admin uploads, manages, and sends file attachments (PDF, Word, Excel, images) to the client from the Documentos tab of the diagnostic detail page. Supports document types: `confidentiality_agreement` (system-generated, see `admin-diagnostic-confidentiality-*` flows), `amendment`, `legal_annex`, `client_document`, `other`.
- **Steps:**
  1. Admin navigates to `/panel/diagnostics/:id/edit`.
  2. Clicks the "Documentos" tab.
  3. Fills in the upload form (title, type, file) and clicks upload → `POST /api/diagnostics/:id/attachments/upload/`.
  4. The new attachment appears in the list.
  5. Admin selects one or more attachments via checkboxes and clicks "Enviar al cliente".
  6. `SendDiagnosticDocumentsModal` opens to compose the send email.
  7. Admin submits → `POST /api/diagnostics/:id/attachments/send/`.
  8. Email is logged in `EmailLog` with `metadata.diagnostic_uuid`, `metadata.attached_doc_ids`, and `metadata.extra_filenames`.
- **Branches:**
  - [No email] Send button disabled when no client email configured.
  - [No selection] Send button disabled until at least one checkbox is checked (counts both `selectedIds` and `selectedMainDocs`).
  - [NDA included] When the diagnostic has a generated NDA, an extra checkbox "📋 NDA — Acuerdo de Confidencialidad (borrador con marca de agua)" appears above the attachment list. When checked, the send payload includes `documents: ['confidentiality_agreement']` and the backend appends a freshly-generated draft NDA (with `BORRADOR` watermark and `XXX-XXX-XXX` placeholders) to the email.
  - [Delete] Admin clicks delete on a non-generated attachment → `DELETE /api/diagnostics/:id/attachments/:att_id/delete/` → row removed.
  - [Delete blocked] Generated NDA attachments (`is_generated=true`) cannot be deleted; backend returns HTTP 400 `{"error": "No se puede eliminar un documento generado por el sistema; regénerelo desde Editar parámetros."}`. They are filtered out of the user-attachments list, so the trash icon is not rendered for them.
- **Coverage:** ✅ Covered (base flow); 🟡 NDA-checkbox branch + delete-blocked branch not yet asserted
- **E2E Spec:** `e2e/admin/admin-diagnostic-email-documents.spec.js`
