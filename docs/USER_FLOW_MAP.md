# User Flow Map

> **Version:** 1.3.0
> **Last updated:** 2026-03-07
> **Scope:** Complete map of end-to-end user navigation flows for projectapp, organized by role.
> **Sources:** Frontend pages (`frontend/pages/`), backend API endpoints (`content/urls.py`), route rules (`nuxt.config.ts`).

---

## Table of Contents

1. [Roles](#1-roles)
2. [Conventions](#2-conventions)
3. [Shared Flows (Guest + Admin)](#3-shared-flows-guest--admin)
4. [Guest Flows](#4-guest-flows)
5. [Proposal Flows (Guest via UUID)](#5-proposal-flows-guest-via-uuid)
6. [Admin Flows](#6-admin-flows)
7. [E2E Coverage Index](#7-e2e-coverage-index)

---

## 1. Roles

| Role | Description | Auth Required |
|------|-------------|---------------|
| **Guest** | Unauthenticated visitor browsing the public site | No |
| **Admin** | Staff user managing content via the `/panel/` admin frontend | Yes (Django session) |

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

---

## 3. Shared Flows (Guest + Admin)

### FLOW: `layout-navbar-navigation`

- **Module:** layout
- **Role:** guest/admin
- **Priority:** P2
- **Routes:** All pages
- **Description:** Navigate between pages using the fixed top navbar.
- **Steps:**
  1. User sees the fixed navbar at the top of the page.
  2. User clicks a navigation link (Home, Services, Portfolio, Blog, Contact).
  3. Page navigates to the selected route.
  4. Navbar remains visible and highlights the active section.
- **Branches:**
  - [Branch A] User switches language via locale switcher → page reloads in selected locale (`/en-us/` or `/es-co/`).
  - [Branch B] User clicks WhatsApp button → external link opens.
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
- **Description:** Browse portfolio works and project showcases.
- **Steps:**
  1. User navigates to the portfolio page.
  2. Portfolio works load from API (`GET /api/portfolio_works/`).
  3. Portfolio grid renders with project cards.
  4. User views project details (images, descriptions).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-pages.spec.js`

### FLOW: `public-web-designs`

- **Module:** public
- **Role:** guest
- **Priority:** P2
- **Routes:** `/web-designs`, `/en-us/web-designs`, `/es-co/web-designs`
- **Description:** Browse web design services and examples.
- **Steps:**
  1. User navigates to the web designs page.
  2. Design data loads from API (`GET /api/designs/`).
  3. Design showcase renders.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-pages.spec.js`

### FLOW: `public-3d-animations`

- **Module:** public
- **Role:** guest
- **Priority:** P3
- **Routes:** `/3d-animations`, `/en-us/3d-animations`, `/es-co/3d-animations`
- **Description:** View 3D animation services and examples.
- **Steps:**
  1. User navigates to the 3D animations page.
  2. 3D model data loads from API (`GET /api/models3d/`).
  3. 3D animation showcase renders.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-pages.spec.js`

### FLOW: `public-hosting`

- **Module:** public
- **Role:** guest
- **Priority:** P3
- **Routes:** `/hosting`, `/en-us/hosting`, `/es-co/hosting`
- **Description:** View hosting plans and pricing.
- **Steps:**
  1. User navigates to the hosting page.
  2. Hosting plans load from API (`GET /api/hostings/`).
  3. Hosting plans render with pricing details.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-pages.spec.js`

### FLOW: `public-ecommerce-prices`

- **Module:** public
- **Role:** guest
- **Priority:** P3
- **Routes:** `/e-commerce-prices`, `/en-us/e-commerce-prices`, `/es-co/e-commerce-prices`
- **Description:** View e-commerce development pricing.
- **Steps:**
  1. User navigates to the e-commerce prices page.
  2. Product/pricing data loads from API (`GET /api/products/`).
  3. Pricing cards render.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-pages.spec.js`

### FLOW: `public-custom-software`

- **Module:** public
- **Role:** guest
- **Priority:** P3
- **Routes:** `/custom-software`, `/en-us/custom-software`, `/es-co/custom-software`
- **Description:** View custom software development services.
- **Steps:**
  1. User navigates to the custom software page.
  2. Service information renders.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-pages.spec.js`

### FLOW: `public-about-us`

- **Module:** public
- **Role:** guest
- **Priority:** P3
- **Routes:** `/about-us`, `/en-us/about-us`, `/es-co/about-us`
- **Description:** View the about us page with team and company information.
- **Steps:**
  1. User navigates to the about us page.
  2. About us content renders.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/public-pages.spec.js`

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
- **Coverage:** ❌ Missing

### FLOW: `proposal-respond`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** Client responds to (accepts/rejects) a business proposal from the ProposalClosing panel.
- **Steps:**
  1. User views the proposal and navigates to the closing panel.
  2. Accept/reject buttons visible when `proposal.status` is `sent` or `viewed`.
  3. User clicks "Acepto la propuesta" → confirmation modal opens.
  4. User confirms → API call to `POST /api/proposals/:uuid/respond/` with `decision: accepted`.
  5. Success state: "¡Propuesta aceptada!" message renders.
- **Branches:**
  - [Branch A — Accept] Client clicks accept → confirm modal → API → success emoji + message.
  - [Branch B — Reject] Client clicks "Rechazar propuesta" → reject modal (select reason + comment) → API → thank-you message.
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
- **Coverage:** ❌ Missing

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
- **Coverage:** ❌ Missing

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
- **Description:** View the list of all business proposals.
- **Steps:**
  1. Admin navigates to `/panel/proposals/`.
  2. Proposals load from API (`GET /api/proposals/`).
  3. Proposal table renders with status, client, dates.
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
- **Coverage:** ❌ Missing

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
- **Coverage:** ❌ Missing

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
- **Coverage:** ❌ Missing

### FLOW: `admin-proposal-analytics`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/:id/edit` (Analytics tab)
- **Description:** View detailed analytics for a single proposal including engagement funnel, section time heatmap, device breakdown, shared links, session history, suggested actions, and CSV export.
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
- **Coverage:** ❌ Missing

### FLOW: `admin-proposal-dashboard`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/` (Dashboard KPI section)
- **Description:** View global KPI dashboard for all proposals: total proposals, conversion rate, average time to first view, average time to response, average value by status, status distribution, top rejection reasons, monthly trends, and discount vs no-discount close rates.
- **Steps:**
  1. Admin navigates to `/panel/`.
  2. ProposalDashboard component loads data from `GET /api/proposals/dashboard/`.
  3. KPI cards render with total proposals, conversion rate, avg time metrics.
  4. Status distribution chart renders.
  5. Top rejection reasons list renders.
  6. Monthly trend data renders.
- **Coverage:** ❌ Missing

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
- **Coverage:** ❌ Missing

### FLOW: `admin-proposal-send`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/`
- **Description:** Send a proposal to a client via email.
- **Steps:**
  1. Admin views the proposal list or edit page.
  2. Admin clicks "Send" on a proposal.
  3. API call to `POST /api/proposals/:id/send/`.
  4. Email is sent to the client with the proposal link.
  5. Success feedback displays.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-send.spec.js`

### FLOW: `admin-blog-list`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/blog/`
- **Description:** View the list of all blog posts (admin view with both languages).
- **Steps:**
  1. Admin navigates to `/panel/blog/`.
  2. Blog posts load from API (`GET /api/blog/admin/`).
  3. Blog table renders with title_es, title_en, status, dates.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-list.spec.js`

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
- **Coverage:** ❌ Missing

---

## 7. E2E Coverage Index

| Flow ID | Module | Role | Priority | Coverage | E2E Spec |
|---------|--------|------|----------|----------|----------|
| `layout-navbar-navigation` | layout | guest/admin | P2 | ✅ Covered | `e2e/layout/layout-navbar.spec.js` |
| `layout-locale-switch` | layout | guest/admin | P2 | ✅ Covered | `e2e/layout/layout-locale.spec.js` |
| `layout-footer-navigation` | layout | guest/admin | P3 | ✅ Covered | `e2e/layout/layout-footer.spec.js` |
| `public-home` | public | guest | P1 | ✅ Covered | `e2e/public/public-home.spec.js` |
| `public-portfolio` | public | guest | P2 | ✅ Covered | `e2e/public/public-pages.spec.js` |
| `public-web-designs` | public | guest | P2 | ✅ Covered | `e2e/public/public-pages.spec.js` |
| `public-3d-animations` | public | guest | P3 | ✅ Covered | `e2e/public/public-pages.spec.js` |
| `public-hosting` | public | guest | P3 | ✅ Covered | `e2e/public/public-pages.spec.js` |
| `public-ecommerce-prices` | public | guest | P3 | ✅ Covered | `e2e/public/public-pages.spec.js` |
| `public-custom-software` | public | guest | P3 | ✅ Covered | `e2e/public/public-pages.spec.js` |
| `public-about-us` | public | guest | P3 | ✅ Covered | `e2e/public/public-pages.spec.js` |
| `public-landing-web-design` | public | guest | P2 | ✅ Covered | `e2e/public/public-pages.spec.js` |
| `public-contact-submit` | public | guest | P1 | ✅ Covered | `e2e/public/public-contact.spec.js` |
| `blog-list` | blog | guest | P2 | ✅ Covered | `e2e/blog/blog-list.spec.js` |
| `blog-detail` | blog | guest | P2 | ✅ Covered | `e2e/blog/blog-detail.spec.js` |
| `proposal-view` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-view.spec.js` |
| `proposal-view-navigation` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-view-navigation.spec.js` |
| `proposal-view-onboarding` | proposal | guest | P3 | ❌ Missing | — |
| `proposal-respond` | proposal | guest | P1 | ✅ Covered | `e2e/proposal/proposal-respond.spec.js` |
| `proposal-download-pdf` | proposal | guest | P2 | ✅ Covered | `e2e/proposal/proposal-pdf.spec.js` |
| `proposal-share` | proposal | guest | P2 | ❌ Missing | — |
| `proposal-engagement-tracking` | proposal | guest | P2 | ❌ Missing | — |
| `admin-login` | auth | admin | P1 | ✅ Covered | `e2e/auth/auth-admin-login.spec.js` |
| `admin-dashboard` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-dashboard.spec.js` |
| `admin-proposal-list` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-list.spec.js` |
| `admin-proposal-create` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-create.spec.js` |
| `admin-proposal-create-from-json` | admin | admin | P1 | ❌ Missing | — |
| `admin-proposal-edit` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-edit.spec.js` |
| `admin-proposal-section-edit-form` | admin | admin | P1 | ⚠️ Partial | `e2e/admin/admin-proposal-section-form.spec.js` |
| `admin-proposal-section-edit-paste` | admin | admin | P1 | ⚠️ Partial | `e2e/admin/admin-proposal-section-paste.spec.js` |
| `admin-proposal-section-reorder` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-section-reorder.spec.js` |
| `admin-proposal-functional-requirements-form` | admin | admin | P1 | ⚠️ Partial | `e2e/admin/admin-proposal-requirements.spec.js` |
| `admin-proposal-functional-requirements-paste` | admin | admin | P1 | ⚠️ Partial | `e2e/admin/admin-proposal-requirements.spec.js` |
| `admin-proposal-delete` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-proposal-delete.spec.js` |
| `admin-proposal-duplicate` | admin | admin | P2 | ❌ Missing | — |
| `admin-proposal-comment` | admin | admin | P3 | ❌ Missing | — |
| `admin-proposal-analytics` | admin | admin | P2 | ❌ Missing | — |
| `admin-proposal-dashboard` | admin | admin | P2 | ❌ Missing | — |
| `admin-mini-crm-clients` | admin | admin | P2 | ❌ Missing | — |
| `admin-proposal-send` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-proposal-send.spec.js` |
| `admin-blog-list` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-blog-list.spec.js` |
| `admin-blog-create` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-blog-create.spec.js` |
| `admin-blog-create-from-json` | admin | admin | P2 | ❌ Missing | — |
| `admin-blog-edit` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-blog-edit.spec.js` |
| `admin-blog-delete` | admin | admin | P3 | ✅ Covered | `e2e/admin/admin-blog-delete.spec.js` |

### Summary

- **Total flows:** 47 (+9 new flows: proposal-share, proposal-engagement-tracking, admin-proposal-duplicate, admin-proposal-comment, admin-proposal-analytics, admin-proposal-dashboard, admin-mini-crm-clients, admin-blog-create-from-json)
- **P1 (Critical):** 16
- **P2 (High):** 22
- **P3 (Medium):** 9
- **Covered (full):** 30 (64%)
- **Partial:** 4 (9%) — section-edit-form, section-edit-paste, requirements-form, requirements-paste
- **Missing:** 13 (28%) — proposal-view-onboarding, proposal-share, proposal-engagement-tracking, admin-proposal-create-from-json, admin-proposal-duplicate, admin-proposal-comment, admin-proposal-analytics, admin-proposal-dashboard, admin-mini-crm-clients, admin-blog-create-from-json, +3 more

### Unit Test Coverage

| Test File | Layer | Tests | Scope |
|-----------|-------|-------|-------|
| `test/components/SectionEditor.test.js` | Frontend unit | 97 | All 12 section types: formToJson, buildFormFromJson, round-trips, formToReadableText, buildSavePayload, edge cases |
| `test/composables/useProposalTracking.test.js` | Frontend unit | — | Engagement tracking composable |
| `test/stores/proposals.test.js` | Frontend unit | — | Proposal store actions including analytics, dashboard, clients, share, duplicate |
| `content/tests/views/test_proposal_views.py` | Backend view | 102 | Full proposal API: CRUD, respond, track, analytics, dashboard, clients, share, duplicate, comment, CSV |
| `content/tests/views/test_section_update_views.py` | Backend view | 22 | PATCH per section type + paste mode + group paste |
| `content/tests/models/test_section_content_json.py` | Backend model | ~40 | DB round-trip for all 12 types |
