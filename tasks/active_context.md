# Active Context — ProjectApp

## Current State

ProjectApp is in **production** at projectapp.co. Core features are deployed. Active branch: **`feat/platform-launch-and-email-improvements`**. The Project Schedule Notification feature (Cronograma) shipped on Apr 9, 2026 and passed the post-merge simplification pass. The Real Client Entity for Proposals feature (`BusinessProposal.client` FK to `accounts.UserProfile` + autocomplete + orphan management + placeholder email skip + the `respond_to_proposal` accepted-branch bug fix) also shipped on Apr 9, 2026 with 69 new tests green and zero regression in the existing proposal regression slices. Codex-first methodology is documented via `AGENTS.md` scopes, native repo skills in `.agents/skills/`, and `.codex/config.toml`, with `CLAUDE.md`, `.claude/`, and `.windsurf/` retained only as compatibility surfaces. The Document System PDF work on branch `generate-pdf-with-template` is still the main unfinished documentation-visible feature area.

---

## Recent Focus Areas

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

## Verified Codebase Metrics (April 15, 2026 — refreshed post-Kanban)

| Metric | Count |
|--------|-------|
| Backend test files | 124 |
| Frontend unit tests | 77 |
| E2E spec files | 132 |
| Vue components | 130 |
| Pages | 65 |
| Pinia stores | 23 |
| Composables | 35 |
| Content model files | 29 |
| Accounts model classes | 21 |
| Accounts URL patterns | 65 |
| Content URL patterns | 128 |
| Email templates | 57 (30 HTML + 27 TXT across `accounts` + `content`) |
| Content services | 17 |
| Accounts services | 11 |
| Content migrations | 87 |
| Quality gate score | 100/100 (0 errors, 2 warnings) |

---

## Next Steps

- **Apply `0087_task.py` migration in production** — `python manage.py migrate` — required before the Kanban board at `/panel/tareas` is usable.
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
