# Active Context — ProjectApp

## Current State

ProjectApp is in **production** at projectapp.co. All core features are implemented and deployed, including the Platform module (auth, onboarding, projects, kanban, client management). Quality gate score: **100/100**. Focus is on test coverage refinement, documentation accuracy, and incremental improvements.

---

## Recent Focus Areas

1. **Platform E2E test fixes (current)** — Fixed all 14 platform Playwright spec files (79 tests total). Key issues resolved:
   - Removed `defineI18nRoute(false)` from all platform pages (conflicted with `i18n.strategy: 'prefix'`)
   - Fixed security bug in `platform-auth.js` middleware: i18n locale prefixes bypassed path-based auth checks
   - Replaced `networkidle` with `domcontentloaded` + explicit element waits (Vite HMR WebSocket keeps connection alive)
   - Fixed strict mode violations: sidebar text duplicated in page content (scoped to `main` or used `getByRole`/`{ exact: true }`)
   - Fixed href assertions to use regex for i18n prefix compatibility
   - Fixed `getByLabel()` failures where `<label>` elements lack `for`/`id` linking
   - Added `test.setTimeout(60_000)` for Vite on-demand SPA route compilation
   - Bypassed HTML5 `type="email"` validation with `novalidate` for custom validator testing
2. **Memory Bank methodology refresh** — fixed all stale Cursor-specific `.mdc` references in methodology rules, updated directory structure, verified all file counts against live codebase
3. **Platform module (accounts app)** — JWT auth, OTP verification, complete-profile onboarding, projects CRUD, 3-column kanban board, client management, role-based sidebar
4. **Platform E2E coverage** — 14 Playwright spec files, 79 tests all passing
5. **Platform unit tests** — 12 backend test files (accounts), 7 frontend store tests (platform-auth, platform-clients, platform-projects, platform-requirements), 3 composable tests (usePlatformApi, usePlatformSidebar, usePlatformTheme)
6. **Quality gate** — 100/100 score, 18 warnings (fragile selectors in platform E2E), 1444 tests scanned across 115 files
7. **CI/CD pipeline** — GitHub Actions with pytest, Jest, Playwright (5 shards), quality gate

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
| E2E spec files | 96 |
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
| Quality gate score | 100/100 |

---

## Next Steps

- Fix 4 failing `usePlatformApi.test.js` tests (`window.location.href` assertion issue in JSDOM)
- Update `flow-definitions.json` and `USER_FLOW_MAP.md` with coverage status for all 14 platform flows
- Increase backend test coverage (target areas: services edge cases, accounts app edge cases)
- Increase frontend unit test coverage (target areas: remaining composables, components)
- Consider splitting large files (proposal views 123K, service 130K, PDF 89K)
- Credential rotation for production secrets exposed in git history
- Explore API rate limiting for public endpoints
- Kill rogue `kore_project` Next.js server on port 3000 permanently (respawns from Windsurf terminal)
