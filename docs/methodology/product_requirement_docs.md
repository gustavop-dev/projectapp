# Product Requirements Document — ProjectApp

## 1. Overview

**ProjectApp** is the full-stack web application for **Project App** (projectapp.co), a custom software development company based in Colombia. The platform serves as:

1. **Company website** — marketing pages, portfolio showcase, blog, and contact form
2. **Business proposal & diagnostic CRM** — create, send, track, and close personalized proposals and web-app diagnostics for prospective clients
3. **Client delivery platform** — post-sale client portal (`/platform/`) for projects, kanban, deliverables, payments/hosting, bug reports, change requests, and click-to-accept document signing
4. **Internal operations** — admin panel for diagnostics + an internal Kanban, a superuser accounting module (personal ledgers, exports, card-debt reminders), and MCP connectors that expose panel modules to claude.ai

The application is bilingual (English / Spanish) and targets two distinct user personas: the **Admin** (company seller/owner) and the **Client** (prospective customer, and — post-sale — platform user).

---

## 2. Problems Solved

| Problem | Solution |
|---------|----------|
| No centralized way to create and send client proposals | Full proposal builder with 18 auto-generated section types plus four client-facing reading modes |
| Proposals sent as static PDFs with no tracking | Interactive fullscreen web experience with engagement analytics |
| No visibility into client interest or behavior | View tracking, section-level time analytics, heat score, engagement signals |
| Manual follow-up prone to human error | Automated email reminders (day 10, day 15, urgency, inactivity, re-engagement) |
| One document status cannot describe concurrent work or preserve what already happened | User-managed cycle/signal states whose open and closed episodes form an attributable timeline |
| The agency had no received copy of customer email | Every client-classified email leaves through one gateway, which sends configurable BCC-only internal copies and links their independent outcomes to the primary history row |
| Client conversations were drafted in disposable chats and reconstructed from memory | A client/project communications registry preserves ordered incoming and outgoing messages, manual send state, date corrections and references to existing documents |
| Sparse or incoherent development data hid pagination, filters and edge defects until production | One guarded, deterministic dataset covers every visible module with explicit volume, skewed relationships, temporal buckets and intentional extremes |
| Company portfolio hard to maintain | Admin CRUD panel for portfolio works with bilingual content |
| No blog for SEO/content marketing | Full blog system with structured JSON content, categories, calendar, sitemap |
| Language barrier for international clients | i18n with prefix routing (`/en-us/`, `/es-co/`) for all public pages |

---

## 3. Core Features

### 3.1 Business Proposal System (Flagship)

The proposal system is the most complex and central feature. It allows the admin to:

- **Create proposals** with client name, email, investment amount, currency, expiration date, language, project type, and market type
- **18 section types auto-generated** per proposal: Greeting, Executive Summary, Context & Diagnostic, Conversion Strategy, Design & UX, Creative Support, Development Stages, Process & Methodology, Functional Requirements, Timeline, Investment, Proposal Summary, Final Note, Next Steps, Technical Document, Value Added Modules, ROI Projection, and Commercial Conditions (the last few are order-dependent; some — e.g. `roi_projection`, `value_added_modules`, `proposal_summary` — are web-only and intentionally skip the PDF)
- **Edit section content** — each section stores structured JSON matching a specific Vue component's props schema
- **Choose a reading mode** — the public gateway offers executive, detailed, technical, and **Contrato y condiciones**. The legal mode is a separate, generic document surface rather than another proposal section.
- **Readable proposal presentation** — closing cards use two columns only when each retains a comfortable reading width; payment amounts keep number, currency, and tax suffix together on laptop/desktop screens. Non-empty lead copy below section titles contains one or two short, safe bold fragments for scanability.
- **Send to client** — triggers email with unique UUID link, schedules automated reminders
- **Track engagement** — view count, first viewed date, per-section or per-contract-clause time analytics, session tracking, reading mode, engagement scoring (heat score 1-10)
- **Share links** — clients can share proposals with stakeholders, each share link tracked independently
- **PDF generation** — downloadable PDF version via ReportLab
- **Investment calculator** — interactive modal for clients to explore payment options (hosting plans, discounts)
- **Client responses** — accept, reject (with reason/comment), or negotiate proposals directly from the proposal page
- **Manual discount offer** — from the proposal actions menu the seller can send a one-off discount/urgency email (`proposal_urgency` template) after previewing it; shown only when a discount percentage is configured and the client has an email (never auto-sent)

#### Proposal Lifecycle

```
DRAFT → SENT → VIEWED → ACCEPTED
                      → REJECTED (with reason)
                      → NEGOTIATING
                      → EXPIRED (auto, daily cron)
```

- **DRAFT**: Created, not yet sent
- **SENT**: Email dispatched, `sent_at` recorded, reminders queued
- **VIEWED**: Client opened the link (first view tracked)
- **ACCEPTED / REJECTED / NEGOTIATING**: Client or admin status updates
- **EXPIRED**: Auto-set by daily Huey periodic task when `expires_at < now()`

#### Automated Emails

| Email | Trigger | Timing |
|-------|---------|--------|
| Proposal sent (client) | Admin clicks "Send" | Immediate |
| Proposal sent (admin notification) | Admin clicks "Send" | Immediate |
| Reminder | Proposal still SENT/VIEWED | Day N (configurable, default 10) |
| Urgency / discount | Proposal still SENT/VIEWED | Day N (configurable, default 15) |
| Abandonment | Proposal viewed but no return | After inactivity period |
| Revisit alert (admin) | Client revisits after inactivity | Immediate |
| Investment interest | Client interacts with calculator | After confirmation |
| Stakeholder alert | Share link is opened | Immediate |
| Post-expiration visit | Client visits expired proposal | Immediate |
| Engagement decay | Declining engagement detected | Immediate |
| Stage warning (internal team) | Project stage 70% elapsed (Cronograma) | Daily 08:30 Bogotá, sent once per stage |
| Stage overdue (internal team) | Project stage past `end_date` (Cronograma) | Daily 08:30 Bogotá, repeats every 3 days while uncompleted |

**24h cooldown** enforced between automated client-facing emails per proposal. **Automations can be paused** per proposal (`automations_paused` flag). **Internal team notifications** (stage warning, stage overdue, first view, comment, seller inactivity, etc.) bypass the cooldown — per-event dedup is handled by dedicated timestamp fields on the source model.

**Internal team recipients** are read from the `NOTIFICATION_EMAIL` env var (CSV-supported). One env var, all internal notifications. To target a different audience for stage tracking specifically, change the env var — there is no per-feature recipient setting.

**Copies of client communication** use a separate administrable list under
`/panel/emails` and never reuse `NOTIFICATION_EMAIL`. The starting behavior is
all client email, with optional segmentation by Propuestas, Diagnósticos,
Documentos/correos manuales, Cuentas de cobro and Plataforma. Copies are sent
as separate BCC-only envelopes after the customer delivery succeeds; their
success or failure is nested in the same delivery history. The authoritative
23-channel inventory is `docs/client-email-copy-inventory.md`.

#### Admin Panel — Proposals

- **Dashboard** (`/panel/`): multi-module command center (redesigned 2026-07-16, #110) — one consolidated endpoint aggregates proposal KPIs/heat scores/alerts, accounting year totals, tasks, diagnostics, and module shortcuts
- **Proposals list** (`/panel/proposals/`): table with title, client, status badge, investment, expiry, views, bulk actions
- **Create** (`/panel/proposals/create`): form with all metadata + JSON import option. Client identity is selected via `<ClientAutocomplete>` (searchable dropdown over `accounts.UserProfile` with `role='client'`); typing a brand-new name + email auto-creates a real `UserProfile` row, and an empty email gets a placeholder `cliente_<id>@temp.example.com` that pauses every email automation for that proposal. A top-level switch controls whether the generic contract mode is visible; it defaults on for Spanish proposals and does not enter the imported/exported section JSON.
- **Edit** (`/panel/proposals/{id}/edit`): Tabs depending on proposal status:
  - **General** — metadata + same `<ClientAutocomplete>` picker + write-through snapshot fields + propagate-changes-to-profile checkbox + send button + immediate contract-mode visibility switch
  - **Correos** (sent+ statuses) — branded email composer
  - **Documentos** (negotiating/accepted/rejected) — contracts + uploaded annexes
  - **Cronograma** (accepted/finished) — project stage scheduling (design + development dates, mark-as-completed, status badges)
  - **Secciones** — section editor (expand/edit JSON per section)
  - **Det. técnico**, **Prompt Proposal**, **JSON**, **Actividad**, **Analytics**
- **Defaults** (`/panel/proposals/defaults`): manage default section templates per language
- **Email templates** (`/panel/proposals/email-templates`): view/edit/preview/reset email content
- **Email deliverability** (`/panel/proposals/email-deliverability`): dashboard tracking email send/delivery/bounce rates
- **Clients list** (`/panel/clients/`): real `UserProfile` (role=client) entities. Tabs (Todos / Activos / Huérfanos), live search, "+ Nuevo cliente" modal for standalone creation (no invitation email sent — that path is reserved for the platform onboarding flow). Orphan clients (zero proposals + zero platform projects) are deletable via a trash icon gated through `requestConfirm`. Each row expands lazily to load the client's full proposal history. Replaced the legacy "synthetic clients grouped by `(name, email)`" implementation on 2026-04-09.

#### Project lifecycle and operational consequences

- `/panel/projects` uses the shared PA-88 state catalog and history engine, scoped
  to `catalog='projects'`; it does not maintain a second status system.
- The six seeded meanings are **En desarrollo**, **Activo**, **Pausado**,
  **Suspendido**, **Completado** and **Dado de baja**. Names and colors are
  administrable, while `operational_effect` remains the stable business meaning.
- New projects begin En desarrollo. Later changes require a server preview and an
  impact token; direct enum writes and the legacy archive/unarchive endpoints do
  not bypass that flow.
- Suspendido is reversible and stops new billing/reminders while retaining debt
  already caused. A failed hosting payment may suggest this state, never apply it.
  Completado means a clean close. Dado de baja is definitive, cancels future
  service and requires an explicit keep/write-off decision for caused receivables;
  a direct jump that skips Suspendido also requires a note.
- Every transition opens/closes dated episodes with actor and note. Existing legacy
  archived projects remain **Sin clasificar / Por revisar** instead of receiving an
  invented final state, and money automation fails closed until an operator decides.
- State filters and header counts come from the live catalog. **Clientes sin
  proyecto** remains literal: a client with no `Project` row, regardless of the
  lifecycle state of projects owned by other clients.

#### Project Schedule Tracking (Cronograma)

A new internal-only sub-system that tracks the **execution** of an accepted proposal — distinct from the client-facing `timeline` proposal section (which is sales/marketing copy with free-text durations like "1 semana").

- **Two stages per accepted proposal**: `design` and `development`. Empty rows are auto-created when the proposal becomes `accepted` via the platform onboarding flow.
- **Per-stage fields**: `start_date`, `end_date`, `completed_at`, `warning_sent_at`, `last_overdue_reminder_at`. The model lives at `backend/content/models/proposal_project_stage.py`.
- **Manual date entry**: Admins fill in `start_date` and `end_date` from the new "Cronograma" tab in the proposal edit page (`frontend/components/BusinessProposal/admin/ProjectScheduleEditor.vue`). We do NOT auto-derive dates from the free-text `timeline` section.
- **70%-elapsed warning email**: The daily Huey task `notify_proposal_stage_deadlines` (08:30 Bogotá) sends a warning email when ≥70% of `(end_date - start_date)` has elapsed. Gated per stage by `warning_sent_at`. **Re-fires after date extension**: when the admin updates `end_date` (or `start_date`) and the new timeline drops elapsed% back below 70%, `update_project_stage` calls `ProposalStageTracker.maybe_reset_warning_on_date_change` to clear `warning_sent_at`; the daily task then fires again once the new 70% mark is crossed.
- **Overdue reminders**: When `today > end_date`, sends a reminder email immediately and then repeats every 3 days until the admin marks the stage as completed (gated by `last_overdue_reminder_at`).
- **Mark as completed**: A button per stage in the Cronograma tab. Sets `completed_at = now()` and clears the alert timestamps. Silences all future emails for that stage.
- **Time format**: Both warning and overdue messages format remaining/overdue time as `"hoy"`, `"1 día"`, `"6 días"`, `"1 semana"`, `"1 semana 5 días"`, `"2 semanas"` (semanas if ≥7 days, días if less, mixed when needed). Logic in `ProposalStageTracker.format_remaining_time` (Python) and `useStageStatus.formatRemainingTime` (JS, kept in sync via parallel test cases).
- **Recipients**: Internal team via `NOTIFICATION_EMAIL` CSV (see Automated Emails table above).
- **Internal-only**: `ProposalProjectStage` is gated by `is_admin` context in `ProposalDetailSerializer.get_project_stages` — never exposed to public proposal views.

### 3.2 Portfolio Showcase

- Public listing and detail pages (`/portfolio-works/`, `/portfolio-works/{slug}`)
- Bilingual content (title, excerpt, structured JSON with problem/solution/results)
- Cover image upload or external URL
- SEO metadata (meta title, description, keywords per language)
- Admin CRUD with JSON import/duplicate/publish flow
- Sitemap data endpoint for SEO

### 3.3 Blog System

- Public listing with featured post hero, category filtering, pagination (`/blog/`)
- Detail page with structured JSON rendering or HTML fallback (`/blog/{slug}`)
- Bilingual content with SEO metadata
- Author profiles, read time estimates, cover images with credit attribution
- 17 categories (technology, design, AI, marketing, etc.)
- Admin CRUD with JSON import, duplicate, publish, calendar view
- Sitemap data endpoint
- **LinkedIn Publishing** — admin can connect a LinkedIn account via OAuth 2.0 and publish/unpublish blog post summaries (with cover image) directly to LinkedIn from the panel; OAuth tokens stored encrypted via Fernet (`LinkedInToken` singleton model)

### 3.4 Contact Form

- Public form (`/contact/`) with fields: name, email, phone, project description, budget range
- Budget ranges: 500-5K, 5-10K, 10-20K, 20-30K, >30K
- Submits to API, triggers email notification to admin
- Success page (`/contact-success/`)

### 3.5 Document System

- Generic branded PDF documents separate from proposals
- Client visibility is an independent `is_client_visible` gate. The legacy
  draft/published field remains only during the expand/contract rollout and no
  longer represents the internal workflow.
- **Administrable workflow**: one document may carry one active state from an
  exclusive cycle group plus any number of additive signals. The editable seed
  catalog is Borrador, Enviado, En revisión, Bug atendido, Cerrado and Solucionar
  bug; stable `system_key` values keep integrations working after a rename.
- **Episode history**: activating a state opens an episode; completing or removing
  it closes that episode with a distinct outcome, actor, exact timestamp, optional
  note and append-only event. A state may recur in multiple episodes, and opening
  times can be corrected when an event was recorded late.
- The list and editor show cycle first, then signals, including live duration.
  Solucionar bug has a high-attention treatment. History opens in a short timeline
  with exact and relative times, duration, actors, notes and linked observations.
- States can be created inline with duplicate suggestions, renamed/recolored,
  retired when unused, or merged from the catalog view. The catalog reports active
  document and historical-episode counts and blocks rule changes that would make
  current documents invalid.
- State filters are OR within the dimension, support absence (for example “without
  Cerrado”), and include the recurring presets Algo por solucionar, Enviados sin
  cerrar, Cerrados and Por clasificar.
- Adding an observation may open Solucionar bug. Resolving/discarding the final
  linked observation may complete/remove the signal and optionally move the cycle
  to Bug atendido. Sending a standalone document email may open Enviado after
  explicit confirmation.
- Structured JSON content stored in `content_json` field
- PDF generation via `DocumentPdfService` + `MarkdownParser` + shared `PdfUtils` layer
- Admin CRUD panel (`/panel/documents/`) with create, edit, list and state-catalog management
- **Long-name containment**: list and gallery titles are always bounded by their
  cell/card. The collapsed state uses one line with ellipsis and exposes the same
  measured **Ver completo/Contraer** path for names with spaces or systematic
  underscore/date naming; the expanded state may break anywhere. Folder comes
  first in a separate metadata row below the title, followed by compact-only
  client/project/state distinctions. Rows without a folder keep natural height.
- **Private notes**: creation and editing keep the email subject, complete email body,
  WhatsApp message, and an ordered collection of custom title/content notes in one
  optional modal. Every non-empty value has an individual 📋 copy action with ✅
  feedback. These administrative fields never render in markdown/PDF and are never
  exposed in the client document portal.
- In an existing document, **Guardar cambios** in the notes modal persists those
  fields immediately and confirms it visibly; no second page-level save remains.
  During creation, **Aplicar al borrador** states that the document still has to be
  created before the notes are stored.
- The Documents MCP can create, read, and partially update all private notes. Every
  report created through `client-report` continues to generate and persist only the
  canonical subject/email/WhatsApp triple; `client-message` reuses that copy without
  producing a second version. Custom notes remain independently managed metadata.
- Bilingual support (es/en)
- **Folders & workflow states**: folders remain the structural hierarchy. The former
  colored document tags were consolidated into additive workflow states instead of
  leaving two overlapping user-facing systems; legacy tag assignments are expanded
  into open episodes with an explicitly unknown opening time during migration.
  - Folder deletion is **blocked (HTTP 409)** when the folder contains documents; the admin must move or delete each document first. The DB FK keeps `on_delete=SET_NULL` only as a safety net for non-API removals.
  - Folder mutations from `FolderManagerModal` re-fetch both the documents list and the folder store so the sidebar count and order reflect the change without a page reload.
- **Context-preserving navigation**: the list URL is the canonical representation of
  folder, normal/archived scope, workflow states, client/project, global search,
  ordering, view mode, page and focused document. Every editor exit returns to that validated list
  URL and identifies its destination; browser Back restores the same list state.
  Direct or untrusted editor entries have no valid origin and fall back to the
  localized Documents root.
  - Collection accounts keep their separate commercial lifecycle and are excluded
    from the generic state catalog and legacy-tag expansion.

### 3.5.1 Client Communications Registry

- **Separate product module, shared infrastructure**: communications are not a
  `Document` subtype. They reuse client/project identities, document references,
  session auth, panel primitives and the existing `content` Django app while
  keeping conversation-specific models, API, store and route.
- A client can own multiple simultaneous threads; a thread may optionally be
  scoped to one of that client's projects.
- A thread contains chronologically ordered messages with channel, direction,
  occurred date, exact content and operational state. Incoming messages are
  optional but first-class, so a reply remains readable beside its origin.
- **State semantics**: outgoing messages are draft or sent; incoming messages are
  received. “Respondido” is derived from a valid opposite-direction reply and
  does not overwrite the stored send fact.
- **Manual-channel boundary**: phase 1 records what the operator copied/sent via
  WhatsApp or email; it does not claim that ProjectApp delivered it. Real email
  delivery through `EmailDeliveryGateway` remains a later phase.
- **References, never copies**: messages link existing `Document` rows through a
  protected join. Document detail exposes reverse usage, and a referenced
  document cannot be deleted accidentally.
- Delivered messages are immutable: corrections create append-only dated audit
  rows and annulments require a reason. Drafts remain editable and deletable.
- The decision record, comparison and phased roadmap live in
  `docs/superpowers/specs/2026-08-25-client-communications-registry-design.md`.

### 3.6 Contract System

- Reusable contract templates (`ContractTemplate`) with customizable sections and parameter substitution
- Contract PDFs generated via `ContractPdfService` using ReportLab + shared `PdfUtils`
- **Draft mode**: generate contract PDF without contractor signature block for review
- **Final mode**: include contractor signature block once contract is agreed
- **Public proposal draft**: Spanish proposals may expose the current default template as **Contrato y condiciones**. Its first panel explains the draft at the same usable width as the linked clause index; its second panel renders the full contract vertically inside a bordered, layered paper surface that remains readable in light and dark themes. The dedicated PDF download is available from the persistent floating action, always forces the global template, masks personal data, omits signatures, and applies the `BORRADOR` watermark.
- The public draft is intentionally independent from proposal-specific `ProposalDocument` contracts and from proposal prompt/section JSON. It is current global content, not a per-proposal snapshot.
- Font: Helvetica throughout for consistent cross-platform rendering
- Clickable Table of Contents with anchor links to contract sections
- `ProposalDocument` links a generated contract to a specific proposal
- `CompanySettings` provides company branding data (name, logo, address, tax ID) used in PDF headers

### 3.7 Data Model Entities

- Reusable JSON-schema–defined data models (`DataModelEntity`) for project technical requirements
- `ProjectDataModelEntity` links a data model entity to a specific project, with optional custom schema override
- Technical requirements sync: project requirements can be synchronized from data model entity definitions
- JSON upload endpoint to bulk-import entity schemas
- Accessible via platform project data model tab (`/platform/projects/:id/data-model`)

### 3.8 Web App Diagnostics

A second sales product alongside proposals: a structured **web-app diagnostic** delivered to a prospect via a public UUID link, mirroring the proposal's JSON-section architecture (rewritten Apr 16, 2026).

- **`WebAppDiagnostic` entity** with 8 typed `DiagnosticSection`s (`purpose`, `radiography`, `categories`, `delivery_structure`, `executive_summary`, `cost`, `timeline`, `scope`), each with `visibility` ∈ initial/final/both.
- **Admin** (`/panel/diagnostics/`): create, edit (base + status-gated tabs: General, Correos, Documentos, Secciones, Prompt, JSON, Activity, Analytics), a send-initial → mark-in-analysis → send-final lifecycle, per-language defaults (`/panel/diagnostics/defaults`), and full analytics parity with proposals (engagement score, funnel, device breakdown, sessions).
- **Public view** (`/diagnostic/{uuid}/`): sidebar-indexed sections, PDF download, share, dark-mode toggle, per-section dwell tracking.
- **NDA / confidentiality**: an optional confidentiality PDF can be attached to diagnostic emails.

### 3.9 Platform — Expanded Modules

Building on the base Platform (auth, projects, kanban), these modules extend client collaboration:

#### Bug Reports
- Client and admin can submit, track, and resolve bug reports per project
- Global view (`/platform/bugs`) + per-project view (`/platform/projects/:id/bugs`)

#### Change Requests
- Structured change request workflow per project
- Global view (`/platform/changes`) + per-project view (`/platform/projects/:id/changes`)

#### Deliverables
- Track project deliverables with status and descriptions
- Global view (`/platform/deliverables`) + per-project view (`/platform/projects/:id/deliverables`)

#### Notifications
- In-platform notification center (`/platform/notifications`)
- Centralizes alerts across all platform modules

#### Payments
- Track payment milestones and subscription plans per project
- Global view (`/platform/payments`) + per-project view (`/platform/projects/:id/payments`)
- Linked to proposal investment section (hosting tiers, payment milestones)
- New hosting offers use exactly three prepaid periods: quarterly (10% discount), semiannual (20%), and every 9 months (40%). Monthly and annual remain readable only on historical records.

#### Global Board + Profile
- `/platform/board` — global kanban view across all projects
- `/platform/profile` — user profile management page

### 3.10 Marketing / Landing Pages

- **Home** (`/`): main company page with animations, portfolio highlights, services overview
- **Landing Web Design** (`/landing-web-design`): targeted landing for web design services
- **Landing Software** (`/landing-software`): targeted landing for software development
- **Landing Apps** (`/landing-apps`): targeted landing for mobile app development
- **About Us** (`/about-us`): team and company information
- All pages fully responsive with GSAP animations

### 3.11 Platform — Quick Access (Admin URLs & Credentials)

Admin-only space at `/platform/access` for rapid access to operational URLs and Django admin credentials per project.

- **Purpose**: Centralise production URL, staging URL, Django admin URL, and repository URL per project; store Django admin credentials encrypted (Fernet) for copy-paste access
- **Visibility**: Staff/admin only — clients cannot see this section
- **Credential storage**: `admin_password_encrypted` (Fernet ciphertext); key configured via `PROJECT_ACCESS_CIPHER_KEY` env var
- **UI**: Grid of project cards — click to open URL in new tab; "Copiar" / "Revelar" buttons for credentials; real-time search
- **Sidebar entry**: "Accesos" under the Administración section in `PlatformSidebar.vue`
- **Backend**: `GET /api/accounts/projects/access/` returns full list with decrypted passwords (admin-only via `IsAdminRole`); `PATCH /api/accounts/projects/<id>/` accepts the new URL/credential fields and encrypts on save
- **Django admin**: `accounts/admin.py` — `ProjectAdmin` exposes the URL/credential fieldset; plaintext password input is encrypted in `save_model`

### 3.12 Admin Panel Enhancements

- **Panel Login** (`/panel/login`) — dedicated login page for admin panel
- **Panel Admins** (`/panel/admins`) — admin user management (invite, list, manage admin accounts)
- **Internal Kanban Task Board** (`/panel/tasks`) — admin-only Kanban board for managing internal ProjectApp team work. Four columns: TO DO, In Progress, Blocked, Done. Tasks have title, description, status, priority (low/medium/high), assignee (FK to any admin User, optional), and due_date (optional). Cards display priority badge and due_date highlighted in red when overdue. Drag-and-drop between columns and reorder within columns via vuedraggable. Create/edit modal with confirm-guarded delete. Tasks are independent — no FK link to proposals or documents.
- **Responsive panel contract** — the internal panel is validated at 412, 835,
  1195, 1440 and 2560 px. Shared primitives own table column priorities,
  tab/filter collapse, modal widths and stacking, navigation, bulk/row actions,
  touch targets, typography and the 1400 px general-content ceiling. The canonical
  fleet standard, project inventory and implementation contract live in
  `docs/RESPONSIVE_STANDARDS.md`, `docs/RESPONSIVE_STANDARD.md` and
  `docs/methodology/responsive-standard.md`, respectively.
- **Responsive operational modules** — Documentos, Clientes and Proyectos preserve their useful information at 412, 835, 1195, 1440 and 2560 px. Below the canonical 1024 px landscape boundary, two-zone/filter-heavy interfaces collapse into one primary content stream plus explicit drawers/selectors, dense rows become labeled cards, every hover/drag action has a touch path, and phone modals use the full viewport. At 1195 px their desktop structures are active. At 2560 px the content column remains capped at 1400 px.
- **Readable document titles** — document names use two lines with end truncation by default. The complete native hint exists only when the rendered title is actually clipped, and the same condition exposes an in-place **Ver completo/Contraer** path for touch layouts. In list mode, Título is adjustable from 240 to 520 px (320 px default), remembered per browser and reset by double click; Proyecto, Cliente and Fecha yield space in that order, while Estados and Acciones stay fixed. After donor minima, only the table wrapper scrolls. Middle truncation was evaluated and intentionally deferred because two lines plus conditional reveal preserve the full value without inventing a second naming rule.

### 3.13 Internationalization (i18n)

- Two locales: `en-us` (English, default) and `es-co` (Spanish Colombia)
- Prefix strategy: `/en-us/about-us`, `/es-co/about-us`
- Lazy-loaded translation files
- Geo-locale detection plugin for automatic language suggestion
- Language store with sync plugin

### 3.14 Accounting (Superuser Finance)

Internal double-ledger bookkeeping at `/panel/accounting/*`, restricted to superusers (shipped 2026-07-03).

- **Three ledgers** — company + two partners (Gustavo, Carlos) — with a **partner-split invariant**: a personal-ledger record must be 100% the owning partner's (enforced in `PartnerSplitMixin.clean()`).
- **Sub-ledgers**: incomes, expenses, hosting, recurring payments, ads spend, pocket movements, and weekly card-balance snapshots — each with server-side + client-side filters and modal CRUD.
- **Dashboard & charts** per year; **exports** to CSV/XLSX per section and a full-year multi-sheet workbook.
- **Card-debt reminder**: a weekly Huey task emails the partners every Friday cycle until a card snapshot dated on/after that Friday is registered (re-alerts every 2 days).
- **Income lifecycle** (2026-07-16, #110): incomes carry a kind — *expected* (projection), *liquid* (actually received; a liquidation modal links the settled record to the projection it fulfills via an `expected_income` FK), or *lost* (write-off excluded from projections). The incomes view reports received-% and lost totals; expenses expose a paid/pending state. Liquidation defaults its destination to the ProjectApp pocket, with an optional exact-payment-date toggle (#114); income/expense `period_date` accepts a full date besides YYYY-MM.
- **Collection-account linked income** (2026-08-26): the selector opens on the chosen client's *expected* incomes and resets to that stable default on every open and client change. This is a reversible kind filter, not a restriction: *all* and *liquid* remain selectable. Kind—not payment status—defines the default, so a partially paid expected income remains eligible. An empty result offers a one-click expansion to all kinds while retaining client scope, then to global scope only when that client has no eligible income; the last choice is not remembered.
- **Pocket as entry point** (#103): pocket movements sync bidirectionally with income/expense records. A pocket egreso attributed to a partner mirrors a **company-ledger expense 100% assigned to that partner** — every pocket draw reduces company liquid utility and the partner's participation, never the personal ledger (#114).
- **Display standards** (#115/#116): emails format COP with the millions apostrophe (`format_cop_email`) while the app uses dot grouping; all dates render as "Jue, 16 jul 2026" (abbreviated Spanish weekday + short month) via the backend Bogotá helpers and the frontend `utils/formatDate.js`.
- **Credit-card catalog & statements** (#105/#106): registered cards with quota (debt computed server-side as quota − available), monthly statements with editable transactions + PDF and an 8-day reminder, plus summary cards for card debt and current-month expected income.
- **Recurring COP projections** (2026-08-22): the server owns each recurring payment's COP equivalent. It derives the charge from price + currency + the current manually configured USD rate, then prorates it by frequency for the monthly column. Editing any input or saving a new exchange rate refreshes the row and all dependent totals; a data migration repairs historical stale values.
- **Audit trail** (`AccountingChangeLog`) + notification-recipient settings.
- **Responsive accounting workspace** (2026-08-22): the twelve tabs share one navigation contract, saved-filter strips collapse to selectors below 1024 px, KPI groups preserve the three business priorities and disclose secondary values, and every table declares which fields stay, group or hide. Grouped client headers stack their totals in narrow layouts; long workflows use semantic full-screen mobile modals and touch-safe action menus. Pocket never drops the running balance: compact rows relocate it below the movement amount and the independent column returns from landscape width. The repeatable 12-tab × 5-width acceptance script lives in `docs/ACCOUNTING_RESPONSIVE_TEST_SCRIPT.md`.

### 3.15 MCP Connectors (claude.ai)

Remote Model-Context-Protocol connectors that expose panel modules to claude.ai custom connectors, managed at `/panel/mcps` (superuser-gated; shipped 2026-07-02/03).

- **Connectors**: blog, documents, proposals, diagnostics, clients, tasks,
  accounting, LinkedIn personal and communications — each a token-authenticated
  JSON-RPC tool server (`content/mcp/*`) grouped by module and exposed through one
  registered slug.
- **Management**: generate/rotate a one-time connector URL (plaintext token shown once, only its SHA-256 hash stored), toggle active, and watch a connection-activity feed (handshake / tool_call / auth_error / origin_rejected).
- **Security**: Origin validation (DNS-rebinding defense), per-connector token, active-state gate.
- **Communications**: lists threads by client/project, opens the ordered message
  history, creates client-owned threads, records incoming/outgoing messages with
  existing Document references and marks an outgoing draft as sent. It reuses the
  panel services and invariants; it records delivery facts but does not send through
  a provider. Migration `content.0212_seed_communications_mcp` creates this connector
  disabled and without a token so activation remains an explicit operator action.
- **Parity**: Documents exposes client, project and workflow states; Accounting
  exposes hosting periods, allocations, partial payments and settlement history.
  `content/mcp/contracts.py`, focused tests and `docs/MCP_VALIDATION_RUNBOOK.md`
  make every exposed model field and repeatable validation scenario explicit.
- The `client-report` skill publishes session change-reports and their canonical
  subject/email/WhatsApp note to the Documents connector; custom notes remain
  available for manual or direct MCP use.

### 3.16 Client Document Portal & Signing

Client-facing document delivery + click-to-accept signing at `/platform/documents` — the landing page for a client after first login.

- Lists the **main contract** (`requires_signature`) first, then annexes; each downloadable as a branded PDF.
- **Email-ownership OTP**: before signing, the client validates their email via a 6-digit code (`email/verify/request` + `/confirm`); `UserProfile.email_verified` gates the sign button.
- **Signing**: click-to-accept with a consent checkbox records `signed_at/signed_by/signature_name/signature_ip/signature_user_agent`; idempotent re-signs.
- **Team milestone notifications** fire (best-effort, in-app + email) on first login, email validated, and document signed.

### 3.17 Representative Development Dataset

Development and test environments have one cross-module dataset contract:

- a default target of 60 root rows where the domain is list-shaped, including a
  60-row heavy project for requirements, deliverables, changes and bugs;
- coherent client → project → income → collection-account and client → thread →
  message relationships, with document creation routed through the production
  service layer;
- deliberately skewed clients, lifecycle states and histories instead of uniform
  random samples;
- past/current/future date buckets and UI-breaking long unbroken labels and large
  amounts;
- isolated random streams plus an explicit business-date anchor for exact replay;
- an atomic, fail-fast refresh guarded by a positive capability that remains hard
  false in production settings;
- an executable model inventory that makes fake-data ownership part of the same
  delivery as every future model.

The canonical counts, commands and exceptions are maintained in
`docs/FAKE_DATA_COVERAGE.md`.

---

## 4. Target Users

### Admin (Seller / Company Owner)
- Creates and manages business proposals
- Tracks client engagement and follows up
- Manages portfolio works and blog content
- Receives notifications via email and WhatsApp

### Client (Prospect)
- Receives unique proposal link via email
- Chooses between executive, detailed, technical, and contract reading modes; the contract itself is a continuous vertical document with clause links
- Can accept, reject, negotiate, or comment on proposals
- Can share proposal with stakeholders
- Can download PDF version

---

## 5. Non-Functional Requirements

- **Explain disabled controls**: A disabled panel control must state why it is
  unavailable. If the operator can resolve the block, every missing prerequisite
  is shown as adjacent text and remains available on hover, keyboard focus and
  touch; lifecycle, permission and positional limits still expose a specific
  reason. A transient operation uses its active status label. The collection
  account flow additionally warns about clients without email in the selector
  and permits an explicit inline repair without losing the draft.
- **Consistent panel actions**: Every operational action rendered with an icon under `/panel/**` must resolve its glyph and default accessible name from one shared Heroicons 24 Outline catalog. Icon-only controls expose hover/focus help, an accessible name and a touch target of at least 44×44 px; decorative, status and editable-content symbols are not action glyphs.
- **Text containment**: Every panel table, card and metadata row must contain
  arbitrary user/API strings, including values with no spaces, at every canonical
  viewport. Data-owned prose/identifiers wrap with intrinsic-safe break
  opportunities; truncation is allowed only when the complete value remains
  available through a disclosure, tooltip or detail view. Bounded dates, money and
  numeric values may remain atomic.
- **Responsive acceptance**: Every panel and public view must pass the same five automated reference viewports (phone 412 px, portrait tablet 835 px, landscape tablet 1195 px, laptop 1440 px, large monitor 2560 px), followed by the separately evidenced physical-device pass required for final certification. Shared components own repeated behavior; large-monitor content keeps an explicit readable maximum width.
- **Performance**: Hybrid SSR/SPA rendering; SSR for SEO-critical pages (home, landing, portfolio, blog), SPA for admin and proposal views
- **Security**: Dual auth — session/CSRF for `/panel/`, JWT (SimpleJWT) for `/platform/`; staff-only admin endpoints; CORS/CSRF trusted origins; Fernet encryption for project admin credentials (`PROJECT_ACCESS_CIPHER_KEY`)
- **SEO**: Server-side rendered public pages, sitemap endpoints, meta tags, Google verification
- **Analytics**: Google Tag Manager, Google Analytics, Facebook Pixel, Microsoft Clarity, Cal.com booking tracker
- **Email**: SMTP via GoDaddy (smtpout.secureserver.net:465 SSL), HTML + text templates
- **Notifications**: WhatsApp via CallMeBot API
- **Backups**: django-dbbackup with configurable storage path, 4 backup retention
- **Monitoring**: Optional Silk profiler for query analysis (gated by env flag)

---

## 6. Business Rules Summary

1. Each proposal gets a unique UUID for public access
2. Proposals auto-expire when `expires_at < now()` (daily Huey cron)
3. 24h cooldown between automated client-facing emails per proposal
4. Automations can be paused per proposal
5. Engagement heat score (1-10) computed from views, section time, recency
6. Proposal sections map 1:1 to Vue components via `section_type` (18 section types; some are web-only and skip the PDF)
7. Default section content is configurable per language (admin-editable)
8. Email templates are editable and resettable via admin panel
9. Share links track independent view counts from main proposal views
10. Change logs record full audit trail of proposal lifecycle events
11. **Project stage notifications**: Stage rows are admin-managed (not auto-derived from JSON timeline). Warning fires once at 70% elapsed; overdue alert fires immediately when `today > end_date` and repeats every 3 days until `completed_at` is set. All day-level arithmetic uses Bogotá time (`today_bogota()` from `content/utils.py`). Internal team recipients live in `NOTIFICATION_EMAIL` CSV.
12. **Proposal client identity**: `BusinessProposal.client` is a FK to `accounts.UserProfile` filtered to `role='client'` (`on_delete=PROTECT`). Legacy denormalized fields `client_name` / `client_email` / `client_phone` are kept as write-through snapshots, synced via `proposal_client_service.sync_snapshot()` after every FK assignment. Empty client emails get a placeholder `cliente_<profile_id>@temp.example.com` (RFC 2606 reserved TLD) generated via two-step save. Clients with placeholder emails are excluded from **all 13 client-facing email methods** in `ProposalEmailService` and from the 4 huey reminder/urgency/abandonment tasks via `_is_unsendable_client_email(email)`. Two candidate-selection querysets (`abandonment_candidates`, `interest_candidates`) also exclude placeholders directly via `.exclude(client_email__iendswith=UserProfile.PLACEHOLDER_EMAIL_DOMAIN)`. Shipped 2026-04-09.
13. **Project scope items**: an accepted proposal's functional-requirement groups are mirrored into `ProjectScopeItem` rows (chain Project → ProjectPhase → ProjectScopeItem → Requirement) by `technical_requirements_sync`. Re-sync overwrites proposal-authored content unless an admin took over a card (`Requirement.content_overridden=True`); removed items are archived and re-added ones resurrected.
14. **Client document signing**: a client can only sign a `requires_signature` document after their email is verified via OTP. Signing records name/timestamp/IP/user-agent and is idempotent; it fires best-effort team milestone notifications (first login, email validated, document signed) that never block the client flow.
15. **Accounting partner split**: every accounting record carries a total plus per-partner amounts; a record on a personal ledger (Gustavo/Carlos) must be 100% that partner's (the other partner's amount = 0), enforced at `clean()`. Company amount is derived, not stored.
16. **Manual-only discount offer**: the discount/urgency email from the proposal actions menu is never sent automatically — it requires an explicit send and is only offered when a discount percentage is configured and the client has a real email.
17. **Hosting periodicities**: the current commercial offer is quarterly, semiannual, and every 9 months. The nine-month charge is the discounted effective monthly price multiplied by nine. Public proposal views and PDFs preserve the stored annual snapshot for closed/inactive proposals, while new operational project/subscription records always use the current 9/6/3-month catalog. Paid cycles and payments are immutable history.
18. **Contract proposal mode**: `show_contract_terms` is top-level proposal metadata, defaults to `True`, and only produces a public mode for Spanish proposals. It never changes the proposal prompt or section JSON. Preview and draft-PDF endpoints read the current default `ContractTemplate`, never a proposal-specific contract, and are unavailable when the proposal is inactive, English, or has the flag disabled.
19. **Server-owned derived values**: a persisted derived value is never accepted as independent input. When any source changes, the canonical backend write path refreshes the derivative in the same transaction. For recurring payments, `price + currency + current AccountingSettings.usd_exchange_rate → cop_equivalent`, and `cop_equivalent ÷ frequency_months → monthly_cop_cost`; changing the rate synchronizes every recurring row.
20. **Document workflow state**: active document state is derived only from open
    `DocumentStateEpisode` rows. Exclusive cycle states transition each other;
    additive signals may coexist unless the catalog declares an incompatibility.
    Closing means completed work and removing means the state was inapplicable; both
    remain in history as different outcomes.
21. **Document migration truthfulness**: legacy Published becomes client visibility,
    not an inferred cycle state. Existing draft/published documents receive no
    invented cycle classification; old tag assignments become additive episodes
    with unknown effective time, and old private note JSON becomes normalized notes
    with an unknown historical creation time.
22. **Communication history is evidence**: changing a project's client detaches
    its historical communication threads from the project instead of moving them
    to the new client. Deleting clients or documents is blocked while historical
    communication references remain.
23. **Project lifecycle meaning outlives its label**: project billing, reminders
    and closure use `DocumentState.operational_effect`, never an editable display
    name. Every transition is previewed, token-bound and recorded as a dated
    episode; legacy unclassified rows fail closed for financial automation.
24. **Searchable selectors inside modals**: result lists belong to a floating
    layer owned by the modal, not to its scrollable panel. On desktop the picker
    exposes at least five complete options and only a long result list scrolls;
    the modal remains still and grows with its review content up to its viewport
    limit. On narrow screens the modal follows the shared full-screen contract.
    A bulk action must show the affected count and record identities before its
    confirmation without requiring the operator to scroll the modal.
