# LinkedIn Personal Content MCP — Design

**Date:** 2026-07-04
**Branch:** `feat/04072026-linkedin-content-module` (PR #85)
**Status:** Approved

## Overview

Expose the new LinkedIn content module (`/panel/linkedin`, this same PR) as a
remote MCP connector, following the exact architecture of the Blog Publisher
MCP (`docs/superpowers/specs/2026-07-02-blog-publisher-mcp-design.md`) and the
Documents MCP: tool registry + `TOOLS_BY_SLUG` entry + seed migration. The
owner's claude.ai account can then draft, schedule, publish and manage
freeform LinkedIn posts for the **personal profile** directly from chat.

A separate `linkedin-company` connector may come later (organization URN +
`w_organization_social` scope) — out of scope here; the `-personal` suffix in
the slug reserves the namespace.

## Goals

- Manage `LinkedInPost` records from claude.ai with zero panel steps: create
  drafts, schedule (Huey ETA + sweep pipeline), publish now, edit, delete.
- Surface OAuth connection health (profile, `expires_at`, near-expiry warning)
  so Claude can warn before a scheduled post would fail.
- Reuse the exact panel pipeline: `LinkedInPostSerializer` validation,
  `linkedin_post_service` (atomic double-publish guard, ETA scheduling),
  `linkedin_service.get_connection_status`. No divergence.
- Reuse all existing MCP infrastructure untouched: `protocol.py`,
  `McpConnector`, endpoint routing, `/panel/mcps` token lifecycle (the panel
  lists tools automatically from `TOOLS_BY_SLUG`).

## Non-Goals

- Image upload via MCP (binary handling stays panel-only; posts created via
  MCP are text-only).
- OAuth connection/reconnection via MCP (panel-only).
- Company-page publishing (future `linkedin-company` connector).

## Connector

- Slug: `linkedin-personal` — Name: **LinkedIn Personal Content**.
- Seeded inactive and tokenless (migration, same pattern as
  `0136_seed_panel_mcp_connectors.py`); operator activates and generates the
  token in `/panel/mcps`.
- Endpoint: `POST /api/mcp/linkedin-personal/<token>/` (already routed by the
  generic `mcp_endpoint`).

## Tools (`backend/content/mcp/linkedin_tools.py`, registry `LINKEDIN_TOOLS`)

| Tool | Input | Behavior |
|---|---|---|
| `get_connection_status` | — | Connection status + profile name + `expires_at`; adds `warning` field when the token expires in ≤7 days or is disconnected. Never exposes tokens. |
| `list_posts` | `status?` (draft/scheduled/published/failed) | Summaries newest-first (commentary truncated to 120 chars, `has_image`, schedule/publish timestamps, public URL when published). |
| `get_post` | `post_id` | Full detail including complete commentary and `error_message`. |
| `create_post` | `commentary` (≤3000), `scheduled_at?` (ISO 8601 future) | Draft, or scheduled (status transition + Huey ETA enqueue via the shared service helper). |
| `update_post` | `post_id`, `commentary?`, `scheduled_at?` (`""`/null clears → back to draft) | Published posts are immutable → ToolError. |
| `delete_post` | `post_id` | Deletes the local record only (never touches LinkedIn). |
| `publish_post` | `post_id` | Publish now through `publish_linkedin_post_now` (atomic claim). Already-published → ToolError; API failure → ToolError with the persisted `error_message`. |

## Refactor (single source of truth)

`_apply_schedule_transition` moves from `views/linkedin.py` to
`linkedin_post_service.apply_schedule_transition(post)`; the panel view and
the MCP handlers both call the service version. The existing view test that
patches `content.views.linkedin.schedule_linkedin_post_eta` is updated to
patch the service path.

## Error handling

- Business errors (`ToolError`) → MCP `isError: true` with a Spanish message
  guiding the next tool call (same style as the Documents MCP).
- Validation reuses `LinkedInPostSerializer` (`scheduled_at` must be future,
  commentary ≤3000).

## Testing

`backend/content/tests/views/test_mcp_linkedin.py`, mirroring
`test_mcp_tasks.py` conventions (connector fixture + JSON-RPC helpers):
tools/list names; create draft; create scheduled (service ETA mocked);
update published → error; publish happy path (publish service mocked);
publish failure → isError with message; delete; status includes `expires_at`.
