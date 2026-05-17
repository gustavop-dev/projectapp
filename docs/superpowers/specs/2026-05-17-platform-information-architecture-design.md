# Platform Information Architecture — Design Spec

- **Status:** Approved (pending implementation plan)
- **Date:** 2026-05-17
- **Surface:** `/platform/*` (JWT auth, admin + client roles)
- **Branch:** `feat/17052026-platform-information-architecture`
- **Scope:** **admin (developer) role only** for this round. Client role keeps its current views; we will revisit in a follow-up.

## 1. Goal

Collapse the duplicated dual-scope architecture of `/platform/*` (global module
pages + per-project copies of the same modules) into a clean drill-down model:
**entities live as tables in the top navigation; their detail pages own the
modules.** Replace the current "Proyectos" cards grid with a table. Move
the project-creation flow to explicitly select **one or more
BusinessProposals** from the panel as ordered project phases.

## 2. Decisions captured during brainstorming

| Topic | Decision |
|---|---|
| Global module pages (`/platform/board`, `/changes`, `/bugs`, `/deliverables`, `/payments`, `/collection-accounts`, `/access`) | **Delete.** Each module lives only inside a project. |
| Global Dashboard (`/platform/dashboard`) | **Delete.** Root redirects to `/platform/projects`. |
| Global payments table | **Not built.** Hosting payments are a per-client subscription; visible as columns on the Clients table + full detail inside each client. |
| Sidebar — admin layout | Three sections: **Navegación** (Notificaciones, Proyectos, Clientes), **Cuenta** (Configuración, [Personaliza]), **Administración** (Panel admin external). |
| Projects list UI | **Table**, not cards. |
| Row action column | **Chevron-only.** Edit/archive/delete live inside the project Resumen. |
| Project sub-navigation | **Secondary sidebar** on the left within `/platform/projects/:id/*`. |
| Back-to-list | **Breadcrumb** in the project header, no separate Back button. |
| Client states | **Activo / Inactivo only.** No "pending onboarding" badge; activos display no chip. Inactivo = stopped paying hosting and left. |
| Pending-invite clients (account exists, never logged in) | Shown as Activo + a subtle "sin acceso aún" icon/tooltip next to the email. |
| Hosting plans | Three cycles: **Mensual / Trimestral / Semestral.** Plan + renewal date + renewal value live on the Clients row. |
| Renewal alert | Amber visual on the row when next renewal is within 30 days. |
| Project ↔ proposals | Many-to-one (one project, many proposals as ordered phases). |
| Phase lifecycle | Editable after creation: add, reorder (drag-and-drop), remove. |

## 3. Sidebar — admin

```
┌─ Navegación ──────────────────────────┐
│  • Notificaciones    /platform/notifications     (badge: unread)
│  • Proyectos         /platform/projects          (table)
│  • Clientes          /platform/clients           (admin, table)
└───────────────────────────────────────┘

┌─ Cuenta ──────────────────────────────┐
│  • Configuración     /platform/profile
│  • [Personaliza]                                 (modal theme picker)
└───────────────────────────────────────┘

┌─ Administración (admin) ──────────────┐
│  • Panel admin       /panel (external)
└───────────────────────────────────────┘
```

Root `/platform` redirects to `/platform/projects`. The Dashboard page goes
away.

The current `projectSubModules` map and special-case `isActive()` logic in
`PlatformSidebar.vue` are removed (no longer needed — the global module
entries that they linked to no longer exist).

## 4. Projects table (`/platform/projects`)

Replaces the card grid in `frontend/pages/platform/projects/index.vue`.

### 4.1 Columns (admin)

| Column | Source | Notes |
|---|---|---|
| Proyecto | `name` + `status` chip | Chip values: Activo / Pausado / Completado / Archivado |
| Cliente | `client.email` + `client.first_name last_name` | Click in client name jumps to `/platform/clients/:id` |
| Progreso | computed % (completed deliverables / total) | Thin progress bar |
| Bugs abiertos | computed count of open bugs | Red badge when > 0 |
| Solicitudes pendientes | computed count of pending change-requests | Amber badge when > 0 |
| Próximo entregable | next-due deliverable name + date | Empty when none upcoming |
| Última actividad | most recent of (bug, change, deliverable, payment, project update) | Ordered desc by default |
| `›` | chevron | Whole row navigates to `/platform/projects/:id`. No dropdown menu. |

### 4.2 Columns (client role)

Client sees a subset (no Cliente column, no Acciones, no Solicitudes count
since "open by them" already counts):

| Column |
|---|
| Proyecto |
| Progreso |
| Bugs abiertos |
| Próximo entregable |
| Última actividad |
| `›` |

### 4.3 Controls

- Status filter chips: **Activos** (default) / Pausados / Completados / Archivados / Todos.
- Search by project name or client.
- "Nuevo proyecto" button (admin only) — opens the proposal-based wizard (§7).
- Pagination: not on day one; if list exceeds 50 rows, add server-side pagination later.

## 5. Clients table (`/platform/clients`)

Refines the existing table in `frontend/pages/platform/clients/index.vue`.

### 5.1 Columns

| Column | Source | Notes |
|---|---|---|
| Cliente | `first_name last_name` + `email` | "Inactivo" badge when `is_active=False`. Subtle clock icon + tooltip "Sin acceso aún" when `last_login is None`. |
| Empresa | `company_name` | Empty when blank |
| Proyectos | active count / total count | Ej. "2 / 3" |
| Plan hosting | `hosting_plan` | Mensual · Trimestral · Semestral. Chip. |
| Próx. renovación | `hosting_renewal_at` | Amber text when within 30 days |
| Valor renovación | `hosting_renewal_value` | Exact amount of next billing |
| Última actividad | most recent of (last_login, last project update) | Sortable |
| `›` | chevron | Row navigates to `/platform/clients/:id` |

### 5.2 Controls

- Filter: Activos (default) / Inactivos / Todos.
- Search by name, email, or company.
- "Nuevo cliente" button → sends invitation (existing flow, unchanged).
- Same pagination policy as Projects.

### 5.3 Client detail (`/platform/clients/:id`) — high-level only

Out of scope for full UI design this round, but the structure is fixed:

- **Header:** identity + actions (reenviar invitación, desactivar, editar).
- **Proyectos** section: mini-table of this client's projects (subset of §4.1 columns).
- **Hosting** section: current plan (cycle, monthly equivalent, fecha inicio, próxima renovación, valor por ciclo), history of past payments. UI for full hosting management is deferred to a follow-up spec.
- **Configuración del cliente** section: email/company/etc., wired to existing endpoints.

## 6. Project shell (`/platform/projects/:id/*`)

A new layout wraps every route under `/platform/projects/:id/`.

### 6.1 Layout

```
┌─ Project header ────────────────────────────────────────────────┐
│  Proyectos / <project name>          [Activo]                    │
│  Cliente: <name> · Inició: <date> · Próx. entrega: <date>        │
└─────────────────────────────────────────────────────────────────┘

┌─ Secondary sidebar ┐  ┌─ Sub-module content ────────────────────┐
│  • Resumen         │  │                                          │
│  • Tablero         │  │   (whichever sub-route is active)        │
│  • Solicitudes     │  │                                          │
│  • Bugs            │  │                                          │
│  • Entregables     │  │                                          │
│  • Pagos           │  │                                          │
│  • Cuentas de cobro│  │                                          │
│  • Modelo de datos │  │                                          │
│  • Accesos         │  │                                          │
└────────────────────┘  └──────────────────────────────────────────┘
```

- Breadcrumb (`Proyectos / <name>`) is the only "back" affordance; clicking
  "Proyectos" returns to the table.
- The main `PlatformSidebar` stays visible on the far left.
- The secondary sidebar lives on the page itself (inside the project layout),
  not in the global sidebar.

### 6.2 Sub-routes

| Sub-module | Route | Current state |
|---|---|---|
| Resumen | `/platform/projects/:id` (root of shell) | Exists; refactor as the overview page |
| Tablero | `/platform/projects/:id/board` | Exists |
| Solicitudes | `/platform/projects/:id/changes` | Exists |
| Bugs | `/platform/projects/:id/bugs` | Exists |
| Entregables | `/platform/projects/:id/deliverables` | Exists |
| Pagos | `/platform/projects/:id/payments` | Exists |
| Cuentas de cobro | `/platform/projects/:id/collection-accounts` | Exists |
| Modelo de datos | `/platform/projects/:id/data-model` | Exists |
| Accesos | `/platform/projects/:id/access` | **New** — content migrated from the deleted `/platform/access` |

### 6.3 Resumen (`/platform/projects/:id`)

The root route of the shell. Refactor of the current
`frontend/pages/platform/projects/[id]/index.vue`. Sections, top to bottom:

1. **KPIs:** progreso %, bugs abiertos, solicitudes pendientes, próximo entregable. Same numbers as the row in the global table, just larger.
2. **Fases** (new — see §7): drag-and-drop list of proposals attached to this project, with actions to add/reorder/remove.
3. **Últimas N en cada módulo:** small section per sub-module (3-5 latest items in Bugs, Solicitudes, Entregables, Pagos) with a "Ver todos" link to the sub-route.
4. **Acciones del proyecto:** editar, archivar, eliminar.

Edit/archive/delete are concentrated here — never in the global table row.

## 7. Project creation from proposals (phases)

### 7.1 Data model

New model `ProjectPhase` in `backend/accounts/models.py`:

```python
class ProjectPhase(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='phases',
    )
    business_proposal = models.ForeignKey(
        'content.BusinessProposal',
        on_delete=models.PROTECT,
        related_name='project_phases',
    )
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = [('project', 'business_proposal')]
```

Notes:
- `on_delete=PROTECT` for the proposal FK: deleting a proposal that is part of an
  active project must fail loudly. Detach the phase first.
- `unique_together` prevents the same proposal being linked twice to the same project.
- `order` is admin-controlled; a phase add appends with `order = max+1`, and
  reorders rewrite the whole list atomically.

The existing `Project.linked_business_proposal()` helper returns the **first**
phase's proposal (i.e., `phases.first().business_proposal`) — same semantics
as today, just routed through the new model.

### 7.2 Backend endpoints

All under `/api/accounts/`:

| Method | Route | Body / response |
|---|---|---|
| POST | `projects/` (existing, extended) | Accepts `phases: [{proposal_id, order}, …]` plus existing fields. Atomically creates the project + all phases. |
| GET | `projects/:id/phases/` | List of phases, ordered. Each: `{id, order, proposal: {id, title, signed_at, total_amount}}` |
| POST | `projects/:id/phases/` | `{proposal_id, order?}` — appends at end if `order` omitted. |
| PATCH | `projects/:id/phases/reorder/` | `[{id, order}, …]` — bulk rewrite. Transactional. |
| DELETE | `projects/:id/phases/:phaseId/` | Detaches the phase (does not delete the proposal). |
| GET | `clients/:id/eligible-proposals/` | Proposals belonging to this client that are **signed/approved** AND not already in any active project. |

### 7.3 Create-project wizard (frontend)

Modal triggered from the "Nuevo proyecto" button on `/platform/projects`. Three steps.

**Step 1 — Cliente**

Searchable dropdown over existing clients. Required.

**Step 2 — Propuestas** (multi-select reorderable)

Two-column layout:

- Left: available proposals for the selected client (from
  `GET /clients/:id/eligible-proposals/`). Each row is a checkbox + proposal title + signed date + total.
- Right: selected proposals as draggable cards (Fase 1, Fase 2, …). Drag handles reorder. An `×` button on each card removes it.

Both columns sync in real time: checking on the left adds a card on the right
(appended at the end); removing on the right unchecks on the left.

At least one proposal must be selected to advance.

**Step 3 — Confirmación**

Summary: client name, ordered phase list, total combined amount (sum of
proposal totals). "Crear proyecto" button submits the wizard.

On success: navigates to the new project's Resumen.

### 7.4 Phases section on the Resumen

`frontend/components/platform/projects/PhaseList.vue` (new):

```
┌─ Fases del proyecto ───────────────────────────────────────┐
│ ⠿ 1. <proposal.title>             $<total>  [editar] [× ]  │
│ ⠿ 2. <proposal.title>             $<total>  [editar] [× ]  │
│ ⠿ 3. <proposal.title>             $<total>  [editar] [× ]  │
│                                                            │
│ [+ Agregar fase desde propuesta del cliente]               │
└────────────────────────────────────────────────────────────┘
```

- `⠿` is a drag handle; releasing fires
  `PATCH /projects/:id/phases/reorder/`.
- `[editar]` opens the proposal in the panel (`/panel/proposals/:id/edit`) in
  a new tab. **No inline edit of proposal content from the platform.**
- `[× ]` opens a confirm dialog and then calls
  `DELETE /projects/:id/phases/:phaseId/`.
- `[+ Agregar fase]` opens a mini-modal: list of eligible proposals for the
  project's client, multi-select, "Agregar" appends them to the end of the
  phase list.

Reuses `vuedraggable` (already in `package.json`).

## 8. Migration plan

Order matters — the deletions only land at the end so the user never sees a
broken intermediate state.

| Phase | Scope | Why this order |
|---|---|---|
| **A. Backend support** | Add the computed/aggregated fields to `GET /projects/` (`bugs_open_count`, `changes_pending_count`, `progress_percent`, `last_activity_at`, `next_deliverable`) and `GET /clients/` (`hosting_plan`, `hosting_renewal_at`, `hosting_renewal_value`, `last_activity_at`, `has_logged_in_once`, `active_projects_count`, `total_projects_count`). Add `ProjectPhase` model + migration + backfill. | New UI cannot render until these fields exist; phase model is a prerequisite for the new create wizard. |
| **B. Tables + project shell** | Refactor `projects/index.vue` to a table. Refine `clients/index.vue` columns. Build the project shell layout with secondary sidebar + breadcrumb. Build the Resumen page with KPIs + Phases section. Create `projects/[id]/access.vue`. | Drops the new structure in place without touching the sidebar or any global page. |
| **C. Create-project wizard** | New modal/page with the 3-step flow. Hooked to the new endpoints. | Independent of A/B except for the phase backend; can land any time after A. |
| **D. Sidebar + middleware + landing** | Rewrite `PlatformSidebar.vue`. Change the redirect root from `/platform/dashboard` to `/platform/projects`. | This is the visible cutover. After this, the user sees the new IA. |
| **E. Cleanup** | Delete the obsolete pages (`dashboard.vue`, `board.vue`, `bugs.vue`, `changes.vue`, `deliverables.vue`, `payments.vue`, `collection-accounts/*`, `access.vue`). Update `viewCatalog.js`. Update or delete the E2E specs that target these pages. Add 301 redirects from old global URLs to `/platform/projects` for bookmark grace. | At the end, when nothing references the deleted pages. |

Each phase is a separate PR (or at minimum a separate commit cluster) so the
review surface stays tractable.

## 9. Backend changes summary

### 9.1 New model + migration

- `ProjectPhase` (§7.1).
- Backfill migration: for every existing `Project`, find the
  `BusinessProposal` currently linked via the first Deliverable, create a
  `ProjectPhase(order=1)`. Projects without a linked proposal skip
  silently.

### 9.2 Aggregated fields on existing endpoints

`GET /api/accounts/projects/` — add:

| Field | Computation |
|---|---|
| `bugs_open_count` | `BugReport.objects.filter(project=p, status__in=['open','in_progress']).count()` |
| `changes_pending_count` | `ChangeRequest.objects.filter(project=p, status='pending').count()` |
| `progress_percent` | (already `progress` field on `Project`) — surface in serializer if not already |
| `last_activity_at` | `MAX(latest bug update, latest change update, latest deliverable update, latest payment update, project.updated_at)` |
| `next_deliverable` | `{id, name, due_date}` of the soonest non-completed deliverable; `null` if none |

`GET /api/accounts/clients/` — add:

| Field | Computation |
|---|---|
| `hosting_plan` | From the client's active hosting subscription |
| `hosting_renewal_at` | From the subscription |
| `hosting_renewal_value` | Next charge amount on the subscription |
| `active_projects_count` | `Project.objects.filter(client=u, status='active').count()` |
| `total_projects_count` | `Project.objects.filter(client=u).exclude(status='archived').count()` |
| `last_activity_at` | `MAX(user.last_login, latest update across user's projects)` |
| `has_logged_in_once` | `user.last_login is not None` |

Implementation note: these are likely best computed in the serializer with
prefetches or annotations to avoid N+1. The current `ClientListSerializer`
already exists; extend it.

### 9.3 New endpoints

The 5 phase endpoints from §7.2.

### 9.4 Hosting subscription cycles

Verify the existing subscription model supports the three plan options
(Mensual / Trimestral / Semestral). If only a subset is supported today,
either extend the choices or document the current state. (This will be
confirmed during the implementation plan.)

## 10. Frontend changes summary

### 10.1 New components

- `frontend/components/platform/projects/PhaseSelectorModal.vue` — the 3-step create wizard (§7.3).
- `frontend/components/platform/projects/PhaseList.vue` — the drag-and-drop phase list on the Resumen (§7.4).
- `frontend/components/platform/projects/ProjectShell.vue` (or a layout) — header + secondary sidebar + breadcrumb wrapper.
- `frontend/components/platform/projects/ProjectSecondarySidebar.vue` — the 9-item nav.
- `frontend/components/platform/projects/ProjectsTable.vue` — replaces the cards grid.
- `frontend/components/platform/clients/ClientsTable.vue` — extracted from the current page (if not already a component) and augmented with the new columns.

### 10.2 Modified pages

- `frontend/pages/platform/projects/index.vue` — use `ProjectsTable`.
- `frontend/pages/platform/clients/index.vue` — use the augmented columns.
- `frontend/pages/platform/projects/[id]/index.vue` — become the Resumen with KPIs, Phases, and last-N sections.
- `frontend/pages/platform/projects/[id]/*` — wrapped by `ProjectShell`.
- `frontend/pages/platform/index.vue` — redirect target changed from `/platform/dashboard` to `/platform/projects`.

### 10.3 New page

- `frontend/pages/platform/projects/[id]/access.vue` — content migrated from the deleted `frontend/pages/platform/access.vue`, scoped to one project's credentials.

### 10.4 Deleted pages

- `frontend/pages/platform/dashboard.vue`
- `frontend/pages/platform/board.vue`
- `frontend/pages/platform/bugs.vue`
- `frontend/pages/platform/changes.vue`
- `frontend/pages/platform/deliverables.vue`
- `frontend/pages/platform/payments.vue`
- `frontend/pages/platform/collection-accounts/index.vue`
- `frontend/pages/platform/collection-accounts/[id].vue`
- `frontend/pages/platform/access.vue`

### 10.5 Modified config / middleware

- `frontend/components/platform/PlatformSidebar.vue` — rewritten per §3.
- `frontend/middleware/platform-auth.js` — root redirect target updated.
- `frontend/config/viewCatalog.js` — remove entries for deleted pages; update `audience` for the surviving admin pages.

### 10.6 Stores / composables

- `frontend/stores/platform-projects.js` — extend to handle phases CRUD; expose
  `createWithPhases(payload)`, `addPhase`, `removePhase`, `reorderPhases`, and
  `loadEligibleProposals(clientId)`.
- The existing project-specific stores (bugs, changes, deliverables) need no
  changes — they were already scoped by project.

## 11. Testing strategy

### 11.1 Backend

New tests in `backend/accounts/tests/`:

- `test_project_phases_model.py` — model integrity (unique_together, ordering, cascade rules).
- `test_project_phases_views.py` — the 5 new endpoints (happy path + permission + edge cases).
- `test_projects_aggregated_fields.py` — the new computed fields on `GET /projects/` (mock a project with bugs/changes/etc. and assert the response).
- `test_clients_aggregated_fields.py` — same for `GET /clients/`.
- Migration test: backfill of `ProjectPhase` for an existing project with a Deliverable-linked proposal.

Sized roughly: 6 model tests, 12 endpoint tests, 4 aggregation tests, 1 migration test = ~23 backend tests.

### 11.2 Frontend unit

- `frontend/test/stores/platform-projects.phases.test.js` — phase actions on the store.
- `frontend/test/components/platform/projects/PhaseList.test.js` — drag-and-drop, add, remove (mock `vuedraggable`).
- `frontend/test/components/platform/projects/PhaseSelectorModal.test.js` — 3-step wizard, validation gates.
- `frontend/test/components/platform/projects/ProjectsTable.test.js` — column rendering, filters, chevron navigation.

### 11.3 Frontend E2E

Update or replace these existing specs:

- `frontend/e2e/platform/platform-dashboard.spec.js` — delete (Dashboard is gone) **or** replace with a "root redirects to projects" smoke.
- `frontend/e2e/platform/platform-bug-reports.spec.js` — re-target to project-scoped routes.
- `frontend/e2e/platform/platform-change-requests.spec.js` — same.
- `frontend/e2e/platform/platform-deliverables.spec.js` — same.
- `frontend/e2e/platform/platform-collection-accounts.spec.js` — same.
- `frontend/e2e/platform/platform-access.spec.js` — re-point to `/platform/projects/:id/access`.
- New `frontend/e2e/platform/platform-projects-table.spec.js` — table renders, chevron navigates.
- New `frontend/e2e/platform/platform-project-creation.spec.js` — the 3-step wizard.
- New `frontend/e2e/platform/platform-project-phases.spec.js` — add, reorder, remove.

## 12. Out of scope (this round)

- **Client role UX rework.** Clients keep their current views; we'll handle the client-side IA after the admin rework lands.
- **Hosting subscription management UI** beyond the Clients table columns + summary section. Editing a hosting plan, changing billing dates, manually charging — all stay in `/panel/` for now.
- **Bulk operations on projects or clients.** No "select multiple rows and archive" in this round.
- **Global search across projects/clients.** The per-table search is enough for MVP.
- **Notifications page restructure.** Stays as-is.
- **Profile/Configuración page.** Stays as-is.
- **i18n.** New components match the existing convention (hardcoded Spanish on the platform pages).
- **Mobile-first layout for the secondary sidebar.** Desktop-first; mobile gets a collapsed sub-nav we'll polish later.

## 13. Risks

| Risk | Mitigation |
|---|---|
| Bookmarks and external links to `/platform/board`, `/platform/bugs`, etc. | Add 301 redirects from each deleted route to `/platform/projects` during cleanup (phase E). Document the redirect map. |
| Existing project rows without a linked BusinessProposal break the migration | Backfill migration skips projects with no proposal. They render with empty Phases section; admin can attach proposals manually post-deploy. |
| Phase reorder race conditions if two admins edit the same project | Use a transactional bulk PATCH (`/phases/reorder/`) that rewrites the full list. Last writer wins is acceptable for MVP. |
| Aggregated fields on `/projects/` and `/clients/` introduce N+1 query risk | Implement with `annotate()` + `prefetch_related()`. Add a slow-query test in `test_projects_aggregated_fields.py` (assert query count). |
| Client role might rely on the global Tablero/Bugs pages we are deleting | Out of scope explicitly. The 301 redirects added in phase E (from `/platform/board`, `/platform/bugs`, etc. to `/platform/projects`) catch both roles, so no 404s. From `/platform/projects` the client picks one of their projects. Client IA will be re-designed in a follow-up spec. |
| `linked_business_proposal()` helper currently returns the first proposal via Deliverable — call sites may break when we shift to `ProjectPhase` | Keep the helper, change its implementation to return `self.phases.first().business_proposal if self.phases.exists() else None`. Same return shape. |

## 14. Open questions to confirm during implementation

- Does the existing hosting subscription model already support all three cycles (Mensual / Trimestral / Semestral)? If only a subset, we either extend or document.
- The `BusinessProposal` model in `content` — what is the "signed/approved" state field that filters eligible proposals? Confirm during phase A.
- The `ChangeRequest` status value used for "pending" in §9.2 — confirm during phase A by reading the model choices.
- The current `Project.payment_milestones` and `hosting_tiers` JSON fields come from the linked proposal. When a project has multiple phases, do these aggregate across phases or stay tied to the first phase? Default: keep tied to first phase for now; revisit if the user reports it.
