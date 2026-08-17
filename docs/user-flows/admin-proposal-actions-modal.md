### FLOW: `admin-proposal-actions-modal`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals`
- **API:** (no direct API call — modal renders action buttons from listing row data)
- **Description:** Admin opens an actions modal from a proposal row in the listing. Modal displays quick-action buttons: edit, preview, send/resend, copy link, WhatsApp, duplicate, toggle active, delete. Send/Resend visibility is conditional on proposal status.
- **Steps:**
  1. Admin is on the proposal listing `/panel/proposals`.
  2. Admin clicks the actions icon (⋮) on a proposal row.
  3. Actions modal opens with buttons: Edit, Preview, Send/Resend, Copy, WhatsApp, Duplicate, Toggle, Delete.
  4. [Branch A — Draft] "Send" action visible; "Resend" hidden.
  5. [Branch B — Sent/Viewed] "Resend" action visible; "Send" hidden.
  6. Admin clicks any action → navigates or triggers the corresponding flow.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-actions-modal.spec.js`
