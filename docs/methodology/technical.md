# Technical Documentation — ProjectApp

## 1. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend Framework** | Django | 5.2.13 |
| **REST API** | Django REST Framework | 3.17.1 |
| **JWT (platform)** | djangorestframework-simplejwt | >=5.3,<6.0 |
| **Frontend Framework** | Nuxt 3 | ^3.21.4 |
| **Vue** | Vue 3 | ^3.5.33 |
| **State Management** | Pinia (Options API) | ^2.3.1 |
| **CSS Framework** | TailwindCSS | ^6.14.0 (@nuxtjs/tailwindcss) |
| **Animations** | GSAP + ScrollTrigger + ScrollToPlugin | ^3.13.0 |
| **i18n** | @nuxtjs/i18n | ^9.1.0 |
| **Task Queue** | Huey (RedisHuey) | >=2.5.0 |
| **Cache/Queue Backend** | Redis | >=4.0.0 |
| **Database (prod)** | MySQL 8+ | via mysqlclient >=2.2 |
| **Database (dev)** | SQLite 3 | built-in |
| **HTTP Client** | Axios | ^1.15.2 |
| **PDF Generation** | ReportLab + pypdf | ^4.0 |
| **Image Processing** | Pillow | 10.3.0 |
| **Email** | Django EmailMultiAlternatives | SMTP (GoDaddy) |
| **WhatsApp** | CallMeBot API | via requests |
| **Testing (backend)** | pytest + pytest-django + pytest-cov | 8.3.2 |
| **Testing (frontend unit)** | Jest + @vue/test-utils | ^29.7.0 |
| **Testing (E2E)** | Playwright | ^1.59.1 |
| **Linter** | Ruff | via ruff.toml |
| **Pre-commit** | pre-commit | .pre-commit-config.yaml |
| **CI/CD** | GitHub Actions | ci.yml |
| **Server (prod)** | Gunicorn + Nginx | >=23.0 |
| **Process Manager** | systemd | 3 services |
| **Backups** | django-dbbackup | >=4.0.0 |
| **Profiling** | django-silk (optional) | >=5.0.0 |
| **Config Management** | python-decouple | >=3.8,<3.9 |
| **Fake Data** | Faker | 28.4.1 |
| **Token Encryption** | cryptography (Fernet) | >=42,<46 | LinkedIn OAuth token + Project admin credential encryption |

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

### Codex Runtime Surfaces (ProjectApp)

- Always-on instructions:
  - `AGENTS.md`
  - `backend/AGENTS.md`
  - `frontend/AGENTS.md`
- Native repo skills: 33 directories under `.agents/skills/` (incl. `backend-test-coverage`, `client-report`, `debug`, `e2e-user-flows-check`, `fix-broken-tests`, `frontend-e2e-test-coverage`, `frontend-unit-test-coverage`, `git-sync`, `human`, `implement`, `methodology-setup`, `new-feature-checklist`, `plan`, `requirement-calculator`, `test-quality-gate`, `user-walkthrough`, `view-map-audit`, `vuln-audit`, plus accounting/MCP-related helpers). The parallel `.claude/skills/` tree has 34 directories.
- Project config: `.codex/config.toml`
- Methodology guide: `docs/CODEX_METHODOLOGY_GUIDE.md`
- Setup & activation: `docs/CODEX_SETUP.md`
- Migration history: `docs/CODEX_MIGRATION_MAP.md`
- Compatibility surfaces: `CLAUDE.md`, `backend/CLAUDE.md`, `frontend/CLAUDE.md`, `.claude/`, `.windsurf/`
- Naming policy: `debug` is canonical; `debugme` remains as legacy alias

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
| `create_fake_data <N>` | Create N contacts + portfolio works + proposals + blog posts + seed tasks |
| `create_fake_proposals` | Create fake proposals with sections and requirements |
| `create_fake_blog_posts` | Create fake blog posts with structured JSON content |
| `create_contacts` | Create sample contact entries |
| `delete_fake_data` | Delete all fake data |
| `cleanup_in_calculator` | Clean up stale in-calculator proposal states |
| `update_hosting_specs` | Update hosting tier specifications |
| `zero_group_price_percent` | Reset group price percentages |
| `create_platform_admin` | Create a platform admin user |
| `seed_demo_clients` | Seed demo client users for platform |
| `seed_platform_data` | Seed full platform demo data (projects, requirements, etc.) |
| `seed_mihuella` | Seed specific demo data for mihuella project |

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

### Content Storage: Structured JSON
- Proposal sections, portfolio works, and blog posts store content as JSON fields
- Each proposal section's `content_json` matches the props schema of its Vue component
- Enables rich, structured content without a full CMS
- Blog supports dual format: structured JSON (preferred) with HTML fallback

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
- **Service layer** — business logic in `content/services/` (30 modules: ProposalService, ProposalEmailService, ProposalPdfService, ProposalStageTracker, ContractPdfService, EmailTemplateRegistry, PdfUtils, DocumentPdfService, MarkdownParser, CollectionAccountService, CollectionAccountPdfService, TechnicalDocumentPdf, TechnicalDocumentFilter, PlatformOnboardingPdf, DiagnosticService, DiagnosticEmailService, DiagnosticPdfService, DiagnosticDocumentsService, AccountingService, AccountingExportService, AccountingEmailService, AccountingCardReminderService, plus the `content/mcp/` tool package) and in `accounts/services/` (19 modules: archive, client_flow_notifications, credential_cipher, hosting_billing, image_utils, impersonation, notifications, onboarding, password_reset, payment_history, payment_notifications, project_phases, proposal_client_service, proposal_platform_onboarding, technical_requirements_sync, tokens, verification, wompi). Services are class-based with `@classmethod` static methods (matching `ProposalEmailService`), or function modules for stateless flows. `proposal_client_service` is the silent variant of `accounts/services/onboarding.create_client` — same User+UserProfile shape but **never sends invitation emails**, so the proposal admin panel can create/reuse clients without triggering platform onboarding.
- **Model layer** — thin models with properties (`is_expired`, `days_remaining`, `public_url`)
- **Huey tasks** — async operations: reminders, expiration, engagement-based emails, project-stage deadline scans, hosting recurring billing (`accounts/tasks.py::auto_charge_due_subscriptions` — daily 06:00 UTC, charges due hosting payments with the subscription's stored Wompi payment source)
- **Custom admin site** — `content/admin.py` with custom `AdminSite` class; `accounts/admin.py` registers `ProjectAdmin` (URLs + encrypted credentials)
- **Management commands** — fake data generation for development/testing
- **Email template registry** — centralized email content management with admin-editable overrides
- **Fernet encryption** — `accounts/services/credential_cipher.py`; `encrypt_password`/`decrypt_password` with key from `PROJECT_ACCESS_CIPHER_KEY`; `@lru_cache` on cipher instance
- **Bogotá time helpers** (`content/utils.py`) — `now_bogota()`, `today_bogota()`, `to_bogota_date(dt)`, `format_bogota_date(d)` (accepts both `date` and `datetime`), `format_bogota_datetime(dt)`. Use these for any day-level arithmetic instead of `date.today()` (UTC). Bogotá is fixed UTC-5 with no DST.
- **Internal-only fields gated by `is_admin`** — when a model is internal-only (e.g., `ProposalProjectStage`), expose it via `SerializerMethodField` returning `[]` for non-admin context, never `read_only=True` model nesting. Precedent: `ProposalDetailSerializer.get_project_stages`.
- **Internal team notifications skip `_log_email`** — `EmailLog` rows are reserved for client-facing single-recipient sends. Internal team alerts (`send_first_view_notification`, `send_stage_warning`, etc.) use `logger.info` only.

### Frontend Patterns

- **Pinia Options API** — all stores use Options API (state, getters, actions), not Composition API
- **Pinia in-place mutation** — store helpers that update nested arrays must mutate in place by index (`this.currentProposal.sections[idx] = response.data`), never spread + reassign the parent. Components reading via `computed(() => store.currentProposal)` don't reliably pick up the spread+reassign combination but DO pick up in-place index assignments. See `_mergeProjectStage` / `updateSection` / `applySync` / `reorderSections` in `frontend/stores/proposals.js`.
- **Composables** — 53 composables for shared logic (`useExpirationTimer`, `useProposalNavigation`, `useProposalTracking`, `useSectionAnimations`, `usePlatformApi`, `usePlatformSidebar`, `usePlatformTheme`, `useMarkdownPreview`, `usePlatformCustomTheme`, `useTechnicalPrompt`, `useSellerPrompt`, `usePlatformIncludeArchived`, `useFreeResources`, `useProposalFilters`, `useClientFilters`, `useSeoJsonLd`, `useIncludeArchivedQuery`, `useStageStatus`, etc.)
- **Component architecture** — 226 Vue component/source files under `frontend/components/`; 50 files under `components/BusinessProposal/`; admin-only proposal components live under `components/BusinessProposal/admin/` (e.g., `ProjectScheduleEditor.vue`, `ProposalEmailsTab.vue`, `ProposalDocumentsTab.vue`); quick-access micro-components under `components/platform/access/` (`CopyField.vue`, `UrlRow.vue`)
- **GSAP animations** — horizontal scroll with ScrollTrigger for proposal client view, reveal animations for marketing pages
- **Layouts** — `default.vue` (public pages with navbar), `admin.vue` (admin panel with sidebar), `platform.vue` (platform with sidebar + theme)
- **Middleware** — `admin-auth.js` route guard for `/panel/**` routes, `platform-auth.js` route guard for `/platform/**` routes

---

## 6. Testing Strategy

### Backend (pytest)

- Location: `backend/content/tests/`, `backend/accounts/tests/`, `backend/tests/`
- Structure: `models/`, `serializers/`, `views/`, `services/`, `tasks/`, `utils/`, `management/`
- Test files: **199 total** (content 130, accounts 65, root/project 4)
- Fixtures: `conftest.py` at root and `content/tests/conftest.py` (provides `proposal`, `accepted_proposal`, `admin_user`, `admin_client`, etc.)
- Coverage: custom terminal report with per-file bars and Top-N focus
- Config: `backend/pytest.ini`
- Run: `source .venv/bin/activate && cd backend && pytest path/to/test_file.py -v --no-cov`

### Frontend Unit (Jest)

- Location: `frontend/test/`
- Structure: `components/`, `composables/`, `stores/` (incl. services), `utils/`
- Test files: **290 total**
- Config: `frontend/jest.config.cjs`
- Run: `npm test -- test/<specific_file>.test.js`

### Frontend E2E (Playwright)

- Location: `frontend/e2e/`
- Structure: `admin/`, `auth/`, `blog/`, `layout/`, `platform/`, `proposal/`, `public/`, `visual/`
- Spec files: **191 total**
- Flow definitions: `frontend/e2e/flow-definitions.json` (must be updated for every new flow)
- Flow tags: `frontend/e2e/helpers/flow-tags.js` (constants imported by spec files)
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
│   │   ├── tests/               # 65 test files
│   │   └── urls.py              # 93 URL patterns
│   ├── content/                 # Main Django app
│   │   ├── models/              # 50 model files (business_proposal, proposal_section, blog, portfolio, contact, document, email, diagnostic, accounting_base/income_record/expense_record/…, task, mcp_connector, mcp_request_log, linkedin_token, etc.)
│   │   ├── serializers/         # DRF serializers (proposal, blog, portfolio, contact, proposal_clients, diagnostic, accounting, document, mcp)
│   │   ├── views/               # 19 FBV modules (proposal is dominant; blog, portfolio, diagnostic, diagnostic_template, accounting, accounting_export, document*, email_templates, standalone_email, task, mcp_blog, contact, proposal_clients)
│   │   ├── mcp/                 # MCP tool package (protocol, actor, tools + blog/documents/proposals/diagnostics/clients/tasks/accounting connectors for claude.ai)
│   │   ├── services/            # 30 service/support modules (proposal_*, contract_pdf_service, document_pdf_service, markdown_parser, linkedin_service, collection_account*, technical_document*, document_type_*, platform_onboarding_pdf, diagnostic_* (service/email/pdf/documents), accounting_* (service/export/email/card_reminder))
│   │   ├── tasks.py             # Huey async tasks (incl. notify_proposal_stage_deadlines daily 13:30 UTC = 08:30 Bogotá; send_card_debt_reminder Fridays)
│   │   ├── templates/emails/    # 73 content email templates (37 HTML + 36 TXT)
│   │   ├── migrations/          # 136 migrations (latest: 0137_alter_businessproposal_automations_paused.py)
│   │   ├── management/commands/ # 21 management commands
│   │   ├── tests/               # 130 test files (models, serializers, views, services, tasks, utils)
│   │   └── urls.py              # 229 URL patterns
│   ├── projectapp/              # Django project (settings, urls, wsgi, views, 1 test file)
│   ├── tests/                   # Root-level tests (test_document_pdf_service.py, test_markdown_parser.py)
│   ├── static/                  # Static files (Nuxt build output in prod)
│   └── media/                   # User uploads
├── frontend/
│   ├── pages/                   # Nuxt file-based routing (90 pages)
│   │   ├── panel/               # Admin pages (proposals, diagnostics, blog, portfolio, clients, documents, admins, tasks, accounting/*, mcps, defaults, styleguide, views). Proposal edit page has Cronograma tab; `/panel/tasks` is the internal Kanban board; `/panel/accounting/*` and `/panel/mcps` are superuser-gated.
│   │   ├── platform/            # Platform pages (login/verify/complete-profile, projects/*, board, bugs, changes, deliverables, collection-accounts, data-model, payments, notifications, clients, profile, documents — client document-signing portal)
│   │   ├── blog/                # Blog listing + detail
│   │   ├── portfolio-works/     # Portfolio listing + detail
│   │   └── proposal/            # Client proposal view
│   ├── components/              # Vue components (226 files)
│   │   ├── BusinessProposal/    # 50 proposal component/source files. Admin-only under `admin/` (incl. `ProjectScheduleEditor.vue`)
│   │   ├── platform/access/     # CopyField.vue, UrlRow.vue — quick-access micro-components
│   │   └── Tasks/               # TaskCard.vue, TaskColumn.vue (vuedraggable), TaskFormModal.vue — internal Kanban board
│   ├── stores/                  # 31 Pinia stores (proposals, diagnostics, blog, portfolio_works, contacts, language, documents, document_folders, document_tags, tasks, emails, accounting, mcps, panel_admins, proposalClients, platform-auth, platform-clients, platform-projects, platform-requirements, platform-bug-reports, platform-change-requests, platform-deliverables, platform-notifications, platform-payments, platform-collection-accounts, platform-data-model, platform-documents)
│   ├── composables/             # 53 composables (incl. useStageStatus.js)
│   ├── e2e/                     # Playwright E2E tests (191 spec files)
│   ├── test/                    # Jest unit tests (290 test files)
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

1. **Dual auth** — `content`/`panel` uses session/CSRF; `accounts`/`platform` uses JWT (SimpleJWT); never mix the two HTTP clients (`request_http` vs `usePlatformApi`)
2. **Two Django apps** — `content` (proposals, blog, portfolio, documents, contracts) + `accounts` (platform users, projects, deliverables, data models, quick-access)
3. **GoDaddy SMTP** — email delivery limited by provider (port 465 SSL only)
4. **Redis required** — for Huey task queue (even if immediate mode in dev)
5. **Nuxt builds to Django static** — production frontend is pre-rendered and served by Django, not a separate server
6. **Large service files** — `proposal_service.py`, `proposal_pdf_service.py`, `proposal_email_service.py`, and `pdf_utils.py` remain large and would benefit from further splitting
7. **Bogotá timezone for day-level arithmetic** — Django's `TIME_ZONE='UTC'` means `date.today()` returns UTC date. For day-level logic (e.g., the daily Huey task computing "is the stage overdue today?") always use `today_bogota()` from `content/utils.py`. Bogotá is fixed UTC-5 with no DST so the offset is stable year-round.
8. **Huey cron schedule is in UTC** — `crontab(hour='13', minute='30')` means 13:30 UTC = 08:30 Bogotá. Document the offset in a comment above any periodic task that's meant to land in the team inbox at a specific local time.
9. **`PROJECT_ACCESS_CIPHER_KEY` required** — must be set in production `.env`; generate with Fernet before first deploy of quick-access feature
