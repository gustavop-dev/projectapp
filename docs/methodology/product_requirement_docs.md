# Product Requirements Document — ProjectApp

## 1. Overview

**ProjectApp** is the full-stack web application for **Project App** (projectapp.co), a custom software development company based in Colombia. The platform serves as:

1. **Company website** — marketing pages, portfolio showcase, blog, and contact form
2. **Business proposal CRM** — create, send, track, and close personalized proposals for prospective clients

The application is bilingual (English / Spanish) and targets two distinct user personas: the **Admin** (company seller/owner) and the **Client** (prospective customer).

---

## 2. Problems Solved

| Problem | Solution |
|---------|----------|
| No centralized way to create and send client proposals | Full proposal builder with 12 auto-generated sections |
| Proposals sent as static PDFs with no tracking | Interactive fullscreen web experience with engagement analytics |
| No visibility into client interest or behavior | View tracking, section-level time analytics, heat score, engagement signals |
| Manual follow-up prone to human error | Automated email reminders (day 10, day 15, urgency, inactivity, re-engagement) |
| Company portfolio hard to maintain | Admin CRUD panel for portfolio works with bilingual content |
| No blog for SEO/content marketing | Full blog system with structured JSON content, categories, calendar, sitemap |
| Language barrier for international clients | i18n with prefix routing (`/en-us/`, `/es-co/`) for all public pages |

---

## 3. Core Features

### 3.1 Business Proposal System (Flagship)

The proposal system is the most complex and central feature. It allows the admin to:

- **Create proposals** with client name, email, investment amount, currency, expiration date, language, project type, and market type
- **12 sections auto-generated** per proposal: Greeting, Executive Summary, Context & Diagnostic, Conversion Strategy, Design & UX, Creative Support, Development Stages, Functional Requirements, Timeline, Investment, Final Note, Next Steps
- **Edit section content** — each section stores structured JSON matching a specific Vue component's props schema
- **Send to client** — triggers email with unique UUID link, schedules automated reminders
- **Track engagement** — view count, first viewed date, per-section time analytics, session tracking, engagement scoring (heat score 1-10)
- **Share links** — clients can share proposals with stakeholders, each share link tracked independently
- **PDF generation** — downloadable PDF version via ReportLab
- **Investment calculator** — interactive modal for clients to explore payment options (hosting plans, discounts)
- **Client responses** — accept, reject (with reason/comment), or negotiate proposals directly from the proposal page

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

#### Admin Panel — Proposals

- **Dashboard** (`/panel/`): total proposals, status counts, heat scores, recent proposals, alerts
- **Proposals list** (`/panel/proposals/`): table with title, client, status badge, investment, expiry, views, bulk actions
- **Create** (`/panel/proposals/create`): form with all metadata + JSON import option. Client identity is selected via `<ClientAutocomplete>` (searchable dropdown over `accounts.UserProfile` with `role='client'`); typing a brand-new name + email auto-creates a real `UserProfile` row, and an empty email gets a placeholder `cliente_<id>@temp.example.com` that pauses every email automation for that proposal.
- **Edit** (`/panel/proposals/{id}/edit`): Tabs depending on proposal status:
  - **General** — metadata + same `<ClientAutocomplete>` picker + write-through snapshot fields + propagate-changes-to-profile checkbox + send button
  - **Correos** (sent+ statuses) — branded email composer
  - **Documentos** (negotiating/accepted/rejected) — contracts + uploaded annexes
  - **Cronograma** (accepted/finished) — project stage scheduling (design + development dates, mark-as-completed, status badges)
  - **Secciones** — section editor (expand/edit JSON per section)
  - **Det. técnico**, **Prompt Proposal**, **JSON**, **Actividad**, **Analytics**
- **Defaults** (`/panel/proposals/defaults`): manage default section templates per language
- **Email templates** (`/panel/proposals/email-templates`): view/edit/preview/reset email content
- **Email deliverability** (`/panel/proposals/email-deliverability`): dashboard tracking email send/delivery/bounce rates
- **Clients list** (`/panel/clients/`): real `UserProfile` (role=client) entities. Tabs (Todos / Activos / Huérfanos), live search, "+ Nuevo cliente" modal for standalone creation (no invitation email sent — that path is reserved for the platform onboarding flow). Orphan clients (zero proposals + zero platform projects) are deletable via a trash icon gated through `requestConfirm`. Each row expands lazily to load the client's full proposal history. Replaced the legacy "synthetic clients grouped by `(name, email)`" implementation on 2026-04-09.

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
- `Document` model with status lifecycle (draft → published → archived), language (es/en), cover_type (generic/none/proposal)
- Structured JSON content stored in `content_json` field
- PDF generation via `DocumentPdfService` + `MarkdownParser` + shared `PdfUtils` layer
- Admin CRUD panel (`/panel/documents/`) with create, edit, list, status management
- Bilingual support (es/en)

### 3.6 Contract System

- Reusable contract templates (`ContractTemplate`) with customizable sections and parameter substitution
- Contract PDFs generated via `ContractPdfService` using ReportLab + shared `PdfUtils`
- **Draft mode**: generate contract PDF without contractor signature block for review
- **Final mode**: include contractor signature block once contract is agreed
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

### 3.11 Admin Panel Enhancements

- **Panel Login** (`/panel/login`) — dedicated login page for admin panel
- **Panel Admins** (`/panel/admins`) — admin user management (invite, list, manage admin accounts)
- **Internal Kanban Task Board** (`/panel/tareas`) — admin-only Kanban board for managing internal ProjectApp team work. Four columns: TO DO, In Progress, Blocked, Done. Tasks have title, description, status, priority (low/medium/high), assignee (FK to any admin User, optional), and due_date (optional). Cards display priority badge and due_date highlighted in red when overdue. Drag-and-drop between columns and reorder within columns via vuedraggable. Create/edit modal with confirm-guarded delete. Tasks are independent — no FK link to proposals or documents.

### 3.12 Internationalization (i18n)

- Two locales: `en-us` (English, default) and `es-co` (Spanish Colombia)
- Prefix strategy: `/en-us/about-us`, `/es-co/about-us`
- Lazy-loaded translation files
- Geo-locale detection plugin for automatic language suggestion
- Language store with sync plugin

---

## 4. Target Users

### Admin (Seller / Company Owner)
- Creates and manages business proposals
- Tracks client engagement and follows up
- Manages portfolio works and blog content
- Receives notifications via email and WhatsApp

### Client (Prospect)
- Receives unique proposal link via email
- Views fullscreen proposal experience with horizontal scroll
- Can accept, reject, negotiate, or comment on proposals
- Can share proposal with stakeholders
- Can download PDF version

---

## 5. Non-Functional Requirements

- **Performance**: Hybrid SSR/SPA rendering; SSR for SEO-critical pages (home, landing, portfolio, blog), SPA for admin and proposal views
- **Security**: Django session + CSRF authentication; no JWT; staff-only admin endpoints; CORS/CSRF trusted origins
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
6. Proposal sections map 1:1 to Vue components via `section_type`
7. Default section content is configurable per language (admin-editable)
8. Email templates are editable and resettable via admin panel
9. Share links track independent view counts from main proposal views
10. Change logs record full audit trail of proposal lifecycle events
11. **Project stage notifications**: Stage rows are admin-managed (not auto-derived from JSON timeline). Warning fires once at 70% elapsed; overdue alert fires immediately when `today > end_date` and repeats every 3 days until `completed_at` is set. All day-level arithmetic uses Bogotá time (`today_bogota()` from `content/utils.py`). Internal team recipients live in `NOTIFICATION_EMAIL` CSV.
12. **Proposal client identity**: `BusinessProposal.client` is a FK to `accounts.UserProfile` filtered to `role='client'` (`on_delete=PROTECT`). Legacy denormalized fields `client_name` / `client_email` / `client_phone` are kept as write-through snapshots, synced via `proposal_client_service.sync_snapshot()` after every FK assignment. Empty client emails get a placeholder `cliente_<profile_id>@temp.example.com` (RFC 2606 reserved TLD) generated via two-step save. Clients with placeholder emails are excluded from **all 13 client-facing email methods** in `ProposalEmailService` and from the 4 huey reminder/urgency/abandonment tasks via `_is_unsendable_client_email(email)`. Two candidate-selection querysets (`abandonment_candidates`, `interest_candidates`) also exclude placeholders directly via `.exclude(client_email__iendswith=UserProfile.PLACEHOLDER_EMAIL_DOMAIN)`. Shipped 2026-04-09.