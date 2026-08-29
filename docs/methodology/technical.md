# Technical Documentation — ProjectApp

> **Formularios 2026-08-29:** `BaseFormField` centraliza el mensaje visible,
> `role="alert"`, `aria-invalid` y `aria-describedby` tanto para validación
> nativa como para errores explícitos del API. `ClientAutocomplete` sólo ofrece
> creación al vuelo cuando el consumidor declara `allow-create`, conserva esa
> acción visible aun con coincidencias y puede exigir una selección realmente
> confirmada. `BaseModalActions` mantiene las acciones finales aisladas del
> contenido de validación.

> **Tracking 2026-08-29:** `useProposalTracking` suspende su intervalo durante
> `document.visibilityState=hidden`, finaliza por `sendBeacon`, reanuda con un
> segmento nuevo y comparte una sola promesa para flushes concurrentes. Al
> confirmar un POST sólo retira las entradas incluidas en ese request.

> **Actualización — 2026-08-28:** cada entrega crea un snapshot previo al SMTP
> con cuerpo, enlaces, MIME total y bytes decodificados de sus adjuntos. Si el
> almacenamiento falla, el gateway bloquea el envío. Los archivos se sirven por
> endpoints administradores `no-store`, el PDF usa el visor compartido y el
> reenvío sólo admite cambiar destinatario mientras reutiliza la copia archivada.

> **Estado 2026-08-28 — implementado:** el catálogo adicional reutiliza DRF
> FBV, servicios de dominio, ReportLab, el cliente HTTP del panel y componentes
> base. La página canónica es indexable y prerenderizada; cada enlace
> seleccionado lleva `noindex`, selección inmutable y contenido vivo. Los
> errores JSON de descargas PDF se decodifican aun cuando Axios los entrega como
> `Blob`, para conservar mensajes accionables.

## 1. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend Framework** | Django | 6.1 |
| **REST API** | Django REST Framework | 3.18.0 |
| **JWT (platform)** | djangorestframework-simplejwt | >=5.3,<6.0 |
| **Frontend Framework** | Nuxt 4 | ^4.5.2 |
| **Vue** | Vue 3 | ^3.5.42 |
| **State Management** | Pinia (Options API) | ^4.0.3 |
| **CSS Framework** | TailwindCSS | ^6.14.0 (@nuxtjs/tailwindcss) |
| **Animations** | GSAP + ScrollTrigger + ScrollToPlugin | ^3.15.0 |
| **Charts** | ApexCharts + vue3-apexcharts | ^7.0.0 + ^1.11.1 |
| **i18n** | @nuxtjs/i18n | ^10.6.0 |
| **Task Queue** | Huey (RedisHuey) | >=3.3.4 |
| **Cache/Queue Backend** | Redis | >=8.1.0 |
| **Database (prod)** | MySQL 8.4 | via mysqlclient >=2.2 |
| **Database (dev)** | SQLite 3 | built-in |
| **HTTP Client** | Axios | ^1.20.0 |
| **PDF Generation** | ReportLab + pypdf | `>=5,<6` + `>=6.16.2,<7` |
| **Image Processing** | Pillow | 12.3.0 |
| **Email** | Django MAILERS + EmailMultiAlternatives | SMTP (GoDaddy) |
| **WhatsApp** | CallMeBot API | via requests |
| **Testing (backend)** | pytest + pytest-django + pytest-cov | 9.1.1 + 4.14.0 + 7.1.0 |
| **Testing (frontend unit)** | Jest + @vue/test-utils | 29.7.0 + ^2.5.0 |
| **Testing (E2E)** | Playwright | ^1.62.1 |
| **Linter** | Ruff | via ruff.toml |
| **Pre-commit** | pre-commit | .pre-commit-config.yaml |
| **CI/CD** | GitHub Actions | ci.yml |
| **Server (prod)** | Gunicorn + Nginx | `>=26.2,<27` |
| **Process Manager** | systemd | 3 services |
| **Backups** | django-dbbackup | >=4.0.0 |
| **Profiling** | django-silk (optional) | >=5.5.2 |
| **Config Management** | python-decouple | >=3.8,<3.9 |
| **Fake Data** | Faker | 40.37.0 |
| **Token Encryption** | cryptography (Fernet) | >=50.0.1,<51 | LinkedIn OAuth token + Project admin credential encryption |
| **MCP Transport** | JSON-RPC over Streamable HTTP | Per-connector capability URL; DRF throttle key is client IP + registered slug |

---

## 2. Development Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Edit with local settings
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py create_fake_data 5    # Creates contacts, portfolio, proposals, blog
python3 manage.py runserver             # http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                             # http://localhost:3000
```

#### Documents navigation URL contract

`useDocumentFilterQuery` synchronizes the list with these canonical query keys:
`folder`, `scope`, `states`, `without_states`, `preset`, `client`, `project`, `q`,
`order`, `view`, `page` and `focus`; `tags` remains accepted only for legacy deep
links during the workflow rollout. Defaults are omitted, ids are normalized, and
interactive filter changes use `router.replace` so browser history represents meaningful list states.
Global search uses an effective all-documents scope without overwriting the scope
that must be restored when the search is cleared or revisited.

Editor links carry `from=<localized documents-list URL>`. All editor exits resolve
that value through `documentReturnNavigation.js`, whose allowlist accepts only the
Documents list in the current application. The explicit return adds `focus` and
restores the owning page before focusing its row/card; native browser Back consumes
the original route entry. A direct, malformed or cross-module `from` falls back to
the localized Documents root.

### Codex Runtime Surfaces (ProjectApp)

- Always-on instructions:
  - `AGENTS.md`
  - `backend/AGENTS.md`
  - `frontend/AGENTS.md`
- Native repo skills: 41 directories under `.agents/skills/`; the parallel `.claude/skills/` tree has 40. `proposal-create` exists in both ecosystems and keeps its shared body/references/scripts aligned, with ecosystem-specific invocation metadata.
- Project config: `.codex/config.toml`
- Methodology guide: `docs/CODEX_METHODOLOGY_GUIDE.md`
- Setup & activation: `docs/CODEX_SETUP.md`
- Migration history: `docs/CODEX_MIGRATION_MAP.md`
- Compatibility surfaces: `CLAUDE.md`, `backend/CLAUDE.md`, `frontend/CLAUDE.md`, `.claude/`
- Naming policy: `debug` is canonical; `debugme` remains as legacy alias

`proposal-create` reads proposal shape and business defaults at runtime rather than freezing them in the skill. Its artifacts live under the gitignored `proposal-artifacts/`: an importable JSON plus a manifest for environment, base/effective price, hosting, modules and section visibility. Its optional creator uses `ProposalFromJSONSerializer` and `build_proposal_from_json`; database writes require a dry-run followed by the literal `CREATE_DRAFT` confirmation.

`client-report` owns the canonical client-delivery copy for report documents. It
generates `client_email_subject`, `client_email_body`, and
`client_whatsapp_message`, then sends them with the markdown through the Documents
MCP after operator confirmation. `client-message` delegates report creation and
prints those exact values rather than redrafting them. The fields are optional model
metadata exposed by admin detail/create/update and MCP detail/create/update only.
`client_custom_notes` extends the same private boundary with an ordered JSON list of
`{title, content}` objects; `document_notes.normalize_client_custom_notes()` is the
shared REST/MCP validator, trims both values, requires both to be non-empty, and caps
titles at 255 characters. `client-report` and `client-message` deliberately leave
that free-form collection alone. List serializers, PDF generation, and platform
document serializers exclude all four private-note fields.
On the admin edit page, the notes modal reuses `PATCH documents/:id/update/` with
only those four fields. `useUnsavedGuard.commit(keys)` re-baselines that saved subset
without clearing unrelated page edits. On the create page the same modal runs in
draft mode and performs no request until the complete document is created.

### Task Queue (for async features)

```bash
cd backend
source venv/bin/activate
python3 manage.py run_huey              # Requires Redis running
```

> **Note**: In development, Huey runs in `immediate` mode (tasks execute synchronously) when `DJANGO_ENV != 'production'`.

### Useful Management Commands

| Command | Description |
|---------|-------------|
| `create_fake_data --settings=projectapp.settings_dev --replace --count 60 --seed N --anchor-date YYYY-MM-DD` | Atomically rebuild the complete representative dataset |
| `create_fake_clients_projects` | Create the 60-client / 67-project skew and edge identities |
| `create_fake_accounting` | Create coherent dated income, expense, hosting and payment data |
| `create_fake_documents` | Create project/client documents and income-backed collection accounts |
| `create_fake_communications` | Create short, regular and long client histories |
| `create_fake_auxiliary` | Create Email, QR, Linktree, LinkedIn and MCP list data |
| `create_fake_proposals` | Create fake proposals with sections and requirements |
| `create_fake_blog_posts` | Create fake blog posts with structured JSON content |
| `create_contacts` | Create sample contact entries |
| `delete_fake_data --settings=projectapp.settings_dev --confirm` | Reset development data while preserving staff/catalogs/manual accounting |
| `cleanup_in_calculator` | Clean up stale in-calculator proposal states |
| `update_hosting_specs` | Update hosting tier specifications |
| `zero_group_price_percent` | Reset group price percentages |
| `create_platform_admin` | Create a platform admin user |
| `seed_demo_clients` | Seed demo client users for platform |
| `seed_platform_data` | Seed full platform demo data (projects, requirements, etc.) |
| `seed_mihuella` | Seed specific demo data for mihuella project |

Fake-data commands share `content.fake_data`: the positive
`FAKE_DATA_ALLOWED` capability, default volume/seed, an isolated per-module RNG,
an explicit business-date anchor and the executable concrete-model inventory.
Base and production settings hard-disable the capability; development settings
enable it while forcing SQLite. The root command is fail-fast inside one outer
transaction, and requires `--replace` on a populated business graph. See
`docs/FAKE_DATA_COVERAGE.md` for targets and relationships.

---

## 3. Environment Configuration

All configuration via `python-decouple` reading from `backend/.env`. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_ENV` | `development` | `development` or `production` |
| `DJANGO_DEBUG` | `true` | Debug mode |
| `DJANGO_SECRET_KEY` | `change-me` | Secret key |
| `DJANGO_ALLOWED_HOSTS` | `` | Comma-separated hosts |
| `DJANGO_DB_ENGINE` | `sqlite3` | Database engine |
| `DJANGO_DB_NAME` | `db.sqlite3` | Database name/path |
| `REDIS_URL` | `redis://localhost:6379/5` | Redis connection |
| `EMAIL_HOST` | `smtpout.secureserver.net` | SMTP server |
| `EMAIL_PORT` | `465` | SMTP port |
| `EMAIL_USE_SSL` | `true` | SSL for SMTP |
| `FRONTEND_BASE_URL` | `http://localhost:3000` | Used for proposal links in emails |
| `NOTIFICATION_EMAIL` | `team@projectapp.co` | CSV-supported recipient list for ALL internal team notifications (first view, comments, seller inactivity, stage warnings, stage overdue, etc.). Read by `ProposalEmailService._get_notification_recipients()`. |
| `ENABLE_SILK` | `false` | Enable query profiler |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `http://127.0.0.1:5173,...` | CORS origins |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://127.0.0.1:5173,...` | CSRF trusted |
| `PROJECT_ACCESS_CIPHER_KEY` | *(required in prod)* | Fernet key for project admin credential encryption. Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

---

## 4. Key Technical Decisions

### Static SPA fallback integrity and locale ownership

- Django's `serve_nuxt` is the production router for generated pages. Private
  routes are skipped during prerender and receive `.output/public/200.html` as
  their client-side entry document.
- Django `_resolve_locale()` owns the redirect from `/`, using the
  `preferred_locale` cookie and nginx's `X-Country` header. Nuxt i18n keeps
  `strategy: 'prefix'` but `detectBrowserLanguage: false`; enabling an
  unprefixed browser-language redirect can transform `/200.html` into a
  self-referential meta refresh.
- `frontend/update-django-template.js` is the publication chokepoint. It validates
  that `200.html` is non-empty, has no meta refresh, and includes the `#__nuxt`
  mount before staging or swapping `backend/static/frontend/`.

### MySQL uniqueness for optional sync keys

- MySQL does not enforce Django conditional unique constraints. Do not add a
  `condition=... IS NOT NULL` when the field already stores absence as SQL
  `NULL`: a plain composite `UniqueConstraint` preserves multiple `NULL` rows
  and enforces every non-null value on MySQL, SQLite and PostgreSQL.
- `DocumentState.system_key` follows that nullable-column pattern and is unique
  with `catalog`. Optional sync keys that instead encode absence as an empty
  string use functional constraints with `NullIf(F(key), Value(''))`.
- Empty strings converted through `NullIf` can repeat; non-empty values remain
  unique inside their project/user scope.
- Schema migrations must check for existing duplicate non-empty keys before replacing an index, so deployment fails before DDL with a useful remediation message.

### Migration graph convergence

- Parallel feature branches may legitimately create migrations with the same number and parent. After both land, add an explicit empty merge migration that depends on both leaves.
- Never rename or re-parent a migration that has already reached a shared branch or an environment. The merge node preserves both histories and gives later migrations one canonical leaf.
- A pre-deploy check must confirm `MigrationLoader.detect_conflicts()` is empty so a duplicate leaf is caught before the production migration phase.

### View inventory and operational taxonomy are separate contracts

- `frontend/config/viewCatalog.js` is the exhaustive technical inventory. `npm run check:view-catalog` derives Nuxt routes from `frontend/pages/` and rejects orphan pages, stale entries, duplicate URLs/files, route mismatches and invalid metadata in CI.
- `frontend/config/viewCapabilityCatalog.js` is a curated commercial projection over that inventory. It owns three spaces (Panel interno, Plataforma de clientes and Experiencias públicas), their 20 main modules and representative submodules. Its validator guarantees complete metadata, unique nodes, valid relationship endpoints, exact ownership for all 104 routes and exact ownership for all seven technical sections without turning source-code dependencies into product relationships.
- `ViewExplorerContextPanel` derives purpose, value, actors, stage, child modules and technical references from the selected or previewed node. Hover/focus preview is ephemeral; selection remains the only interaction that changes the shareable URL. Context is curated and deterministic, with no live-metrics API.
- The Explorer uses compact cards below the landscape breakpoint and positioned semantic buttons plus SVG connectors from landscape upward. `useOrbitalExplorer` owns rotation, pointer drag, keyboard adjustments, zoom and reduced-motion behavior, and accepts an external pause while a tour is active.
- `useViewMapMode` owns shareable `viewMode`, `node`, `tour` and `relations` query state. A valid `tour=<space-id>` normalizes to one of that space's main modules; stopping it preserves `node`, while navigation outside its ordered steps returns to free mode.
- `ViewMapSettings.default_view_mode` accepts `list`, `map` or `explorer`. The backend persists only the preferred entry mode; the active route remains the authority for shared links.

### Client chart loading and bundle budget

- ApexCharts is not a global Nuxt plugin. `components/ApexChart.client.vue` imports only the chart types and features used by the application and is consumed through Nuxt's lazy `LazyApexChart` component.
- Heavy vendor splitting belongs under `vite.$client.build.rollupOptions`; applying the same manual chunks to Nitro's server build can generate unusable server output.
- The production build gate is zero emitted client chunks above 500,000 bytes. Current maximum after gzip-independent measurement is 448,634 bytes.

### Canonical responsive profiles

- Frontend responsive automation uses five named reference viewports: 412×915, 835×1195, 1195×835, 1440×900 and 2560×1440. Physical-device certification is a separate acceptance step.
- `frontend/config/responsive.js` feeds Tailwind and Playwright; `responsiveAcceptance.js` assigns every catalog view to a repeatable module script. Individual pages must not invent alternative device matrices.
- The portrait-tablet profile is an explicit acceptance target, and admin content is capped at 1400 px on the large-monitor profile.
- The responsive Definition of Done, commands and periodic review live in `docs/methodology/responsive-acceptance.md`.

### Responsive panel decisions are capability branches

- The operational compact boundary is `useIsMobile(PANEL_BREAKPOINTS.landscape - 1)`: the 412 px and 835 px reference viewports use drawers/cards; the 1195 px landscape reference uses the two-zone/table branch. Tailwind remains responsible for inner density and card columns, not for duplicating whole interactive trees.
- `BaseDrawer` owns modal semantics, focus containment, Escape/backdrop close and body-scroll lock. Use it for a transient folder/filter/action zone; do not rebuild those mechanics inside a page.
- `BaseModal` already uses `100dvh` below `panel-portrait` and preserves its semantic size above that boundary. Long workflows keep a scrollable body and sticky footer actions; consumers do not introduce a second fullscreen prop.
- Semantic modal ceilings are `confirm` 28 rem, `form` 42 rem, `form-wide` 64 rem, `wizard` 80 rem, `detail` 64 rem and `workspace` `min(90vw, 100rem)`. Consumers select intent and do not pair `kind` with a legacy `size` override.
- Short labels, chips, buttons and segmented options default to `white-space: nowrap`; a sentence-like exception must opt into `labelPolicy="wrap"` or `textPolicy="wrap"`. A segmented group may reflow between options, never inside one option.
- Multi-column forms use `BaseFormRow` bands. Put explanatory copy in the row-level `help`/`#help` surface, and use `BaseFormRowAction` for a button beside a field so its vertical reference is the control band.
- Every panel page in this family consumes `PAGE_MAX_WIDTH` (`max-w-[87.5rem] mx-auto`). At 2560 px, measure the page root rather than inferring the cap from a class.
- Responsive acceptance uses that exact matrix. A qualifying E2E enters from panel navigation, asserts fixture data and verifies `scrollWidth <= clientWidth`.
- The specialized Documents table declares its fixed business order and
  `keep/group` policy in the same column array consumed by width resolution.
  Landscape keeps Actions/Title/States/Date and groups Client/Project; compact
  cards apply the same priority without persisting a user-specific column order.
- A table with one three-dot row menu opts into
  `rowActionsLayout="menu-start"`. The shared table/grid primitives then render
  Checkbox → Actions → Data, reserve an immutable 3.5 rem track outside the
  proportional data split, expose an accessible but visually empty header and
  stop click/auxclick propagation from the action cell. The default
  `inline-end` mode is only for legacy loose-icon action rows; do not migrate
  those implicitly while adopting the kebab contract.
- KPI cards use `BaseIndicatorCard`. Its fixed three-row layout always reserves
  one support line; the help control remains outside the optional main action so
  the DOM never nests buttons. Below `PANEL_BREAKPOINTS.landscape`, dense KPI
  headers expose two summaries and move the complete facts into `BaseDrawer`;
  expanded layouts may suppress zero-valued detail cards but must retain their
  filters in the compact drawer or ordinary filter controls.

### Panel-owned dialogs and observation deletion

- Browser-native `window.alert`, `window.confirm` and `window.prompt` are not UI
  primitives. Panel flows use `BaseModal`, `ConfirmModal` or an inline actionable
  error; `npm run check:panel-native-dialogs` scans `pages/panel` and
  `components/panel`, and CI runs it independently of the affected-flow selector.
- `DocumentNote` soft deletion uses nullable `deleted_at`/`deleted_by`; ordinary
  document, episode and history reads filter deleted rows. `DocumentNoteEvent`
  stores `deleted`/`restored`, actor, timestamp and structural details only.
- All removal paths call `document_note_service.delete_notes()` under one
  transaction and document/note locks. `DELETE .../notes/:id/` is the single-row
  facade; `POST .../notes/bulk-delete/` accepts 1–100 unique IDs from one document.
  Trash, restore and activity use `?scope=deleted`, `.../:id/restore/` and
  `.../notes/events/` respectively.
- The Documents MCP mirrors the lifecycle with `delete_document_notes`,
  `list_deleted_document_notes` and `restore_document_note`; its catalog now has
  17 tools. It reuses the service rather than reproducing workflow rules.

### Static payload and collection policy

- Production sets `experimental.payloadExtraction: false`. The generated site is mounted below Django's `/static/frontend/` CDN prefix; keeping payloads inline prevents Nitro from treating CDN payload URLs as prerenderable HTML routes.
- Both `scripts/deploy.sh` and the automatic blog rebuild call `collectstatic` with `clear=True`/`--clear`. `staticfiles/` is generated output and must not retain hashed chunks or file/directory shapes from older Nuxt builds.
- A production-equivalent build must contain zero `_payload.json` artifacts and zero JavaScript chunks above 500,000 bytes before publication.

### MCP connector concurrency

- Connector URLs remain token-authenticated capability URLs; tokens are not part of the throttle key.
- Nine registered connectors — blog, documents, proposals, diagnostics, clients,
  tasks, accounting, LinkedIn personal and communications — receive independent
  per-IP buckets keyed by slug, allowing Codex to initialize configured domains in
  parallel.
- Unknown slugs share one `unknown` bucket. Never key untrusted paths directly without first checking them against `TOOLS_BY_SLUG`.
- `content/mcp/contracts.py` is the field-level anti-drift manifest. A model change
  in one of those domains must update its classification, tool schemas and
  descriptions in the same delivery; focused tests fail on missing or stale fields.
- `docs/MCP_VALIDATION_RUNBOOK.md` is the repeatable create/read/update/error script
  for connector delivery and later revalidation.

### Single outbound email gateway

- Production code may perform Django mail I/O only through
  `content.services.email_delivery_service.EmailDeliveryGateway`; a focused
  static test scans every backend Python file and rejects direct alternatives.
- Every call carries a stable `template_key` registered in
  `outbound_email_inventory.OUTBOUND_EMAIL_CHANNELS`. Unknown keys raise before
  SMTP, and every non-client message also requires an explicit classification.
  The same copy rule applies to client, internal and security traffic.
- The primary envelope is sent before any copy lookup or copy SMTP attempt.
  Configured internal recipients then receive independent BCC-only envelopes.
  A lookup/copy failure is logged independently and cannot alter or retry the
  already-successful primary delivery.
- Before the primary SMTP call, the gateway renders a clone into MIME and writes
  `EmailDeliverySnapshot`, `EmailAttachmentSnapshot` and `EmailLinkSnapshot`.
  Attachment payloads are decoded from the rendered MIME, hashed and stored as
  independent media files; a capture/storage/provenance mismatch raises and
  prevents transport. Primary and copy logs reference the same snapshot.
- `EmailLinkSnapshot.url` keeps the exact URL up to 2048 characters, but database
  uniqueness uses the fixed 64-character `url_sha256` with `snapshot`. Indexing
  the full URL under MySQL `utf8mb4` can exceed InnoDB's 3072-byte key limit.
  The model save path owns fingerprinting, so the snapshot writer must not bypass
  it with `bulk_create`.
- Migration `content.0223_email_delivery_snapshots` contains a MySQL-only recovery
  guard for its known non-transactional partial-apply state. It removes the three
  snapshot tables and `EmailLog.snapshot_id` only when every artifact is empty;
  any retained snapshot or reference aborts before cleanup. Its `RunPython` is
  explicitly `atomic=False`, because Django otherwise opens a transaction around
  the recovery and MySQL rejects the required DDL. Migration `0228` backfills
  fingerprints before adding the short unique constraint.
- `EmailLog.delivery_id` groups primary and copy attempts;
  `delivery_role=primary|copy` keeps dashboards, cooldowns, contact counts and
  retry endpoints from treating internal copies as new primary sends. Every
  gateway send has baseline history, including internal and security messages;
  complete bodies are retained by the explicit product policy.
- Copy recipients are database configuration, separate from
  `NotificationRecipient`/`NOTIFICATION_EMAIL`, and can subscribe to one or
  more stable families. Migration `content.0225` provisions
  `carlos18bp@gmail.com` active for all eight families; the address remains an
  administrable `EmailCopyRecipient` row instead of transport-layer branching.
  See `docs/client-email-copy-inventory.md`.
- `/api/emails/history/<log>/attachments/<attachment>/` streams retained bytes
  only to panel admins (`private, no-store`; inline only for PDF). Exact resend
  accepts a validated recipient only, constructs a new snapshot with `resend_of`,
  and preserves archived subject/body/attachments. Rows without a snapshot are
  `legacy_partial` or `legacy_unknown` and cannot be downloaded or resent.

### Document workflow is episode-derived and visibility-independent

- `Document.is_client_visible` is the only client-portal visibility gate. The
  legacy `status` field remains temporarily for expand/contract compatibility and
  must not be reused for internal workflow decisions.
- `DocumentStateGroup.selection_mode` expresses the only-one cycle versus additive
  signals. `DocumentState.system_key` is stable integration identity; the user-facing
  name, description and color remain editable. Seed states may not be moved into a group whose
  mode contradicts their integration role.
- Open `DocumentStateEpisode` rows are the materialized current state. Every open,
  close, removal, exclusive transition, merge and effective-date correction writes a
  `DocumentStateEpisodeEvent`; this document-local stream is the single audit source
  for workflow changes.
- All episode writes go through `document_state_service`, which locks the document
  and validates future dates, exclusivity and symmetric incompatibilities. Catalog
  edits are rejected when they would invalidate combinations already active.
- `DocumentNote` is the normalized private observation model.
  `document_note_service` links it to needs-fix and refuses to auto-close the signal
  while another linked observation remains open.
- Migration `content.0210_document_state_episodes` is deliberately non-inferential: Published maps to
  visibility, existing documents receive no invented cycle state, old tag assignments
  become additive episodes with unknown `opened_at`, and collection accounts remain
  outside this workflow.
- The panel client uses `stores/services/request_http` through the Options-API
  `document_states.js` store. State names are suggestions only; all mutation and
  conflict enforcement remains server-owned.

### Project lifecycle reuses the shared state engine

- `DocumentStateGroup`, `DocumentState`, `DocumentStateEpisode` and
  `DocumentStateEpisodeEvent` are catalog-scoped (`documents` or `projects`). An
  episode belongs to exactly one document or project.
- `Project.current_state` is canonical. `Project.status` is a compatibility mirror;
  create/update APIs reject direct lifecycle input outside the transition service.
- `content.services.project_state_service` owns preview, token validation, atomic
  consequences, history initialization, catalog merge and hosting-failure suggestions.
- Session/CSRF APIs: `GET|POST /api/project-states/`, catalog update/retire/merge,
  `POST /api/projects/<id>/state-transitions/preview/`, apply at
  `/state-transitions/`, and `GET /state-history/`.
- Nuxt uses the Options-API `project_states.js` store and the same
  `StateCatalogManager` / `StateHistoryModal` primitives as Documents. The project
  transition modal is specific because it must collect financial decisions.
  `ProjectStateHelpBadge` pairs the editable `description` with the derived,
  read-only `operational_effect_help` in counts, filters, rows, cards, catalog and
  transition context, with pointer, keyboard and touch access.
- Migrations `accounts.0055_project_lifecycle_state` and
  `content.0213/0214_project_lifecycle_states` add the relations and map known
  legacy statuses. `content.0218_project_state_help` adds state descriptions,
  backfills existing project states and seeds **En evolución** after **Activo** as
  a second `operating` meaning. Legacy `archived` remains unclassified and
  review-required; deploy applies migrations, never a session worktree.

### Project-owned document roots and reviewed reconciliation

- Migration `content.0222_project_document_folders` adds the nullable one-to-one
  `DocumentFolder.managed_project`, database checks for managed-root invariants,
  and `DocumentState.show_in_document_manager`. Existing development, active and
  evolving project states are seeded visible; later catalog entries are configured
  in the state manager instead of being hard-coded into the folder UI.
- `ProjectDocumentFolderService` is the only owner of automatic root creation and
  synchronization. The `Project` post-save signal delegates to it; it is atomic,
  idempotent and creates the four standard children only when the managed root is
  first provisioned. Descendants retain normal user-controlled hierarchy.
- Managed roots cannot be renamed, moved, archived, deleted or reordered through
  REST, MCP or Django admin. On project deletion the nullable ownership link is
  cleared, deliberately preserving the former root and all content as a personal
  hierarchy.
- Production reconciliation is always two-step and review-gated:
  `python manage.py reconcile_project_folders --plan <artifact.json>` performs no
  writes and emits the JSON artifact plus a Markdown proposal. After every pending
  action is marked `approve` or `skip`, run
  `python manage.py reconcile_project_folders --apply-reviewed <artifact.json> --confirm <sha256> --inverse-out <snapshot.json>`.
  Apply aborts if the database fingerprint or digest changed, if decisions remain
  pending, or if conflicts exist. Never manufacture an approval artifact or apply
  a proposal that was not reviewed against the named folders and impacts.

### Communications are a separate domain with shared infrastructure

The client communications registry lives in the existing `content` Django app
but does not reuse `Document` as its persistence shape. Four models introduced
by migration `content.0210_communications_registry` own threads, ordered messages, protected document
references and append-only date corrections. `communication_service.py` is the
only write owner; DRF function-based views remain thin and staff-only.

The operating model is transport-neutral: `source=manual` means an operator
recorded the fact. `source=platform_email` and the optional one-to-one
`email_log` remain persistence seams, not a product commitment to automatic
delivery. “Respondido” is derived from a non-void reply and is not an additional
mutable database status. Delivered/received messages are corrected or annulled,
never edited.

The Nuxt surface is `/panel/communications`; its Options-API Pinia store uses
`request_http` (session + CSRF), not `usePlatformApi`. Documents are referenced
by ID and expose reverse usage through
`GET /api/documents/<id>/communications/`.

`communication_query_service.py` is the single read contract for REST and MCP.
It parses scalar legacy parameters plus comma-separated/repeated values, applies
OR inside `status`, `channel`, `direction` and `message_status`, and AND across
dimensions. Message dimensions share one correlated `Exists`, so their values
must match the same message. `project=none` addresses unscoped threads; `order`
accepts `recent`, `oldest` or `title`. The REST response also includes
self-excluding option counts plus project/client navigation counts, including
nested thread totals.

The panel URL is canonical for selection, filters, order and the `thread` detail
modal. `CommunicationNavigation` is resizable on landscape widths and moves to
the shared drawer below that breakpoint. `CommunicationFilterPanel` consumes
searchable `BaseFilterDropdown` instances with multi-selection and counts.
Named cuts reuse `SavedFilterTab` with the `communication` view choice; migration
`accounts.0056_add_communication_saved_filter_view` adds only that catalog value.

Both parallel `0210` leaves converge through `content.0211_merge_document_states_communications`.

`content.0212_seed_communications_mcp` registers the Communications connector
inactive and tokenless. `content/mcp/communication_tools.py` exposes five JSON-RPC
tools and reuses the same queryset/serializer/service boundary as the panel. No MCP
tool sends email or WhatsApp: `mark_message_sent` only records a delivery fact already
confirmed by the operator or another integration.

### Authentication: Dual Strategy
- **Panel (`/panel/`)**: Django session + CSRF; middleware `admin-auth.js` checks `/api/auth/check/`; unauthenticated → Django admin login
- **Platform (`/platform/`)**: JWT via SimpleJWT (access + refresh tokens); middleware `platform-auth.js`; platform stores use `composables/usePlatformApi.js` (axios with JWT interceptors)
- Never mix the two HTTP clients across contexts

### Hybrid Rendering (SSR + SPA)
- **SSR**: Home, landing pages, about-us, portfolio, blog (SEO-critical)
- **SPA**: Admin panel (`/panel/**`), proposal client view (`/proposal/**`)
- Configured via `routeRules` in `nuxt.config.ts`
- Pre-rendered routes for static generation in production

### Blog prerender at build time (build:django)
- `npm run build:django` (`frontend/update-django-template.js`) is the single chokepoint for every production build — used by both `/deploy-and-check` and the on-publish `run_frontend_rebuild` task.
- Blog post pages are prerendered to static HTML so crawlers and link previews get the full article + per-post `og:`/JSON-LD metadata. The route list is fetched from `/api/blog/sitemap-data/`; each page fetches its post from `/api/blog/<slug>/` (`pages/blog/[slug].vue`).
- **Must prerender against Django on loopback, not the public domain.** Hitting `https://projectapp.co` routes the build's many API requests through nginx, whose `limit_req zone=api` (5 r/s) returns 429 and drops most posts (see error-documentation ERR-015). The build script therefore spins up a throwaway Django server on a free 127.0.0.1 port using `backend/projectapp/settings_build.py` (prod DB + data, HTTPS enforcement off), prerenders against it, and tears it down.
- `settings_build.py` exists **only** for this loopback build server — never serves real traffic. It disables `SECURE_SSL_REDIRECT`/HSTS/secure-cookies that `settings_prod` enforces.
- Gates: `PRERENDER_BLOG=1` enables it; `PRERENDER_API_ORIGIN` overrides the target; `PRERENDER_REQUIRE_BLOG=1` makes a failed prerender a hard build error. With no backend present (CI/dev) the script skips the local server and falls back to the env-provided origin.

### Current hosting terms versus historical snapshots

- The selectable hosting enum is `quarterly`, `semiannual`, `nine_month`; `monthly` and `annual` constants/maps exist only to render preserved history.
- `normalize_hosting_plan(proposal, data)` is context-sensitive: public/PDF callers preserve closed or inactive proposal JSON, while operational onboarding passes `force_current_terms=True` to create a new 9/6/3-month project snapshot.
- The twelve-month hosting percentage remains only a calculation reference. A nine-month cycle is `effective_monthly_amount × 9`; it is not 75% of an independently rounded annual total at runtime.
- Schema migrations rename `hosting_discount_annual` to `hosting_discount_nine_month`. Data migrations update only current proposal/accounting/platform state, never paid cycles or payments, and guard Wompi-linked work before mutation.
- Write serializers reject new monthly/annual accounting values but allow an unchanged legacy value when editing another field on a historical row.

### Server-owned recurring COP projections

- `RecurringPayment.cop_equivalent` remains persisted for consistent API, export, dashboard and MCP aggregation, but it is `editable=False` and read-only in write serializers.
- `RecurringPayment.save()` derives COP from `price` and `currency`; USD uses the singleton `AccountingSettings.usd_exchange_rate`. `monthly_cop_cost` then divides that canonical charge by the normalized frequency length.
- `AccountingSettings.save()` detects a persisted rate change inside one transaction and bulk-refreshes all recurring equivalents. This is an explicit current-rate policy; no external exchange-rate API is involved.
- Migration `content.0208_recalculate_recurring_cop_equivalent` repairs every existing COP and USD row from its current inputs. Panel, MCP, fake-data and import writers do not accept `cop_equivalent` as an independent input.
- Frontend calculations are previews only. The panel refetch after save remains authoritative and rebuilds both the category sums and the general monthly COP total from the server response.

### Recurring lifecycle contract

- Migration `content.0219_recurring_lifecycle` adds indexed `is_archived`, `archived_at`, `reminders_muted` and `reminders_muted_until` fields. `reminders_effectively_muted` is serialized from stored preference plus today's Bogotá date; an expired dated mute is cleared by the payment-calendar collector.
- `content/services/accounting_recurring_service.py` is the single lifecycle writer. It builds a duplicate form draft, toggles active state, archives/restores, changes reminder mute and applies at most 500 selected ids under `transaction.atomic()` + `select_for_update()`. Missing/conflicting ids are validated before the first write, so a bulk action never partially succeeds.
- REST endpoints live under `/api/accounting/recurring/`: `:id/duplicate-draft/`, `:id/state/`, `:id/archive/`, `:id/restore/`, `:id/reminders/mute/` and `bulk-action/`. The list/export contract accepts `archive_scope=current|archived|all`; current is the default. Hard delete returns 409 until the record is archived.
- Accounting MCP exposes the same six operations (`get_recurring_duplicate_draft`, `set_recurring_active`, `archive_recurring`, `restore_recurring`, `mute_recurring`, `bulk_action_recurring`) through the shared serializers/service. Lifecycle fields are read-only in the generic MCP model contract so callers cannot bypass those invariants.
- The panel uses a PA-102 `menu-start` track in grouped and classic tables, plus `RecurringActionsModal`, `RecurringMuteModal` and `RecurringBulkActionBar`. Every successful lifecycle mutation refetches server metadata; local projections never guess the new total. `countsTowardRecurringBudget()` mirrors the backend gate (`is_active && !is_archived`) for group totals, weights and charts.
- Duplicate is deliberately two-step: GET returns inherited editable inputs and a recalculated `cycle_anchor_date`, then the existing create endpoint writes only after the operator reviews the ordinary form. Reminder cadence, notes, archive state and audit history are never copied.
- This contract manages definitions only. It does not create `ExpenseRecord` or `PocketMovement` rows and has no charge-history relation; adding those requires a separate idempotent period-charge service and ledger transaction design.

### Collection-account linked-income selector

- `CollectionAccountFormModal.vue` keeps the eligible expected/liquid response in memory and derives scope and kind counts client-side; no API parameter or schema field is needed for its starting view.
- `DEFAULT_INCOME_KIND = 'expected'` is reapplied when the modal opens and whenever its selected client changes. There is intentionally no local-storage/session memory.
- The kind predicate reads `IncomeRecord.kind`, never `payment_status`, so expected rows with partial settlements remain visible. The contextual empty action changes kind to `all` first and preserves client scope; it widens scope only if that client has no eligible rows.

### Client picker catalog and progressive paging

- `GET /api/proposals/client-profiles/search/` accepts `q`, `limit`, `offset`
  and optional `order=name|-name`. It caps each page at 20, sorts case-
  insensitively by the same display-name fallback the serializer renders, and
  uses the profile id as a stable tie-break. Missing/invalid order stays A-Z.
- The response body remains the legacy array. The filtered total is exposed as
  `X-Total-Count`, allowing existing consumers to remain compatible while
  `proposal_clients.searchClients()` derives `hasMore` and `nextOffset`.
- `ClientAutocomplete` keeps one request/selection state and two presentations.
  `floating` is the backward-compatible default and loads `q=''` on focus when
  uncommitted. `catalog` loads while its `active` prop is true, is always visible
  in flow and delegates the shared result markup to
  `ClientAutocompleteResults`. Text input is debounced and generation-guarded;
  scroll-end paging appends de-duplicated rows. Bulk client assignment supplies
  `panel.accounting.bulk-client-name-order`, default `asc`, as the browser-local
  persistence key. Initial and subsequent-page failures have separate retry
  states, and an empty initial catalog offers the same `create-new` event as an
  unmatched filter.

### Content Storage: Structured JSON
- Proposal sections, portfolio works, and blog posts store content as JSON fields
- Each proposal section's `content_json` matches the props schema of its Vue component
- Enables rich, structured content without a full CMS
- Blog supports dual format: structured JSON (preferred) with HTML fallback
- `functional_requirements.groups` has nine base entries because five
  value-added-module catalogs remain stored there for shared data. Its first four
  client-facing entries are ordered `views`, `components`, `features`,
  `cross_cutting_features`; the last id is structurally required and protected
  from whole-group deletion, while its internal content remains editable.

### Proposal presentation and traceability contracts

- `next_steps.content_json` has two public consumers. `steps` and `introMessage` feed the closed kickoff disclosure in `FinalNote`; `ctaMessage`, `primaryCTA`, `secondaryCTA` and `contactMethods` feed the synthetic `ProposalClosing` panel. Do not restore a standalone `next_steps` panel or duplicate these blocks.
- Proposal descriptions may contain limited emphasis. Render them through `useLinkify.linkify`, whose whitelist preserves safe `<b>/<strong>/<i>/<em>/<br>` tags and escapes all other HTML; do not introduce raw `v-html` paths.
- Lead-copy generation is a field-level contract, not a generic style suggestion. `useSellerPrompt` and `_seller_prompt.bold_formatting` must both enumerate the same 14 JSON paths and require one or two short `<b>` fragments per non-empty value; empty optional fields remain empty and Markdown `**` is forbidden.
- Responsive acceptance is based on usable inner width. `FinalNote` switches to two columns at `xl` and keeps each column above 520 px at a 1366 px viewport; investment payment rows allow the label to wrap but apply `shrink-0 whitespace-nowrap tabular-nums` to the amount so the tax suffix remains attached.
- `buildProposalItemLinkOptions()` marks each commercial item as required, optional or ignored from its real group visibility/selection. `buildTechnicalItemCoverage()` compares those ids against technical `linked_item_ids`; the technical editor refuses to emit `save` while required gaps remain.
- Public requirement cards receive `itemRequirementsMap` in detailed and executive modes. A base item is never filtered merely because it has no calculator selection; only uncontracted optional-module requirements are removed.
- The commercial prompt treats `cross_cutting_features` as a contextual starter
  catalog, distinguishes it from project-specific behavior and forbids unsupported
  compliance/performance promises. The technical prompt requires an epic with the
  exact same id and links every retained commercial item through
  `linked_item_ids`; an extra technical-only cross-cutting epic may exist only at
  the end and may not duplicate the commercial card.
- Data migration `content.0222_cross_cutting_features` updates
  `ProposalDefaultConfig` and active draft functional-requirement snapshots only.
  It inserts after `features`, preserves a customized existing group, and moves
  the legacy responsive item with its stable id. Reverse is intentionally a
  no-op so contractual history is never reconstructed destructively.
- Commercial and technical generation prompts preserve scope discipline: requirement lifting, QA and deployment are distinct processes; warranty text comes from contractual context; analytics is never inferred; institutional users/roles/admin are not invented; requirements should normally fit a 1–3 point story and external feeds should model source, ingestion, resource version, health, cache/retention and last-valid-data semantics separately.

### Contract terms are global proposal metadata, not section JSON
- `BusinessProposal.show_contract_terms` is a Boolean visibility flag and defaults to `True`; the public mode additionally requires `language='es'` and an active proposal.
- The legal reader is built from two synthetic frontend panels and `ContractTermsService`, not from a `ProposalSection`. Creation/import/update pass the flag as top-level metadata, leaving AI prompts and the 18-section JSON contract unchanged.
- `ContractTermsOverview` uses the same `max-w-5xl` content column for its introduction and clause index. It owns no proposal identifier or download URL; legal-mode downloads stay centralized in the page-level floating `PdfDownloadButton`.
- `ContractTermsDocument` groups its header, states, preamble and clauses under one `role="document"` paper surface. Border, front sheet, decorative back sheet and shadows use semantic theme tokens; anchors and lazy-loading behavior stay unchanged.
- `GET /api/proposals/<uuid>/contract-terms/` parses the current default contract Markdown into stable `clause-NN` anchors. `GET /api/proposals/<uuid>/contract/draft-pdf/` forces that same default template even if the proposal has custom contract Markdown.
- Both public endpoints use draft masking; the PDF omits the contractor signature image and carries the `BORRADOR` watermark. Responses are `no-store` because the global template can change independently from the proposal.

### API Proxy in Development
- Nuxt dev server proxies `/api`, `/admin`, `/static`, `/media` to Django at `127.0.0.1:8000`
- Configured in `nuxt.config.ts` → `nitro.devProxy`

### Production: Django Serves Everything
- Nuxt builds to `backend/static/frontend/` via `npm run build:django`
- Django's `serve_nuxt` catch-all view serves pre-rendered pages
- Assets served via `STATIC_URL` backed by Nginx
- CDN URL configurable via `NUXT_APP_CDN_URL`

---

## 5. Design Patterns

### Backend Patterns

- **Function-based views** (`@api_view`) — all DRF views are FBV, not class-based
- **Service layer** — business logic in `content/services/` (47 modules: ProposalService, ProposalEmailService, ProposalPdfService, ProposalStageTracker, ContractPdfService, EmailTemplateRegistry, PdfUtils, DocumentPdfService, MarkdownParser, CollectionAccountService, CollectionAccountPdfService, TechnicalDocumentPdf, TechnicalDocumentFilter, PlatformOnboardingPdf, DiagnosticService, DiagnosticEmailService, DiagnosticPdfService, DiagnosticDocumentsService, AccountingService, AccountingExportService, AccountingEmailService, AccountingCardReminderService, plus the `content/mcp/` tool package) and in `accounts/services/` (19 modules: archive, client_flow_notifications, credential_cipher, hosting_billing, image_utils, impersonation, notifications, onboarding, password_reset, payment_history, payment_notifications, project_phases, proposal_client_service, proposal_platform_onboarding, technical_requirements_sync, tokens, verification, wompi). Services are class-based with `@classmethod` static methods (matching `ProposalEmailService`), or function modules for stateless flows. `proposal_client_service` is the silent variant of `accounts/services/onboarding.create_client` — same User+UserProfile shape but **never sends invitation emails**, so the proposal admin panel can create/reuse clients without triggering platform onboarding.
- **Model layer** — thin models with properties (`is_expired`, `days_remaining`, `public_url`)
- **Huey tasks** — async operations: reminders, expiration, engagement-based emails, project-stage deadline scans, hosting recurring billing (`accounts/tasks.py::auto_charge_due_subscriptions` — daily 06:00 UTC, charges due hosting payments with the subscription's stored Wompi payment source)
- **Custom admin site** — `content/admin.py` with custom `AdminSite` class; `accounts/admin.py` registers `ProjectAdmin` (URLs + encrypted credentials)
- **Management commands** — fake data generation for development/testing
- **Email template registry** — centralized email content management with admin-editable overrides
- **Fernet encryption** — `accounts/services/credential_cipher.py`; `encrypt_password`/`decrypt_password` with key from `PROJECT_ACCESS_CIPHER_KEY`; `@lru_cache` on cipher instance
- **Bogotá time helpers** (`content/utils.py`) — `now_bogota()`, `today_bogota()`, `to_bogota_date(dt)`, `format_bogota_date(d)` (accepts both `date` and `datetime`), `format_bogota_datetime(dt)`. Use these for any day-level arithmetic instead of `date.today()` (UTC). Bogotá is fixed UTC-5 with no DST.
- **Internal-only fields gated by `is_admin`** — when a model is internal-only (e.g., `ProposalProjectStage`), expose it via `SerializerMethodField` returning `[]` for non-admin context, never `read_only=True` model nesting. Precedent: `ProposalDetailSerializer.get_project_stages`.
- **Gateway baseline history for every outbound message** — client, internal and
  security traffic gets a primary `EmailLog` row at the transport boundary.
  Domain-specific `_log_email` calls enrich that row through the shared delivery
  trace instead of creating a duplicate.
- **Global accounting presentation preferences** — `AccountingSettings` owns the collection-account view (`grouped`/`classic`) and one grouping criterion (`client`/`project`). They travel through the existing settings serializer/API and audit labels; migration `content.0213` defaults existing installations to grouped-by-client without changing collection-account rows.
- **Generated-document paths are keyed, not name-matched** —
  `generated_document_filing_service` builds each level from a stable nullable
  `DocumentFolder.system_key`, then reconciles parent, name, owner and archive
  flags inside a transaction. Human-readable project/client names may change;
  identity and concurrency safety do not depend on them.
- **One render, one retained proposal version** — proposal send/resend/multi-send
  calls `proposal_snapshot_service` before SMTP. It locks source proposals,
  allocates `source_version`, renders all PDFs before writing any Document,
  stores a SHA-256 plus `generated_file`, and passes those in-memory bytes to
  `ProposalEmailService`. A generated file, rather than the nullable source FK,
  is the immutable marker so deleting a proposal cannot make its archive editable.
- **Generated branches are server-owned** — REST serializers/views, folder
  endpoints and the Documents MCP reject manual targets or structural mutations
  with an explicit conflict. The list sorts a selected generated folder by
  case-insensitive title; collection accounts expose a derived lifecycle/email
  state instead of workflow episodes.
- **Backfill deployment order** — apply schema migrations first, preview with
  `python manage.py backfill_collection_account_filing`, review its paths, then
  run the same command with `--apply`. It only considers folderless collection
  accounts, preserves manual classification and skips missing issue dates. Never
  run either migrations or this data-writing command from a session worktree.

### Frontend Patterns

- **Pinia Options API** — all stores use Options API (state, getters, actions), not Composition API
- **Disabled-control contract** — pass `disabledReason` for semantic locks and
  `loading` for transient work. If the operator can satisfy prerequisites, wrap
  the control in `BaseControlGate` with the complete reasons array so the same
  explanation is visible, keyboard/touch reachable and linked by
  `aria-describedby`. `frontend/scripts/check-disabled-controls.mjs --strict`
  scans panel pages and reachable shared components in CI; do not suppress it
  unless equivalent adjacent copy owns the explanation.
- **Pinia in-place mutation** — store helpers that update nested arrays must mutate in place by index (`this.currentProposal.sections[idx] = response.data`), never spread + reassign the parent. Components reading via `computed(() => store.currentProposal)` don't reliably pick up the spread+reassign combination but DO pick up in-place index assignments. See `_mergeProjectStage` / `updateSection` / `applySync` / `reorderSections` in `frontend/stores/proposals.js`.
- **One responsive DOM branch** — use a viewport composable for structural swaps (`v-if` drawer/cards vs table/two-zone layout) and Tailwind for local reflow. Never render desktop and compact action controls simultaneously behind CSS; duplicated controls confuse focus order, accessible names and E2E selectors.
- **Indicator-card contract** — use `BaseIndicatorCard` for label/value/support
  KPI surfaces. Always supply consistent help and an explicit action; group
  lifecycle and operational questions separately, preserve catalog order, and
  use two drawer-backed summaries when the complete card set would push the
  first result below the initial compact viewport.
- **Touch parity** — row actions use a 44 px minimum target and bottom action drawer; any drag/hover behavior must have an explicit click path. Client proposal/diagnostic reassignment and document folder operations are the reference implementations.
- **Action tooltip/accessibility split** — `BaseActionButton` is the sole tooltip
  owner for an icon-only panel action. Its visual copy defaults to the short
  action-catalog label (for example, **Acciones**), while `label` remains the
  contextual `aria-label` (for example, **Acciones de Contrato**). It passes
  `nativeTitle=false` to `BaseButton`, which filters the fallthrough `title`
  attribute without dropping `aria-*`, `data-*` or link attributes. Do not add a
  second `title` to a consumer; use the explicit `tooltip` prop only when the
  short visual copy genuinely differs from the catalog.
- **Leading kebab control track** — tables with a single three-dot menu use
  `rowActionsLayout="menu-start"`: selection remains first when present, then a
  fixed 56 px actions track with an empty visual header, then identity/content.
  The control cell stops row-navigation clicks but leaves touch/pointer movement
  unhandled so the table wrapper can still pan horizontally. Loose icon rows are
  a separate migration decision and remain `inline-end` until consolidated.
- **Measured overflow, intrinsic containment and table widths** — use
  `BaseOverflowText` for one clipped-only floating `BaseTooltip` plus in-place
  touch disclosure; consumer classes may style typography but must not override
  its display/clamp state. The primitive remeasures after
  `document.fonts.ready`. Floating tooltips
  teleport to `body`, flip/clamp to the viewport and update on scroll/resize.
  `BaseActionButton` consumes the same primitive and suppresses
  `BaseButton.nativeTitle` to avoid duplicate notices.
  `frontend/utils/tableLayout.js` assigns every value `wrap`, `truncate` or
  `atomic`: user/API strings default to `min-w-0` + bounded width +
  `overflow-wrap:anywhere`, truncation requires another full-value path, and only
  bounded money/date/number fields stay nowrap. `BaseResponsiveTable` and
  `BaseExploratoryList` apply that policy to table, grouped-detail and card
  representations. Resizable tables declare `columnWidth` for every track and a
  stable `columnWidthsKey`, then delegate pointer/keyboard/reset behavior to
  `BaseResizeHandle` and allocation/persistence to `useResizableTableColumns`.
  Fixed tracks never donate; ordered flexible tracks reach their minima before
  internal table scroll. Documentos keeps its content-backed Título range at
  240–520 px (320 px default); the 520 px cap covers the current 56-character
  production boundary with cell padding and safety.
- **Composables** — 70 composables for shared logic (`useExpirationTimer`, `useProposalNavigation`, `useProposalTracking`, `useSectionAnimations`, `usePlatformApi`, `usePlatformSidebar`, `usePlatformTheme`, `useMarkdownPreview`, `usePlatformCustomTheme`, `useTechnicalPrompt`, `useSellerPrompt`, `usePlatformIncludeArchived`, `useFreeResources`, `useProposalFilters`, `useAccountingFilters`, `useResizableTableColumns`, `usePanelViewportProfile`, etc.)
- **Component architecture** — 377 `.vue` components (387 files) under `frontend/components/`; admin-only proposal components live under `components/BusinessProposal/admin/` (e.g., `ProjectScheduleEditor.vue`, `ProposalEmailsTab.vue`, `ProposalDocumentsTab.vue`); quick-access micro-components under `components/platform/access/` (`CopyField.vue`, `UrlRow.vue`)
- **GSAP animations** — horizontal scroll with ScrollTrigger for proposal client view, reveal animations for marketing pages
- **Layouts** — `default.vue` (public pages with navbar), `admin.vue` (admin panel with sidebar), `platform.vue` (platform with sidebar + theme)
- **Middleware** — `admin-auth.js` route guard for `/panel/**` routes, `platform-auth.js` route guard for `/platform/**` routes
- **Panel responsive contract** — import breakpoints/media/reference devices
  from `frontend/config/responsive.js`; use the `panel-*` Tailwind screens and
  shared base primitives instead of local `window.innerWidth` thresholds.
  Acceptance runs at 412×915, 835×1195, 1195×835, 1440×900 and 2560×1440;
  general content is capped at 1400 px and touch actions expose at least 44 px targets.
  Full decisions and the adoption inventory are in
  `docs/RESPONSIVE_STANDARD.md`.
- **Accounting responsive acceptance** — the twelve accounting routes use
  business-declared table/KPI priorities rather than positional hiding. The
  Pocket route is the structural exception below `PANEL_BREAKPOINTS.portrait`:
  `useIsMobile` renders exactly one `PocketMovementCards` branch with concept,
  signed amount and labelled facts, while the shared priority table returns at
  640 px. Both branches reuse `PocketMovementRowActionsButton` and
  `PocketMovementActionsModal`; Incomes and Collection Accounts use the same
  `menu-start` contract in classic and grouped modes. `BaseBadge` owns atomic
  direction/link/status text. `withRunningBalance` remains filter-first, so cards
  say **Acumulado filtrado** when filters are active while the headline balance
  continues to describe the complete ledger. The
  executable representative checks live in
  `frontend/e2e/admin/admin-accounting-pocket-recurring.spec.js`; the complete
  repeatable 60-cell route/viewport matrix and long-modal scenarios are in
  `docs/ACCOUNTING_RESPONSIVE_TEST_SCRIPT.md`.
- **Collection-account aggregation** — keep grouping, ordering and money/status
  semantics in `frontend/utils/collectionAccounts.js`; pages provide rows and
  controls, while `IncomeGroupedTable` and `AccountingGroupSummaryBand` own the
  shared visual contract. Do not duplicate overdue or amount rules in templates.
  `useCollectionAccountsViewPreferences` treats both settings as one save unit and
  rolls back an optimistic change on API failure.

---

## 6. Testing Strategy

### Backend (pytest)

- Location: `backend/content/tests/`, `backend/accounts/tests/`, `backend/tests/`
- Structure: `models/`, `serializers/`, `views/`, `services/`, `tasks/`, `utils/`, `management/`
- Test files: **255 total** (content 184, accounts 67, root/project 4)
- Fixtures: `conftest.py` at root and `content/tests/conftest.py` (provides `proposal`, `accepted_proposal`, `admin_user`, `admin_client`, etc.)
- Coverage: custom terminal report with per-file bars and Top-N focus
- Coverage floor: CI enforces `--cov-fail-under=92.5` on the full-suite run (ci.yml); local slices keep using `--no-cov`, unaffected. Raise the floor as coverage grows, never lower it.
- Config: `backend/pytest.ini`
- Run: `cd backend && source venv/bin/activate && pytest path/to/test_file.py -v --no-cov` (the venv lives at `backend/venv`, not repo-root `.venv`)

### Frontend Unit (Jest)

- Location: `frontend/test/`
- Structure: `components/`, `composables/`, `stores/` (incl. services), `utils/`
- Test files: **368 total** (267 `.test.js` + 101 `.spec.js`)
- Config: `frontend/jest.config.cjs`
- Coverage floors: enforced by the ci.yml "Enforce frontend coverage floors" step (statements ≥85%, branches ≥81% over `coverage-summary.json`) — NOT via jest `coverageThreshold`, because the CI jest step swallows exit codes with `|| true`.
- Run: `npm test -- test/<specific_file>.test.js`

### Frontend E2E (Playwright)

- Location: `frontend/e2e/`
- Structure: `admin/`, `auth/`, `blog/`, `layout/`, `platform/`, `proposal/`, `public/`, `visual/`
- Spec files: **216 total**
- Flow definitions: one source shard per flow in `frontend/e2e/flows/*.json` (must be updated for every new flow)
- Flow tags and `docs/USER_FLOW_MAP.md` are generated from shards/docs with `python3 scripts/generate_flow_registry.py --repo-root .`; never edit either aggregate by hand
- Config: `frontend/playwright.config.js`
- Helpers: `frontend/e2e/helpers/`
- Run: `npx playwright test e2e/<specific_file>.spec.js` (max 2 files per invocation)
- Reuse running dev server: `E2E_REUSE_SERVER=1 npx playwright test ...`

### Quality Gate

- Script: `scripts/test_quality_gate.py`
- Analyzers: `scripts/quality/` (backend_analyzer, frontend_analyzer, e2e_analyzer, etc.)
- CI: Runs after all test suites pass
- Command: `python3 scripts/test_quality_gate.py --repo-root . --external-lint run --semantic-rules strict --verbose`

---

## 7. CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`):

| Job | Runner | Description |
|-----|--------|-------------|
| `backend-tests` | ubuntu-latest | Python 3.12, pytest with SQLite |
| `frontend-unit-tests` | ubuntu-latest | Node 22, Jest |
| `frontend-e2e-tests` | ubuntu-latest × 5 shards | Node 22, Playwright chromium |
| `merge-e2e-reports` | ubuntu-latest | Merges Playwright blob reports into HTML |
| `test-quality-gate` | ubuntu-latest | Quality analysis after all tests pass |

Triggers: Push/PR to `main`/`master`. Concurrency group cancels in-progress runs.

---

## 8. Project Structure

```
projectapp/
├── backend/
│   ├── accounts/               # Platform app (auth, onboarding, projects, kanban, bug reports, changes, deliverables, notifications, payments, collection accounts, quick-access)
│   │   ├── models.py            # 24 models (UserProfile, VerificationCode, SavedFilterTab, Project, ProjectPhase, ProjectScopeItem, Requirement, RequirementComment, RequirementHistory, BugReport, BugComment, ChangeRequest, ChangeRequestComment, Deliverable, DeliverableVersion, DeliverableFile, DeliverableClientFolder, DeliverableClientUpload, DataModelEntity, ProjectDataModelEntity, Notification, HostingSubscription, Payment, PaymentHistory)
│   │   ├── admin.py             # ProjectAdmin — URL + encrypted credential fields
│   │   ├── services/            # 19 service modules (archive, client_flow_notifications, credential_cipher, hosting_billing, image_utils, impersonation, notifications, onboarding, password_reset, payment_history, payment_notifications, project_phases, proposal_client_service, proposal_platform_onboarding, technical_requirements_sync, tokens, verification, wompi)
│   │   ├── management/commands/ # 6 commands (create_platform_admin, seed_demo_clients, seed_platform_data, seed_mihuella, …)
│   │   ├── document_views.py    # Client document portal (list/retrieve/pdf/sign) + email OTP verify (request/confirm)
│   │   ├── tests/               # 67 test files
│   │   └── urls.py              # 94 URL patterns
│   ├── content/                 # Main Django app
│   │   ├── models/              # 56 model files (business_proposal, proposal_section, blog, portfolio, contact, document, email, diagnostic, accounting_base/income_record/expense_record/credit_card/credit_card_statement/…, task, mcp_connector, mcp_request_log, linkedin_token, etc.)
│   │   ├── serializers/         # DRF serializers (proposal, blog, portfolio, contact, proposal_clients, diagnostic, accounting, document, mcp)
│   │   ├── views/               # 19 FBV modules (proposal is dominant; blog, portfolio, diagnostic, diagnostic_template, accounting, accounting_export, document*, email_templates, standalone_email, task, mcp_blog, contact, proposal_clients)
│   │   ├── mcp/                 # MCP protocol, actor, field contracts + nine module catalogs (including communications and LinkedIn)
│   │   ├── services/            # 30 service/support modules (proposal_*, contract_pdf_service, document_pdf_service, markdown_parser, linkedin_service, collection_account*, technical_document*, document_type_*, platform_onboarding_pdf, diagnostic_* (service/email/pdf/documents), accounting_* (service/export/email/card_reminder))
│   │   ├── tasks.py             # Huey async tasks (incl. notify_proposal_stage_deadlines daily 13:30 UTC = 08:30 Bogotá; send_card_debt_reminder Fridays)
│   │   ├── templates/emails/    # 73 content email templates (37 HTML + 36 TXT)
│   │   ├── migrations/          # 163 migrations (latest: 0164_pocket_draws_to_company_ledger.py)
│   │   ├── management/commands/ # 21 management commands
│   │   ├── tests/               # 184 test files (models, serializers, views, services, tasks, utils)
│   │   └── urls.py              # 284 URL patterns
│   ├── projectapp/              # Django project (settings, urls, wsgi, views, 1 test file)
│   ├── tests/                   # Root-level tests (test_document_pdf_service.py, test_markdown_parser.py)
│   ├── static/                  # Static files (Nuxt build output in prod)
│   └── media/                   # User uploads
├── frontend/
│   ├── pages/                   # Nuxt file-based routing (96 pages)
│   │   ├── panel/               # Admin pages (proposals, diagnostics, blog, portfolio, clients, documents, admins, tasks, accounting/*, mcps, defaults, styleguide, views). Proposal edit page has Cronograma tab; `/panel/tasks` is the internal Kanban board; `/panel/accounting/*` and `/panel/mcps` are superuser-gated.
│   │   ├── platform/            # Platform pages (login/verify/complete-profile, projects/*, board, bugs, changes, deliverables, collection-accounts, data-model, payments, notifications, clients, profile, documents — client document-signing portal)
│   │   ├── blog/                # Blog listing + detail
│   │   ├── portfolio-works/     # Portfolio listing + detail
│   │   └── proposal/            # Client proposal view
│   ├── components/              # Vue components (299 .vue files)
│   │   ├── BusinessProposal/    # 50 proposal component/source files. Admin-only under `admin/` (incl. `ProjectScheduleEditor.vue`)
│   │   ├── platform/access/     # CopyField.vue, UrlRow.vue — quick-access micro-components
│   │   └── Tasks/               # TaskCard.vue, TaskColumn.vue (vuedraggable), TaskFormModal.vue — internal Kanban board
│   ├── stores/                  # Pinia Options-API stores, including documents, document_folders and the administrable document_states workflow catalog; platform stores remain isolated behind usePlatformApi
│   ├── composables/             # 59 composables (incl. useStageStatus.js)
│   ├── e2e/                     # Playwright E2E tests (216 spec files)
│   ├── test/                    # Jest unit tests (368 test files)
│   ├── layouts/                 # default.vue, admin.vue, platform.vue
│   ├── middleware/              # admin-auth.js, platform-auth.js
│   ├── plugins/                 # 4 plugins (gsap, geo-locale, language-sync, cal-booking)
│   ├── locales/                 # i18n translation files
│   └── i18n/                    # i18n config
├── docs/                        # Documentation and standards
├── scripts/                     # Quality gate, nginx, systemd configs
└── tasks/                       # Task planning and active context
```

---

## 9. Technical Constraints

0. **Panel action icon catalog** — operational glyphs under `/panel/**` use `@heroicons/vue/24/outline` through the shared action catalog. Interactive consumers must not embed action SVG paths or emojis; icon-only controls use the shared action button so accessible naming, tooltip behavior and the coarse-pointer 44 px target stay aligned.
1. **Dual auth** — `content`/`panel` uses session/CSRF; `accounts`/`platform` uses JWT (SimpleJWT); never mix the two HTTP clients (`request_http` vs `usePlatformApi`)
2. **Two Django apps** — `content` (proposals, blog, portfolio, documents, contracts) + `accounts` (platform users, projects, deliverables, data models, quick-access)
3. **GoDaddy SMTP** — email delivery limited by provider (port 465 SSL only)
4. **Redis required** — for Huey task queue (even if immediate mode in dev)
5. **Nuxt builds to Django static** — production frontend is pre-rendered and served by Django, not a separate server
6. **Large service files** — `proposal_service.py`, `proposal_pdf_service.py`, `proposal_email_service.py`, and `pdf_utils.py` remain large and would benefit from further splitting
7. **Bogotá timezone for day-level arithmetic** — Django's `TIME_ZONE='UTC'` means `date.today()` returns UTC date. For day-level logic (e.g., the daily Huey task computing "is the stage overdue today?") always use `today_bogota()` from `content/utils.py`. Bogotá is fixed UTC-5 with no DST so the offset is stable year-round.
8. **Huey cron schedule is in UTC** — `crontab(hour='13', minute='30')` means 13:30 UTC = 08:30 Bogotá. Document the offset in a comment above any periodic task that's meant to land in the team inbox at a specific local time.
9. **`PROJECT_ACCESS_CIPHER_KEY` required** — must be set in production `.env`; generate with Fernet before first deploy of quick-access feature
10. **Modal search results use the shared floating layer** — searchable listboxes
    inside `BaseModal` render through `BaseFloatingListbox`; consumers must pass
    their anchor and owner elements instead of positioning a results panel inside
    a clipped container. The primitive owns viewport clamping, above/below
    placement, outside-click and Escape behavior, list scrolling and modal focus
    containment.
11. **Panel flows never use browser-native dialogs** — confirmation and text input
    stay inside application-owned modal primitives; errors remain inline or in the
    panel notification system. The static guard is mandatory in CI.
12. **Deleted observations are recoverable but inactive** — every active queryset,
    count and prefetched episode filters `deleted_at IS NULL`; restoration must pass
    state compatibility in the same transaction before clearing the tombstone.
