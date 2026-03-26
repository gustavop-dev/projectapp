# Active Context — ProjectApp

## Current State

ProjectApp is in **production** at projectapp.co. All core features are implemented and deployed, including the Platform module (auth, onboarding, projects, kanban, client management). Quality gate score: **100/100** (0 errors, 0 warnings, 0 info). Focus is on test coverage refinement, documentation accuracy, and incremental improvements.

---

## Recent Focus Areas

1. **Proposal → Project integration (current)** — Link business proposals to projects with automatic data extraction:
   - Auto-create Kanban requirements from proposal's `functional_requirements` section (groups → modules, items → cards in backlog)
   - Extract payment milestones from proposal's `investment` section → stored in `Project.payment_milestones` JSONField (admin-visible only)
   - Extract hosting tiers with computed pricing → stored in `Project.hosting_tiers` JSONField (visible to both roles)
   - Auto-renewal: first Payment created with subscription; next Payment auto-generated on payment approval
   - Client can now change hosting plan (monthly/quarterly/semiannual) from their dashboard
   - Refactored 3 payment completion paths (card-pay, verify, webhook) into shared `_handle_payment_approved()` helper
   - Frontend: proposal selector + hosting plan picker in project creation modal; payment milestones + hosting tiers + Pagos module in project detail
   - Migration `0011_project_payment_milestones_hosting_tiers`
   - 15 new tests (auto-requirements, financial extraction, admin/client visibility, auto-renewal, no-duplicate)
2. **Platform E2E test fixes** — Fixed all 14 platform Playwright spec files (79 tests total). Key issues resolved:
   - Removed `defineI18nRoute(false)` from all platform pages (conflicted with `i18n.strategy: 'prefix'`)
   - Fixed security bug in `platform-auth.js` middleware: i18n locale prefixes bypassed path-based auth checks
   - Replaced `networkidle` with `domcontentloaded` + explicit element waits (Vite HMR WebSocket keeps connection alive)
   - Fixed strict mode violations: sidebar text duplicated in page content (scoped to `main` or used `getByRole`/`{ exact: true }`)
   - Fixed href assertions to use regex for i18n prefix compatibility
   - Fixed `getByLabel()` failures where `<label>` elements lack `for`/`id` linking
   - Added `test.setTimeout(60_000)` for Vite on-demand SPA route compilation
   - Bypassed HTML5 `type="email"` validation with `novalidate` for custom validator testing
3. **Memory Bank methodology refresh** — fixed all stale Cursor-specific `.mdc` references in methodology rules, updated directory structure, verified all file counts against live codebase
4. **Platform module (accounts app)** — JWT auth, OTP verification, complete-profile onboarding, projects CRUD, 3-column kanban board, client management, role-based sidebar
5. **Platform E2E coverage** — 14 Playwright spec files, 79 tests all passing
6. **Platform unit tests** — 12 backend test files (accounts), 7 frontend store tests (platform-auth, platform-clients, platform-projects, platform-requirements), 3 composable tests (usePlatformApi, usePlatformSidebar, usePlatformTheme)
7. **E2E coverage audit & remediation** — Full audit of 117 user flows against E2E specs. Fixed stale summary in `USER_FLOW_MAP.md`, registered 2 untracked flows, archived 1 deleted feature (`proposal-sticky-bar-accept`). Extended 3 existing specs (+10 tests for partial P1 flows). Created 2 new specs (executive-to-detailed, section-onboarding). Replaced all fragile selectors in platform specs with `getByTestId`/`getByLabel`. Quality gate: **100/100** with **0 warnings** across **1522 tests** in **128 files**.
8. **CI/CD pipeline** — GitHub Actions with pytest, Jest, Playwright (5 shards), quality gate

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

## Verified Codebase Metrics (March 2026)

| Metric | Count |
|--------|-------|
| Backend test files | 43 (30 content + 12 accounts + 1 projectapp) |
| Frontend unit tests | 36 |
| E2E spec files | 98 |
| Vue components | 93 |
| Pages | 41 |
| Pinia stores | 9 |
| Composables | 23 |
| Content models | 14 files |
| Accounts models | 6 classes |
| Content URL patterns | 71 |
| Accounts URL patterns | 15 |
| Email templates | 44 |
| Management commands | 8 (5 content + 3 accounts) |
| Quality gate score | 100/100 (0 warnings, 0 info) |

---

## Next Steps

- Fix 4 failing `usePlatformApi.test.js` tests (`window.location.href` assertion issue in JSDOM)
- **Deferred E2E:** `platform-verify-onboarding` — requires OTP test infrastructure (mock OTP delivery or test bypass)
- Increase backend test coverage (target areas: services edge cases, accounts app edge cases)
- Increase frontend unit test coverage (target areas: remaining composables, components)
- Consider splitting large files (proposal views 123K, service 130K, PDF 89K)
- Credential rotation for production secrets exposed in git history
- Explore API rate limiting for public endpoints
- Kill rogue `kore_project` Next.js server on port 3000 permanently (respawns from Windsurf terminal)
