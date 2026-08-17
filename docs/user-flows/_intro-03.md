Registered by the `/e2e-user-flows-check` audit of the `feat/03072026-panel-modules-mcp-connectors` branch. Covers the new admin discount-offer action, backfills six flows that were already tested but undocumented here, and registers three system-triggered client-milestone notifications for traceability.

Also registered/updated in this audit and documented in their home sections:
- The three `platform-client-*` flows (§8.14) — now **✅ Covered** by `e2e/platform/platform-client-documents.spec.js`.
- `platform-password-reset` (§8.1) — added to `flow-definitions.json`; **✅ Covered** by `e2e/platform/platform-password-reset.spec.js`.
