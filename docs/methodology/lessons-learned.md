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
- Services: `ProposalService`, `ProposalEmailService`, `ProposalPdfService`, `ContractPdfService`, `EmailTemplateRegistry`, `PdfUtils`, `DocumentPdfService`, `MarkdownParser`, `CollectionAccountService`, `CollectionAccountPdfService`, `TechnicalDocumentPdf`, `TechnicalDocumentFilter`, `PlatformOnboardingPdf`, `LinkedInService`

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

### Section Types Are Fixed
- 12 section types defined in `ProposalSection.SectionType` choices
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

### Accounts Services
- `services/onboarding.py` — profile completion flow
- `services/tokens.py` — JWT token generation/refresh
- `services/verification.py` — OTP code generation and validation
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

## 12. Pinia Reactivity (Vue 3 + Options API stores)

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

## 13. Internal Team Notifications vs Client-Facing Sends

### `_log_email` is for client-facing emails only

`backend/content/services/proposal_email_service.py` has a `_log_email()` helper that creates `EmailLog` rows. Use it ONLY for sends to a single client recipient (`proposal.client_email`). For team-facing internal alerts that fan out to multiple ops emails, **do not** call `_log_email()` — match the convention of:
- `send_first_view_notification`
- `send_comment_notification`
- `send_share_notification`
- `send_stakeholder_detected_notification`
- `send_seller_inactivity_escalation`
- `send_stage_warning` / `send_stage_overdue`

These use `logger.info(...)` and `logger.exception(...)` only.

### Why

Per-recipient `_log_email` loops produce one EmailLog row per addressee for a single SMTP `send()` call. SMTP failures are per-connection, not per-recipient — so the loop encodes a lie ("recipient A failed AND recipient B failed AND…") that you can't distinguish from reality. Single-row internal logging via `logger` is honest about what actually happened.

### Recipient list

All internal team notifications resolve recipients via `cls._get_notification_recipients()`, which reads `NOTIFICATION_EMAIL` (CSV-supported) and `NOTIFICATION_EMAILS` (list/CSV). To target a different audience for one feature, change the env var — do NOT add a per-feature recipient setting.

---

## 14. Single Source of Truth for Small Catalogs

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

## 15. Bogotá Timezone Arithmetic

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

## 16. Internal-Only Model Fields in Shared Serializers

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

---

## 11. Methodology Maintenance

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
