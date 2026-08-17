### FLOW: `admin-diagnostic-send-final`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/diagnostics/:id/edit`
- **Description:** Admin completes pricing and radiography data, finalises the `categories` section with findings/recommendations + the `executive_summary` section with severity counts, then sends the final-phase diagnostic from NEGOTIATING state, transitioning back to SENT with `final_sent_at` stamped. Public view now also exposes sections whose `visibility = final`.
- **Steps:**
  1. Admin updates pricing fields in the General tab and radiography data in the Secciones tab (as of 2026-04-18 the Pricing and Radiografía sub-tabs live in General/Secciones; the former "Det. técnico" tab was retired).
  2. Fills findings, strengths, and recommendations for each of the 14 categories in the Secciones tab.
  3. Completes the Resumen Ejecutivo section with severity counts + narrative.
  4. Clicks "Enviar diagnóstico final" → POST `/api/diagnostics/:id/send-final/`.
  5. Status returns to SENT; `final_sent_at` stamped; email sent to client with the public link.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-send.spec.js`
