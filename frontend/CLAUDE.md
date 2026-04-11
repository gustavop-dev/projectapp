# Frontend Rules — ProjectApp

## Stack And Scope
- Nuxt 3 + Vue 3 frontend.
- The codebase is primarily JavaScript, not TypeScript-first.
- State management uses Pinia.

## Project Conventions
- Pinia stores use the Options API pattern: `state`, `getters`, `actions`.
- Do not rewrite stores into setup-style Composition API stores unless explicitly asked.
- Content/admin HTTP flows use `frontend/stores/services/request_http.js`.
- Platform/auth HTTP flows use `frontend/composables/usePlatformApi.js`.
- Do not mix those two clients in the same feature.
- Preserve existing filename conventions:
  - content stores -> snake_case
  - platform stores -> kebab-case
  - components -> PascalCase
- Follow the current framework/file style in the touched area; do not force TypeScript into JS-heavy files.

## UX And Routing
- Nuxt pages and layouts drive routing.
- For Playwright and async UI work, prefer role-based locators and explicit element waits.
- Do not use `networkidle` for Nuxt/Vite flows.
- For SPA-heavy routes, keep `test.setTimeout(60_000)` in E2E specs.

## Commands
- Run frontend dev server: `npm --prefix frontend run dev`
- Run frontend unit tests: `npm --prefix frontend test -- path/to/file.spec.js`
- Run frontend coverage for a focused slice only when needed.
- Run E2E: `npm --prefix frontend run e2e -- path/to/spec.js`
- Build frontend: `npm --prefix frontend run build`

## Testing Rules
- Never run the full frontend unit or E2E suite.
- Assert user-visible behavior, not implementation details.
- Use stable locators in E2E and avoid brittle text matches when a role or scoped locator exists.
