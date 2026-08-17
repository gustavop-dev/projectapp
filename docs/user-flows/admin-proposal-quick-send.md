### FLOW: `admin-proposal-quick-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Admin sends or re-sends a proposal directly from the proposals list without entering the edit page. Draft proposals show a "📤 Enviar" button; sent/viewed proposals show "🔄 Re-enviar". A confirmation modal prevents accidental sends.
- **Steps:**
  1. Admin views the proposals list.
  2. For draft proposals with client_email: "📤 Enviar" button is visible in the row.
  3. Admin clicks "📤 Enviar" → confirmation modal opens: "¿Enviar esta propuesta?".
  4. Admin confirms → API call to `POST /api/proposals/:id/send/`.
  5. Success: proposal status changes to `sent`, list refreshes.
  6. For sent/viewed proposals: "🔄 Re-enviar" button is visible → confirm dialog → `POST /api/proposals/:id/resend/`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-list.spec.js`
