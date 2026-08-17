### FLOW: `admin-mcps`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P2
- **Routes:** `/panel/mcps`
- **Description:** Superuser sees one card per MCP connector (starting with Blog Publisher): name, description, active toggle, masked token prefix, last-used timestamp and the tool catalog exposed to Claude. "Generar/Regenerar token" calls `POST /api/mcp-connectors/<slug>/generate-token/` and shows the full connector URL exactly once in a modal with a copy button (the plaintext token is never retrievable again; only its SHA-256 hash is stored). The toggle PATCHes `is_active`, killing or enabling the public MCP endpoint instantly.
- **Steps:**
  1. Superuser opens `/panel/mcps` (sidebar section "Integrations", superuser-gated).
  2. Reviews the Blog Publisher card and its tool list.
  3. Clicks "Generar token" → one-time modal with the connector URL → copies it into claude.ai → Settings → Connectors.
  4. Activates the connector with the toggle.
  - [Branch A — gating] Staff non-superuser navigating to `/panel/mcps` is redirected to `/panel`; the Integrations sidebar section is hidden.
  - [Branch B — rotation] Regenerating the token invalidates the previous one immediately (old connector URL starts returning 404).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-mcps.spec.js`

### 24.1 Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-mcps` | admin | superuser | P2 | ✅ Covered | `e2e/admin/admin-mcps.spec.js` |
