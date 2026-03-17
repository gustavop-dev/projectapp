# Active Context — ProjectApp

## Current State

**Date**: 2026-03-16

ProjectApp is a **mature production application** running at `projectapp.co`. All core features are implemented and deployed. The Memory Files system has just been initialized to formalize project knowledge.

---

## Recent Focus Areas

Based on codebase analysis, the most recently developed/evolved areas include:

1. **Engagement Tracking & Scoring** — Heat score computation, engagement decay detection, section-level time analytics, view modes (executive vs detailed)
2. **Investment Calculator** — Interactive modal for clients to explore payment options with hosting discounts (quarterly, semiannual)
3. **Email Deliverability Dashboard** — Monitoring email send/delivery/bounce/failed rates per template
4. **Blog System** — Full admin CRUD with structured JSON content, categories, author profiles, calendar view, sitemap
5. **Portfolio Admin** — CRUD with JSON import, cover image upload, duplicate, bilingual content
6. **Email Template Management** — Admin-editable email content with preview and reset functionality
7. **Proposal Automation Enhancements** — Calculator follow-ups, post-rejection revisits, conditional acceptance, engagement decay alerts
8. **Share Links** — Multi-stakeholder proposal sharing with independent tracking

---

## Active Decisions & Considerations

- **No active feature development** at the time of Memory Files initialization
- **Credential rotation** is a documented pending action (see `docs/deployment-guide.md`)
- **Large files** (`proposal_service.py` 130K, `proposal_pdf_service.py` 89K, `views/proposal.py` 123K) are candidates for future refactoring but not blocking

---

## Development Environment

- **Backend**: Django 5.0.6, Python 3.12, SQLite (dev), MySQL (prod)
- **Frontend**: Nuxt 3.14, Node 22, Vue 3.4
- **Task Queue**: Huey + Redis (immediate mode in dev)
- **CI/CD**: GitHub Actions with 5 jobs (backend pytest, frontend Jest, Playwright 5-shard E2E, merge reports, quality gate)

---

## Next Steps

- Monitor and maintain production stability
- Address credential rotation (high priority security item)
- Consider splitting large service/view files when next touching proposal code
- Continue expanding test coverage
- Memory Files will be updated as new features or changes are implemented