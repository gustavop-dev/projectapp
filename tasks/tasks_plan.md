# Task Plan — ProjectApp

## 1. Feature Status

| Feature | Status | Details |
|---------|--------|---------|
| Business Proposal — Core Models | ✅ Done | BusinessProposal, ProposalSection, ProposalAlert, RequirementGroup/Item |
| Business Proposal — Public View | ✅ Done | Fullscreen horizontal scroll, 12 section components, GSAP animations |
| Business Proposal — Admin CRUD | ✅ Done | Create, edit, send, duplicate, JSON import, section editor, defaults, alerts |
| Business Proposal — Email System | ✅ Done | 54 content email templates (27 HTML + 27 TXT), automated reminders, cooldown, pause, admin notifications |
| Business Proposal — Analytics | ✅ Done | View tracking, section time, heat score, session tracking, engagement signals |
| Business Proposal — PDF | ✅ Done | ReportLab generation, downloadable from proposal page |
| Business Proposal — Share Links | ✅ Done | UUID share links with independent tracking |
| Business Proposal — Investment Calculator | ✅ Done | Interactive modal for payment options |
| Business Proposal — Client Responses | ✅ Done | Accept, reject (with reason), negotiate |
| Business Proposal — Expiration | ✅ Done | Auto-expire via daily Huey cron task |
| Business Proposal — Change Log | ✅ Done | Full audit trail (20+ change types) |
| Business Proposal — Email Deliverability | ✅ Done | Dashboard with send/delivery/bounce rates |
| Business Proposal — Email Templates Editor | ✅ Done | View, edit, preview, reset email content |
| Business Proposal — Default Config | ✅ Done | Per-language default section templates |
| Business Proposal — Clients List | ✅ Done | Real `accounts.UserProfile` client entities power `/panel/clients/`, proposal autocomplete, orphan cleanup, and snapshot sync back to linked proposals |
| Portfolio Works — Public | ✅ Done | Listing and detail with bilingual structured JSON |
| Portfolio Works — Admin CRUD | ✅ Done | Create, edit, delete, duplicate, cover image upload, JSON import |
| Blog — Public | ✅ Done | Listing with featured hero, categories, pagination, detail with JSON/HTML |
| Blog — Admin CRUD | ✅ Done | Create, edit, delete, duplicate, cover image upload, calendar view, JSON import |
| Blog — Sitemap | ✅ Done | Sitemap data endpoint + XML rendering |
| Portfolio — Sitemap | ✅ Done | Sitemap data endpoint |
| Contact Form | ✅ Done | Public submission with budget ranges, email notification |
| Landing Pages (3) | ✅ Done | Web design, software, apps — with animations |
| Home Page | ✅ Done | Marketing page with GSAP animations |
| About Us Page | ✅ Done | Company information page |
| Internationalization (i18n) | ✅ Done | EN/ES with prefix routing, lazy loading, geo-detection |
| Admin Auth Middleware | ✅ Done | Session/CSRF check, redirect to Django admin login |
| CI/CD Pipeline | ✅ Done | GitHub Actions: pytest, Jest, Playwright (5 shards), quality gate |
| Codex Ecosystem Methodology | ✅ Done | Codex-first runtime documented and implemented: `AGENTS.md` hierarchy, native repo skills in `.agents/skills/`, project config in `.codex/config.toml`, canonical guide + quickstart, legacy compatibility notes |
| Deployment (Production) | ✅ Done | Gunicorn + Nginx + systemd, documented in deployment-guide.md |
| WhatsApp Notifications | ✅ Done | CallMeBot API integration |
| Database Backups | ✅ Done | django-dbbackup with rotation |
| Query Profiling (Silk) | ✅ Done | Optional, env-gated |
| Platform — Auth & Onboarding | ✅ Done | JWT login, OTP verify, complete-profile, middleware gating |
| Platform — Dashboard | ✅ Done | Admin KPI cards + recent clients; Client profile summary |
| Platform — Projects & Kanban | ✅ Done | Project CRUD, detail hub, 3-column kanban board, drag & drop, comments |
| Platform — Client Management | ✅ Done | Admin invite, list, detail, edit, deactivate, reactivate |
| Platform — Sidebar & Layout | ✅ Done | Collapsible sidebar, mobile drawer, theme toggle, role-based nav |
| Platform — E2E Coverage | ✅ Done | Platform flows are registered and covered across auth, dashboard, projects, kanban, clients, collection accounts, data model, notifications, payments, and related routes |
| Document System — Model + Admin CRUD | ✅ Done | `Document` model (uuid, title, slug, status, language, cover_type); panel pages (index, create, edit); `documents.js` store |
| Document System — Folders & Tags | ✅ Done | `DocumentFolder` + `DocumentTag` models (migration `0086`); CRUD FBV views + 8 URL patterns; `document_folders.js` + `document_tags.js` stores; `FolderSidebar`, `TagFilterChips`, `TagSelector`, `FolderManagerModal`, `TagManagerModal` components; `documentTagColors.js` shared util; `index.vue` 2-col layout + `create.vue`/`edit.vue` selectors; `?folder=<id|none>` + `?tags=<ids>` OR filtering; 25 backend + ~24 unit + 3 E2E tests |
| Admin Panel — Internal Kanban Task Board | ✅ Done | `Task` model (status/priority TextChoices, position, assignee FK SET_NULL, due_date); migration `0087_task.py`; 5 FBV endpoints (`tasks/`, `tasks/create/`, `tasks/<id>/update/`, `tasks/<id>/reorder/`, `tasks/<id>/delete/`); `TaskListSerializer` (assignee_name, is_overdue via context today) + `TaskCreateUpdateSerializer`; `tasks.js` Pinia Options API store (fetchTasks, createTask, updateTask, moveTask, deleteTask, replaceTaskInPlace); `TaskCard.vue` (priority badge, due_date red if overdue), `TaskColumn.vue` (vuedraggable cross-column DnD), `TaskFormModal.vue`; `/panel/tareas` page with `useConfirmModal`; panel nav entry "Tareas" / "Kanban" as first section; 11 backend tests + 9 frontend unit tests + 2 E2E specs; `ADMIN_KANBAN_TASKS` flow tag registered |
| Business Proposal — Admin UX Improvements | ✅ Done | Inline "days" number input beside `datetime-local` on create + edit pages (bidirectional sync, time-preserving); `@temp.example.com` domain bypass in `validate_email_domain_mx` + `jsonForm` default; fixed bottom-right save toast with Tailwind `<Transition>`, `clearTimeout` guard, 5 s auto-dismiss |
| Business Proposal — Value Added Modules Section | ✅ Done | New `section_type = 'value_added_modules'` (migration `0102`). `ValueAddedModules.vue` public component renders card grid of included-free modules (icon, title, justification, description). Seeded from `functional_requirements.manual_module` group for existing proposals. `test_value_added_modules.py` covers default schema; `ValueAddedModules.test.js` created (not yet run locally). |
| Diagnostic Templates Exposure in Proposal Tab | ✅ Done | Static `.md` templates (`diagnostico_aplicacion_es.md`, `diagnostico_tecnico_es.md`, `anexo_es.md`) served via 2 new admin FBV endpoints (`diagnostic-templates/` list + `<slug>/` detail). `ProposalDiagnosticTemplatesSection.vue` added to proposal admin "Documentos & Plantillas" tab. Per-slug client-side cache; copy-to-clipboard, download (.md Blob), and inline `<pre>` preview. Template content audited Apr 20, 2026: structure, coherence, tone, and cross-doc duplications corrected (see active_context.md for full audit log). |
| Diagnostic Markdown-to-PDF Email Attachment | ✅ Done | When diagnostic is in `negotiating` status, "Crear documento desde markdown" button appears in `DiagnosticEmailsTab.vue`. `MarkdownAttachmentModal.vue` (refactored to `endpoint: String` prop — moved to `components/` root for cross-context reuse) generates a branded PDF via `POST /api/diagnostics/<id>/email/markdown-attachment/` → `DocumentPdfService.generate_from_markdown()` → returns inline PDF; seller previews in iframe, then attaches as a `File` object to the email composer. Shared backend helper `content/views/_email_attachment.py` (functions `render_markdown_pdf_response` + `inline_pdf_response`) removes duplication between proposal and diagnostic attachment views. New frontend utilities: `useMarkdownAttachmentHandler.js` composable + `emailAttachments.js` validator + `proposals_constants.js` frozen enum. |
| Web App Diagnostics — Default Config | ✅ Done | `DiagnosticDefaultConfig` singleton-per-language model (`backend/content/models/diagnostic_default_config.py`, migration `0101`) holding `sections_json`, `payment_initial_pct=60`/`payment_final_pct=40` (with `clean()` sum-to-100 guard), `default_currency` (COP/USD), `default_investment_amount`, `default_duration_label`, `expiration_days=21`/`reminder_days=7`/`urgency_reminder_days=14`. `DiagnosticDefaultConfigSerializer` validates `sections_json` shape (`{section_type, title, order, content_json}`) and re-checks the payment sum. `diagnostic_service.py` exposes `DEFAULT_PAYMENT_INITIAL_PCT=60` etc. + `get_default_config(lang)` / `get_default_section_specs(lang)`; `create_diagnostic` reads the config once and forwards it to `seed_sections(diagnostic, config=...)` — no duplicate query. 2 admin endpoints: `GET/PUT /api/diagnostics/defaults/?lang=` and `POST /api/diagnostics/defaults/reset/`. Frontend page `panel/diagnostics/defaults.vue` (5 tabs: General + Sections + Emails-link + Prompt-placeholder + JSON) reuses `usePanelToast`, `useConfirmModal`, `ResponsiveTabs`, `<PanelToast />`. Pinia actions `fetchDiagnosticDefaults`/`saveDiagnosticDefaults`/`resetDiagnosticDefaults` (whitelisted general fields). Header link added to `panel/diagnostics/index.vue`. Tests: 8 model + 16 view backend (24 green) + 6 frontend store unit (jest run pending local install). Side effect: a misplaced `penal_clause_value` field was moved back to `ConfidentialityParamsSerializer`. |
| Web App Diagnostics — Full Module | ✅ Done | **JSON-section architecture** (rewrite Apr 16, 2026): `WebAppDiagnostic` model + new `DiagnosticSection` (8 section_types: `purpose`/`radiography`/`categories`/`delivery_structure`/`executive_summary`/`cost`/`timeline`/`scope`, `content_json`, `visibility` ∈ initial/final/both), `DiagnosticChangeLog`, `DiagnosticViewEvent`, `DiagnosticSectionView`. Migrations `0094` (schema) + `0095` (seed existing rows) + `0096` (drop legacy `DiagnosticDocument`). `content/seeds/diagnostic_template.py` → `default_sections()` seeds the 8-section + 14-category payload via `bulk_create`. Service (`diagnostic_service.py`): `create_diagnostic`, `seed_sections`, `reset_section`, `transition_status` (writes `STATUS_CHANGE` log), `visible_sections(phase)`, `register_view`, `log_change`, `build_render_context`. Email service (`diagnostic_email_service.py`): `send_initial_to_client`, `send_final_to_client`, `send_custom_email` + rate-limited composer. Serializers: `DiagnosticSectionSerializer` + `DiagnosticChangeLogSerializer`; `DiagnosticDetailSerializer` memoizes `build_render_context` per instance and slices prefetched `change_logs` in Python; `PublicDiagnosticSerializer` whitelists `render_context` via `PUBLIC_RENDER_CONTEXT_KEYS`. Views: 18 FBVs under `/api/diagnostics/` — CRUD, sections CRUD (single + bulk + reset), activity log list/create, analytics aggregate, send-initial/mark-in-analysis/send-final, attachments CRUD + send, email composer (send/defaults/history), public retrieve/track/track-section/respond. `_ensure_view_event` dedups session rows; `_send_and_transition` returns `(ok, email_ok)` so the UI surfaces email failures. `get_client_ip` hoisted to `content/utils.py`. Admin page `panel/diagnostics/[id]/edit.vue` has 5 base + 2 status-gated tabs: `general` → `[emails]` (≥SENT) → `[documents]` (≥NEGOTIATING) → `sections` → `prompt` → `json` → `activity` → `analytics`. The previous consolidated `technical` tab (Pricing + Radiografía sub-tabs) was removed on 2026-04-18; pricing fields live in General, radiography is edited as a regular section, and legacy deep-links (`?tab=pricing|radiography|technical`) redirect to `general`/`sections`. Admin components (`components/WebAppDiagnostic/admin/`): `DiagnosticSectionEditor.vue` + 8 per-type forms under `admin/sections/`, `DiagnosticPromptPanel.vue` + `PromptEditor.vue`, `DiagnosticActivityTab.vue`, `DiagnosticAnalytics.vue`. Shared `usePromptState({storageKey,defaultPrompt})` factory (`composables/usePromptState.js`) + `useDiagnosticCommercialPrompt`/`useDiagnosticTechnicalPrompt`. Public components: 8 section components + `SectionHeader.vue` + `DiagnosticIndex.vue` (sidebar index — hamburger toggle, backdrop blur, floating panel, numbered badges, visited checkmarks) under `components/WebAppDiagnostic/public/`. Public page (`pages/diagnostic/[uuid]/index.vue`): `layout: false`; no default Nuxt header; sections rendered via `COMPONENTS` map; `DiagnosticIndex` sidebar replaces the former pill nav; `visitedIds` ref + `markSectionVisited` helper track visited sections; per-section dwell time tracked with `session_id`, final row flushed via `navigator.sendBeacon` on unmount. `diagnostics_constants.js` exports `DIAGNOSTIC_STATUS`/`STATUS_META`/`SECTION_VISIBILITY`/`VISIBILITY_OPTIONS`/`SEVERITY_LEVELS`/`severityLevelClass`/`ACTIVITY_CHANGE_TYPES`; `arrToText`/`textToArr` re-imported from `BusinessProposal/admin/sectionEditorUtils.js`. Pinia store actions: `updateSection`/`bulkUpdateSections`/`resetSection`/`fetchActivity`/`logActivity`/`fetchAnalytics`/`trackSectionView`. Legacy `.md` templates retained under `templates/diagnostics/_legacy/` (unused at runtime). Tests: 29 backend (18 in `test_web_app_diagnostic.py` + 11 in `test_diagnostic_attachments_and_emails.py`) + 41 frontend (31 store + 10 section-utils roundtrip) — all green. |
| Document System — PDF Generation | 🔄 In Progress | `document_pdf_service.py`, `markdown_parser.py`, and shared `pdf_utils.py`; branch `generate-pdf-with-template` |
| Panel — Admins Management | ✅ Done | `panel/admins/index.vue` + `panel_admins.js` store |
| Panel — Dedicated Login | ✅ Done | `panel/login.vue` page |
| Platform — Bug Reports | ✅ Done | `platform-bug-reports.js`; global `/platform/bugs` + per-project `/platform/projects/[id]/bugs`; `test_bug_reports.py` |
| Platform — Change Requests | ✅ Done | `platform-change-requests.js`; global `/platform/changes` + per-project `/platform/projects/[id]/changes`; `test_change_requests.py` |
| Platform — Deliverables | ✅ Done | `platform-deliverables.js`; global `/platform/deliverables` + per-project `/platform/projects/[id]/deliverables`; `test_deliverables.py` |
| Platform — Notifications | ✅ Done | `platform-notifications.js`; `/platform/notifications`; `test_notifications.py` |
| Platform — Payments | ✅ Done | `platform-payments.js`; global `/platform/payments` + per-project `/platform/projects/[id]/payments`; `test_payments.py` |
| Platform — Global Board + Profile | ✅ Done | `/platform/board` (global kanban view); `/platform/profile` (profile management) |
| Business Proposal — Contract System | ✅ Done | `CompanySettings`, `ContractTemplate`, `ProposalDocument` models (migrations 0061–0068); `contract_pdf_service.py` with contractor signature + draft mode; `ContractParamsModal.vue`, `SendDocumentsModal.vue`, `ProposalDocumentsTab.vue` admin UI; `proposal_documents_sent` email template |
| Platform — Data Model Entities | ✅ Done | `DataModelEntity` + `ProjectDataModelEntity` in accounts app; `technical_requirements_sync.py` service; `/platform/projects/[id]/data-model.vue` page; `platform-data-model.js` store; 60 backend + 26 unit + E2E tests |
| Platform — UI Terminology & UX | ✅ Done | Épica → Módulo rename; `useConfirmModal.js` refactored to promise-based API; dark mode removed from platform login/verify/complete-profile pages |
| Business Proposal — Branded Email | ✅ Done | "Correos" tab on proposal edit (negotiating/accepted/rejected): draggable sections composer, file attachments, branded preview, paginated history; `_send_composed_email()` shared service; 6 URL patterns; `EmailLog.metadata` JSONField |
| Business Proposal — Proposal Email | ✅ Done | "Enviar correo" tab on proposal edit (sent+ statuses): same composer UI, each send creates `ProposalChangeLog` with `EMAIL_SENT` change type + updates `last_activity_at`; `ProposalEmailsTab.vue` with `mode` prop |
| Blog — LinkedIn Publishing | ✅ Done | `LinkedInToken` singleton model with Fernet-encrypted OAuth tokens; `linkedin_service.py` — 3-legged OAuth flow, auto token refresh, publish/unpublish blog post summaries with cover images via LinkedIn Posts API |
| Business Proposal — Advanced Filters & Saved Tabs | ✅ Done | `useProposalFilters.js` composable (11 filter dimensions, saved tabs with localStorage, URL sync); `ProposalFilterTabs.vue` (tab bar with +, rename, delete); `ProposalFilterPanel.vue` (collapsible filter grid); single-pass client-side filtering; max 12 tabs; `selectArrowStyle.js` shared utility |
| Business Proposal — Project Schedule Tracking (Cronograma) | ✅ Done | `ProposalProjectStage` child model (design + development with `start_date`/`end_date`/`completed_at`/`warning_sent_at`/`last_overdue_reminder_at`); `ProposalStageTracker` service with `STAGE_DEFINITIONS`, `ensure_stages`, `get_or_create_stage`, `format_remaining_time`, `process(proposal)`; daily Huey task `notify_proposal_stage_deadlines` (08:30 Bogotá); 70%-elapsed warning + every-3-days overdue reminders; admin Cronograma tab (`ProjectScheduleEditor.vue` + `useStageStatus.js`); 2 PUT/POST endpoints; onboarding auto-creates rows; 2 internal email templates; 51 backend tests + 49 frontend unit tests + 6 E2E |
| Backend — Bogotá date helpers | ✅ Done | `now_bogota()`, `today_bogota()`, `to_bogota_date(dt)` in `content/utils.py`; `format_bogota_date()` accepts both `date` and `datetime` instances |
| Business Proposal — Real client profiles | ✅ Done | `BusinessProposal.client` FK to `accounts.UserProfile` (PROTECT, `limit_choices_to={'role':'client'}`) with migrations `0079` (schema) + `0080` (backfill dedups by normalized email, two-step placeholder generation). New `accounts/services/proposal_client_service.py` (silent variant of `onboarding.create_client` — get-or-create, update + cascade snapshots, delete-orphan with 3 guards, sync_snapshot, generate_placeholder_email, build_client_display_name). 6 FBV endpoints under `proposals/client-profiles/*` (`views/proposal_clients.py`). `ProposalListSerializer`/`ProposalDetailSerializer` expose nested `client`; `ProposalCreateUpdateSerializer` accepts `client_id`/`client_company`/`propagate_client_updates`. Email automations: `_is_unsendable_client_email` helper + `UserProfile.PLACEHOLDER_EMAIL_DOMAIN` constant + `is_email_placeholder` property gate **13 client-facing email methods** + 4 huey tasks + 2 candidate querysets. N+1 fixes via `select_related('client__user')` in 4 views. Bug fix: `respond_to_proposal` now sends `send_acceptance_confirmation` for `action='accepted'`. Frontend: `proposalClients.js` Pinia store (Options API + AbortController search), `ClientAutocomplete.vue` (debounce 200ms, keyboard nav, click-outside via VueUse, placeholder badge), `/panel/clients/` rewrite with tabs (Todos/Activos/Huérfanos) + new-client modal + trash icon for orphans, `[id]/edit.vue` and `create.vue` use `<ClientAutocomplete>` + snapshot fields + propagate checkbox. Tests: 15 service + 19 view + 10 placeholder-skip backend + 25 store frontend = **69 new tests**, zero regression. Shipped 2026-04-09. |

---

## 2. Known Issues & Technical Debt

| Issue | Priority | Notes |
|-------|----------|-------|
| Credential rotation needed | High | MySQL password, email password, SECRET_KEY, CallMeBot key exposed in git history (see `docs/deployment-guide.md`) |
| Port 3000 squatted by `kore_project` | Medium | A Windsurf terminal respawns `kore_project` Next.js on port 3000. Workaround: run Nuxt on 3001 with `E2E_PORT=3001`. Tracked as `KNOWN-001` in `error-documentation.md`. |
| Large service files | Medium | `proposal_service.py`, `proposal_pdf_service.py`, `proposal_email_service.py`, and `pdf_utils.py` remain large enough to justify future splitting |
| Large view file | Medium | `views/proposal.py` remains a very large FBV module and could benefit from submodule extraction |
| Single Django app for content | Low | All proposal/blog/portfolio/contact models in `content` app; consider splitting if scope grows |

---

## 3. Testing Status

| Suite | Location | Approximate Count | Status |
|-------|----------|-------------------|--------|
| Backend (pytest) | `backend/content/tests/` + `backend/accounts/tests/` + `backend/tests/` | 126 test files | Active |
| Frontend Unit (Jest) | `frontend/test/` | 77 test files | Active |
| Frontend E2E (Playwright) | `frontend/e2e/` | 132 spec files across admin, auth, blog, layout, proposal, public, platform | Active |
| Quality Gate | `scripts/test_quality_gate.py` | 100/100, 0 warnings/info | Active |

---

## 4. Documentation Status

| Document | Location | Status |
|----------|----------|--------|
| Product Requirements | `docs/methodology/product_requirement_docs.md` | ✅ Initialized |
| Architecture | `docs/methodology/architecture.md` | ✅ Initialized |
| Technical | `docs/methodology/technical.md` | ✅ Initialized |
| Task Plan | `tasks/tasks_plan.md` | ✅ Initialized |
| Active Context | `tasks/active_context.md` | ✅ Initialized |
| Error Documentation | `docs/methodology/error-documentation.md` | ✅ Initialized |
| Lessons Learned | `docs/methodology/lessons-learned.md` | ✅ Initialized |
| Codex Methodology Guide | `docs/CODEX_METHODOLOGY_GUIDE.md` | ✅ Complete |
| Codex Setup Quickstart | `docs/CODEX_SETUP.md` | ✅ Complete |
| Codex Migration Map | `docs/CODEX_MIGRATION_MAP.md` | ✅ Complete |
| Deployment Guide | `docs/deployment-guide.md` | ✅ Complete |
| Testing Quality Standards | `docs/testing-quality-standards.md` | ✅ Complete |
| User Flow Map | `docs/USER_FLOW_MAP.md` | ✅ Complete |
| E2E Flow Definitions | `frontend/e2e/flow-definitions.json` | ✅ Complete |
| README | `README.md` | ✅ Complete |
| CI Workflow | `.github/workflows/ci.yml` | ✅ Complete |
| Nginx Config | `scripts/nginx/projectapp.conf` | ✅ Complete |
| Systemd Services | `scripts/systemd/` | ✅ Complete |

---

## 5. Potential Improvements

1. **Split large files** — proposal views/services and the shared PDF utility layer are still large enough to benefit from decomposition
2. **API versioning** — no versioning strategy currently
3. **Rate limiting** — no rate limiting on public endpoints
4. **Caching layer** — Redis available but no application-level caching implemented
5. **WebSocket notifications** — real-time alerts instead of polling
6. **Multi-tenant support** — currently single-company; could generalize for SaaS
7. **Codex docs drift guard** — add a lightweight check ensuring native skill inventory and sensitive-skill policy stay in sync with Codex methodology docs
