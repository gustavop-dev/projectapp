# User Flow Map

> **Version:** 2.10.0
> **Last updated:** 2026-04-03
> **Scope:** Complete map of end-to-end user navigation flows for projectapp, organized by role.
> **Sources:** Frontend pages (`frontend/pages/`), backend API endpoints (`content/urls.py`, `accounts/urls.py`), route rules (`nuxt.config.ts`).

---

## Table of Contents

1. [Roles](#1-roles)
2. [Conventions](#2-conventions)
3. [Shared Flows (Guest + Admin)](#3-shared-flows-guest--admin)
4. [Guest Flows](#4-guest-flows)
5. [Proposal Flows (Guest via UUID)](#5-proposal-flows-guest-via-uuid)
6. [Admin Flows](#6-admin-flows)
7. [E2E Coverage Index](#7-e2e-coverage-index)
8. [Platform Flows](#8-platform-flows)

---

## 1. Roles

| Role | Description | Auth Required |
|------|-------------|---------------|
| **Guest** | Unauthenticated visitor browsing the public site | No |
| **Admin** | Staff user managing content via the `/panel/` admin frontend | Yes (Django session) |
| **Platform-Admin** | Staff user managing clients, projects and kanban via `/platform/` | Yes (JWT) |
| **Platform-Client** | Invited client accessing their projects via `/platform/` | Yes (JWT) |

> **Excluded:** Django Admin (`/admin/`) is managed by Django's built-in admin interface and is not covered by E2E tests.

---

## 2. Conventions

### Flow ID Format

- **Kebab-case**, prefixed with module name: `public-home`, `blog-list`, `proposal-view`, `admin-blog-create`
- Cross-role flows use `cross-` infix (not applicable in this project currently)

### Priority Levels

| Level | Meaning | Criteria |
|-------|---------|----------|
| **P1** | Critical | Core business flow — blocks release if missing |
| **P2** | High | Important feature — should be covered before release |
| **P3** | Medium | Secondary feature — cover after P1/P2 |
| **P4** | Nice-to-have | Informational pages, low risk |

### Coverage Statuses

| Status | Symbol | Meaning |
|--------|--------|---------|
| Covered | ✅ | E2E spec exists and passes |
| Partial | ⚠️ | E2E spec exists but has known gaps |
| Missing | ❌ | No E2E spec yet |

### Branch Notation

- **[Branch A]** / **[Branch B]** — Alternative outcomes within a flow
- **[Optional]** — Step that may or may not occur

### E2E scope decisions (audit follow-up)

- **TechnicalDocumentEditor (panel):** No dedicated flow ID. Scope remains within `admin-proposal-edit` and `admin-proposal-defaults-config`; client-facing technical reading is covered by `proposal-technical-view`.
- **Panel sidebar (collapse / mobile drawer):** No dedicated flow ID. Exercised indirectly by specs that load `/panel` routes using the admin layout.

### Backend-only and system-triggered flows (not browser E2E)

Entries in `flow-definitions.json` with `roles: ["system"]` and `expectedSpecs: 0` describe **automations** (Huey/cron, alert generation, digests). They remain in the registry for traceability to backend tests but are **out of scope** for Playwright user-journey coverage. Examples: `proposal-pre-expiration-discount-suggestion`, `admin-seller-inactivity-escalation`, `admin-daily-pipeline-digest`, `admin-high-engagement-alert`, `admin-calculator-followup-alert`, `admin-whatsapp-suggestion`, `admin-auto-archive-zombie`, `admin-proposal-engagement-decay-alert`, `admin-proposal-post-rejection-revisit`, `proposal-calculator-abandonment-tracking`.

---

## 3. Shared Flows (Guest + Admin)

### FLOW: `layout-navbar-navigation`

- **Module:** layout
- **Role:** guest/admin
- **Priority:** P2
- **Routes:** All pages
- **Description:** Navigate between pages using the glassmorphism pill navbar with sliding lemon indicator.
- **Steps:**
  1. User sees the glassmorphism pill navbar fixed at the top of the page.
  2. User clicks a navigation link (Custom Software, App Development, Our work, Blog, Contact/WhatsApp).
  3. Page navigates to the selected route.
  4. Lemon pill indicator slides to highlight the active section.
- **Branches:**
  - [Branch A] User toggles language via EN/ES button → page reloads in selected locale (`/en-us/` or `/es-co/`).
  - [Branch B] User clicks Contact (WhatsApp) → external link opens.
  - [Branch C — Mobile] Hamburger menu opens with navigation links + WhatsApp CTA button.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/layout/layout-navbar.spec.js`

### FLOW: `layout-locale-switch`

- **Module:** layout
- **Role:** guest/admin
- **Priority:** P2
- **Routes:** All pages with locale prefix (`/en-us/`, `/es-co/`)
- **Description:** Switch the application language between English and Spanish.
- **Steps:**
  1. User clicks the locale switcher component in the navbar.
  2. User selects a different language.
  3. URL updates with the new locale prefix.
  4. Page content re-renders in the selected language.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/layout/layout-locale.spec.js`

### FLOW: `layout-footer-navigation`

- **Module:** layout
- **Role:** guest/admin
- **Priority:** P3
- **Routes:** All pages
- **Description:** Navigate using footer links and social media links.
- **Steps:**
  1. User scrolls to the footer section.
  2. User clicks a footer link (social media, navigation, or contact).
  3. Page navigates or external link opens.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/layout/layout-footer.spec.js`

---

## 4. Guest Flows

### FLOW: `public-home`

- **Module:** public
- **Role:** guest
- **Priority:** P1
- **Routes:** `/`, `/en-us`, `/es-co`
- **Description:** View the public home/landing page with hero, services, study cases, portfolio and contact sections.
- **Steps:**
  1. User navigates to the home page.
  2. Hero section renders with animations.
  3. TechStack section displays technology logos.
  4. Services cards section renders with service offerings.
  5. Study cases section displays project showcases.
  6. Bento grid section renders.
  7. Contract section and contact form section render.
  8. Marquee strips and Book-a-Call section render.
  9. Footer section renders with links.
- **Branches:**
  - [Branch A] User fills contact form → form submits via API → success feedback.
  - [Branch B] User clicks "Book a Call" → external booking link opens.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-home.spec.js`

### FLOW: `public-portfolio`

- **Module:** public
- **Role:** guest
- **Priority:** P2
- **Routes:** `/portfolio-works`, `/en-us/portfolio-works`, `/es-co/portfolio-works`
- **Description:** Browse portfolio works listing page (Awwwards-style) with hero section, animated gradient, and project cards linking to case study detail pages.
- **Steps:**
  1. User navigates to the portfolio page.
  2. Hero section renders with animated gradient background.
  3. Portfolio works load from API (`GET /api/portfolio/`).
  4. Project cards render with title, excerpt, cover image, and "View" link.
  5. User clicks a project card.
  6. Page navigates to `/portfolio-works/:slug`.
- **Branches:**
  - [Branch A] Empty state renders when no projects are published.
  - [Branch B] Loading spinner renders while data is being fetched.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-pages.spec.js`

### FLOW: `public-portfolio-detail`

- **Module:** public
- **Role:** guest
- **Priority:** P2
- **Routes:** `/portfolio-works/:slug`, `/en-us/portfolio-works/:slug`, `/es-co/portfolio-works/:slug`
- **Description:** View a single portfolio case study (Awwwards-style) with cover image, content sections, share button, project URL link, and back navigation.
- **Steps:**
  1. User clicks a project from the portfolio listing or navigates directly to `/portfolio-works/:slug`.
  2. Case study data loads from API (`GET /api/portfolio/:slug/`).
  3. Title, excerpt, cover image, and share button render.
  4. Content sections render (JSON-structured content or HTML fallback).
  5. Back link to `/portfolio-works` is visible.
  6. [Optional] "Visit project" link renders if `project_url` exists.
- **Branches:**
  - [Branch A — Not found] 404 page renders with "Back to portfolio" link.
  - [Branch B — Share] User clicks share button to share the case study.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-portfolio-detail.spec.js`

> **Archived Flows:** The following pages were moved to `_archived/` and are no longer accessible via navigation:
> `public-web-designs`, `public-3d-animations`, `public-hosting`, `public-ecommerce-prices`, `public-custom-software`.
> They were previously covered by `e2e/public/public-pages.spec.js`.

### FLOW: `public-about-us` *(ARCHIVED)*

- **Module:** public
- **Role:** guest
- **Priority:** P3
- **Routes:** `/about-us` *(page exists but is no longer linked from navigation)*
- **Description:** View the about us page with team and company information.
- **Status:** ARCHIVED — removed from navbar and footer. No internal links point to this page.
- **Coverage:** ❌ E2E test removed (flow archived)

### FLOW: `public-landing-web-design`

- **Module:** public
- **Role:** guest
- **Priority:** P2
- **Routes:** `/landing-web-design`, `/en-us/landing-web-design`, `/es-co/landing-web-design`
- **Description:** View the web design landing page (marketing/conversion page).
- **Steps:**
  1. User navigates to the landing web design page.
  2. Landing page content renders with hero, features, CTA.
  3. Contact form section renders.
- **Branches:**
  - [Branch A] User submits contact form → API call → success feedback.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-pages.spec.js`

### FLOW: `public-contact-submit`

- **Module:** public
- **Role:** guest
- **Priority:** P1
- **Routes:** `/contact`, `/en-us/contact`, `/es-co/contact` → `/contact-success`
- **Description:** Submit a contact form to reach the company.
- **Steps:**
  1. User navigates to the contact page.
  2. Contact form renders with fields (name, email, message, etc.).
  3. User fills in the form fields.
  4. User submits the form.
  5. API call to `POST /api/new-contact/`.
  6. On success, user is redirected to `/contact-success`.
- **Branches:**
  - [Branch A — Validation error] Form shows inline validation errors, user corrects and resubmits.
  - [Branch B — API error] Error message displays, form remains editable.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-contact.spec.js`

### FLOW: `blog-list`

- **Module:** blog
- **Role:** guest
- **Priority:** P2
- **Routes:** `/blog`, `/en-us/blog`, `/es-co/blog`
- **Description:** Browse the blog post listing with bilingual support.
- **Steps:**
  1. User navigates to the blog index page.
  2. Blog posts load from API (`GET /api/blog/?lang=es|en`).
  3. Post grid renders with titles, excerpts, and cover images.
  4. Language is resolved from the URL locale prefix.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/blog/blog-list.spec.js`

### FLOW: `blog-detail`

- **Module:** blog
- **Role:** guest
- **Priority:** P2
- **Routes:** `/blog/:slug`, `/en-us/blog/:slug`, `/es-co/blog/:slug`
- **Description:** Read a single blog post with bilingual content.
- **Steps:**
  1. User clicks a blog post from the listing.
  2. Blog post detail loads from API (`GET /api/blog/:slug/?lang=es|en`).
  3. Post content renders with title, content, sources.
  4. Navigation back to blog listing is available.
- **Branches:**
  - [Branch A — Post not found] 404 page or error message displays.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/blog/blog-detail.spec.js`

---

## 5. Proposal Flows (Guest via UUID)

### FLOW: `proposal-view`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** View a business proposal shared via unique UUID link with horizontal scroll navigation.
- **Steps:**
  1. User opens the proposal URL with UUID.
  2. Proposal data loads from API (`GET /api/proposals/:uuid/`).
  3. Proposal index page renders with title, client info, expiration badge.
  4. User navigates through proposal sections using horizontal scroll (GSAP).
  5. Section counter updates as user navigates.
  6. User reads requirement groups and items within sections.
- **Branches:**
  - [Branch A — Proposal expired] Expired proposal page renders with expiration message.
  - [Branch B — Proposal not found] 404 or error page renders.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-view.spec.js`

### FLOW: `proposal-view-navigation`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** Navigate between proposal sections using prev/next arrow buttons and the ProposalIndex side panel. Includes SectionNavButtons (with `hideLeft` when index is open), ProposalIndex (floating hamburger menu listing all sections), and SectionCounter.
- **Steps:**
  1. User opens the proposal URL.
  2. First section renders. Next button (`nav-side--right`) is visible; Prev button absent.
  3. User clicks next button → transition animation → second section renders.
  4. Prev button (`nav-side--left`) now visible.
  5. User clicks hamburger toggle (`.index-toggle`) → ProposalIndex panel opens.
  6. While index is open, prev button is hidden (`hideLeft` prop).
  7. User clicks an index item → navigates directly to that section → index closes.
  8. On last panel (proposal_closing), next button disappears.
- **Branches:**
  - [Branch A — Index navigation] User jumps to any section via ProposalIndex.
  - [Branch B — Sequential navigation] User steps through each section one by one.
  - [Branch C — Mobile swipe] Touch swipe left/right triggers navigation.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-view-navigation.spec.js`

### FLOW: `proposal-view-onboarding`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P3
- **Routes:** `/proposal/:uuid`
- **Description:** First-visit tutorial overlay (ProposalOnboarding component) that shows step-by-step tooltips guiding the client through the proposal interface. After completion, a reading-time popup appears.
- **Steps:**
  1. User opens the proposal for the first time.
  2. ProposalOnboarding overlay appears with first tooltip step.
  3. User clicks through each onboarding step.
  4. Onboarding completes and emits `@complete` event.
  5. Reading time popup appears: "Tiempo de lectura: ~7 minutos".
  6. User clicks "Entendido" to dismiss popup.
- **Branches:**
  - [Branch A — Returning visitor] Onboarding is skipped if already seen (localStorage flag).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-onboarding.spec.js`

### FLOW: `proposal-section-onboarding`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P3
- **Routes:** `/proposal/:uuid`
- **Description:** Per-section spotlight onboarding tutorials that trigger automatically the first time a client navigates to specific sections. Each section has its own component with a spotlight overlay (blur backdrop + cloned element), progress dots, and positioned tooltip card. Tutorials are skipped for returning visitors (localStorage flag per proposal UUID).
- **Steps:**
  1. Client navigates to the Investment section for the first time (detailed view, with calculator modules).
  2. InvestmentOnboarding component triggers after 800ms delay.
  3. Spotlight highlights the "Personalizar tu inversión" button with a tooltip explaining the calculator.
  4. Client clicks through onboarding steps → completes → localStorage flag set.
  5. [Separate trigger] Client navigates to functional_requirements section.
  6. RequirementsOnboarding component triggers after 800ms delay.
  7. Spotlight highlights requirement group cards with a tooltip explaining how to expand them.
  8. [Separate trigger] Client in executive view navigates to investment section.
  9. ExecutiveInvestmentOnboarding triggers, highlighting the "Ver detalle" teaser button.
- **Branches:**
  - [Branch A — Detailed Investment] InvestmentOnboarding triggers only in detailed view when calculator modules exist.
  - [Branch B — Executive Investment] ExecutiveInvestmentOnboarding triggers only in executive view.
  - [Branch C — Requirements] RequirementsOnboarding triggers in both view modes.
  - [Branch D — Returning visitor] Each tutorial is skipped if already completed (per-UUID localStorage flag).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-section-onboarding.spec.js`
- **Components:** `InvestmentOnboarding.vue`, `RequirementsOnboarding.vue`, `ExecutiveInvestmentOnboarding.vue`

### FLOW: `proposal-executive-to-detailed`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Client switches from executive view to the full detailed proposal view via the "Ver Propuesta Completa" button in the ProposalIndex sidebar, or via the teaser button in the executive Investment section. A branded transition overlay (esmerald background with lemon icon + loading text) plays during the mode switch. The page scrolls to top and renders all sections.
- **Steps:**
  1. Client is viewing the proposal in executive mode (filtered sections).
  2. Client opens the ProposalIndex sidebar menu.
  3. Client clicks "Ver Propuesta Completa" button at the bottom of the sidebar.
  4. ProposalIndex emits `switchToDetailed` event and closes.
  5. Branded transition overlay appears (esmerald bg, lemon bouncing icon, "Cargando propuesta completa…").
  6. After ~1s, `viewMode` switches from `'executive'` to `'detailed'`, all sections render.
  7. Overlay fades out, page scrolls to top.
  8. Client can now navigate all proposal sections.
- **Branches:**
  - [Branch A — From sidebar] Client clicks "Ver Propuesta Completa" in ProposalIndex.
  - [Branch B — From Investment teaser] Executive Investment section has a teaser button that also triggers `switchToDetailed`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-executive-to-detailed.spec.js`
- **Components:** `ProposalIndex.vue` (`switchToDetailed` emit), `[uuid]/index.vue` (`handleSwitchToDetailed`)

### FLOW: `proposal-technical-view`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid?mode=technical`
- **Description:** Third gateway option when `technical_document` is enabled: carousel of synthetic panels from `content_json` (intro, stack, architecture, etc.) plus `proposal_closing`. PDF download uses `?doc=technical`. Tracking sends `view_mode: technical`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-technical-view.spec.js`
- **Components:** `ProposalViewGateway.vue`, `TechnicalDocumentPublicPanel.vue`, `[uuid]/index.vue`, `technicalProposalPanels.js`

### FLOW: `proposal-respond`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** Client responds to (accepts/rejects) a business proposal from the ProposalClosing panel. Accept button has visual dominance (larger, glow, pulse animation). Acceptance triggers a confetti celebration animation via `canvas-confetti`.
- **Steps:**
  1. User views the proposal and navigates to the closing panel.
  2. Accept/reject buttons visible when `proposal.status` is `sent` or `viewed`. Accept button is visually dominant (larger, green glow, subtle pulse).
  3. User clicks "Acepto la propuesta" → confirmation modal opens.
  4. User confirms → API call to `POST /api/proposals/:uuid/respond/` with `decision: accepted`.
  5. Success state: confetti animation fires (canvas-confetti), bouncing 🎉 emoji, "¡Propuesta aceptada!" message renders.
- **Branches:**
  - [Branch A — Accept] Client clicks accept → confirm modal → API → confetti animation + success message.
  - [Branch B — Reject] Client clicks "Rechazar propuesta" → reject modal (select reason + comment) → API → smart recovery message.
  - [Branch C — Already responded] Buttons hidden, status message shown.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-respond.spec.js`

### FLOW: `proposal-download-pdf`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Download a proposal as PDF.
- **Steps:**
  1. User views the proposal.
  2. User clicks the download PDF button.
  3. API call to `GET /api/proposals/:uuid/pdf/`.
  4. PDF file downloads to user's device.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-pdf.spec.js`

### FLOW: `proposal-share`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Client shares the proposal with a team member or stakeholder via the share button. A tracked share link is created, and the recipient receives an email notification.
- **Steps:**
  1. User views the proposal.
  2. User clicks the share button (ShareProposalButton component).
  3. User fills in recipient name and email.
  4. API call to `POST /api/proposals/:uuid/share/`.
  5. Backend creates a ProposalShareLink record.
  6. Share notification email is sent to the recipient.
  7. Success feedback displays.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-share.spec.js`

### FLOW: `proposal-engagement-tracking`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Automatic tracking of client engagement while viewing a proposal. The frontend composable `useProposalTracking` sends section-level time data to the backend, which records view events and section views, detects stakeholders by IP, and triggers smart follow-up alerts.
- **Steps:**
  1. User opens a proposal page.
  2. `useProposalTracking` composable initializes and generates a session ID.
  3. As user navigates sections, time spent per section is recorded.
  4. Periodically, engagement data is sent via `POST /api/proposals/:uuid/track/`.
  5. Backend creates/updates ProposalViewEvent and ProposalSectionView records.
  6. [Optional] If ≥3 unique sessions detected, a revisit alert email is sent to the admin.
  7. [Optional] If a new IP is detected, a stakeholder detection alert is sent.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-engagement-tracking.spec.js`

---

## 6. Admin Flows

### FLOW: `admin-login`

- **Module:** auth
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/login` → `/panel/`
- **Description:** Admin authenticates to access the management panel.
- **Steps:**
  1. User navigates to `/panel/login`.
  2. Login page renders with link to Django Admin.
  3. User authenticates via Django Admin (`/admin/`).
  4. Auth check verifies session (`GET /api/auth/check/`).
  5. User is redirected to `/panel/` dashboard.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/auth/auth-admin-login.spec.js`

### FLOW: `admin-dashboard`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/`
- **Description:** View the admin dashboard with overview of proposals and blog posts.
- **Steps:**
  1. Authenticated admin navigates to `/panel/`.
  2. Dashboard renders with summary data.
  3. Quick links to proposal and blog management are available.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-dashboard.spec.js`

### FLOW: `admin-proposal-list`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/`
- **Description:** View the list of all business proposals. Table includes heat score badge (1-10, color-coded), "días sin actividad" red badge for inactive proposals, WhatsApp quick-action in dropdown, and a floating metrics manual button.
- **Steps:**
  1. Admin navigates to `/panel/proposals/`.
  2. Proposals load from API (`GET /api/proposals/`) with `heat_score` per proposal.
  3. Proposal table renders with status, client, dates, 🔥 heat score column, and inactivity badges.
  4. Actions dropdown includes "Enviar por WhatsApp" with pre-filled contextual message.
  5. Floating "?" button opens the MetricsManual slide-over with searchable metric definitions.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-list.spec.js`

### FLOW: `admin-proposal-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/create`
- **Description:** Create a new business proposal (manual mode) with 12 auto-generated default sections.
- **Steps:**
  1. Admin navigates to `/panel/proposals/create`.
  2. Page loads with Manual / Importar JSON tab toggle.
  3. Manual tab is active by default — form renders with Título, Nombre del cliente, Email del cliente, Idioma, etc.
  4. Admin fills in the fields and submits.
  5. API call to `POST /api/proposals/create/`.
  6. Backend auto-creates 12 default sections and returns the full proposal.
  7. Admin is redirected to `/panel/proposals/:id/edit`.
- **Branches:**
  - [Branch A — Validation error] Form shows errors, admin corrects and resubmits.
  - [Branch B — JSON import] Admin switches to "Importar JSON" tab (see `admin-proposal-create-from-json`).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-create.spec.js`

### FLOW: `admin-proposal-create-from-json`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/create` (JSON import tab)
- **Description:** Admin creates a proposal by importing a pre-filled JSON payload (e.g., exported from a template). All 12 section `content_json` values are provided in the payload. Missing sections fall back to defaults.
- **Steps:**
  1. Admin navigates to `/panel/proposals/create`.
  2. Admin clicks "Importar JSON" tab.
  3. JSON textarea/file input appears.
  4. Admin pastes or loads a valid JSON payload (must include `sections.general.clientName`).
  5. Admin submits.
  6. API call to `POST /api/proposals/create-from-json/` with `ProposalFromJSONSerializer` validation.
  7. Backend creates proposal + all 12 sections with the provided `content_json`.
  8. Admin is redirected to `/panel/proposals/:id/edit`.
- **Branches:**
  - [Branch A — Missing general key] Validation error `sections.general required`.
  - [Branch B — Past expires_at] Validation error on date.
  - [Branch C — Partial sections] Unspecified sections default to template defaults.
  - [Branch D — `_meta` key] Stripped from sections before saving.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-create.spec.js`

### FLOW: `admin-proposal-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit`
- **Description:** Edit an existing business proposal.
- **Steps:**
  1. Admin navigates to `/panel/proposals/:id/edit`.
  2. Proposal data loads from API (`GET /api/proposals/:id/detail/`).
  3. Edit form renders pre-filled with current data.
  4. Admin modifies proposal details, sections, requirements.
  5. Admin saves changes.
  6. API call to `PATCH /api/proposals/:id/update/`.
  7. Success feedback displays.
- **Branches:**
  - [Branch A] Admin reorders sections → `POST /api/proposals/:id/reorder-sections/`.
  - [Branch B] Admin updates individual section → `PATCH /api/proposals/sections/:id/update/`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-edit.spec.js`

### FLOW: `admin-proposal-section-edit-form`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (Sections tab)
- **Description:** Admin edits a proposal section using the structured form fields. Each of the 12 section types has its own form layout (greeting, executive_summary, context_diagnostic, conversion_strategy, design_ux, creative_support, development_stages, functional_requirements, timeline, investment, final_note, next_steps). When saved in form mode, `_editMode: 'form'` is stored in content_json and the client sees the structured presentation.
- **Steps:**
  1. Admin opens a proposal in edit mode and navigates to the "Secciones" tab.
  2. Admin selects a section to edit.
  3. SectionEditor renders the form fields specific to the section type.
  4. Admin fills/modifies the form fields (text inputs, textareas, repeatable items).
  5. Admin clicks "Guardar Sección".
  6. Component emits save event with `{ sectionId, payload: { title, is_wide_panel, content_json } }`.
  7. content_json includes `_editMode: 'form'` (no `rawText`).
  8. API call to `PATCH /api/proposals/sections/:id/update/` with the content_json.
  9. Backend stores the content_json as-is in the ProposalSection model.
  10. Success feedback "✓ Guardado" displays.
  11. Next time admin expands the section, it opens in "Formulario" mode.
- **Branches:**
  - [Branch A — Each section type] Form layout differs: greeting has clientName + inspirationalQuote; executive_summary has paragraphs + highlights; conversion_strategy has steps with bullets; functional_requirements has nested groups with items; timeline has phases with tasks; investment has whatsIncluded + paymentOptions; etc.
  - [Branch B — Repeatable items] Admin adds/removes steps, stages, phases, groups, items, badges, payment options, contact methods via + / Eliminar buttons.
  - [Branch C — Client view] When `_editMode: 'form'`, the client-facing proposal renders the section using its structured component (e.g., ExecutiveSummary, ConversionStrategy).
- **Coverage:** ⚠️ Partial
- **E2E Spec:** `e2e/admin/admin-proposal-section-form.spec.js`
- **Unit Tests:** `test/components/SectionEditor.test.js`
- **Backend Tests:** `content/tests/views/test_section_update_views.py`

### FLOW: `admin-proposal-section-edit-paste`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (Sections tab)
- **Description:** Admin uses the "Pegar contenido" mode to save raw text content for a section. The paste textarea auto-syncs from form fields via `formToReadableText()`. When saved in paste mode, `_editMode: 'paste'` and `rawText` are stored in content_json. The client-facing proposal renders paste sections using `RawContentSection.vue` — a rounded card with markdown rendering — instead of the structured component.
- **Steps:**
  1. Admin opens a section in the SectionEditor.
  2. Admin clicks the "Pegar contenido" toggle button (switches from "Formulario" mode).
  3. A large textarea (rows=18) appears, pre-filled with `formToReadableText()` output from the current form fields.
  4. Admin types or pastes content (supports Markdown formatting).
  5. Admin clicks "Guardar Sección".
  6. content_json includes `_editMode: 'paste'` and `rawText` with the textarea content.
  7. API call to `PATCH /api/proposals/sections/:id/update/`.
  8. Backend stores `_editMode` and `rawText` in content_json.
  9. Success feedback "✓ Guardado" displays.
  10. Next time admin expands the section, it opens in "Pegar contenido" mode (remembers last saved mode).
- **Branches:**
  - [Branch A — Form auto-sync] As admin fills form fields, the paste textarea dynamically updates when toggling to paste mode.
  - [Branch B — Toggle back to form] Admin switches back to "Formulario" → saves with `_editMode: 'form'`, no `rawText`.
  - [Branch C — Empty paste] Saves `rawText` as empty string.
  - [Branch D — Client view] When `_editMode: 'paste'`, the client-facing proposal renders `RawContentSection` with the section title and the pasted content in a rounded card (`bg-gray-50/80 backdrop-blur-sm border rounded-2xl`) with Markdown rendered via `marked` + `DOMPurify`.
- **Coverage:** ⚠️ Partial
- **E2E Spec:** `e2e/admin/admin-proposal-section-paste.spec.js`
- **Unit Tests:** `test/components/SectionEditor.test.js`
- **Backend Tests:** `content/tests/views/test_section_update_views.py`

### FLOW: `admin-proposal-section-reorder`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Secciones tab)
- **Description:** Admin reorders the sections within a proposal.
- **Steps:**
  1. Admin views the sections list in the edit page.
  2. Admin changes the order of sections.
  3. API call to `POST /api/proposals/:id/reorder-sections/` with `{ sections: [{id, order}] }`.
  4. Sections re-render in the new order.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-section-reorder.spec.js`

### FLOW: `admin-proposal-functional-requirements-form`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (Sections tab → functional_requirements section)
- **Description:** Admin manages functional requirement groups (Views, Components, Features, Admin Module) and their items using the form interface.
- **Steps:**
  1. Admin opens the functional_requirements section editor.
  2. Four default groups render: Views, Components, Features, Admin Module.
  3. Admin edits group fields: icon, title, description.
  4. Admin adds items to a group: icon, name, description.
  5. Admin removes items from a group.
  6. Admin adds additional modules via "+ Agregar módulo adicional".
  7. Admin saves the section → content_json includes groups[] and additionalModules[] with per-group `_editMode`.
- **Coverage:** ⚠️ Partial
- **E2E Spec:** `e2e/admin/admin-proposal-requirements.spec.js`
- **Unit Tests:** `test/components/SectionEditor.test.js`
- **Backend Tests:** `content/tests/views/test_section_update_views.py`

### FLOW: `admin-proposal-functional-requirements-paste`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (Sections tab → functional_requirements section)
- **Description:** Admin uses the per-group "Pegar contenido" mode to save raw text for individual requirement groups. Each group and additional module has its own paste toggle. When a group is in paste mode, the client-facing proposal renders that group as a `RawContentSection` with Markdown.
- **Steps:**
  1. Admin opens the functional_requirements section editor.
  2. Admin clicks "Pegar contenido" on a specific group (e.g., Views).
  3. A textarea (rows=10) appears within that group, pre-filled via `groupToReadableText()`.
  4. Admin types or pastes content.
  5. Admin saves the section → group's `_editMode: 'paste'` and `rawText` are stored in content_json.
  6. On next open, the group remembers paste mode.
- **Branches:**
  - [Branch A — Mixed modes] Some groups in form mode, others in paste mode → each saved independently.
  - [Branch B — Client view] Groups with `_editMode: 'paste'` render as `RawContentSection` in the client proposal.
- **Coverage:** ⚠️ Partial
- **E2E Spec:** `e2e/admin/admin-proposal-requirements.spec.js`
- **Unit Tests:** `test/components/SectionEditor.test.js`
- **Backend Tests:** `content/tests/views/test_section_update_views.py`

### FLOW: `admin-proposal-delete`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Delete an existing business proposal.
- **Steps:**
  1. Admin views the proposal list.
  2. Admin clicks delete on a proposal.
  3. Confirmation dialog appears.
  4. Admin confirms deletion.
  5. API call to `DELETE /api/proposals/:id/delete/`.
  6. Proposal is removed from the list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-delete.spec.js`

### FLOW: `admin-proposal-duplicate`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Duplicate an existing proposal to create a new draft copy with the same sections and content.
- **Steps:**
  1. Admin views the proposal list or detail page.
  2. Admin clicks "Duplicar" on a proposal.
  3. API call to `POST /api/proposals/:id/duplicate/`.
  4. Backend creates a new proposal with status=draft, copying all sections and content.
  5. Admin is redirected to the new proposal's edit page.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-duplicate.spec.js`

### FLOW: `admin-proposal-comment`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/proposals/:id/edit`
- **Description:** Add internal comments to a proposal for team collaboration.
- **Steps:**
  1. Admin opens a proposal in edit mode.
  2. Admin writes a comment in the comment field.
  3. API call to `POST /api/proposals/:id/comment/`.
  4. Comment is saved and a changelog entry is created.
  5. Comment notification email is sent to the client.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-comment.spec.js`

### FLOW: `admin-proposal-analytics`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Analytics tab)
- **Description:** View detailed analytics for a single proposal including engagement funnel, section time heatmap, device breakdown, shared links, session history, suggested actions, and CSV export. Technical engagement unifies `technical_document` (sección) and `technical_document_public` (paneles en modo técnico) for skip list, funnel, `technical_engagement`, engagement score, and CSV “Metric group”.
- **Steps:**
  1. Admin opens a proposal and navigates to the Analytics tab.
  2. ProposalAnalytics component loads data from `GET /api/proposals/:id/analytics/`.
  3. Summary cards render (views, unique sessions, avg time, bounce rate).
  4. Comparison badges show performance vs portfolio average.
  5. Engagement funnel visualization renders (Sent → Viewed → Engaged → Responded).
  6. Section time heatmap shows color-coded bars per section.
  7. Shared links table renders if any ProposalShareLinks exist.
  8. Activity timeline and session history display.
  9. [Optional] Admin clicks "Exportar CSV" to download analytics data.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-analytics.spec.js`

### FLOW: `admin-proposal-dashboard`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/` (Dashboard KPI section)
- **Description:** View global KPI dashboard for all proposals: total proposals, conversion rate, average time to first view, average time to response, average value by status, status distribution, top rejection reasons, monthly trends, discount vs no-discount close rates, win rate by predominant tracking view mode (ejecutiva / completa / técnica), and top drop-off section scoped to commercial section types (excluye doc. técnico y paneles sintéticos).
- **Steps:**
  1. Admin navigates to `/panel/`.
  2. ProposalDashboard component loads data from `GET /api/proposals/dashboard/`.
  3. KPI cards render with total proposals, conversion rate, avg time metrics.
  4. Status distribution chart renders.
  5. Top rejection reasons list renders.
  6. Monthly trend data renders.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-dashboard.spec.js`

### FLOW: `admin-proposal-defaults-config`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/defaults`
- **Description:** Admin manages the default section configurations used when creating new proposals. Supports both ES and EN languages. Changes are saved to a DB-backed config and applied to all future proposals. Includes reset-to-hardcoded functionality.
- **Steps:**
  1. Admin navigates to `/panel/proposals/defaults` via the "Valores por Defecto" button on the proposals list page.
  2. Default sections load from API (`GET /api/proposals/defaults/?lang=es`).
  3. Language selector allows switching between Español and English.
  4. Section accordion list renders with all default sections (same structure as proposal edit).
  5. Admin expands a section and edits its content using SectionEditor (form or paste mode).
  6. Section is marked as "Modificado" locally.
  7. Admin clicks "Guardar Todos los Cambios".
  8. API call to `PUT /api/proposals/defaults/` with the full sections_json array.
  9. Success feedback displays.
- **Branches:**
  - [Branch A — Reset] Admin clicks "Restaurar valores originales" → confirmation modal → `POST /api/proposals/defaults/reset/` → sections reload from hardcoded defaults.
  - [Branch B — Language switch with unsaved changes] Confirmation prompt warns about losing changes.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-defaults.spec.js`
- **Backend Tests:** `content/tests/views/test_proposal_defaults_views.py`, `content/tests/models/test_proposal_default_config.py`, `content/tests/services/test_proposal_service.py::TestGetDefaultSectionsFromDB`

### FLOW: `admin-email-templates-config`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/email-templates`
- **Description:** Admin manages email template content customization. Lists all email templates (client, internal, contact) with category filter. Admin can edit text fields (greeting, body, CTA, subject), toggle templates on/off, preview rendered HTML with sample data, and reset to defaults.
- **Steps:**
  1. Admin navigates to `/panel/proposals/email-templates`.
  2. Template list loads from API (`GET /api/email-templates/`).
  3. Category filter buttons (Todos, Cliente, Interno, Contacto) allow filtering.
  4. Admin clicks a template row to expand the editor.
  5. Template detail loads from API (`GET /api/email-templates/:key/`).
  6. Admin edits text fields (greeting, body, cta_text, subject) and toggles active/inactive.
  7. Admin clicks "Guardar Cambios" → `PUT /api/email-templates/:key/`.
  8. Success feedback displays.
- **Branches:**
  - [Branch A — Preview] Admin clicks "Vista previa" → `GET /api/email-templates/:key/preview/` → modal with rendered HTML iframe.
  - [Branch B — Reset] Admin clicks "Restaurar" → confirmation modal → `POST /api/email-templates/:key/reset/` → template reverts to defaults.
  - [Branch C — Disable] Admin toggles template off → emails of this type stop being sent.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-email-templates.spec.js`
- **Backend Tests:** `content/tests/views/test_email_template_views.py`

### FLOW: `admin-mini-crm-clients`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`
- **Description:** View a Mini-CRM client list grouped by client email, with proposal history, statistics, and search functionality.
- **Steps:**
  1. Admin navigates to `/panel/clients/`.
  2. Client list loads from `GET /api/proposals/clients/`.
  3. Clients render with stats (total, accepted, rejected, pending proposals).
  4. Admin searches clients by name or email.
  5. Admin expands a client row to view individual proposals.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-mini-crm-clients.spec.js`

### FLOW: `admin-proposal-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/`, `/panel/proposals/:id/edit`
- **Description:** Send a proposal to a client via email. On edit page, a visual pre-send checklist modal replaces the native `confirm()` dialog, validating: client email, client name, investment > $0, future expiration date, at least 1 enabled section.
- **Steps:**
  1. Admin views the proposal edit page.
  2. Admin clicks "Enviar al Cliente".
  3. Pre-send checklist modal opens showing pass/fail status for each item (✓/✗).
  4. "Enviar al Cliente" button is disabled until all checks pass.
  5. Admin clicks "Enviar al Cliente" in modal → API call to `POST /api/proposals/:id/send/`.
  6. Email is sent to the client with the proposal link.
  7. Success feedback displays.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-send.spec.js`

### FLOW: `admin-proposal-manual-alerts`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Create, view, and dismiss manual seller alerts/reminders for proposals. Auto-alerts now include: seller_inactive (🏷️ no follow-up >3d), zombie (💀 sent >7d, no views, no activity), late_return (🔄 client returned after ≥5d gap).
- **Steps:**
  1. Admin navigates to `/panel/proposals/`.
  2. Alerts panel shows auto-alerts (not_viewed, not_responded, expiring_soon, seller_inactive, zombie, late_return) merged with manual alerts from API (`GET /api/proposals/alerts/`).
  3. Each alert type has a distinct icon (👁️‍🗨️, ⏳, 🔥, 🏷️, 💀, 🔄).
  4. Admin clicks "+ Crear recordatorio" to open the create alert form.
  5. Admin selects a proposal, alert type (reminder/followup/call/meeting/custom), date, and message.
  6. Admin submits → API call to `POST /api/proposals/alerts/create/`.
  7. New alert appears in the panel with dismiss (✕) button.
  8. Admin clicks ✕ → API call to `PATCH /api/proposals/alerts/:id/dismiss/` → alert removed from list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-manual-alerts.spec.js`

### FLOW: `admin-proposal-win-rate-dashboard`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Dashboard displays win rate segmented by project type, market type, and combination. Backend computes accepted/(accepted+rejected+expired) per type.
- **Steps:**
  1. Admin opens the KPI Dashboard on the proposals page.
  2. Dashboard loads data from `GET /api/proposals/dashboard/` including `win_rate_by_project_type`, `win_rate_by_market_type`, `win_rate_by_combination`.
  3. Two side-by-side bar charts show win rates by project type and market type (best type highlighted).
  4. Combination table shows project×market cross-tab for combos with ≥2 proposals.
- **Coverage:** ✅ Covered — `frontend/e2e/admin/admin-proposal-win-rate.spec.js`

### FLOW: `admin-proposal-engagement-score`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Analytics tab)
- **Description:** ProposalAnalytics displays an engagement score (0-100) per proposal, computed from recent sessions, investment section time, unique stakeholders, response recency, and revisits.
- **Steps:**
  1. Admin opens the Analytics tab for a proposal.
  2. Analytics loads from `GET /api/proposals/:id/analytics/` including `engagement_score`.
  3. Engagement score card renders with color-coded level (green ≥70, yellow ≥40, red <40) and contextual recommendation text.
- **Coverage:** ✅ Covered — `frontend/e2e/admin/admin-proposal-analytics.spec.js`

### FLOW: `admin-proposal-metrics-manual`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/proposals/`
- **Description:** Floating "?" button opens a slide-over panel (MetricsManual component) with searchable definitions of all metrics: conversion rate, engagement score, heat score, time-to-first-view, win rate, zombie proposals, late returns, seller inactivity, etc.
- **Steps:**
  1. Admin clicks the floating "?" button (bottom-right corner).
  2. MetricsManual slide-over opens with search bar and 16 metric definitions.
  3. Admin types in search bar → results filter in real-time.
  4. Each metric shows name, description, calculation method, and recommended action.
  5. Admin clicks outside or ✕ to close.
- **Coverage:** ✅ Covered — `frontend/e2e/admin/admin-proposal-metrics-manual.spec.js`

### FLOW: `admin-proposal-batch-actions`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Admin selects multiple proposals via checkboxes and performs batch actions (re-send, expire, delete). A sticky action bar appears at the top when at least one proposal is selected. Includes a select-all checkbox in the table header.
- **Steps:**
  1. Admin navigates to `/panel/proposals/`.
  2. Admin clicks checkboxes on individual proposal rows (or the header checkbox to select all visible).
  3. Sticky batch action bar appears showing "{N} seleccionada(s)" with action buttons.
  4. Admin clicks a batch action (🔄 Re-enviar, ⏰ Expirar, or 🗑️ Eliminar).
  5. Confirmation dialog appears.
  6. Admin confirms → API call to `POST /api/proposals/bulk-action/` with `{ ids, action }`.
  7. On success, selection is cleared and proposal list refreshes.
- **Branches:**
  - [Branch A — Cancel] Admin clicks "Cancelar" → selection is cleared, action bar disappears.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-list.spec.js`

### FLOW: `admin-proposal-engagement-decay-alert`

- **Module:** admin
- **Role:** system
- **Priority:** P2
- **Routes:** N/A (backend-triggered)
- **Description:** When a client views fewer sections in a session compared to their average from previous sessions (below 50% of the average), the system creates an `engagement_decay` ProposalAlert. The alert is rate-limited to one per 3 days per proposal. It appears in the alerts panel on the proposals list page.
- **Steps:**
  1. Client views a proposal and engagement data is sent via `POST /api/proposals/:uuid/track/`.
  2. Backend compares current session section count to the average of previous sessions.
  3. If current count < 50% of average, and no `engagement_decay` alert exists for the last 3 days, a new alert is created.
  4. Alert message includes section counts: "{clientName} vio {N} secciones vs promedio anterior de {avg}. Posible pérdida de interés."
  5. Alert appears in the admin proposals list alerts panel.
- **Coverage:** ⚠️ Backend-only
- **Backend Tests:** `content/tests/views/test_proposal_views.py`

### FLOW: `admin-proposal-post-rejection-revisit`

- **Module:** admin
- **Role:** system
- **Priority:** P2
- **Routes:** N/A (backend-triggered)
- **Description:** When a client revisits a proposal that was previously rejected, the system creates a `post_rejection_revisit` ProposalAlert. This signals potential reconsideration and appears in the admin alerts panel.
- **Steps:**
  1. Client opens a proposal URL where `status = 'rejected'`.
  2. Backend detects the rejected status in `retrieve_public_proposal`.
  3. A `post_rejection_revisit` ProposalAlert is created with message: "{clientName} revisitó la propuesta rechazada. Posible reconsideración."
  4. Alert appears in the admin proposals list alerts panel.
- **Coverage:** ⚠️ Backend-only
- **Backend Tests:** `content/tests/views/test_proposal_views.py`

### FLOW: `admin-proposal-json-import-warnings`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/create` (JSON import tab)
- **Description:** When importing a proposal from JSON, the backend validates the payload and returns warnings for any section keys that don't map to known section types. Warnings are non-blocking — the proposal is still created, but the admin is informed of unmapped keys that were ignored.
- **Steps:**
  1. Admin switches to "Importar JSON" tab on the create page.
  2. Admin pastes a JSON payload containing extra or misspelled section keys.
  3. Admin submits → API call to `POST /api/proposals/create-from-json/`.
  4. Backend validates with `ProposalFromJSONSerializer`, identifies unmapped keys.
  5. Proposal is created successfully with known sections populated.
  6. Response includes `warnings` array listing unmapped section keys.
  7. Frontend displays warnings to the admin.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-create.spec.js`

### FLOW: `proposal-welcome-back`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Returning client sees a welcome-back overlay with their name and last visited section. Progress is persisted in localStorage per proposal UUID.
- **Steps:**
  1. Client opens a proposal they've previously visited.
  2. On animation complete, the system checks `localStorage` for saved progress (`proposal-{uuid}-progress`).
  3. If progress exists (sectionIndex > 0), welcome-back overlay appears: "Bienvenido de nuevo, [name]. La última vez llegaste hasta [section]."
  4. Client clicks "Continuar donde lo dejé" → navigates to saved section.
  5. Client clicks "Empezar desde el inicio" → dismisses overlay.
  6. Onboarding tutorial is skipped for returning visitors.
- **Branches:**
  - [Branch A — First visit] No saved progress → normal onboarding flow.
  - [Branch B — Preview mode] Welcome-back is skipped in preview mode.
- **Coverage:** ✅ Covered — `frontend/e2e/proposal/proposal-welcome-back.spec.js`

### FLOW: `proposal-process-methodology`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** New "Proceso y Metodología" section with a 5-step visual pipeline (Discovery → Diseño → Desarrollo → QA → Lanzamiento). Horizontal on desktop, vertical timeline on mobile. Each step shows icon, title, description, and optional "Tu aporte" client action tag.
- **Steps:**
  1. Client navigates to the Process & Methodology section.
  2. Section renders with intro text and 5-step pipeline.
  3. Active steps are highlighted with green styling.
  4. Client action tags indicate what input the client provides at each stage.
- **Coverage:** ✅ Covered — `frontend/e2e/proposal/proposal-process-methodology.spec.js`

### FLOW: `proposal-calculator-modules`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** Calculator modal displays core calculator modules in order: PWA (40%), AI (invite-only), Conversiones Inteligentes (invite-only), Facturación Electrónica (60%), Pasarela Internacional (20%), Pasarela Regional (20%), Email Marketing (10%), Reportes y Alertas (20%, selected by default), Multi-idioma (15%). An informational badge at the **top** of the modal explains items are optional. Selecting a calculator module **adds** ~1 week to the timeline.
- **Steps:**
  1. Client navigates to the Investment section and clicks "Personalizar tu inversión".
  2. Calculator modal opens with informational badge at the top.
  3. Modules appear in the specified order: PWA, AI, Smart Conversions, Electronic Invoicing, International Payments, Regional Payments, Email Marketing, Reports & Alerts, Multi-idioma.
  4. PWA module appears unselected by default, with price as +40% of total.
  5. AI module appears with "Agendar llamada" label instead of price and a purple creative invite note.
  6. Reports & Alerts module appears selected by default with price as +20% of total.
  7. Selecting a module adds ~1 week to estimated timeline; deselecting an investment module reduces ~1 week.
  8. Client confirms selection → modal closes, total updates on Investment section.
- **Branches:**
  - [Branch A — AI invite] Client selects AI module → invite note visible, no cost added.
  - [Branch B — FR integration] Selected calculator modules appear in Functional Requirements section.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-calculator-modules.spec.js`

### FLOW: `proposal-calculator-selected-first`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** When the calculator modal opens, groups containing pre-selected (`default_selected`) modules are sorted to the top so the client sees included modules first without scrolling.
- **Steps:**
  1. Client opens the proposal and navigates to the Investment section.
  2. Client clicks "Personalizar tu inversión".
  3. Calculator modal opens with selected module groups sorted to the top.
  4. Unselected module groups appear below.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-calculator-modules.spec.js`

### FLOW: `proposal-expired-graceful`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** When a client opens an expired proposal, the backend returns HTTP 410 Gone and creates a `post_expiration_visit` alert. The frontend renders a graceful `ProposalExpired` component with the client name, proposal title, a WhatsApp reactivation CTA, and an email contact option.
- **Steps:**
  1. Client opens a proposal URL where `expires_at` is in the past.
  2. API call to `GET /api/proposals/:uuid/` returns HTTP 410 with partial proposal data.
  3. Backend creates a `post_expiration_visit` ProposalAlert for the seller.
  4. Frontend detects 410 status and sets `loadError = 'expired'`.
  5. `ProposalExpired` component renders with personalized message: "{clientName}, esta propuesta ha expirado".
  6. WhatsApp reactivation button pre-fills a message mentioning the proposal title.
  7. Email contact button links to team email.
- **Branches:**
  - [Branch A — Post-rejection revisit] If the proposal was rejected and the client revisits, a `post_rejection_revisit` alert is also created.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-view.spec.js` (Branch A — Proposal expired)

### FLOW: `proposal-calculator-abandonment-tracking`

- **Module:** proposal
- **Role:** guest (via shared UUID link) / system
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The calculator modal tracks whether the client confirms or abandons their module selection. On close without confirming, an `abandoned` event is sent. On confirm, a `confirmed` event is sent. Both are stored as `ProposalChangeLog` entries and aggregated in the admin dashboard as `calc_abandonment_rate` and `dropped_modules`.
- **Steps:**
  1. Client opens the calculator modal in the Investment section.
  2. Client toggles modules (selects/deselects).
  3. [Branch A — Confirm] Client clicks "Confirmar selección" → `confirmed` event sent via `POST /api/proposals/:uuid/track-calculator/`.
  4. [Branch B — Abandon] Client closes modal without confirming → `abandoned` event sent automatically.
  5. Backend creates `ProposalChangeLog` with `calc_confirmed` or `calc_abandoned` change type.
  6. Dashboard aggregates data: `calc_abandonment_rate` = abandoned / (abandoned + confirmed), `dropped_modules` = most frequently deselected modules.
- **Coverage:** ⚠️ Backend-only
- **Backend Tests:** `content/tests/views/test_proposal_views.py`

### FLOW: `proposal-negotiate`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** Client clicks "Necesito ajustes" from the ProposalClosing panel to open a negotiation flow. The response is sent to the backend with `decision: negotiating`, which pauses automations and logs the event.
- **Steps:**
  1. Client navigates to the closing panel.
  2. Client clicks "Necesito ajustes" (amber button).
  3. Confirmation modal opens.
  4. Client confirms → API call to `POST /api/proposals/:uuid/respond/` with `decision: negotiating`.
  5. Backend sets `automations_paused = True` and status to `negotiating`.
  6. Success message displays with WhatsApp CTA for further discussion.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-respond.spec.js`

### FLOW: `admin-proposal-quick-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Admin sends or re-sends a proposal directly from the proposals list without entering the edit page. Draft proposals show a "📤 Enviar" button; sent/viewed proposals show "🔄 Re-enviar". A confirmation modal prevents accidental sends.
- **Steps:**
  1. Admin views the proposals list.
  2. For draft proposals with client_email: "📤 Enviar" button is visible in the row.
  3. Admin clicks "📤 Enviar" → confirmation modal opens: "¿Enviar esta propuesta?".
  4. Admin confirms → API call to `POST /api/proposals/:id/send/`.
  5. Success: proposal status changes to `sent`, list refreshes.
  6. For sent/viewed proposals: "🔄 Re-enviar" button is visible → confirm dialog → `POST /api/proposals/:id/resend/`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-list.spec.js`

### FLOW: `admin-proposal-quick-log`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Admin registers a seller activity (call, meeting, follow-up, note) directly from the proposals list via the actions modal, without entering the proposal detail. Opens a quick-log modal with activity type selector and description field.
- **Steps:**
  1. Admin opens the actions modal (⋮) for a proposal.
  2. Admin clicks "📝 Registrar actividad".
  3. Quick-log modal opens showing client name and proposal title.
  4. Admin selects activity type (call, meeting, follow-up, note).
  5. Admin enters a description.
  6. Admin clicks "Registrar" → API call to `POST /api/proposals/:id/log-activity/`.
  7. Success: modal closes, proposal list refreshes with updated `last_activity_at`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-quick-log.spec.js`

### FLOW: `proposal-discount-multi-section`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** When a proposal has an active discount, the discount badge is consistently visible across three sections: Investment (banner with % OFF), Calculator modal (footer badge), and ProposalClosing (special price badge). This ensures the client is always aware of the time-limited offer.
- **Steps:**
  1. Client opens a proposal with `discount_percent > 0`.
  2. Investment section shows a discount banner with percentage and days remaining.
  3. Calculator modal shows a discount badge in the footer.
  4. Closing section shows a "Precio especial" badge above the accept button.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-discount-multi-section.spec.js`

### FLOW: `proposal-onboarding-mobile-swipe`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P3
- **Routes:** `/proposal/:uuid`
- **Description:** On mobile devices, the onboarding tutorial replaces positioned tooltips with a fullscreen swipe carousel overlay. Users navigate steps by swiping left/right or tapping next/back buttons. Desktop retains tooltip-based onboarding.
- **Steps:**
  1. First-time visitor opens a proposal on a mobile device.
  2. ProposalOnboarding detects `isMobile` and renders fullscreen overlay.
  3. User swipes left/right or taps navigation buttons to progress through steps.
  4. On completion, onboarding emits `@complete` and sets localStorage flag.
  5. Reading time popup appears.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-onboarding-mobile-swipe.spec.js`

### FLOW: `proposal-og-meta-personalized`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P3
- **Routes:** `/proposal/:uuid`
- **Description:** Personalized Open Graph meta tags are set dynamically so WhatsApp/social media previews show the client name and proposal title. Uses `useHead` with computed `og:title` and `og:description`.
- **Steps:**
  1. Proposal page loads and fetches proposal data.
  2. `useHead` sets `og:title` to "Propuesta para {client_name}".
  3. `og:description` includes client name and proposal title in the appropriate language.
  4. When the proposal URL is shared on WhatsApp/social media, the personalized preview is shown.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-og-meta-personalized.spec.js`

### FLOW: `admin-proposal-dashboard-auto-refresh`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/proposals/`
- **Description:** The ProposalDashboard KPI panel auto-refreshes every 60 seconds when open. A manual "Actualizar" button and "last updated" label are also available. Auto-refresh pauses when the dashboard is collapsed.
- **Steps:**
  1. Admin views the proposals list with the dashboard open.
  2. Dashboard fetches data on first open.
  3. Every 60 seconds, data refreshes automatically if the panel is open.
  4. "Actualizar" button triggers manual refresh with spin animation.
  5. "justo ahora" / "hace Xs" label shows time since last refresh.
  6. Collapsing the dashboard stops auto-refresh; expanding resumes it.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-dashboard-auto-refresh.spec.js`

### FLOW: `proposal-summary-kpis`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The Proposal Summary section displays personalized KPI cards at the top, sourced from `content_json.kpis`. Each KPI shows a value, label, and source citation. KPIs are editable in the admin SectionEditor and included in the JSON template.
- **Steps:**
  1. Client navigates to the Proposal Summary section.
  2. KPI cards render from `content.kpis` array with value, label, and source.
  3. Below KPIs, standard summary cards (investment, timeline, etc.) render.
  4. Admin can add/edit/remove KPIs in the SectionEditor for proposal_summary.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-summary-kpis.spec.js`

### FLOW: `admin-proposal-log-activity`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Activity tab)
- **Description:** Admin manually logs a seller activity on a proposal. Activity types include call, meeting, follow-up, and note. The activity is stored as a ProposalChangeLog entry and updates `last_activity_at`.
- **Steps:**
  1. Admin opens a proposal edit page and navigates to the Activity tab.
  2. Admin selects an activity type and enters a description.
  3. Admin submits → API call to `POST /api/proposals/:id/log-activity/`.
  4. Backend creates a ProposalChangeLog entry and updates `last_activity_at`.
  5. Activity timeline refreshes with the new entry.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-log-activity.spec.js`

### FLOW: `proposal-calculator-new-modules`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The investment calculator displays additional default modules: Email Marketing (10%), i18n (15%), and Gift Cards (20%). KPI Dashboard has been removed from the calculator and is now included by default (like Analytics). Conversion Tracking moved to integrations (see `proposal-calculator-integrations`).
- **Steps:**
  1. Client opens the calculator modal.
  2. Email Marketing module appears unselected with price as +10% of total.
  3. i18n module appears unselected with price as +15% of total.
  4. Gift Cards module appears unselected with price as +20% of total.
  5. Client toggles modules → total investment and timeline update in real-time.
  6. KPI Dashboard is NOT shown in the modal (included by default like Analytics module).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-calculator-new-modules.spec.js`

### FLOW: `proposal-calculator-integrations`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The investment calculator displays integration groups as individually toggleable calculator modules: International Payments (20%), Regional Payments Colombia (20%), Electronic Invoicing / DIAN (60%), and Conversion Tracking Meta & Google Ads (invite-only, 0%). Each was previously grouped under a single `integrations_api` group and now has its own pricing, selection state, and invite attributes.
- **Steps:**
  1. Client opens the calculator modal.
  2. International Payments integration appears unselected with price as +20% of total.
  3. Regional Payments (Colombia) integration appears unselected with price as +20% of total.
  4. Electronic Invoicing integration appears unselected with price as +60% of total.
  5. Conversion Tracking integration appears with "Agendar llamada" invite-only label and invite note.
  6. Client selects International Payments → total investment increases by 20%.
  7. Client selects Electronic Invoicing → total investment increases by 60%.
- **Branches:**
  - [Branch A — Conversion Tracking invite] Client sees invite note, no cost added.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-calculator-integrations.spec.js`

### FLOW: `admin-blog-list`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/blog/`
- **Description:** View the paginated list of all blog posts (admin view with both languages).
- **Steps:**
  1. Admin navigates to `/panel/blog/`.
  2. Blog posts load from API (`GET /api/blog/admin/?page=1&page_size=15`).
  3. Blog table renders with title_es, title_en, status, dates.
  4. Pagination controls appear if total pages > 1 (prev/next + page numbers).
  5. "Calendario" button links to calendar view.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-list.spec.js`

### FLOW: `admin-blog-calendar`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/blog/calendar`
- **Description:** Weekly calendar view showing scheduled, published, and draft blog posts.
- **Steps:**
  1. Admin navigates to `/panel/blog/calendar`.
  2. Calendar loads current week posts from API (`GET /api/blog/admin/calendar/?start=YYYY-MM-DD&end=YYYY-MM-DD`).
  3. Week grid renders Mon–Sun with posts color-coded: green (published), blue (scheduled), gray (draft).
  4. Admin uses ← / → arrows to navigate weeks, "Hoy" button to return to current week.
  5. Clicking a post card navigates to its edit page.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-calendar.spec.js`

### FLOW: `admin-blog-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/blog/create`
- **Description:** Create a new bilingual blog post.
- **Steps:**
  1. Admin navigates to `/panel/blog/create`.
  2. Blog form renders with bilingual fieldsets (ES + EN: title, excerpt, content).
  3. Admin fills in both language versions.
  4. Admin optionally uploads a cover image.
  5. Admin submits the form.
  6. API call to `POST /api/blog/admin/create/`.
  7. On success, admin is redirected to blog list.
- **Branches:**
  - [Branch A — Validation error] Form shows errors, admin corrects and resubmits.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-create.spec.js`

### FLOW: `admin-blog-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/blog/:id/edit`
- **Description:** Edit an existing bilingual blog post.
- **Steps:**
  1. Admin navigates to `/panel/blog/:id/edit`.
  2. Blog post data loads from API (`GET /api/blog/admin/:id/detail/`).
  3. Edit form renders pre-filled with current bilingual data.
  4. Admin modifies content.
  5. Admin saves changes.
  6. API call to `PATCH /api/blog/admin/:id/update/`.
  7. Success feedback displays.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-edit.spec.js`

### FLOW: `admin-blog-delete`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/blog/`
- **Description:** Delete an existing blog post.
- **Steps:**
  1. Admin views the blog list.
  2. Admin clicks delete on a blog post.
  3. Confirmation dialog appears.
  4. Admin confirms deletion.
  5. API call to `DELETE /api/blog/admin/:id/delete/`.
  6. Blog post is removed from the list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-delete.spec.js`

### FLOW: `admin-blog-create-from-json`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/blog/create` (JSON import tab)
- **Description:** Create a blog post by importing a structured JSON payload with content_json sections, template download, validation, and preview.
- **Steps:**
  1. Admin navigates to `/panel/blog/create`.
  2. Admin clicks "Importar JSON" tab.
  3. Admin pastes or uploads a valid JSON payload.
  4. Admin submits.
  5. API call to `POST /api/blog/admin/create/` with structured content_json.
  6. On success, admin is redirected to blog list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-create.spec.js`

### FLOW: `admin-portfolio-list`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/portfolio/`
- **Description:** View the list of all portfolio works with status badges, edit/duplicate/delete actions.
- **Steps:**
  1. Admin navigates to `/panel/portfolio/`.
  2. Portfolio works load from API (`GET /api/portfolio/admin/`).
  3. Table renders with title, slug, status (published/draft/archived), dates.
  4. Admin sees action links: edit, duplicate, delete.
  5. "Nuevo Proyecto" button links to create page.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-portfolio-list.spec.js`

### FLOW: `admin-portfolio-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/portfolio/create`
- **Description:** Create a new portfolio work via manual form (bilingual fields, cover image, project URL, content JSON, SEO) or JSON import.
- **Steps:**
  1. Admin navigates to `/panel/portfolio/create`.
  2. Page loads with Manual / Importar JSON tab toggle.
  3. Manual tab is active by default — form renders with ES/EN fieldsets.
  4. Admin fills title, tagline, project URL, cover image, content JSON, SEO fields.
  5. Admin submits.
  6. API call to `POST /api/portfolio/admin/create/`.
  7. On success, admin is redirected to portfolio list.
- **Branches:**
  - [Branch A — JSON import] Admin switches to "Importar JSON" tab, pastes JSON, submits via `POST /api/portfolio/admin/create-from-json/`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-portfolio-create.spec.js`

### FLOW: `admin-portfolio-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/portfolio/:id/edit`
- **Description:** Edit an existing portfolio work including bilingual fields, cover image upload, content JSON, and SEO meta.
- **Steps:**
  1. Admin navigates to `/panel/portfolio/:id/edit`.
  2. Portfolio work data loads from API (`GET /api/portfolio/admin/:id/detail/`).
  3. Edit form renders pre-filled with current data.
  4. Admin modifies content.
  5. Admin saves changes.
  6. API call to `PATCH /api/portfolio/admin/:id/update/`.
  7. Success feedback displays.
- **Branches:**
  - [Branch A] Admin uploads a new cover image via `POST /api/portfolio/admin/:id/upload-cover/`.
  - [Branch B] "Ver en público" link opens the public page in a new tab.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-portfolio-edit.spec.js`

### FLOW: `admin-portfolio-delete`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/portfolio/`
- **Description:** Delete an existing portfolio work.
- **Steps:**
  1. Admin views the portfolio list.
  2. Admin clicks delete on a portfolio work.
  3. Confirmation dialog appears.
  4. Admin confirms deletion.
  5. API call to `DELETE /api/portfolio/admin/:id/delete/`.
  6. Portfolio work is removed from the list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-portfolio-delete.spec.js`

### FLOW: `proposal-view-paste-rendering`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Client views proposal sections that use paste mode (`_editMode: 'paste'`). Paste-mode sections render as `RawContentSection` with markdown rendering in a styled card, while form-mode sections render their structured Vue components. Mixed form/paste proposals show each section in its correct mode.
- **Steps:**
  1. Client opens a proposal containing sections with `_editMode: 'paste'`.
  2. Paste-mode sections render `RawContentSection` with section title, index number, and a rounded card with markdown content.
  3. Markdown features (headings, bold, lists, blockquotes) render correctly via `marked` + `DOMPurify`.
  4. Form-mode sections in the same proposal render their structured components (no `RawContentSection`).
- **Branches:**
  - [Branch A — All form] Proposal with all form-mode sections renders zero `RawContentSection` components.
  - [Branch B — Mixed] Proposal with some paste and some form sections renders each correctly.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-view-paste-rendering.spec.js`

### FLOW: `proposal-sticky-bar-accept` *(ARCHIVED)*

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** ~~P2~~ Archived
- **Routes:** `/proposal/:uuid`
- **Description:** ~~Client accepts the proposal from the sticky bottom bar (ProposalResponseButtons) while browsing any section.~~ **ARCHIVED** — `ProposalResponseButtons` component was removed from production. Acceptance is now handled via `ProposalClosing` section buttons.
- **Coverage:** N/A (feature removed)
- **E2E Spec:** —

---

## 7. E2E Coverage Index

| Flow ID | Module | Role | Priority | Coverage | E2E Spec |
|---------|--------|------|----------|----------|----------|
| `layout-navbar-navigation` | layout | guest/admin | P2 | ✅ Covered | `e2e/layout/layout-navbar.spec.js` |
| `layout-locale-switch` | layout | guest/admin | P2 | ✅ Covered | `e2e/layout/layout-locale.spec.js` |
| `layout-footer-navigation` | layout | guest/admin | P3 | ✅ Covered | `e2e/layout/layout-footer.spec.js` |
| `public-home` | public | guest | P1 | ✅ Covered | `e2e/public/public-home.spec.js` |
| `public-portfolio` | public | guest | P2 | ✅ Covered | `e2e/public/public-pages.spec.js` |
| `public-portfolio-detail` | public | guest | P2 | ✅ Covered | `e2e/public/public-portfolio-detail.spec.js` |
| `public-about-us` | public | guest | P3 | ✅ Covered | `e2e/public/public-pages.spec.js` |
| `public-landing-web-design` | public | guest | P2 | ✅ Covered | `e2e/public/public-pages.spec.js` |
| `public-contact-submit` | public | guest | P1 | ✅ Covered | `e2e/public/public-contact.spec.js` |
| `blog-list` | blog | guest | P2 | ✅ Covered | `e2e/blog/blog-list.spec.js` |
| `blog-detail` | blog | guest | P2 | ✅ Covered | `e2e/blog/blog-detail.spec.js` |
| `proposal-view` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-view.spec.js` |
| `proposal-view-navigation` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-view-navigation.spec.js` |
| `proposal-view-onboarding` | proposal | guest | P3 | ✅ Covered | `e2e/proposal/proposal-onboarding.spec.js` |
| `proposal-section-onboarding` | proposal | guest | P3 | ✅ Covered | `e2e/proposal/proposal-section-onboarding.spec.js` |
| `proposal-executive-to-detailed` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-executive-to-detailed.spec.js` |
| `proposal-technical-view` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-technical-view.spec.js` |
| `proposal-respond` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-respond.spec.js` |
| `proposal-download-pdf` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-pdf.spec.js` |
| `proposal-share` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-share.spec.js` |
| `proposal-engagement-tracking` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-engagement-tracking.spec.js` |
| `admin-login` | auth | admin | P1 | ✅ Covered | `e2e/auth/auth-admin-login.spec.js` |
| `admin-dashboard` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-dashboard.spec.js` |
| `admin-proposal-list` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-list.spec.js` |
| `admin-proposal-create` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-create.spec.js` |
| `admin-proposal-create-from-json` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-create.spec.js` |
| `admin-proposal-edit` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-edit.spec.js` |
| `admin-proposal-section-edit-form` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-section-form.spec.js` |
| `admin-proposal-section-edit-paste` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-section-paste.spec.js` |
| `admin-proposal-section-reorder` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-section-reorder.spec.js` |
| `admin-proposal-functional-requirements-form` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-requirements.spec.js` |
| `admin-proposal-functional-requirements-paste` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-requirements.spec.js` |
| `admin-proposal-delete` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-delete.spec.js` |
| `admin-proposal-duplicate` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-duplicate.spec.js` |
| `admin-proposal-comment` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-proposal-comment.spec.js` |
| `admin-proposal-analytics` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-analytics.spec.js` |
| `admin-proposal-dashboard` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-dashboard.spec.js` |
| `admin-mini-crm-clients` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-mini-crm-clients.spec.js` |
| `admin-proposal-send` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-send.spec.js` |
| `admin-blog-list` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-blog-list.spec.js` |
| `admin-blog-calendar` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-blog-calendar.spec.js` |
| `admin-blog-create` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-blog-create.spec.js` |
| `admin-blog-create-from-json` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-blog-create.spec.js` |
| `admin-blog-edit` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-blog-edit.spec.js` |
| `admin-blog-delete` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-blog-delete.spec.js` |
| `admin-proposal-manual-alerts` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-manual-alerts.spec.js` |
| `admin-proposal-win-rate-dashboard` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-win-rate.spec.js` |
| `admin-proposal-engagement-score` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-analytics.spec.js` |
| `admin-proposal-metrics-manual` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-proposal-metrics-manual.spec.js` |
| `proposal-welcome-back` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-welcome-back.spec.js` |
| `proposal-process-methodology` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-process-methodology.spec.js` |
| `admin-portfolio-list` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-portfolio-list.spec.js` |
| `admin-portfolio-create` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-portfolio-create.spec.js` |
| `admin-portfolio-edit` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-portfolio-edit.spec.js` |
| `admin-portfolio-delete` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-portfolio-delete.spec.js` |
| `proposal-pre-expiration-discount-suggestion` | admin | system | P2 | ⚠️ Backend-only | Backend unit tests (`test_proposal_views.py`) |
| `admin-proposal-zombie-segment` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-zombie-segment.spec.js` |
| `proposal-countdown-realtime` | proposal | guest | P3 | ✅ Covered | `e2e/proposal/proposal-countdown-realtime.spec.js` |
| `admin-proposal-create-and-send` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-create.spec.js` |
| `admin-proposal-create-preview` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-create.spec.js` |
| `admin-seller-inactivity-escalation` | admin | system | P2 | ⚠️ Backend-only | Backend unit tests (`test_proposal_views.py`) |
| `admin-dashboard-pipeline-value` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-dashboard.spec.js` |
| `proposal-rejection-optional-reason` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-rejection-optional.spec.js` |
| `proposal-calculator-timeline` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-calculator-timeline.spec.js` |
| `admin-discount-analysis-enhanced` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-discount-analysis.spec.js` |
| `proposal-calculator-modules` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-calculator-modules.spec.js` |
| `proposal-calculator-selected-first` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-calculator-modules.spec.js` |
| `proposal-calculator-integrations` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-calculator-integrations.spec.js` |
| `proposal-expired-graceful` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-view.spec.js` |
| `proposal-calculator-abandonment-tracking` | proposal | system | P2 | ⚠️ Backend-only | Backend unit tests (`test_proposal_views.py`) |
| `admin-proposal-batch-actions` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-list.spec.js` |
| `admin-proposal-engagement-decay-alert` | admin | system | P2 | ⚠️ Backend-only | Backend unit tests (`test_proposal_views.py`) |
| `admin-proposal-post-rejection-revisit` | admin | system | P2 | ⚠️ Backend-only | Backend unit tests (`test_proposal_views.py`) |
| `admin-proposal-json-import-warnings` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-create.spec.js` |
| `proposal-negotiate` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-respond.spec.js` |
| `admin-proposal-quick-send` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-list.spec.js` |
| `admin-proposal-quick-log` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-quick-log.spec.js` |
| `proposal-calculator-timeline-impact` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-calculator-timeline.spec.js` |
| `proposal-discount-multi-section` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-discount-multi-section.spec.js` |
| `proposal-onboarding-mobile-swipe` | proposal | guest | P3 | ✅ Covered | `e2e/proposal/proposal-onboarding-mobile-swipe.spec.js` |
| `proposal-og-meta-personalized` | proposal | guest | P3 | ✅ Covered | `e2e/proposal/proposal-og-meta-personalized.spec.js` |
| `admin-proposal-dashboard-auto-refresh` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-proposal-dashboard-auto-refresh.spec.js` |
| `proposal-summary-kpis` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-summary-kpis.spec.js` |
| `admin-proposal-log-activity` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-log-activity.spec.js` |
| `proposal-calculator-new-modules` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-calculator-new-modules.spec.js` |
| `admin-proposal-inline-status-change` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-inline-status.spec.js` |
| `admin-proposal-scorecard` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-scorecard.spec.js` |
| `admin-proposal-section-completeness` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-proposal-section-completeness.spec.js` |
| `admin-daily-pipeline-digest` | admin | system | P2 | ⚠️ Backend-only | Backend unit tests |
| `admin-high-engagement-alert` | admin | system | P2 | ⚠️ Backend-only | Backend unit tests |
| `admin-calculator-followup-alert` | admin | system | P2 | ⚠️ Backend-only | Backend unit tests |
| `admin-whatsapp-suggestion` | admin | system | P2 | ⚠️ Backend-only | Backend unit tests |
| `admin-auto-archive-zombie` | admin | system | P3 | ⚠️ Backend-only | Backend unit tests |
| `proposal-calculator-micro-feedback` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-calculator-micro-feedback.spec.js` |
| `proposal-payment-plan-closing` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-payment-plan-closing.spec.js` |
| `proposal-post-acceptance-welcome` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-post-acceptance-welcome.spec.js` |
| `proposal-structured-negotiation` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-structured-negotiation.spec.js` |
| `proposal-conditional-acceptance` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-conditional-acceptance.spec.js` |
| `proposal-view-paste-rendering` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-view-paste-rendering.spec.js` |
| `proposal-sticky-bar-accept` | proposal | guest | ~~P2~~ | 🗄️ Archived | — (feature removed) |
| `admin-document-list` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-document-list.spec.js` |
| `admin-document-create` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-document-create.spec.js` |
| `admin-document-edit` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-document-edit.spec.js` |
| `admin-admin-management` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-admin-management.spec.js` |
| `admin-email-deliverability` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-email-deliverability.spec.js` |
| `public-landing-software` | public | guest | P3 | ✅ Covered | `e2e/public/public-landing-software.spec.js` |
| `public-landing-apps` | public | guest | P3 | ✅ Covered | `e2e/public/public-landing-apps.spec.js` |
| `platform-login` | platform | platform-admin/client | P1 | ✅ Covered | `e2e/platform/platform-login.spec.js` |
| `platform-verify-onboarding` | platform | platform-admin/client | P1 | ✅ Covered | `e2e/platform/platform-verify.spec.js` |
| `platform-complete-profile` | platform | platform-admin/client | P1 | ✅ Covered | `e2e/platform/platform-complete-profile.spec.js` |
| `platform-kanban-board` | platform | platform-admin/client | P1 | ✅ Covered | `e2e/platform/platform-kanban-board.spec.js` |
| `platform-dashboard` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-dashboard.spec.js` |
| `platform-sidebar-navigation` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-sidebar.spec.js` |
| `platform-project-list` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-project-list.spec.js` |
| `platform-project-detail` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-project-detail.spec.js` |
| `platform-unified-board` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-unified-board.spec.js` |
| `platform-admin-client-list` | platform | platform-admin | P2 | ✅ Covered | `e2e/platform/platform-admin-client-list.spec.js` |
| `platform-admin-client-detail` | platform | platform-admin | P2 | ✅ Covered | `e2e/platform/platform-admin-client-detail.spec.js` |
| `platform-profile-edit` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-profile.spec.js` |
| `platform-hosting-subscription` | platform | platform-admin/client | P1 | ✅ Covered | `e2e/platform/platform-hosting-subscription.spec.js` |
| `platform-change-requests` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-change-requests.spec.js` |
| `platform-bug-reports` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-bug-reports.spec.js` |
| `platform-deliverables` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-deliverables.spec.js` |
| `platform-notifications` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-notifications.spec.js` |
| `platform-kanban-json-upload` | platform | platform-admin | P2 | ✅ Covered | `e2e/platform/platform-kanban-json-upload.spec.js` |
| `platform-requirement-client-review` | platform | platform-client | P2 | ✅ Covered | `e2e/platform/platform-requirement-client-review.spec.js` |
| `platform-admin-project-create` | platform | platform-admin | P3 | ✅ Covered | `e2e/platform/platform-project-create.spec.js` |
| `platform-kanban-card-comments` | platform | platform-admin/client | P3 | ✅ Covered | `e2e/platform/platform-kanban-comments.spec.js` |

### Summary

- **Total flows:** 124
- **P1 (Critical):** 24
- **P2 (High):** 76
- **P3 (Medium):** 23
- **Covered (full):** 103 (83%)
- **Backend-only:** 10 (8%) — system-triggered alerts and automation covered by backend unit tests
- **Partial:** 0 (0%)
- **Missing:** 0 (0%)
- **Deferred:** 0
- **Archived:** 2 — `public-about-us`, `proposal-sticky-bar-accept` (feature removed)

### Unit Test Coverage

| Test File | Layer | Tests | Scope |
|-----------|-------|-------|-------|
| `test/components/SectionEditor.test.js` | Frontend unit | 97 | All 12 section types: formToJson, buildFormFromJson, round-trips, formToReadableText, buildSavePayload, edge cases |
| `test/composables/useProposalTracking.test.js` | Frontend unit | — | Engagement tracking composable |
| `test/stores/proposals.test.js` | Frontend unit | — | Proposal store actions including analytics, dashboard, clients, share, duplicate |
| `content/tests/views/test_proposal_views.py` | Backend view | 102 | Full proposal API: CRUD, respond, track, analytics, dashboard, clients, share, duplicate, comment, CSV |
| `content/tests/views/test_section_update_views.py` | Backend view | 22 | PATCH per section type + paste mode + group paste |
| `content/tests/models/test_section_content_json.py` | Backend model | ~40 | DB round-trip for all 12 types |

---

## 8. Platform Flows

> Platform flows cover the `/platform/` section of the application — a JWT-authenticated portal for **platform-admin** and **platform-client** roles. Backend API is served from `accounts/urls.py` under `/api/accounts/`.

### 8.1 Authentication & Onboarding

#### FLOW: `platform-login`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P1
- **Routes:** `/platform/login`
- **API:** `POST /api/accounts/login/`
- **Description:** Client or admin authenticates via JWT login form. Routes to one of three destinations based on user state.
- **Steps:**
  1. User navigates to `/platform/login`.
  2. Login form renders with email and password fields plus theme toggle button.
  3. User enters credentials and submits the form.
  4. API returns JWT tokens (onboarded) or `requires_verification: true` (first login).
- **Branches:**
  - [Branch A — Onboarded] API returns tokens → user is redirected to `/platform/dashboard`.
  - [Branch B — First login] API returns `requires_verification: true` → user is redirected to `/platform/verify`.
  - [Branch C — Profile incomplete] Tokens returned but `needsProfileCompletion` is true → user is redirected to `/platform/complete-profile`.
  - [Branch D — Invalid credentials] API returns 401 → error message displayed inline.
  - [Branch E — Deactivated account] API returns 403 → error message displayed inline.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-login.spec.js`

#### FLOW: `platform-verify-onboarding`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P1
- **Routes:** `/platform/verify`
- **API:** `POST /api/accounts/verify/`, `POST /api/accounts/resend-code/`
- **Description:** First-login OTP verification with 6-digit code input, new password set, and redirect based on profile completion.
- **Steps:**
  1. User lands on `/platform/verify` after first login redirect.
  2. Page renders 6-digit code input fields and new password + confirm password fields.
  3. User enters the OTP code received via email.
  4. User sets a new permanent password.
  5. User submits verification form.
  6. API validates OTP, sets password, marks user as onboarded, returns JWT tokens.
- **Branches:**
  - [Branch A — Profile incomplete] User is redirected to `/platform/complete-profile`.
  - [Branch B — Profile complete] User is redirected to `/platform/dashboard`.
  - [Branch C — Invalid code] API returns 400 → error message displayed.
  - [Branch D — Resend code] User clicks "Reenviar código" → `POST /api/accounts/resend-code/` sends new OTP.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-verify.spec.js`

#### FLOW: `platform-complete-profile`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P1
- **Routes:** `/platform/complete-profile`
- **API:** `POST /api/accounts/me/complete-profile/`
- **Description:** Mandatory profile completion form with personal data and optional avatar upload. Middleware gates dashboard access until completed.
- **Steps:**
  1. User lands on `/platform/complete-profile` after verification or login redirect.
  2. Form renders with fields: first name, last name, company name, phone, cédula, date of birth, gender, education level.
  3. User optionally uploads an avatar image (preview displayed).
  4. User fills all required fields and submits.
  5. API sets `profile_completed = true` and saves all fields.
  6. User is redirected to `/platform/dashboard`.
- **Branches:**
  - [Branch A — Validation error] API returns errors → displayed inline under form.
  - [Branch B — Already completed] API returns 400 "El perfil ya fue completado." → user should be on dashboard already.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-complete-profile.spec.js`

### 8.2 Dashboard & Navigation

#### FLOW: `platform-dashboard`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P2
- **Routes:** `/platform/dashboard` (also `/platform` which redirects here)
- **API:** `GET /api/accounts/me/`, `GET /api/accounts/clients/`, `GET /api/accounts/projects/`
- **Description:** Main landing page after login. Content differs by role.
- **Steps:**
  1. User navigates to `/platform/dashboard`.
  2. Welcome message renders with user's first name.
  3. Page fetches data from API.
- **Branches:**
  - [Branch A — Admin] KPI stat cards render (active/pending/inactive clients). Recent clients table renders with status badges. Module cards link to Projects, Board, Clients.
  - [Branch B — Client] Profile summary card renders. Module cards link to Projects, Board.
  - [Branch C — Redirect] Navigating to `/platform` auto-redirects to `/platform/dashboard`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-dashboard.spec.js`

#### FLOW: `platform-sidebar-navigation`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P2
- **Routes:** All `/platform/*` pages
- **Description:** Left sidebar layout with collapsible navigation, mobile drawer, theme toggle, and logout.
- **Steps:**
  1. User sees left sidebar with logo, navigation sections (Principal, Proyectos, Administración), and user footer.
  2. User clicks a navigation item → page navigates to the selected route.
  3. Active route is highlighted in the sidebar.
- **Branches:**
  - [Branch A — Collapse/Expand] User clicks collapse button → sidebar shrinks to 64px icon-only mode. Click again to expand.
  - [Branch B — Mobile] Screen < md → hamburger button in top bar opens `PlatformMobileDrawer` overlay with full navigation.
  - [Branch C — Theme toggle] User clicks theme button → toggles light/dark mode across all platform pages.
  - [Branch D — Logout] User clicks logout button → `authStore.logout()` clears tokens → redirected to `/platform/login`.
  - [Branch E — Admin-only items] Admin sees "Clientes" and "Pagos" nav items under Administración section; client does not.
  - [Branch F — Profile link] User clicks settings icon → navigates to `/platform/profile`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-sidebar.spec.js`

### 8.3 Projects

#### FLOW: `platform-project-list`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P2
- **Routes:** `/platform/projects`
- **API:** `GET /api/accounts/projects/`, `POST /api/accounts/projects/`
- **Description:** Project listing with status filters and role-based views.
- **Steps:**
  1. User navigates to `/platform/projects`.
  2. API fetches projects (admin: all; client: own projects only).
  3. Project cards render in a grid with name, client, status badge, progress bar, and dates.
  4. User clicks a project card → navigates to `/platform/projects/:id`.
- **Branches:**
  - [Branch A — Admin filters] Admin sees status filter tabs (Todos/Activos/Pausados/Completados/Archivados) → filters refetch from API with `?status=` param.
  - [Branch B — Admin create] Admin clicks "Nuevo proyecto" → create project modal opens (see `platform-admin-project-create`).
  - [Branch C — Empty state] No projects → empty state message renders.
  - [Branch D — Client view] Client sees only their assigned projects without create button.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-project-list.spec.js`

#### FLOW: `platform-project-detail`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P2
- **Routes:** `/platform/projects/:id`
- **API:** `GET /api/accounts/projects/:id/`, `PATCH /api/accounts/projects/:id/`
- **Description:** Project detail hub with stats row, module cards, and admin edit modal.
- **Steps:**
  1. User navigates to `/platform/projects/:id` (or clicks a project card).
  2. Back link to `/platform/projects` renders.
  3. Project header renders with name, status badge, and description.
  4. Stats row renders: progress %, client info, start date, estimated end date (with days remaining).
  5. Module cards render: "Tablero" (active link to board), plus coming-soon placeholders (Solicitudes, Bugs, Entregables).
- **Branches:**
  - [Branch A — Admin edit] Admin clicks "Editar" → modal opens with name, description, status, start/end dates → submit calls `PATCH` API → modal closes and data refreshes.
  - [Branch B — Not found] Invalid project ID → "Proyecto no encontrado" with back link.
  - [Branch C — Board link] User clicks "Tablero" module card → navigates to `/platform/projects/:id/board`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-project-detail.spec.js`

#### FLOW: `platform-admin-project-create`

- **Module:** platform
- **Role:** platform-admin
- **Priority:** P3
- **Routes:** `/platform/projects` (modal)
- **API:** `POST /api/accounts/projects/`
- **Description:** Admin creates a new project via modal form.
- **Steps:**
  1. Admin clicks "Nuevo proyecto" button on projects list page.
  2. Modal opens with form fields: name, description, client selector, start date, estimated end date.
  3. Admin fills required fields and submits.
  4. API creates project and returns details.
  5. Modal closes and project list refreshes with the new project.
- **Branches:**
  - [Branch A — Validation error] Missing required fields → error displayed.
  - [Branch B — Cancel] Admin clicks cancel or outside modal → modal closes without action.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-project-create.spec.js`

### 8.4 Kanban Board

#### FLOW: `platform-kanban-board`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P1
- **Routes:** `/platform/projects/:id/board`
- **API:** `GET /api/accounts/projects/:id/deliverables/`, `GET|POST /api/accounts/projects/:projectId/deliverables/:deliverableId/requirements/`, `POST .../requirements/:id/move/`, `GET .../requirements/:id/` (requirements are scoped to a deliverable).
- **Description:** 3-column kanban board with drag & drop, card detail modal, and completed checklist.
- **Steps:**
  1. User navigates to `/platform/projects/:id/board`.
  2. Back link to project detail renders with project name.
  3. Progress pill renders with percentage and completed count.
  4. Three kanban columns render: "Por hacer" (todo), "En progreso" (in_progress), "En revisión" (in_review).
  5. Requirement cards render in their respective columns with priority dot, module tag, title, estimated hours, and comment count.
  6. Collapsible "Completados" section renders below columns with done cards as a checklist.
- **Branches:**
  - [Branch A — Admin drag & drop] Admin drags a card from one column to another → `POST .../move/` API updates status → card moves to target column.
  - [Branch B — Admin create card] Admin clicks "Card" button → create modal opens with title, description, priority, column, module, hours → submit creates requirement.
  - [Branch C — Complete card] Admin (or client for in_review) clicks checkmark → card moves to "done" column.
  - [Branch D — Card detail] User clicks any card → detail modal opens showing description, meta (status, estimated hours, created date), history timeline, and comments section.
  - [Branch E — Client approval] Client sees "Aprobar requerimiento" button for cards in approval status → clicking approves and moves to done.
  - [Branch F — Toggle completed] User clicks "Completados" bar → expands/collapses the done cards list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-kanban-board.spec.js`

#### FLOW: `platform-unified-board`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P2
- **Routes:** `/platform/board`
- **API:** `GET /api/accounts/projects/`, then per deliverable `GET .../deliverables/:deliverableId/requirements/`
- **Description:** Cross-project view showing active requirement cards grouped by project.
- **Steps:**
  1. User navigates to `/platform/board`.
  2. Page fetches all projects and their active requirements.
  3. Cards render grouped by project with project name headers and summary pills (todo/in_progress/in_review counts).
  4. Each card shows priority dot, title, and module tag.
- **Branches:**
  - [Branch A — Project link] User clicks project name → navigates to `/platform/projects/:id`.
  - [Branch B — Board link] User clicks "Ver tablero" → navigates to `/platform/projects/:id/board`.
  - [Branch C — Empty state] No active requirements → empty state message.
  - [Branch D — Loading] Skeleton/spinner renders while fetching data.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-unified-board.spec.js`

#### FLOW: `platform-kanban-card-comments`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P3
- **Routes:** `/platform/projects/:id/board` (card detail modal)
- **API:** `POST /api/accounts/projects/:projectId/deliverables/:deliverableId/requirements/:id/comments/`
- **Description:** Add public or internal (admin-only) comments on requirement cards.
- **Steps:**
  1. User opens card detail modal (from kanban board flow).
  2. Comments section renders with existing comments (author, date, content).
  3. User types a comment in the input field and clicks "Enviar".
  4. API creates the comment and it appears in the list.
- **Branches:**
  - [Branch A — Internal comment] Admin checks "Comentario interno" checkbox → comment saves with `is_internal: true` → rendered with amber border and "Interno" label (only visible to admins).
  - [Branch B — Client comment] Client can only post public comments (no internal checkbox visible).
  - [Branch C — Empty comment] Submit button disabled when input is empty.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-kanban-comments.spec.js`

### 8.5 Client Management (Admin-only)

#### FLOW: `platform-admin-client-list`

- **Module:** platform
- **Role:** platform-admin
- **Priority:** P2
- **Routes:** `/platform/clients`
- **API:** `GET /api/accounts/clients/`, `POST /api/accounts/clients/`, `POST /api/accounts/clients/:id/resend-invite/`, `DELETE /api/accounts/clients/:id/`
- **Description:** Admin-only client management table with invite, search, filter, and action capabilities.
- **Steps:**
  1. Admin navigates to `/platform/clients`.
  2. Client table renders with columns: client (avatar + name + email), company, status badge, created date, actions.
  3. Status filter tabs render: Todos, Onboarded, Pendientes, Inactivos.
  4. Search input filters clients by name, email, or company.
- **Branches:**
  - [Branch A — Invite client] Admin clicks "Invitar cliente" → modal opens with email, first name, last name, company, phone fields → submit calls `POST /api/accounts/clients/` → creates client + sends invitation email → success message.
  - [Branch B — Resend invite] Admin clicks "Reenviar" on a client row → `POST .../resend-invite/` → success/error message.
  - [Branch C — Deactivate] Admin clicks "Desactivar" → confirm modal → `DELETE /api/accounts/clients/:id/` → client deactivated.
  - [Branch D — Detail link] Admin clicks "Detalle" → navigates to `/platform/clients/:id`.
  - [Branch E — Filter by status] Admin clicks status tab → API refetches with `?filter=` param.
  - [Branch F — Search] Admin types in search → client-side filtering of visible results.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-admin-client-list.spec.js`

#### FLOW: `platform-admin-client-detail`

- **Module:** platform
- **Role:** platform-admin
- **Priority:** P2
- **Routes:** `/platform/clients/:id`
- **API:** `GET /api/accounts/clients/:id/`, `PATCH /api/accounts/clients/:id/`, `DELETE /api/accounts/clients/:id/`, `POST /api/accounts/clients/:id/resend-invite/`
- **Description:** Admin-only client detail page with profile card, edit form, and quick actions.
- **Steps:**
  1. Admin navigates to `/platform/clients/:id`.
  2. Back link to `/platform/clients` renders.
  3. Left column: profile card (avatar, name, email, company, phone, status, created date) + quick actions section.
  4. Right column: edit form (first name, last name, email disabled, company, phone, active toggle).
- **Branches:**
  - [Branch A — Save changes] Admin edits fields and clicks "Guardar cambios" → `PATCH` API updates client → success message.
  - [Branch B — Reset form] Admin clicks "Restablecer" → form reverts to server values.
  - [Branch C — Resend invite] Admin clicks "Reenviar invitación" → API resends → success/error message.
  - [Branch D — Deactivate] Admin clicks "Desactivar acceso" → confirm modal → `DELETE` API deactivates → success message.
  - [Branch E — Reactivate] For inactive clients, admin clicks "Reactivar acceso" → `PATCH` with `is_active: true` → success message.
  - [Branch F — Not found] Invalid client ID → "No encontramos el cliente solicitado" message.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-admin-client-detail.spec.js`

### 8.6 Profile

#### FLOW: `platform-profile-edit`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P2
- **Routes:** `/platform/profile`
- **API:** `GET /api/accounts/me/`, `PATCH /api/accounts/me/`
- **Description:** View and update personal profile fields with avatar display and role badge.
- **Steps:**
  1. User navigates to `/platform/profile` (via sidebar settings icon).
  2. Profile page renders with avatar, name, role badge, and editable form fields (first name, last name, company, phone, cédula, DOB, gender, education).
  3. User modifies fields and clicks "Guardar cambios".
  4. `PATCH /api/accounts/me/` updates profile.
  5. Success feedback displayed.
- **Branches:**
  - [Branch A — Validation error] Invalid input → API returns errors → displayed inline.
  - [Branch B — Cancel] User navigates away without saving → no changes persisted.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-profile.spec.js`

### 8.7 Change Requests, Bug Reports & Deliverables

#### FLOW: `platform-change-requests`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P2
- **Routes:** `/platform/projects/:id/changes`, `/platform/changes`
- **API:** `GET/POST /api/accounts/projects/:id/change-requests/`, `POST .../evaluate/`, `POST .../comments/`
- **Description:** Client creates change requests for a project. Admin evaluates (approve/reject/needs clarification) with estimated cost and time. Both roles can comment. Per-project view and unified cross-project view.
- **Steps:**
  1. User navigates to `/platform/projects/:id/changes` or `/platform/changes`.
  2. Change request list renders with status tabs and create button.
  3. Client fills create form (title, description, module, priority, urgency, screenshot).
  4. Admin evaluates: sets status, admin_response, estimated cost/time.
  5. Both roles add comments on individual change requests.
- **Branches:**
  - [Branch A — Create] Client creates a change request → notification sent to admin.
  - [Branch B — Evaluate] Admin evaluates → status changes → notification sent to client.
  - [Branch C — Unified view] `/platform/changes` shows all change requests grouped by project.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-change-requests.spec.js`

#### FLOW: `platform-bug-reports`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P2
- **Routes:** `/platform/projects/:id/bugs`, `/platform/bugs`
- **API:** `GET/POST /api/accounts/projects/:id/bug-reports/`, `POST .../evaluate/`, `POST .../comments/`
- **Description:** Both roles report bugs with severity, steps to reproduce, expected/actual behavior, device/browser, and screenshot. Admin evaluates with status changes and responses.
- **Steps:**
  1. User navigates to `/platform/projects/:id/bugs` or `/platform/bugs`.
  2. Bug report list renders with status tabs and severity badges.
  3. User fills create form (title, description, severity, steps, expected/actual behavior, environment, device, screenshot).
  4. Admin evaluates: sets status, admin_response, linked_bug.
  5. Both roles add comments.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-bug-reports.spec.js`

#### FLOW: `platform-deliverables`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P2
- **Routes:** `/platform/projects/:id/deliverables` (list), `/platform/deliverables` (cross-project), `/platform/projects/:id/deliverables/:deliverableId` (full-page ficha — see `platform-deliverable-detail`)
- **API:** `GET/POST /api/accounts/projects/:id/deliverables/`, `POST .../upload-version/`
- **Description:** Admin uploads deliverables (designs, documents, APKs, credentials) with version history. Client downloads files. List UI is implemented as `pages/.../deliverables/index.vue` so nested dynamic routes resolve correctly.
- **Steps:**
  1. User navigates to deliverables page.
  2. Deliverable list renders with category filter tabs and file count.
  3. Admin uploads a new deliverable (title, description, category, file).
  4. Admin uploads new versions of existing deliverables.
  5. Client views and downloads files.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-deliverables.spec.js`

### 8.8 Hosting & Payments

#### FLOW: `platform-hosting-subscription`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P1
- **Routes:** `/platform/projects/:id/payments`, `/platform/payments`
- **API:** `GET /api/accounts/subscriptions/` (unified `/platform/payments` list), `GET/POST/PATCH /api/accounts/projects/:id/subscription/`, `GET /api/accounts/projects/:id/payments/`, `POST .../card-pay/`, `POST .../verify/`, `GET .../widget-data/`
- **Description:** Client selects hosting plan (semiannual/quarterly/monthly), activates subscription, and pays via Wompi (card or widget). Admin sees subscription status. Netflix-style active state with next renewal date.
- **Steps:**
  1. Client navigates to `/platform/projects/:id/payments`.
  2. If no subscription: hosting tier cards render (semiannual/quarterly/monthly with pricing).
  3. Client selects plan and clicks "Activar plan de hosting" → `POST .../subscription/`.
  4. Subscription created with first payment → payment action card appears.
  5. Client pays via card form or Wompi widget.
  6. After payment: Netflix-style "Suscripción activa" card with next renewal date.
- **Branches:**
  - [Branch A — Admin view] Admin sees subscription status (not plan selector).
  - [Branch B — Up to date] Active subscription with no urgent payments shows clean green card.
  - [Branch C — Payment due] Shows payment action 7 days before billing date.
  - [Branch D — Unified view] `/platform/payments` shows all subscriptions across projects.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-hosting-subscription.spec.js`

### 8.9 Notifications

#### FLOW: `platform-notifications`

- **Module:** platform
- **Role:** platform-admin / platform-client
- **Priority:** P2
- **Routes:** `/platform/notifications`
- **API:** `GET /api/accounts/notifications/`, `PATCH .../mark-read/`, `POST .../mark-all-read/`, `GET .../unread-count/`
- **Description:** In-app notification center with unread count badge in sidebar, filter tabs, mark-all-read, and click-to-navigate deep links.
- **Steps:**
  1. Sidebar badge shows unread notification count (polled every 30s).
  2. User navigates to `/platform/notifications`.
  3. Notification list renders with filter tabs (Todas/Sin leer/Leídas).
  4. User clicks a notification → marked as read → navigates to relevant project module.
  5. User clicks "Marcar todas como leídas" → all notifications marked read.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-notifications.spec.js`

### 8.10 Kanban Enhancements

#### FLOW: `platform-kanban-json-upload`

- **Module:** platform
- **Role:** platform-admin
- **Priority:** P2
- **Routes:** `/platform/projects/:id/board`
- **API:** `POST /api/accounts/projects/:projectId/deliverables/:deliverableId/requirements/bulk/`
- **Description:** Admin bulk-creates requirements by uploading a JSON file. Includes downloadable example template.
- **Steps:**
  1. Admin clicks "Ejemplo" button → downloads `requerimientos-ejemplo.json` template.
  2. Admin prepares JSON with requirements (title, description, configuration, flow).
  3. Admin clicks "Subir JSON" → file picker opens → selects JSON file.
  4. API creates requirements in bulk → success alert with count.
  5. Backlog section updates with new cards.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-kanban-json-upload.spec.js`

#### FLOW: `platform-requirement-client-review`

- **Module:** platform
- **Role:** platform-client
- **Priority:** P2
- **Routes:** `/platform/projects/:id/board`
- **API:** `GET .../deliverables/:deliverableId/requirements/`, `GET .../requirements/:id/`, `POST .../requirements/:id/move/`
- **Description:** Client reviews completed requirements. Clicking a done card shows: Approve, Request Change, or Report Bug.
- **Steps:**
  1. Client clicks a completed requirement in the "Completados" section.
  2. Card detail modal opens showing description, configuration, flow, and review actions.
  3. Client clicks "Aprobar" → requirement accepted.
  4. Client clicks "Solicitar cambio" → navigates to change requests with pre-filled data.
  5. Client clicks "Reportar bug" → navigates to bug reports with pre-filled data.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-requirement-client-review.spec.js`

### 8.11 Collection Accounts & Deliverable Detail

#### FLOW: `platform-collection-accounts-list`

- **Module:** platform
- **Role:** platform-admin, platform-client
- **Priority:** P2
- **Routes:** `/platform/collection-accounts`
- **API:** `GET /api/accounts/collection-accounts/` (optional query params for admin filters)
- **Description:** Global list of collection accounts; admin sees filters and “New collection account”; client sees “My collection accounts”. Table rows link to detail via Open.
- **Steps:**
  1. User navigates to `/platform/collection-accounts`.
  2. List loads from API → table shows number, title, status, total, due date.
  3. User clicks Open → navigates to `/platform/collection-accounts/:id`.
  4. **[Admin]** User applies project/status filters and Apply filters → list refreshes.
  5. **[Admin]** User clicks New collection account → modal → `POST /api/accounts/collection-accounts/` → redirect to new detail (covered in E2E).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-collection-accounts.spec.js`

#### FLOW: `platform-collection-account-detail`

- **Module:** platform
- **Role:** platform-admin, platform-client
- **Priority:** P2
- **Routes:** `/platform/collection-accounts/:id`
- **API:** `GET/PATCH /api/accounts/collection-accounts/:id/`, `POST .../issue/`, `.../mark-paid/`, `.../mark-cancelled/`, `GET .../pdf/`
- **Description:** Single document view: status, amounts, line items; Download PDF; admin actions Issue / Mark paid / Cancel by status.
- **Steps:**
  1. User opens detail from list or direct URL.
  2. Document loads → title, public number, status, totals, line items render.
  3. User clicks Download PDF → PDF downloaded (blob).
  4. **[Admin — draft]** User clicks Issue → status becomes issued.
  5. **[Admin — issued]** User clicks Mark paid → status becomes paid.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-collection-accounts.spec.js`

#### FLOW: `platform-project-collection-accounts`

- **Module:** platform
- **Role:** platform-admin, platform-client
- **Priority:** P2
- **Routes:** `/platform/projects/:id/collection-accounts`
- **API:** `GET /api/accounts/projects/:id/collection-accounts/`
- **Description:** Project-scoped list of collection accounts with Open links to shared detail route.
- **Steps:**
  1. User navigates from project hub or URL to `/platform/projects/:projectId/collection-accounts`.
  2. List loads → cards or rows per account with status.
  3. User clicks Open → `/platform/collection-accounts/:id`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-collection-accounts.spec.js`

#### FLOW: `platform-deliverable-detail`

- **Module:** platform
- **Role:** platform-admin, platform-client
- **Priority:** P2
- **Routes:** `/platform/projects/:id/deliverables/:deliverableId`
- **API:** `GET /api/accounts/projects/:id/deliverables/:deliverableId/`, PDF subpaths from `pdf_download_paths`, optional attachment upload (admin)
- **Description:** Deliverable hub: title, description, epic; linked commercial proposal PDFs; main file and attachments; link to kanban filtered by deliverable; admin can upload annex.
- **Steps:**
  1. User navigates to deliverable detail URL (from list or deep link).
  2. Detail loads → heading, Documents section, Requirements / board CTA.
  3. If linked proposal exists → user clicks PDF comercial or PDF técnico → download.
  4. **[Admin]** User may upload attachment via form (optional branch).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-deliverables.spec.js`

#### FLOW: `platform-project-data-model`

- **Module:** platform
- **Role:** platform-admin, platform-client
- **Priority:** P2
- **Routes:** `/platform/projects/:id/data-model`
- **API:** `GET/POST /api/accounts/projects/:id/data-model-entities/`, `GET /api/accounts/projects/:id/data-model-entities/template/`
- **Description:** Manage the data model (entity list) for a project. Admin can upload a JSON payload via file or textarea, validate, and sync entities to the backend. Both roles browse the entity table.
- **Steps:**
  1. User navigates to `/platform/projects/:id/data-model` (linked from project detail or sidebar).
  2. Page loads entities from `GET /api/accounts/projects/:id/data-model-entities/`.
  3. **[Admin only]** "Subir modelo de datos" card renders with two template buttons ("Copiar plantilla" / "Descargar plantilla").
  4. Admin copies/downloads the JSON template (`{ entities: [{ name, description, keyFields, relationship }] }`).
  5. Admin uploads a `.json` file via file input OR pastes JSON into the textarea.
  6. Parse/validate runs on `@input`; detected entity count preview renders if valid; error message if invalid JSON.
  7. Admin clicks "Subir modelo de datos" → `POST /api/accounts/projects/:id/data-model-entities/`.
  8. Success banner "Modelo de datos actualizado correctamente." renders.
  9. Entity table refreshes with rows: Entidad | Descripción | Campos clave (badge chips) | Relación.
- **Branches:**
  - [Branch A — Empty state] No entities yet: client sees "No hay modelo de datos definido para este proyecto." Admin sees additional hint "Sube un JSON con las entidades para empezar."
  - [Branch B — Error state] API fetch fails: error message + "Reintentar" button visible.
  - [Branch C — Client role] Upload section not rendered; only entity table (or empty state) shown.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-data-model.spec.js`

### 8.12 Platform Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `platform-login` | platform | platform-admin/client | P1 | ✅ Covered | `e2e/platform/platform-login.spec.js` |
| `platform-verify-onboarding` | platform | platform-admin/client | P1 | ✅ Covered | `e2e/platform/platform-verify.spec.js` |
| `platform-complete-profile` | platform | platform-admin/client | P1 | ✅ Covered | `e2e/platform/platform-complete-profile.spec.js` |
| `platform-kanban-board` | platform | platform-admin/client | P1 | ✅ Covered | `e2e/platform/platform-kanban-board.spec.js` |
| `platform-hosting-subscription` | platform | platform-admin/client | P1 | ✅ Covered | `e2e/platform/platform-hosting-subscription.spec.js` |
| `platform-dashboard` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-dashboard.spec.js` |
| `platform-sidebar-navigation` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-sidebar.spec.js` |
| `platform-project-list` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-project-list.spec.js` |
| `platform-project-detail` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-project-detail.spec.js` |
| `platform-unified-board` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-unified-board.spec.js` |
| `platform-admin-client-list` | platform | platform-admin | P2 | ✅ Covered | `e2e/platform/platform-admin-client-list.spec.js` |
| `platform-admin-client-detail` | platform | platform-admin | P2 | ✅ Covered | `e2e/platform/platform-admin-client-detail.spec.js` |
| `platform-profile-edit` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-profile.spec.js` |
| `platform-change-requests` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-change-requests.spec.js` |
| `platform-bug-reports` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-bug-reports.spec.js` |
| `platform-deliverables` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-deliverables.spec.js` |
| `platform-notifications` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-notifications.spec.js` |
| `platform-kanban-json-upload` | platform | platform-admin | P2 | ✅ Covered | `e2e/platform/platform-kanban-json-upload.spec.js` |
| `platform-requirement-client-review` | platform | platform-client | P2 | ✅ Covered | `e2e/platform/platform-requirement-client-review.spec.js` |
| `platform-collection-accounts-list` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-collection-accounts.spec.js` |
| `platform-collection-account-detail` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-collection-accounts.spec.js` |
| `platform-project-collection-accounts` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-collection-accounts.spec.js` |
| `platform-deliverable-detail` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-deliverables.spec.js` |
| `platform-project-data-model` | platform | platform-admin/client | P2 | ✅ Covered | `e2e/platform/platform-data-model.spec.js` |
| `platform-admin-project-create` | platform | platform-admin | P3 | ✅ Covered | `e2e/platform/platform-project-create.spec.js` |
| `platform-kanban-card-comments` | platform | platform-admin/client | P3 | ✅ Covered | `e2e/platform/platform-kanban-comments.spec.js` |

### Platform Coverage Summary

- **Total platform flows:** 26
- **P1 (Critical):** 5
- **P2 (High):** 19
- **P3 (Medium):** 2
- **Covered:** 26 (100%)
- **Missing:** 0
- **Deferred:** 0

---

## 9. New Feature Flows (v2.7.0)

> Flows registered during the v2.7.0 audit (documents, admin management, deliverability, public landings). E2E specs were added afterward; coverage below reflects the current Playwright suite (`frontend/e2e/`).

### 9.1 Admin Document Management

#### FLOW: `admin-document-list`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents`
- **Description:** View the list of admin documents with title, status, client association, and row actions (edit, download PDF, duplicate, delete).
- **Steps:**
  1. Admin navigates to `/panel/documents`.
  2. Document list loads from API (`GET /api/content/documents/`).
  3. Table renders with columns: title, client name, status badge, created date, actions.
  4. Admin clicks a row or the edit icon → navigates to `/panel/documents/:id/edit`.
  5. "Nuevo Documento" button navigates to `/panel/documents/create`.
- **Branches:**
  - [Branch A — Empty state] No documents → "No hay documentos todavía." with create link.
  - [Branch B — Download PDF] Admin clicks download icon → PDF generated and downloaded.
  - [Branch C — Duplicate] Admin clicks duplicate icon → document cloned and list refreshes.
  - [Branch D — Delete] Admin clicks delete icon → confirm modal → document removed from list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-document-list.spec.js`

#### FLOW: `admin-document-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents/create`
- **Description:** Create a new admin document using Markdown paste mode (with live preview) or file upload mode.
- **Steps:**
  1. Admin navigates to `/panel/documents/create`.
  2. Page renders with "Pegar Markdown" / "Cargar Archivo" tab toggle.
  3. Admin fills title, optional client association.
  4. **Paste mode:** Admin pastes Markdown content → live preview renders alongside.
  5. **Upload mode:** Admin selects a file → file content loaded.
  6. Admin submits → API call `POST /api/content/documents/` creates document.
  7. On success, admin redirected to `/panel/documents`.
- **Branches:**
  - [Branch A — Validation error] Missing required fields → inline errors displayed.
  - [Branch B — Preview toggle] Admin clicks preview button → split-pane preview shown alongside editor.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-document-create.spec.js`

#### FLOW: `admin-document-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents/:id/edit`
- **Description:** Edit an existing admin document, update content and status, download as PDF.
- **Steps:**
  1. Admin navigates to `/panel/documents/:id/edit`.
  2. Document data loads from API (`GET /api/content/documents/:id/`).
  3. Edit form renders pre-filled with current content, title, status, client.
  4. Admin modifies content and clicks save.
  5. API call `PATCH /api/content/documents/:id/` updates document.
  6. Success feedback displayed.
- **Branches:**
  - [Branch A — Download PDF] Admin clicks "Descargar PDF" → PDF generated from current content.
  - [Branch B — Status change] Admin updates status (draft/published/archived) → status badge updates.
  - [Branch C — Back] "Volver a documentos" link → navigates to list without saving.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-document-edit.spec.js`

### 9.2 Admin User Management

#### FLOW: `admin-admin-management`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/admins`
- **Description:** Manage platform admin users — list with status filters, invite new admin via modal, deactivate existing admins.
- **Steps:**
  1. Admin navigates to `/panel/admins`.
  2. Admin list loads from API (`GET /api/accounts/admins/`).
  3. Filter tabs render: Todos / Activos / Inactivos.
  4. Each admin row shows avatar, name, email, role, status badge, and actions.
- **Branches:**
  - [Branch A — Invite] Admin clicks "Agregar Administrador" → modal opens with email, name, role fields → submit calls `POST /api/accounts/admins/` → invitation sent.
  - [Branch B — Filter] Admin clicks status tab → list filters client-side.
  - [Branch C — Deactivate] Admin clicks deactivate → confirm → `PATCH /api/accounts/admins/:id/` → status changes.
  - [Branch D — Empty state] No admins → empty state message with invite CTA.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-admin-management.spec.js`

### 9.3 Email Deliverability Dashboard

#### FLOW: `admin-email-deliverability`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/proposals/email-deliverability`
- **Description:** Dashboard tracking email send/delivery/bounce/open rates for all proposal-related automated emails. Admin monitors deliverability health.
- **Steps:**
  1. Admin navigates to `/panel/proposals/email-deliverability`.
  2. Dashboard loads email delivery metrics from API.
  3. Stats render: total sent, delivered, bounced, open rate.
  4. Per-proposal email log table shows individual send events.
- **Branches:**
  - [Branch A — Empty state] No emails sent yet → "No hay datos de entregas." message.
  - [Branch B — Date filter] Admin filters by date range → metrics update.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-email-deliverability.spec.js`

### 9.4 Public Landing Pages

#### FLOW: `public-landing-software`

- **Module:** public
- **Role:** guest
- **Priority:** P3
- **Routes:** `/landing-software`
- **Description:** Custom software development landing page with hero section, feature highlights, CTA, and contact form.
- **Steps:**
  1. Guest navigates to `/landing-software`.
  2. Hero section renders with headline and CTA button.
  3. Feature/service highlights section renders.
  4. Contact form or CTA link rendered at the bottom.
- **Branches:**
  - [Branch A — CTA click] Guest clicks primary CTA → scrolls to contact section or navigates to `/contacto`.
  - [Branch B — Locale] Page renders in both ES and EN via locale switcher.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-landing-software.spec.js`

#### FLOW: `public-landing-apps`

- **Module:** public
- **Role:** guest
- **Priority:** P3
- **Routes:** `/landing-apps`
- **Description:** Mobile app development landing page with hero section, feature highlights, platform badges (iOS/Android), CTA, and contact form.
- **Steps:**
  1. Guest navigates to `/landing-apps`.
  2. Hero section renders with headline and CTA button.
  3. Feature/service highlights and platform badges render.
  4. Contact form or CTA link rendered at the bottom.
- **Branches:**
  - [Branch A — CTA click] Guest clicks primary CTA → scrolls to contact section or navigates to `/contacto`.
  - [Branch B — Locale] Page renders in both ES and EN via locale switcher.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-landing-apps.spec.js`

---

### 9.5 New Flows Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-document-list` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-document-list.spec.js` |
| `admin-document-create` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-document-create.spec.js` |
| `admin-document-edit` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-document-edit.spec.js` |
| `admin-admin-management` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-admin-management.spec.js` |
| `admin-email-deliverability` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-email-deliverability.spec.js` |
| `public-landing-software` | public | guest | P3 | ✅ Covered | `e2e/public/public-landing-software.spec.js` |
| `public-landing-apps` | public | guest | P3 | ✅ Covered | `e2e/public/public-landing-apps.spec.js` |

---

## 10. New Feature Flows (v2.9.0)

> Flows registered during the v2.9.0 audit for contract generation, document management, and document sending features on the proposal edit Documents tab. These features are visible only when proposal status is `negotiating`, `accepted`, or `rejected`.

### 10.1 Admin Proposal Contract & Documents

#### FLOW: `admin-proposal-contract-generate`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (Documents tab)
- **Description:** Admin generates a development contract from the proposal edit Documents tab. Two source modes: "Contrato por defecto" (structured params form with auto-populated company settings for contractor/client info, banking details, contract date) or "Contrato personalizado" (paste or upload custom Markdown with live preview). Submit calls `POST /api/proposals/:id/contract/save-and-negotiate/`.
- **Steps:**
  1. Admin navigates to `/panel/proposals/:id/edit` for a proposal with status `negotiating`/`accepted`/`rejected`.
  2. Admin clicks the "Documentos" tab.
  3. In the "Contrato de desarrollo" section, admin clicks "Generar contrato de desarrollo" button (visible when no contract exists).
  4. ContractParamsModal opens with "Contrato por defecto" mode selected. Company settings auto-populate contractor fields.
  5. [Branch A — Default] Admin fills/verifies contractor params (name, cedula, email, city, bank details) and client params (name, cedula, email), sets contract date.
  6. [Branch B — Custom] Admin toggles to "Contrato personalizado", pastes or uploads a `.md` file, optionally toggles preview.
  7. Admin clicks "Generar contrato y negociar" → API call to `POST /api/proposals/:id/contract/save-and-negotiate/`.
  8. Contract document appears in the Documents tab with download links.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-contract-generate.spec.js`

#### FLOW: `admin-proposal-contract-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Documents tab)
- **Description:** Admin edits an existing contract's parameters via "Editar parámetros" button. ContractParamsModal opens pre-filled with saved params. Submit calls `PUT /api/proposals/:id/contract/update/`.
- **Steps:**
  1. Admin opens Documents tab for a proposal that already has a generated contract.
  2. Admin clicks "Editar parámetros" button next to the contract.
  3. ContractParamsModal opens in edit mode with existing params pre-filled.
  4. Admin modifies fields and clicks "Actualizar contrato".
  5. API call to `PUT /api/proposals/:id/contract/update/`.
  6. Updated contract reflected in Documents tab.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-contract-edit.spec.js`

#### FLOW: `admin-proposal-contract-download`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Documents tab)
- **Description:** Admin downloads contract PDF (final) or draft PDF from the Documents tab. Links visible only when a contract has been generated.
- **Steps:**
  1. Admin opens Documents tab for a proposal with a generated contract.
  2. "Descargar" link points to `GET /api/proposals/:id/contract/pdf/`.
  3. "Borrador" link points to `GET /api/proposals/:id/contract/draft-pdf/`.
  4. [Branch A — No contract] When no contract is generated, section shows "No generado" and no download links.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-contract-download.spec.js`

#### FLOW: `admin-proposal-documents-manage`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Documents tab)
- **Description:** Admin uploads additional documents (otrosí, legal annex, client document, other with custom type label) to a proposal. Existing documents listed with type badges. Non-generated documents can be deleted.
- **Steps:**
  1. Admin opens Documents tab.
  2. "Documentos adicionales" section lists existing uploaded documents with type badge and download link.
  3. Admin fills upload form: title, type (select), file, optionally custom label for "Otro" type.
  4. Admin clicks "Subir" → `POST /api/proposals/:id/documents/upload/` with FormData.
  5. New document appears in the list after refresh.
  6. Admin clicks delete icon on a non-generated document → `DELETE /api/proposals/:id/documents/:docId/delete/`.
  7. Document removed from list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-documents-manage.spec.js`

#### FLOW: `admin-proposal-documents-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (Documents tab)
- **Description:** Admin selects documents to send to client via email. Checkboxes for main docs (draft contract, commercial PDF, technical PDF) and additional uploaded docs. Opens SendDocumentsModal with editable email fields (subject, greeting, body, per-document descriptions, footer). Submit calls `POST /api/proposals/:id/documents/send/`.
- **Steps:**
  1. Admin opens Documents tab.
  2. "Enviar documentos al cliente" section shows checkboxes: draft contract (disabled if no contract), commercial, technical, plus any additional docs.
  3. Admin selects desired documents.
  4. Admin clicks "Enviar al cliente" button (disabled if no docs selected or no client email).
  5. SendDocumentsModal opens with pre-filled email: subject, greeting with client name, intro body, per-document descriptions, footer.
  6. Admin edits email fields as needed.
  7. Admin clicks "Enviar documentos" → API call to `POST /api/proposals/:id/documents/send/`.
  8. Success message: "Documentos enviados correctamente."
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-documents-send.spec.js`

---

### 10.2 New Flows Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-proposal-contract-generate` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-contract-generate.spec.js` |
| `admin-proposal-contract-edit` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-contract-edit.spec.js` |
| `admin-proposal-contract-download` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-contract-download.spec.js` |
| `admin-proposal-documents-manage` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-documents-manage.spec.js` |
| `admin-proposal-documents-send` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-documents-send.spec.js` |
