---
trigger: model_decision
description: Project intelligence and lessons learned. Reference for project-specific patterns, preferences, and key insights discovered during development.
---

# Lessons Learned — ProjectApp

This file captures important patterns, preferences, and project intelligence that help work more effectively with this codebase. Updated as new insights are discovered.

---

## 1. Architecture Patterns

### Content Storage: Structured JSON over CMS
- Proposal sections, portfolio works, and blog posts use Django `JSONField` for content
- Each proposal section's `content_json` maps directly to a Vue component's props schema
- Blog supports dual format: structured JSON (preferred) with HTML fallback via `v-html`
- This avoids the need for a full CMS while keeping content rich and structured

### Single Django App: `content`
- All models, views, serializers, and services live in the `content` app
- This works for now but may need splitting if scope grows significantly
- Models are already split into individual files under `content/models/`

### Service Layer Pattern
- Business logic lives in `content/services/`, not in views
- Views are thin FBV wrappers that call service methods
- Services: `ProposalService`, `ProposalEmailService`, `ProposalPdfService`, `ContractPdfService`, `EmailTemplateRegistry`, `PdfUtils`, `DocumentPdfService`, `MarkdownParser`, `CollectionAccountService`, `CollectionAccountPdfService`, `TechnicalDocumentPdf`, `TechnicalDocumentFilter`, `PlatformOnboardingPdf`, `LinkedInService`

### External API Integration Pattern (LinkedIn)
- External OAuth integrations follow the singleton model + service module pattern
- `LinkedInToken` (singleton, pk=1) stores Fernet-encrypted access/refresh tokens in the DB; encryption key from `LINKEDIN_ENCRYPTION_KEY` env var
- `linkedin_service.py` encapsulates the full OAuth flow + API calls — views stay thin
- Follow this pattern for any future third-party OAuth integration (e.g., Twitter/X, Instagram)

### PDF Generation Layer
- `pdf_utils.py` is the shared utility layer — fonts, colors, layout helpers, reusable drawing functions
- `proposal_pdf_service.py`, `contract_pdf_service.py`, and `document_pdf_service.py` all depend on `PdfUtils`
- Never duplicate PDF primitives across services — add to `pdf_utils.py` and import from there
- All PDF services use ReportLab directly (no external PDF library abstraction)

---

## 2. Code Style & Conventions

### Backend: Function-Based Views (FBV)
- **All** DRF views use `@api_view` decorators, not class-based views
- Never convert to CBV unless explicitly requested
- Views file for proposals is very large (162K, 4385 lines) — be careful with edits

### Frontend: Pinia Options API
- **All** Pinia stores use Options API pattern: `{ state, getters, actions }`
- Do NOT use Composition API (`setup()`) style for stores
- HTTP requests go through `stores/services/request_http` centralized service

### Bilingual Content Pattern
- Models have paired fields: `title_en`/`title_es`, `content_json_en`/`content_json_es`, etc.
- Frontend reads the appropriate field based on current locale
- Proposals have a `language` field (`es`/`en`) that determines which default content to use

### Naming Conventions
- Backend: snake_case for everything (Python standard)
- Frontend stores: snake_case file names (`portfolio_works.js`, `proposals.js`)
- Frontend components: PascalCase (`BusinessProposal/Greeting.vue`)
- Frontend composables: camelCase with `use` prefix (`useExpirationTimer.js`)

---

## 3. Development Workflow

### Backend Commands Always Need venv
```bash
source venv/bin/activate && <command>
# or
venv/bin/python <command>
```

### Huey Immediate Mode in Development
- When `DJANGO_ENV != 'production'`, Huey tasks execute synchronously
- No need to run Redis or Huey worker for development
- Tasks still need to be importable and functional

### Frontend Dev Proxy
- Nuxt proxies `/api`, `/admin`, `/static`, `/media` to Django at `127.0.0.1:8000`
- Both servers must be running simultaneously for full functionality
- In production, everything goes through Django (no separate Nuxt server)

### Test Execution Rules
- Never run the full test suite — always specify files
- Backend: `pytest backend/content/tests/<specific_file> -v`
- Frontend: `npm test -- <specific_file>`
- E2E: max 2 files per `npx playwright test` invocation
- Use `E2E_REUSE_SERVER=1` when dev server is already running

---

## 4. Production Deployment

### Build Flow
1. Frontend: `npm run build:django` → generates `backend/static/frontend/`
2. Backend: `python manage.py collectstatic` → copies to `backend/staticfiles/`
3. Restart: `sudo systemctl restart projectapp && sudo systemctl restart projectapp-huey`

### Django Serves Nuxt Pages
- The `serve_nuxt` catch-all view in `projectapp/views.py` serves pre-rendered Nuxt pages
- This is the LAST URL pattern — all other routes take priority
- CDN URL for assets configurable via `NUXT_APP_CDN_URL`

---

## 5. Email System

### Template Registry Pattern
- All emails defined in `EmailTemplateRegistry` with default content
- Admin can override content via `EmailTemplateConfig` model
- Admin can disable specific emails via `is_active` flag
- Preview rendering available for all templates

### 24h Cooldown Rule
- `last_automated_email_at` field on `BusinessProposal` tracks last automated email
- All automated email tasks check this before sending
- Manual sends (admin clicks "Send") bypass the cooldown

### Composed Email Pattern (Branded + Proposal)
- Shared `_send_composed_email()` method reads templates from registry (not hardcoded paths)
- `send_branded_email()` — thin wrapper, no side effects beyond email + log
- `send_proposal_email()` — creates `ProposalChangeLog(EMAIL_SENT)` + updates `last_activity_at`
- Rate limited: 1 email per minute per template_key per proposal via `EmailLog` query
- `EmailLog.metadata` JSONField stores greeting, sections, footer, attachment_names for history
- View layer: shared `_parse_composed_email()` returns `(data, error_response)` tuple; 3 handler helpers (`_send_composed_email_view`, `_get_email_defaults_view`, `_list_emails_view`) serve 6 thin public views
- Frontend: single `ProposalEmailsTab.vue` with `mode` prop ('branded'/'proposal') + computed `basePath`

### Automations Pause
- `automations_paused` flag on `BusinessProposal` stops all automated emails
- Each Huey task checks this flag early and returns if paused

---

## 6. Proposal System Specifics

### Section Types Are Fixed
- 12 section types defined in `ProposalSection.SectionType` choices
- Each maps to a specific Vue component in `components/BusinessProposal/`
- Unique together constraint: `(proposal, section_type)` — one of each per proposal

### Heat Score (1-10)
- Pre-computed and cached in `cached_heat_score` field
- Updated by tracking endpoint and periodic task (`refresh_all_heat_scores`)
- Based on: view count, section time, recency, engagement patterns

### Change Log Types
- 20+ change types in `ProposalChangeLog.ChangeType`
- Includes: created, updated, sent, viewed, accepted, rejected, resent, expired, duplicated, commented, negotiating, reengagement, call, meeting, followup, note, calc_confirmed, calc_abandoned, auto_archived, status_change, cond_accepted, calc_followup, email_sent, req_clicked

---

## 7. Contract System Patterns

### Contract PDF Generation
- `ContractPdfService` generates PDFs via ReportLab using Helvetica font for consistent cross-platform rendering
- **Draft mode**: `is_draft=True` suppresses the contractor signature block — use for review cycles
- **Final mode**: includes full contractor signature block with name, date, and signature line
- Clickable Table of Contents generated at PDF start with anchor links to each section heading
- Template parameter substitution: `{{client_name}}`, `{{company_name}}`, etc. replaced at render time using `CompanySettings` + proposal data

### Data Model Entity Patterns
- `DataModelEntity` stores a reusable JSON schema (field definitions, types, constraints) independent of any project
- `ProjectDataModelEntity` associates an entity with a project and optionally overrides its schema
- Technical requirements sync: syncs project `Requirement` entries from the linked data model entity's schema fields
- JSON upload via API endpoint allows bulk creation of entity schemas from external tools
- Platform UI: `/platform/projects/:id/data-model` tab shows linked entities and allows sync actions

## 8. Platform / Accounts App Patterns

### Dual Auth Strategy
- `/panel/` admin uses Django session + CSRF (same as before)
- `/platform/` uses JWT via SimpleJWT (access + refresh tokens)
- Platform stores use `composables/usePlatformApi.js` (axios instance with JWT interceptors)
- Content stores use `stores/services/request_http` (axios with CSRF)
- **Never mix these two HTTP clients**

### Platform Store Naming
- Platform stores use kebab-case: `platform-auth.js`, `platform-clients.js`, `platform-projects.js`, `platform-requirements.js`
- Content stores use snake_case: `portfolio_works.js`, `proposals.js`

### Accounts Services
- `services/onboarding.py` — profile completion flow
- `services/tokens.py` — JWT token generation/refresh
- `services/verification.py` — OTP code generation and validation
- `services/image_utils.py` — avatar processing

### Platform Layout
- `layouts/platform.vue` with collapsible sidebar, mobile drawer, theme toggle
- Role-based navigation: admin sees all, client sees own projects only
- Dark mode support via `usePlatformTheme` composable

---

## 9. Testing Insights

### Backend conftest.py
- Custom coverage report with Unicode progress bars replaces default pytest-cov output
- `api_client` fixture provides unauthenticated DRF APIClient
- Content tests have their own `conftest.py` with model-specific fixtures

### E2E Flow Definitions
- Every navigation flow must be registered in `docs/USER_FLOW_MAP.md` and `frontend/e2e/flow-definitions.json`
- E2E tests must reflect real user integrations
- Follow quality standards from `docs/TESTING_QUALITY_STANDARDS.md`

### CI Sharding
- Playwright E2E tests are sharded into 5 parallel jobs
- Blob reports are merged after all shards complete
- Test quality gate runs after all test suites pass

### Known Test Issues
- `usePlatformApi.test.js` has 4 failing tests due to `window.location.href` assertions in JSDOM
- JSDOM doesn't support real navigation; `window.location.href` stays as `http://localhost/` after assignment
- Fix: use `delete window.location` + `Object.defineProperty` or mock `window.location` properly

### Playwright + Nuxt Dev Server Patterns
- **Never use `networkidle`** with Vite/Nuxt dev server — HMR WebSocket keeps connection alive, causing infinite hang
- Use `{ waitUntil: 'domcontentloaded' }` in `page.goto()` + explicit element waits (`getByRole('heading').waitFor()`)
- **Always add `test.setTimeout(60_000)`** to describe blocks for SPA routes — first visit triggers Vite on-demand compilation
- **Strict mode violations** are common when sidebar navigation duplicates page content text. Fix patterns:
  - Scope to `page.locator('main')` for page-specific content
  - Use `getByRole('heading', { name: '...' })` instead of `getByText('...')`
  - Use `{ exact: true }` when substring matching causes ambiguity (e.g., 'Activo' vs 'Activos')
- **i18n prefix strategy** adds locale prefix to all `<NuxtLink>` hrefs — use regex in `toHaveAttribute('href', /\/platform\/...$/)`
- **`<label>` without `for` attribute**: `getByLabel()` won't work. Use `page.locator('input[type="date"]')` or `page.locator('select').first()`
- **HTML5 validation bypass**: For testing custom validators, add `novalidate` via `page.evaluate(() => document.querySelector('form').setAttribute('novalidate', ''))`
- **Port conflicts**: Use `E2E_PORT=3001 E2E_REUSE_SERVER=1` when port 3000 is occupied

---

## 10. Methodology Maintenance

### Memory Bank Source
- Methodology rules based on [rules_template](https://github.com/Bhartendu-Kumar/rules_template)
- Original format is Cursor `.mdc` files; must be adapted to Windsurf `.md` format
- Key adaptation: replace `mdc:` prefix links with standard paths, `.mdc` → `.md` references, `src/` → `backend/`+`frontend/`
- `directory-structure.md` must be customized per project (the template uses generic `src/`, `test/`, etc.)

### When to Refresh Memory Files
- After adding a new Django app or major feature module
- After significant changes to test infrastructure or counts
- When file counts drift by >10% from documented values
- After methodology rule updates from upstream template
