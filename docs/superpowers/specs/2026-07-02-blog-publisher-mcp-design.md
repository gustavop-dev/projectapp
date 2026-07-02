# Blog Publisher MCP — Design

**Date:** 2026-07-02
**Branch:** `feat/02072026-blog-publisher-mcp`
**Status:** Approved design, pending spec review

## Overview

Expose the existing blog publishing pipeline as a remote MCP server embedded in the
Django backend, so the owner's claude.ai account (web/mobile) can create, schedule,
edit, and inspect blog posts directly via a custom connector — replacing the current
manual flow of pasting Claude-generated JSON into `/panel` blog module.

A new panel section `/panel/mcps` manages connector tokens (generate, rotate,
disable) and documents what each MCP can do. It starts with one card (Blog
Publisher) and is designed to host future MCPs.

## Goals

- Publish/schedule bilingual blog posts from claude.ai chat with zero panel steps.
- Reuse the exact existing pipeline: `BlogPostFromJSONSerializer` validation, Huey
  scheduled publish, LinkedIn auto-post, frontend rebuild. No divergence.
- Token lifecycle fully self-served from the panel (no deploys to rotate/revoke).
- No new infrastructure: same Django service, same deploy protocol, same monitoring.

## Non-Goals

- OAuth for the connector (webhook-style capability URL is accepted for this
  experiment; OAuth is the natural evolution if MCPs become permanent).
- SSE streaming / server-initiated MCP messages (not needed for these tools; WSGI
  stays as-is).
- Cover image file upload via MCP (posts reference `cover_image_url`; file uploads
  stay in the panel).
- MCPs other than the blog publisher (the panel section is built to list more, but
  only this one ships now).

## Architecture

```
backend/content/
├── mcp/
│   ├── __init__.py
│   ├── protocol.py      # Minimal JSON-RPC 2.0 dispatch: initialize, tools/list,
│   │                    #   tools/call, ping, notifications/initialized
│   └── tools.py         # 6 tool definitions: JSON Schema + handler functions
├── services/
│   └── blog_service.py  # NEW: shared logic extracted from views/blog.py
├── views/
│   ├── blog.py          # Panel views become thin wiring over blog_service
│   └── mcp_blog.py      # MCP endpoint + panel token-management endpoints
└── models/
    └── mcp_connector.py # McpConnector model
```

- MCP endpoint: `POST /api/mcp/blog/<token>/` (in `content/urls.py`).
- The endpoint is a DRF `@api_view(['POST'])` with `AllowAny` + manual token
  validation (the token in the URL *is* the credential), CSRF-exempt, with a
  dedicated DRF throttle scope (e.g. `mcp` at 60/min).
- Responses are plain `application/json` (Streamable HTTP transport without the
  optional SSE mode — valid per MCP spec, works under gunicorn WSGI).
- Stateless server: no MCP session IDs; `GET` returns 405.

## Data Model — `McpConnector`

| Field | Type | Notes |
|---|---|---|
| `slug` | SlugField, unique | `'blog'` for this MCP; identifies the mount path |
| `name` | CharField | Display name, e.g. "Blog Publisher" |
| `token_hash` | CharField(64) | SHA-256 hex of the token; plaintext never stored |
| `token_prefix` | CharField(8) | First 8 chars, shown masked in panel + used for lookup |
| `is_active` | BooleanField, default False | Toggle from panel; inactive → endpoint 404s |
| `last_used_at` | DateTimeField, null | Updated on successful `tools/call` (max once/min to avoid write amplification) |
| `created_at` / `updated_at` | DateTimeField | Standard timestamps |

Token generation: `secrets.token_urlsafe(36)` (48 chars). Shown once at
generation time as a full connector URL with copy button. Regenerating replaces
`token_hash` (old token dies instantly). Validation: look up connector by slug,
compare `hashlib.sha256(token)` with `hmac.compare_digest`. Wrong/missing/inactive
token → 404 (do not reveal the endpoint exists).

## Panel Endpoints (session + CSRF, `IsSuperUser`)

Superuser-only, matching the accounting module pattern (`content/permissions.py::IsSuperUser`
backend enforcement + `superuser-only.js` middleware for UI coherence).

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/mcp-connectors/` | List connectors with status, masked token prefix, last_used_at, and their tool catalog (name + description per tool, served from the tool registry) |
| POST | `/api/mcp-connectors/<slug>/generate-token/` | Create/rotate token; returns full connector URL **once** |
| PATCH | `/api/mcp-connectors/<slug>/` | Toggle `is_active` |

The Blog Publisher connector row is seeded by the migration (inactive, no token).

## MCP Protocol Subset (`protocol.py`)

JSON-RPC 2.0 over POST. Methods:

- `initialize` → protocol version negotiation, capabilities `{"tools": {}}`, serverInfo.
- `notifications/initialized` → HTTP 202, empty body.
- `tools/list` → the 6 tools with JSON Schemas from `tools.py`.
- `tools/call` → dispatch to handler. Business/validation errors return
  `result.isError: true` with a readable message (so the calling Claude can fix its
  JSON and retry); only malformed JSON-RPC gets protocol-level error objects.
- `ping` → `{}`.
- Unknown method → JSON-RPC `-32601`.

## Tools

| Tool | Input | Behavior |
|---|---|---|
| `get_blog_template` | — | Returns the bilingual JSON template + available categories (same payload as `/api/blog/admin/json-template/`) |
| `create_blog_post` | full post JSON | Validates via `BlogPostFromJSONSerializer`; creates via `blog_service`; returns id, slug, status (draft/scheduled/published) and public URL |
| `update_blog_post` | `post_id` + partial fields | Partial update via `BlogPostCreateUpdateSerializer` + same post-save pipeline as the panel view |
| `delete_blog_post` | `post_id` | **Guardrail: refuses if `is_published=True`** (unpublish first via update, or delete from panel). Protects live SEO content |
| `list_blog_posts` | `page`, `page_size` | Paginated admin list with per-post status |
| `get_blog_calendar` | `start`, `end` (YYYY-MM-DD) | Posts in range with `calendar_status` — lets Claude check the schedule before booking a slot |

Scheduling contract (unchanged from today): `is_published=false` +
future `published_at` → Huey one-shot task publishes at that exact time,
triggering LinkedIn auto-post and frontend rebuild.

## Service Refactor (`blog_service.py`)

Extract from `views/blog.py`, preserving behavior exactly:

- `create_post_from_json(validated_data) -> BlogPost` — the ORM create currently
  inlined in `create_blog_post_from_json`.
- `run_post_save_pipeline(post, was_published=False)` — `auto_publish_blog_to_linkedin`
  + `_enqueue_scheduled_publish_if_future` + conditional `schedule_rebuild_after_publish`.

Panel views (`create_blog_post`, `create_blog_post_from_json`, `update_blog_post`)
become request/response wiring over these functions; MCP tools call the same
functions. Existing `test_blog_views.py` suite is the regression net for the
refactor.

## Frontend (`/panel/mcps`)

- Page `frontend/pages/panel/mcps/index.vue` — card per connector: name, active
  toggle, masked token (`abc12345…`), last-used date, tool list (name +
  description), "Generate/Regenerate token" button. On generation, a modal shows
  the full connector URL once with a copy button and a claude.ai setup hint.
- Middleware: `['admin-auth', 'superuser-only']` (same as accounting pages).
- Store: `frontend/stores/mcps.js` (Options API shape, snake_case filename,
  `request_http.js` client — content/admin flow conventions).
- Sidebar entry in `panelNav.js` (superuser-gated like accounting) +
  `viewCatalog.js` registration.
- Mobile: follow the responsive card pattern used by panel tables
  (`useIsMobile` with `v-if`, not CSS hiding).

## Security

- Capability-URL auth: the token is the credential; treat the connector URL as a
  secret. Hash-only storage; one-time display; instant rotation/revocation from
  panel; inactive or missing connector → 404.
- CSRF exempt only on the MCP endpoint (token auth replaces it); panel management
  endpoints keep session + CSRF + `IsSuperUser`.
- DRF throttle scope on the MCP endpoint (60/min) to bound abuse.
- `[MCP]`-prefixed logging on every `tools/call` (tool name, post id/slug, outcome)
  for auditability.
- Accepted trade-off: anyone holding the URL can publish until rotated. Mitigations
  above; OAuth is the upgrade path.

## Testing

- `backend/content/tests/views/test_mcp_blog.py`: initialize handshake, tools/list,
  happy path per tool, validation error surfaces as `isError` with readable
  message, wrong/inactive token → 404, delete guardrail on published post,
  scheduled create enqueues the Huey task, token generate/rotate/toggle endpoints
  (superuser vs staff 403).
- Regression slice: existing `test_blog_views.py` (covers the refactored views).
- Frontend unit: `mcps.js` store + the token modal component.
- E2E: `e2e-user-flows-check` audit applies at the end (new panel route/flow);
  add a spec for the mcps page happy path per its outcome.
- Per repo rules: only changed-file slices, ≤20 tests per batch, never the full suite.

## Rollout

1. Ship migration (seeds inactive `blog` connector).
2. Deploy via normal protocol.
3. Owner generates token in `/panel/mcps`, adds the connector URL in claude.ai
   Settings → Connectors.
4. First real test: create a draft from claude.ai chat, verify in panel; then a
   scheduled post end-to-end (Huey publish + LinkedIn + rebuild).
