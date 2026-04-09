---
trigger: model_decision
description: Error documentation and known issues tracking. Reference when debugging, fixing bugs, or encountering recurring issues.
---

# Error Documentation — ProjectApp

This file tracks known errors, their context, and resolutions. When a reusable fix or correction is found during development, document it here to avoid repeating the same mistake.

---

## Format

```
### [ERROR-NNN] Short description
- **Date**: YYYY-MM-DD
- **Context**: Where/when this error occurs
- **Root Cause**: Why it happens
- **Resolution**: How to fix it
- **Files Affected**: List of files
```

---

## Known Issues

### [KNOWN-001] kore_project Next.js server occupies port 3000
- **Date**: 2025-07-07
- **Context**: A Windsurf terminal runs `npm run dev --port 3000` for `kore_project`, which respawns after being killed
- **Impact**: Nuxt dev server can't bind port 3000; E2E tests fail intermittently
- **Workaround**: Run Nuxt on port 3001 with `E2E_PORT=3001`
- **Permanent fix**: Close the kore_project terminal in Windsurf IDE

### [KNOWN-002] usePlatformApi.test.js has 4 failing tests in JSDOM
- **Date**: 2026-04-03
- **Context**: `frontend/test/composables/usePlatformApi.test.js` — tests that assert `window.location.href` has changed after a redirect call
- **Root Cause**: JSDOM doesn't support real navigation; `window.location.href` stays as `http://localhost/` even after assignment
- **Impact**: 4 tests permanently fail in Jest/JSDOM environment; does not affect runtime behavior
- **Workaround**: Tests are known failures; excluded from quality gate pass/fail criteria
- **Permanent fix**: Mock `window.location` using `delete window.location` + `Object.defineProperty(window, 'location', { value: { href: '' }, writable: true })` before assertions

---

## Resolved Issues

### [ERR-001] defineI18nRoute(false) conflicts with i18n strategy 'prefix'
- **Date**: 2025-07-07
- **Context**: All platform pages had `defineI18nRoute(false)`, but Nuxt i18n uses `strategy: 'prefix'`
- **Root Cause**: Routes returned 404 because the router expected locale-prefixed paths
- **Resolution**: Removed `defineI18nRoute(false)` from all 11 platform page files
- **Files Affected**: `frontend/pages/platform/*.vue`, `frontend/pages/platform/projects/**/*.vue`, `frontend/pages/platform/clients/**/*.vue`

### [ERR-002] platform-auth middleware bypassed by i18n locale prefix (SECURITY)
- **Date**: 2025-07-07
- **Context**: `platform-auth.js` checked `to.path.startsWith('/platform')` but i18n produces `/en-us/platform/login`
- **Root Cause**: Path comparisons didn't strip locale prefix, so all auth guards were bypassed
- **Resolution**: Added `rawPath = to.path.replace(/^\/[a-z]{2}(-[a-z]{2})?(?=\/)/, '')` before path checks
- **Files Affected**: `frontend/middleware/platform-auth.js`

### [ERR-003] Playwright networkidle hangs with Vite HMR WebSocket
- **Date**: 2025-07-07
- **Context**: `page.waitForLoadState('networkidle')` never resolves in Nuxt dev mode
- **Root Cause**: Vite HMR WebSocket keeps persistent connection, preventing networkidle
- **Resolution**: Use `domcontentloaded` + explicit element waits instead
- **Files Affected**: All 14 `frontend/e2e/platform/*.spec.js` files

### [ERR-004] Playwright strict mode violations from sidebar + page content
- **Date**: 2025-07-07
- **Context**: `getByText('Tablero')`, `getByText('Proyectos')`, etc. matched both sidebar links and page headings
- **Resolution**: Scope to `page.locator('main')`, use `getByRole('heading')`, or `{ exact: true }`
- **Files Affected**: Multiple platform E2E spec files

### [ERR-005] format_bogota_date crashed on plain `date` instances
- **Date**: 2026-04-09
- **Context**: New `ProposalProjectStage` model uses `DateField` for `start_date` and `end_date`. The stage email send methods passed `stage.start_date` to `format_bogota_date()`, which expected a `datetime`.
- **Root Cause**: `format_bogota_date()` called `dj_timezone.is_naive(dt)` and `dt.astimezone(_BOGOTA_TZ)` unconditionally — both of which AttributeError on a plain `date` instance.
- **Resolution**: Updated `format_bogota_date()` in `backend/content/utils.py` to check `isinstance(dt, datetime)` first and skip the timezone conversion for `date` instances. The function now accepts both types and returns `''` for unsupported inputs.
- **Files Affected**: `backend/content/utils.py:format_bogota_date`
- **Test coverage**: 9 stage email service tests now exercise this code path with `DateField` values.

### [ERR-006] Vue stage badge didn't update after store action
- **Date**: 2026-04-09
- **Context**: Mark-as-completed E2E test for the new Cronograma tab failed: clicking "Marcar como completada" called the API and returned `completed_at`, but the badge still showed "🟡 Faltan 1 día" instead of "🟢 Completada".
- **Root Cause**: The store helper `_mergeProjectStage` was reassigning `currentProposal` to a new object spread (`this.currentProposal = { ...this.currentProposal, project_stages: stages }`). The component was reading via `props.proposal` which came from a parent `computed(() => proposalStore.currentProposal)`. Vue's reactivity through the computed → prop chain didn't reliably pick up the spread+reassign combination, even though it tracks the top-level ref.
- **Resolution**: Two changes:
  1. Switched `_mergeProjectStage` to in-place index mutation matching the established pattern used by `updateSection`, `applySync`, and `reorderSections` in the same store: `this.currentProposal.project_stages[idx] = stage`.
  2. Refactored `ProjectScheduleEditor.vue` to read stages directly from `proposalStore.currentProposal?.project_stages` via a computed (with `props.proposal` as fallback for tests), instead of maintaining a local `localStages` mirror with a deep prop watcher (which also clobbered in-progress form edits when other parts of the proposal changed).
- **Files Affected**:
  - `frontend/stores/proposals.js:_mergeProjectStage`
  - `frontend/components/BusinessProposal/admin/ProjectScheduleEditor.vue`
- **Lesson**: When updating nested arrays in a Pinia store consumed by Vue components, mutate by index — do not spread + reassign the parent object. See `lessons-learned.md` § Pinia Reactivity for the rule.

### [ERR-007] respond_to_proposal omitía send_acceptance_confirmation
- **Date**: 2026-04-09
- **Context**: The public endpoint `POST /api/proposals/<uuid>/respond/` with `action='accepted'` was not sending the acceptance confirmation email to the client, even though the docstring of `respond_to_proposal` explicitly promised it. Pre-existing test `TestRespondReengagement.test_acceptance_sends_confirmation_email` was already in the working tree but was failing — this surfaced when running the full proposal test slice during Phase A of the real-client-entity feature.
- **Root Cause**: `backend/content/views/proposal.py:respond_to_proposal` had branches for `action == 'rejected'` (sends `send_rejection_thank_you` + schedules re-engagement) and `action == 'negotiating'` (sends `send_negotiation_notification` + `send_negotiation_confirmation`), but **no branch for `accepted`**. The view always called `send_response_notification` (internal team alert) regardless of action, but the client-facing acceptance confirmation was never wired in.
- **Resolution**: Added the missing branch:
  ```python
  elif action == 'accepted':
      ProposalEmailService.send_acceptance_confirmation(proposal)
  ```
  Right after the existing `negotiating` branch in `respond_to_proposal`. Verified by re-running the failing test plus the full `TestRespondReengagement` class (4/4 green).
- **Files Affected**: `backend/content/views/proposal.py:respond_to_proposal`
- **Lesson**: When a docstring describes a side effect, write a test that asserts the side effect AND wire the side effect into the code. Tests-and-docstring drift is the most common silent regression source.
