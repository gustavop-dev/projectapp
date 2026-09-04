### FLOW: `admin-proposal-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/`, `/panel/proposals/:id/edit`
- **Description:** Send a proposal to a client via email. The canonical **Correos** tab is available while the proposal is still a draft and owns the editable plain-text personalized message (`BusinessProposal.email_intro`). The message explains the client's problem, how this proposal solves it, and the expected business outcome. A draft may save it empty, but every send is blocked until it contains text. The delivered email keeps the predefined body and inserts the message immediately after it, before payment/timeline/commercial blocks; the commercial PDF is attached automatically. Editing the proposal later does not rewrite historical email snapshots.
- **Steps:**
  1. Admin views the proposal edit page or the actions modal in the list page.
  2. Admin opens **Correos**, writes or adjusts the message, previews it if desired, and clicks "Guardar mensaje". The tab saves only `{ email_intro }`; it does not overwrite unsaved changes in other tabs.
  3. Admin clicks "Enviar al Cliente".
  4. The scorecard checks client data, commercial readiness, and a nonblank personalized message. A missing message appears as a blocker with "Completar en Correos"; no send request is made.
  5. Once all checks pass, admin confirms → `POST /api/proposals/:id/send/`.
  6. Backend validates the message again before snapshots or state changes, changes status to `sent`, renders predefined body → personalized message → commercial blocks, attaches the PDF, sends, and returns `email_delivery`.
  7. `email_delivery.ok=true` shows "Propuesta enviada al cliente"; a delivery failure shows its detail/reason instead of false success.
- **Branches:**
  - [Error — Missing message] The scorecard and backend return the `missing_email_intro` blocker before any send side effect.
  - [Failure — Delivery] SMTP/template failure leaves an explicit warning even if the proposal state was advanced.
  - [Display — History] The exact sent body is stored in the delivery snapshot and remains immutable after later edits.
- **Coverage:** ✅ Covered — independent Correos save, missing-message blocker, successful send and delivery-failure feedback are E2E-covered; ordering, backend atomicity, PDF metadata and immutable snapshots are pytest-covered.
- **E2E Spec:** `e2e/admin/admin-proposal-send.spec.js`
