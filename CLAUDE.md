# ProjectApp — Claude Compatibility Guide

## Source Of Truth
- The canonical repo guidance is maintained in the Codex-native surfaces: `AGENTS.md`, `backend/AGENTS.md`, `frontend/AGENTS.md`, `.agents/skills/*`, `.codex/config.toml`.
- This `CLAUDE.md` file is a compatibility mirror for mixed-tool teams and should stay aligned with the Codex guidance.
- Deep project context lives in `docs/methodology/` and `tasks/`.

## Project Overview
- Stack: Django 5 + DRF, Nuxt 3 + Vue 3, MySQL 8, Redis, Huey.
- Main Django apps: `content` for proposals/blog/portfolio and `accounts` for platform/auth/project data.
- Production path: `/home/ryzepeck/webapps/projectapp`.
- Services: `projectapp.service`, `projectapp.socket`, `projectapp-huey.service`.
- Frontend build output is served by Django.

## Architecture Invariants
- Backend API views in this repo are function-based DRF views with `@api_view`; do not convert them to CBVs unless the user explicitly asks.
- Business logic belongs in services, serializers, helpers, or model methods; keep views thin.
- Proposal section `content_json` data maps directly to Vue component props; keep backend and frontend shapes aligned.
- Bilingual content usually uses paired fields such as `_en` and `_es`; preserve that pattern.
- `/panel/` uses Django session + CSRF. `/platform/` uses JWT via SimpleJWT.
- Do not mix the two frontend HTTP clients:
  - content/admin flows -> `frontend/stores/services/request_http.js`
  - platform flows -> `frontend/composables/usePlatformApi.js`
- Pinia stores use the Options API shape `{ state, getters, actions }`.
- Content stores use snake_case filenames. Platform stores use kebab-case filenames.

## Working Rules
- Prefer existing project patterns over generic framework advice.
- Keep edits localized in large files, especially `backend/content/views/proposal.py`.
- Do not change old migrations; add new migrations when schema changes are required.
- Keep security basics intact: validated serializer inputs, ORM-first queries, escaped rendering, CSRF/session boundaries, and no secrets in code.

## Commands
- Backend tests: `source .venv/bin/activate && cd backend && pytest path/to/test_file.py -v`
- Backend dev server: `source .venv/bin/activate && cd backend && python manage.py runserver`
- Frontend dev server: `npm --prefix frontend run dev`
- Frontend unit tests: `npm --prefix frontend test -- path/to/file.spec.js`
- Frontend E2E: `npm --prefix frontend run e2e -- path/to/spec.js`
- Frontend build: `npm --prefix frontend run build`

## Testing Constraints
- Never run the full test suite.
- Maximum 20 tests per batch and 3 test commands per cycle.
- Run only the smallest backend, frontend unit, or E2E slice needed for the changed behavior.
- For Playwright on Nuxt routes, use `domcontentloaded` and explicit waits, not `networkidle`.

## Memory Bank
- Core files: `docs/methodology/product_requirement_docs.md`, `architecture.md`, `technical.md`, `error-documentation.md`, `lessons-learned.md`, `tasks/tasks_plan.md`, `tasks/active_context.md`.
- Update memory files when the user asks, or when you have verified a meaningful change to runtime surfaces, architecture, or recurring workflow guidance.
- Do not churn memory files after every routine code edit.
