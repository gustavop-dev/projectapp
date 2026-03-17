# Active Context — ProjectApp

## Current State

ProjectApp is in **production** at projectapp.co. All core features are implemented and deployed. The focus is on testing coverage, documentation, and incremental improvements.

---

## Recent Focus Areas

1. **Memory Files initialization** — documented the entire project in 7 core Memory Files
2. **Testing quality gate** — custom CI step enforcing test quality standards
3. **E2E test coverage** — 82 Playwright spec files covering admin, auth, blog, layout, proposal, public flows
4. **Email deliverability** — dashboard and tracking for proposal email system
5. **Proposal analytics** — heat score, section time tracking, engagement signals
6. **Blog system** — structured JSON content with bilingual support
7. **CI/CD pipeline** — GitHub Actions with pytest, Jest, Playwright (5 shards), quality gate
8. **Documentation** — deployment guide, testing standards, user flow map

---

## Active Decisions

- **FBV over CBV** — all views remain function-based; no plans to migrate
- **Pinia Options API** — all stores use Options API pattern; no Composition API stores
- **Single `content` app** — all models/views/services stay in one app for now
- **Hybrid rendering** — SSR for SEO pages, SPA for admin and proposal views
- **No JWT** — session/CSRF auth only; frontend proxies through same origin

---

## Development Environment

- **Backend**: Django 5 + DRF, SQLite (dev) / MySQL (prod), Huey immediate mode
- **Frontend**: Nuxt 3 + Pinia + TailwindCSS, dev server on port 3000
- **Both servers** must run simultaneously for full functionality in development
- **Redis**: Required in production for Huey task queue

---

## Next Steps

- Increase backend test coverage (target areas: services, edge cases)
- Increase frontend unit test coverage (target areas: composables, components)
- Consider splitting large files (proposal views 123K, service 130K, PDF 89K)
- Credential rotation for production secrets exposed in git history
- Explore API rate limiting for public endpoints
