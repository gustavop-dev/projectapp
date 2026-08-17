### FLOW: `admin-accounting-hosting-billing`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P1
- **Routes:** `/panel/accounting/hostings`
- **Description:** Send a client the cuenta de cobro from a hosting row. The paper-plane action (disabled without client email, tooltip explains) opens a ConfirmModal previewing amount and recipient; confirm POSTs `/api/accounting/hostings/:id/send-collection-account/`, which issues the Document (public number PA-YYYY-NNNN, one line item for the next modality period, issuer default payment methods), emails the client the branded message with the Spanish PDF attached and stamps `billing_requested_at` (pauses the expiry notices; a "Cobro enviado" badge appears on the row). If the email fails the document stays issued and a warning toast points to Cuentas de cobro for re-send. Since PA-25 the recipient and the numbering come from the linked client (see `admin-accounting-hosting-client`): the action gates on `billing_email` (hosting override, else the client's address), and a linked hosting issues on that client's series.
- **Steps:**
  1. Superuser opens `/panel/accounting/hostings` and clicks the paper-plane action on a row with client email.
  2. ConfirmModal previews `payment_per_cycle` and the recipient; confirm fires the POST.
  3. Success toast (with "Ver en Cuentas de cobro" action) and the row shows the "Cobro enviado" badge.
- **Coverage:** ✅ Covered (email gate, confirm + POST + badge, email-failure warning)
- **E2E Spec:** `e2e/admin/admin-accounting-hosting-billing-cycles.spec.js`
