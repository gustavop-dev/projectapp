---
trigger: model_decision
description: Project intelligence and lessons learned. Reference for project-specific patterns, preferences, and key insights discovered during development.
---

# Lessons Learned — ProjectApp

This file captures important patterns, preferences, and project intelligence that help work more effectively with this codebase. Updated as new insights are discovered.

---

## 1. Architecture Patterns

### Content Storage: Structured JSON over CMS
- Proposal sections, portfolio works, and blog posts use Django `JSONField` for content
- Each proposal section's `content_json` maps directly to a Vue component's props schema
- Blog supports dual format: structured JSON (preferred) with HTML fallback via `v-html`
- This avoids the need for a full CMS while keeping content rich and structured

### Single Django App: `content`
- All models, views, serializers, and services live in the `content` app
- This works for now but may need splitting if scope grows significantly
- Models are already split into individual files under `content/models/`

### Service Layer Pattern
- Business logic lives in `content/services/`, not in views
- Views are thin FBV wrappers that call service methods
- Services (30 modules): `ProposalService`, `ProposalEmailService`, `ProposalPdfService`, `ContractPdfService`, `EmailTemplateRegistry`, `PdfUtils`, `DocumentPdfService`, `MarkdownParser`, `CollectionAccountService`, `CollectionAccountPdfService`, `TechnicalDocumentPdf`, `TechnicalDocumentFilter`, `PlatformOnboardingPdf`, `LinkedInService`, `DiagnosticService`, `DiagnosticEmailService`, `DiagnosticPdfService`, `DiagnosticDocumentsService`, `AccountingService`, `AccountingExportService`, `AccountingEmailService`, `AccountingCardReminderService`
- MCP tool servers live in `content/mcp/` (`protocol`, `actor`, `tools` + per-domain connector modules), not in `services/` — they wrap existing service/ORM calls behind a token-authed JSON-RPC surface for claude.ai

### External API Integration Pattern (LinkedIn)
- External OAuth integrations follow the singleton model + service module pattern
- `LinkedInToken` (singleton, pk=1) stores Fernet-encrypted access/refresh tokens in the DB; encryption key from `LINKEDIN_ENCRYPTION_KEY` env var
- `linkedin_service.py` encapsulates the full OAuth flow + API calls — views stay thin
- Follow this pattern for any future third-party OAuth integration (e.g., Twitter/X, Instagram)

### PDF Generation Layer
- `pdf_utils.py` is the shared utility layer — fonts, colors, layout helpers, reusable drawing functions
- `proposal_pdf_service.py`, `contract_pdf_service.py`, and `document_pdf_service.py` all depend on `PdfUtils`
- Never duplicate PDF primitives across services — add to `pdf_utils.py` and import from there
- All PDF services use ReportLab directly (no external PDF library abstraction)

---

## 2. Code Style & Conventions

### Backend: Function-Based Views (FBV)
- **All** DRF views use `@api_view` decorators, not class-based views
- Never convert to CBV unless explicitly requested
- The proposal views module is very large — be careful with edits and prefer localized changes

### Frontend: Pinia Options API
- **All** Pinia stores use Options API pattern: `{ state, getters, actions }`
- Do NOT use Composition API (`setup()`) style for stores
- HTTP requests go through `stores/services/request_http` centralized service

### Bilingual Content Pattern
- Models have paired fields: `title_en`/`title_es`, `content_json_en`/`content_json_es`, etc.
- Frontend reads the appropriate field based on current locale
- Proposals have a `language` field (`es`/`en`) that determines which default content to use

### Naming Conventions
- Backend: snake_case for everything (Python standard)
- Frontend stores: snake_case file names (`portfolio_works.js`, `proposals.js`)
- Frontend components: PascalCase (`BusinessProposal/Greeting.vue`)
- Frontend composables: camelCase with `use` prefix (`useExpirationTimer.js`)

---

## 3. Development Workflow

### Backend Commands Always Need venv
```bash
source venv/bin/activate && <command>
# or
venv/bin/python <command>
```

### Huey Immediate Mode in Development
- When `DJANGO_ENV != 'production'`, Huey tasks execute synchronously
- No need to run Redis or Huey worker for development
- Tasks still need to be importable and functional

### Frontend Dev Proxy
- Nuxt proxies `/api`, `/admin`, `/static`, `/media` to Django at `127.0.0.1:8000`
- Both servers must be running simultaneously for full functionality
- In production, everything goes through Django (no separate Nuxt server)

### Test Execution Rules
- Never run the full test suite — always specify files
- Backend: `pytest backend/content/tests/<specific_file> -v`
- Frontend: `npm test -- <specific_file>`
- E2E: max 2 files per `npx playwright test` invocation
- Use `E2E_REUSE_SERVER=1` when dev server is already running

---

## 4. Production Deployment

### Build Flow
1. Frontend: `npm run build:django` → generates `backend/static/frontend/`
2. Backend: `python manage.py collectstatic` → copies to `backend/staticfiles/`
3. Restart: `sudo systemctl restart projectapp && sudo systemctl restart projectapp-huey`

### Django Serves Nuxt Pages
- The `serve_nuxt` catch-all view in `projectapp/views.py` serves pre-rendered Nuxt pages
- This is the LAST URL pattern — all other routes take priority
- CDN URL for assets configurable via `NUXT_APP_CDN_URL`

---

## 5. Email System

### Template Registry Pattern
- All emails defined in `EmailTemplateRegistry` with default content
- Admin can override content via `EmailTemplateConfig` model
- Admin can disable specific emails via `is_active` flag
- Preview rendering available for all templates

### 24h Cooldown Rule
- `last_automated_email_at` field on `BusinessProposal` tracks last automated email
- All automated email tasks check this before sending
- Manual sends (admin clicks "Send") bypass the cooldown

### Composed Email Pattern (Branded + Proposal)
- Shared `_send_composed_email()` method reads templates from registry (not hardcoded paths)
- `send_branded_email()` — thin wrapper, no side effects beyond email + log
- `send_proposal_email()` — creates `ProposalChangeLog(EMAIL_SENT)` + updates `last_activity_at`
- Rate limited: 1 email per minute per template_key per proposal via `EmailLog` query
- `EmailLog.metadata` JSONField stores greeting, sections, footer, attachment_names for history
- View layer: shared `_parse_composed_email()` returns `(data, error_response)` tuple; 3 handler helpers (`_send_composed_email_view`, `_get_email_defaults_view`, `_list_emails_view`) serve 6 thin public views
- Frontend: single `ProposalEmailsTab.vue` with `mode` prop ('branded'/'proposal') + computed `basePath`

### Automations Pause
- `automations_paused` flag on `BusinessProposal` stops all automated emails
- Each Huey task checks this flag early and returns if paused

### Structured `email_delivery` Result, Not Silent Bool
- `ProposalEmailService.send_proposal_to_client` returns `{ ok, reason, detail }` (built via the module-local `_delivery()` helper). Reasons: `sent`, `placeholder_email`, `template_disabled`, `send_failed`, `unexpected_error`.
- `ProposalService.send_proposal`, `resend_proposal`, and `_send_initial_email` propagate this dict — they never swallow failures into `logger.exception` alone.
- The admin views (`send_proposal`, `update_proposal_status`, `resend_proposal`) attach `email_delivery` to the response via the local `_proposal_admin_response()` helper in `views/proposal.py`. The status change still returns 200 (status DID change) but the body tells the truth about the email.
- Frontend stores read `response.data.email_delivery` and the panel toast surfaces the failure reason instead of a generic success. If you add a new email side effect, follow this pattern — never return a bool that the view ignores.

### Defense-in-Depth on Status Transitions That Trigger Emails
- Multiple UI paths can trigger the same transition (`draft → sent` exists in: dedicated "Enviar al Cliente" button, actions modal, and the inline status dropdown).
- Every endpoint that performs the transition must trigger the same side effects. `update_proposal_status` delegates `draft → sent` to `ProposalService.send_proposal` rather than re-implementing the save+email+schedule. If a future endpoint exposes the same transition, route it through the service — never duplicate the save-only path.

---

## 6. Proposal System Specifics

### Proposal creation automation must preserve runtime decisions
- Generate from `ProposalService.get_default_sections()`, then validate through `ProposalFromJSONSerializer` and create through `build_proposal_from_json`; hardcoded templates miss admin-edited defaults.
- `BusinessProposal.total_investment` is the base. The effective client total adds each selected calculator module after per-module rounding, so a quoted all-inclusive total must first be converted into a base that reproduces it.
- Persist `selected_modules` and a `calc_confirmed` change log even when the confirmed selection is empty; otherwise default-selected modules can silently re-enter scope.
- Hosting numbers live on `BusinessProposal`, while `investment.hostingPlan` is presentation. Setting only the JSON is insufficient because public/PDF serializers normalize from the model.

### Section Types Are Fixed
- 18 section types defined in `ProposalSection.SectionType` choices
- Each maps to a specific Vue component in `components/BusinessProposal/`
- Unique together constraint: `(proposal, section_type)` — one of each per proposal

### Heat Score (1-10)
- Pre-computed and cached in `cached_heat_score` field
- Updated by tracking endpoint and periodic task (`refresh_all_heat_scores`)
- Based on: view count, section time, recency, engagement patterns

### Change Log Types
- 20+ change types in `ProposalChangeLog.ChangeType`
- Includes: created, updated, sent, viewed, accepted, rejected, resent, expired, duplicated, commented, negotiating, reengagement, call, meeting, followup, note, calc_confirmed, calc_abandoned, auto_archived, status_change, cond_accepted, calc_followup, email_sent, req_clicked

---

## 7. Contract System Patterns

### Contract PDF Generation
- `ContractPdfService` generates PDFs via ReportLab using Helvetica font for consistent cross-platform rendering
- **Draft mode**: `is_draft=True` suppresses the contractor signature block — use for review cycles
- **Final mode**: includes full contractor signature block with name, date, and signature line
- Clickable Table of Contents generated at PDF start with anchor links to each section heading
- Template parameter substitution: `{{client_name}}`, `{{company_name}}`, etc. replaced at render time using `CompanySettings` + proposal data

### Data Model Entity Patterns
- `DataModelEntity` stores a reusable JSON schema (field definitions, types, constraints) independent of any project
- `ProjectDataModelEntity` associates an entity with a project and optionally overrides its schema
- Technical requirements sync: syncs project `Requirement` entries from the linked data model entity's schema fields
- JSON upload via API endpoint allows bulk creation of entity schemas from external tools
- Platform UI: `/platform/projects/:id/data-model` tab shows linked entities and allows sync actions

## 8. Platform / Accounts App Patterns

### Dual Auth Strategy
- `/panel/` admin uses Django session + CSRF (same as before)
- `/platform/` uses JWT via SimpleJWT (access + refresh tokens)
- Platform stores use `composables/usePlatformApi.js` (axios instance with JWT interceptors)
- Content stores use `stores/services/request_http` (axios with CSRF)
- **Never mix these two HTTP clients**

### Platform Store Naming
- Platform stores use kebab-case: `platform-auth.js`, `platform-clients.js`, `platform-projects.js`, `platform-requirements.js`
- Content stores use snake_case: `portfolio_works.js`, `proposals.js`

### Accounts Services (19 modules)
- `services/onboarding.py` — profile completion flow
- `services/tokens.py` — JWT token generation/refresh
- `services/verification.py` — OTP code generation and validation (login + email validation purposes)
- `services/password_reset.py` — password-reset OTP flow
- `services/client_flow_notifications.py` — best-effort team milestone alerts (first login / email validated / document signed); never raises
- `services/technical_requirements_sync.py` — mirrors accepted-proposal FR groups into `ProjectScopeItem` + `Requirement` rows (respects `content_overridden`)
- `services/hosting_billing.py` + `services/payment_notifications.py` + `services/project_phases.py` — hosting multi-phase billing/proration + payment alerts
- `services/impersonation.py` — panel→platform admin impersonation exchange
- `services/image_utils.py` — avatar processing
- `services/credential_cipher.py` — Fernet encrypt/decrypt for project admin passwords; `_get_cipher()` is `@lru_cache(maxsize=1)` so the key is read once; `PROJECT_ACCESS_CIPHER_KEY` env var; call `_get_cipher.cache_clear()` in tests after setting the env var

### Encrypted Credential Pattern (Quick Access)
- Admin passwords stored as Fernet ciphertexts in `Project.admin_password_encrypted` (TextField)
- Plain-text password is never stored; always encrypt before saving (`encrypt_password()`)
- Django admin form uses `PasswordInput(render_value=False)` — password field always blank on edit; leave empty to keep existing
- `ProjectDetailSerializer.to_representation()` blanks all admin-only fields in a single pass for non-admin — avoids N × `is_admin` checks from multiple `SerializerMethodField` getters
- The dedicated `GET /api/accounts/projects/access/` endpoint uses `IsAdminRole` permission class (same as all other admin-only views in `accounts/views.py`); returns decrypted passwords only to admin
- Frontend: password never persisted in store or localStorage; held in ephemeral Vue ref; `revealed` reactive object tracks per-card reveal state; `flashTimer` must be cleared in `onUnmounted`

### Platform Layout
- `layouts/platform.vue` with collapsible sidebar, mobile drawer, theme toggle
- Role-based navigation: admin sees all, client sees own projects only
- Dark mode support via `usePlatformTheme` composable

---

## 9. Testing Insights

### Backend conftest.py
- Custom coverage report with Unicode progress bars replaces default pytest-cov output
- `api_client` fixture provides unauthenticated DRF APIClient
- Content tests have their own `conftest.py` with model-specific fixtures

### E2E Flow Definitions
- Every navigation flow must be registered in `docs/USER_FLOW_MAP.md` and `frontend/e2e/flow-definitions.json`
- E2E tests must reflect real user integrations
- Follow quality standards from `docs/TESTING_QUALITY_STANDARDS.md`

### CI Sharding
- Playwright E2E tests are sharded into 5 parallel jobs
- Blob reports are merged after all shards complete
- Test quality gate runs after all test suites pass

### Known Test Issues
- `usePlatformApi.test.js` has 4 failing tests due to `window.location.href` assertions in JSDOM
- JSDOM doesn't support real navigation; `window.location.href` stays as `http://localhost/` after assignment
- Fix: use `delete window.location` + `Object.defineProperty` or mock `window.location` properly

### Playwright + Nuxt Dev Server Patterns
- **Never use `networkidle`** with Vite/Nuxt dev server — HMR WebSocket keeps connection alive, causing infinite hang
- Use `{ waitUntil: 'domcontentloaded' }` in `page.goto()` + explicit element waits (`getByRole('heading').waitFor()`)
- **Always add `test.setTimeout(60_000)`** to describe blocks for SPA routes — first visit triggers Vite on-demand compilation
- **Strict mode violations** are common when sidebar navigation duplicates page content text. Fix patterns:
  - Scope to `page.locator('main')` for page-specific content
  - Use `getByRole('heading', { name: '...' })` instead of `getByText('...')`
  - Use `{ exact: true }` when substring matching causes ambiguity (e.g., 'Activo' vs 'Activos')
- **i18n prefix strategy** adds locale prefix to all `<NuxtLink>` hrefs — use regex in `toHaveAttribute('href', /\/platform\/...$/)`
- **`<label>` without `for` attribute**: `getByLabel()` won't work. Use `page.locator('input[type="date"]')` or `page.locator('select').first()`
- **HTML5 validation bypass**: For testing custom validators, add `novalidate` via `page.evaluate(() => document.querySelector('form').setAttribute('novalidate', ''))`
- **Port conflicts**: Use `E2E_PORT=3001 E2E_REUSE_SERVER=1` when port 3000 is occupied

---

## 10. Cross-Language Shared Logic

### Technical Fragment Content Check (Python ↔ JavaScript)
- `_technical_fragment_has_content()` in `backend/content/views/proposal.py` and `technicalFragmentHasContent()` in `frontend/utils/technicalProposalPanels.js` implement the **same logic** in two languages
- Both determine whether a technical document fragment has real content based on the `content_json` structure
- **If the technical document schema changes** (new fragments, renamed keys, new fields), **both files must be updated together**
- The Python version is used by the analytics funnel to decide which fragments to show; the JS version is used by the client-facing proposal viewer to decide which panels to render

### Stage Time Formatter (Python ↔ JavaScript)
- `ProposalStageTracker.format_remaining_time(days)` in `backend/content/services/proposal_stage_tracker.py` and `useStageStatus.formatRemainingTime(days)` in `frontend/composables/useStageStatus.js` implement the **same** Spanish duration formatter (`"hoy"`, `"1 día"`, `"1 semana 5 días"`, `"2 semanas"`)
- Used by the warning + overdue email subjects on the backend AND the badge labels in the Cronograma admin tab on the frontend
- Both have parallel test suites covering the same case table (0, 1, 2, 6, 7, 8, 12, 14, 15, 21, -12 days). Update both test suites together if you change the format.

---

## 11. Pinia Reactivity (Vue 3 + Options API stores)

### In-place mutation, not spread + reassign

When updating nested arrays inside `currentProposal` (or any other top-level state), **mutate by index** — do not create a new array and reassign the parent:

```js
// ✅ Correct — matches the established pattern in proposals.js
const idx = this.currentProposal.sections.findIndex((s) => s.id === sectionId);
if (idx !== -1) {
  this.currentProposal.sections[idx] = response.data;
}

// ❌ Wrong — silently fails to propagate through computed → prop chains
this.currentProposal = {
  ...this.currentProposal,
  sections: this.currentProposal.sections.map((s) =>
    s.id === sectionId ? response.data : s,
  ),
};
```

**Why**: Components that read via `computed(() => store.currentProposal)` track Vue's reactivity through the computed dependency. The spread+reassign pattern creates a new object reference at the parent level, but the chain through `props.proposal.project_stages` doesn't always re-fire reliably (especially with deep nested arrays). In-place index assignment works because Vue 3's `reactive()` tracks individual array indices.

**Established sites to mirror**:
- `frontend/stores/proposals.js:updateSection`
- `frontend/stores/proposals.js:applySync`
- `frontend/stores/proposals.js:reorderSections`
- `frontend/stores/proposals.js:_mergeProjectStage` (added Apr 9 2026 after fixing ERR-006)

### Components: read from the store, not deep-watch the prop

When a component already imports the store, prefer reading directly from `proposalStore.currentProposal?.field` via a computed instead of receiving the data via prop and deep-watching it. Deep watchers are doubly bad: (a) they fire on every unrelated proposal mutation, and (b) they can clobber in-progress form edits if you re-snapshot form state on every change.

If a deep watcher feels needed, ask: is the watch on the right subset (`() => proposal.project_stages`, not `() => proposal`)? Can the form state stay decoupled and only sync once on mount?

### Reference-based prop watchers do not see `push`/`splice`

When a child component receives a Pinia state array as a prop and watches it with `watch(() => props.list, ...)` (no `deep: true`), in-place mutations like `this.folders.push(...)` or `splice(...)` from the store action will **not** re-run the watcher — the array reference is unchanged. The store's own subscribers (and templates iterating directly) re-render because Pinia's reactivity tracks indices, but a derived `localList` synced via the watcher will go stale.

After a CRUD modal emits `@changed`, parent pages that pass store arrays into children **must** also call `store.fetchX()`. The fetch replaces the array reference (`this.folders = response.data`), which triggers ref-based watchers everywhere downstream.

**Established sites**:
- `frontend/pages/panel/documents/index.vue:handleFoldersChanged` and `handleMoved` — both refresh `documentStore.fetchDocuments()` AND `folderStore.fetchFolders()` in parallel.
- `frontend/components/panel/documents/FolderSidebar.vue` — uses `watch(() => props.folders, ...)` to populate a draggable mirror; depends on the parent calling `fetchFolders()` to see new entries.

This supersedes the earlier rule "stores self-maintain state after CRUD, parents need only refresh the document list" — that was true for templates reading `store.folders` directly, but not for ref-based watchers.

---

## 12. Internal Team Notifications vs Client-Facing Sends

Every outbound message uses `EmailDeliveryGateway`, but its policy is explicit:

- `client`: the stable key must be in `CLIENT_EMAIL_CHANNELS`; after the
  primary succeeds, configured customer-copy BCCs are attempted.
- `internal`: team/operations traffic is delivered once and never triggers the
  customer-copy audience.
- `security`: OTPs, invitations, temporary credentials and password links are
  deliberately excluded from copies.

The recipient catalogs are separate by design. Operational notifications use
`NotificationRecipient` and legacy `NOTIFICATION_EMAIL(S)` consumers; customer
communication copies use `ClientEmailCopyRecipient` and its family selection.
Never infer one list from the other — volume, privacy and responsibility differ.

`EmailLog` may contain both client and internal business traffic. For a copied
customer delivery it stores the customer row as `primary` and each independent
BCC attempt as `copy`. Readers that calculate deliverability, cooldowns, contact
counts or retries must filter to `primary`; history readers may nest the copy
rows using their shared `delivery_id`.

---

## 13. Single Source of Truth for Small Catalogs

When you have a small enum-like catalog (e.g., the two project stages `design` + `development`), put the canonical list in **one place** and have all consumers delegate to it.

For project stages, that place is `ProposalStageTracker` in `backend/content/services/proposal_stage_tracker.py`:

```python
class ProposalStageTracker:
    STAGE_DEFINITIONS = (
        ('design', 0),
        ('development', 1),
    )

    @classmethod
    def ensure_stages(cls, proposal): ...

    @classmethod
    def get_or_create_stage(cls, proposal, stage_key): ...
```

Backed by the model's `TextChoices`:

```python
class ProposalProjectStage(models.Model):
    class StageKey(models.TextChoices):
        DESIGN = 'design', 'Diseño'
        DEVELOPMENT = 'development', 'Desarrollo'
```

**Anti-pattern**: duplicating the `('design', 0)` tuple in the views file (`_STAGE_DEFAULT_ORDER`), the onboarding service, the migration, the frontend component, AND the test file. The first time you have to add a third stage, you'll have to chase six places.

**Migrations are the one exception**: data migrations are frozen in time and should NOT import from current code, so a migration may legitimately re-declare the catalog locally.

---

## 14. Bogotá Timezone Arithmetic

All day-level arithmetic (e.g., "is the stage overdue today?") must use Bogotá time, not Django's default UTC.

**Helpers in `backend/content/utils.py`**:
- `now_bogota()` — current `datetime` in `America/Bogota`
- `today_bogota()` — current calendar `date` in `America/Bogota`
- `to_bogota_date(dt)` — convert any datetime (naive or aware) to its Bogotá calendar date
- `format_bogota_date(d)` — render `"8 de abril, 2026"` (accepts both `date` and `datetime`)
- `format_bogota_datetime(dt)` — render `"8 de abril, 2026 — 14:30"`

**Anti-pattern**: `date.today()` (returns UTC date on a UTC-configured Django) or `timezone.now().date()` (also UTC). Both will give wrong answers around midnight Bogotá local time.

**Why it works**: Bogotá is fixed UTC-5 with **no daylight saving time**. The offset is stable year-round, so we can hard-code it via `ZoneInfo('America/Bogota')` without worrying about DST transitions.

**Cron schedules**: Huey `crontab(...)` is evaluated in UTC (since `TIME_ZONE='UTC'` and Huey has no `tz` override). To run a daily task at 08:30 Bogotá, use `crontab(hour='13', minute='30')` and add a comment explaining the offset.

---

## 15. Internal-Only Model Fields in Shared Serializers

When a model is internal-only by design (e.g., `ProposalProjectStage` per its docstring: "internal-only and never rendered to the client"), the corresponding field on a shared serializer must be **gated by admin context**, not exposed via plain nested-model rendering.

### Pattern

```python
class ProposalDetailSerializer(serializers.ModelSerializer):
    project_stages = serializers.SerializerMethodField()

    def get_project_stages(self, obj):
        if not self.context.get('is_admin', False):
            return []
        return ProposalProjectStageSerializer(obj.project_stages.all(), many=True).data
```

The view sets `context={'request': request, 'is_admin': True}` for admin endpoints. Public proposal views never set `is_admin`, so they get an empty list — the internal data leaks nowhere.

### Anti-pattern

```python
# ❌ Always exposed, including via the public /proposal/{uuid}/ endpoint
project_stages = ProposalProjectStageSerializer(many=True, read_only=True)
```

### Performance

Don't forget to `prefetch_related('project_stages')` in the admin queryset, otherwise the SerializerMethodField triggers an extra SELECT per detail load.

A tab can be slow with **zero network involved** — measure DOM-node delta and long tasks before blaming the backend. Det. técnico (2026-08) rendered an O(requirements × commercial-items) checkbox matrix ≈38k nodes while the whole optimized page was ~610; the cure was the ProposalSectionsTab pattern (sections collapsed by default, bodies mounted on expand via Set + `v-if`) plus a per-row disclosure for the grids, taking the warm tab switch from 2.9s to 155ms.

`list(qs)[:50]` materializes the entire table before slicing. Slice the queryset instead (`qs[:50]`): a warm prefetch cache still serves it in memory, and cold paths emit `LIMIT 50` SQL. The change-log table grows unboundedly with proposal age, so this class of bug gets worse silently.

Never pre-mount a `v-show`-hidden panel to "warm" it: `v-auto-resize` measures `scrollHeight=0` under `display:none` and its `updated` hook is value-memoized, so textareas stay permanently mis-sized. Warm the async **chunk** (share the loader between `defineAsyncComponent` and a `requestIdleCallback` call), not the mount.

---

## 16. Methodology Maintenance

### Memory Bank Source
- Methodology rules based on [rules_template](https://github.com/Bhartendu-Kumar/rules_template)
- Original format is Cursor `.mdc` files; must be adapted to Windsurf `.md` format
- Key adaptation: replace `mdc:` prefix links with standard paths, `.mdc` → `.md` references, `src/` → `backend/`+`frontend/`
- `directory-structure.md` must be customized per project (the template uses generic `src/`, `test/`, etc.)

### When to Refresh Memory Files
- After adding a new Django app or major feature module
- After significant changes to test infrastructure or counts
- When file counts drift by >10% from documented values
- After methodology rule updates from upstream template

**Last full refresh: 2026-07-16** (previous: 2026-07-04). The 2026-07-04 pass had found drift far exceeding the >10% trigger (migrations documented at `0087` vs actual `0137`; test files 124/77/131 vs 199/290/191) because the Accounting, MCP-connector, and client-signing waves shipped without a memory-bank pass. The 2026-07-16 pass caught another 12-day wave (accounting statements/cards/pocket-sync/income-liquidation, proposal + document PDF redesign, panel dashboard command center): migrations 0137 → 0163, test files 199/290/191 → 250/334/206. Lesson: run `/methodology-setup` at the end of a feature *wave*, not just per-feature — the >10% rule only helps if something actually checks it.

---

## Real-Entity FK + Write-Through Snapshot Pattern

When upgrading a denormalized field set into a real foreign key (e.g., `BusinessProposal.client` → `accounts.UserProfile`), keep the original snapshot columns and treat them as a frozen audit trail. **Do not drop them in the same PR** — the rewrite would touch every email/PDF/log path that reads `proposal.client_name` and bloat the diff dangerously, AND it would lose the ability to know what the client was *called at the time of send* if the profile is later edited.

**Pattern applied in this repo (`backend/accounts/services/proposal_client_service.py`)**:

1. **FK with `on_delete=PROTECT`** — accidental client deletion can never cascade and lose proposal history. Combined with the orphan-only delete guard in the service (zero proposals + zero projects), there is no path that loses data.

2. **Snapshot fields kept** — `client_name`, `client_email`, `client_phone` stay on `BusinessProposal` and are synced via `proposal_client_service.sync_snapshot(proposal)` after every FK assignment. Email sends, PDFs, and audit logs read from the snapshot; the FK is the source of truth for *current* identity.

3. **Single resolver in the service**, called from both serializer overrides AND raw view code so the JSON-flow path and the form path share one implementation. `ProposalCreateUpdateSerializer.create()`/`update()` and `create_proposal_from_json()`/`update_proposal_from_json()` all route through `get_or_create_client_for_proposal()`.

4. **Cascade updates via bulk update** — `update_client_profile()` cascades changes to all linked proposals via a single `BusinessProposal.objects.filter(client=profile).update(...)`. Bumping `updated_at=timezone.now()` manually is mandatory because `.update()` bypasses `auto_now`.

5. **Service is the silent twin of an existing service** — `proposal_client_service` mirrors `accounts/services/onboarding.create_client` but **never sends invitation emails**. This lets the proposal admin panel create / reuse client rows without triggering platform onboarding, which is reserved for the proposal-acceptance flow.

### Placeholder Email Skip Pattern (linked technique)

When a feature lets users create rows quickly without committing real contact details (typical for sales test/draft flows), use a **canonical placeholder domain** to mark unsendable rows so automations skip them silently:

1. **Single canonical constant** — `UserProfile.PLACEHOLDER_EMAIL_DOMAIN = '@temp.example.com'` (RFC 2606 reserved TLD, never resolves to a real recipient). Imported by `proposal_client_service`, `proposal_email_service`, and `tasks.py` — never duplicated as a literal string. Migrations may keep their own frozen copy because migration code is supposed to be self-contained.

2. **Two-step save for id-embedded placeholders** — to generate `cliente_<profile_id>@temp.example.com` you have to know the id, which only exists after save. Solution: save with a temp uuid-based username/email first, then rewrite both fields with the real id and save again. See `_create_placeholder_profile()` in `proposal_client_service.py`.

3. **Single helper in the email service** — `_is_unsendable_client_email(email)` returns `True` for empty strings and any address ending in `UserProfile.PLACEHOLDER_EMAIL_DOMAIN`. Every client-facing send method (currently 13 in `ProposalEmailService`) calls this helper as its first guard. Huey tasks import the same helper so the gate is applied consistently across sync and async paths.

4. **Querysets that select candidates exclude placeholders directly** — `BusinessProposal.objects.filter(...).exclude(client_email__iendswith=UserProfile.PLACEHOLDER_EMAIL_DOMAIN)` instead of iterating then skipping. Avoids wasted DB rows in cron task scans.

5. **A model property `is_email_placeholder`** — exposed to the frontend via the serializer so the UI can render a "placeholder, automations paused" badge inline.

6. **MX validator whitelists the placeholder domain** — `validate_email_domain_mx()` in `backend/content/utils.py` short-circuits with `True` when `domain == _PLACEHOLDER_EMAIL_DOMAIN`, before any DNS lookup. This prevents the "El dominio de este correo no puede recibir emails (sin registros MX)." error when an admin manually types a `@temp.example.com` address. The constant `_PLACEHOLDER_EMAIL_DOMAIN = 'temp.example.com'` is local to `utils.py`; it does **not** import from `accounts/models.py` to avoid a cross-app import cycle.

**Why this matters**: vendors creating test/draft proposals at speed never accidentally email real recipients (because the address is a reserved TLD), AND multiple placeholder rows never collapse into a single dedup'd row (because each placeholder is keyed on a unique profile id). The model also exposes `is_email_placeholder` so the UI can warn the user that they need to enter a real email before automations resume.

**Reference implementation**:
- `backend/accounts/models.py` — `PLACEHOLDER_EMAIL_DOMAIN` constant + `is_email_placeholder` property on `UserProfile`
- `backend/accounts/services/proposal_client_service.py` — get-or-create + 2-step placeholder save + cascade update
- `backend/content/services/proposal_email_service.py` — `_is_unsendable_client_email` helper + 13 client-facing methods gated
- `backend/content/tasks.py` — 4 huey task gates + 2 candidate-queryset excludes
- `backend/content/migrations/0079_add_business_proposal_client_fk.py` + `0080_backfill_proposal_clients.py` — schema + dedup backfill
- `backend/content/utils.py:validate_email_domain_mx` — domain whitelist so manually-typed placeholder addresses pass MX validation

---

## 17. Frontend Admin UX Patterns

### Bidirectional Date / Duration Input Sync

When two inputs must stay in sync (e.g., a `datetime-local` + a "number of days" field), use two separate `watch()` calls rather than a single computed getter/setter. The key invariant is:

- **Date → Days**: compute `Math.round(diff / 86_400_000)`, always safe to recalculate.
- **Days → Date**: rebuild from `Date.now() + safeDays × 86_400_000` **but preserve the existing time component** (`form.expires_at.slice(11, 16)`) so a user who set a specific hour does not lose it when they only intend to adjust the day count.

```js
// Days watcher — preserves user's chosen time
watch(expiryDaysInput, (days) => {
  const safeDays = Number.isInteger(days) && days > 0 ? days : DEFAULT_EXPIRATION_DAYS;
  const expiry = new Date(Date.now() + safeDays * 24 * 60 * 60 * 1000);
  const dateStr = `${expiry.getFullYear()}-${pad(expiry.getMonth() + 1)}-${pad(expiry.getDate())}`;
  const timeStr = form.expires_at ? form.expires_at.slice(11, 16)
                                  : `${pad(expiry.getHours())}:${pad(expiry.getMinutes())}`;
  form.expires_at = `${dateStr}T${timeStr}`;
});
```

Vue reactivity short-circuits when `expiryDaysInput` produces the same integer twice in a row, so the two-watcher pattern does not create an infinite loop.

**Implemented in**: `create.vue` + `[id]/edit.vue` for the proposal expiration date field.

### Toast Notifications for Admin Save Feedback

The standard UX pattern for save confirmation in the admin edit page is a **fixed bottom-right toast** (not an inline div inside the form, which may be scrolled out of view at submission time).

**Template pattern**:
```html
<Teleport to="body">
  <Transition
    enter-active-class="transition-all duration-300 ease-out"
    leave-active-class="transition-all duration-200 ease-in"
    enter-from-class="opacity-0 translate-y-4"
    leave-to-class="opacity-0 translate-y-4"
  >
    <div v-if="updateMsg" class="fixed bottom-6 right-6 z-[9999] ...">
      {{ updateMsg.text }}
      <button @click="updateMsg = null">✕</button>
    </div>
  </Transition>
</Teleport>
```

**Auto-dismiss without timer stacking** — store the timer id and `clearTimeout` before scheduling:
```js
const updateMsgTimer = ref(null);
clearTimeout(updateMsgTimer.value);
updateMsgTimer.value = setTimeout(() => { updateMsg.value = null; }, 5000);
```

Use `<Teleport to="body">` so the toast renders above all panel layout layers (sticky headers, sidebars) without z-index conflicts. Use Tailwind `transition-all` classes inline on `<Transition>` to avoid a separate `<style>` block.

**Also clear on unmount.** Any `setTimeout` that mutates a reactive ref must be tracked in a module-scoped binding and cleared in `onUnmounted` — otherwise a click-then-navigate flips state on a gone component. Applies to every clipboard-feedback flag (`urlCopied`, `jsonCopied`) and toast timer. See `frontend/pages/panel/diagnostics/[id]/edit.vue` — both copy helpers capture their timer and the unmount hook clears all three (toast + url + json).

**Implemented in**: `frontend/pages/panel/proposals/[id]/edit.vue`, `frontend/pages/panel/diagnostics/[id]/edit.vue`.

**Preferred path for new admin pages**: import `usePanelToast` from `~/composables/usePanelToast` + mount `<PanelToast />` once in the template. The composable already encapsulates the timer + `clearTimeout` ceremony and a single `<PanelToast />` Teleport renders the bottom-right card. No need to re-implement `updateMsg`/`updateMsgTimer`/`setTimeout` pairs in each page — that pattern is reserved for legacy edit pages that already had inline toasts. New pages: `frontend/pages/panel/diagnostics/defaults.vue` (Apr 18, 2026) follows the composable path.

### Generic Modal Reuse via `endpoint` Prop (not `resourceId`)

When a modal performs an HTTP action whose target (proposal vs. diagnostic vs. document) varies across callers, accept a relative `endpoint: String` prop instead of a typed `proposalId` / `diagnosticId`. Each caller constructs the path (`diagnostics/${id}/email/markdown-attachment/`); the modal prepends `/api/` and calls the endpoint without knowing the resource type.

**Pattern**: `MarkdownAttachmentModal.vue` (`components/MarkdownAttachmentModal.vue`) — moved from `BusinessProposal/admin/` to `components/` root when it gained a second consumer (`DiagnosticEmailsTab`). Any future email-composing attachment modal should start here rather than as a copy inside the feature folder.

**Anti-pattern**: `proposalId: [Number, String]` — forced the modal to hardcode the URL template, preventing reuse across resource types.

### Shared Backend View Helpers for Identical Response Bodies

When two or more views produce an identical response body (same validation, same service call, same error codes), extract the logic into a module-level helper in a dedicated file rather than duplicating 40 lines each time.

**Pattern**: `backend/content/views/_email_attachment.py`:
- `inline_pdf_response(pdf_bytes, filename)` — builds `HttpResponse` with `Content-Disposition: inline`.
- `render_markdown_pdf_response(request, *, client_name)` — validates `title`/`markdown`, calls `DocumentPdfService.generate_from_markdown()`, returns the PDF response or a typed 400/500 error.

Both markdown-attachment views (proposal + diagnostic) import these and are 3 lines each. The underscore prefix (`_email_attachment.py`) signals that the module is a helper, not a standalone view router.

### `coerce_bool` vs. Inline `_bool()` for DRF Request Data

DRF's `request.data` delivers form-submitted booleans as strings (`"true"`, `"false"`, `"1"`, `"0"`). Inline helpers that call `request.data.get(key, default)` accidentally return the *string* `"True"` when the key is missing — because the fallback is passed through unchanged.

**Safe pattern**: `coerce_bool(value, default=True)` in `content/utils.py` — handles `None → return default`, `bool → return as-is`, `str → lowercase compare against DRF's BooleanField.TRUE_VALUES`. Never stringify the default.

### Reusing Existing Transition Infrastructure for New Navigation Events

Before adding a new CSS transition, check whether an existing overlay/transition already covers the visual effect you need. The `switch-mode-overlay` in `proposal/[uuid]/index.vue` was designed for gateway → mode transitions but works equally well for mode → gateway by adding a new sentinel value (`'gateway'`) to the icon/heading/subtitle ternary chain. No new CSS needed — the bouncy-scale enter/leave keyframes are reused as-is.

**Pattern**: add a new `v-else-if` case to the overlay template, update `handleBackToGateway` to set `switchOverlayMode = 'gateway'` and `switchOverlayVisible = true` before resetting state, then mirror the timing of the existing `handleViewModeSelect` function (1 s hold → state reset → 1.2 s overlay hide).

## 18. Adding a New `ProposalSection.SectionType`

These three lessons surfaced together while shipping `roi_projection`; treat them as a single checklist for the next person adding a section type.

### Migration backfill: don't trust `ProposalService.get_default_sections` from inside the migration

`ProposalDefaultConfig` is a DB-backed override of the hardcoded `DEFAULT_SECTIONS` list. When the migration calls `ProposalService.get_default_sections(language)` and the DB row exists with the OLD section list (no entry for the new type), `cfg = _defaults_index(language).get('roi_projection')` returns `None` and the row creation **silently no-ops** — the migration reports success but no rows are created. The order-bump step still runs, leaving a permanent gap at `order=4`.

**Fix pattern**: import the canonical hardcoded list directly inside the migration, not via the service:

```python
from content.services.proposal_service import DEFAULT_SECTIONS, DEFAULT_SECTIONS_EN
cfg = next((s for s in (DEFAULT_SECTIONS_EN if lang == 'en' else DEFAULT_SECTIONS)
            if s['section_type'] == 'roi_projection'), None)
```

After running the migration, also update `ProposalDefaultConfig.sections_json` for each language so future proposals (created via `/panel/defaults` or the panel UI) include the new section by default.

### Frontend dispatcher: components expecting `{ content }` need a named branch

`getSectionProps(section, currentIndex)` in `pages/proposal/[uuid]/index.vue` flat-spreads `content_json` keys as top-level props for any section type without a named `if` branch. Components like `ProposalSummary.vue` and `RoiProjection.vue` that `defineProps({ content: { type: Object } })` will mount but bind `undefined` everywhere.

**Fix pattern**: every new section component that uses the single-`content` prop pattern must add a named branch:

```js
if (section.section_type === 'roi_projection') {
  return { content: { ...content, index: paddedIndex } };
}
```

Symptom in browser: section element renders (correct CSS class) but inner h2/cards are empty. Symptom in Playwright: snapshot shows the section but `getByText(...)` for inner content times out.

### Web-only sections: skip from PDF *including* the TOC

Sections without an entry in `SECTION_RENDERERS` (`proposal_pdf_service.py`) silently skip content rendering, but historically the section loop **still appended a TOC entry** for them — leaving orphan TOC links pointing at the next section. After fixing this for `roi_projection`, the loop now `continue`s before appending the TOC entry when both `is_paste=False` and `renderer is None`. The same guard now also drops `proposal_summary` and `process_methodology` from the TOC (they were always content-less in the PDF anyway).

**Pattern**: web-only sections need only one explicit code change — *not* registering them in `SECTION_RENDERERS`. The TOC behavior is consistent because of the loop guard.

### Schema dead-code check before reusing existing components

Before deciding "I'll just add a `kpis` array to `proposal_summary` instead of building a new section", grep the public component:

```bash
grep -nE "v-html|v-for|content\.kpis" frontend/components/BusinessProposal/ProposalSummary.vue
```

`ProposalSummary.vue` defines a `kpis` field in its admin form and seller prompt but the public template only iterates `cards[]`. The `kpis` array is dead schema. Always verify the data path is wired end-to-end (admin form → JSON → backend serializer → public component) before adding fields to an existing section.

## 19. Build-time prerender must bypass production nginx (rate limit / TLS)

A build step that prerenders pages by fetching the app's **own public API** is, from nginx's perspective, just another external client — it inherits production's rate limiting, WAF rules, and TLS redirects. This silently broke blog prerender (ERR-015): `build:django` fetched all 114 blog routes from `https://projectapp.co`, tripped `limit_req zone=api` (5 r/s) → 429 → ~100 posts rendered as 500 → build shipped the SPA shell with no per-post HTML/OG tags. It worked when the blog was small and degraded as it grew past the burst window.

### Rules of thumb
- **Prerender/SSR-at-build against the app server on loopback, never the public hostname.** The build script (`frontend/update-django-template.js`) starts a throwaway Django on a free `127.0.0.1` port and points `PRERENDER_API_ORIGIN` at it.
- **Don't assume `127.0.0.1:8000` works.** Production gunicorn binds `unix:/run/projectapp.sock`, not a TCP port — there is nothing on :8000. The build brings up its own server instead.
- **A loopback build server needs a no-TLS settings module.** `settings_prod` forces `SECURE_SSL_REDIRECT=True`, which 301s plain-HTTP loopback fetches to `https://127.0.0.1` and breaks them. `backend/projectapp/settings_build.py` extends prod (real DB/content) but disables SSL redirect / HSTS / secure cookies. It exists only for the build server.
- **Put the fix at the single build chokepoint.** Both `/deploy-and-check` and the on-publish `run_frontend_rebuild` task call `npm run build:django`, so fixing it there covers every path. Keep a graceful fallback (env-provided origin) for environments with no backend (CI/dev).
- **Make a dropped prerender loud, not silent.** Set `PRERENDER_REQUIRE_BLOG=1` once the build can reliably reach the API, so a regression fails the build instead of silently shipping un-prerendered SEO pages.

---

## 20. Panel Modules Wave — MCP, Accounting, Client Signing (Jul 2026)

### MCP connector security (claude.ai remote connectors)
- The connector token is a **capability URL**: shown in full exactly once at generation, then only its **SHA-256 hash** is stored (`McpConnector`). Regenerating rotates the hash and instantly 404s the old URL.
- The MCP endpoint (`content/views/mcp_blog.py`) validates **Origin** (DNS-rebinding defense) + token + active-state on every JSON-RPC call, and logs `handshake/tool_call/auth_error/origin_rejected` to `McpRequestLog` (the panel's connection-activity feed reads this).
- Rate limits for a multi-connector client must be keyed by **IP + registered connector slug**, not IP alone: Codex starts its connectors concurrently, so a shared IP bucket turns legitimate sibling startups into HTTP 429 failures. Unknown slugs must collapse into one defensive bucket; using arbitrary path text would make the throttle bypassable.
- MCP tools wrap existing services/ORM — they are **not** a new business layer. Guardrails live in the tool module (e.g. Documents connector only exposes MARKDOWN docs, refuses to delete published docs). The machine-facing endpoint is integration-tested in pytest, not E2E.

### Accounting partner-split invariant
- `PartnerSplitMixin.clean()` is the single source of truth for the money rule: no negative amounts, `gustavo + carlos ≤ total`, and a **personal-ledger record must be 100% the owning partner's** (other partner = 0). `company_amount` is a derived property, never stored. Keep validation in `clean()` so both the API and the admin enforce it; don't re-implement in serializers.
- `source_ref` is an idempotency key (`import:<hash>` / `fake:<tag>`) — dedups re-imports and fake-data reseeds.

### Client document signing
- Two independent gates before a signature is accepted: the document must be `requires_signature`, and the client's email must be **verified via OTP** (`UserProfile.email_verified`). The sign button is disabled client-side and the endpoint returns 403 server-side — test both.
- Signing is **idempotent** (re-sign returns the signed doc, doesn't re-notify). Milestone team notifications are best-effort and must never raise into the client flow (`client_flow_notifications` swallows errors).

### E2E flow tags must be array literals, not bare constants
- The flow-definitions sync checker (`scripts/lib/e2e-flow-refs.mjs`) only detects `@flow:` references inside `tag: [ ... ]` **array literals**. A spec that applies `{ tag: PLATFORM_PASSWORD_RESET }` (bare imported constant) is invisible to it — its coverage silently doesn't count. Always spread: `{ tag: [...PLATFORM_PASSWORD_RESET] }` / `{ tag: [...CONST, '@role:client'] }`. This stayed hidden until the flow was registered in `flow-definitions.json` (an unregistered flow trips neither the "unknown-in-specs" nor the "required-but-unreferenced" check).
- **Verify at the served-HTML layer, not just HTTP 200.** A Nuxt SPA shell returns 200 with no article content. Confirm `<article>` + per-post `og:title` + JSON-LD are present in `curl` output, and spot-check a real browser render.

---

## 21. Test Quality Gate: CI runs DEFAULT mode — `--strict` SUPPRESSES semantic rules

The gate has two semantic-rules modes and they are **not** a superset relationship. The CI job (`.github/workflows/test-quality-gate.yml`) invokes `scripts/test_quality_gate.py` **without** `--semantic-rules strict` — i.e. DEFAULT mode. DEFAULT enables rules that strict mode suppresses: PR #113 went red in CI on the `forbidden_token` rule (the word "batch" in a test name) and the `no_assertions` rule, even though a local `--semantic-rules strict` run was clean.

### Rules of thumb
- **Validate pre-push in DEFAULT mode** — the exact CI invocation is `python3 scripts/test_quality_gate.py --repo-root . --report-path <out>.json --frontend-unit-dir test --verbose`. Do not add `--strict`/`--semantic-rules strict` when the goal is predicting CI.
- **Any ERROR fails the gate** regardless of the overall score; warnings/info only lower the score (score ≥80 green, ≥60 yellow).
- **File-scoped runs** use `--include-file <path>` — cheap way to gate only the specs touched in a batch.
- Watch for `forbidden_token` in test **names** (not just bodies) and `no_assertions` on tests whose assertion lives inside a helper — use plain asserts in the test body.

## 22. Test-audit (Round 8, 2026-07-24): `duplicate_coverage` is a naming signal, not a merge signal; the backend gate is `content`-only

The first whole-corpus `test-audit` (report: `docs/audits/test-audit-2026-07-24.md`) produced two findings worth keeping. Note this corpus is literally the one behind the `test-audit` skill's example table (301 no-interaction E2E / 72 junk-only flows / 146 duplicate unit / 164 weak assertions — measured identically here).

### `duplicate_coverage` findings are overwhelmingly false-positives-for-merge
The `duplicate_coverage` detector matches on **test name + structural shape**, blind to the enclosing `describe` block. All 147 findings here were unmergeable:
- **115 same-file** were the *same generic name* (`"handles error"`, `"sets error on failure"`, `"does nothing when el is null"`) reused across **different** `describe` blocks — i.e. different store actions / different composables (`useDiagnosticCommercialPrompt` vs `useDiagnosticTechnicalPrompt`). Merging deletes real coverage of a distinct subject. The correct fix is **rename to a single-purpose name** (prefix with the action), never merge.
- **32 cross-file** were structurally identical tests for **different components** (`DiagnosticPricingForm` vs `DiagnosticRadiographyForm`, `PrivacyPolicy` vs `TermsAndConditions`) — parallel coverage, **keep**.

Rule of thumb: before actioning any `duplicate_coverage` finding, resolve each test's enclosing `describe`; only two tests in the **same** describe with identical bodies are a true duplicate. Same name + different describe = rename; same shape + different SUT = keep (or `test.each` if truly one subject with a value table).

### The quality gate's backend suite scans only the `content` app
`.testquality.yml` sets `backend_app_name: content`, and CI (`test-quality-gate.yml`) runs the gate with no `--backend-app` override, so **`accounts`, `projectapp`, and top-level `backend/tests/` are ungated in CI**. The audit found 72 error-level findings in `accounts` (67 `misplaced_file` — test files outside the `models/services/views/...` folders `py_allowed_folders` expects) that CI has never seen. To audit the full backend, run the gate once per app: `python3 scripts/test_quality_gate.py --suite backend --backend-app accounts` (repeat for `projectapp`).

## 23. A pre-deploy SPA session survives every deploy — "the feature doesn't work" starts with a hard reload

The panel is a static Nuxt SPA: `serve_nuxt` sends the entry HTML with `Cache-Control: no-cache`, but a browser tab opened before a deploy never refetches it — client-side navigation keeps running the old bundle indefinitely, and old hashed assets stay servable (`staticfiles/frontend/_nuxt` accumulates every deploy's files under a 30d immutable cache; 9,693 files as of Aug 2026), so the stale app never even breaks on its own. Real incident (2026-08-03): "Solo esperados" filtered identically to "Todos los esperados" in the operator's session — the pre-Aug-1 bundle had no `paymentStatus` matcher, so the tab's filter key was silently inert; the shipped feature was fine and a reload fixed it. Diagnosis order for "the deployed feature doesn't show": (1) hard-reload the tab; (2) confirm the served build (`backend/staticfiles/frontend` mtime + grep the new symbol in `_nuxt/`); (3) only then suspect code or data. Purging old `_nuxt` bundles would force stale tabs to break loudly on their next navigation — a possible future chore, deliberately not done yet.

## 24. Gross-income deductions: utility must stay asymmetric

Under the gross convention (operator decision 2026-08-03) an expected income keeps its invoiced total; fees discounted at origin become linked deduction expenses that credit it as payment (`paid = liquid children + linked deductions`, via `ExpenseRecord.source_income`). The utility formulas CANNOT subtract deductions on both sides: **expected** utility subtracts them (gross projection minus known fees) but **liquid** utility subtracts only operational spending, because the liquid total is cash that already arrived net of every fee — subtracting the fee there counts the same loss twice. The same asymmetry holds in `monthly_breakdown`, and any new aggregate should follow it. Corollary: editing or deleting a deduction expense mutates its income's payment state through the credit — they are one bookkeeping unit, which is why manual writes can neither set nor clear `deduction_type` (settlement context only) and a deduction never gains a pocket movement.

## 25. A new required field may not be demanded where it cannot be filled in

PA-51 made the covered period mandatory on hosting incomes, and the rule landed in `IncomeRecordCreateUpdateSerializer.validate` — a serializer every write path shares, not just the panel form that grew the fields. From then on **no hosting income could be settled at all**: `accounting_settlement_service` builds its children (the liquid payment, the rescheduled balance, each abono allocation) through that same serializer, copying the parent's `origin` but nothing else, so the check fired on records nobody could complete from where they stood — the modal has no period fields, and the child is new, so it cannot read the parent's window either. Both a legacy income and one with a perfect window failed identically; the flow was dead for two weeks with no test noticing, because not one test settled a hosting income.

**The rule.** When a field becomes required, walk EVERY path that writes that record — panel form, MCP tool, bulk action, and the services that derive records from other records — and decide for each one: *asked for*, *deferred*, or *not applicable*. A path that cannot show the field must never be the one refused. Concretely in this codebase:

- **Derived records inherit the exemption.** A record a service builds out of another describes nothing on its own, so the rules meant for a person describing something do not reach it. `origin`, `deduction_type` and now the covered period all take the same `context={'settlement': True}` escape — when a fourth one appears, it belongs on that list, not on a new mechanism.
- **Watch for fields whose validation also DERIVES other fields.** The period block rewrites `period_date` from `period_start`. Handing the window to a settlement child would have been the obvious fix and would have silently moved the collected money to the month the window opens, instead of the day it came in.
- **Money is never held for a descriptive field.** Registering that the money arrived and describing what it covers are different acts; the missing description is completed where it shows up (the Liquidar modal offers the window when the hosting charge has none) and, left empty, the settlement goes through all the same.
- **The test that would have caught it** is the one that runs the *derived* path, not the one that runs the form. Any new required field deserves at least one test per writing path — see `content/tests/views/test_settlement_hosting_period.py`.

## 26. Commercial catalogs and contractual snapshots need an explicit time boundary

Replacing an offered periodicity is not a global string substitution. The proposal document, its public view and its PDF may be contractual history, while a project or subscription created today is an operational record governed by the current catalog. In the 2026-08-20 annual→nine-month change, using one unconditional normalizer either rewrote accepted proposals or leaked annual terms into new projects.

The stable pattern is:

- Define “current” once (proposal activity/status or operational record state).
- Preserve stored JSON and paid ledger rows for terminal history; label legacy enum values as historical instead of deleting their read maps.
- Let new-write serializers expose only the current enum while permitting an unchanged legacy value during unrelated edits.
- Give operational conversions an explicit call-site override (`force_current_terms=True`) rather than changing a public/PDF helper's default semantics.
- Put payment-provider state ahead of mutation: abort a data migration before touching any subscription whose pending charge is processing or linked externally.
- Test both sides of the boundary in the same change: historical display stays old, new operational creation becomes current.

## 27. Client-facing copy belongs beside the document, not inside the deliverable

A report and the message used to deliver it have different audiences and lifecycles.
Putting email/WhatsApp copy in the markdown would leak internal working text into the
PDF and client portal; keeping it only in terminal output makes a delayed delivery
easy to lose. The durable boundary is optional private metadata on `Document`, read
and written only by the admin detail surface and the Documents MCP. Free-form notes
follow the same boundary as an ordered JSON collection of small `{title, content}`
objects; a shared normalizer keeps REST and MCP writes consistent without coupling
them to the report markdown schema.

One workflow must own the words. `client-report` creates the report and its canonical
subject/email/WhatsApp triple; `client-message`, when it requests a report, reuses the
same bytes instead of composing an equivalent second message. An omitted MCP field
means “preserve” during partial updates, while an explicit empty string means “clear”.
Duplicating a document deliberately clears all fixed and custom notes because the
metadata is specific to one concrete handoff. Test this boundary from both sides:
internal CRUD round-trips the notes in insertion order, and platform serializers
never expose them.

## 28. Parallel Django migrations converge through an explicit merge node

Two feature branches can both create `0204_*` from the same `0203` parent and merge
without a textual Git conflict because the filenames differ. Django still has two
leaf nodes and will refuse every `migrate` until the graph is reunified.

The safe repair is a new, empty migration whose dependencies are both leaves. Do not
rename either shared migration and do not make one depend retroactively on the other:
either action rewrites published history and can produce inconsistent migration state
across environments. Verify the repair at graph level (`detect_conflicts()` is empty
and the app has one leaf), then run `makemigrations --check --dry-run` and the system
check. This graph check belongs before production deploys because Git alone cannot
detect the condition.

## 29. Responsive card grids need an inner-width acceptance threshold

A desktop breakpoint does not guarantee readable columns. `FinalNote` looked spacious
at the viewport level while `max-w-6xl`, large container padding, the grid gap and card
padding left roughly 460 px per column. Measure the element the user reads, not the
screen: at 1366 px the commitment and kickoff cards must each retain more than 520 px,
and below that capacity the layout should stack. The same rule applies within rows:
allow a descriptive payment label to wrap, but reserve an indivisible column for the
amount, currency and tax suffix.

## 30. Generated rich text needs exact JSON paths in every prompt surface

“Use bold in introductions” is too ambiguous when multiple prompt surfaces and JSON
field names exist. Keep a canonical field list in both `useSellerPrompt` and backend
`_seller_prompt.bold_formatting`, state the allowed tag (`<b>`), fragment limit and
empty-field behavior, and regression-test every path. When correcting one live
proposal, use an exact-match, reversible data migration so deployment cannot overwrite
copy edited after the correction was prepared.

## 31. A persisted derivative needs one backend owner and an explicit refresh graph

`cop_equivalent` looked like ordinary editable accounting data, so creation initialized
it once and later edits simply carried the stale value forward. Reloading could not help:
the database itself was wrong, and every total faithfully summed that wrong cache. The
repair pattern is broader than this field: declare the source inputs, choose the policy
for time-sensitive inputs, make one backend boundary own the calculation, and trigger
that boundary from every source change. Here the policy is the current manually
configured USD rate; `RecurringPayment.save()` owns row changes and
`AccountingSettings.save()` owns rate-wide synchronization. Client previews may explain
the result, but they never become the source of truth. When introducing the invariant,
ship a data migration and a stale-row regression so old data is brought under the same
rule immediately.

## 32. Responsive contracts need one width vocabulary and compiled-CSS proof

Do not derive breakpoints independently in Vue, Tailwind and Playwright. Keep
the panel bands, `matchMedia` queries and five acceptance viewports in one
configuration, then make shared components own adaptation. A table still needs
an explicit per-column `keep/group/hide` policy: a generic “hide the last
columns” rule cannot know business priority. Likewise, cap the content shell on
wide monitors instead of treating responsiveness as only a small-screen issue.

Framework vocabulary is part of the contract. Tailwind already means
orientation when it sees `portrait:` or `landscape:`, so panel width aliases use
the `panel-*` namespace. Unit tests can prove that a class string exists while
missing a bad media query; every new breakpoint family must also be inspected
in generated CSS and exercised at the boundary viewports.

Those breakpoints are product data, not framework defaults. ProjectApp is
operated on five known screen classes, including the awkward portrait-tablet
middle and a 27-inch monitor. A `md` or `lg` class is not acceptance evidence
by itself: choose navigation from usable content width, cap wide screens, and
measure the element the operator uses instead of inferring success from the
viewport alone.

## 32. Structural responsiveness needs one breakpoint owner and exact-device tests

A two-zone page cannot be made compact by hiding random descendants: that leaves two
focus trees, filters ahead of content and desktop assumptions inside a narrow main
column. Choose the structural branch once
(`useIsMobile(PANEL_BREAKPOINTS.landscape - 1)` here), render exactly
one interactive DOM, and let smaller CSS breakpoints refine only the inside of that
branch. The 835 px portrait tablet is the reason this boundary cannot simply inherit
a library's `md`; the 1195 px landscape tablet is the reason it cannot be treated as
a phone.

Verification must name the real five viewport dimensions. For every module, navigate
through the UI, assert concrete fixture data, exercise its transient zone, check page
overflow and measure the large-screen cap. A generic “mobile” project plus one desktop
project misses both the portrait-tablet failure and the over-stretched 27-inch layout.

## 33. Mobile lists and comparative tables are different interaction problems

A responsive table primitive should not turn every dataset into the same mobile
shape. Transactional and comparative screens need stable column semantics, so
they declare `keep/group/hide` by business priority. Exploratory CRUD screens are
usually scanned one entity at a time, so a single card representation below the
panel breakpoint is clearer. Rendering both versions and hiding one with CSS is
not equivalent: it duplicates links, test IDs and accessibility targets in the
DOM. `BaseExploratoryList` therefore chooses exactly one representation from the
shared media-query source, while `BaseResponsiveTable` retains explicit column
policy.

The lasting control is ownership, not a one-time sweep. Every catalog page must
map to one module script, each module must retain a real tagged E2E, and the same
five profiles run on affected PRs and on a monthly full matrix. A semestral review
checks whether the devices themselves changed; individual pages never move a
breakpoint without changing the shared contract and its evidence together.

## 34. Responsive accounting must preserve business meaning, not table shape

An accounting column cannot be hidden because it happens to be last. Declare a
primary field, retained totals and grouped secondary facts for every table, then
verify the choice against the operation users perform. In Ingresos that means
concept and total survive while collection state, month and origin can share a
compact detail block; grouped client headers stack identity and totals instead
of compressing four meanings into one line.

Some data must change location rather than disappear. Pocket's running balance
is the clearest case: its independent column is too expensive below 1024 px, but
without it the ledger becomes a list of unrelated movements. Relocating the
balance below each retained amount preserves chronology and frees horizontal
space. Apply the same rule to secondary KPIs: show the three ranked decisions,
then disclose the rest on demand. A repeatable matrix needs all twelve routes
and all five real widths; representative Playwright checks pin the breakpoint
semantics while the written 12×5 script preserves business review tab by tab.

## 35. Customer email policy belongs at the transport boundary

Adding a BCC inside every template is not durable: template registries describe
content, while sends also originate in services, views, tasks and both Django
apps. The enforceable boundary is the last abstraction before Django's email
backend. Make that gateway the only permitted mail-I/O owner and require every
caller to declare a stable key plus client/internal/security intent.

The client inventory is executable policy, not documentation alone. A new
customer key must enter that mapping before the gateway accepts it, and a static
test must fail if a future caller bypasses the gateway. Keep operational and
security traffic in the same transport path but outside the customer-copy
audience; otherwise OTPs, temporary passwords or internal digests can leak into
an unrelated inbox.

Failure isolation requires separate envelopes. Deliver the customer message
first, then create one BCC-only envelope per configured copy recipient. Group
those attempts with the primary via a delivery identifier, but give each its own
status row. Reader queries must explicitly select `primary` so a copy neither
inflates contact counts nor triggers cooldowns/retries; history surfaces can
then attach `copy` rows underneath without changing the meaning of existing
metrics.

## 36. Reuse infrastructure, not the wrong aggregate

Two features can share clients, projects, documents, authentication and UI
primitives without sharing a persistence model. A `Document` is one editorial
artifact; a client conversation is an aggregate root containing ordered,
bidirectional events. Treating messages as documents would make folders,
editorial states and list filters ambiguous and create an expensive extraction
later. The communications module therefore owns thread/message models inside the
existing `content` app and references Documents through a protected join.

Operational facts also need stable semantics. “Sent” remains stored evidence;
“Respondido” is derived from a valid reply. Delivered events are not silently
rewritten: annulment and business-date corrections append audit context, while
only drafts remain mutable. When project ownership changes, historical threads
stay with the original client and lose only their optional project scope.
