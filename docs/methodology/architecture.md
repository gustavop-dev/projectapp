# Architecture — ProjectApp

## 1. System Overview

```mermaid
flowchart TB
    subgraph Internet
        Client[Client Browser]
    end

    subgraph Production["Production Server (Ubuntu)"]
        Nginx["Nginx (SSL termination)"]
        Gunicorn["Gunicorn (2 workers)"]
        Django["Django 5 (settings_prod)"]
        Redis["Redis :6379/5"]
        Huey["Huey Worker"]
        MySQL["MySQL 8"]

        Nginx -->|unix socket| Gunicorn
        Gunicorn --> Django
        Django -->|ORM| MySQL
        Django -->|enqueue| Redis
        Redis -->|dequeue| Huey
        Huey -->|import models/services| Django
    end

    Client -->|HTTPS| Nginx
    Nginx -->|/static/| StaticFiles["backend/staticfiles/"]
    Nginx -->|/media/| MediaFiles["backend/media/"]

    subgraph ExternalServices["External Services"]
        SMTP["GoDaddy SMTP :465"]
        WhatsApp["CallMeBot API"]
        GTM["Google Tag Manager"]
        GA["Google Analytics"]
        FB["Facebook Pixel"]
        Clarity["Microsoft Clarity"]
        Cal["Cal.com"]
    end

    Django -->|email| SMTP
    Django -->|notifications| WhatsApp
    Client -->|tracking| GTM
    Client -->|tracking| GA
    Client -->|tracking| FB
    Client -->|tracking| Clarity
    Client -->|booking| Cal
```

---

## 2. Development Architecture

```mermaid
flowchart LR
    subgraph DevBrowser["Developer Browser"]
        NuxtDev["http://localhost:3000"]
    end

    subgraph NuxtServer["Nuxt Dev Server :3000"]
        NitroProxy["Nitro Dev Proxy"]
    end

    subgraph DjangoServer["Django Dev Server :8000"]
        DjAPI["/api/* → DRF Views"]
        DjAdmin["/admin/* → Django Admin"]
        DjStatic["/static/ → Static Files"]
        DjMedia["/media/ → Media Files"]
    end

    NuxtDev --> NuxtServer
    NitroProxy -->|/api/*| DjAPI
    NitroProxy -->|/admin/*| DjAdmin
    NitroProxy -->|/static/*| DjStatic
    NitroProxy -->|/media/*| DjMedia
```

---

## 3. Request Flow

```mermaid
flowchart TD
    Request[Incoming Request] --> Nginx

    Nginx -->|/static/| FS1[Filesystem: staticfiles/]
    Nginx -->|/media/| FS2[Filesystem: media/]
    Nginx -->|everything else| Gunicorn

    Gunicorn --> Django
    Django --> URLRouter{URL Router}

    URLRouter -->|/api/health/| HealthCheck
    URLRouter -->|/admin/| DjangoAdmin

    URLRouter -->|/api/*| ContentURLs["content.urls (81 patterns)"]
    URLRouter -->|/api/auth/*<br>/api/platform/*| AccountsURLs["accounts.urls (48 patterns)"]
    URLRouter -->|/sitemap.xml| Sitemap
    URLRouter -->|/*| ServeNuxt["serve_nuxt (catch-all)"]

    AccountsURLs --> AuthViews["Auth Views (login, verify, refresh)"]
    AccountsURLs --> PlatformViews["Platform Views (projects, clients, kanban)"]

    ContentURLs --> ProposalViews["Proposal Views (public + admin)"]
    ContentURLs --> BlogViews["Blog Views (public + admin)"]
    ContentURLs --> PortfolioViews["Portfolio Views (public + admin)"]
    ContentURLs --> ContactViews["Contact Views"]
    ContentURLs --> EmailTemplateViews["Email Template Views"]
```

---

## 4. Data Model

### 4.1 Model Inventory

```mermaid
erDiagram
    BusinessProposal ||--o{ ProposalSection : "has sections"
    BusinessProposal ||--o{ ProposalAlert : "has alerts"
    BusinessProposal ||--o{ ProposalViewEvent : "has view events"
    BusinessProposal ||--o{ ProposalChangeLog : "has change logs"
    BusinessProposal ||--o{ ProposalShareLink : "has share links"
    BusinessProposal ||--o{ EmailLog : "has email logs"
    BusinessProposal ||--o{ ProposalRequirementGroup : "has requirement groups"
    ProposalRequirementGroup ||--o{ ProposalRequirementItem : "has items"
    ProposalViewEvent ||--o{ ProposalSectionView : "has section views"
    Document }o--o{ UserProfile : "created by (optional)"

    UserProfile ||--o{ Project : "owns projects"
    UserProfile ||--o{ VerificationCode : "has codes"
    Project ||--o{ Requirement : "has requirements"
    Requirement ||--o{ RequirementComment : "has comments"
    Requirement ||--o{ RequirementHistory : "has history"
```

### 4.2 Model Details

| Model | Purpose | Key Fields |
|-------|---------|------------|
| **BusinessProposal** | Core proposal entity | uuid, title, client_name, client_email, status, total_investment, currency, language, expires_at, view_count, cached_heat_score |
| **ProposalSection** | Individual section within a proposal | proposal_fk, section_type (12 types), title, order, is_enabled, content_json, is_wide_panel |
| **ProposalRequirementGroup** | Functional requirements group | proposal_fk, group_id, title, description, order |
| **ProposalRequirementItem** | Individual requirement item | group_fk, name, description, icon |
| **ProposalAlert** | Manual/auto alerts for sellers | proposal_fk, alert_type (12 types), message, alert_date, priority, is_dismissed |
| **ProposalViewEvent** | Each client page-load | proposal_fk, session_id, ip_address, user_agent, view_mode |
| **ProposalSectionView** | Per-section time tracking | view_event_fk, section_type, time_spent_seconds, entered_at, view_mode |
| **ProposalChangeLog** | Full audit trail | proposal_fk, change_type (20 types), field_name, old_value, new_value |
| **ProposalShareLink** | Multi-stakeholder sharing | proposal_fk, uuid, shared_by_name, recipient_name, view_count |
| **ProposalDefaultConfig** | Default section templates per language | language (unique), sections_json |
| **EmailTemplateConfig** | Admin-editable email content | template_key (unique), content_overrides, is_active |
| **EmailLog** | Email deliverability tracking | proposal_fk, template_key, recipient, status, error_message |
| **Contact** | Contact form submissions | email, phone_number, subject, message, budget |
| **PortfolioWork** | Portfolio case studies | title_en/es, slug, cover_image, project_url, content_json_en/es, SEO fields |
| **BlogPost** | Blog articles | title_en/es, slug, cover_image, excerpt, content_json/html, category, author, SEO fields |
| **Document** | Generic branded PDF document | uuid, title, slug, status (draft/published/archived), language (es/en), cover_type (generic/none/proposal), content_json, created_at |
| **UserProfile** | Platform user (extends Django User) | user_fk, role (admin/client), company_name, phone, avatar, onboarding_completed, is_active |
| **VerificationCode** | OTP codes for login | user_fk, code, expires_at, is_used |
| **Project** | Client projects in platform | owner_fk, title, description, status (active/completed/archived), created_at |
| **Requirement** | Kanban board items | project_fk, title, description, status (backlog/in_progress/done), priority, assignee, order |
| **RequirementComment** | Comments on requirements | requirement_fk, author_fk, text, created_at |
| **RequirementHistory** | Audit trail for requirements | requirement_fk, field_name, old_value, new_value, changed_by |

---

## 5. Service Layer

```mermaid
flowchart TD
    Views["DRF Views (FBV)"] --> PS["ProposalService"]
    Views --> PES["ProposalEmailService"]
    Views --> PPDF["ProposalPdfService"]
    Views --> ETR["EmailTemplateRegistry"]
    Views --> DPS["DocumentPdfService"]

    PS -->|CRUD, lifecycle, analytics| Models["Django Models"]
    PES -->|send emails| SMTP["Django Email Backend"]
    PES -->|get content| ETR
    PPDF -->|generate| ReportLab["ReportLab PDF"]
    PPDF -->|shared utils| PU["PdfUtils"]
    DPS -->|generate| ReportLab
    DPS -->|shared utils| PU
    DPS -->|parse markdown| MP["MarkdownParser"]
    ETR -->|read overrides| ETC["EmailTemplateConfig model"]

    HueyTasks["Huey Tasks"] --> PES
    HueyTasks --> Models
```

### Service Responsibilities

| Service | File Size | Responsibilities |
|---------|-----------|-----------------|
| **ProposalService** | 132K | Proposal CRUD, section management, default sections, analytics computation, engagement scoring, dashboard aggregation, CSV export, scorecard |
| **ProposalEmailService** | 60K | All email sending: proposal sent, reminders, urgency, abandonment, revisit alerts, stakeholder alerts, engagement decay, post-expiration |
| **ProposalPdfService** | 72K | PDF generation with ReportLab: all 12 section types rendered to PDF |
| **EmailTemplateRegistry** | 38K | Centralized registry of all email templates with default content, admin-editable overrides, preview rendering |
| **PdfUtils** | 36K | Shared PDF rendering utilities (fonts, colors, layout helpers) used by ProposalPdfService and DocumentPdfService |
| **DocumentPdfService** | 20K | PDF generation for generic branded Documents with template-based rendering |
| **MarkdownParser** | 9K | Parses markdown content for Document PDF rendering |

---

## 6. Frontend Architecture

### 6.1 Page Routing

```mermaid
flowchart TD
    subgraph Public["Public Pages (SSR)"]
        Home["/"]
        Landing1["/landing-web-design"]
        Landing2["/landing-software"]
        Landing3["/landing-apps"]
        About["/about-us"]
        Portfolio["/portfolio-works"]
        PortfolioDetail["/portfolio-works/:slug"]
        Blog["/blog"]
        BlogDetail["/blog/:slug"]
        Contact["/contact"]
        ContactSuccess["/contact-success"]
    end

    subgraph SPA["SPA Pages"]
        Proposal["/proposal/:uuid"]
        Panel["/panel/ (Dashboard)"]
        PanelLogin["/panel/login"]
        ProposalsList["/panel/proposals"]
        ProposalCreate["/panel/proposals/create"]
        ProposalEdit["/panel/proposals/:id/edit"]
        ProposalDefaults["/panel/proposals/defaults"]
        EmailTemplates["/panel/proposals/email-templates"]
        EmailDeliverability["/panel/proposals/email-deliverability"]
        BlogAdmin["/panel/blog"]
        BlogCreate["/panel/blog/create"]
        BlogEdit["/panel/blog/:id/edit"]
        BlogCalendar["/panel/blog/calendar"]
        PortfolioAdmin["/panel/portfolio"]
        PortfolioCreate["/panel/portfolio/create"]
        PortfolioEdit["/panel/portfolio/:id/edit"]
        Clients["/panel/clients"]
        Admins["/panel/admins"]
        DocumentsAdmin["/panel/documents"]
        DocumentCreate["/panel/documents/create"]
        DocumentEdit["/panel/documents/:id/edit"]
    end

    subgraph Platform["Platform Pages (JWT Auth)"]
        PlatformLogin["/platform/login"]
        PlatformVerify["/platform/verify"]
        PlatformProfile["/platform/complete-profile"]
        PlatformDashboard["/platform/dashboard"]
        PlatformBoard["/platform/board"]
        PlatformProjects["/platform/projects"]
        PlatformProjectDetail["/platform/projects/:id"]
        PlatformProjectBoard["/platform/projects/:id/board"]
        PlatformProjectBugs["/platform/projects/:id/bugs"]
        PlatformProjectChanges["/platform/projects/:id/changes"]
        PlatformProjectDeliverables["/platform/projects/:id/deliverables"]
        PlatformProjectPayments["/platform/projects/:id/payments"]
        PlatformClients["/platform/clients"]
        PlatformClientDetail["/platform/clients/:id"]
        PlatformBugs["/platform/bugs"]
        PlatformChanges["/platform/changes"]
        PlatformDeliverables["/platform/deliverables"]
        PlatformNotifications["/platform/notifications"]
        PlatformPayments["/platform/payments"]
        PlatformProfilePage["/platform/profile"]
    end

    Panel -->|middleware: admin-auth| AuthCheck["/api/auth/check/"]
    PlatformDashboard -->|middleware: platform-auth| JWTCheck["JWT validation"]
```

### 6.2 Store Architecture

```mermaid
flowchart LR
    subgraph Stores["Pinia Stores (Options API) — 16 total"]
        ProposalStore["proposals.js"]
        BlogStore["blog.js"]
        PortfolioStore["portfolio_works.js"]
        ContactStore["contacts.js"]
        LanguageStore["language.js"]
        DocumentStore["documents.js"]
        PanelAdmins["panel_admins.js"]
        PlatformAuth["platform-auth.js"]
        PlatformClients["platform-clients.js"]
        PlatformProjects["platform-projects.js"]
        PlatformRequirements["platform-requirements.js"]
        PlatformBugReports["platform-bug-reports.js"]
        PlatformChangeRequests["platform-change-requests.js"]
        PlatformDeliverables["platform-deliverables.js"]
        PlatformNotifications["platform-notifications.js"]
        PlatformPayments["platform-payments.js"]
    end

    subgraph HTTP["HTTP Service"]
        RequestHTTP["stores/services/request_http"]
    end

    ProposalStore --> RequestHTTP
    BlogStore --> RequestHTTP
    PortfolioStore --> RequestHTTP
    ContactStore --> RequestHTTP
    DocumentStore --> RequestHTTP
    PanelAdmins --> RequestHTTP
    PlatformAuth --> PlatformHTTP["composables/usePlatformApi"]
    PlatformClients --> PlatformHTTP
    PlatformProjects --> PlatformHTTP
    PlatformRequirements --> PlatformHTTP
    PlatformBugReports --> PlatformHTTP
    PlatformChangeRequests --> PlatformHTTP
    PlatformDeliverables --> PlatformHTTP
    PlatformNotifications --> PlatformHTTP
    PlatformPayments --> PlatformHTTP

    RequestHTTP -->|axios| API["/api/*"]
    PlatformHTTP -->|axios + JWT| API
```

### 6.3 Proposal Client View Architecture

```mermaid
flowchart TD
    ProposalPage["pages/proposal/[uuid].vue"]
    ProposalPage --> ProposalStore
    ProposalPage --> useProposalNavigation
    ProposalPage --> useExpirationTimer
    ProposalPage --> useProposalTracking
    ProposalPage --> useSectionAnimations
    ProposalPage --> GSAP["GSAP ScrollTrigger (horizontal scroll)"]

    ProposalPage --> Sections["12 Section Components"]
    Sections --> Greeting
    Sections --> ExecutiveSummary
    Sections --> ContextDiagnostic
    Sections --> ConversionStrategy
    Sections --> DesignUX
    Sections --> CreativeSupport
    Sections --> DevelopmentStages
    Sections --> FunctionalRequirements
    Sections --> Timeline
    Sections --> Investment
    Sections --> FinalNote
    Sections --> NextSteps

    ProposalPage --> Overlays["Overlay Components"]
    Overlays --> ProposalIndex
    Overlays --> SectionCounter
    Overlays --> ExpirationBadge
    Overlays --> PdfDownloadButton
    Overlays --> ShareProposalButton
    Overlays --> ProposalExpired
```

---

## 7. Async Task Architecture

```mermaid
flowchart TD
    subgraph Triggers["Task Triggers"]
        SendAction["Admin: Send Proposal"]
        DailyCron["Daily Cron (midnight)"]
        TrackEndpoint["Client: Track Engagement"]
    end

    subgraph HueyTasks["Huey Tasks"]
        SendReminder["send_proposal_reminder"]
        SendUrgency["send_urgency_reminder"]
        ExpireStale["expire_stale_proposals (periodic)"]
        SendAbandon["send_abandonment_email"]
        SendRevisit["send_revisit_alert"]
        SendInvestment["send_investment_interest_email"]
        SendStakeholder["send_stakeholder_alert"]
        SendPostExpiry["send_post_expiration_alert"]
        SendEngagementDecay["send_engagement_decay_alert"]
        SendCalcFollowup["send_calculator_followup"]
        RefreshHeatScores["refresh_all_heat_scores (periodic)"]
        AutoArchive["auto_archive_stale_proposals (periodic)"]
    end

    SendAction -->|schedule delay| SendReminder
    SendAction -->|schedule delay| SendUrgency
    DailyCron --> ExpireStale
    DailyCron --> RefreshHeatScores
    DailyCron --> AutoArchive
    TrackEndpoint -->|conditional| SendAbandon
    TrackEndpoint -->|conditional| SendRevisit
    TrackEndpoint -->|conditional| SendInvestment
    TrackEndpoint -->|conditional| SendStakeholder
    TrackEndpoint -->|conditional| SendPostExpiry
    TrackEndpoint -->|conditional| SendEngagementDecay
    TrackEndpoint -->|conditional| SendCalcFollowup
```

---

## 8. Deployment Architecture

```
Client (HTTPS)
    │
    ▼
Nginx (SSL termination, Let's Encrypt)
    ├── /static/  → backend/staticfiles/
    ├── /media/   → backend/media/
    └── /*        → unix:/run/projectapp.sock
                        │
                        ▼
                   Gunicorn (2 workers)
                        │
                        ▼
                   Django (settings_prod)
                   ├── /api/*     → DRF views
                   ├── /admin/*   → Django admin
                   └── /*         → serve_nuxt (pre-rendered Nuxt pages)

Systemd Services:
  - projectapp.service  → Gunicorn (via projectapp.socket)
  - projectapp-huey     → Huey worker

Redis:
  - redis://localhost:6379/5  → Huey task queue

MySQL:
  - localhost:3306  → projectapp_db
```

### Production Build Flow

```mermaid
flowchart LR
    NuxtBuild["npm run build:django"]
    NuxtBuild -->|generates| StaticFrontend["backend/static/frontend/"]
    CollectStatic["python manage.py collectstatic"]
    StaticFrontend --> CollectStatic
    CollectStatic -->|copies to| StaticFiles["backend/staticfiles/"]
    Nginx -->|serves| StaticFiles
```

---

## 9. Current Workflow

### Proposal Creation → Client View → Close

1. Admin creates proposal via `/panel/proposals/create` (or JSON import)
2. 12 sections auto-generated with default content per language
3. Admin edits sections via `/panel/proposals/{id}/edit`
4. Admin clicks "Send" → email sent to client + admin notification + reminders scheduled
5. Client opens unique link `/proposal/{uuid}`
6. Frontend loads GSAP horizontal-scroll experience with all enabled sections
7. Engagement tracked: view events, section time, session ID
8. Automated emails triggered based on behavior (reminder, urgency, abandonment, etc.)
9. Client responds: accept / reject (with reason) / negotiate / comment
10. Admin monitors via dashboard, alerts, analytics, scorecard