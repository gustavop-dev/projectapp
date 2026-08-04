# Tarjetas QR — QR code + short-link generator (design)

## Purpose

New "Tarjetas QR" module under `/panel/` that lets an admin create a "tarjeta":
a record identified by a UUID, reachable through a short public link
(`{domain}/t/{uuid}/`), which redirects to a `destination_url` configurable
independently of the UUID. This decouples the printed/shared QR code from
its destination: the operator can reprint nothing and just change where the
link points.

This is phase one of a broader "Tarjetas"/TapTag-style product direction
(see `/home/cerrotico/work/taptag` for a reference implementation of a
similar domain). Only the QR + short-link generator is in scope here —
no card groups, no physical inventory tracking, no scan analytics, no
connected-site resolution.

## Out of scope (explicitly deferred)

- Scan/usage analytics (counters, timestamps).
- Grouping cards / bulk destination reassignment (TapTag's `CardGroup`).
- Physical inventory status tracking.
- Persisted QR color/style preferences.
- Public-facing styling of the "not configured" / "inactive" redirect
  fallback pages beyond a minimal message.

## Data model

New model `QRCard` in `backend/content/models/qr_cards.py` (new file,
registered in `content/models/__init__.py`), new migration in
`backend/content/migrations/` (never edit existing migrations).

| Field | Type | Notes |
|---|---|---|
| `id` | `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)` | Same idiom as `ProposalShareLink`, `Document`, `WebAppDiagnostic`. Doubles as the short-link token. |
| `name` | `CharField`, required | Human label for the admin listing; the UUID alone isn't identifiable. |
| `destination_url` | `URLField`, blank=True | Optional at creation — the whole point of the shortener is to set/change this independently of the UUID. |
| `is_active` | `BooleanField(default=True)` | Pause a card without deleting it (and without invalidating a printed QR). |
| `created_at` / `updated_at` | auto timestamps | Standard convention across the app. |

No fields for QR color/background — customization is purely client-side at
download time (see below), never persisted.

## Backend

Follows the existing function-based `@api_view` house style (see
`backend/content/views/portfolio_works.py` as the template) — do not
convert to CBVs.

- **Serializers** (`backend/content/serializers/qr_cards.py`): `AdminListSerializer`
  (list rows: id, name, destination_url, is_active, created_at) and a
  `CreateUpdateSerializer` (name required, destination_url optional with URL
  validation when present).
- **Admin CRUD views** (`backend/content/views/qr_cards.py`, all
  `@permission_classes([IsAdminUser])`): list, create, retrieve, update
  (PATCH), delete. Registered in `content/urls.py` under
  `qr-cards/admin/...`, same grouping style as `portfolio/admin/...`.
- **Public redirect view** (`@permission_classes([AllowAny])`, no auth):
  looks up `QRCard` by UUID.
  - Not found → 404.
  - Found, `is_active=True`, `destination_url` set → `HttpResponseRedirect`
    (302) to `destination_url`.
  - Found but inactive → minimal plain-text HTML response (`HttpResponse`,
    not JSON — the visitor is a human who just scanned a physical QR code
    in their phone's browser): "Este enlace no está disponible."
  - Found but `destination_url` empty → same minimal HTML response style:
    "Este enlace aún no ha sido configurado."
- **Routing of the public redirect**: `content.urls` is mounted under
  `/api/` (`projectapp/urls.py:38`), and everything unmatched falls through
  to a catch-all `serve_nuxt` view (`projectapp/urls.py:61`) that serves the
  SPA. For the short link to read as `{domain}/t/{uuid}/` (not
  `/api/t/{uuid}/`), the redirect view is registered as its own top-level
  `path('t/<uuid:card_id>/', ...)` in `projectapp/urls.py`, placed **before**
  the catch-all — same placement pattern already used for `sitemap.xml`
  (`projectapp/urls.py:40`).
- **No new Python dependencies.** QR image generation happens entirely in
  the browser (see Frontend), so no `qrcode`/Pillow usage is needed for
  this feature.

## Frontend

- **Store** — `frontend/stores/qr_cards.js`, Pinia Options API
  (`{ state, getters, actions }`), same shape as
  `frontend/stores/portfolio_works.js`: state (`cards`, `currentCard`,
  `isLoading`, `isUpdating`, `error`), actions using
  `get_request`/`create_request`/`patch_request`/`delete_request` from
  `frontend/stores/services/request_http.js` (content/admin HTTP client —
  not `usePlatformApi.js`).
- **Page** — single `frontend/pages/panel/qr-cards/index.vue`. Given the
  entity only has 2-3 fields, create/edit is a **modal** (`BaseModal`) on
  this page rather than separate `create.vue`/`[id]/edit.vue` routes.
  Table columns: name, short link (`{domain}/t/{uuid}` with a copy-to-
  clipboard button), destination (or "Sin configurar"), active toggle,
  row actions (Editar, Descargar QR, Eliminar).
- **Create/Edit modal**: form with `name` (required) and `destination_url`
  (optional, URL-validated), plus the `is_active` toggle on edit.
- **Download QR modal**:
  - QR always encodes `{domain}/t/{uuid}/` — never the destination
    directly — so the printed/downloaded QR never needs to change even if
    `destination_url` changes later.
  - Rendered client-side via the `qrcode` npm package (new frontend
    dependency; no existing QR library in `package.json`). Its `color.dark`
    / `color.light` options accept 8-digit hex (alpha channel), so a
    transparent background is just `color.light = '#ffffff00'` — no need
    for a heavier library like `qr-code-styling`.
  - Controls: foreground color picker, background color picker, and a
    "Fondo transparente" checkbox that disables the background color
    picker and forces alpha-zero.
  - Live canvas preview + "Descargar PNG" button. Colors are ephemeral
    (form state only) — nothing is persisted to `QRCard`.
- **Sidebar** — new entry in `frontend/config/panelNav.js`:
  `{ label: 'Tarjetas QR', href: lp('/panel/qr-cards'), icon: 'qrcode' }`.
  Deliberately named "Tarjetas QR", not "Tarjetas" — the sidebar already has
  a "Tarjetas" item pointing at `/panel/accounting/cards` (credit-card
  balance snapshots), and reusing the bare label would be ambiguous. No
  `'qrcode'` case exists yet in `frontend/components/platform/SidebarIcon.vue`
  (existing cases: `dashboard`, `bell`, `folder`, `board`, `refresh`, `bug`,
  `file`, `users`, `credit-card`, …) — add a new SVG case for it there.
- **viewCatalog.js** — one entry (`viewType: 'list'`) for
  `/panel/qr-cards` in the `admin-panel` section, following the shape used
  for the portfolio list view. The public `/t/:uuid` redirect is **not**
  cataloged — it's a pure Django-served 302, it never renders a Nuxt page.

## Error handling summary

| Case | Behavior |
|---|---|
| Redirect: UUID not found | 404 |
| Redirect: card inactive | Minimal "no disponible" response, no redirect |
| Redirect: no destination set | Minimal "aún no configurado" response, no redirect |
| Redirect: active + destination set | 302 to `destination_url` |
| Admin create: missing name | Validation error, form blocks submit |
| Admin create/edit: malformed destination_url | Validation error (URLField/serializer validation) |

## Testing plan

- **Backend** (pytest): model defaults (UUID auto-generated, `is_active`
  defaults true); CRUD view permission checks (admin-only); the public
  redirect view's four branches (404 / inactive / no-destination / happy
  path 302).
- **Frontend unit**: the Pinia store's actions against a mocked
  `request_http` client, matching the existing store test conventions.
- **E2E**: create → edit destination → toggle active → list reflects
  changes, tagged with new flow tags. Per the project's mandatory
  `e2e-user-flows-check` skill (this is a new panel view/flow), add
  corresponding entries to `docs/USER_FLOW_MAP.md` and
  `frontend/e2e/flow-definitions.json` before considering the feature done.
- QR rendering itself (canvas/colors) is not unit-tested — it's a thin
  wrapper over the `qrcode` library; correctness is visually verified via
  the download button during manual QA.
