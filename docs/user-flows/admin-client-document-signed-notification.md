### FLOW: `admin-client-document-signed-notification`

- **Module:** admin
- **Role:** system
- **Priority:** P2
- **Trigger:** `POST /api/accounts/documents/:uuid/sign/`
- **Description:** When a client click-to-accept signs a document, `notify_team_document_signed_task` fires a team milestone alert (in-app to project admins + email) and the client receives a signature-confirmation email. Best-effort; idempotent re-signs do not re-notify.
- **Coverage:** ⚠️ Backend-only
- **Evidence:** Backend service `accounts/services/client_flow_notifications.py` + Huey task `notify_team_document_signed_task` (out of browser-E2E scope; may be asserted as a branch of `platform-client-document-sign`).

### 25.1 Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-proposal-discount-offer-send` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-discount-offer.spec.js` |
| `admin-styleguide` | admin | admin | P3 | ✅ Covered | `e2e/visual/styleguide.spec.js` |
| `admin-layout-title-mapping` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-layout-title-mapping.spec.js` |
| `platform-layout-title-mapping` | platform | platform-admin | P3 | ✅ Covered | `e2e/platform/platform-layout-title-mapping.spec.js` |
| `admin-proposal-json-import-client-picker` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-json-import-client-picker.spec.js` |
| `proposal-calculator-reopen-after-nav` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-calculator-reopen-after-nav.spec.js` |
| `proposal-slug-access` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-slug-access.spec.js` |
| `admin-client-first-login-notification` | admin | system | P2 | ⚠️ Backend-only | `accounts/services/client_flow_notifications.py` |
| `admin-client-email-validated-notification` | admin | system | P2 | ⚠️ Backend-only | `accounts/services/client_flow_notifications.py` |
| `admin-client-document-signed-notification` | admin | system | P2 | ⚠️ Backend-only | `accounts/services/client_flow_notifications.py` |
