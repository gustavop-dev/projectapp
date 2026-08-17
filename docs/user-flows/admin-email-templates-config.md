### FLOW: `admin-email-templates-config`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/email-templates`
- **Description:** Admin manages email template content customization. Lists all email templates (client, internal, contact) with category filter. Admin can edit text fields (greeting, body, CTA, subject), toggle templates on/off, preview rendered HTML with sample data, and reset to defaults.
- **Steps:**
  1. Admin navigates to `/panel/proposals/email-templates`.
  2. Template list loads from API (`GET /api/email-templates/`).
  3. Category filter buttons (Todos, Cliente, Interno, Contacto) allow filtering.
  4. Admin clicks a template row to expand the editor.
  5. Template detail loads from API (`GET /api/email-templates/:key/`).
  6. Admin edits text fields (greeting, body, cta_text, subject) and toggles active/inactive.
  7. Admin clicks "Guardar Cambios" → `PUT /api/email-templates/:key/`.
  8. Success feedback displays.
- **Branches:**
  - [Branch A — Preview] Admin clicks "Vista previa" → `GET /api/email-templates/:key/preview/` → modal with rendered HTML iframe.
  - [Branch B — Reset] Admin clicks "Restaurar" → confirmation modal → `POST /api/email-templates/:key/reset/` → template reverts to defaults.
  - [Branch C — Disable] Admin toggles template off → emails of this type stop being sent.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-email-templates.spec.js`
- **Backend Tests:** `content/tests/views/test_email_template_views.py`
