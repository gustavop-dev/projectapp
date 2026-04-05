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
| **Testing (E2E)** | Playwright | ^1.58.2 |
| **Linter** | Ruff | via ruff.toml |
| **Pre-commit** | pre-commit | .pre-commit-config.yaml |
| **CI/CD** | GitHub Actions | ci.yml |
| **Server (prod)** | Gunicorn + Nginx | >=23.0 |
| **Process Manager** | systemd | 3 services |
| **Backups** | django-dbbackup | >=4.0.0 |
| **Profiling** | django-silk (optional) | >=5.0.0 |
| **Config Management** | python-decouple | >=3.8,<3.9 |
| **Fake Data** | Faker | 28.4.1 |
| **Token Encryption** | cryptography (Fernet) | via cryptography | LinkedIn OAuth token encryption |

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
| `create_fake_data <N>` | Create N contacts + portfolio works + proposals + blog posts |
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
| `ENABLE_SILK` | `false` | Enable query profiler |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `http://127.0.0.1:5173,...` | CORS origins |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://127.0.0.1:5173,...` | CSRF trusted |

---

## 4. Key Technical Decisions

### Authentication: Session + CSRF (No JWT)
- Django session-based auth for admin panel
- CSRF token validation for all mutations
- Nuxt middleware `admin-auth.js` checks `/api/auth/check/` endpoint
- Unauthenticated users redirected to Django admin login

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
- **Service layer** — business logic in `content/services/` (ProposalService, ProposalEmailService, ProposalPdfService, ContractPdfService, EmailTemplateRegistry, PdfUtils, DocumentPdfService, MarkdownParser, CollectionAccountService, CollectionAccountPdfService, TechnicalDocumentPdf, TechnicalDocumentFilter, PlatformOnboardingPdf)
- **Model layer** — thin models with properties (`is_expired`, `days_remaining`, `public_url`)
- **Huey tasks** — async operations: reminders, expiration, engagement-based emails
- **Custom admin site** — `content/admin.py` with custom `AdminSite` class
- **Management commands** — fake data generation for development/testing
- **Email template registry** — centralized email content management with admin-editable overrides

### Frontend Patterns

- **Pinia Options API** — all stores use Options API (state, getters, actions), not Composition API
- **Composables** — 29 composables for shared logic (`useExpirationTimer`, `useProposalNavigation`, `useProposalTracking`, `useSectionAnimations`, `usePlatformApi`, `usePlatformSidebar`, `usePlatformTheme`, `useMarkdownPreview`, `usePlatformCustomTheme`, `useTechnicalPrompt`, `useSellerPrompt`, `usePlatformIncludeArchived`, `useFreeResources`, etc.)
- **Component architecture** — 107 Vue components total; 34 BusinessProposal components (12 section types + admin + overlays + utilities)
- **GSAP animations** — horizontal scroll with ScrollTrigger for proposal client view, reveal animations for marketing pages
- **Layouts** — `default.vue` (public pages with navbar), `admin.vue` (admin panel with sidebar), `platform.vue` (platform with sidebar + theme)
- **Middleware** — `admin-auth.js` route guard for `/panel/**` routes, `platform-auth.js` route guard for `/platform/**` routes

---

## 6. Testing Strategy

### Backend (pytest)

- Location: `backend/content/tests/`, `backend/accounts/tests/`, `backend/tests/`
- Structure: `models/`, `serializers/`, `views/`, `services/`, `tasks/`, `utils/`, `management/`
- Test files: 74 total (46 content + 24 accounts + 1 projectapp + 2 backend/tests/ + 1 conftest)
- Fixtures: `conftest.py` at root and `content/tests/conftest.py`
- Coverage: custom terminal report with per-file bars and Top-N focus
- Config: `backend/pytest.ini`
- Run: `source venv/bin/activate && pytest backend/content/tests/<specific_file> -v`

### Frontend Unit (Jest)

- Location: `frontend/test/`
- Structure: `components/` (4), `composables/` (28+8 SSR), `stores/` (18 incl. services), `utils/` (5)
- Test files: 60 total
- Config: `frontend/jest.config.cjs`
- Run: `npm test -- test/<specific_file>.test.js`

### Frontend E2E (Playwright)

- Location: `frontend/e2e/`
- Structure: `admin/`, `auth/`, `blog/`, `layout/`, `platform/`, `proposal/`, `public/`
- Spec files: 121 total
- Flow definitions: `frontend/e2e/flow-definitions.json`
- Config: `frontend/playwright.config.js`
- Helpers: `frontend/e2e/helpers/`
- Run: `npx playwright test e2e/<specific_file>.spec.js` (max 2 files per invocation)

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
│   ├── accounts/               # Platform app (auth, onboarding, projects, kanban, bug reports, changes, deliverables, notifications, payments)
│   │   ├── models.py            # 21 models (UserProfile, VerificationCode, Project, Requirement, RequirementComment, RequirementHistory, BugReport, BugComment, ChangeRequest, ChangeRequestComment, Deliverable, DeliverableVersion, DeliverableFile, DeliverableClientFolder, DeliverableClientUpload, DataModelEntity, ProjectDataModelEntity, Notification, HostingSubscription, Payment, PaymentHistory)
│   │   ├── services/            # 10 services (image_utils, onboarding, tokens, verification, archive, notifications, payment_history, proposal_platform_onboarding, technical_requirements_sync, wompi)
│   │   ├── management/commands/ # 4 commands (create_platform_admin, seed_demo_clients, seed_platform_data, seed_mihuella)
│   │   ├── tests/               # 24 test files
│   │   └── urls.py              # 65 URL patterns
│   ├── content/                 # Main Django app
│   │   ├── models/              # 24 model files (proposal, blog, portfolio, contact, document, email, contract, etc.)
│   │   ├── serializers/         # DRF serializers (proposal, blog, portfolio, contact)
│   │   ├── views/               # FBV views (proposal 162K, blog 18K, portfolio 9K, email_templates 8K, document 10K, contact 2K)
│   │   ├── services/            # 15 service files (proposal 133K, email 71K, pdf 72K, templates 44K, pdf_utils 47K, contract_pdf 12K, document_pdf 19K, markdown_parser 9K, collection_account*, technical_document*, platform_onboarding_pdf)
│   │   ├── tasks.py             # Huey async tasks
│   │   ├── templates/emails/    # 48 email templates (24 HTML + 24 TXT)
│   │   ├── management/commands/ # 8 management commands
│   │   ├── tests/               # 46 test files (models, serializers, views, services, tasks, utils)
│   │   └── urls.py              # 99 URL patterns
│   ├── projectapp/              # Django project (settings, urls, wsgi, views, 1 test file)
│   ├── tests/                   # Root-level tests (test_document_pdf_service.py, test_markdown_parser.py)
│   ├── static/                  # Static files (Nuxt build output in prod)
│   └── media/                   # User uploads
├── frontend/
│   ├── pages/                   # Nuxt file-based routing (52 pages)
│   │   ├── panel/               # Admin pages (proposals, blog, portfolio, clients, documents, admins)
│   │   ├── platform/            # Platform pages (dashboard, board, projects, kanban, bugs, changes, deliverables, notifications, payments, clients, collection-accounts, profile, data-model)
│   │   ├── blog/                # Blog listing + detail
│   │   ├── portfolio-works/     # Portfolio listing + detail
│   │   └── proposal/            # Client proposal view
│   ├── components/              # Vue components (107 files)
│   │   └── BusinessProposal/    # 34 proposal components (12 sections + admin tabs + overlays + utilities)
│   ├── stores/                  # 18 Pinia stores (proposals, blog, portfolio_works, contacts, language, documents, panel_admins, platform-auth, platform-clients, platform-projects, platform-requirements, platform-bug-reports, platform-change-requests, platform-deliverables, platform-notifications, platform-payments, platform-collection-accounts, platform-data-model)
│   ├── composables/             # 29 composables
│   ├── e2e/                     # Playwright E2E tests (121 spec files)
│   ├── test/                    # Jest unit tests (60 test files)
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

1. **Dual auth** — `content`/`panel` uses session/CSRF; `accounts`/`platform` uses JWT (SimpleJWT); never mix the two HTTP clients
2. **Two Django apps** — `content` (proposals, blog, portfolio, documents, contracts) + `accounts` (platform users, projects, deliverables, data models)
3. **GoDaddy SMTP** — email delivery limited by provider (port 465 SSL only)
4. **Redis required** — for Huey task queue (even if immediate mode in dev)
5. **Nuxt builds to Django static** — production frontend is pre-rendered and served by Django, not a separate server
6. **Large service files** — `proposal_service.py` (133K), `proposal_pdf_service.py` (72K), `proposal_email_service.py` (71K), `pdf_utils.py` (47K) — shared utils extracted but could benefit from further splitting