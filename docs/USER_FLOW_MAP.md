# User Flow Map

> **Version:** 2.29.0
> **Last updated:** 2026-04-20
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

### FLOW: `public-privacy-policy`

- **Module:** public
- **Role:** guest
- **Priority:** P4
- **Routes:** `/privacy-policy`
- **Description:** View the public privacy policy page with localized content (ES/EN).
- **Steps:**
  1. User navigates to `/privacy-policy`.
  2. Page renders with localized privacy policy content.
  3. SEO meta tags and structured data are present.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-privacy-policy.spec.js`

### FLOW: `public-terms-conditions`

- **Module:** public
- **Role:** guest
- **Priority:** P4
- **Routes:** `/terms-and-conditions`
- **Description:** View the public terms and conditions page with localized content (ES/EN).
- **Steps:**
  1. User navigates to `/terms-and-conditions`.
  2. Page renders with localized terms and conditions content.
  3. SEO meta tags and structured data are present.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-terms-conditions.spec.js`

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

### FLOW: `admin-proposal-advanced-filters`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Admin uses advanced filter panel with 11 dimensions (status, project type, market type, currency, language, investment range, heat score range, view count range, created date range, last activity date range, active status) and saves filter combinations as named tabs (max 12) with localStorage persistence and URL sync.
- **Steps:**
  1. Admin navigates to `/panel/proposals/` and clicks "Filtros" toggle button.
  2. Filter panel expands with responsive grid of filter controls.
  3. Admin selects filter values (e.g., status pills, project type dropdown, date range).
  4. Proposal table updates in real-time (client-side filtering, single-pass).
  5. Admin clicks "+" tab button → inline input appears → types tab name → clicks "Guardar".
  6. New named tab appears in tab bar; filters are persisted to localStorage.
  7. Admin reloads page → saved tabs persist; clicking a tab restores its filters.
  8. Admin right-clicks tab context menu → "Renombrar" or "Eliminar".
  9. "Todas" tab resets all filters. "Limpiar filtros" button clears active filters.
  10. URL updates with `?tab=<tabId>` for deep-linking.
- **Branches:**
  - [Branch A — Tab limit] When 12 tabs exist, "+" button is disabled with tooltip.
  - [Branch B — Mobile] Tab bar collapses to `<select>` dropdown below `md` breakpoint.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-advanced-filters.spec.js`

### FLOW: `admin-proposal-project-schedule`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/<id>/edit?tab=schedule`
- **Description:** Admin sets per-stage start/end dates (design, development) for an accepted proposal in the Cronograma tab, sees proportional status badges (faltan / vencida / completada), and marks stages as completed to silence deadline alerts. The daily Huey task `notify_proposal_stage_deadlines` reads these dates and emails the team a 70%-elapsed warning + every-3-day overdue reminder.
- **Steps:**
  1. Admin opens an accepted proposal via `/panel/proposals/<id>/edit`.
  2. Admin clicks the "Cronograma" tab (only visible when status is `accepted` or `finished`).
  3. Tab shows two stage cards: Diseño and Desarrollo.
  4. Admin types start_date and end_date for the Diseño stage and clicks "Guardar fechas".
  5. PUT `/api/proposals/<id>/stages/design/` succeeds; the stage card status badge updates ("Faltan X días" / "Vencida hace X días").
  6. Admin clicks "Marcar como completada" → POST `/api/proposals/<id>/stages/design/complete/` → badge becomes "🟢 Completada".
- **Branches:**
  - [Branch A — Validation] When start_date > end_date, the form shows an inline error and no request is sent.
  - [Branch B — Tab visibility] When the proposal is in `draft`/`sent`/`viewed`/`negotiating`, the Cronograma tab is hidden.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-project-schedule.spec.js`

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

### FLOW: `admin-proposal-client-autocomplete`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/create` (Manual tab), `/panel/proposals/:id/edit`
- **API:** `GET /api/proposals/client-profiles/search/?q=<term>`
- **Description:** Client picker autocomplete in the proposal create/edit form. Admin types a search term; backend returns matching clients (by name, email, or company) from the mini-CRM. Selecting a client auto-fills the snapshot fields (name, email, phone, company). When no match is found, a "Crear nuevo" button sets the typed value as a brand-new client name without triggering another search.
- **Steps:**
  1. Admin navigates to `/panel/proposals/create` and activates the Manual tab (or opens `/panel/proposals/:id/edit`).
  2. The autocomplete input (`[data-testid="client-autocomplete-input"]`) is visible.
  3. Admin types 2+ characters → `GET /api/proposals/client-profiles/search/?q=...` fires (debounced).
  4. Matching results render as a dropdown (`[data-testid="client-autocomplete-option-:id"]`) showing name, email, company, and total proposals count.
  5. Admin clicks a result → `#create-client-name`, `#create-client-email`, phone and company snapshot fields auto-populate.
- **Branches:**
  - [Branch A — No match] Dropdown shows "Crear nuevo" button (`[data-testid="client-autocomplete-create-new"]`) → clicking it sets the typed value as the client name and clears the dropdown.
  - [Branch B — Placeholder client] When the selected client has `is_email_placeholder=true`, the email field remains empty and the placeholder hint is shown (see `admin-proposal-client-no-email`).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-client-autocomplete.spec.js`

### FLOW: `admin-proposal-client-no-email`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/create` (Manual tab)
- **API:** `POST /api/proposals/` (omitted `client_email`)
- **Description:** Admin creates a proposal without providing a client email. The backend generates a placeholder email (`cliente_<id>@temp.example.com`), flags the client as `is_email_placeholder=true`, and pauses all automations for that client (e.g., reminder / overdue stage notifications). A hint banner informs the admin that email-based automations will be paused until the email is filled in.
- **Steps:**
  1. Admin navigates to `/panel/proposals/create` (Manual tab).
  2. Admin fills `#create-client-name` and leaves `#create-client-email` blank.
  3. Placeholder hint text (e.g., "email temporal" / "automatizaciones pausadas") renders near the email input.
  4. Admin submits the form → `POST /api/proposals/` with `client_email=""`.
  5. Backend creates the proposal and a placeholder client profile with `automations_paused=true`.
  6. Admin is redirected to `/panel/proposals/:id/edit`; the client snapshot shows the placeholder email.
- **Branches:**
  - [Branch A — Fill email later] Admin edits the client email from the proposal edit page later → the placeholder flag clears and automations resume (handled by `admin-mini-crm-clients` or proposal edit).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-client-autocomplete.spec.js`

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

### FLOW: `admin-proposal-slug-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (General tab → URL personalizada)
- **Description:** Admin sets or regenerates the human-friendly slug for the public proposal URL. The slug replaces the UUID in the shared link (`/proposal/<slug>/`) making it feel personal to the client. Includes format validation, uniqueness check, and one-click regeneration from client name.
- **Steps:**
  1. Admin opens a proposal and stays on the General tab.
  2. The slug input shows the current slug (auto-generated on creation from default pattern or client name).
  3. Admin types a new slug in the input field (lowercase, numbers, hyphens only).
  4. Client validates format with regex `/^[a-z0-9]+(?:-[a-z0-9]+)*$/`; red error shown for invalid format.
  5. Admin clicks "Guardar URL" → `PATCH /api/proposals/:id/update/` with `{ slug }`.
  6. Server validates uniqueness; 400 error surfaced in UI if taken.
  7. Success state (✓) shown; copy-link button and preview href update to use new slug.
  8. [Branch] Admin clicks "Regenerar" to reset slug from client name via `toSlug(clientName)`.
- **Branches:**
  - [Branch A — Valid format] Save succeeds, slug persists, public URL updates.
  - [Branch B — Invalid format] Red error message blocks save.
  - [Branch C — Duplicate slug] Server 400 → "Esa URL ya está en uso" message.
  - [Branch D — Regenerate] Slug input pre-filled with `toSlug(clientName)`; admin can still modify before saving.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-slug-edit.spec.js`

### FLOW: `admin-proposal-section-edit-form`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (Sections tab)
- **Description:** Admin edits a proposal section using the structured form fields. Each of the 17 section types has its own form layout (greeting, executive_summary, context_diagnostic, conversion_strategy, roi_projection, design_ux, creative_support, development_stages, process_methodology, functional_requirements, timeline, investment, value_added_modules, proposal_summary, final_note, next_steps, technical_document). When saved in form mode, `_editMode: 'form'` is stored in content_json and the client sees the structured presentation.
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
- **Routes:** `/panel/defaults?mode=proposal` (old `/panel/proposals/defaults` redirects here)
- **Description:** Admin manages the default section configurations used when creating new proposals. Supports both ES and EN languages. Changes are saved to a DB-backed config and applied to all future proposals. Includes reset-to-hardcoded functionality.
- **Steps:**
  1. Admin navigates to `/panel/defaults?mode=proposal` via the "Defaults" sidebar item or the "Valores por Defecto" button on the proposals list page.
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

### FLOW: `admin-proposal-defaults-slug-pattern`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/defaults?mode=proposal` (General tab)
- **Description:** Admin configures the default slug pattern used when new proposals are created. The pattern supports `{client_name}`, `{project_type}`, and `{year}` placeholders. A live preview below the input shows the slugified result (e.g., `{client_name}` → `/proposal/empresa-demo`). Saved to `ProposalDefaultConfig.default_slug_pattern`.
- **Steps:**
  1. Admin navigates to `/panel/defaults?mode=proposal`.
  2. General tab renders. Slug pattern input shows current value (default: `{client_name}`).
  3. Live preview below input updates reactively as admin types, showing the `toSlug()` result.
  4. Admin edits the pattern (e.g., `{client_name}-{year}`).
  5. Admin clicks "Guardar" → `PUT /api/proposals/defaults/` with `{ default_slug_pattern }`.
  6. Future proposals auto-generate slugs using the new pattern.
- **Branches:**
  - [Branch A — Valid pattern] Pattern saved; new proposals use the pattern.
  - [Branch B — Custom text] Any free-text pattern (no placeholders) works; becomes a fixed prefix with collision suffix appended.
- **Coverage:** ❌ Not covered
- **E2E Spec:** *(pending `e2e/admin/admin-proposal-defaults-slug-pattern.spec.js`)*

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
- **Description:** View a Mini-CRM client list with tab filtering (Todos/Activos/Huérfanos), search, expand client to see linked proposals, and empty state.
- **Steps:**
  1. Admin navigates to `/panel/clients/`.
  2. Client list loads from `GET /api/proposals/client-profiles/`.
  3. Clients render with name, email, proposal count, and orphan/placeholder badges.
  4. Admin uses tab buttons (Todos/Activos/Huérfanos) to filter — sends `?orphans=true/false`.
  5. Admin searches clients by name, email, or company.
  6. Admin expands a client row to view individual proposals (lazy-loaded via `GET /api/proposals/client-profiles/:id/`).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-mini-crm-clients.spec.js`
- **Backend Tests:** `content/tests/views/test_proposal_clients_views.py`

### FLOW: `admin-client-create-standalone`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`
- **Description:** Create a new client profile standalone (without a proposal) from the clients page via the "+ Nuevo cliente" modal. Email is optional — if omitted the backend generates a placeholder `cliente_<id>@temp.example.com` and the client shows a placeholder badge.
- **Steps:**
  1. Admin clicks "+ Nuevo cliente" button (data-testid: `clients-new-button`).
  2. Modal opens with name, email, phone, company fields.
  3. Admin fills the form (email is optional).
  4. Admin clicks "Crear cliente" (data-testid: `clients-new-submit`).
  5. API call to `POST /api/proposals/client-profiles/create/` — backend calls `proposal_client_service.get_or_create_client_for_proposal`.
  6. New client appears at the top of the list (store prepends it).
- **Branches:**
  - [Branch A — With email] Client created with real email, no badge.
  - [Branch B — Without email] Backend generates `cliente_<id>@temp.example.com`; client row shows 📧 placeholder badge.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-mini-crm-clients.spec.js`
- **Backend Tests:** `content/tests/views/test_proposal_clients_views.py::TestCreateProposalClient`

### FLOW: `admin-client-delete-orphan`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`
- **Description:** Delete an orphan client (zero proposals + zero platform projects) via the trash icon that appears only on orphan rows. A confirm modal prevents accidental deletion.
- **Steps:**
  1. Admin navigates to `/panel/clients/` (or switches to Huérfanos tab).
  2. Orphan client rows show a trash icon (data-testid: `client-delete-<id>`).
  3. Admin clicks the trash icon.
  4. ConfirmModal appears with warning text.
  5. Admin confirms → `DELETE /api/proposals/client-profiles/:id/delete/`.
  6. Client row is removed from the list (store filters it out client-side).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-mini-crm-clients.spec.js`
- **Backend Tests:** `content/tests/views/test_proposal_clients_views.py::TestDeleteProposalClient`, `content/tests/views/test_proposal_clients_views.py::TestOrphanFlagTransitionsAfterProposalDelete`

### FLOW: `admin-client-delete-protected`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients/`
- **Description:** Active clients (those with linked proposals or platform projects) do NOT show the delete trash icon. The backend also enforces this with a 400 + `client_has_proposals` / `client_has_projects` error code if the API is called directly.
- **Steps:**
  1. Admin navigates to `/panel/clients/`.
  2. Clients with `is_orphan: false` render WITHOUT a trash icon.
  3. Attempting DELETE via API returns `400 { error: 'client_has_proposals', count: N }`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-mini-crm-clients.spec.js`
- **Backend Tests:** `content/tests/views/test_proposal_clients_views.py::TestDeleteProposalClient::test_delete_with_proposals_returns_400_with_error_code`

### FLOW: `admin-proposal-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/`, `/panel/proposals/:id/edit`
- **Description:** Send a proposal to a client via email. On edit page, a visual pre-send checklist modal replaces the native `confirm()` dialog, validating: client email, client name, investment > $0, future expiration date, at least 1 enabled section. The email body now interpolates the editable `email_intro` textarea (BusinessProposal.email_intro, persisted on the General tab) and the commercial PDF is attached automatically (`ProposalEmailService._attach_commercial_pdf`). The backend returns `email_delivery: { ok, reason, detail }`; when `ok=false`, the panel shows a red toast with the reason (`placeholder_email`, `template_disabled`, `send_failed`) instead of the generic "Propuesta enviada" toast, so the admin learns the email did not actually reach the client.
- **Steps:**
  1. Admin views the proposal edit page or the actions modal in the list page.
  2. Admin (optional) edits the "Texto introductorio del correo" textarea (`data-testid=edit-email-intro`) in the General tab and saves the form. Empty falls back to a default derived from the title.
  3. Admin clicks "Enviar al Cliente".
  4. Pre-send checklist modal opens showing pass/fail status for each item (✓/✗).
  5. "Enviar al Cliente" button is disabled until all checks pass.
  6. Admin clicks "Enviar al Cliente" in modal → API call to `POST /api/proposals/:id/send/`.
  7. Backend changes status to `sent`, generates the commercial PDF, attaches it, sends the email, and returns the proposal payload with `email_delivery`. `EmailLog.metadata.pdf_attached` records whether the attachment succeeded.
  8. If `email_delivery.ok === true`, success toast "Propuesta enviada al cliente". If `false`, error toast surfacing `email_delivery.detail || email_delivery.reason` with a hint to verify client email and use "Re-enviar".
- **Coverage:** 🟡 Partial — happy path covered; **email_delivery failure-feedback toast, `email_intro` editing, and PDF-attached metadata are not asserted in E2E**.
- **E2E Spec:** `e2e/admin/admin-proposal-send.spec.js` (extend with: edit `email_intro` and assert it appears in the request payload; mocked `email_delivery.ok=false` cases for `placeholder_email`, `template_disabled`, `send_failed`).

### FLOW: `admin-proposal-multi-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit`
- **Description:** Send a single email referencing 2+ proposals from the same client. From the edit page, the lightning-bolt button opens `ProposalActionsModal`; the new action "Enviar varias propuestas como un solo correo" (visible whenever `client_email` is set) opens `ProposalMultiSendModal`. The modal lists every proposal of that client grouped by status: Borradores (draft), Enviadas/Vistas/Negociación (sent/viewed/negotiating), and Expiradas (status=`expired` or past `expires_at`). The current proposal is pre-selected and the checkbox is disabled to keep it always included. Selecting an "Expiradas" item shows a "Se reabrirá" badge. The send button stays disabled until ≥2 are selected and is capped at 10. Click → `POST /api/proposals/:id/send-multi/` with `{ proposal_ids: [...] }`. The backend dispatches a single email rendering each proposal as a numbered phase ("Propuesta N de M") and attaches one PDF per proposal. Per-proposal side effects: draft→sent + Huey reminders, expired/past expires_at→reopen + extend expires_at, sent/viewed/negotiating→resend timers (no status change). One `EmailLog` row per proposal sharing a `group_uuid` in metadata, plus a `ProposalChangeLog` entry per proposal.
- **Steps:**
  1. Admin opens `/panel/proposals/:id/edit` for a client that has another eligible proposal.
  2. Admin clicks the lightning-bolt button next to "Guardar cambios".
  3. `ProposalActionsModal` opens; admin clicks "Enviar varias propuestas como un solo correo" (`data-testid=proposal-action-send-multi`).
  4. `ProposalMultiSendModal` opens, listing the client's other proposals grouped by status. The current proposal is pre-checked and locked.
  5. Admin selects one or more additional proposals → "Enviar N propuestas" button enables.
  6. Admin clicks the send button → `POST /api/proposals/:id/send-multi/` with `proposal_ids`.
  7. Backend validates same-client, ≥2 proposals, ≤10 proposals, applies side effects, sends one email with N PDF attachments, returns the proposal payload + `email_delivery` + `transitions` map.
  8. Modal closes; success toast "Correo enviado al cliente con N propuestas." renders. Page data refreshes so updated statuses/expires_at show.
- **Coverage:** ❌ Missing — feature is brand new; no spec exercises the modal, the backend call, the same-client validation, the ≥2/≤10 guards, or the success toast.
- **E2E Spec (suggested):** `e2e/admin/admin-proposal-multi-send.spec.js`. Mock `GET /api/proposals/?client_id=` to return ≥2 proposals across at least two of the status groups, click through the modal, mock `POST /api/proposals/:id/send-multi/` with `email_delivery.ok=true`, and assert the success toast.

### FLOW: `admin-proposal-resend`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Resend an already-sent proposal via the "Re-enviar" action in the proposals list actions modal. Keeps the existing `expires_at`, resets `sent_at`, `reminder_sent_at`, `urgency_email_sent_at`, re-schedules Huey reminders, and dispatches the proposal email again. The endpoint returns `email_delivery`; the panel toast surfaces success or failure with the reason — symmetric to `admin-proposal-send`.
- **Steps:**
  1. Admin opens the actions modal for a proposal whose status is `sent`/`viewed`.
  2. Admin clicks "Re-enviar".
  3. Confirmation dialog "¿Re-enviar esta propuesta? Se mantendrá la misma fecha de expiración." is shown.
  4. On confirm → `POST /api/proposals/:id/resend/`.
  5. Backend resets timers and re-sends the email, returning `email_delivery`.
  6. Success toast "Propuesta re-enviada al cliente" or error toast with `email_delivery.detail || email_delivery.reason`.
- **Coverage:** ❌ Missing — only button visibility is asserted in `admin-proposal-send.spec.js`; the end-to-end resend execution path and the toast feedback have no dedicated spec.
- **E2E Spec (suggested):** `e2e/admin/admin-proposal-resend.spec.js`

### FLOW: `admin-proposal-reopen-from-expired`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (General tab — date picker, and JSON re-import panel)
- **Description:** Recover an `expired` proposal by extending `expires_at` to a future date. The validator no longer blocks re-saving when the date is left unchanged, so admins can fix any other field on an expired proposal; when the date does move into the future, `ProposalService.reopen_if_unexpired` auto-reverts `status` from `expired` to `viewed` (when `view_count > 0`) or `sent`, and logs an "Auto-reopened from expired…" entry in `ProposalChangeLog`. Same behavior on both update paths (form PATCH and JSON re-import PUT).
- **Steps:**
  1. Admin opens an expired proposal at `/panel/proposals/:id/edit`. The status badge reads "Expirada".
  2. Admin moves the `expires_at` datetime input to a future date (or pastes a JSON with a future `expires_at` in the JSON re-import panel).
  3. Admin clicks Save.
  4. PATCH `/api/proposals/:id/update/` (form) or PUT `/api/proposals/:id/update-from-json/` (JSON path).
  5. Backend persists `expires_at` and `status` in a single save; `ProposalChangeLog` records the auto-reopen.
  6. UI refreshes — the status badge no longer shows "Expirada"; the proposal returns to `sent`/`viewed`.
- **Branches:**
  - [Branch A — form path] PATCH `/update/`. Status reverts to `viewed` if `view_count > 0`, else `sent`.
  - [Branch B — JSON path] PUT `/update-from-json/`. Same reopen logic; `ProposalFromJSONSerializer` reads the bound proposal via `context={'proposal': proposal}` to skip the future-only check when `expires_at` is unchanged.
  - [Branch C — keep `expires_at` unchanged] Admin edits other fields on an expired proposal without touching the date. Save succeeds (no longer blocked by validator); `status` stays `expired`.
- **Coverage:** ❌ Missing — backend pytest covers the behavior (`test_update_reopens_status_when_expires_at_moved_to_future_no_views`, `test_update_reopens_to_viewed_when_proposal_was_visited`, `test_update_from_json_reopens_status_when_expires_at_moved_to_future`, plus the unchanged-date variants), but no Playwright spec exercises the UI path.
- **E2E Spec (suggested):** `e2e/admin/admin-proposal-reopen-from-expired.spec.js`

### FLOW: `admin-proposal-update-from-json`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (JSON re-import panel)
- **Description:** Re-import a complete JSON payload over an existing proposal — distinct from `admin-proposal-create-from-json` which creates a new proposal. The admin pastes/uploads JSON in the edit screen; the store calls `PUT /api/proposals/:id/update-from-json/` which replaces metadata and each known section's `content_json`. Unrecognized section keys come back as a `warnings` array; sections not present in the payload are left unchanged.
- **Steps:**
  1. Admin opens `/panel/proposals/:id/edit` and switches to the JSON re-import panel.
  2. Admin pastes (or uploads) a JSON payload that follows the `create-from-json` template shape.
  3. Admin clicks "Actualizar desde JSON".
  4. Frontend store calls `proposalStore.updateProposalFromJSON(id, payload)` → `PUT /api/proposals/:id/update-from-json/`.
  5. Backend validates via `ProposalFromJSONSerializer` (with the bound proposal in context, so an unchanged past `expires_at` is allowed), updates metadata fields, replaces section `content_json` for matching keys, and logs each changed field.
  6. Success toast "Propuesta actualizada desde JSON."; if the JSON contained unmapped section keys, the response includes a `warnings` array which the UI surfaces.
- **Branches:**
  - [Branch A — happy path] Valid JSON → 200 with refreshed proposal payload.
  - [Branch B — unknown section keys] Payload includes unrecognized keys → 200 + `warnings` listing them.
  - [Branch C — invalid `expires_at`] New value in the past → 400 from `validate_expires_at` (unless the value matches the proposal's stored `expires_at`).
- **Coverage:** ❌ Missing — backend pytest covers the round-trip and warnings cases (`TestUpdateProposalFromJSON`), but no Playwright spec exercises the UI re-import path.
- **E2E Spec (suggested):** `e2e/admin/admin-proposal-update-from-json.spec.js`

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

### FLOW: `admin-proposal-actions-modal`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals`
- **API:** (no direct API call — modal renders action buttons from listing row data)
- **Description:** Admin opens an actions modal from a proposal row in the listing. Modal displays quick-action buttons: edit, preview, send/resend, copy link, WhatsApp, duplicate, toggle active, delete. Send/Resend visibility is conditional on proposal status.
- **Steps:**
  1. Admin is on the proposal listing `/panel/proposals`.
  2. Admin clicks the actions icon (⋮) on a proposal row.
  3. Actions modal opens with buttons: Edit, Preview, Send/Resend, Copy, WhatsApp, Duplicate, Toggle, Delete.
  4. [Branch A — Draft] "Send" action visible; "Resend" hidden.
  5. [Branch B — Sent/Viewed] "Resend" action visible; "Send" hidden.
  6. Admin clicks any action → navigates or triggers the corresponding flow.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-actions-modal.spec.js`

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

### FLOW: `proposal-value-added-modules`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The "Value Added Modules" section (`section_type: value_added_modules`) renders a card grid of included-free items. Each card is resolved from the proposal's `functional_requirements` groups using `module_ids`. Cards show module title, icon, justification text, and a "Gratis" badge. An optional `footer_note` appears below the grid. Falls back to "Incluido sin costo adicional" when no `title` is set in `content_json`.
- **Steps:**
  1. Client navigates to the Value Added Modules section.
  2. Section title and intro text render.
  3. Each module card resolves its title and icon from `functional_requirements.content_json.groups`.
  4. Each card shows the justification text from `content_json.justifications`.
  5. A "Gratis" badge appears on every card.
  6. Optional `footer_note` renders at the bottom of the section.
- **Coverage:** ✅ Covered — `frontend/e2e/proposal/proposal-value-added-modules.spec.js`

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

### FLOW: `proposal-investment-calculator`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **API:** (client-side only — no API call for toggling)
- **Description:** Client opens investment calculator modal from the closing/investment section, toggles optional feature modules on/off, sees dynamic total investment and estimated timeline update in real time, and confirms or cancels the selection.
- **Steps:**
  1. Client views the proposal and navigates to the Investment section.
  2. Client clicks "Personalizar tu inversión" to open the calculator modal.
  3. Client toggles optional feature modules — total investment and timeline update dynamically.
  4. Client clicks "Confirmar selección" → modal closes; closing section reflects updated total.
  5. [Branch B — Abandon] Client closes modal without confirming → selection reverts.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-investment-calculator.spec.js`

### FLOW: `proposal-comment-from-closing`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Client submits a written comment from the proposal closing panel via a comment modal. This is distinct from the full accept/reject/negotiate response flow.
- **Steps:**
  1. Client is viewing the proposal closing section.
  2. Client opens the comment modal from the closing panel.
  3. Client types a comment and submits.
  4. Comment is recorded; confirmation feedback shown.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-comment-flow.spec.js`

### FLOW: `proposal-rejection-smart-recovery`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** After a client rejects a proposal, context-specific recovery cards render based on the rejection reason, each with appropriate CTAs (e.g., schedule call, adjust budget, revisit later).
- **Steps:**
  1. Client rejects the proposal and sees the rejection confirmation screen.
  2. Recovery cards render based on the rejection reason provided.
  3. Each card shows a relevant CTA (schedule a call, request changes, revisit later).
  4. Client can click a CTA to take the suggested recovery action.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-rejection-recovery.spec.js`

### FLOW: `proposal-functional-requirements-modal`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Client clicks a functional requirement group card in the proposal to open a detail modal showing individual requirement items with icons and descriptions.
- **Steps:**
  1. Client views the functional requirements section of the proposal.
  2. Client clicks a requirement group card.
  3. Detail modal opens listing individual items with icons and descriptions.
  4. Client closes the modal by clicking outside or the close button.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-requirements-modal.spec.js`

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

### FLOW: `proposal-roi-projection`

- **Module:** proposal
- **Role:** guest (via shared UUID link); admin (edits via SectionEditor)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** ROI Projection / Business Outcomes section. Renders configurable KPI cards (visualizations/day, ad reach, MRR, payback, year-1 revenue) and per-scenario blocks (Conservative / Realistic / Optimistic) with metric rows and an emphasis flag for totals; closes with an optional CTA note. The section sits at `order=4`, between `conversion_strategy` and `investment`, so the sponsor sees quantified business outcomes BEFORE the price ask. The section is **web-only** — it has no PDF renderer (sections without a renderer are silently skipped). Migration 0118 backfilled an empty disabled row in every existing proposal so admins can enable + populate per-proposal without breaking legacy flows.
- **Steps:**
  1. Client opens `/proposal/:uuid` and selects "Propuesta Completa" in the gateway.
  2. Client navigates past `greeting`, `executive_summary`, `context_diagnostic`, `conversion_strategy` panels.
  3. ROI Projection panel renders if the section's `is_enabled=true`.
  4. KPI cards display value, label, optional sublabel, and source citation.
  5. Scenarios block lists each scenario with metric rows; metrics with `emphasis=true` get bolded total styling.
  6. CTA note (if any) renders inside a primary-tinted banner closing the section.
- **Branches:**
  - [Branch A — Disabled section] When `is_enabled=false`, the panel is filtered out of `displayPanels` (regression-tested for the 31 legacy proposals that received the row via migration 0118).
  - [Branch B — Empty arrays] When `kpis` and `scenarios` are empty, only header/subtitle/CTA render without breaking the layout.
  - [Branch C — Admin edit] Admin form in `SectionEditor.vue` lets admins drag-reorder KPIs and scenarios; round-trip JSON persistence is validated by `test/components/admin-sectionEditorUtils-roi.test.js`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-roi-projection.spec.js`
- **Unit Tests:** `test/components/admin-sectionEditorUtils-roi.test.js`, `test/composables/useLinkify-html-escape.test.js`
- **Backend Tests:** `content/tests/test_roi_projection.py`

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

### FLOW: `admin-diagnostic-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/diagnostics/create` → `/panel/diagnostics/:id/edit`
- **Description:** Admin creates a new WebAppDiagnostic by searching for an existing client via autocomplete (reuses `/api/proposals/client-profiles/search/`), selecting language, and submitting. The service seeds 8 JSON sections (`purpose`, `radiography`, `categories`, `delivery_structure`, `executive_summary`, `cost`, `timeline`, `scope`) from `content.seeds.diagnostic_template` and redirects to the edit page.
- **Steps:**
  1. Admin navigates to `/panel/diagnostics/create`.
  2. Types in the client search input (autocomplete fetches from `client-profiles/search`).
  3. Selects a client from the dropdown — submit button becomes enabled.
  4. Optionally sets a custom title.
  5. Clicks "Crear diagnóstico" → POST `/api/diagnostics/create/`.
  6. Redirected to `/panel/diagnostics/:id/edit`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-create.spec.js`

---

### FLOW: `admin-diagnostic-send-initial`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/diagnostics/:id/edit`
- **Description:** Admin sends the initial-phase diagnostic to the client from the edit page, transitioning status DRAFT → SENT (stamps `initial_sent_at`). Then promotes the diagnostic to NEGOTIATING once the client authorises the work. Public view exposes only sections whose `visibility ∈ {initial, both}`.
- **Steps:**
  1. Admin navigates to `/panel/diagnostics/:id/edit` (status: DRAFT).
  2. Clicks "Enviar envío inicial" → POST `/api/diagnostics/:id/send-initial/`.
  3. Status transitions to SENT; `initial_sent_at` stamped; client email dispatched; response body carries `email_ok` flag.
  4. After client confirmation, admin clicks "Marcar en análisis" → POST `/api/diagnostics/:id/mark-in-analysis/`.
  5. Status transitions to NEGOTIATING.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-send.spec.js`

---

### FLOW: `admin-diagnostic-send-final`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/diagnostics/:id/edit`
- **Description:** Admin completes pricing and radiography data, finalises the `categories` section with findings/recommendations + the `executive_summary` section with severity counts, then sends the final-phase diagnostic from NEGOTIATING state, transitioning back to SENT with `final_sent_at` stamped. Public view now also exposes sections whose `visibility = final`.
- **Steps:**
  1. Admin updates pricing fields in the General tab and radiography data in the Secciones tab (as of 2026-04-18 the Pricing and Radiografía sub-tabs live in General/Secciones; the former "Det. técnico" tab was retired).
  2. Fills findings, strengths, and recommendations for each of the 14 categories in the Secciones tab.
  3. Completes the Resumen Ejecutivo section with severity counts + narrative.
  4. Clicks "Enviar diagnóstico final" → POST `/api/diagnostics/:id/send-final/`.
  5. Status returns to SENT; `final_sent_at` stamped; email sent to client with the public link.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-send.spec.js`

---

### FLOW: `admin-diagnostic-sections`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/diagnostics/:id/edit` (Secciones tab)
- **Description:** Admin edits each of the 8 JSON sections through typed form components. Each section has its own form (paragraphs, severity scale, 14-category findings/recommendations, radiography table, timeline day distribution, cost payment description, etc.). Edits are debounced 600 ms and PATCHed to `/sections/:id/update/`. A per-section "Restaurar contenido por defecto" action reloads from the seed. The tab header shows a **completeness indicator** (progress bar + percentage) that counts how many enabled sections have non-empty `content_json`. Raw-JSON export/import is a separate flow (`admin-diagnostic-json-export` / `admin-diagnostic-json-import`).
- **Steps:**
  1. Admin opens the Secciones tab — the completeness bar renders at the top and the 8 seeded section cards render (collapsed).
  2. Expands a section, edits its typed form (e.g., appends a finding in the Categorías section).
  3. After 600 ms of inactivity the change PATCHes; saving indicator flips to "Guardado HH:MM".
  4. Completeness percentage and color band (≥80 emerald / ≥50 amber / otherwise red) update as enabled sections gain content.
  5. A `section_updated` entry appears in the Actividad timeline.
- **Branches:**
  - [Visibility toggle] Changing `visibility` between `initial` / `final` / `both` changes what the public page shows per phase.
  - [Disable] Unchecking "Activa en la vista pública" hides the section without deleting it and removes it from the completeness denominator.
  - [Reset] "Restaurar contenido por defecto" restores the section from `content.seeds.diagnostic_template.default_sections()` via POST `/sections/:id/reset/`.
  - [Completeness indicator] Progress bar reflects `sectionsWithContent / enabledSectionsCount`; empty content + disabled sections both drop the ratio.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-sections.spec.js`

---

### FLOW: `admin-diagnostic-activity`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` (Actividad tab)
- **Description:** Admin reviews the `DiagnosticChangeLog` timeline for a diagnostic and logs manual notes (note / call / meeting / followup). Automated entries are appended by the backend on creation, status transitions, section edits, email sends, and client responses.
- **Steps:**
  1. Admin navigates to the Actividad tab.
  2. Selects a change_type, types a description, clicks "Registrar" → POST `/activity/create/`.
  3. New entry appears at the top of the timeline with icon + color + timestamp.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-sections.spec.js`

---

### FLOW: `admin-diagnostic-analytics`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` (Analytics tab)
- **Description:** Admin reviews full analytics dashboard at parity with proposal analytics: engagement score (0–100 color-coded), 6 summary KPI cards (total views, unique sessions, first view, reading time, coverage %, last visit), global comparison (3 metrics with ↑↓ arrows), funnel with drop-off % per section, device breakdown (desktop/mobile/tablet via user-agent), suggested actions (heuristic), skipped sections warning, section interest heatmap + top-2 insights, section engagement table, activity timeline (DiagnosticChangeLog), sessions history (last 50, no Mode column), and CSV export. No view-mode comparison, no share-links table (not applicable to diagnostics).
- **Steps:**
  1. Admin navigates to the Analytics tab — GET `/analytics/` fires on mount.
  2. Engagement score card renders with color-coded level label.
  3. Summary cards show total_views, unique_sessions, first_viewed_at, etc.
  4. Funnel rows render with section names and drop-off percentages.
  5. Device breakdown card shows desktop/mobile/tablet counts.
  6. CSV export button triggers download via `window.open`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-analytics.spec.js` (also smoke-tested in `e2e/admin/admin-diagnostic-sections.spec.js`)

---

### FLOW: `admin-diagnostic-engagement-score`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` (Analytics tab — Engagement Score card)
- **Description:** Engagement score card renders with the correct color-coded label based on score value: ≥70 → "Alto engagement — prioridad de follow-up" (emerald), 40–69 → "Engagement moderado" (yellow), <40 → "Bajo engagement — necesita atención" (red). Card is hidden when `engagement_score` is null.
- **Steps:**
  1. Admin opens Analytics tab with score ≥70 → sees "Alto engagement" in emerald.
  2. Admin opens Analytics tab with score <40 → sees "Bajo engagement" in red.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-analytics.spec.js`

---

### FLOW: `admin-diagnostic-prompt`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` (Prompt tab)
- **Description:** Admin copies / edits / downloads the two diagnostic prompts used with an LLM to draft content — "Propuesta comercial" (fills the 8-section JSON narrative) and "Detalle técnico" (fills the `categories` section with per-category findings at the 4 severity levels). State is persisted per browser via `localStorage` using `usePromptState({storageKey, defaultPrompt})`.
- **Steps:**
  1. Admin navigates to the Prompt tab.
  2. Selects a sub-tab (Comercial / Técnico).
  3. Clicks Copiar / Editar / Descargar / Restaurar — prompt text round-trips through `localStorage`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-prompt.spec.js` (5 tests: sub-tabs visible, edit mode, save custom, restore original, technical sub-tab).

---

### FLOW: `admin-diagnostic-email`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` → Correos tab
- **Description:** Admin sends a follow-up branded email to the client from the Correos tab of the diagnostic detail page. The composer supports a recipient address, subject, greeting, draggable body sections, footer, and optional file attachments. Email history shows previous sends with expandable metadata.
- **Steps:**
  1. Admin navigates to `/panel/diagnostics/:id/edit`.
  2. Clicks the "Correos" tab → composer loads with defaults from `GET /api/diagnostics/:id/email/defaults/`.
  3. Fills in sections and clicks "Enviar correo" → `POST /api/diagnostics/:id/email/send/` (FormData).
  4. On success, history list refreshes and shows the new send.
  5. Email is logged in `EmailLog` with `metadata.diagnostic_uuid`.
- **Branches:**
  - [Error] If client has no email, send button is disabled.
  - [Rate limit] Backend enforces 1 send/minute; 429 surfaces as an error message.
  - [NDA attachment] Admin checks "Adjuntar acuerdo de confidencialidad" → `attach_confidentiality: '1'` appended to FormData → backend generates confidentiality PDF and attaches it to the email; if PDF generation fails (missing diagnostic params), backend returns 400 and frontend shows `sendError`.
- **Coverage:** ✅ Covered (including NDA checkbox branch, Apr 20 2026)
- **E2E Spec:** `e2e/admin/admin-diagnostic-email-documents.spec.js`

---

### FLOW: `admin-diagnostic-documents`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` → Documentos tab
- **Description:** Admin uploads, manages, and sends file attachments (PDF, Word, Excel, images) to the client from the Documentos tab of the diagnostic detail page. Supports document types: `confidentiality_agreement` (system-generated, see `admin-diagnostic-confidentiality-*` flows), `amendment`, `legal_annex`, `client_document`, `other`.
- **Steps:**
  1. Admin navigates to `/panel/diagnostics/:id/edit`.
  2. Clicks the "Documentos" tab.
  3. Fills in the upload form (title, type, file) and clicks upload → `POST /api/diagnostics/:id/attachments/upload/`.
  4. The new attachment appears in the list.
  5. Admin selects one or more attachments via checkboxes and clicks "Enviar al cliente".
  6. `SendDiagnosticDocumentsModal` opens to compose the send email.
  7. Admin submits → `POST /api/diagnostics/:id/attachments/send/`.
  8. Email is logged in `EmailLog` with `metadata.diagnostic_uuid`, `metadata.attached_doc_ids`, and `metadata.extra_filenames`.
- **Branches:**
  - [No email] Send button disabled when no client email configured.
  - [No selection] Send button disabled until at least one checkbox is checked (counts both `selectedIds` and `selectedMainDocs`).
  - [NDA included] When the diagnostic has a generated NDA, an extra checkbox "📋 NDA — Acuerdo de Confidencialidad (borrador con marca de agua)" appears above the attachment list. When checked, the send payload includes `documents: ['confidentiality_agreement']` and the backend appends a freshly-generated draft NDA (with `BORRADOR` watermark and `XXX-XXX-XXX` placeholders) to the email.
  - [Delete] Admin clicks delete on a non-generated attachment → `DELETE /api/diagnostics/:id/attachments/:att_id/delete/` → row removed.
  - [Delete blocked] Generated NDA attachments (`is_generated=true`) cannot be deleted; backend returns HTTP 400 `{"error": "No se puede eliminar un documento generado por el sistema; regénerelo desde Editar parámetros."}`. They are filtered out of the user-attachments list, so the trash icon is not rendered for them.
- **Coverage:** ✅ Covered (base flow); 🟡 NDA-checkbox branch + delete-blocked branch not yet asserted
- **E2E Spec:** `e2e/admin/admin-diagnostic-email-documents.spec.js`

---

### FLOW: `admin-proposal-diagnostic-templates`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` → "Documentos & Plantillas" tab
- **Description:** Admin accesses 3 static markdown diagnostic templates (Diagnóstico de Aplicación, Diagnóstico Técnico, Anexo — Dimensionamiento) from the proposal edit page. Tab is visible when `proposal.status ∈ {sent, viewed, negotiating, accepted, rejected}` — the same condition as the Correos tab. Each template card shows the title, filename, and last-modified date. Three actions are available per card: **Copiar contenido** (fetches `GET /api/diagnostic-templates/:slug/` and writes to clipboard via `navigator.clipboard.writeText`; shows "¡Copiado!" feedback for 2 s; per-slug response cached in component `ref` to avoid duplicate requests), **Descargar .md** (Blob + temporary `<a download>` link click), and **Vista previa** (toggles an inline `<pre>` block with raw markdown).
- **Steps:**
  1. Admin opens a proposal in `sent` or later status via `/panel/proposals/:id/edit`.
  2. Admin clicks the "Documentos & Plantillas" tab.
  3. Template list fetches `GET /api/diagnostic-templates/` → 3 cards render.
  4. Admin clicks "Copiar contenido" on a card → detail fetch → clipboard write → "¡Copiado!" appears.
  5. Admin clicks "Descargar .md" → Blob download triggers.
  6. Admin clicks "Vista previa" → inline `<pre>` block expands; "Ocultar" collapses it.
- **Branches:**
  - [Tab hidden] When `proposal.status === 'draft'`, the tab is not rendered.
  - [Proposal documents sub-section] `ProposalDocumentsTab` (contract, generated PDFs) is only shown within this tab for `negotiating|accepted|rejected` — not for `sent|viewed`.
- **API:** `GET /api/diagnostic-templates/` (list), `GET /api/diagnostic-templates/:slug/` (detail + content_markdown)
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-diagnostic-templates.spec.js`
- **Unit Tests:** `frontend/test/components/ProposalDiagnosticTemplatesSection.test.js`
- **Backend Tests:** `backend/content/tests/views/test_diagnostic_template_views.py`

---

### FLOW: `admin-diagnostic-markdown-attachment`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` → Correos tab
- **Description:** When a diagnostic is in `negotiating` status, a "Crear documento desde markdown" button appears in the Correos tab of the diagnostic edit page. Admin uses it to compose a custom branded PDF (e.g., expanded scope, technical annex, pricing supplement) and attach it to the email composer without uploading a pre-built file.
- **Steps:**
  1. Admin opens a diagnostic in `negotiating` status via `/panel/diagnostics/:id/edit`.
  2. Admin clicks the "Correos" tab.
  3. "Crear documento desde markdown" button is visible.
  4. Admin clicks the button → `MarkdownAttachmentModal` opens.
  5. [Optional] Admin clicks one of the three **Plantillas base** buttons (Diagnóstico de Aplicación / Diagnóstico Técnico / Anexo) → `GET /api/diagnostic-templates/:slug/` fetches the template markdown and writes it to the clipboard; button shows "¡Copiado!" for 2 s. Subsequent clicks reuse an in-memory cache.
  6. Admin fills in the **Título** (text input) and **Contenido en Markdown** (textarea).
  7. Admin optionally unchecks one or more cover toggles (Portada / Subportada / Contraportada).
  8. Admin clicks "Vista previa" → `POST /api/diagnostics/:id/email/markdown-attachment/` fires (FormData with title, markdown, cover booleans).
  9. Backend generates PDF via `DocumentPdfService.generate_from_markdown()` and returns it inline (`Content-Disposition: inline`).
  10. Axios fetches the response as a Blob → `URL.createObjectURL` → `<iframe>` renders the preview.
  11. Admin clicks "Adjuntar" → Blob is converted to a `File` object, emitted via `@attach` → appended to the email composer's attachment list.
  12. Success toast "Adjunto «title.pdf» agregado al correo." appears.
  13. Modal closes automatically.
- **Branches:**
  - [Button absent] When `diagnostic.status !== 'negotiating'`, the button is not rendered.
  - [Preview disabled] "Vista previa" button stays disabled until both title and markdown are non-empty.
  - [Cache reuse] If admin generates a preview, changes nothing, and clicks "Adjuntar", a second POST is skipped — the previously fetched Blob is reused (tracked via `previewSnapshot` vs `currentSnapshot` comparison).
  - [Template fetch error] If `GET /api/diagnostic-templates/:slug/` fails, `error.value` shows "No se pudo copiar la plantilla." and the button re-enables.
- **API:** `POST /api/diagnostics/:id/email/markdown-attachment/`, `GET /api/diagnostic-templates/:slug/`
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-markdown-attachment.spec.js`
- **Unit Tests:** `frontend/test/components/MarkdownAttachmentModal.test.js`
- **Backend Tests:** `backend/content/tests/views/test_diagnostic_email_markdown_attachment.py`

---

### FLOW: `diagnostic-public-view`

- **Module:** diagnostic
- **Role:** guest (via UUID link in email)
- **Priority:** P1
- **Routes:** `/diagnostic/:uuid`
- **Description:** Client opens the public diagnostic link (no Nuxt global header — `layout: false`) and navigates the 8 JSON-driven section components (Purpose / Radiography / Categories / DeliveryStructure / ExecutiveSummary / Cost / Timeline / Scope). Navigation is via a floating sidebar index (`DiagnosticIndex.vue`) — hamburger toggle top-left, panel slides in with numbered badges and visited checkmarks. Server-side filtering returns only sections whose `visibility ∈ {phase, both}` where `phase = 'final' if final_sent_at else 'initial'`. Per-section dwell time is recorded via `DiagnosticViewEvent` + `DiagnosticSectionView`; the final row is flushed via `navigator.sendBeacon` on tab unload.
- **Steps:**
  1. Client navigates to `/diagnostic/:uuid` (no auth required).
  2. Page fetches GET `/api/diagnostics/public/:uuid/` (auto-increments `view_count`) and generates a client-side `session_id`.
  3. POST `/track/` with `session_id` creates a `DiagnosticViewEvent`.
  4. [Branch: SENT + no `final_sent_at`] — Only `initial`/`both` sections are returned by the API and appear in the sidebar index.
  5. [Branch: SENT + `final_sent_at`] — Sections with `final` visibility (e.g. `executive_summary`) also appear; footer shows accept/reject buttons.
  6. Client opens the sidebar (hamburger button) and clicks a section → sidebar closes, section changes, POST `/track-section/` fires with elapsed seconds.
  7. Client clicks "Aceptar propuesta" → POST `/api/diagnostics/public/:uuid/respond/` with `decision: 'accept'`.
  8. Status transitions to `accepted`; acceptance footer replaces the CTA.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/diagnostic-public-view.spec.js` + `e2e/admin/admin-diagnostic-sections.spec.js` (initial-phase visibility filter)

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
| `public-about-us` | public | guest | P3 | 🗄️ Archived | — (page removed from navigation) |
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
| `admin-proposal-client-autocomplete` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-client-autocomplete.spec.js` |
| `admin-proposal-client-no-email` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-client-autocomplete.spec.js` |
| `admin-proposal-edit` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-edit.spec.js` |
| `admin-proposal-slug-edit` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-slug-edit.spec.js` |
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
| `admin-client-create-standalone` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-mini-crm-clients.spec.js` |
| `admin-client-delete-orphan` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-mini-crm-clients.spec.js` |
| `admin-client-delete-protected` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-mini-crm-clients.spec.js` |
| `admin-proposal-send` | admin | admin | P1 | 🟡 Partial (email_intro editing, PDF attachment, failure-feedback toast not asserted) | `e2e/admin/admin-proposal-send.spec.js` |
| `admin-proposal-multi-send` | admin | admin | P1 | ❌ Missing | `e2e/admin/admin-proposal-multi-send.spec.js` |
| `admin-proposal-resend` | admin | admin | P2 | ❌ Missing | `e2e/admin/admin-proposal-resend.spec.js` |
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
| `proposal-value-added-modules` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-value-added-modules.spec.js` |
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
| `proposal-calculator-timeline` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-calculator-timeline.spec.js` |
| `proposal-discount-multi-section` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-discount-multi-section.spec.js` |
| `proposal-onboarding-mobile-swipe` | proposal | guest | P3 | ✅ Covered | `e2e/proposal/proposal-onboarding-mobile-swipe.spec.js` |
| `proposal-og-meta-personalized` | proposal | guest | P3 | ✅ Covered | `e2e/proposal/proposal-og-meta-personalized.spec.js` |
| `admin-proposal-dashboard-auto-refresh` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-proposal-dashboard-auto-refresh.spec.js` |
| `proposal-summary-kpis` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-summary-kpis.spec.js` |
| `admin-proposal-log-activity` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-log-activity.spec.js` |
| `proposal-calculator-new-modules` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-calculator-new-modules.spec.js` |
| `admin-proposal-inline-status-change` | admin | admin | P2 | 🟡 Partial (draft→sent dispatch + email_delivery toast not asserted) | `e2e/admin/admin-proposal-inline-status.spec.js` |
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
| `admin-document-pdf-download` | admin | admin | P2 | ⬜ Missing | — (spec not yet written) |
| `admin-document-move-folder` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-document-move-folder.spec.js` |
| `admin-task-deadline-notification` | admin | system | P2 | ⬜ Backend-only | N/A |
| `admin-admin-management` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-admin-management.spec.js` |
| `admin-email-deliverability` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-email-deliverability.spec.js` |
| `admin-view-map` | admin | admin | P4 | ✅ Covered | `e2e/admin/admin-view-map.spec.js` |
| `admin-send-branded-email` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-email.spec.js` |
| `admin-send-proposal-email` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-email.spec.js` |
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
| `proposal-investment-calculator` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-investment-calculator.spec.js` |
| `admin-proposal-actions-modal` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-actions-modal.spec.js` |
| `proposal-comment-from-closing` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-comment-flow.spec.js` |
| `proposal-rejection-smart-recovery` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-rejection-recovery.spec.js` |
| `proposal-functional-requirements-modal` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-requirements-modal.spec.js` |
| `platform-access-view` | platform | platform-admin | P2 | ✅ Covered | `e2e/platform/platform-access.spec.js` |

### Summary

- **Total flows:** 142
- **P1 (Critical):** 29
- **P2 (High):** 91
- **P3 (Medium):** 19
- **P4 (Nice-to-have):** 1
- **Covered (full):** 130 (92%)
- **Backend-only:** 10 (7%) — system-triggered alerts and automation covered by backend unit tests
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

### 8.12 Quick Access

#### FLOW: `platform-access-view`

- **Module:** platform
- **Role:** platform-admin
- **Priority:** P2
- **Routes:** `/platform/access`
- **API:** `GET /api/accounts/projects/access/`
- **Description:** Admin-only quick-access hub with a searchable grid of project cards. Each card shows the project name, client, and status badge, plus four clickable URL rows (production, staging, Django admin, repository) and a credential block with copy and reveal controls.
- **Steps:**
  1. Admin navigates to `/platform/access` (via "Accesos" item in the Administración sidebar group).
  2. `GET /api/accounts/projects/access/` fetches the admin-only list with decrypted credentials.
  3. Project cards render in a responsive grid.
  4. Each card shows up to four URL rows; rows with no URL render a dash.
  5. Admin clicks a URL row → external link opens in a new tab.
  6. Admin clicks "Copiar" on a credential field → value copied to clipboard → flash feedback appears.
  7. Admin clicks "Revelar" → password unmasks; "Ocultar" re-masks it.
  8. Admin types in the search input → cards filter by project name, client, or URL substring.
  9. Admin clicks "Actualizar" → list re-fetches from API.
- **Branches:**
  - [Branch A — No projects] API returns empty list → "Todavía no hay proyectos con accesos configurados." empty state.
  - [Branch B — Search no match] Search term matches no project → "Ningún proyecto coincide con esa búsqueda."
  - [Branch C — Access guard] Client role navigates to page → middleware redirects to `/platform/dashboard`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/platform/platform-access.spec.js`

### 8.13 Platform Coverage Index

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
| `platform-access-view` | platform | platform-admin | P2 | ✅ Covered | `e2e/platform/platform-access.spec.js` |
| `platform-admin-project-create` | platform | platform-admin | P3 | ✅ Covered | `e2e/platform/platform-project-create.spec.js` |
| `platform-kanban-card-comments` | platform | platform-admin/client | P3 | ✅ Covered | `e2e/platform/platform-kanban-comments.spec.js` |

### Platform Coverage Summary

- **Total platform flows:** 27
- **P1 (Critical):** 5
- **P2 (High):** 20
- **P3 (Medium):** 2
- **Covered:** 27 (100%)
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

#### FLOW: `admin-document-folders`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents`
- **Description:** Organize admin documents with a folder sidebar and tag filter chips. Admin selects a folder to filter the list, toggles tag chips for multi-tag OR filtering, opens the FolderManagerModal to create/rename/delete folders, and opens the TagManagerModal to create/rename/delete tags with color coding.
- **Steps:**
  1. Admin loads `/panel/documents` — left sidebar renders all folders; tag chips appear above the table.
  2. Admin clicks a folder entry (e.g., "Cuentas de cobro") → list refreshes with `?folder=<id>`.
  3. Admin clicks "Sin carpeta" → list refreshes with `?folder=none`.
  4. Admin clicks "Todos" → list refreshes without folder param.
  5. Admin clicks a tag chip → list refreshes with `?tags=<id>` (OR logic; multiple chips additive).
  6. Admin clicks "Limpiar" → tag filter cleared, list refreshes.
  7. Admin clicks "Gestionar" / "Gestionar etiquetas" → modal opens for inline CRUD.
  8. Admin creates, renames, or deletes a folder/tag → modal emits `@changed` → document list refreshes.
- **Branches:**
  - [Branch A — Empty folders] No folders yet → "Sin carpeta" and "Todos" entries only; "Crear la primera →" prompt for tags.
  - [Branch B — Create folder] Admin fills name + submits in FolderManagerModal → folder added to sidebar.
  - [Branch C — Delete folder with SET_NULL] Deleting a folder leaves documents with `folder = null` (not deleted).
  - [Branch D — Assign on create] Creating a document from `?folder=<id>` pre-selects that folder.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-document-folders.spec.js`

#### FLOW: `admin-document-pdf-download`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents/:id/edit`
- **API:** `GET /api/content/documents/<id>/pdf/`
- **Description:** Admin downloads a Document entity as a branded PDF from the document edit page. The "Descargar PDF" button triggers `documentStore.downloadPdf()` which calls the backend generation endpoint.
- **Steps:**
  1. Admin opens `/panel/documents/:id/edit`.
  2. Admin clicks "Descargar PDF".
  3. `isDownloading` state activates (button shows "Descargando...").
  4. Backend generates the PDF and returns a blob.
  5. Browser downloads the file named after the document title.
- **Branches:**
  - [Branch A — Generation in progress] If PDF backend is still being developed, the endpoint may return an error; UI should handle gracefully.
- **Coverage:** ⬜ Missing
- **E2E Spec:** *(not yet written — Document PDF generation feature is in progress)*

#### FLOW: `admin-document-move-folder`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/documents`
- **API:** `PATCH /api/content/documents/<id>/update/`
- **Description:** Admin moves a document to a different folder (or removes it from any folder) via MoveFolderModal from the documents list page. The modal shows all folders from `document-folders/`; clicking a folder PATCHes the document with `folder_id`; "Sin carpeta" sets `folder_id: null`.
- **Steps:**
  1. Admin loads `/panel/documents`.
  2. Admin clicks "Mover a carpeta" button on a document row → `MoveFolderModal` opens.
  3. Modal renders "Sin carpeta" option and all available folder buttons.
  4. Admin clicks a target folder → `documentStore.updateDocument(id, { folder_id })` is called.
  5. On success, modal closes and document list + folder counts refresh.
- **Branches:**
  - [Branch A — Move to folder] Admin selects a named folder → PATCH with `folder_id: <id>`.
  - [Branch B — Remove from folder] Admin clicks "Sin carpeta" → PATCH with `folder_id: null`.
  - [Branch C — Same folder] Clicking the current folder → no PATCH, modal closes.
  - [Branch D — Error] PATCH fails → modal shows "No se pudo mover el documento." error message.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-document-move-folder.spec.js`

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
| `admin-document-folders` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-document-folders.spec.js` |
| `admin-document-pdf-download` | admin | admin | P2 | ⬜ Missing | — (spec not yet written) |
| `admin-document-move-folder` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-document-move-folder.spec.js` |
| `admin-task-deadline-notification` | admin | system | P2 | ⬜ Backend-only | N/A |
| `admin-diagnostic-create` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-diagnostic-create.spec.js` |
| `admin-diagnostic-send-initial` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-diagnostic-send.spec.js` |
| `admin-diagnostic-send-final` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-diagnostic-send.spec.js` |
| `admin-diagnostic-email` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-email-documents.spec.js` |
| `admin-diagnostic-documents` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-email-documents.spec.js` |
| `admin-diagnostic-sections` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-diagnostic-sections.spec.js` |
| `admin-diagnostic-activity` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-sections.spec.js` |
| `admin-diagnostic-analytics` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-analytics.spec.js` |
| `admin-diagnostic-engagement-score` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-analytics.spec.js` |
| `admin-diagnostic-prompt` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-prompt.spec.js` |
| `diagnostic-public-view` | diagnostic | guest | P1 | ✅ Covered | `e2e/public/diagnostic-public-view.spec.js` + `e2e/admin/admin-diagnostic-sections.spec.js` |
| `admin-admin-management` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-admin-management.spec.js` |
| `admin-email-deliverability` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-email-deliverability.spec.js` |
| `admin-send-branded-email` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-email.spec.js` |
| `admin-send-proposal-email` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-email.spec.js` |
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
- **Coverage:** ⚠️ Superseded — replaced by `admin-proposal-attach-from-documents` (Apr 22, 2026). The "Enviar documentos" section was removed from the Documents tab; document attachment now happens in the Correos tab via `doc_refs`.
- **E2E Spec:** *(spec deleted; see `e2e/admin/admin-proposal-attach-from-documents.spec.js`)*

### 10.3 Composed Email Flows

#### FLOW: `admin-send-branded-email`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Description:** Admin sends a branded email from the proposal edit page "Correos" tab.
- **Visible when:** Proposal status in `negotiating`, `accepted`, `rejected`
- **Steps:**
  1. Navigate to `/panel/proposals/:id/edit`
  2. Click the "Correos" tab
  3. Fill composer: recipient, subject, greeting, draggable sections, footer
  4. Optionally attach files (PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, JPEG; max 15 MB)
  5. Preview email in "Vista previa" sub-tab
  6. Click "Enviar correo" → `POST /api/proposals/:id/branded-email/send/`
  7. Verify history updates with new entry
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-email.spec.js`

#### FLOW: `admin-send-proposal-email`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Description:** Admin sends a proposal email from the proposal edit page "Enviar correo" tab. Each send is logged as `ProposalChangeLog` activity.
- **Visible when:** Proposal status in `sent`, `viewed`, `negotiating`, `accepted`, `rejected`
- **Steps:**
  1. Navigate to `/panel/proposals/:id/edit`
  2. Click the "Enviar correo" tab
  3. Fill same composer UI as branded email
  4. Click "Enviar correo" → `POST /api/proposals/:id/proposal-email/send/`
  5. Verify `ProposalChangeLog` entry created with `change_type=email_sent`
  6. Verify `last_activity_at` updated on the proposal
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-email.spec.js`

#### FLOW: `admin-standalone-email-composer`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/emails`
- **Description:** Admin composes and sends branded emails from the standalone Emails page (not tied to any proposal). Draggable sections, file attachments, branded preview, and paginated email history. Uses dedicated standalone endpoints distinct from proposal-scoped email flows.
- **Steps:**
  1. Admin navigates to `/panel/emails` via sidebar navigation.
  2. Composer loads with defaults from `GET /api/emails/defaults/`.
  3. Admin fills recipient email, subject, greeting, draggable body sections, and footer.
  4. Optionally attaches files.
  5. Admin previews email in branded template preview tab.
  6. Admin clicks "Enviar" → `POST /api/emails/send/`.
  7. Success message renders; email history updates.
  8. Admin views paginated email history from `GET /api/emails/history/`.
- **Branches:**
  - [Branch A — Empty recipient] Send button disabled when recipient email is empty.
  - [Branch B — File limits] Attachment validation enforces type and size limits.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-standalone-email-composer.spec.js`

---

### 10.4 New Flows Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-proposal-contract-generate` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-contract-generate.spec.js` |
| `admin-proposal-contract-edit` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-contract-edit.spec.js` |
| `admin-proposal-contract-download` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-contract-download.spec.js` |
| `admin-proposal-documents-manage` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-documents-manage.spec.js` |
| `admin-proposal-documents-send` | admin | admin | P1 | ⚠️ Superseded | replaced by `admin-proposal-attach-from-documents` (Apr 22, 2026) |
| `admin-send-branded-email` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-email.spec.js` |
| `admin-send-proposal-email` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-email.spec.js` |
| `admin-standalone-email-composer` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-standalone-email-composer.spec.js` |

---

## 11. New Feature Flows (v2.12.0)

> Flows registered during the v2.12.0 audit for the LinkedIn integration (commit `e070c330`). LinkedIn publishing is available on the blog post edit page and requires OAuth connection.

### 11.1 Admin Blog LinkedIn Integration

#### FLOW: `admin-blog-linkedin-connect`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/blog/:id/edit` (LinkedIn fieldset)
- **API:** `GET /api/linkedin/auth-url/`, `POST /api/linkedin/callback/`, `GET /api/linkedin/status/`
- **Frontend pages involved:** `/panel/blog/:id/edit`, `/auth/linkedin/callback`
- **Description:** Admin connects the LinkedIn account to the panel via OAuth 2.0 authorization code flow. The OAuth popup opens, the user authenticates with LinkedIn, and the callback page exchanges the code for encrypted tokens stored server-side.
- **Steps:**
  1. Admin opens `/panel/blog/:id/edit`.
  2. LinkedIn section is shown in the form. Status loads from `GET /api/linkedin/status/`.
  3. Connection status is **disconnected** → "LinkedIn no conectado." label and "Conectar LinkedIn" button are visible.
  4. Admin clicks "Conectar LinkedIn" → `GET /api/linkedin/auth-url/` → popup window opens at the LinkedIn authorization URL.
  5. User authenticates with LinkedIn in the popup.
  6. LinkedIn redirects to `/auth/linkedin/callback?code=...&state=...`.
  7. Callback page exchanges code via `POST /api/linkedin/callback/`.
  8. On success: popup shows "LinkedIn conectado correctamente" and "Puedes cerrar esta ventana." with green checkmark.
  9. Popup sends `postMessage({ type: 'linkedin-connected', data: connection })` to opener window.
  10. Opener window updates `linkedinStatus` → "Conectar LinkedIn" button replaced with profile name and language selector.
- **Branches:**
  - [Branch A — OAuth error] LinkedIn returns `?error=access_denied` → popup shows error message in red.
  - [Branch B — No code] Callback page receives no `code` param → error "No se recibió código de autorización."
  - [Branch C — API error] Backend exchange fails → error displayed in popup.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-linkedin.spec.js`

#### FLOW: `admin-blog-linkedin-publish`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/blog/:id/edit` (LinkedIn fieldset)
- **API:** `POST /api/blog/admin/:post_id/publish-linkedin/`
- **Description:** Admin publishes a blog post summary to LinkedIn directly from the edit page. Requires LinkedIn to be connected and a summary text filled for the selected language.
- **Steps:**
  1. Admin opens `/panel/blog/:id/edit`.
  2. LinkedIn status loads — account is **connected**: green dot + profile name shown.
  3. Admin fills `linkedin_summary_es` (≤1300 chars) or `linkedin_summary_en` textarea with the post summary.
  4. Admin selects language from dropdown ("Publicar en Español" / "Publish in English").
  5. Admin clicks "Publicar en LinkedIn" button (disabled if summary is empty or publish in progress).
  6. API call to `POST /api/blog/admin/:id/publish-linkedin/` with `{ lang }`.
  7. Success: success message "Publicado en LinkedIn correctamente." renders and auto-hides after 5s.
  8. "Última publicación:" timestamp renders with date of last publish.
- **Branches:**
  - [Branch A — API error] Publish fails → error message renders in red.
  - [Branch B — Token expired] Backend auto-refreshes token; if refresh token also expired, error is returned.
  - [Branch C — Empty summary] "Publicar en LinkedIn" button is disabled until summary is filled.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-linkedin.spec.js`

### 11.2 New Flows Coverage Index

| Flow ID | Module | Role | Priority | Status | Suggested Spec |
|---------|--------|------|----------|--------|----------------|
| `admin-blog-linkedin-connect` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-blog-linkedin.spec.js` |
| `admin-blog-linkedin-publish` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-blog-linkedin.spec.js` |
| `admin-proposal-advanced-filters` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-advanced-filters.spec.js` |
| `public-privacy-policy` | public | guest | P4 | ✅ Covered | `e2e/public/public-privacy-policy.spec.js` |
| `public-terms-conditions` | public | guest | P4 | ✅ Covered | `e2e/public/public-terms-conditions.spec.js` |
| `admin-proposal-project-schedule` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-project-schedule.spec.js` |

---

## 12. New Feature Flows (v2.15.0)

> Flows registered during the v2.15.0 audit for the Real Client Entity feature (shipped 2026-04-09). Covers the two client-write flows discovered during the e2e-user-flows-check audit that were not yet registered: editing an existing client profile with propagation, and re-assigning the client on an existing proposal.

### 12.1 Admin Client Profile Update

No active browser flow is registered for client profile editing at this time.

- **Current panel surface:** `/panel/clients/` supports list, filter, expand, standalone create, and orphan delete.
- **Missing UI route:** `/panel/clients/:id/edit` is not implemented in `frontend/pages/panel/clients/` as of 2026-04-10.
- **Backend capability:** `PATCH /api/proposals/client-profiles/:id/` exists and is covered by backend tests, but there is no current panel route that exposes it as a user journey.
- **E2E expectation:** none until a real panel edit surface exists.

### 12.2 Admin Proposal Re-assign Client

#### FLOW: `admin-proposal-update-client`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit`
- **API:** `PATCH /api/proposals/:id/` with `client_id` (new client)
- **Frontend pages involved:** `/panel/proposals/:id/edit`
- **Description:** Admin changes the client linked to an existing draft or active proposal. Uses the same `ClientAutocomplete.vue` component as the create flow. On save, the backend re-assigns `BusinessProposal.client` FK and syncs snapshot fields to the newly selected client's data.
- **Steps:**
  1. Admin opens `/panel/proposals/:id/edit`.
  2. Client autocomplete input shows the current client name.
  3. Admin clears the input and types a different client name to search.
  4. Dropdown shows matching results; admin selects a different client.
  5. Snapshot fields (`client_name`, `client_email`, `client_phone`) update immediately in the form.
  6. Admin clicks "Guardar propuesta".
  7. `PATCH /api/proposals/:id/` is sent with the new `client_id`.
  8. Backend calls `proposal_client_service.sync_snapshot(proposal)` after FK update.
  9. Success toast renders; snapshot fields now reflect the new client.
- **Branches:**
  - [Branch A — New client has placeholder email] Autocomplete badge shows "Sin email real"; proposal automations are paused for this client until a real email is provided.
  - [Branch B — Client cleared without selection] Autocomplete input left empty → proposal save fails validation (client is required for existing proposals).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-update-client.spec.js`

### 12.3 New Flows Coverage Index

| Flow ID | Module | Role | Priority | Status | Suggested Spec |
|---------|--------|------|----------|--------|----------------|
| `admin-proposal-update-client` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-update-client.spec.js` |

---

## 13. Audit Alignment Flows (v2.16.0)

> Retro-documented browser flows that were already registered in `frontend/e2e/flow-definitions.json` and tagged in Playwright specs, but did not yet have full headed entries in this markdown map. Also adds the new `/panel/views` admin reference flow introduced during the audit.

### 13.1 Proposal Audit Additions

#### FLOW: `proposal-countdown-realtime`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P3
- **Routes:** `/proposal/:uuid`
- **Description:** When a proposal expires within 48 hours, the countdown switches from day-based copy to a live HH:MM timer that updates on the client without reloading the page.
- **Steps:**
  1. Client opens a proposal whose `expires_at` is within the 48-hour window.
  2. Countdown UI renders a live hours/minutes timer.
  3. Timer updates on the page over time.
  4. Expiration badge and urgency messaging stay in sync with the live countdown.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-countdown-realtime.spec.js`

#### FLOW: `proposal-rejection-optional-reason`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The rejection path keeps the reason optional while nudging the client to provide context before submitting a negative response.
- **Steps:**
  1. Client opens the rejection modal from the closing section.
  2. Helper copy explains that feedback is optional but useful.
  3. Client submits rejection without choosing a reason.
  4. Proposal is rejected successfully and the UI moves to the rejection confirmation state.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-rejection-optional.spec.js`

#### FLOW: `proposal-calculator-timeline`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** Investment calculator changes the estimated delivery timeline dynamically as optional modules are toggled on or off.
- **Steps:**
  1. Client opens the investment calculator modal.
  2. Baseline weeks are visible before any changes.
  3. Client selects or removes priced modules.
  4. Estimated timeline updates immediately to reflect the module mix.
  5. Confirming the selection preserves the new timeline in the closing state.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-calculator-timeline.spec.js`

#### FLOW: `proposal-calculator-micro-feedback`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Calculator toggles show transient micro-feedback badges such as positive or negative price deltas when the client adds or removes priced modules.
- **Steps:**
  1. Client opens the investment calculator modal.
  2. Client toggles a module with a price impact.
  3. A transient feedback badge appears near the interaction showing the delta.
  4. Badge fades away while totals remain updated.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-calculator-micro-feedback.spec.js`

#### FLOW: `proposal-payment-plan-closing`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Payment milestones are summarized near the accept CTA in the closing section so the client can review the plan without reopening the investment section.
- **Steps:**
  1. Client navigates to the proposal closing section.
  2. Closing card renders payment milestones and labels.
  3. Payment plan stays visible next to the primary accept action.
  4. The displayed plan matches the investment data configured for the proposal.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-payment-plan-closing.spec.js`

#### FLOW: `proposal-post-acceptance-welcome`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** After acceptance, the client sees a welcome-kit style success state with onboarding guidance, downloadable material, and a direct PM communication CTA.
- **Steps:**
  1. Client accepts the proposal from the closing flow.
  2. Proposal switches to the post-acceptance state.
  3. Welcome content renders with next steps and onboarding guidance.
  4. PDF download and PM WhatsApp contact actions are available.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-post-acceptance-welcome.spec.js`

#### FLOW: `proposal-structured-negotiation`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Negotiation modal provides structured reasons and tabs so the client can request changes with more specific context than a free-text note alone.
- **Steps:**
  1. Client opens the negotiation modal from the closing section.
  2. Modal renders structured reason options and adjust/comment tab states.
  3. Client selects reasons and optionally adds custom context.
  4. Client submits the negotiation request and sees success feedback.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-structured-negotiation.spec.js`

#### FLOW: `proposal-conditional-acceptance`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Client accepts the proposal while attaching an optional “Acepto, pero…” condition note that is persisted with the response.
- **Steps:**
  1. Client opens the acceptance flow from the closing section.
  2. Client adds an optional condition note.
  3. Client confirms acceptance.
  4. Proposal moves to the accepted state while retaining the condition note.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-conditional-acceptance.spec.js`

### 13.2 Admin Audit Additions

#### FLOW: `admin-dashboard-pipeline-value`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/`
- **Description:** Dashboard shows a dedicated pipeline-value KPI card summarizing the total investment currently active in the sales pipeline.
- **Steps:**
  1. Admin opens the panel dashboard.
  2. Proposal dashboard data loads from `GET /api/proposals/dashboard/`.
  3. Pipeline KPI card renders the total active value and proposal count.
  4. Card is hidden when the backend returns no pipeline value.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-dashboard.spec.js`

#### FLOW: `admin-proposal-create-and-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/create`
- **Description:** After creating a proposal with valid client contact data, the admin can send it immediately from the post-create interstitial without first navigating to the edit page.
- **Steps:**
  1. Admin creates a proposal from the create screen.
  2. Post-create modal appears with next actions.
  3. Admin clicks the send action from the modal.
  4. Proposal send endpoint is called and the new proposal moves to the sent state.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-create.spec.js`

#### FLOW: `admin-proposal-create-preview`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/create`
- **Description:** Post-create interstitial lets the admin preview, edit, or send the newly created proposal before leaving the creation context.
- **Steps:**
  1. Admin completes proposal creation.
  2. Confirmation modal summarizes the created proposal.
  3. Modal exposes preview and edit actions for the new record.
  4. Admin can move to the edit page directly from the interstitial.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-create.spec.js`

#### FLOW: `admin-discount-analysis-enhanced`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/proposals/`
- **Description:** Discount analysis card shows richer context including sample sizes, average discount percentages, and warnings when discount performance differs from the baseline.
- **Steps:**
  1. Admin opens the proposals page dashboard.
  2. Discount analysis card loads from dashboard metrics.
  3. Card renders sample size and average discount context.
  4. Delta warning messaging appears when discount performance trends negatively.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-discount-analysis.spec.js`

#### FLOW: `admin-proposal-inline-status-change`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Proposal status can be updated directly from the proposals table via an inline dropdown without opening the edit page. The `draft → sent` transition is delegated to `ProposalService.send_proposal`, so it dispatches the client email and schedules Huey reminders (matching the dedicated "Enviar al Cliente" button — defense-in-depth so the dropdown can never silently move a proposal to `sent` without notifying the client). Response includes `email_delivery`; the panel toast surfaces failures with the reason.
- **Steps:**
  1. Admin opens the proposals list.
  2. Row-level status dropdown is visible for editable proposals.
  3. Admin selects a new status from the inline selector.
  4. `PATCH /api/proposals/:id/update-status/` is called with `{status}`.
  5. For `draft → sent`: backend delegates to `ProposalService.send_proposal` (sends email, schedules reminders) and returns `email_delivery`. For other transitions: legacy save + `ProposalChangeLog`; `email_delivery` omitted.
  6. Row refreshes; toast shows "Estado actualizado correctamente" on success, or surfaces `email_delivery` failure when applicable.
- **Coverage:** 🟡 Partial — generic dropdown PATCH is covered; **the `draft → sent` dispatch (delegating to `send_proposal`) and the email_delivery failure toast are not asserted in E2E**.
- **E2E Spec:** `e2e/admin/admin-proposal-inline-status.spec.js` (extend with: assert `draft → sent` invokes `POST /send/` semantics — i.e. response carries `email_delivery` — and that a mocked `ok=false` triggers the error toast).

#### FLOW: `admin-proposal-scorecard`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit`
- **Description:** Edit view surfaces a pre-send scorecard with blockers so the admin can see whether a proposal is ready to be sent.
- **Steps:**
  1. Admin opens a proposal edit page.
  2. Scorecard endpoint loads readiness data for that proposal.
  3. Score and blocker state render in the UI.
  4. Blocking issues prevent sending until the missing data is fixed.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-scorecard.spec.js`

#### FLOW: `admin-proposal-section-completeness`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/proposals/:id/edit`
- **Description:** Edit page shows a section-completeness indicator summarizing how many enabled sections currently have content.
- **Steps:**
  1. Admin opens a proposal edit page.
  2. Completeness summary loads from current section data.
  3. Progress UI shows the percentage of enabled sections with content.
  4. Indicator updates as section content changes.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-section-completeness.spec.js`

#### FLOW: `admin-proposal-zombie-segment`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Proposals dashboard highlights stale “zombie” proposals in a dedicated collapsible segment so the sales owner can triage cold opportunities quickly.
- **Steps:**
  1. Admin opens the proposals page.
  2. Zombie segment renders when stale draft/sent proposals are present.
  3. Segment shows the relevant proposals and alert styling.
  4. Admin can expand or collapse the section while reviewing the stale pipeline.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-zombie-segment.spec.js`

#### FLOW: `admin-view-map`

- **Module:** admin
- **Role:** admin
- **Priority:** P4
- **Routes:** `/panel/views`
- **Description:** Admin opens the panel route inventory page, searches grouped browser views by name/URL/file, and copies route references for QA or support communication.
- **Steps:**
  1. Admin opens `/panel/views` from the Reference section in the panel sidebar.
  2. Grouped route catalog renders with section totals and a proposal reference guide.
  3. Admin searches for a route, view name, or file path to narrow the catalog.
  4. Admin clicks the copy button on a view row and sees copied feedback.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-view-map.spec.js`

#### FLOW: `admin-kanban-tasks`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/tasks` (alias `/panel/tareas` redirects here)
- **Description:** Internal Kanban task board for the admin team. Admin creates, edits, moves, and deletes tasks across four columns (Todo, In Progress, Blocked, Done). Tasks have priority labels (low/medium/high), optional assignee, and optional due date shown in red when overdue.
- **Steps:**
  1. Admin navigates to `/panel/tasks` from the "Tareas → Kanban" sidebar entry.
  2. Board renders four columns loaded from `GET /api/content/tasks/`.
  3. Admin clicks "+ Nueva Tarea" → `TaskFormModal` opens.
  4. Admin fills title, priority, optional assignee, due date → submits → task appears in the "Todo" column.
  5. Admin clicks a task card → modal reopens for editing; saves → card updates in place.
  6. Admin drags a task card to another column → `PATCH /api/content/tasks/<id>/update/` fires with new status; board updates.
  7. Admin deletes a task via the modal → `DELETE /api/content/tasks/<id>/delete/` → card removed from column.
- **Branches:**
  - [Branch A — Overdue] Tasks with a past `due_date` render the date in red.
  - [Branch B — Empty column] Columns with no tasks show a ghost-style drop target.
  - [Branch C — Reorder] Dragging a task within the same column calls `PATCH tasks/<id>/reorder/` to renumber positions.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-tasks-kanban.spec.js`

#### FLOW: `admin-task-deadline-notification`

- **Module:** admin
- **Role:** system (no browser interaction)
- **Priority:** P2
- **Routes:** N/A — backend-only
- **API:** Huey periodic task; `PATCH /api/content/tasks/<id>/update/` (internal); Django email backend
- **Description:** Automated email notifications sent to task assignees at 40%, 70%, and 100% of deadline elapsed, and again for overdue tasks. Notification state is tracked via `notified_40`, `notified_70`, `notified_100`, `last_overdue_notified_at` fields added in migration `0089_task_notification_fields.py`. The Huey task runs periodically and skips tasks that have already been notified at each threshold.
- **Steps:**
  1. Huey scheduler triggers the deadline-notification task.
  2. Task queries all `Task` records with a `due_date` and an assignee email.
  3. For each task, time-to-deadline % is computed; if threshold crossed and not yet notified, an email is sent.
  4. The corresponding `notified_*` field is set to `True` to prevent duplicate notifications.
  5. Overdue tasks send a daily reminder until `last_overdue_notified_at` is today.
- **Coverage:** ⬜ Backend-only — no E2E spec needed (expectedSpecs: 0)

### 13.3 Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-dashboard-pipeline-value` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-dashboard.spec.js` |
| `admin-proposal-create-and-send` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-create.spec.js` |
| `admin-proposal-create-preview` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-create.spec.js` |
| `admin-discount-analysis-enhanced` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-discount-analysis.spec.js` |
| `admin-proposal-inline-status-change` | admin | admin | P2 | 🟡 Partial (draft→sent dispatch + email_delivery toast not asserted) | `e2e/admin/admin-proposal-inline-status.spec.js` |
| `admin-proposal-scorecard` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-scorecard.spec.js` |
| `admin-proposal-section-completeness` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-proposal-section-completeness.spec.js` |
| `admin-proposal-zombie-segment` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-zombie-segment.spec.js` |
| `admin-view-map` | admin | admin | P4 | ✅ Covered | `e2e/admin/admin-view-map.spec.js` |
| `admin-kanban-tasks` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-tasks-kanban.spec.js` |
| `admin-task-deadline-notification` | admin | system | P2 | ⬜ Backend-only | N/A |

---

## 14. New Feature Flows (v2.17.0–v2.20.0)

> Flows registered during the v2.17.0–v2.20.0 audit cycles. Covers Document PDF download (in progress), Web App Diagnostics, document move-folder modal, and task deadline notifications.

### 14.1 Document PDF Download

#### FLOW: `admin-document-pdf-download`

*(See Section 9.1 for full flow detail — this section tracks coverage status only.)*

### 14.2 New Flows Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-document-pdf-download` | admin | admin | P2 | ⬜ Missing | — (Document PDF generation in progress) |
| `admin-document-move-folder` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-document-move-folder.spec.js` |
| `admin-task-deadline-notification` | admin | system | P2 | ⬜ Backend-only | N/A |
| `admin-diagnostic-create` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-diagnostic-create.spec.js` |
| `admin-diagnostic-send-initial` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-diagnostic-send.spec.js` |
| `admin-diagnostic-send-final` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-diagnostic-send.spec.js` |
| `admin-diagnostic-email` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-email-documents.spec.js` |
| `admin-diagnostic-documents` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-email-documents.spec.js` |
| `admin-diagnostic-sections` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-diagnostic-sections.spec.js` |
| `admin-diagnostic-activity` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-sections.spec.js` |
| `admin-diagnostic-analytics` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-analytics.spec.js` |
| `admin-diagnostic-engagement-score` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-analytics.spec.js` |
| `admin-diagnostic-prompt` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-prompt.spec.js` |
| `diagnostic-public-view` | diagnostic | guest | P1 | ✅ Covered | `e2e/public/diagnostic-public-view.spec.js` + `e2e/admin/admin-diagnostic-sections.spec.js` |

---

## Section 15 — v2.21.0 Gaps (Task Alerts + Diagnostic Lifecycle)

> Flows registered during the v2.21.0 audit cycle. Covers manual task alert management, diagnostic edit, and diagnostic delete.

### 15.1 Task Alert Management

#### FLOW: `admin-task-alert-management`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-task-alert-management` |
| **Module** | tasks |
| **Role** | admin |
| **Priority** | P1 |
| **Status** | ⬜ Missing spec |

**Steps:**
1. Admin navigates to `/panel/tasks`.
2. Admin clicks a task card to open `TaskFormModal` in edit mode.
3. Admin sees the **Alertas** section below the due-date/assignee row.
4. Admin enters a date in the "Fecha" input and an optional note.
5. Admin clicks **+ Agregar** — alert appears in the list with "Pendiente" badge.
6. Admin clicks the **✕** delete button on an alert — alert is removed from the list.
7. Admin closes the modal.

**Expected outcome:** Alerts persist to backend via POST `tasks/{id}/alerts/create/` and DELETE `tasks/{id}/alerts/{alertId}/delete/`.

---

### 15.2 Diagnostic Edit

#### FLOW: `admin-diagnostic-edit`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-edit` |
| **Module** | diagnostics |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ⬜ Missing spec |

**Steps:**
1. Admin navigates to `/panel/diagnostics`.
2. Admin clicks **Edit** on a diagnostic card.
3. Admin is taken to `/panel/diagnostics/{id}/edit`.
4. Admin modifies one or more fields (title, status, investment amount, etc.).
5. Admin clicks **Guardar** — PATCH sent to `diagnostics/{id}/update/`.
6. Admin sees success feedback; the updated values are reflected in the form.

**Expected outcome:** Diagnostic fields are updated in the backend and reflected in the UI.

---

### 15.3 Diagnostic Delete

#### FLOW: `admin-diagnostic-delete`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-delete` |
| **Module** | diagnostics |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ⬜ Missing spec |

**Steps:**
1. Admin navigates to `/panel/diagnostics`.
2. Admin clicks **Delete** (or trash icon) on a diagnostic card.
3. A confirmation modal appears asking the admin to confirm deletion.
4. Admin confirms — DELETE sent to `diagnostics/{id}/delete/`.
5. The diagnostic is removed from the list.

**Expected outcome:** Diagnostic is deleted in the backend and removed from the list without a page reload.

---

### 15.4 New Flows Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-task-alert-management` | tasks | admin | P1 | ✅ Covered | `e2e/admin/admin-task-alerts.spec.js` |
| `admin-diagnostic-edit` | diagnostics | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-edit-delete.spec.js` |
| `admin-diagnostic-delete` | diagnostics | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-edit-delete.spec.js` |

---

## Section 16 — v2.22.0 Gaps (Diagnostic Acuerdo de Confidencialidad)

> Flows registered during the v2.22.0 audit cycle. Covers the new system-generated Acuerdo de Confidencialidad (NDA) PDF on the diagnostic Documentos tab — mirrors the proposal contract pattern (`admin-proposal-contract-{generate,edit,download}`).

### 16.1 Diagnostic NDA Generate

#### FLOW: `admin-diagnostic-confidentiality-generate`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-confidentiality-generate` |
| **Module** | diagnostics |
| **Role** | admin |
| **Priority** | P1 |
| **Status** | ✅ Covered |
| **Spec** | `e2e/admin/admin-diagnostic-confidentiality.spec.js` |

**Routes:** `/panel/diagnostics/:id/edit` → Documentos tab.

**Description:** Admin generates the Acuerdo de Confidencialidad (NDA) PDF for a diagnostic. The Documents tab opens with a dedicated "Acuerdo de confidencialidad" section above the send/upload sections. When no NDA exists, the section displays "No generado" plus a copy line ("Plantilla colombiana (Ley 1581/2012). Llena los datos del cliente y consultor para generar el PDF.") and a "Generar acuerdo" CTA. Clicking the CTA opens `ConfidentialityParamsModal` with three field groups: Cliente (nombre/NIT/representante legal/email — pre-filled from `diagnostic.client.name` and `.email` when available), Consultor (nombre — default "Project App SAS"; NIT; email — default "team@projectapp.co"), Datos del acuerdo (ciudad — default "Medellín"; día/mes/año; cláusula penal — default "CINCUENTA SALARIOS MÍNIMOS MENSUALES LEGALES VIGENTES (50 SMMLV)"). Submit POSTs trimmed/non-empty fields to `POST /api/diagnostics/:id/confidentiality/params/` (`{confidentiality_params: {...}}`); backend validates via `ConfidentialityParamsSerializer`, persists to `diagnostic.confidentiality_params`, then calls `_generate_and_save_confidentiality_pdf` which loads the default `ConfidentialityTemplate`, substitutes placeholders, renders the branded ProjectApp PDF (esmeralda + Lemon accent, "ACUERDO DE CONFIDENCIALIDAD" title page, two-column EL CLIENTE / EL CONSULTOR signature block), and creates a `DiagnosticAttachment(document_type='confidentiality_agreement', is_generated=True)`. A `DiagnosticChangeLog(UPDATED, field_name='confidentiality_agreement')` row is appended.

**Steps:**
1. Admin navigates to `/panel/diagnostics/:id/edit` and opens the **Documentos** tab.
2. Admin sees the "Acuerdo de confidencialidad" section with "No generado" label and "Generar acuerdo" button.
3. Admin clicks **Generar acuerdo** — `ConfidentialityParamsModal` opens, prefilling client name/email from the diagnostic plus contractor + city + penal clause defaults.
4. Admin fills the cliente fields (nombre, NIT, representante legal) and confirms the others.
5. Admin clicks **Guardar y generar PDF** → POST `/api/diagnostics/:id/confidentiality/params/`.
6. Modal closes; the section now shows "Generado el {fecha}" plus three buttons: **Descargar**, **Borrador**, **Editar parámetros**.
7. The new attachment also appears in the "Enviar documentos al cliente" section as a checkbox "📋 NDA — Acuerdo de Confidencialidad (borrador con marca de agua)".

**Branches:**
- [Empty params] Admin clicks "Generar acuerdo", leaves all fields blank, submits — request succeeds, PDF is generated with all `_______________` placeholders for missing fields (default `Project App SAS` / `Medellín` / 50 SMMLV still apply for contractor and city).
- [Server failure] If `generate_confidentiality_pdf` returns `None`, response is HTTP 500 `{"error": "Parámetros guardados pero no se pudo generar el PDF."}` (params are still saved — admin can retry generate without re-entering data).

**Expected outcome:** A `DiagnosticAttachment` with `document_type='confidentiality_agreement'` and `is_generated=True` exists for the diagnostic, with a downloadable PDF file.

---

### 16.2 Diagnostic NDA Edit Params

#### FLOW: `admin-diagnostic-confidentiality-edit`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-confidentiality-edit` |
| **Module** | diagnostics |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ✅ Covered |

**Routes:** `/panel/diagnostics/:id/edit` → Documentos tab.

**Description:** Admin re-opens `ConfidentialityParamsModal` via the **Editar parámetros** button on a diagnostic that already has a generated NDA. The form pre-fills from `diagnostic.confidentiality_params` (with the same Project App / Medellín / 50 SMMLV defaults overlaid for any field still blank). Submit hits the same `POST /api/diagnostics/:id/confidentiality/params/` endpoint; the existing `DiagnosticAttachment` row is updated in place — `existing.file.delete(save=False)` then `existing.file.save(filename, ContentFile(pdf_bytes), save=False)` then a single `existing.save()`, so the attachment id is preserved and any prior file is removed from storage.

**Steps:**
1. Admin opens the Documentos tab for a diagnostic that already has an NDA (section header shows "Generado el {fecha}").
2. Admin clicks **Editar parámetros** — `ConfidentialityParamsModal` opens with the saved params pre-filled.
3. Admin modifies one or more fields (e.g. updates the client NIT) and clicks **Guardar y generar PDF**.
4. Modal closes; section header now shows the new "Generado el {fecha}" timestamp.
5. Admin clicks **Descargar** to verify the PDF reflects the new value.

**Branches:**
- [Same id, replaced file] The store updates `current.attachments` in place (matching by id from the response); the row count does not increase.

**Expected outcome:** `diagnostic.confidentiality_params` is updated, the same `DiagnosticAttachment` row is reused, and the rendered PDF reflects the new params.

---

### 16.3 Diagnostic NDA Download

#### FLOW: `admin-diagnostic-confidentiality-download`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-confidentiality-download` |
| **Module** | diagnostics |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ✅ Covered |

**Routes:** `/panel/diagnostics/:id/edit` → Documentos tab.

**Description:** Admin downloads the Acuerdo de Confidencialidad PDF in either of two modes from the Documentos tab. **Descargar** points to `GET /api/diagnostics/:id/confidentiality/pdf/` which returns the saved file via `FileResponse` (streamed, `Content-Type: application/pdf`, filename built via `_confidentiality_filename`). **Borrador** points to `GET /api/diagnostics/:id/confidentiality/draft-pdf/` which generates a fresh PDF with all params forced to `XXX-XXX-XXX` (no real data leaks) and applies `add_watermark_to_pdf` to stamp `BORRADOR` diagonally across each page; returned inline as `HttpResponse`.

**Steps:**
1. Admin opens the Documentos tab for a diagnostic with an existing NDA.
2. Admin clicks **Descargar** — browser opens `/api/diagnostics/:id/confidentiality/pdf/` in a new tab; PDF renders with branded ProjectApp template, title "ACUERDO DE CONFIDENCIALIDAD", and placeholders filled from `confidentiality_params`.
3. Admin clicks **Borrador** — browser opens `/api/diagnostics/:id/confidentiality/draft-pdf/` in a new tab; PDF renders with the same template but every value shows as `XXX-XXX-XXX` plus a diagonal `BORRADOR` watermark.

**Branches:**
- [Not generated] When no NDA exists, neither link is rendered; the section shows "No generado" plus the **Generar acuerdo** CTA. Hitting `/confidentiality/pdf/` directly returns HTTP 404 `{"error": "El acuerdo aún no ha sido generado."}`.

**Expected outcome:** Both URLs return valid PDFs (≥ 50 KB each); the draft includes a watermark and no real client data.

---

### 16.4 New Flows Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-diagnostic-confidentiality-generate` | diagnostics | admin | P1 | ✅ Covered | `e2e/admin/admin-diagnostic-confidentiality.spec.js` |
| `admin-diagnostic-confidentiality-edit` | diagnostics | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-confidentiality-edit.spec.js` |
| `admin-diagnostic-confidentiality-download` | diagnostics | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-confidentiality-download.spec.js` |
| `admin-diagnostic-documents` (NDA branches) | diagnostics | admin | P2 | 🟡 Partial | Existing `e2e/admin/admin-diagnostic-email-documents.spec.js` covers base; NDA-checkbox + delete-blocked branches not yet asserted |

---

## Section 17 — v2.23.0 Gaps (Diagnostic Admin Tab Restructure)

> Flows registered during the v2.23.0 audit cycle. Covers the diagnostic admin edit-page alignment with the proposals admin pattern: tab reorder, conditional visibility of Correos/Documentos by status, and the replacement of the raw-JSON "Plantillas" textarea with a full JSON export/import tab (parity with `admin-proposal-json`). The short-lived "Det. técnico" tab (Pricing + Radiografía sub-tabs) was retired on 2026-04-18 — pricing now lives in General and radiografía is edited as a regular section from Secciones.

### 17.1 Diagnostic JSON Export

#### FLOW: `admin-diagnostic-json-export`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-json-export` |
| **Module** | diagnostics |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ✅ Covered |

**Routes:** `/panel/diagnostics/:id/edit` → JSON tab.

**Description:** Admin opens the JSON tab (replaces the prior "Plantillas" tab). A read-only `<textarea>` renders the full diagnostic serialized as JSON — `{metadata: {title, language, investment_amount, currency, payment_terms, duration_label, size_category, radiography, client: {id, name, email, company}}, sections: [...]}`. The string is lazy-computed from `store.current` so it only rebuilds when the tab is rendered (not on every debounced section save). Three buttons sit above the textarea: **Actualizar** refetches `/api/diagnostics/:id/detail/`; **Copiar** writes the textarea content to the clipboard and flips the label to "¡Copiado!" for ~1.5s; **Descargar** streams a Blob download named `{slug}.json` where `{slug}` is the diagnostic title lowercased with non-alphanumerics collapsed to `-`.

**Steps:**
1. Admin opens `/panel/diagnostics/:id/edit` and clicks the **JSON** tab.
2. Read-only textarea renders with the current diagnostic's full JSON.
3. Admin clicks **Copiar** — clipboard receives the text, label flips to "¡Copiado!" and reverts after ~1.5s.
4. Admin clicks **Descargar** — browser downloads `{slug}.json` with the same payload.
5. Admin clicks **Actualizar** — `fetchDetail` re-hits the server; textarea reflects any server-side changes.

**Branches:**
- [Legacy deep-link] `?tab=plantillas` redirects to `?tab=json` on initial mount and on in-session route changes.

**Expected outcome:** The exported JSON round-trips back through `admin-diagnostic-json-import` without loss.

---

### 17.2 Diagnostic JSON Import

#### FLOW: `admin-diagnostic-json-import`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-json-import` |
| **Module** | diagnostics |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ⬜ Missing spec |

**Routes:** `/panel/diagnostics/:id/edit` → JSON tab (Importar JSON section).

**Description:** Admin imports a full-diagnostic JSON blob from the JSON tab, either by pasting into the import textarea or uploading a `.json` file (FileReader → textarea). `parseImportJson` runs on every `@input`; validation requires the root to be an object (not an array) with `sections` as an array. When parse succeeds, a green preview strip shows Cliente (`metadata.client.name`), # Secciones (`sections.length`), and Inversión (formatted with `formatMoney` + `currency`). **Aplicar JSON** first issues `PATCH /api/diagnostics/:id/update/` with the whitelisted metadata keys (title, language, investment_amount, currency, payment_terms, duration_label, size_category, radiography, client_id from `metadata.client?.id`); if that succeeds it then `POST`s `/sections/bulk-update/` with `{sections: [...]}` using id/title/order/is_enabled/visibility/content_json per row. On success the import state is cleared and `syncForms()` refreshes the Pricing/Radiography forms; on error the apply is aborted with an inline red message.

**Steps:**
1. Admin opens the JSON tab.
2. Admin either pastes a JSON blob into the "Importar JSON" textarea or clicks **Subir .json** and picks a file.
3. Parse succeeds → preview strip shows Cliente / Secciones / Inversión; **Aplicar JSON** button enables.
4. Admin clicks **Aplicar JSON** — metadata PATCH fires first, then bulk sections POST.
5. Success toast: "JSON aplicado correctamente." Textarea clears, preview hides, General-tab pricing fields and the radiografía section reflect the new values.

**Branches:**
- [Invalid JSON] Parse throws → red box with `JSON inválido: {message}`; Aplicar button stays disabled.
- [Wrong root] Root is an array or lacks `sections` → red box: "`sections` debe ser un array." or "El JSON raíz debe ser un objeto con `metadata` y `sections`."
- [Metadata error] Metadata PATCH fails → red box with backend error, sections bulk is skipped (no partial apply).
- [Sections error — metadata not yet applied] Sections bulk fails and no metadata was sent → red box "Error al aplicar las secciones: {error}."
- [Sections error — metadata already applied] Sections bulk fails after metadata succeeded → explicit partial-state red box: "Se aplicaron los datos generales, pero fallaron las secciones: {error}. Corrige el JSON y vuelve a aplicar — la metadata ya está actualizada." Admin knows exactly what persisted and what didn't.

**Expected outcome:** On a valid payload, the diagnostic's metadata and all 8 sections reflect the imported JSON; the JSON export (17.1) round-trips identically.

---

### 17.3 New Flows Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-diagnostic-json-export` | diagnostics | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-json.spec.js` |
| `admin-diagnostic-json-import` | diagnostics | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-json-import.spec.js` |
| `admin-diagnostic-defaults-config` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-defaults.spec.js` |
| `admin-diagnostic-mark-in-analysis` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-diagnostic-send.spec.js` (`'Marcar en análisis' button POSTs…`) |
| `diagnostic-public-respond` | diagnostic | guest | P1 | ✅ Covered | `e2e/public/diagnostic-public-view.spec.js` (`clicking 'Aceptar propuesta'…`) |
| `admin-proposal-diagnostic-templates` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-diagnostic-templates.spec.js` |
| `admin-diagnostic-markdown-attachment` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-markdown-attachment.spec.js` |
| `admin-defaults-unified` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-defaults-unified.spec.js` |
| `admin-proposal-defaults-slug-pattern` | admin | admin | P2 | ❌ Missing | pending `e2e/admin/admin-proposal-defaults-slug-pattern.spec.js` |

---

### 17.5 Diagnostic Defaults Config (Apr 18, 2026)

#### FLOW: `admin-diagnostic-defaults-config`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-defaults-config` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ✅ Covered |

**Routes:** `/panel/defaults?mode=diagnostic` (old `/panel/diagnostics/defaults` redirects here).

**Description:** Admin manages the per-language defaults applied to every new `WebAppDiagnostic` from `panel/diagnostics/defaults.vue`. The page mirrors `/panel/proposals/defaults/` but is scoped to diagnostics. Five tabs render from one config payload: **General** (idioma, moneda, inversión, duración, % pagos con auto-sync 100, días de recordatorio/urgencia/expiración), **Secciones** (lista read-only de las 8 secciones del seed activo), **Plantillas de Email** (link a `/panel/email-templates`), **Prompt** (placeholder), **JSON** (vista cruda). Cuando no existe una `DiagnosticDefaultConfig` para el idioma, `GET /api/diagnostics/defaults/?lang=` devuelve los valores hardcoded del seed con 60% inicial / 40% final como pagos por defecto.

**Steps:**
1. Admin abre `/panel/defaults?mode=diagnostic` desde el botón "Valores por Defecto" del header de `/panel/diagnostics` (o el ítem "Defaults" del sidebar con el switch en modo Diagnóstico).
2. La página llama `GET /api/diagnostics/defaults/?lang=es` y popula `generalForm` + `sectionsList` + `rawConfig` vía `applyConfig(data)`.
3. El tab General muestra los inputs precargados (60/40, COP, 21/7/14 días).
4. Admin edita el % inicial — `syncPaymentFinal()` mueve el % final automáticamente para mantener suma=100.
5. Admin presiona "Guardar cambios" → `PUT /api/diagnostics/defaults/` con language + sections_json + payment_initial_pct + payment_final_pct + default_currency + default_investment_amount + default_duration_label + reminder/urgency/expiration days.
6. La respuesta se aplica vía `applyConfig(result.data)` (sin re-fetch). `usePanelToast` muestra "Valores guardados correctamente."
7. Cualquier diagnóstico creado a partir de ahora hereda esos valores en `payment_terms` / `currency` / `investment_amount` / `duration_label`.

**Branches:**
- [Branch A — Reset] Admin presiona "Restablecer a valores del sistema" → `useConfirmModal` muestra "¿Eliminar el config personalizado y volver a los valores del sistema (60/40, COP, 21 días)?" → al confirmar se ejecuta `POST /api/diagnostics/defaults/reset/`, se borra la fila DB y la página recarga el seed hardcoded.
- [Branch B — Cambio de idioma] Admin cambia el `<select>` de idioma → `onLanguageChange` re-llama `GET /defaults/?lang=` con el idioma nuevo. La fila de la otra lengua queda intacta.
- [Branch C — Pagos no suman 100] Si el cliente fuerza valores manuales que no sumen 100 (deshabilitando el sync), el botón Guardar queda disabled y se muestra el aviso "La suma debe ser exactamente 100% (actual: N%)". El backend valida con la misma regla por si la UI se salta.

**Expected outcome:** El `DiagnosticDefaultConfig` para ese idioma queda persistido (o eliminado en el caso del reset). Cualquier llamada subsecuente a `diagnostic_service.create_diagnostic(language=...)` lee el config y lo aplica al nuevo diagnóstico antes de sembrar las secciones.

**Backend Tests:** `content/tests/views/test_diagnostic_defaults_views.py` (16) + `content/tests/models/test_diagnostic_default_config.py` (8).
**Frontend Tests:** `frontend/test/stores/diagnostics.test.js` (`fetchDiagnosticDefaults`/`saveDiagnosticDefaults`/`resetDiagnosticDefaults` — 6 cases).
**E2E Spec:** `e2e/admin/admin-diagnostic-defaults.spec.js`.

### 17.6 Unified Defaults Shell (Apr 20, 2026)

#### FLOW: `admin-defaults-unified`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-defaults-unified` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ✅ Covered |

**Routes:** `/panel/defaults` (with `?mode=proposal` or `?mode=diagnostic`).

**Description:** Admin accesses a unified shell page that replaces the two separate defaults pages. A segmented mode switch toggles between the **Propuesta** panel and the **Diagnóstico** panel. The active mode is persisted via query param so reloads and direct links preserve it. The back link adapts to the active mode. Old routes `/panel/proposals/defaults` and `/panel/diagnostics/defaults` redirect here preserving existing `?tab=` params.

**Steps:**
1. Admin clicks **"Defaults"** in the Sales section of the sidebar → navigates to `/panel/defaults` (defaults to proposal mode).
2. The mode switch shows **Propuesta** as active (highlighted with `bg-emerald-600`).
3. `ProposalDefaultsPanel` lazy-loads and fetches `GET /api/proposals/defaults/?lang=es`.
4. Admin clicks **"Diagnóstico"** in the mode switch → URL updates to `?mode=diagnostic`, tab param is cleared.
5. `DiagnosticDefaultsPanel` lazy-loads and fetches `GET /api/diagnostics/defaults/?lang=es`.
6. Back link shows "Volver a Diagnósticos" linking to `/panel/diagnostics`.

**Branches:**
- [Branch A — Direct diagnostic link] Navigating to `/panel/defaults?mode=diagnostic` starts in diagnostic mode.
- [Branch B — Old URL redirect] `/panel/proposals/defaults?tab=sections` redirects to `/panel/defaults?mode=proposal&tab=sections`.
- [Branch C — Old URL redirect] `/panel/diagnostics/defaults` redirects to `/panel/defaults?mode=diagnostic`.
- [Branch D — Unknown mode] Unknown `?mode=` value falls back to proposal mode.

**Unit Tests:** `frontend/test/components/DefaultsShell.test.js` (9 cases — mode computed, setMode, backLink).
**E2E Spec:** `e2e/admin/admin-defaults-unified.spec.js`.

---

### 17.7 Diagnostic Lifecycle Transitions Split (Apr 18, 2026)

Two transitions that were previously bundled into other flows now have their own IDs so the registry honestly reflects three distinct admin/client interactions:

#### FLOW: `admin-diagnostic-mark-in-analysis`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-mark-in-analysis` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P1 |
| **Status** | ✅ Covered (assertion already existed under `admin-diagnostic-send-initial`; tag now points to its own flow ID) |

**Routes:** `/panel/diagnostics/:id/edit` — sticky bottom action bar.
**Description:** After the initial diagnostic has been sent (status SENT, `initial_sent_at` stamped), the admin clicks **Marcar en análisis** to acknowledge the client authorized continuing. A `useConfirmModal` warns "¿Confirmar que el cliente autorizó? Se moverá a «En negociación»." On confirm, the store calls `POST /api/diagnostics/:id/mark-in-analysis/`, status transitions SENT → NEGOTIATING, the page toast shows "Diagnóstico en negociación.", and the action bar swaps the button for **Enviar diagnóstico final**.
**Steps:**
1. Admin opens a SENT diagnostic.
2. Admin clicks **Marcar en análisis** in the action bar.
3. Confirmation modal renders.
4. Admin confirms → POST `/mark-in-analysis/`.
5. Status updates to NEGOTIATING; toast shown; button row updates.
**Branches:**
- [Branch — Cancel] Admin cancels the modal → no state change.
- [Branch — API error] Backend returns non-2xx → red toast with the error message; status unchanged.
**E2E Spec:** `e2e/admin/admin-diagnostic-send.spec.js` ("Marcar en análisis" test).

#### FLOW: `diagnostic-public-respond`

| Attribute | Value |
|-----------|-------|
| **ID** | `diagnostic-public-respond` |
| **Module** | diagnostic |
| **Role** | guest |
| **Priority** | P1 |
| **Status** | ✅ Covered (assertion already existed under `diagnostic-public-view`; tag now points to its own flow ID) |

**Routes:** `/diagnostic/:uuid/`.
**Description:** On the public diagnostic page in final phase (status SENT with `final_sent_at` stamped), the footer exposes **Aceptar propuesta** and **Rechazar**. Clicking either calls `POST /api/diagnostics/public/<uuid>/respond/` with `{decision: 'accept' | 'reject'}`. The backend transitions to ACCEPTED or REJECTED, the page swaps to the acceptance / rejection confirmation footer, and the matching toast renders ("Tu aceptación quedó registrada." / "Tu respuesta quedó registrada.").
**Steps:**
1. Client opens a final-phase public diagnostic.
2. Client clicks **Aceptar propuesta** (or **Rechazar**).
3. Frontend POSTs `/respond/`.
4. Confirmation footer renders; status reflected on next refresh.
**Branches:**
- [Branch A — Accept] decision=accept → ACCEPTED, acceptance footer.
- [Branch B — Reject] decision=reject → REJECTED, rejection footer (typically with reason field).
- [Branch C — Already responded] If the diagnostic was already responded to, the respond buttons are hidden and the footer shows the existing response state.
**E2E Spec:** `e2e/public/diagnostic-public-view.spec.js` ("clicking 'Aceptar propuesta'…" test).

---

### 17.4 Out-of-scope behaviors documented but not registered as standalone flows

- **Legacy `?tab=technical|pricing|radiography` deep-links** — retired on 2026-04-18. `LEGACY_TAB_REDIRECTS` now maps `pricing → general`, `radiography → sections`, `technical → sections` so existing bookmarks land on the new owner of that data. Not a user outcome, documented here as a branch.
- **Conditional tab visibility by status** — Correos appears from `sent` onward; Documentos from `negotiating` onward. This is asserted implicitly by `admin-diagnostic-send-initial` (Correos should appear after the transition) and `admin-diagnostic-send-final` / confidentiality flows (Documentos should be available). Added here as a documented branch rather than a new flow since no new user outcome is introduced.

---

## Section 18 — Diagnostic List & Filter Flows (Apr 20, 2026)

> Flows identified during the Apr 20 E2E coverage audit. The diagnostic list page had no registered flow, and the `DiagnosticFilterPanel` + `useDiagnosticFilters` feature (saved tabs, 5 filter dimensions) shipped Apr 18 with no E2E spec or flow ID.

### 18.1 New Flows Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-diagnostic-list` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-diagnostic-list.spec.js` |
| `admin-diagnostic-filters` | admin | admin | P2 | 🟡 Partial | Covered by `e2e/admin/admin-diagnostic-advanced-filters.spec.js` |
| `admin-diagnostic-advanced-filters` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-advanced-filters.spec.js` |
| `admin-client-edit` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-client-edit.spec.js` |

---

### 18.2 Diagnostic List

#### FLOW: `admin-diagnostic-list`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-list` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P1 |
| **Status** | ✅ Covered — `e2e/admin/admin-diagnostic-list.spec.js` |

**Routes:** `/panel/diagnostics/`

**Description:** Admin views the list of all `WebAppDiagnostic` records. Each card shows title, client name, status badge (chip), investment amount, language, and creation date. The page exposes a search input, a "Valores por Defecto" header button, and a "+ Nuevo Diagnóstico" button. The list is fetched from `GET /api/diagnostics/` with the active filter params applied.

**Steps:**
1. Admin navigates to `/panel/diagnostics/`.
2. `GET /api/diagnostics/` fires; diagnostic cards render.
3. Admin sees each card with title, client name, status badge.
4. Admin clicks a diagnostic card → navigated to `/panel/diagnostics/:id/edit`.
5. Admin clicks "+ Nuevo Diagnóstico" → navigated to `/panel/diagnostics/create`.
6. Admin clicks "Valores por Defecto" → navigated to `/panel/diagnostics/defaults`.

**Branches:**
- [Branch A — Empty list] When no diagnostics exist, the empty-state copy renders ("Aún no has creado diagnósticos.").
- [Branch B — Search] Admin types in the search input → `searchQuery` filters the list client-side; matching cards remain visible, others hide.

**Expected outcome:** Diagnostic cards are visible; navigation to create/edit/defaults works; empty state renders correctly when list is empty.

**Flow tag:** `ADMIN_DIAGNOSTIC_LIST`

---

### 18.3 Diagnostic Filter Tabs

#### FLOW: `admin-diagnostic-filters`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-filters` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ⬜ Missing spec |

**Routes:** `/panel/diagnostics/`

**Description:** Admin filters diagnostics via `DiagnosticFilterPanel` + `useDiagnosticFilters`. Five filter dimensions: `statuses` (multi-select chip list), `investmentMin` / `investmentMax` (number inputs), `createdAfter` / `createdBefore` (date inputs). Results are filtered client-side on the already-fetched list. Filter state is persisted per saved tab in localStorage (`diagnostic_filter_tabs`). Tab bar mirrors `ProposalFilterTabs` behaviour: up to 12 tabs, add / rename / delete, URL sync via `?tab=<tabId>`.

**Steps:**
1. Admin navigates to `/panel/diagnostics/`.
2. Admin clicks "Filtros" toggle → `DiagnosticFilterPanel` expands.
3. Admin selects one or more statuses (e.g. "sent") → card list updates immediately.
4. Admin enters an investment range → cards outside the range are hidden.
5. Admin clicks "+ Guardar filtro" → modal prompts for tab name → new tab appears in the tab bar.
6. Admin reloads the page and selects the saved tab → the stored filters re-apply.
7. Admin deletes the tab → it disappears from the tab bar.

**Branches:**
- [Branch A — No results] All diagnostics filtered out → "No hay diagnósticos que coincidan con los filtros." empty state renders.
- [Branch B — Reset] Admin clicks "Restablecer" → all filter dimensions clear and full list shows.
- [Branch C — URL deep-link] `/panel/diagnostics/?tab=<tabId>` pre-selects the matching saved tab on load.

**Expected outcome:** Filter dimensions hide/show cards in real-time; tab save/load/delete persists to localStorage; URL reflects active tab.

**Flow tag:** `ADMIN_DIAGNOSTIC_FILTERS`

---

#### FLOW: `admin-diagnostic-advanced-filters`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-advanced-filters` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ✅ Covered |

**Routes:** `/panel/diagnostics/`

**Description:** Advanced tab-based filter UI for diagnostics. Default view shows all diagnostics with no active filters. "Filtros" toggle button expands/collapses `DiagnosticFilterPanel` showing the Estados dimension. The "+" button opens a name input to create a saved filter tab (persisted to `localStorage['diagnostic_filter_tabs']`). The search input filters the rendered diagnostic list client-side by title.

**Steps:**
1. Admin navigates to `/panel/diagnostics/`.
2. All diagnostics are visible with no active filters.
3. Admin clicks "Filtros" → `DiagnosticFilterPanel` expands with status chips.
4. Admin clicks "Filtros" again → panel collapses.
5. Admin clicks "+" → name input appears → admin enters a name and confirms → new tab appears in the tab bar.
6. Admin types in the search input → visible cards filter by title immediately.

**E2E Spec:** `e2e/admin/admin-diagnostic-advanced-filters.spec.js` (4 tests).

**Flow tag:** `ADMIN_DIAGNOSTIC_ADVANCED_FILTERS`

---

#### FLOW: `admin-client-edit`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-client-edit` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ✅ Covered |

**Routes:** `/panel/clients/`

**Description:** Admin edits an existing client profile from the Clientes list. Clicking the edit (pencil) icon on a client row opens a modal pre-filled with name, email, phone, and company. Admin changes one or more fields and submits. On success (`PUT /api/proposals/client-profiles/:id/update/` → 200), the modal closes. On validation error (400 with field errors), the modal stays open with the server error surfaced.

**Steps:**
1. Admin navigates to `/panel/clients/`.
2. Admin clicks the edit button on a client row (`data-testid="client-edit-{id}"`).
3. Modal opens with all fields pre-filled from the client profile.
4. Admin modifies the name field.
5. Admin clicks "Guardar" / submit.
6. [Branch A — Success] Modal closes; client list may refresh.
7. [Branch B — Error] Modal stays open; validation error message visible.

**E2E Spec:** `e2e/admin/admin-client-edit.spec.js` (3 tests).

**Flow tag:** `ADMIN_CLIENT_EDIT`

---

## Section 19 — Diagnostic Public Client Affordances (Apr 20, 2026)

> Flows added alongside the diagnostic public UI polish: PDF download endpoint, share modal, and dark mode toggle. These three affordances mirror the equivalent proposal client flows (`proposal-download-pdf`, `proposal-share`) and align the diagnostic public view with the proposal client experience.

### 19.1 New Flows Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `diagnostic-public-pdf-download` | diagnostic | guest | P2 | ✅ Covered | `e2e/public/diagnostic-public-affordances.spec.js` |
| `diagnostic-public-share`        | diagnostic | guest | P2 | ✅ Covered | `e2e/public/diagnostic-public-affordances.spec.js` |
| `diagnostic-public-dark-mode`    | diagnostic | guest | P3 | ✅ Covered | `e2e/public/diagnostic-public-affordances.spec.js` |

---

### 19.2 Diagnostic Public PDF Download

#### FLOW: `diagnostic-public-pdf-download`

| Attribute | Value |
|-----------|-------|
| **ID** | `diagnostic-public-pdf-download` |
| **Module** | diagnostic |
| **Role** | guest |
| **Priority** | P2 |
| **Status** | ✅ Covered — `e2e/public/diagnostic-public-affordances.spec.js` |

**Routes:** `/diagnostic/:uuid/`
**Endpoint:** `GET /api/diagnostics/public/:uuid/pdf/` (AllowAny, returns `application/pdf` when status is SENT/ACCEPTED/NEGOTIATING; 404 on DRAFT).

**Description:** The floating `DownloadDiagnosticPdfButton` (`data-testid="download-diagnostic-pdf-btn"`) appears once `store.current` is loaded. Clicking it calls the public PDF endpoint via `fetch()`, creates a blob URL, and triggers a browser download named `Diagnostico_<client>_<DD-MM-YY>.pdf`. The button disables and shows a spinner while the request is in flight and re-enables on completion. PDF is generated by `DiagnosticPdfService` (ReportLab), which renders all enabled sections in order using `pdf_utils` helpers.

**Steps:**
1. Client opens a SENT public diagnostic.
2. Client clicks the floating PDF button.
3. `GET /api/diagnostics/public/<uuid>/pdf/` fires.
4. On 200: blob is downloaded; button re-enables.
5. On error: console error logged; button re-enables.

**Flow tag:** `DIAGNOSTIC_PUBLIC_PDF_DOWNLOAD`

---

### 19.3 Diagnostic Public Share

#### FLOW: `diagnostic-public-share`

| Attribute | Value |
|-----------|-------|
| **ID** | `diagnostic-public-share` |
| **Module** | diagnostic |
| **Role** | guest |
| **Priority** | P2 |
| **Status** | ✅ Covered — `e2e/public/diagnostic-public-affordances.spec.js` |

**Routes:** `/diagnostic/:uuid/`

**Description:** The floating `ShareDiagnosticButton` (`data-testid="share-diagnostic-btn"`) opens a bottom-sheet modal (Teleport to body) with the current URL and a **Copiar enlace** action using `navigator.clipboard`. If `navigator.share` is available (mobile / Chromium with flag), a **Compartir vía apps** button also appears. No backend tracking is performed (silent). Modal closes on backdrop click or the close button.

**Steps:**
1. Client opens the public diagnostic page.
2. Client clicks the share button.
3. Modal renders with "Compartir diagnóstico" heading and "Copiar enlace" button.
4. Client clicks "Copiar enlace" → clipboard receives the URL; button changes to "¡Copiado!" for 2.5 s.
5. [Branch — native share] If `navigator.share` available, client clicks "Compartir vía apps" → OS share sheet opens.

**Flow tag:** `DIAGNOSTIC_PUBLIC_SHARE`

---

### 19.4 Diagnostic Public Dark Mode Toggle

#### FLOW: `diagnostic-public-dark-mode`

| Attribute | Value |
|-----------|-------|
| **ID** | `diagnostic-public-dark-mode` |
| **Module** | diagnostic |
| **Role** | guest |
| **Priority** | P3 |
| **Status** | ✅ Covered — `e2e/public/diagnostic-public-affordances.spec.js` |

**Routes:** `/diagnostic/:uuid/`

**Description:** A fixed bottom-left toggle button (`data-testid="diagnostic-theme-toggle"`) switches between light and dark mode by setting `data-theme` on `[data-diagnostic-wrapper]`. State is persisted to `localStorage['diagnostic-dark-mode']` via `useDiagnosticDarkMode` composable and restored on the next page load. Dark mode applies brand-aligned colors (`#0a1f1c` background, `#143d35` cards, `#E6EFEF` text) via scoped CSS `[data-theme="dark"] :deep(...)` rules.

**Steps:**
1. Client opens the public diagnostic page (light mode by default).
2. Client clicks the toggle (`🌙` icon).
3. `[data-diagnostic-wrapper]` receives `data-theme="dark"`; page styles update.
4. `localStorage['diagnostic-dark-mode']` is set to `"true"`.
5. Client reloads the page → composable reads localStorage on `onMounted`; dark mode is restored.
6. Client clicks the toggle again (`☀️` icon) → reverts to light mode.

**Flow tag:** `DIAGNOSTIC_PUBLIC_DARK_MODE`

---

## Section 20 — Flows Audit Gaps (Apr 20, 2026)

> Flows identified by the `/e2e-user-flows-check` audit as missing from the registry. All three carry `expectedSpecs: 0` and ❌ coverage — they are registered for traceability and to prioritize future E2E work.

---

### 20.1 Admin Proposal → Platform Handoff

#### FLOW: `admin-proposal-platform-handoff`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-proposal-platform-handoff` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P1 |
| **Status** | ❌ Missing — no E2E spec |

**Routes:** `/panel/proposals/:id/edit` (actions panel after acceptance)

**Description:** After a proposal is accepted by the client, admin clicks **"Lanzar a plataforma"** — `POST /api/proposals/:id/launch-to-platform/` — which creates a `PlatformProject` linked to the proposal and sends the client an invitation email containing an OTP. Admin sees a **"Ver en plataforma"** action in the proposal actions panel; client then starts the platform onboarding flow (`platform-login` → `platform-verify-onboarding` → `platform-complete-profile`).

**Steps:**
1. Admin navigates to a proposal in `accepted` status.
2. Actions panel shows "Lanzar a plataforma" button.
3. Admin clicks the button → `POST /api/proposals/:id/launch-to-platform/` fires.
4. Backend creates a `PlatformProject` (linked to proposal), sends invitation email with OTP.
5. Admin sees "Ver en plataforma" link in actions panel.
6. Client receives email, clicks link, enters OTP → platform onboarding starts.

**Known gaps:** This cross-module flow (proposal → platform) has no E2E coverage. The backend endpoint (`launch-to-platform`) exists and is tested in Python. An E2E spec would mock both the proposal detail and the `launch-to-platform` POST and verify the UI transition.

**Flow tag:** `ADMIN_PROPOSAL_PLATFORM_HANDOFF`

---

### 20.2 Diagnostic Public Phase Visibility

#### FLOW: `diagnostic-public-phase-visibility`

| Attribute | Value |
|-----------|-------|
| **ID** | `diagnostic-public-phase-visibility` |
| **Module** | diagnostic |
| **Role** | guest |
| **Priority** | P2 |
| **Status** | ❌ Missing — no dedicated E2E spec |

**Routes:** `/diagnostic/:uuid/`

**Description:** The public diagnostic page renders different sections depending on the diagnostic phase. After admin sends **initial phase** (`initial_sent_at` set, status=SENT), the API returns only sections with `visibility ∈ {initial, both}` and sections with `visibility='final'` are absent. After admin sends **final phase** (`final_sent_at` set), sections with `visibility='final'` (e.g. `executive_summary`, `cost`, `timeline`) are also returned.

**Steps:**
1. [Initial phase] Admin sends initial → client opens diagnostic link.
2. API returns only `initial`/`both` sections; `final`-only sections are not in the response.
3. Sidebar index and scroll containers show only the filtered sections.
4. [Final phase] Admin sends final → `final_sent_at` is stamped.
5. Client reloads → API now includes `final`-visibility sections.
6. Sidebar index updates; accept/reject footer appears.

**Known gaps:** `diagnostic-public-view` E2E covers section rendering for a single state but does not explicitly verify which section types appear or disappear when switching between initial and final phases.

**Flow tag:** `DIAGNOSTIC_PUBLIC_PHASE_VISIBILITY`

---

### 20.3 Admin Proposal Section Disable/Enable Toggle

#### FLOW: `admin-proposal-section-disable`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-proposal-section-disable` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ❌ Missing — no E2E spec |

**Routes:** `/panel/proposals/:id/edit` (Secciones tab)

**Description:** Admin toggles section visibility (`is_enabled`) from the Secciones tab of the proposal edit page. Each section row has an enable/disable toggle; disabled sections are greyed out in the admin list and excluded from the public proposal view. Complements `admin-proposal-section-reorder` — both operations may be combined.

**Steps:**
1. Admin opens the Secciones tab of a proposal edit page.
2. Each section row shows an enable/disable toggle.
3. Admin clicks the toggle on a section → `PATCH /api/proposals/sections/:id/update/` with `{ is_enabled: false }`.
4. Section row is greyed out in the admin list.
5. Admin visits the public proposal link → the disabled section is not visible.
6. Admin re-enables the section → `PATCH` with `{ is_enabled: true }` → section reappears on public view.

**Known gaps:** `admin-proposal-section-reorder` covers drag reorder only. No E2E explicitly asserts that toggling `is_enabled` removes a section from the public proposal view.

**Flow tag:** `ADMIN_PROPOSAL_SECTION_DISABLE`

---

## Section 21 — Documents Tab Reorganization & doc_refs Attachment (Apr 22, 2026)

> Flows registered during the Apr 22, 2026 reorganization. The Documents tab now serves as a read-only document viewer; sending files is done from the Correos tab using `doc_refs` references — no re-upload needed. The old `admin-proposal-documents-send` flow is superseded.

---

### 21.1 Proposal — Adjuntar desde Documentos

#### FLOW: `admin-proposal-attach-from-documents`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-proposal-attach-from-documents` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P1 |
| **Status** | ✅ Covered |

**Routes:** `/panel/proposals/:id/edit` (Correos tab)

**Description:** Admin attaches existing proposal documents to the email composer without re-uploading them. The "Adjuntar desde Documentos" button opens `AttachFromDocumentsModal` which lists: contract PDF + draft (if a generated contract exists), commercial PDF, technical PDF, and any uploaded `proposal_documents`. Selected items become `doc_refs` badges in the composer. On send, `doc_refs` is included in the POST body and the backend resolves each reference to a real file attachment.

**Steps:**
1. Admin opens the Correos tab of a proposal (status `sent`, `viewed`, `negotiating`, `accepted`, or `rejected`).
2. Admin clicks **"Adjuntar desde Documentos"** button.
3. `AttachFromDocumentsModal` opens with a list of available documents.
4. Admin checks one or more documents; confirm button shows count: "Adjuntar (N)".
5. Admin clicks confirm → modal closes; emerald ref badges appear in the composer attachment area.
6. Admin completes the email and clicks "Enviar correo" → `POST /api/proposals/:id/branded-email/send/` with `doc_refs=[{source, id?}]`.
7. Backend resolves each `doc_refs` entry to a file binary and attaches it to the email.

**E2E Spec:** `e2e/admin/admin-proposal-attach-from-documents.spec.js`

**Flow tag:** `ADMIN_PROPOSAL_ATTACH_FROM_DOCUMENTS`

---

### 21.2 Diagnostic — Adjuntar desde Documentos

#### FLOW: `admin-diagnostic-attach-from-documents`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-attach-from-documents` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ✅ Covered |

**Routes:** `/panel/diagnostics/:id/edit` (Correos tab)

**Description:** Admin attaches existing diagnostic documents to the email composer without re-uploading. The "Adjuntar desde Documentos" button opens `AttachFromDocumentsModal` with: NDA final + NDA draft (if a generated `confidentiality_agreement` attachment exists), all diagnostic MD templates (Diagnóstico de Aplicación, Diagnóstico Técnico, Anexo — Dimensionamiento), and any uploaded `DiagnosticAttachment` files. Selected items become `doc_refs` badges. On send, `doc_refs` is included and the backend resolves each reference.

**Steps:**
1. Admin opens the Correos tab of a diagnostic (status `sent`, `viewed`, `negotiating`, `accepted`, `rejected`, or `finished`).
2. Composer loads `diagnostic-templates/` to populate available MD templates.
3. Admin clicks **"Adjuntar desde Documentos"** button.
4. `AttachFromDocumentsModal` opens; NDA items appear only if a generated `confidentiality_agreement` attachment exists.
5. Admin checks one or more items; confirm button shows count.
6. Admin clicks confirm → badges appear in the composer.
7. Admin completes the email and clicks "Enviar correo" → `POST /api/diagnostics/:id/email/send/` with `doc_refs=[{source, slug?, id?}]`.
8. Backend resolves: `nda_final`/`nda_draft` generate PDF; `template:<slug>` resolves MD; `attachment:<id>` reads the uploaded file.

**E2E Spec:** `e2e/admin/admin-diagnostic-attach-from-documents.spec.js`

**Flow tag:** `ADMIN_DIAGNOSTIC_ATTACH_FROM_DOCUMENTS`

---

### 21.3 Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-proposal-attach-from-documents` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-attach-from-documents.spec.js` |
| `admin-diagnostic-attach-from-documents` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-diagnostic-attach-from-documents.spec.js` |
| `admin-proposal-documents-send` | admin | admin | P1 | ⚠️ Superseded | Replaced by `admin-proposal-attach-from-documents` (Apr 22, 2026); `expectedSpecs: 0` |
| `admin-proposal-slug-edit` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-slug-edit.spec.js` |

---

## Section 22 — Flows Audit Gaps (Apr 26, 2026)

> Flows surfaced by the `/e2e-user-flows-check` audit on 2026-04-26 from recent feature commits (`4862b149`, `9877df24`, `e827bd38`). All carry `expectedSpecs: 0` and ❌ coverage — registered for traceability and to prioritize future E2E work. Component-level unit tests already exist for several of them.

---

### 22.1 Diagnostic Public Onboarding

#### FLOW: `diagnostic-public-onboarding`

| Attribute | Value |
|-----------|-------|
| **ID** | `diagnostic-public-onboarding` |
| **Module** | diagnostic |
| **Role** | guest |
| **Priority** | P3 |
| **Status** | ❌ Missing — no E2E spec |

**Routes:** `/diagnostic/:uuid/`

**Description:** First-visit tutorial overlay on the public diagnostic page (`DiagnosticOnboarding.vue`, 376 lines) that walks the client through the report's structure with step-by-step tooltips, scroll-to-section behavior, and a "No volver a mostrar" option persisted to `localStorage`. Mirrors `proposal-view-onboarding` for the diagnostic module. Shipped with the diagnostic dark-mode rollout.

**Steps:**
1. Client opens `/diagnostic/:uuid/` for the first time (no `localStorage` skip flag set).
2. `DiagnosticOnboarding` overlay renders centered above the report, showing the first step.
3. Client clicks **"Siguiente"** → tooltip transitions to the next step; the page scrolls so the highlighted section is in view.
4. Final step shows a **"Listo"** button. On click, the overlay dismisses and the skip flag is set.
5. Client reloads the page → onboarding does not reappear.
6. [Branch — opt-out] Client checks **"No volver a mostrar"** at any step and dismisses → skip flag set even mid-tour.

**Known gaps:** Component-level unit tests exist (`DiagnosticOnboarding.test.js`, 227 lines). E2E spec pending; should mock the diagnostic public payload, clear `localStorage`, and assert step navigation, scroll-into-view, and the persistence of the skip flag.

**Flow tag:** `DIAGNOSTIC_PUBLIC_ONBOARDING`

---

### 22.2 Admin Proposal Document Preview

#### FLOW: `admin-proposal-document-preview`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-proposal-document-preview` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P3 |
| **Status** | ❌ Missing — no E2E spec |

**Routes:** `/panel/proposals/:id/edit` (Documents tab)

**Description:** From the Documents tab of the proposal edit page, admin clicks the eye icon next to a document. A modal opens previewing the file inline — PDF (rendered in `<iframe>`) or image (via `<img>`), gated by `frontend/utils/filePreview.js` (`isPdfUrl` / `isImageUrl` / `canPreviewFile`). Non-previewable files (Word, Excel, etc.) keep only the existing download action.

**Steps:**
1. Admin opens the Documents tab on a proposal edit page.
2. Each document row shows an eye icon when `canPreviewFile(url)` returns `true`.
3. Admin clicks the icon → preview modal opens.
4. PDF documents render in an `<iframe>`; image documents render in an `<img>`.
5. Admin closes the modal via the close button or backdrop click.
6. [Branch — non-previewable] For docs not matching PDF/image extensions, the eye icon is not rendered; only the download link is available.

**Known gaps:** Eye-icon preview modal added in `ProposalDocumentsTab.vue` on 2026-04-26 (commits `9877df24`, `e827bd38`). E2E spec pending; should mock `/uploads/<file>.pdf` and assert the modal opens.

**Flow tag:** `ADMIN_PROPOSAL_DOCUMENT_PREVIEW`

---

### 22.3 Admin Diagnostic Document Preview

#### FLOW: `admin-diagnostic-document-preview`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-diagnostic-document-preview` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P3 |
| **Status** | ❌ Missing — no E2E spec |

**Routes:** `/panel/diagnostics/:id/edit` (Documentos tab)

**Description:** From the Documentos tab of the diagnostic edit page, admin clicks the eye icon next to an attachment. A modal opens previewing the file inline — PDF or image, gated by `frontend/utils/filePreview.js`. Replaces the previous inline template-expand behavior on `DiagnosticDocumentsTab.vue`.

**Steps:**
1. Admin opens the Documentos tab on a diagnostic edit page.
2. Each attachment row shows an eye icon when the file is previewable.
3. Admin clicks the icon → preview modal opens with PDF or image.
4. Admin closes the modal via the close button or backdrop click.
5. [Branch — non-previewable] Eye icon hidden; download link only.

**Known gaps:** Component-level unit test exists (`DiagnosticDocumentsTab.spec.js`). E2E spec pending; should mirror `admin-proposal-document-preview` against the diagnostic API surface.

**Flow tag:** `ADMIN_DIAGNOSTIC_DOCUMENT_PREVIEW`

---

### 22.4 Admin Blog Publish Mode

#### FLOW: `admin-blog-publish-mode`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-blog-publish-mode` |
| **Module** | admin |
| **Role** | admin |
| **Priority** | P2 |
| **Status** | ❌ Missing — no E2E spec |

**Routes:** `/panel/blog/:id/edit`

**Description:** From the blog edit page, admin selects how the post should be published via three radio options: **Borrador** (draft), **Publicar ahora** (immediate), or **Programar** (scheduled). Selecting "Programar" reveals a datetime input for `publish_scheduled_for`. If the chosen datetime is in the past, an amber overdue banner (`[data-test="scheduled-overdue-banner"]`) warns that the safety-net Huey task will publish on the next run. The mode is computed by `frontend/utils/blogPublishMode.js` (`resolveBlogPublishMode → { mode, scheduledIso, overdue }`) and submitted with the blog update.

**Steps:**
1. Admin opens `/panel/blog/:id/edit` for an existing post.
2. The publish-mode group renders three radios pre-selected based on the current post state.
3. Admin selects **Programar** → datetime input appears.
4. Admin enters a future datetime → no banner; on save, `publish_scheduled_for` is persisted and `published=false`.
5. Admin enters a past datetime → amber `scheduled-overdue-banner` renders; on save, the post remains unpublished and waits for the safety-net task.
6. Admin selects **Publicar ahora** → on save, the backend marks `published=true` and clears `publish_scheduled_for`.
7. Admin selects **Borrador** → on save, the post is unpublished and unscheduled.

**Known gaps:** Publish-mode radio + scheduled-overdue-banner shipped 2026-04-25 (commit `4862b149`). Unit-tested via `frontend/test/utils/blogPublishMode.test.js`; no E2E spec covers the admin UI yet.

**Flow tag:** `ADMIN_BLOG_PUBLISH_MODE`

---

### 22.5 Admin Blog Overdue Schedule Safety-Net

#### FLOW: `admin-blog-overdue-detection`

| Attribute | Value |
|-----------|-------|
| **ID** | `admin-blog-overdue-detection` |
| **Module** | admin |
| **Role** | system |
| **Priority** | P2 |
| **Status** | ⬜ Backend-only — no E2E spec needed (`expectedSpecs: 0`) |

**Routes:** N/A — backend-only

**API:** Huey periodic task; management command `python manage.py publish_blog_post`

**Description:** Backend safety-net for missed schedules: scans `BlogPost` rows where `publish_scheduled_for` is in the past but the post is still unpublished, then publishes them automatically (and triggers the LinkedIn auto-publish if connected). The `publish_blog_post.py` management command is the manual escape hatch for the same logic.

**Steps:**
1. Huey scheduler triggers the periodic task.
2. Task queries `BlogPost.objects.filter(published=False, publish_scheduled_for__lte=now())`.
3. For each row, the post is published and `publish_scheduled_for` is cleared.
4. If the post has a connected LinkedIn account and a non-empty summary, `auto_publish_blog_to_linkedin` is invoked.

**Known gaps:** Backend-only — covered by `backend/content/tests/tasks/test_blog_publish_guards.py` (151 lines). No E2E surface to test.

**Flow tag:** `ADMIN_BLOG_OVERDUE_DETECTION`

---

### 22.6 Coverage Index

| Flow ID | Module | Role | Priority | Status | Suggested Spec |
|---------|--------|------|----------|--------|----------------|
| `diagnostic-public-onboarding` | diagnostic | guest | P3 | ❌ Missing | `e2e/public/diagnostic-public-onboarding.spec.js` |
| `admin-proposal-document-preview` | admin | admin | P3 | ❌ Missing | extend `e2e/admin/admin-proposal-documents-manage.spec.js` |
| `admin-diagnostic-document-preview` | admin | admin | P3 | ❌ Missing | extend `e2e/admin/admin-diagnostic-email-documents.spec.js` |
| `admin-blog-publish-mode` | admin | admin | P2 | ❌ Missing | `e2e/admin/admin-blog-publish-mode.spec.js` |
| `admin-blog-overdue-detection` | admin | system | P2 | ⬜ Backend-only | N/A |
