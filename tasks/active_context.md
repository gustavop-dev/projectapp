# Active Context — ProjectApp

## Current State

ProjectApp is in **production** at projectapp.co. All core features are implemented and deployed. Active development branch: **`generate-pdf-with-template`** — Document System (generic branded PDF). Platform module has been significantly expanded with Bug Reports, Change Requests, Deliverables, Notifications, and Payments modules.

---

## Recent Focus Areas

1. **Document System (current — branch `generate-pdf-with-template`)** — Generic branded PDF documents:
   - `Document` model in `content/models/document.py` — uuid, title, slug, status (draft/published/archived), language, cover_type
   - Services: `document_pdf_service.py` (20K), `markdown_parser.py` (9K), `pdf_utils.py` (36K shared PDF utilities)
   - Panel pages: `/panel/documents/` (index, create, edit)
   - Store: `documents.js`
   - New composable: `useMarkdownPreview.js`
   - Backend tests: `test_document_pdf_service.py`, `test_markdown_parser.py` (in `backend/tests/`)
2. **Platform — Expanded Modules** — Five new Platform feature areas added to accounts app:
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

## Verified Codebase Metrics (March 2026 — refreshed)

| Metric | Count |
|--------|-------|
| Backend test files | 50 (30 content + 17 accounts + 1 projectapp + 2 backend/) |
| Frontend unit tests | 36 |
| E2E spec files | 112 |
| Vue components | 96 |
| Pages | 54 |
| Pinia stores | 16 |
| Composables | 25 |
| Content model files | 15 (added document.py) |
| Accounts models file | 1 (models.py with 6+ classes) |
| Content URL patterns | 81 |
| Accounts URL patterns | 48 |
| Email templates | 44 |
| Management commands | 12 (8 content + 4 accounts) |
| Content services | 7 (proposal, email, pdf, templates, document_pdf, markdown_parser, pdf_utils) |
| Quality gate score | 100/100 (0 warnings, 0 info) |

---

## Next Steps

- Complete Document System PDF generation (branch `generate-pdf-with-template`): template rendering, preview, download flow
- Fix 4 failing `usePlatformApi.test.js` tests (`window.location.href` assertion issue in JSDOM)
- **Deferred E2E:** `platform-verify-onboarding` — requires OTP test infrastructure (mock OTP delivery or test bypass)
- Add E2E coverage for new Platform modules (bug reports, change requests, deliverables, notifications, payments)
- Add E2E coverage for Document system (admin panel CRUD + PDF download)
- Increase backend test coverage (target areas: services edge cases, accounts app edge cases)
- Increase frontend unit test coverage (target areas: remaining composables, components)
- Consider splitting large files (proposal views 123K, service 132K, PDF 72K — shared utils already in `pdf_utils.py`)
- Credential rotation for production secrets exposed in git history
- Explore API rate limiting for public endpoints
- Kill rogue `kore_project` Next.js server on port 3000 permanently (respawns from Windsurf terminal)
