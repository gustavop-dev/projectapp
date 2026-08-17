### FLOW: `admin-diagnostic-markdown-attachment`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` → Correos tab
- **Description:** When a diagnostic is in `negotiating` status, a "Crear documento desde markdown" button appears in the Correos tab of the diagnostic edit page. Admin uses it to compose a custom branded PDF (e.g., expanded scope, technical annex, pricing supplement) and attach it to the email composer without uploading a pre-built file.
- **Steps:**
  1. Admin opens a diagnostic in `negotiating` status via `/panel/diagnostics/:id/edit`.
  2. Admin clicks the "Correos" tab.
  3. "Crear documento desde markdown" button is visible.
  4. Admin clicks the button → `MarkdownAttachmentModal` opens.
  5. [Optional] Admin clicks one of the three **Plantillas base** buttons (Diagnóstico de Aplicación / Diagnóstico Técnico / Anexo) → `GET /api/diagnostic-templates/:slug/` fetches the template markdown and writes it to the clipboard; button shows "¡Copiado!" for 2 s. Subsequent clicks reuse an in-memory cache.
  6. Admin fills in the **Título** (text input) and **Contenido en Markdown** (textarea).
  7. Admin optionally unchecks one or more cover toggles (Portada / Subportada / Contraportada).
  8. Admin clicks "Vista previa" → `POST /api/diagnostics/:id/email/markdown-attachment/` fires (FormData with title, markdown, cover booleans).
  9. Backend generates PDF via `DocumentPdfService.generate_from_markdown()` and returns it inline (`Content-Disposition: inline`).
  10. Axios fetches the response as a Blob → `URL.createObjectURL` → `<iframe>` renders the preview.
  11. Admin clicks "Adjuntar" → Blob is converted to a `File` object, emitted via `@attach` → appended to the email composer's attachment list.
  12. Success toast "Adjunto «title.pdf» agregado al correo." appears.
  13. Modal closes automatically.
- **Branches:**
  - [Button absent] When `diagnostic.status !== 'negotiating'`, the button is not rendered.
  - [Preview disabled] "Vista previa" button stays disabled until both title and markdown are non-empty.
  - [Cache reuse] If admin generates a preview, changes nothing, and clicks "Adjuntar", a second POST is skipped — the previously fetched Blob is reused (tracked via `previewSnapshot` vs `currentSnapshot` comparison).
  - [Template fetch error] If `GET /api/diagnostic-templates/:slug/` fails, `error.value` shows "No se pudo copiar la plantilla." and the button re-enables.
- **API:** `POST /api/diagnostics/:id/email/markdown-attachment/`, `GET /api/diagnostic-templates/:slug/`
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-markdown-attachment.spec.js`
- **Unit Tests:** `frontend/test/components/MarkdownAttachmentModal.test.js`
- **Backend Tests:** `backend/content/tests/views/test_diagnostic_email_markdown_attachment.py`
