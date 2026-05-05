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

### [ERR-008] DRF APIClient: `content_type='application/json'` with a dict causes KeyError
- **Date**: 2026-04-19
- **Context**: New backend tests for markdown PDF attachment endpoints used `client.post(url, data=dict, content_type='application/json')`. Tests that then accessed `response.data['error']` raised `KeyError` because the response body was a DRF validation error dict with a different shape.
- **Root Cause**: Passing `content_type='application/json'` with a `dict` skips DRF's multipart parsing — the dict is JSON-serialized by Django's test client, but DRF's parser may not decode it as expected when `request.data` is checked. The simpler and correct form is `format='json'` with a plain dict.
- **Resolution**: Replace `client.post(url, data=dict, content_type='application/json')` with `client.post(url, data=dict, format='json')` in all DRF `APIClient` tests. The `format='json'` kwarg sets the content type AND JSON-encodes the body in one step.
- **Files Affected**: `backend/content/tests/views/test_diagnostic_email_attachment.py` (and any test file using manual `content_type='application/json'`)
- **Lesson**: In DRF `APIClient` tests, always use `format='json'` for JSON payloads — never `content_type='application/json'` with a `dict`. The `format` kwarg is the canonical DRF approach.
### [ERR-009] Documents tab hidden for sent proposals and contract actions enabled too early
- **Date**: 2026-04-22
- **Context**: Proposal admin detail only showed the `Documentos` tab for `negotiating/accepted/rejected`, while the intended flow needs it from `sent` onward
- **Root Cause**: Frontend tab visibility was gated by a narrow status list, and the contract row did not distinguish between `sent/viewed` and `negotiating`
- **Resolution**: Show the tab for every non-`draft` proposal and disable contract actions in `sent/viewed` with a tooltip until the proposal reaches `negotiating`
- **Files Affected**: `frontend/pages/panel/proposals/[id]/edit.vue`, `frontend/components/BusinessProposal/admin/ProposalDocumentsTab.vue`, `frontend/e2e/admin/admin-proposal-contract-generate.spec.js`

### [ERR-010] FolderSidebar didn't show new folders until reload
- **Date**: 2026-05-04
- **Context**: On `/panel/documents`, creating a folder via `FolderManagerModal` persisted the folder in backend and updated the modal's list, but `FolderSidebar` only showed the new folder after a full page reload. Same staleness affected rename/delete/document-count after move.
- **Root Cause**: `frontend/pages/panel/documents/index.vue:handleFoldersChanged` only called `documentStore.fetchDocuments()`. `folderStore.createFolder` mutates `this.folders.push(...)` in place; templates reading `folderStore.folders` directly re-rendered, but `FolderSidebar`'s reference-based watcher `watch(() => props.folders, ...)` never re-fired because the array reference didn't change. Its `localFolders` mirror (used by the draggable list) stayed stale.
- **Resolution**: `handleFoldersChanged` now refreshes `folderStore.fetchFolders()` in parallel with `documentStore.fetchDocuments()` (matching `handleMoved`). The fetch reassigns `this.folders = response.data`, changing the reference and re-triggering the watcher.
- **Files Affected**: `frontend/pages/panel/documents/index.vue`
- **Lesson**: When passing a Pinia state array to a child via prop and the child uses `watch(() => props.list, ...)` (no `deep`), parent CRUD handlers must call `store.fetchX()` to swap the reference. See `lessons-learned.md` § 12 "Reference-based prop watchers" for the rule.

### [ERR-011] Deleting a folder with documents silently orphaned them
- **Date**: 2026-05-04
- **Context**: Admins could delete a folder from `FolderManagerModal` even when it contained documents. The DB FK with `on_delete=SET_NULL` left those documents in "Sin carpeta" without a confirmation that explained the side effect, making the action feel destructive and lossy.
- **Root Cause**: Product rule was missing — `delete_document_folder` accepted DELETE unconditionally; the modal warning said "quedarán sin carpeta" but the user expected the operation to be blocked.
- **Resolution**: Backend now returns **HTTP 409** with `{ detail, document_count }` when `folder.documents.exists()`. Modal shows an amber blocking warning ("No se puede eliminar… Primero mueve o elimina sus N documento(s)") with no destructive button when `document_count > 0`. Empty-folder deletion still works (204). DB-level `SET_NULL` is preserved as a safety net for admin/shell removals.
- **Files Affected**: `backend/content/views/document_folder.py:delete_document_folder`, `frontend/components/panel/documents/FolderManagerModal.vue` (computed `deleteVariant`).
- **Lesson**: When the DB cascade and the user expectation differ, encode the user expectation at the API layer — DB constraints are a safety net, not the contract.

### [ERR-012] "Enviar al cliente" reported success while the email had failed silently
- **Date**: 2026-05-04
- **Context**: Admins moved a proposal from `draft` to `sent` (button "Enviar al Cliente" or inline status dropdown) and the panel showed a generic success toast, but the client never received the email. There was no visible error and no way to know the send had failed.
- **Root Cause**: Two compounding issues:
  1. `ProposalEmailService.send_proposal_to_client` returned `bool` and `_send_initial_email` swallowed every failure path (placeholder email, disabled template, render/SMTP exception) into `logger.exception` without propagating to the caller. The `/proposals/<id>/send/` view always returned 200 + serialized proposal regardless of whether the email was actually dispatched.
  2. `update_proposal_status` (the inline dropdown endpoint) only changed the `status` field for the `draft → sent` transition; it never invoked the email service, so moving a proposal to `sent` from the table dropdown never sent a client email at all.
- **Resolution**:
  1. `send_proposal_to_client` now returns a structured result `{ ok, reason, detail }` (`reason ∈ {sent, placeholder_email, template_disabled, send_failed, unexpected_error}`) constructed via the local `_delivery()` helper. `ProposalService.send_proposal`, `resend_proposal`, and `_send_initial_email` propagate this dict.
  2. The three admin views (`send_proposal`, `update_proposal_status`, `resend_proposal`) attach `email_delivery` to the response payload via the new `_proposal_admin_response()` helper. `update_proposal_status` now delegates `draft → sent` to `ProposalService.send_proposal` (defense-in-depth so the dropdown can never silently mark a proposal as `sent` without dispatching the email).
  3. Frontend store actions (`sendProposal`, `updateProposalStatus`, `resendProposal`) propagate `email_delivery` to callers; `pages/panel/proposals/index.vue` shows a red toast with `email_delivery.detail || email_delivery.reason` when `ok === false` instead of a generic success.
- **Files Affected**: `backend/content/services/proposal_email_service.py`, `backend/content/services/proposal_service.py`, `backend/content/views/proposal.py`, `frontend/stores/proposals.js`, `frontend/pages/panel/proposals/index.vue`.
- **Lesson**: Side-effect operations (email, push, webhook) must surface their result to the caller as structured data, not as a silently-logged bool. If a status change and a side-effect both happen in the same endpoint, return both outcomes (e.g. `{ status: 'sent', email_delivery: { ok: false, reason: 'placeholder_email' } }`) so the UI can be honest. Never have two endpoints with overlapping behavior diverge — if one path triggers a side effect and another doesn't, the panel can silently bypass the side effect.

### [ERR-013] Expired proposals could not be re-saved and stayed expired even after extending the date
- **Date**: 2026-05-04
- **Context**: An admin opened a proposal in `expired` status to fix it: editing any field via the form (PATCH `/proposals/:id/update/`) or re-importing JSON (PUT `/proposals/:id/update-from-json/`) failed with `"Expiration date must be in the future."` even when the admin was not changing `expires_at` at all. When they did change the date to a future value, the proposal was saved but `status` stayed `expired` because nothing recomputed it; the admin panel kept showing the proposal as expired forever.
- **Root Cause**: Two compounding issues:
  1. Both `ProposalCreateUpdateSerializer.validate_expires_at` and `ProposalFromJSONSerializer.validate_expires_at` rejected any `value < timezone.now()` unconditionally. On an expired proposal, the form pre-fills `expires_at` with the (already past) stored value; submitting it back — even with no change — tripped the validator. Same for the JSON path: the exported JSON carried the past `expires_at`, so re-importing the same payload was blocked.
  2. Neither `update_proposal` nor `update_proposal_from_json` recomputed `status` after `expires_at` changed. The model's `is_expired` property returns `True` whenever `status == 'expired'` (regardless of date), so once the cron or the public view persisted `'expired'`, only an explicit status change could undo it — and `'expired'` was not in `ALLOWED_TRANSITIONS` as a manual source state.
- **Resolution**:
  1. Both validators now allow the value through unchanged. `ProposalCreateUpdateSerializer.validate_expires_at` reads `self.instance.expires_at`; `ProposalFromJSONSerializer.validate_expires_at` reads `self.context['proposal'].expires_at` (the JSON view passes `context={'proposal': proposal}` when instantiating the serializer). The future-only check still fires when the value is genuinely changing.
  2. New `ProposalService.reopen_if_unexpired(proposal, *, old_status)` mutates `proposal.status` in memory only when `old_status == EXPIRED` and the new `expires_at > now()` — reverting to `viewed` if `proposal.view_count > 0`, else `sent`. `update_proposal_from_json` calls it before `proposal.save()` so the status mutation rides the single save; `update_proposal` calls it after `serializer.save()` and persists with `update_fields=['status']` only when the helper fires. Both views log the auto-reopen via `ProposalChangeLog` with description `'Auto-reopened from expired after expires_at moved to the future (<old> → <new>).'`.
- **Files Affected**: `backend/content/serializers/proposal.py` (both `validate_expires_at` methods), `backend/content/services/proposal_service.py` (new `reopen_if_unexpired`), `backend/content/views/proposal.py` (`update_proposal_from_json` passes context + calls helper before save; `update_proposal` calls helper after `serializer.save()` and reuses tracked-fields loop with description override).
- **Test coverage**: 5 new pytest cases in `backend/content/tests/views/test_proposal_views.py` — `test_update_succeeds_for_expired_proposal_when_expires_at_unchanged`, `test_update_reopens_status_when_expires_at_moved_to_future_no_views`, `test_update_reopens_to_viewed_when_proposal_was_visited`, `test_update_from_json_succeeds_for_expired_proposal_when_expires_at_unchanged`, `test_update_from_json_reopens_status_when_expires_at_moved_to_future`.
- **Lesson**: A serializer validator that compares against an absolute boundary (`< now()`, `> max`, etc.) must skip the check when the new value equals the bound instance's existing value — otherwise the "edit other fields without touching this one" path becomes impossible the moment the existing value drifts past the boundary. Use `self.instance.<field>` for `ModelSerializer` and pass the bound object via `context=` for plain `Serializer`. And when a status field is computed from another field's state (here: `is_expired` from `expires_at`), every mutation of the source field must go through the same recomputation path — otherwise the system can persist a state inconsistent with its own predicate.

### [ERR-014] Migration backfill silently no-op'd because `ProposalDefaultConfig` had stale `sections_json`
- **Date**: 2026-05-05
- **Context**: Migration `0118_roi_projection_section.py` ran successfully on prod (the `AlterField` step took effect, the `RunPython` step reported no errors), but **zero `roi_projection` rows were created** across the 32 existing proposals. The order-bump step (every `order >= 4` shifted `+1`) DID run, leaving a permanent gap at `order=4`.
- **Root Cause**: The backfill function called `ProposalService.get_default_sections(language)` to look up the template for the new section, then `_defaults_index(language).get('roi_projection')` to fetch the row's content. `get_default_sections` reads from `ProposalDefaultConfig` first (DB-backed override) and falls back to the hardcoded `DEFAULT_SECTIONS` list only when no DB row exists. In prod, the `ProposalDefaultConfig (es)` row had been edited via `/panel/defaults` long ago and stored a frozen 16-section list with no `roi_projection`. So the lookup returned `None`, and the migration `continue`d past every proposal without creating rows.
- **Resolution**:
  1. Recovery via Django shell, importing the canonical lists directly from the source module rather than going through the service:
     ```python
     from content.services.proposal_service import DEFAULT_SECTIONS, DEFAULT_SECTIONS_EN
     def cfg_for(lang): return next((s for s in (DEFAULT_SECTIONS_EN if lang == 'en' else DEFAULT_SECTIONS) if s['section_type'] == 'roi_projection'), None)
     for p in BusinessProposal.objects.all().only('id', 'language'):
         if not ProposalSection.objects.filter(proposal_id=p.id, section_type='roi_projection').exists():
             ProposalSection.objects.create(proposal_id=p.id, section_type='roi_projection',
                                            order=4, is_enabled=False,
                                            content_json=deepcopy(cfg_for(p.language or 'es')['content_json']),
                                            title=cfg_for(p.language or 'es')['title'])
     ```
  2. Updated `ProposalDefaultConfig.sections_json` for each language row to include `roi_projection` so future proposals created via the panel pick it up automatically.
- **Files Affected**: `backend/content/migrations/0118_roi_projection_section.py` (the migration itself was idempotent so no fix to ship — the lesson is for the *next* migration). Lessons captured in `docs/methodology/lessons-learned.md` §18.
- **Test coverage**: New `backend/content/tests/test_roi_projection.py` asserts ES + EN defaults include the section at `order=4` (catches the source list being correct but does NOT exercise the migration's DB-override interaction — that path is hard to test without a real `ProposalDefaultConfig` fixture).
- **Lesson**: Inside a migration, if you need a section/template definition, import the canonical hardcoded list directly (`from content.services.proposal_service import DEFAULT_SECTIONS`) rather than going through a service method that may be reading from a DB-backed override. The service layer's "DB first, fallback to hardcoded" behavior is correct for the runtime app but actively wrong inside a migration — the migration's *purpose* is to update both surfaces (data rows + DB config). After the schema change runs, **also update the `ProposalDefaultConfig.sections_json` rows** so the runtime path stays in sync with the new hardcoded list.
