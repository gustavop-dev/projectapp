# Active Context — ProjectApp

## Current State

ProjectApp is in **production** at projectapp.co. All core features are implemented and deployed. Active branch: **`main`**. The Document System PDF (generic branded PDF on branch `generate-pdf-with-template`) is still in progress and not yet merged. Platform module has been significantly expanded with Bug Reports, Change Requests, Deliverables, Notifications, Payments modules, and a new Data Model Entities feature.

---

## Recent Focus Areas

1. **Proposal Advanced Filters & Saved Tabs** (Apr 5, 2026):
   - New composable `useProposalFilters.js` — 11 filter dimensions (status, project type, market type, currency, language, investment range, heat score range, view count range, created date range, last activity date range, active status), saveable named tabs with localStorage persistence, URL sync (`?tab=xxx`), max 12 tabs
   - New components: `ProposalFilterTabs.vue` (tab bar with +, rename, delete), `ProposalFilterPanel.vue` (collapsible filter panel with responsive grid)
   - Shared utility: `selectArrowStyle.js` extracted from duplicated SVG constant
   - Backend: added `language`, `sent_at` to `ProposalListSerializer`; batch engagement summary computation in `list_proposals` view (3 aggregated queries instead of N+1)
   - Performance: single filter pass, pre-computed date boundaries, `structuredClone`, shallow watcher
   - Replaced old status pills with filter tabs + "Filtros" toggle button; `statusOptions` array simplified to `statusLabelMap` object
2. **LinkedIn Integration for Blog Publishing** (Apr 5, 2026):
   - `LinkedInToken` singleton model with Fernet-encrypted access/refresh token storage (`linkedin_token.py`)
   - `linkedin_service.py` — OAuth 2.0 authorization code flow, automatic token refresh, publish/unpublish blog post summaries with cover images via LinkedIn Posts API (`/rest/posts`)
   - Admin panel UI: connect/disconnect LinkedIn account, publish toggle per blog post
   - Scopes: `openid profile email w_member_social`; encryption key via `LINKEDIN_ENCRYPTION_KEY` env var
2. **Branded + Proposal Composed Email System** (Apr 4, 2026):
   - Two new email tabs on proposal edit page: "Correos" (branded, for negotiating/accepted/rejected) and "Enviar correo" (proposal, for sent+ statuses)
   - Shared composer UI with draggable sections (vuedraggable), file attachments, branded preview, paginated history
   - Backend: `_send_composed_email()` shared service method, `send_branded_email()` + `send_proposal_email()` wrappers; proposal email creates `ProposalChangeLog` with `EMAIL_SENT` change type
   - 6 new URL patterns: send/defaults/history for each variant (branded-email + proposal-email)
   - `EmailLog.metadata` JSONField for storing full email content in history
   - New component: `ProposalEmailsTab.vue` with `mode` prop ('branded'/'proposal')
   - Store actions: `sendComposedEmail()`, `fetchEmailDefaults()`, `fetchEmailHistory()` with `basePath` parameter
   - Tests: 14 service + 19 view + 2 registry (backend), 30 component + 3 store (frontend), 4 E2E
   - 2 new flows in `flow-definitions.json` + `USER_FLOW_MAP.md` (v2.11.0)
   - Seed data: `create_fake_proposals.py` generates EmailLog entries for negotiating/accepted proposals
2. **Contract System** — Full contract parameters and proposal document handling (merged to main Apr 2–3, 2026):
   - New models: `CompanySettings` (contractor_signature ImageField), `ContractTemplate`, `ProposalDocument` — migrations 0061–0068
   - Service: `contract_pdf_service.py` — full contract PDF generation with template support, contractor signature rendering, draft mode (no signature), Helvetica/Times fonts
   - PDF enhancements in `pdf_utils.py`: `_apply_toc_links()` (clickable GoTo annotations), `_draw_line_with_links()` (inline justification with bold/italic/link tokens), `_draw_toc_page()`, `lru_cache` on `_font()`
   - Admin UI: `ContractParamsModal.vue`, `SendDocumentsModal.vue`, `ProposalDocumentsTab.vue`
   - Email: `proposal_documents_sent` template; enhanced `ProposalEmailService`
   - E2E: 5 new admin proposal specs (contract download/edit/generate, documents manage/send)
2. **Data Model Entities** — Platform feature for deliverables and project data models (Apr 3, 2026):
   - New models: `DataModelEntity`, `ProjectDataModelEntity` in accounts app — migrations 0021–0022
   - Service: `technical_requirements_sync.py` — sync entities with technical requirements
   - New page: `/platform/projects/[id]/data-model.vue` — JSON upload, entity list, template download
   - New store: `platform-data-model.js` — fetchEntities, uploadEntities, fetchTemplate
   - Tests: `test_data_model_entity.py` (60 cases), `test_data_model_views.py`, `platform-data-model.test.js` (26 cases), `platform-data-model.spec.js` (E2E)
3. **Platform UI Improvements** (Apr 1, 2026):
   - Terminology: 'Épica' → 'Módulo' across all platform pages
   - `useConfirmModal.js` refactored to promise-based API (+34 lines); `useConfirmModal.test.js` added
   - Dark mode removed from platform login, verify, complete-profile pages; `usePlatformTheme.js` simplified
4. **Document System (branch `generate-pdf-with-template` — not yet merged)** — Generic branded PDF documents:
   - `Document` model in `content/models/document.py` — uuid, title, slug, status (draft/published/archived), language, cover_type
   - Services: `document_pdf_service.py` (20K), `markdown_parser.py` (9K), `pdf_utils.py` (shared PDF utilities)
   - Panel pages: `/panel/documents/` (index, create, edit)
   - Store: `documents.js`
   - New composable: `useMarkdownPreview.js`
   - Backend tests: `test_document_pdf_service.py`, `test_markdown_parser.py` (in `backend/tests/`)
5. **Platform — Expanded Modules** — Five new Platform feature areas added to accounts app:
   - Bug Reports: `platform-bug-reports.js`, `/platform/bugs`, `/platform/projects/[id]/bugs`, `test_bug_reports.py`
   - Change Requests: `platform-change-requests.js`, `/platform/changes`, `/platform/projects/[id]/changes`, `test_change_requests.py`
   - Deliverables: `platform-deliverables.js`, `/platform/deliverables`, `/platform/projects/[id]/deliverables`, `test_deliverables.py`
   - Notifications: `platform-notifications.js`, `/platform/notifications`, `test_notifications.py`
   - Payments: `platform-payments.js`, `/platform/payments`, `/platform/projects/[id]/payments`, `test_payments.py`
   - Global Board: `/platform/board`; Profile page: `/platform/profile`
   - New composable: `usePlatformCustomTheme.js`
   - New accounts tests: `test_permissions.py`, `test_views_edge_cases.py`
3. **Panel Admins** — Admin management: `panel/admins/index.vue` + `panel_admins.js` store
4. **Panel Login** — Dedicated `panel/login.vue` page
5. **Proposal → Project integration** — Link proposals to projects: auto-create Kanban requirements from `functional_requirements` section, extract payment milestones and hosting tiers, auto-renewal on payment approval
6. **Platform E2E test fixes** — Fixed all platform Playwright spec files; removed `defineI18nRoute(false)`, fixed security bug in `platform-auth.js` middleware, replaced `networkidle` with `domcontentloaded`
7. **E2E coverage audit & remediation** — 112 E2E spec files; Quality gate: **100/100** with **0 warnings**
8. **CI/CD pipeline** — GitHub Actions with pytest, Jest, Playwright (5 shards), quality gate
9. **SEO On-Page Optimization** — Comprehensive SEO improvements across main views and blog:
   - Enhanced `useSeoHead.js` composable: added canonical URL, `og:locale`, `twitter:site`
   - Created `useSeoJsonLd.js` composable: `useJsonLd`, `useServiceJsonLd`, `useBlogPostJsonLd`, `useBlogListJsonLd`, `useWebPageJsonLd`
   - Enhanced global JSON-LD in `layouts/default.vue`: Organization + WebSite `@graph` with `@id` references
   - Added Service + BreadcrumbList JSON-LD to: `index.vue`, `landing-software.vue`, `landing-apps.vue`, `landing-web-design.vue`
   - Added WebPage JSON-LD to: `about-us.vue` (AboutPage), `contact.vue` (ContactPage), `portfolio-works/index.vue` (CollectionPage)
   - Fixed `contact.vue`: added missing `useSeoHead('contact')` + router locale meta (en/es)
   - Fixed `blog/index.vue`: locale-aware canonical, `og:url`, `og:site_name`, `og:locale`, `twitter:card/site`, hreflang, Blog JSON-LD
   - Fixed `blog/[slug].vue`: locale-aware canonical, `og:url`, `og:site_name`, `og:locale`, `article:author`, `twitter:card/site`, hreflang, BlogPosting JSON-LD
   - Fixed hardcoded CTA links in blog pages to use `localePath('/contact')`
10. **Terms & Privacy Pages** — Created localized Terms and Conditions + Privacy Policy views with SEO, routing, and footer links

---

## Active Decisions

- **FBV over CBV** — all views remain function-based; no plans to migrate
- **Pinia Options API** — all stores use Options API pattern; no Composition API stores
- **Two Django apps** — `content` (proposals, blog, portfolio, contact) + `accounts` (platform auth, projects, kanban)
- **Hybrid rendering** — SSR for SEO pages, SPA for admin, proposal, and platform views
- **Dual auth strategy** — Session/CSRF for `/panel/` admin; JWT (SimpleJWT) for `/platform/`

---

## Development Environment

- **Backend**: Django 5 + DRF, SQLite (dev) / MySQL (prod), Huey immediate mode
- **Frontend**: Nuxt 3 + Pinia + TailwindCSS, dev server on port 3001 (port 3000 occupied by kore_project Next.js)
- **Both servers** must run simultaneously for full functionality in development
- **Redis**: Required in production for Huey task queue

---

## Verified Codebase Metrics (April 5, 2026 — refreshed)

| Metric | Count |
|--------|-------|
| Backend test files | 83 |
| Frontend unit tests | 60 |
| E2E spec files | 125 |
| Vue components | 111 |
| Pages | 62 |
| Pinia stores | 18 |
| Composables | 31 |
| Content model files | 26 |
| Accounts models | 21 |
| Accounts URL patterns | 65 |
| Content URL patterns | 103 |
| Email templates | 48 (24 HTML + 24 TXT) |
| Content services | 16 |
| Accounts services | 10 |
| Quality gate score | 100/100 (0 warnings, 0 info) |

---

## Next Steps

- Complete Document System PDF generation (branch `generate-pdf-with-template`): template rendering, preview, download flow
- Add unit tests for `useProposalFilters.js` composable and `ProposalFilterPanel.vue` / `ProposalFilterTabs.vue` components
- Add E2E coverage for Contract System (ContractParamsModal, SendDocumentsModal admin workflows)
- Add E2E coverage for Platform Data Model page (`/platform/projects/[id]/data-model`)
- Add backend test coverage for contract/document services (`contract_pdf_service.py`, `technical_document_pdf.py`)
- Fix 4 failing `usePlatformApi.test.js` tests (`window.location.href` assertion issue in JSDOM)
- **Deferred E2E:** `platform-verify-onboarding` — requires OTP test infrastructure (mock OTP delivery or test bypass)
- Add E2E coverage for new Platform modules (bug reports, change requests, deliverables, notifications, payments)
- Increase backend test coverage (target areas: services edge cases, accounts app edge cases)
- Increase frontend unit test coverage (target areas: remaining composables, components)
- Consider splitting large files (proposal views 162K, proposal service 133K, email service 71K — shared utils already in `pdf_utils.py`)
- Credential rotation for production secrets exposed in git history
- Explore API rate limiting for public endpoints
- Kill rogue `kore_project` Next.js server on port 3000 permanently (respawns from Windsurf terminal)
