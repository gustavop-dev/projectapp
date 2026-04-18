# Active Context — ProjectApp

## Current State

ProjectApp is in **production** at projectapp.co. Core features are deployed. Active branch: **`main`**. The Web App Diagnostic module was rewritten on Apr 16, 2026 to the same JSON-section architecture used by `BusinessProposal` — 3 markdown documents replaced by 8 `DiagnosticSection` rows with typed `content_json`, 5 new admin tabs (Sections, Plantillas, Prompt, Activity, Analytics), a fully restructured public page, and per-section + per-session analytics tracking. Earlier Apr 9 work (Project Schedule Notifications, Real Client Entity for Proposals with 69 new tests, Codex-first methodology) remains in place. Codex-first methodology is documented via `AGENTS.md` scopes, native repo skills in `.agents/skills/`, and `.codex/config.toml`, with `CLAUDE.md`, `.claude/`, and `.windsurf/` retained only as compatibility surfaces. The Document System PDF work on branch `generate-pdf-with-template` remains the main unfinished documentation-visible feature area.

---

## Recent Focus Areas

- **Diagnostic Defaults — Per-Language Singleton Config** (Apr 18, 2026):
  - **Motivation**: parity with `/panel/proposals/defaults/`. Diagnostics now created from `panel/diagnostics/create.vue` had hardcoded payment terms (`{"initial_pct": 40, "final_pct": 60}` only as `help_text`, actually empty `{}` in practice), no admin-controllable default currency/investment/duration, and no editor over the section seed shipped from `content/seeds/diagnostic_template.py`. The product pricing default also flipped to **60% inicial / 40% final** — encoded in the new model defaults.
  - **Backend model**: new `DiagnosticDefaultConfig` (`backend/content/models/diagnostic_default_config.py`) — singleton per `language` (es/en) holding `sections_json`, `payment_initial_pct=60`, `payment_final_pct=40`, `default_currency` (COP/USD), `default_investment_amount` (decimal, nullable), `default_duration_label`, `expiration_days=21`, `reminder_days=7`, `urgency_reminder_days=14`. `clean()` enforces `payment_initial_pct + payment_final_pct == 100`. Registered in `content/models/__init__.py`. Migration `0101_diagnostic_default_config.py`.
  - **Serializer** (`backend/content/serializers/diagnostic.py:DiagnosticDefaultConfigSerializer`): mirrors the proposal pattern but trimmed — language and currency are validated by the model's `choices` (no redundant `validate_language`/`validate_default_currency`). Custom `validate_sections_json` ensures list of `{section_type, title, order, content_json}` dicts and normalizes missing/non-dict `content_json` to `{}`. Cross-field `validate()` re-checks the payment sum (catches PUT-time mismatches).
  - **Service helpers** (`backend/content/services/diagnostic_service.py`): added module-level constants `DEFAULT_PAYMENT_INITIAL_PCT=60`, `DEFAULT_PAYMENT_FINAL_PCT=40`, `DEFAULT_EXPIRATION_DAYS=21`, `DEFAULT_REMINDER_DAYS=7`, `DEFAULT_URGENCY_REMINDER_DAYS=14`; new `get_default_config(lang)`, `get_default_section_specs(lang)`, `get_hardcoded_section_specs()`. `seed_sections(diagnostic, config=None)` now accepts a pre-fetched config to avoid a duplicate query, and filters out specs whose `section_type` isn't a valid choice. `create_diagnostic` calls `get_default_config(language)` once, applies `payment_terms`/`currency`/`investment_amount`/`duration_label` from it (or the constants when no row exists), then passes the same config to `seed_sections` — single DB read per create.
  - **Views & URLs**: 2 new admin endpoints (`backend/content/views/diagnostic.py`): `GET/PUT /api/diagnostics/defaults/?lang=` (returns DB config or hardcoded fallback wrapped in the same shape; PUT upserts and preserves existing `sections_json` when the payload omits it) and `POST /api/diagnostics/defaults/reset/` (deletes the row for that language). Routes added under the diagnostics block in `content/urls.py`.
  - **Frontend page** (`frontend/pages/panel/diagnostics/defaults.vue`): 5 tabs — **General** (idioma, moneda, inversión, duración, % pagos con auto-sync a 100, días de recordatorio/urgencia/expiración, botón Restablecer con `useConfirmModal`), **Secciones** (lista read-only de las 8 secciones del seed activo), **Plantillas de Email** (informativo, link a `/panel/email-templates`), **Prompt** (placeholder — todavía no hay defaults compartidos), **JSON** (vista cruda para debugging). Reusa `ResponsiveTabs`, `ConfirmModal`, `usePanelToast` (no inline `setTimeout` que se filtraría al desmontar) y `<PanelToast />`. `applyConfig(data)` actualiza `rawConfig` + `sectionsList` + `generalForm` desde la respuesta del backend; `handleSaveGeneral` no recarga del backend tras guardar — usa `result.data` directo, ahorrando una query.
  - **Store** (`frontend/stores/diagnostics.js`): añadidos imports `put_request` + actions `fetchDiagnosticDefaults(lang)`, `saveDiagnosticDefaults(lang, sectionsJson, generalConfig)` (whitelist explícito de campos; ignora claves extra), `resetDiagnosticDefaults(lang)`. Mismo patrón Options API de `proposals.js:saveProposalDefaults`/`resetProposalDefaults`.
  - **Nav**: `frontend/pages/panel/diagnostics/index.vue` ahora muestra un botón "Valores por Defecto" en el header (estilo idéntico al de `/panel/proposals/`).
  - **Bug colateral arreglado**: una edición externa había dejado `penal_clause_value = serializers.CharField(...)` dentro de `DiagnosticDefaultConfigSerializer`. Movido a `ConfidentialityParamsSerializer` donde corresponde (placeholder del NDA; ya consumido por `confidentiality_pdf_service.py`).
  - **Tests**: backend nuevos `test_diagnostic_default_config.py` (8) + `test_diagnostic_defaults_views.py` (16) — 24 verdes; las 29 tests del módulo `test_web_app_diagnostic.py` y 11 de `test_diagnostic_attachments_and_emails.py` siguen verdes (pasaron por el cambio de `seed_sections`/`create_diagnostic`). Frontend: 6 tests añadidos al final de `frontend/test/stores/diagnostics.test.js` para las 3 actions; `put_request` añadido al mock del módulo. Jest no se ejecutó localmente (binario ausente en `node_modules`), correr con `npm --prefix frontend install && npm --prefix frontend test -- test/stores/diagnostics.test.js` cuando se necesite.
  - **No tocado** (a propósito): la página `panel/diagnostics/[id]/edit.vue` (los pagos por diagnóstico se editan ahí independiente del default), `panel/diagnostics/create.vue` (el backend ya aplica los defaults en `create_diagnostic`), las plantillas de email (`/panel/email-templates` ya las gestiona).
  - **Ops**: `python manage.py migrate content 0101` aplica la nueva tabla en producción. Sin cambios de config ni nuevas dependencias.

- **Diagnostic Edit — "Det. técnico" Tab Removed** (Apr 18, 2026):
  - **Motivation**: the consolidated `technical` tab (Pricing + Radiografía sub-tabs) no longer matches the real workflow. Pricing fields already live in the **General** tab; the Radiografía is one of the 8 section rows and is edited from **Secciones**. The actual diagnostic deliverable is produced offline — the team downloads the three markdown documents (diagnóstico aplicación, diagnóstico técnico, anexo), completes them, and sends them to the client from the **Correos** tab. The tab had nothing left to drive.
  - **Frontend change** (`frontend/pages/panel/diagnostics/[id]/edit.vue`): removed the `technical` entry from the `tabs` computed, the entire `<section v-if="activeTab === 'technical'">` template (outer visibility checkbox + Pricing/Radiografía sub-tab pills + `DiagnosticPricingForm`/`DiagnosticRadiographyForm`), their imports, and the matching script state (`technicalSubTab`, `formPricing`, `formRadiography`, `technicalSection` computed, `toggleTechnicalSectionEnabled`, `savePricing`, `saveRadiography`). The `syncForms` wrapper became a no-op and was inlined — the `watch(() => store.current?.id, …)` now calls `syncFormGeneral` directly.
  - **Legacy deep-link redirects**: `LEGACY_TAB_REDIRECTS` updated from `{ pricing: 'technical', radiography: 'technical', … }` to `{ pricing: 'general', radiography: 'sections', technical: 'sections', … }`. Bookmarked URLs land on the new owner of that data.
  - **Checkbox alignment** (`frontend/components/WebAppDiagnostic/admin/DiagnosticSectionEditor.vue`): the "Activa en la vista pública" checkbox used to hang off the bottom of the 3-col meta grid (`flex items-end`). Switched to `flex items-center gap-3 sm:self-center` so the grid item aligns itself to the row's vertical center — no more hand-rolled `sm:pt-5` compensation for the sibling labels.
  - **Not touched** (preserved on purpose): the `radiography` JSONField on `WebAppDiagnostic`, `DiagnosticDetailSerializer.radiography`, the `radiography` seed in `diagnostic_template.py`, `build_render_context()` use, and the public `RadiographySection.vue`. All radiography data still round-trips through the sections array, just without the extra editor.
  - **No backend/API/test changes.** Stale memory entries (tab list in the "Web App Diagnostics — JSON-Section Rewrite" / "Diagnostic Edit — UI/UX Parity" sections below) describe the superseded 10-tab layout; keep them as historical context.

- **Diagnostic Edit — UI/UX Parity With Proposal Edit** (Apr 16, 2026):
  - **Motivation**: the diagnostic admin page had acquired all the functional tabs of the proposal editor but its shell had drifted (sticky header shape, tab order, card chrome, dark-mode palette). Admins switching between the two flows noticed the mismatch. This pass aligns only the shell — no functional or backend changes.
  - **Template rewrite** in `frontend/pages/panel/diagnostics/[id]/edit.vue`: back-link lifted above sticky header; sticky header now carries only title + investment + status (client name + public URL moved into the Resumen info grid); margin collapse unified to `-mx-4 sm:-mx-6 lg:-mx-8`; dark tokens migrated from `dark:bg-gray-*` / `dark:border-gray-*` to `dark:bg-esmerald[-dark]` / `dark:border-white/[0.06]` / `dark:text-green-light/60`.
  - **Tab order re-sequenced** for proposal-editor parity: `summary` → `emails` → `documents` → `pricing` → `radiography` → `sections` → `prompt` → `plantillas` → `activity` → `analytics`. Labels unchanged.
  - **Resumen restructured**: three separate `rounded-2xl` cards collapsed into a single `bg-gray-50 dark:bg-white/[0.03] rounded-xl` info grid (ID, URL pública with copy button using `DocumentDuplicateIcon`/`CheckIcon` heroicons, Cliente block with inline Cambiar form, Idioma, Inversión, Vistas, fechas). Actions promoted to a sticky bottom bar mirroring the proposal's pattern.
  - **Per-tab width wrappers**: `max-w-2xl` on summary/pricing/radiography; `max-w-4xl` on the rest. Pricing/Radiografía/Plantillas cards unified to `bg-white dark:bg-esmerald rounded-xl shadow-sm border border-gray-100 dark:border-white/[0.06] p-4 sm:p-8`.
  - **Timer-leak fix**: both `urlCopied` and `jsonCopied` `setTimeout`s are now captured in module-scoped bindings and cleared in `onUnmounted` alongside `toastTimer`. Preexisting `jsonCopied` leak was the same pattern — fixed while in the area. See updated lessons-learned entry.
  - **No schema/API/test changes**; out of scope by design. No new dependencies — `@heroicons/vue/24/outline` was already in use on the proposal page.

- **Web App Diagnostics — JSON-Section Rewrite** (Apr 16, 2026):
  - **Motivation**: standardize the diagnostic client-facing presentation against the proven `BusinessProposal` pattern — JSON-typed sections edited via per-type form components instead of the 3 legacy markdown documents. Added the missing companion tabs (*Prompt*, *Actividad*, *Analítica*) so the diagnostic panel matches the proposal panel surface for surface.
  - **Backend models added**: `DiagnosticSection` (FK to diagnostic, 8-entry `SectionType` enum: `purpose`/`radiography`/`categories`/`delivery_structure`/`executive_summary`/`cost`/`timeline`/`scope`; `content_json` JSONField; `order`; `is_enabled`; `visibility` enum `initial|final|both`; `unique_together=[diagnostic,section_type]`), `DiagnosticChangeLog` (audit trail mirroring `ProposalChangeLog` — `ChangeType` / `ActorType` enums, `created_at`), `DiagnosticViewEvent` (per-session page-load tracking, indexed by `session_id`), `DiagnosticSectionView` (per-section time spent during a view event, `entered_at` + `time_spent_seconds`). `DiagnosticDocument` **removed** — replaced by `DiagnosticSection`.
  - **Migrations**: `0094_diagnostic_sections.py` (schema for 4 new models), `0095_seed_diagnostic_sections.py` (data — seeds the 8 default sections for any pre-existing diagnostic using `content/seeds/diagnostic_template.py` with an inline fallback), `0096_drop_diagnostic_document.py` (deletes the legacy model; kept as a separate migration so rollback is clean). Legacy `.md` templates moved to `backend/content/templates/diagnostics/_legacy/`.
  - **Seed** (`backend/content/seeds/diagnostic_template.py`): `default_sections()` returns the 8-section payload with the 14 diagnostic categories (architecture, code_quality, ui_ux, database, security, performance, scalability, testing, maintainability, reliability, integrations, tech_currency, documentation, functional_capabilities), severity scale, radiography table, delivery structure blocks, cost/timeline/scope boilerplate — all derived from the retired markdown proposal.
  - **Service** (`backend/content/services/diagnostic_service.py`): `create_diagnostic()` uses `seed_sections()` with `bulk_create` (1 INSERT batched) instead of loading `.md`. `build_render_context()` retained as the shared variable map for section components (stack, entities, routes, etc.). New helpers: `reset_section()` restores a single section from seed, `log_change()` centralizes `DiagnosticChangeLog.objects.create` (called from status transitions, section edits, email sends, client responses), `visible_sections()` filters by `is_enabled` + `visibility ∈ {phase, 'both'}` where `phase = 'final' if final_sent_at else 'initial'`, `transition_status()` now also writes a `STATUS_CHANGE` log entry.
  - **Serializers** (`backend/content/serializers/diagnostic.py`): `DiagnosticSectionSerializer` (read + update), `DiagnosticChangeLogSerializer`, `DiagnosticDetailSerializer` exposes `sections` + `attachments` + `change_logs` + `render_context`, `PublicDiagnosticSerializer` ships `sections` + a **whitelisted** `render_context` (`PUBLIC_RENDER_CONTEXT_KEYS` frozenset — admin-only fields like `controllers_disconnected` / `routes_protected` stay off the wire). Both detail + public memoize `build_render_context` on the serializer instance via `_render_context_for()`. `get_change_logs` slices the prefetched list in Python (`list(qs)[:60]`) to preserve the `_admin_qs().prefetch_related('change_logs')` cache. `get_sections` also consumes via `list()` to reuse the prefetch.
  - **Views** (`backend/content/views/diagnostic.py`): Admin — added `list_diagnostic_sections`, `update_diagnostic_section`, `bulk_update_diagnostic_sections`, `reset_diagnostic_section`, `list_diagnostic_activity`, `create_diagnostic_activity`, `diagnostic_analytics` on top of the existing CRUD + send endpoints. `_send_and_transition` now returns `(ok, email_ok)` and the response body carries `email_ok` so the UI can surface silent email failures. Private `_client_ip` deduped — new `get_client_ip()` helper hoisted to `content/utils.py`. `_ensure_view_event()` extracted so `track_public_diagnostic` + `track_diagnostic_section_view` share the lookup-or-create path (avoids the duplicate-session-row race). Public — added `track_diagnostic_section_view` endpoint.
  - **URLs** (`content/urls.py`): 8 new patterns under `/api/diagnostics/<id>/` for sections/activity/analytics + 1 public `track-section/`. Legacy `/documents/<id>/update|restore/` routes removed.
  - **Admin UI** (`frontend/pages/panel/diagnostics/[id]/edit.vue`): tab list expanded from 6 to **10** — see parity re-order in the Apr 16 follow-up entry below. Legacy `DiagnosticDocumentEditor` deleted; the debounced save timer map now keys by `sectionId`. `resyncJsonBuffer()` guards against clobbering unsaved JSON edits when the user is actively typing in Plantillas.
  - **Admin components** (`frontend/components/WebAppDiagnostic/admin/`): `DiagnosticSectionEditor.vue` + 8 per-type forms under `admin/sections/` (`PurposeForm`, `RadiographyForm`, `CategoriesForm`, `DeliveryStructureForm`, `ExecutiveSummaryForm`, `CostForm`, `TimelineForm`, `ScopeForm`). Watchers key on `[section.id, section.section_type]` instead of deep watch to avoid clobbering in-flight keystrokes when the parent merges the debounced-save response. `DiagnosticPromptPanel.vue` uses the shared `~/components/panel/PromptSubTabsPanel.vue` with `useDiagnosticCommercialPrompt`/`useDiagnosticTechnicalPrompt` (both built on the new `usePromptState({storageKey, defaultPrompt})` factory in `frontend/composables/usePromptState.js` — same factory replaces the duplicated localStorage ceremony of `useSellerPrompt`/`useTechnicalPrompt`). `DiagnosticActivityTab.vue` renders a timeline + nota form. `DiagnosticAnalytics.vue` shows view KPIs, per-section heatbar, and lifecycle timestamps. `PromptEditor.vue` is the shared edit/copy/download/reset UI.
  - **Public components** (`frontend/components/WebAppDiagnostic/public/`): 8 section components (one per `section_type`) + a shared `SectionHeader.vue` so the `<div flex items-baseline><span>{{index}}</span><h2>{{title}}</h2></div>` header stays in one place. Components receive `content`, `diagnostic`, `render_context` props.
  - **Public page** (`frontend/pages/diagnostic/[uuid]/index.vue`): section-based render with dynamic `<component :is>` dispatch via a `COMPONENTS` map, tab nav, prev/next controls, accept/reject footer. Session analytics: `generateSessionId()` on mount → `store.trackView(uuid, sessionId)` → per-section dwell timer flushed on section change; `onBeforeUnmount` uses `navigator.sendBeacon` so the final row survives tab unload (fetch fallback when beacon unavailable).
  - **Store** (`frontend/stores/diagnostics.js`): added `updateSection`, `bulkUpdateSections`, `resetSection`, `fetchActivity`, `logActivity`, `fetchAnalytics`, `trackSectionView` actions. Getters: `enabledSections`, `sectionsByPhase(phase)`. Legacy `updateDocument`/`restoreDocument`/`visibleDocuments` removed. `trackView` now sends `session_id`.
  - **Shared constants** (`frontend/stores/diagnostics_constants.js`): `SECTION_VISIBILITY`, `VISIBILITY_OPTIONS`, `SEVERITY_LEVELS`, `SEVERITY_LEVEL_CLASSES`, `severityLevelClass()`, `ACTIVITY_CHANGE_TYPES` — single source of truth used by the admin forms, the public `CategoriesSection`, and `DiagnosticActivityTab`. `arrToText`/`textToArr` re-imported from `frontend/components/BusinessProposal/admin/sectionEditorUtils.js` (no duplication).
  - **Prompt defaults** (`frontend/composables/useDiagnosticPrompt.js`): two diagnostic-specific prompts — commercial (fills the 8-section JSON narrative) + technical (fills the `categories` section with per-category findings/recommendations at the 4 severity levels).
  - **Dropped legacy**: `DiagnosticDocument` model + `DiagnosticDocumentEditor.vue` + `DiagnosticDocumentViewer.vue` + `_load_template`/`render_document`/`restore_document_from_template`/`visible_documents` service helpers. The 3 `.md` templates live under `templates/diagnostics/_legacy/` for reference only; nothing imports them.
  - **Tests (all green)**:
    - Backend 29: 18 in `test_web_app_diagnostic.py` (seed creates 8 sections, 14 categories seeded, reset_section restores default, status transition + change log entry, `visible_sections` phase filtering, section update + bulk update, activity log API, track-section view records time, analytics aggregate) + 11 in `test_diagnostic_attachments_and_emails.py` (unchanged — attachments + composer).
    - Frontend 41: 31 in `test/stores/diagnostics.test.js` (state/getters/fetchAll/detail/CRUD/update+bulk+reset sections/activity/analytics/transitions/public+track+trackSection) + 10 in `test/components/diagnosticSectionEditorUtils.test.js` (JSON↔form roundtrip per section_type).
  - **Ops**: `python manage.py migrate content 0096` in production applies the 3 new migrations. No config changes. Legacy `.md` files stay in-tree for history but are not loaded at runtime.

- **Proposal Admin & Public — 4 UX Improvements** (Apr 15, 2026):
  - **Expiry days input** (create + edit proposal pages): Number input placed inline beside the `datetime-local` field. Bidirectionally synced via two `watch()` calls — datetime change → days update; days change → date update while **preserving the existing time component** (`form.expires_at.slice(11, 16)`) so a custom hour is not overwritten when only the day count changes. Helpers: `getExpiryDaysFromStr()` in both pages; `create.vue` reuses existing `pad` + `buildDefaultExpiryStr`; `edit.vue` adds `padDate` + `DEFAULT_EXPIRY_DAYS`. Days watcher in `create.vue` also syncs `jsonForm.expires_at` (consistent with the existing cross-mode sync comment at line 1021). Timer stacking in `edit.vue` prevented via `updateMsgTimer` ref + `clearTimeout`.
  - **Smooth back-to-gateway transition** (`proposal/[uuid]/index.vue`): `handleBackToGateway()` now triggers the existing `switch-mode-overlay` `<Transition>` with `switchOverlayMode = 'gateway'` before resetting state. Overlay template gained a 4th case: grid icon, "Seleccionar vista" / "Select view" heading, bilingual subtitle. Timing mirrors `handleViewModeSelect`: 1 s hold → state reset + 1.2 s overlay hide.
  - **`@temp.example.com` email bypass** (`backend/content/utils.py`): `validate_email_domain_mx()` now short-circuits with `True` when `domain == 'temp.example.com'`, before any DNS lookup. `_PLACEHOLDER_EMAIL_DOMAIN = 'temp.example.com'` constant is local to `utils.py` (avoids cross-app import). `jsonForm.client_email` default in `create.vue` changed from `''` to `'usuario@temp.example.com'` so the JSON-import form is pre-filled with a valid placeholder address.
  - **Save toast notification** (`edit.vue`): Inline `updateMsg` div (inside the form, often scrolled away) replaced with a `<Teleport to="body">` toast fixed bottom-right. Uses Tailwind `<Transition>` enter/leave classes. Green = success, red = error; auto-dismisses in 5 s; `clearTimeout` + `updateMsgTimer` ref prevents timer stacking on rapid saves; manual ✕ button for immediate dismiss.

- **Admin Panel — Internal Kanban Task Board** (Apr 15, 2026):
  - **Backend model**: `backend/content/models/task.py` — `Task` with `Status` / `Priority` TextChoices (todo/in_progress/blocked/done; low/medium/high), `assignee` FK (SET_NULL to `AUTH_USER_MODEL`), `due_date`, `position` (ordering within column), `created_at`, `updated_at`. Migration `0087_task.py` (manual, no venv available). Registered in `content/models/__init__.py`.
  - **Serializers**: `TaskListSerializer` — read-side with `assignee_name` (`get_full_name() or username`) and `is_overdue` (reads `today` from serializer context — computed once per request via `_serializer_context()`). `TaskCreateUpdateSerializer` — write-side, `assignee_id` PrimaryKeyRelatedField.
  - **Views** (`backend/content/views/task.py`): `_next_position(status_value, exclude_pk=None)` helper (used by both create + update); `_serializer_context()` (hoists `timezone.localdate()` once per request); `_grouped_tasks()` (always returns all 4 status keys via `select_related('assignee')`). FBVs: `list_tasks` (GET), `create_task` (POST), `update_task` (PATCH — injects computed position into `serializer.validated_data` before single `serializer.save()` to eliminate double-save), `reorder_task` (PATCH `tasks/<id>/reorder/` — `transaction.atomic`, renumbers full column), `delete_task` (DELETE). 5 URL patterns in `content/urls.py`.
  - **Frontend store** (`frontend/stores/tasks.js`): Pinia Options API. State: `{ columns: {todo,in_progress,blocked,done}, isLoading, isUpdating, error }`. Actions: `fetchTasks`, `createTask` (appends optimistically), `updateTask` (replaces in-place, refetches only if status changed), `moveTask` (replaces board from API response; on error: fetches then sets `this.error` so fetchTasks reset doesn't overwrite it), `deleteTask`, `replaceTaskInPlace`.
  - **Components** (`frontend/components/Tasks/`): `TaskCard.vue` (priority badge gray/blue/red, due_date formatted `es-CO`, red if `is_overdue`); `TaskColumn.vue` (wraps vuedraggable with `group: { name:'tasks' }`, `handleChange(evt)` dispatches move for both `evt.added` and `evt.moved`); `TaskFormModal.vue` (create/edit, unified `buildForm()`, single dep watch on `modelValue`, emits `submit` + `delete`).
  - **Page** (`frontend/pages/panel/tareas/index.vue`): `definePageMeta({ layout:'admin', middleware:['admin-auth'] })`; 4 `TaskColumn` components in a responsive grid; `TaskFormModal`; delete gated through `useConfirmModal` + `ConfirmModal`.
  - **Navigation**: Added `{ id:'tasks', label:'Tareas', items:[{label:'Kanban', href:lp('/panel/tareas'), icon:'board'}] }` as first section in `frontend/config/panelNav.js`.
  - **Tests**: 11 backend (`test_task_views.py` — CRUD, non-admin 403, reorder within/across columns, position logic); 9 frontend unit (`tasks.test.js` — all actions + replaceTaskInPlace); 2 E2E (`admin-tasks-kanban.spec.js` — 4-column render + create, edit title). Flow tag `ADMIN_KANBAN_TASKS` registered in `flow-tags.js` + `flow-definitions.json`.
  - **Pending ops**: `python manage.py migrate` to apply `0087_task.py` in production.

- **Document System — Folders & Tags** (Apr 15, 2026):
  - **Backend models**: `DocumentFolder` (flat, slug auto-generated with collision avoidance, `order` sort field) and `DocumentTag` (M2M, 6 `Color` enum choices: gray/emerald/blue/yellow/red/purple). Both in `backend/content/models/`. `Document` model gained `folder` (FK `SET_NULL`) and `tags` (M2M). Migration `0086_document_folders_and_tags.py`.
  - **Serializers** (`backend/content/serializers/`): `DocumentFolderSerializer` reads `document_count` from `Count` annotation when available (N+1 free). `DocumentTagSerializer` (simple). `DocumentListSerializer` exposes `folder`, `folder_name`, `tag_details`. `DocumentCreateUpdateSerializer` accepts writable `folder_id` (PrimaryKeyRelatedField) and `tag_ids` (sets M2M via `.set()`). `DocumentFromMarkdownSerializer` extended with same fields.
  - **Views** (`backend/content/views/`): `document_folder.py` and `document_tag.py` — full CRUD FBV with `@api_view` + `IsAdminUser`. `list_document_folders` annotates `Count('documents')`. `list_documents` in `document.py` now accepts `?folder=<id|none>` and `?tags=<id,id,...>` (OR with `.distinct()`), prefetches tags and folder via `prefetch_related`/`select_related`.
  - **URLs**: 8 new patterns for `/api/document-folders/` and `/api/document-tags/` registered in `backend/content/urls.py`.
  - **Frontend stores**: `frontend/stores/document_folders.js` and `frontend/stores/document_tags.js` — Pinia Options API, snake_case filenames, CRUD with local mutation (no re-fetch after mutate). `frontend/stores/documents.js` extended: `activeFolderId`, `activeTagIds` state; `fetchDocuments(overrides={})` builds query params; `setFilters({folder,tags})`; `toggleTagFilter(tagId)`.
  - **Shared utility**: `frontend/utils/documentTagColors.js` — single source of truth for all tag Tailwind classes (`TAG_BADGE_CLASS`, `TAG_ACTIVE_CLASS`, `TAG_DOT_CLASS`, `TAG_IDLE_CHIP_CLASS`) + helper functions `tagBadgeClass()`, `tagActiveClass()`, `tagDotClass()`. Eliminates duplicate color maps that had existed across components.
  - **Components** (all new in `frontend/components/panel/documents/`): `FolderSidebar.vue` (pure `<script setup>`), `TagFilterChips.vue` (pure `<script setup>`), `TagSelector.vue` (v-model, pure `<script setup>`), `FolderManagerModal.vue`, `TagManagerModal.vue`.
  - **Pages updated**: `frontend/pages/panel/documents/index.vue` — 2-column layout (`lg:grid-cols-[240px_1fr]`), FolderSidebar left, tag chips + table right; table has folder badge on title and "Etiquetas" column. `create.vue` and `[id]/edit.vue` — folder dropdown + `<TagSelector>`, pre-populated from `?folder=` query param on create.
  - **Tests**: 25 backend tests across `test_document_folder_views.py` and `test_document_tag_views.py` (CRUD + SET_NULL + filter coverage). Frontend unit: `document_folders.test.js` (8), `document_tags.test.js` (8), `documents.test.js` extended (filter params, setFilters, toggleTagFilter). E2E: `e2e/admin/admin-document-folders.spec.js` (3 specs: sidebar filter, tag chip filter, "Sin carpeta" filter).
  - **Key patterns**: `?folder=none` → `filter(folder__isnull=True)`; M2M OR filter via `tags__id__in=[...].distinct()`; modal mutations emit `@changed` → parent only refreshes document list (folder/tag stores self-maintain local state after mutations).

- **Real Client Entity for Proposals** (Apr 9, 2026):
  - **Model**: New `BusinessProposal.client = ForeignKey('accounts.UserProfile', on_delete=PROTECT, limit_choices_to={'role':'client'}, null=True)`. Migration `0079_add_business_proposal_client_fk.py` (schema), `0080_backfill_proposal_clients.py` (data — dedups existing proposals by normalized email and creates UserProfile rows; empty emails get a placeholder via two-step save so the id can be embedded in `cliente_<id>@temp.example.com`). Legacy `client_name`/`client_email`/`client_phone` columns kept as **write-through snapshots**, never dropped.
  - **Service**: New `backend/accounts/services/proposal_client_service.py` — silent variant of `accounts/services/onboarding.py:create_client` that does NOT send invitation emails. Public API: `get_or_create_client_for_proposal(name, email, phone, company)`, `update_client_profile(profile, ...)` (cascades snapshots to all linked proposals via single bulk `BusinessProposal.objects.filter(client=profile).update(...)` and bumps `updated_at` manually because `.update()` bypasses `auto_now`), `delete_orphan_client(profile)` (3 guards: zero proposals + zero projects + zero deliverables), `sync_snapshot(proposal)`, `generate_placeholder_email(profile_id)`, `build_client_display_name(profile)` (shared with serializer). Refuses to hijack existing admin accounts when an email collision is detected.
  - **API**: 6 FBV endpoints under `proposals/client-profiles/*` — `list_proposal_clients` (with `?search=`, `?orphans=`, `?limit=`), `search_proposal_clients` (max 20 results, lightweight payload, AbortController-friendly), `retrieve_proposal_client` (with nested `proposals` history), `create_proposal_client` (standalone, no invite email), `update_proposal_client` (cascades snapshots), `delete_proposal_client` (returns 400 with `client_has_proposals` / `client_has_projects` codes when guard trips). All gated by `IsAdminUser`. Routes registered in `backend/content/urls.py`.
  - **Serializers**: `backend/content/serializers/proposal_clients.py` — `ProposalClientSerializer` (full, with annotated `total_proposals` + `is_orphan` + `is_email_placeholder`) and `ProposalClientSearchSerializer` (lightweight). `ProposalListSerializer` and `ProposalDetailSerializer` now expose nested `client = ProposalClientSerializer(read_only=True)`. `ProposalCreateUpdateSerializer` accepts write-only `client_id` (FK), `client_company`, `propagate_client_updates` and routes `create()`/`update()` through the service + `sync_snapshot`.
  - **Frontend**: `frontend/stores/proposalClients.js` — Pinia Options API with `fetchClients`, `searchClients` (uses `AbortController` + identity guard so rapid keystrokes don't race), `fetchClient`, `createClient`, `updateClient`, `deleteClient`. Getters: `orphanClients`, `activeClients`, `getClientById`. `frontend/components/ui/ClientAutocomplete.vue` — searchable dropdown with debounce 200ms (`useDebounceFn`), keyboard navigation, click-outside via `onClickOutside` from `@vueuse/core` (auto-cleanup on unmount), placeholder badge, "Crear nuevo" inline footer. `frontend/pages/panel/clients/index.vue` rewritten — tabs (Todos / Activos / Huérfanos), "+ Nuevo cliente" modal, trash icon visible only on orphans wired through `requestConfirm`, lazy-loaded proposals on row expand. `frontend/pages/panel/proposals/[id]/edit.vue` and `frontend/pages/panel/proposals/create.vue` use `<ClientAutocomplete>` + snapshot fields + propagate checkbox; the edit page extracted `hydrateFormFromProposal()` helper to dedup `onMounted` and `refreshData`. `frontend/stores/services/request_http.js` got an optional `config` arg on `get_request` (backward compatible) for AbortController support.
  - **Email automation skip**: `_is_unsendable_client_email(email)` helper in `proposal_email_service.py` returns `True` for empty strings and any address ending in `UserProfile.PLACEHOLDER_EMAIL_DOMAIN` (`@temp.example.com`, RFC 2606 reserved TLD). All **13 client-facing email methods** in `ProposalEmailService` (acceptance, finished, rejection, reminder, urgency, abandonment, investment-interest, scheduled-followup, negotiation-confirmation, documents, etc.) now exit early when the helper returns `True`. The 4 huey tasks in `content/tasks.py` (`send_proposal_reminder`, `send_urgency_reminder`, `send_rejection_reengagement`, `send_scheduled_followup`) use the same gate. Two candidate-selection querysets in `process_engagement_alerts` exclude placeholders via `.exclude(client_email__iendswith=UserProfile.PLACEHOLDER_EMAIL_DOMAIN)`.
  - **N+1 fixes**: `select_related('client__user')` added to `list_proposals` (admin dashboard hot path), `retrieve_proposal` (admin detail), `retrieve_public_proposal` (client view), and `retrieve_proposal_client` (the new client detail with nested proposals).
  - **Bug fix**: `respond_to_proposal` in `backend/content/views/proposal.py` was missing the `elif action == 'accepted':` branch — clients accepting a proposal never received the confirmation email even though the docstring promised it. See `error-documentation.md` ERR-007 for the full incident.
  - **Tests**: 15 (`accounts/tests/test_proposal_client_service.py`) + 19 (`content/tests/views/test_proposal_clients_views.py`) + 10 (`content/tests/services/test_proposal_email_service_placeholder_skip.py`) backend + 25 (`frontend/test/stores/proposalClients.test.js`) frontend = **69 new tests**, all green. Ran the full proposal regression slice afterwards (368 backend + 847 frontend tests) — zero regression.

- **Project Schedule Notifications (Cronograma)** (Apr 9, 2026):
  - New `ProposalProjectStage` child model on `BusinessProposal` (`backend/content/models/proposal_project_stage.py`) with `start_date`, `end_date`, `completed_at`, `warning_sent_at`, `last_overdue_reminder_at`. Migration `0081`, backfill `0082`, change-type enum `0083`.
  - New `ProposalStageTracker` service (`backend/content/services/proposal_stage_tracker.py`) with `STAGE_DEFINITIONS` constant, `ensure_stages` / `get_or_create_stage` classmethods, `format_remaining_time(days)` ("hoy", "1 día", "1 semana 5 días", "2 semanas"), and `process(proposal)` decision logic
  - Daily Huey periodic task `notify_proposal_stage_deadlines` at `crontab(hour='13', minute='30')` = 08:30 Bogotá. Filters by stage existence + dates + not-completed (NOT by proposal status), with `prefetch_related('project_stages')`.
  - Two new internal-team email templates registered in `EmailTemplateRegistry`: `proposal_stage_warning_notification` (70% elapsed, sent once) + `proposal_stage_overdue_notification` (overdue, every 3 days while not completed). Both with HTML+TXT twins under `backend/content/templates/emails/`.
  - Send methods `send_stage_warning` / `send_stage_overdue` in `ProposalEmailService` share a private `_send_stage_notification` helper. They use `_get_notification_recipients()` (CSV via `NOTIFICATION_EMAIL`) and do NOT call `_log_email` — internal team notifications use `logger.info` only, matching the convention of `send_first_view_notification`, `send_comment_notification`, etc.
  - Admin UI: new "Cronograma" tab in proposal edit page (`frontend/pages/panel/proposals/[id]/edit.vue`), only visible when status is `accepted`/`finished`. Component: `frontend/components/BusinessProposal/admin/ProjectScheduleEditor.vue`. Composable: `frontend/composables/useStageStatus.js` (mirrors backend `format_remaining_time` + computes status badges in JS).
  - Onboarding hook: `_ensure_project_stages` in `proposal_platform_onboarding.py` calls `ProposalStageTracker.ensure_stages` so accepted proposals get two empty stage rows automatically.
  - 2 new endpoints: `PUT /api/proposals/<id>/stages/<stage_key>/` and `POST /api/proposals/<id>/stages/<stage_key>/complete/`.
  - `ProposalDetailSerializer.get_project_stages` is gated by `is_admin` context — internal-only data is never exposed to public proposal views.
  - Tests: 26 tracker + 9 email service + 13 view + 5 task + 2 onboarding (backend); 11 store + 22 composable + 16 component (frontend); 6 E2E (`admin-proposal-project-schedule.spec.js` registered in `flow-definitions.json` + `USER_FLOW_MAP.md`).
  - Bogotá time helpers added to `backend/content/utils.py`: `now_bogota()`, `today_bogota()`, `to_bogota_date(dt)`. `format_bogota_date()` now accepts both `date` and `datetime`.
  - **Ops action pending**: set `NOTIFICATION_EMAIL=team@projectapp.co,carlos18bp@gmail.com` in production environment. This is a single env var change; affects all internal team notifications, not just stage alerts.

- **Codex Native Runtime Cleanup** (Apr 9, 2026):
  - Replaced the plugin-based Codex runtime with native repo skills in `.agents/skills/`
  - Added project-scoped Codex config in `.codex/config.toml`
  - Rewrote `AGENTS.md` / `CLAUDE.md` scopes to match the actual repo conventions (FBV backend, JS-first Nuxt frontend, Pinia Options API, split HTTP clients)
  - Kept `debug` canonical and `debugme` as the only legacy alias in the native skill inventory
  - Rewrote Codex setup docs around the native runtime and marked Claude-only guidance as compatibility documentation

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
   - Services: `document_pdf_service.py`, `markdown_parser.py`, `pdf_utils.py` (shared PDF utilities)
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
7. **E2E coverage audit & remediation** — current workspace carries 129 E2E spec files; Quality gate: **100/100** with **0 warnings**
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
- **Pinia in-place mutation** — store helpers that update nested arrays must mutate in place (`this.currentProposal.sections[idx] = response.data`), never spread + reassign the parent. Components reading via `computed(() => store.currentProposal)` don't reliably pick up the spread+reassign combination but DO pick up in-place index assignments. See `_mergeProjectStage` / `updateSection` / `applySync` / `reorderSections` in `frontend/stores/proposals.js`.
- **Two Django apps** — `content` (proposals, blog, portfolio, contact) + `accounts` (platform auth, projects, kanban)
- **Hybrid rendering** — SSR for SEO pages, SPA for admin, proposal, and platform views
- **Dual auth strategy** — Session/CSRF for `/panel/` admin; JWT (SimpleJWT) for `/platform/`
- **Stage tracking is admin-managed** — `ProposalProjectStage.start_date` / `end_date` are set manually from the Cronograma tab. We do NOT auto-derive them by parsing the free-text `timeline` proposal section ("1 semana", "2 weeks") because that text is sales/marketing copy, not project execution data.
- **Internal team notifications use `_get_notification_recipients()` only** — recipient list lives in the `NOTIFICATION_EMAIL` env var (comma-separated). Do NOT add per-feature recipient settings. Internal sends are NOT logged to `EmailLog` (that table is for client-facing single-recipient sends).
- **Internal-only model fields must be gated by `is_admin` in shared serializers** — when a model docstring says "internal-only" (e.g., `ProposalProjectStage`), the field on `ProposalDetailSerializer` must be a `SerializerMethodField` returning `[]` for non-admin context, never a nested `read_only=True` model serializer.

---

## Development Environment

- **Backend**: Django 5 + DRF, SQLite (dev) / MySQL (prod), Huey immediate mode
- **Frontend**: Nuxt 3 + Pinia + TailwindCSS, dev server on port 3001 (port 3000 occupied by kore_project Next.js)
- **Both servers** must run simultaneously for full functionality in development
- **Redis**: Required in production for Huey task queue

---

## Verified Codebase Metrics (April 18, 2026 — refreshed post-Diagnostic-Defaults)

| Metric | Count |
|--------|-------|
| Backend test files | 125 |
| Frontend unit tests | 77 |
| E2E spec files | 132 |
| Vue components | 135 |
| Pages | 69 |
| Pinia stores | 24 |
| Composables | 35 |
| Content model files | 30 |
| Accounts model classes | 21 |
| Accounts URL patterns | 65 |
| Content URL patterns | ~138 |
| Email templates | 61 (32 HTML + 29 TXT across `accounts` + `content`) |
| Content services | 19 |
| Accounts services | 11 |
| Content migrations | 101 |
| Quality gate score | 100/100 (0 errors, 2 warnings) |

---

## Next Steps

- **Apply pending migrations in production** — `python manage.py migrate` — required to activate the Kanban board (`0087_task.py`), the Web App Diagnostics module (`0090_web_app_diagnostic.py`), and the new Diagnostic Defaults table (`0101_diagnostic_default_config.py`).
- **Set `NOTIFICATION_EMAIL` in production env** to `team@projectapp.co,carlos18bp@gmail.com` so the new stage warning + overdue alerts reach the right inbox.
- Consider extending `ProposalStageTracker.STAGE_DEFINITIONS` beyond design + development (e.g., QA, Lanzamiento, Entrega Final) — the model + service already support N stages, only the catalog constant needs an update.
- Complete Document System PDF generation (branch `generate-pdf-with-template`): template rendering, preview, download flow — **folders & tags layer is now in place**
- Keep Codex docs, native repo skills, and compatibility mirrors synchronized when adding or renaming recurring workflows
- Add unit tests for `useProposalFilters.js` composable and `ProposalFilterPanel.vue` / `ProposalFilterTabs.vue` components
- Add E2E coverage for Contract System (ContractParamsModal, SendDocumentsModal admin workflows)
- Add E2E coverage for Platform Data Model page (`/platform/projects/[id]/data-model`)
- Add backend test coverage for contract/document services (`contract_pdf_service.py`, `technical_document_pdf.py`)
- ~~Fix 4 failing `usePlatformApi.test.js` tests~~ — all 56 tests pass (already resolved)
- **Deferred E2E:** `platform-verify-onboarding` — requires OTP test infrastructure (mock OTP delivery or test bypass)
- Add E2E coverage for new Platform modules (bug reports, change requests, deliverables, notifications, payments)
- Increase backend test coverage (target areas: services edge cases, accounts app edge cases)
- Increase frontend unit test coverage (target areas: remaining composables, components)
- Consider splitting the largest proposal/backend modules (`views/proposal.py`, `proposal_service.py`, `proposal_email_service.py`) now that the shared PDF helpers already live in `pdf_utils.py`
- Credential rotation for production secrets exposed in git history
- Explore API rate limiting for public endpoints
- Kill rogue `kore_project` Next.js server on port 3000 permanently (respawns from Windsurf terminal)
