### FLOW: `admin-diagnostic-email`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` → Correos tab
- **Description:** Admin sends a follow-up branded email to the client from the Correos tab of the diagnostic detail page. The composer supports a recipient address, subject, greeting, draggable body sections (each with an optional Markdown toggle), footer, and optional file attachments. The "Vista previa" sub-tab shows the real branded template server-rendered via `POST /api/emails/preview/`. Email history shows previous sends with expandable metadata (sections stored as legacy strings or `{text, markdown}` objects).
- **Steps:**
  1. Admin navigates to `/panel/diagnostics/:id/edit`.
  2. Clicks the "Correos" tab → composer loads with defaults from `GET /api/diagnostics/:id/email/defaults/`.
  3. Fills in sections and clicks "Enviar correo" → `POST /api/diagnostics/:id/email/send/` (FormData).
  4. On success, history list refreshes and shows the new send.
  5. Email is logged in `EmailLog` with `metadata.diagnostic_uuid`.
- **Branches:**
  - [Error] If client has no email, send button is disabled.
  - [Rate limit] Backend enforces 1 send/minute; 429 surfaces as an error message.
  - [NDA attachment] Admin checks "Adjuntar acuerdo de confidencialidad" → `attach_confidentiality: '1'` appended to FormData → backend generates confidentiality PDF and attaches it to the email; if PDF generation fails (missing diagnostic params), backend returns 400 and frontend shows `sendError`.
- **Coverage:** ✅ Covered (including NDA checkbox branch, Apr 20 2026)
- **E2E Spec:** `e2e/admin/admin-diagnostic-email-documents.spec.js`
