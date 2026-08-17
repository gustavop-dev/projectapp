### FLOW: `admin-diagnostic-send-initial`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/diagnostics/:id/edit`
- **Description:** Admin sends the initial-phase diagnostic to the client from the edit page, transitioning status DRAFT → SENT (stamps `initial_sent_at`). Then promotes the diagnostic to NEGOTIATING once the client authorises the work. Public view exposes only sections whose `visibility ∈ {initial, both}`.
- **Steps:**
  1. Admin navigates to `/panel/diagnostics/:id/edit` (status: DRAFT).
  2. Clicks "Enviar envío inicial" → POST `/api/diagnostics/:id/send-initial/`.
  3. Status transitions to SENT; `initial_sent_at` stamped; client email dispatched; response body carries `email_ok` flag.
  4. After client confirmation, admin clicks "Marcar en análisis" → POST `/api/diagnostics/:id/mark-in-analysis/`.
  5. Status transitions to NEGOTIATING.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-send.spec.js`
