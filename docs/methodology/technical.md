# Technical Documentation — ProjectApp

## 1. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend Framework** | Django | 5.0.6 |
| **REST API** | Django REST Framework | 3.15.1 |
| **Frontend Framework** | Nuxt 3 | ^3.14.0 |
| **Vue** | Vue 3 | ^3.4.21 |
| **State Management** | Pinia (Options API) | ^2.1.7 |
| **CSS Framework** | TailwindCSS | ^6.12.0 (@nuxtjs/tailwindcss) |
| **Animations** | GSAP + ScrollTrigger + ScrollToPlugin | ^3.13.0 |
| **i18n** | @nuxtjs/i18n | ^9.1.0 |
| **Task Queue** | Huey (RedisHuey) | >=2.5.0 |
| **Cache/Queue Backend** | Redis | >=4.0.0 |
| **Database (prod)** | MySQL 8+ | via mysqlclient >=2.2 |
| **Database (dev)** | SQLite 3 | built-in |
| **HTTP Client** | Axios | ^1.7.2 |
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
- Native repo skills: 17 directories under `.agents/skills/` (`backend-test-coverage`, `blog-ai-weekly`, `debug`, `debugme`, `deploy-and-check`, `e2e-user-flows-check`, `fix-broken-tests`, `frontend-e2e-test-coverage`, `frontend-unit-test-coverage`, `git-commit`, `git-sync`, `human`, `implement`, `methodology-setup`, `new-feature-checklist`, `plan`, `test-quality-gate`)
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
- **Service layer** — business logic in `content/services/` (ProposalService, ProposalEmailService, ProposalPdfService, ProposalStageTracker, ContractPdfService, EmailTemplateRegistry, PdfUtils, DocumentPdfService, MarkdownParser, CollectionAccountService, CollectionAccountPdfService, TechnicalDocumentPdf, TechnicalDocumentFilter, PlatformOnboardingPdf) and in `accounts/services/` (archive, credential_cipher, image_utils, notifications, onboarding, payment_history, proposal_client_service, proposal_platform_onboarding, technical_requirements_sync, tokens, verification, wompi). Services are class-based with `@classmethod` static methods (matching `ProposalEmailService`), or function modules for stateless flows. `proposal_client_service` is the silent variant of `accounts/services/onboarding.create_client` — same User+UserProfile shape but **never sends invitation emails**, so the proposal admin panel can create/reuse clients without triggering platform onboarding.
- **Model layer** — thin models with properties (`is_expired`, `days_remaining`, `public_url`)
- **Huey tasks** — async operations: reminders, expiration, engagement-based emails, project-stage deadline scans
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
- **Composables** — 35 composables for shared logic (`useExpirationTimer`, `useProposalNavigation`, `useProposalTracking`, `useSectionAnimations`, `usePlatformApi`, `usePlatformSidebar`, `usePlatformTheme`, `useMarkdownPreview`, `usePlatformCustomTheme`, `useTechnicalPrompt`, `useSellerPrompt`, `usePlatformIncludeArchived`, `useFreeResources`, `useProposalFilters`, `useClientFilters`, `useSeoJsonLd`, `useIncludeArchivedQuery`, `useStageStatus`, etc.)
- **Component architecture** — 122 Vue component/source files under `frontend/components/`; 50 files under `components/BusinessProposal/`; admin-only proposal components live under `components/BusinessProposal/admin/` (e.g., `ProjectScheduleEditor.vue`, `ProposalEmailsTab.vue`, `ProposalDocumentsTab.vue`); quick-access micro-components under `components/platform/access/` (`CopyField.vue`, `UrlRow.vue`)
- **GSAP animations** — horizontal scroll with ScrollTrigger for proposal client view, reveal animations for marketing pages
- **Layouts** — `default.vue` (public pages with navbar), `admin.vue` (admin panel with sidebar), `platform.vue` (platform with sidebar + theme)
- **Middleware** — `admin-auth.js` route guard for `/panel/**` routes, `platform-auth.js` route guard for `/platform/**` routes

---

## 6. Testing Strategy

### Backend (pytest)

- Location: `backend/content/tests/`, `backend/accounts/tests/`, `backend/tests/`
- Structure: `models/`, `serializers/`, `views/`, `services/`, `tasks/`, `utils/`, `management/`
- Test files: **124 total**
- Fixtures: `conftest.py` at root and `content/tests/conftest.py` (provides `proposal`, `accepted_proposal`, `admin_user`, `admin_client`, etc.)
- Coverage: custom terminal report with per-file bars and Top-N focus
- Config: `backend/pytest.ini`
- Run: `source .venv/bin/activate && cd backend && pytest path/to/test_file.py -v --no-cov`

### Frontend Unit (Jest)

- Location: `frontend/test/`
- Structure: `components/`, `composables/`, `stores/` (incl. services), `utils/`
- Test files: **77 total**
- Config: `frontend/jest.config.cjs`
- Run: `npm test -- test/<specific_file>.test.js`

### Frontend E2E (Playwright)

- Location: `frontend/e2e/`
- Structure: `admin/`, `auth/`, `blog/`, `layout/`, `platform/`, `proposal/`, `public/`
- Spec files: **131 total**
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
│   │   ├── models.py            # 21 models (UserProfile, VerificationCode, Project, Requirement, RequirementComment, RequirementHistory, BugReport, BugComment, ChangeRequest, ChangeRequestComment, Deliverable, DeliverableVersion, DeliverableFile, DeliverableClientFolder, DeliverableClientUpload, DataModelEntity, ProjectDataModelEntity, Notification, HostingSubscription, Payment, PaymentHistory)
│   │   ├── admin.py             # ProjectAdmin — URL + encrypted credential fields
│   │   ├── services/            # 12 service modules (archive, credential_cipher, image_utils, notifications, onboarding, payment_history, proposal_client_service, proposal_platform_onboarding, technical_requirements_sync, tokens, verification, wompi)
│   │   ├── management/commands/ # 4 commands (create_platform_admin, seed_demo_clients, seed_platform_data, seed_mihuella)
│   │   ├── tests/               # 28 test files
│   │   └── urls.py              # 65 URL patterns
│   ├── content/                 # Main Django app
│   │   ├── models/              # 29 model files (proposal, blog, portfolio, contact, document, email, contract, proposal_project_stage, task, etc.)
│   │   ├── serializers/         # DRF serializers (proposal, blog, portfolio, contact, proposal_clients)
│   │   ├── views/               # FBV views (proposal is the dominant module; blog, portfolio, email_templates, document, contact, and proposal_clients are split separately)
│   │   ├── services/            # 17 service/support modules (proposal_service, proposal_email_service, proposal_pdf_service, proposal_stage_tracker, email_template_registry, contract_pdf_service, document_pdf_service, markdown_parser, linkedin_service, collection_account*, technical_document*, document_type_*, platform_onboarding_pdf)
│   │   ├── tasks.py             # Huey async tasks (incl. notify_proposal_stage_deadlines daily at 13:30 UTC = 08:30 Bogotá)
│   │   ├── templates/emails/    # 54 content email templates (27 HTML + 27 TXT)
│   │   ├── migrations/          # 87 migrations (latest: 0087_task.py)
│   │   ├── management/commands/ # 8 management commands
│   │   ├── tests/               # 61 test files (models, serializers, views, services, tasks, utils)
│   │   └── urls.py              # 128 URL patterns
│   ├── projectapp/              # Django project (settings, urls, wsgi, views, 1 test file)
│   ├── tests/                   # Root-level tests (test_document_pdf_service.py, test_markdown_parser.py)
│   ├── static/                  # Static files (Nuxt build output in prod)
│   └── media/                   # User uploads
├── frontend/
│   ├── pages/                   # Nuxt file-based routing (64 pages)
│   │   ├── panel/               # Admin pages (proposals, blog, portfolio, clients, documents, admins, tareas). Proposal edit page has Cronograma tab. `/panel/tareas` is the internal Kanban board.
│   │   ├── platform/            # Platform pages (dashboard, board, projects, kanban, bugs, changes, deliverables, notifications, payments, clients, collection-accounts, profile, data-model, access)
│   │   ├── blog/                # Blog listing + detail
│   │   ├── portfolio-works/     # Portfolio listing + detail
│   │   └── proposal/            # Client proposal view
│   ├── components/              # Vue components (130 files)
│   │   ├── BusinessProposal/    # 50 proposal component/source files. Admin-only under `admin/` (incl. `ProjectScheduleEditor.vue`)
│   │   ├── platform/access/     # CopyField.vue, UrlRow.vue — quick-access micro-components
│   │   └── Tasks/               # TaskCard.vue, TaskColumn.vue (vuedraggable), TaskFormModal.vue — internal Kanban board
│   ├── stores/                  # 23 Pinia stores (proposals, blog, portfolio_works, contacts, language, documents, document_folders, document_tags, tasks, emails, panel_admins, proposalClients, platform-auth, platform-clients, platform-projects, platform-requirements, platform-bug-reports, platform-change-requests, platform-deliverables, platform-notifications, platform-payments, platform-collection-accounts, platform-data-model)
│   ├── composables/             # 35 composables (incl. useStageStatus.js)
│   ├── e2e/                     # Playwright E2E tests (129 spec files)
│   ├── test/                    # Jest unit tests (73 test files)
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
10. **Folder hierarchy depth cap** — `content.models.document_folder.MAX_FOLDER_DEPTH = 5`. Enforced in `DocumentFolder.clean()` and in `DocumentFolderSerializer.validate()` (which also rejects self-parent and cycle: `parent ∈ self.get_descendant_ids()`). The serializer is reused by the dedicated `move_document_folder` view so the same rules apply to reparenting via drag-and-drop. The DB FK is `on_delete=PROTECT` because the delete view already blocks-with-409 on non-empty subtrees.
11. **Tree context pattern** — for hierarchical reads that need `path`, `depth`, and recursive aggregates per node, do **not** rely on `WITH RECURSIVE` SQL or N+1 lookups. `backend/content/views/document_folder.py:_build_tree_context()` is the canonical pattern: one annotated query (`annotate(_direct_count=Count('documents'))`) + Python DFS to populate `folder_by_id`, `children_map`, `direct_counts`, `recursive_counts`; the maps are passed via `serializer.context` and the serializer's `SerializerMethodField`s resolve in O(1) per node. Acceptable because depth is bounded (max 5) and folder count is small.

---

## 10. Claude Code Hooks (`.claude/settings.json`)

Two hooks are wired so the agent receives context and reminders automatically:

| Event | Command (timeout) | Purpose |
|-------|---|---|
| `SessionStart` | `timeout 20 bash /home/ryzepeck/webapps/ops/vps/scripts/maintenance/session-start-git-status.sh` | Read-only `git fetch` + status across all tracked repos; injects `behind=N ahead=N dirty=N` per repo so the agent can decide whether to invoke the `git-sync` skill before editing. The agent **must not** use `git pull --force`, `git reset --hard`, or auto-stash to resolve drift — only the `git-sync` skill, which rebases against the parent branch and walks the operator through any conflicts. |
| `Stop` | `timeout 10 bash /home/ryzepeck/webapps/ops/vps/scripts/maintenance/stop-check-user-flows.sh` | Checks for uncommitted changes under `frontend/src/`, `frontend/app/`, `frontend/pages/`, or `frontend/components/` and, if found, surfaces a reminder to run the `e2e-user-flows-check` skill before claiming the task complete. Non-blocking; the rule in `CLAUDE.md` § "E2E User Flows Check" applies regardless. |

Both hooks are wrapped in `|| true` so a failed script never blocks the session. The scripts themselves live outside the project tree (under the shared `ops/vps/scripts/maintenance/` toolkit) so they can be reused across every project on this VPS.
