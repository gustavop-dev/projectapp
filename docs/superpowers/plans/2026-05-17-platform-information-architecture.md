# Platform Information Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `/platform/*` admin navigation from dual-scope (global module pages + per-project copies) to strict drill-down, replace the projects cards grid with a table, and add a multi-proposal phase model to project creation.

**Architecture:** Five sequential migration phases (A backend → B tables/shell → C wizard → D sidebar cutover → E cleanup) so users never see a broken intermediate state. State machine for the new "phases" model is enforced by a `ProjectPhase` join table with an explicit `order` column. The redesign deletes 9 pages and adds 3 (Resumen refactor, project-scoped Accesos, plus the wizard modal).

**Tech Stack:** Django 5 + DRF, SimpleJWT, Nuxt 3 + Vue 3 + Pinia (Options API), Tailwind utility classes, `vuedraggable` (already in `package.json`), Jest + Vue Test Utils for unit specs, Playwright for E2E.

**Spec:** `docs/superpowers/specs/2026-05-17-platform-information-architecture-design.md`

**Branch:** `feat/17052026-platform-information-architecture` (already created from `main`).

---

## Working conventions

- Backend tests: `cd backend && source venv/bin/activate && pytest accounts/tests/<file> -v` (never run the full suite).
- Frontend unit: `npm --prefix frontend test -- test/path/file.test.js`.
- Frontend E2E: `npm --prefix frontend run e2e -- e2e/platform/<spec>` (default base URL `http://localhost:3000`; host-only setup is NOT on this branch).
- After every task: `cd backend && source venv/bin/activate && python manage.py check` (catches import/URL drift early).
- Commit prefix style: `FEAT:` / `FIX:` / `DOCS:` / `REFACTOR:` / `CHORE:`. No `Co-Authored-By` lines, no Claude attribution footer (per `CLAUDE.md`).

---

## File Structure

**Backend — create:**
- `backend/accounts/models.py` (append) — `ProjectPhase` model.
- `backend/accounts/migrations/00XX_project_phase.py` — schema + data backfill migration.
- `backend/accounts/services/project_phases.py` — phase CRUD logic.
- `backend/accounts/serializers.py` (append) — `ProjectPhaseSerializer`, `EligibleProposalSerializer`, augmented `ClientListSerializer` and `ProjectListSerializer`.
- `backend/accounts/tests/test_project_phases.py` — 14 model + service + view tests.
- `backend/accounts/tests/test_project_list_aggregates.py` — 5 tests for aggregated fields.
- `backend/accounts/tests/test_client_list_aggregates.py` — 5 tests for aggregated fields.
- `backend/accounts/tests/test_eligible_proposals.py` — 4 tests for the eligible-proposals endpoint.

**Backend — modify:**
- `backend/accounts/models.py` — `Project.linked_business_proposal()` routes through phases.
- `backend/accounts/views.py` — 5 phase views, 1 eligible-proposals view, augmented project/client list views.
- `backend/accounts/urls.py` — 6 new routes under `/projects/:id/phases/...` and `/clients/:id/eligible-proposals/`.

**Frontend — create:**
- `frontend/components/platform/projects/ProjectsTable.vue` — the new table.
- `frontend/components/platform/projects/ProjectShell.vue` — the per-project layout wrapper.
- `frontend/components/platform/projects/ProjectSecondarySidebar.vue` — the 9-item nav.
- `frontend/components/platform/projects/ProjectBreadcrumb.vue` — `Proyectos / <name>` header.
- `frontend/components/platform/projects/PhaseList.vue` — drag-and-drop phase list.
- `frontend/components/platform/projects/PhaseSelectorModal.vue` — 3-step create wizard.
- `frontend/pages/platform/projects/[id]/access.vue` — new project-scoped Accesos page.
- Frontend tests: 4 spec files matching components above.
- E2E specs: `platform-projects-table.spec.js`, `platform-project-creation.spec.js`, `platform-project-phases.spec.js`.

**Frontend — modify:**
- `frontend/pages/platform/projects/index.vue` — use `ProjectsTable`.
- `frontend/pages/platform/clients/index.vue` — augmented columns.
- `frontend/pages/platform/projects/[id]/index.vue` — refactor as Resumen.
- All other `frontend/pages/platform/projects/[id]/*.vue` — wrap via `ProjectShell`.
- `frontend/pages/platform/index.vue` — redirect target → `/platform/projects`.
- `frontend/components/platform/PlatformSidebar.vue` — rewritten.
- `frontend/middleware/platform-auth.js` — landing redirect updated.
- `frontend/config/viewCatalog.js` — entries adjusted.
- `frontend/stores/platform-projects.js` — phase actions.

**Frontend — delete (Phase E):**
- `frontend/pages/platform/dashboard.vue`
- `frontend/pages/platform/board.vue`
- `frontend/pages/platform/bugs.vue`
- `frontend/pages/platform/changes.vue`
- `frontend/pages/platform/deliverables.vue`
- `frontend/pages/platform/payments.vue`
- `frontend/pages/platform/collection-accounts/index.vue`
- `frontend/pages/platform/collection-accounts/[id].vue`
- `frontend/pages/platform/access.vue`

---

# PHASE A — Backend foundation

Goal of this phase: every backend field and endpoint the new UI needs is in place and tested. No frontend changes yet.

## Task 1 — `ProjectPhase` model + migration + backfill

**Files:**
- Modify: `backend/accounts/models.py`
- Create: `backend/accounts/migrations/00XX_project_phase.py`
- Create: `backend/accounts/tests/test_project_phases.py` (seeded with model tests in this task)

- [ ] **Step 1: Write the failing model tests**

`backend/accounts/tests/test_project_phases.py`:

```python
"""Tests for the ProjectPhase model and related helpers."""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from accounts.models import Project, ProjectPhase

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def client_user(db):
    return User.objects.create_user(
        username='client@example.com', email='client@example.com', password='x',
    )


@pytest.fixture
def project(client_user):
    return Project.objects.create(name='Test project', client=client_user)


@pytest.fixture
def business_proposal(client_user):
    from content.models import BusinessProposal
    return BusinessProposal.objects.create(
        title='Proposal A', client_email='client@example.com',
        client_name='Test Client',
    )


def test_phase_links_project_and_proposal_with_order(project, business_proposal):
    p = ProjectPhase.objects.create(
        project=project, business_proposal=business_proposal, order=1,
    )
    assert p.project == project
    assert p.business_proposal == business_proposal
    assert p.order == 1


def test_unique_constraint_blocks_same_proposal_twice_on_one_project(project, business_proposal):
    ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=1)
    with pytest.raises(IntegrityError):
        ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=2)


def test_ordering_by_order_field(project, business_proposal, client_user):
    from content.models import BusinessProposal
    p2 = BusinessProposal.objects.create(title='P2', client_email='c@example.com', client_name='X')
    ProjectPhase.objects.create(project=project, business_proposal=p2, order=2)
    ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=1)
    titles = [ph.business_proposal.title for ph in project.phases.all()]
    assert titles == ['Proposal A', 'P2']


def test_linked_business_proposal_returns_first_phase_proposal(project, business_proposal):
    ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=1)
    assert project.linked_business_proposal() == business_proposal


def test_linked_business_proposal_returns_none_when_no_phases(project):
    assert project.linked_business_proposal() is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_project_phases.py -v
```

Expected: `ImportError: cannot import name 'ProjectPhase'`.

- [ ] **Step 3: Append `ProjectPhase` model to `backend/accounts/models.py`**

Add at the end of the file (or after the Project class):

```python
class ProjectPhase(models.Model):
    """One phase of a Project, backed by a BusinessProposal from the panel.

    A project can have multiple phases (e.g. discovery, design, build),
    each corresponding to a separate signed proposal. Phases are ordered;
    `order=1` is the first phase, `order=2` is the second, etc.
    """

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
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'business_proposal'],
                name='unique_proposal_per_project',
            ),
        ]

    def __str__(self):
        return f'{self.project.name} — Fase {self.order}: {self.business_proposal.title}'
```

- [ ] **Step 4: Refactor `Project.linked_business_proposal()` to route through phases**

Replace the existing `linked_business_proposal` method on the `Project` class with:

```python
def linked_business_proposal(self):
    """Returns the first phase's BusinessProposal, or None.

    Kept for backwards compatibility with serializers and templates that
    expect a single proposal per project. New code should iterate
    `self.phases.all()` instead.
    """
    first = self.phases.select_related('business_proposal').first()
    return first.business_proposal if first else None
```

- [ ] **Step 5: Create the migration with backfill**

```
cd backend && source venv/bin/activate && python manage.py makemigrations accounts --name project_phase
```

Then edit the generated file (`00XX_project_phase.py`) to add a data backfill step. After the `CreateModel` operation, append:

```python
def backfill_phases_from_deliverables(apps, schema_editor):
    """For each existing Project, find the first proposal linked via a
    Deliverable and create a ProjectPhase row (order=1). Projects with no
    linked proposal are left without phases."""
    Project = apps.get_model('accounts', 'Project')
    ProjectPhase = apps.get_model('accounts', 'ProjectPhase')
    BusinessProposal = apps.get_model('content', 'BusinessProposal')

    for project in Project.objects.all():
        bp = BusinessProposal.objects.filter(
            deliverable__project_id=project.id,
        ).first()
        if bp is None:
            continue
        ProjectPhase.objects.get_or_create(
            project=project, business_proposal=bp,
            defaults={'order': 1},
        )


def reverse_backfill(apps, schema_editor):
    ProjectPhase = apps.get_model('accounts', 'ProjectPhase')
    ProjectPhase.objects.all().delete()


class Migration(migrations.Migration):
    # ... existing dependencies and operations ...

    operations = [
        # ... the auto-generated CreateModel(name='ProjectPhase', ...) ...
        migrations.RunPython(backfill_phases_from_deliverables, reverse_backfill),
    ]
```

- [ ] **Step 6: Run migration**

```
cd backend && source venv/bin/activate && python manage.py migrate
```

Expected: `Applying accounts.00XX_project_phase... OK`.

- [ ] **Step 7: Run tests to verify they pass**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_project_phases.py -v
```

Expected: 5 passed.

- [ ] **Step 8: Regression check — existing project tests still green**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_models.py -v
```

Expected: all green. If any test reads `Project.linked_business_proposal()`, it now goes through the phase relation — verify behavior matches.

- [ ] **Step 9: Commit**

```
git add backend/accounts/models.py backend/accounts/migrations/ backend/accounts/tests/test_project_phases.py
git commit -m "FEAT: ProjectPhase model with proposal ordering + backfill from deliverables"
```

---

## Task 2 — Phase service module (CRUD logic)

**Files:**
- Create: `backend/accounts/services/project_phases.py`
- Append to: `backend/accounts/tests/test_project_phases.py`

- [ ] **Step 1: Write failing service tests**

Append to `backend/accounts/tests/test_project_phases.py`:

```python
from accounts.services.project_phases import (
    PhaseError,
    add_phase,
    list_phases,
    remove_phase,
    reorder_phases,
)


def test_add_phase_appends_at_end_when_order_omitted(project, business_proposal):
    phase = add_phase(project, business_proposal)
    assert phase.order == 1
    from content.models import BusinessProposal
    p2 = BusinessProposal.objects.create(title='P2', client_email='c@e.co', client_name='X')
    phase2 = add_phase(project, p2)
    assert phase2.order == 2


def test_add_phase_rejects_duplicate(project, business_proposal):
    add_phase(project, business_proposal)
    with pytest.raises(PhaseError) as exc:
        add_phase(project, business_proposal)
    assert exc.value.code == 'duplicate_proposal'


def test_remove_phase_renumbers_remaining(project, business_proposal):
    from content.models import BusinessProposal
    p2 = BusinessProposal.objects.create(title='P2', client_email='c@e.co', client_name='X')
    p3 = BusinessProposal.objects.create(title='P3', client_email='c@e.co', client_name='X')
    ph1 = add_phase(project, business_proposal)
    ph2 = add_phase(project, p2)
    ph3 = add_phase(project, p3)
    remove_phase(project, ph2.id)
    remaining = list(project.phases.values_list('order', 'business_proposal__title').order_by('order'))
    assert remaining == [(1, 'Proposal A'), (2, 'P3')]


def test_reorder_phases_writes_new_order_atomically(project, business_proposal):
    from content.models import BusinessProposal
    p2 = BusinessProposal.objects.create(title='P2', client_email='c@e.co', client_name='X')
    p3 = BusinessProposal.objects.create(title='P3', client_email='c@e.co', client_name='X')
    ph1 = add_phase(project, business_proposal)
    ph2 = add_phase(project, p2)
    ph3 = add_phase(project, p3)
    reorder_phases(project, [
        {'id': ph3.id, 'order': 1},
        {'id': ph1.id, 'order': 2},
        {'id': ph2.id, 'order': 3},
    ])
    titles_in_order = [
        ph.business_proposal.title for ph in project.phases.all()
    ]
    assert titles_in_order == ['P3', 'Proposal A', 'P2']


def test_reorder_phases_rejects_phase_from_another_project(project, business_proposal, client_user):
    other = Project.objects.create(name='Other', client=client_user)
    from content.models import BusinessProposal
    p_other = BusinessProposal.objects.create(title='PO', client_email='c@e.co', client_name='X')
    phase_other = add_phase(other, p_other)
    ph1 = add_phase(project, business_proposal)
    with pytest.raises(PhaseError) as exc:
        reorder_phases(project, [
            {'id': phase_other.id, 'order': 1},
            {'id': ph1.id, 'order': 2},
        ])
    assert exc.value.code == 'invalid_phase_id'
```

- [ ] **Step 2: Run — expect ImportError**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_project_phases.py -v -k 'phase' 2>&1 | tail -5
```

- [ ] **Step 3: Create the service module**

`backend/accounts/services/project_phases.py`:

```python
"""Business logic for managing ProjectPhase rows."""
from django.db import transaction
from django.db.models import Max

from accounts.models import ProjectPhase


class PhaseError(Exception):
    """Service-level error with a stable code + optional payload extras."""

    def __init__(self, code: str, http_status: int = 400, extra: dict | None = None):
        self.code = code
        self.http_status = http_status
        self.extra = extra or {}
        super().__init__(code)


def list_phases(project):
    """Returns the project's phases as a QuerySet ordered by `order`."""
    return project.phases.select_related('business_proposal').order_by('order')


def add_phase(project, proposal, order: int | None = None) -> ProjectPhase:
    """Attach a proposal as a new phase. Appends at end when `order` omitted.
    Raises PhaseError(code='duplicate_proposal') if the proposal is already
    in this project."""
    if project.phases.filter(business_proposal=proposal).exists():
        raise PhaseError('duplicate_proposal')
    if order is None:
        max_order = project.phases.aggregate(m=Max('order'))['m'] or 0
        order = max_order + 1
    return ProjectPhase.objects.create(
        project=project, business_proposal=proposal, order=order,
    )


def remove_phase(project, phase_id: int) -> None:
    """Detach a phase. Renumbers remaining phases to 1..N."""
    try:
        phase = project.phases.get(id=phase_id)
    except ProjectPhase.DoesNotExist:
        raise PhaseError('phase_not_found', http_status=404)
    with transaction.atomic():
        phase.delete()
        for new_order, ph in enumerate(project.phases.order_by('order'), start=1):
            if ph.order != new_order:
                ph.order = new_order
                ph.save(update_fields=['order'])


def reorder_phases(project, items: list[dict]) -> None:
    """Bulk-rewrite phase ordering. `items` is a list of {id, order} pairs
    covering every existing phase of the project. Atomic."""
    given_ids = {item['id'] for item in items}
    existing_ids = set(project.phases.values_list('id', flat=True))
    if given_ids != existing_ids:
        raise PhaseError('invalid_phase_id', extra={
            'expected': sorted(existing_ids), 'received': sorted(given_ids),
        })
    with transaction.atomic():
        for item in items:
            ProjectPhase.objects.filter(id=item['id']).update(order=item['order'])
```

- [ ] **Step 4: Run tests — expect pass**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_project_phases.py -v 2>&1 | tail -8
```

Expected: 10 passed (5 model + 5 service).

- [ ] **Step 5: Commit**

```
git add backend/accounts/services/project_phases.py backend/accounts/tests/test_project_phases.py
git commit -m "FEAT: project phases service (add/list/remove/reorder with renumbering)"
```

---

## Task 3 — Phase endpoints (5 routes)

**Files:**
- Modify: `backend/accounts/serializers.py`
- Modify: `backend/accounts/views.py`
- Modify: `backend/accounts/urls.py`
- Append to: `backend/accounts/tests/test_project_phases.py`

- [ ] **Step 1: Write failing HTTP-level tests**

Append to `backend/accounts/tests/test_project_phases.py`:

```python
from rest_framework.test import APIClient


@pytest.fixture
def admin_user(db):
    from accounts.models import UserProfile
    u = User.objects.create_user(
        username='admin@example.com', email='admin@example.com', password='x',
    )
    UserProfile.objects.create(user=u, role='admin', is_onboarded=True, profile_completed=True)
    return u


@pytest.fixture
def authed_client(admin_user):
    from accounts.services.tokens import get_tokens_for_user
    tokens = get_tokens_for_user(admin_user)
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
    return c


def test_list_phases_endpoint_returns_ordered_phases(authed_client, project, business_proposal):
    add_phase(project, business_proposal)
    resp = authed_client.get(f'/api/accounts/projects/{project.id}/phases/')
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]['proposal']['title'] == 'Proposal A'


def test_add_phase_endpoint(authed_client, project, business_proposal):
    resp = authed_client.post(
        f'/api/accounts/projects/{project.id}/phases/',
        {'proposal_id': business_proposal.id},
        format='json',
    )
    assert resp.status_code == 201
    assert resp.json()['order'] == 1


def test_add_phase_endpoint_rejects_duplicate(authed_client, project, business_proposal):
    add_phase(project, business_proposal)
    resp = authed_client.post(
        f'/api/accounts/projects/{project.id}/phases/',
        {'proposal_id': business_proposal.id},
        format='json',
    )
    assert resp.status_code == 400
    assert resp.json()['detail'] == 'duplicate_proposal'


def test_remove_phase_endpoint(authed_client, project, business_proposal):
    phase = add_phase(project, business_proposal)
    resp = authed_client.delete(f'/api/accounts/projects/{project.id}/phases/{phase.id}/')
    assert resp.status_code == 204
    assert project.phases.count() == 0


def test_reorder_phases_endpoint(authed_client, project, business_proposal):
    from content.models import BusinessProposal
    p2 = BusinessProposal.objects.create(title='P2', client_email='c@e.co', client_name='X')
    ph1 = add_phase(project, business_proposal)
    ph2 = add_phase(project, p2)
    resp = authed_client.patch(
        f'/api/accounts/projects/{project.id}/phases/reorder/',
        [{'id': ph2.id, 'order': 1}, {'id': ph1.id, 'order': 2}],
        format='json',
    )
    assert resp.status_code == 200
    titles = [ph.business_proposal.title for ph in project.phases.all()]
    assert titles == ['P2', 'Proposal A']
```

- [ ] **Step 2: Run — expect 404 (routes don't exist)**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_project_phases.py -v -k 'endpoint' 2>&1 | tail -5
```

- [ ] **Step 3: Add `ProjectPhaseSerializer` to `backend/accounts/serializers.py`**

Append after `ClientListSerializer`:

```python
class _NestedProposalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    signed_at = serializers.DateTimeField(allow_null=True)
    total_amount = serializers.SerializerMethodField()

    def get_total_amount(self, obj):
        # BusinessProposal stores total in `total_investment` or similar field;
        # fall back to 0 if not present.
        return getattr(obj, 'total_investment', None) or 0


class ProjectPhaseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    order = serializers.IntegerField()
    proposal = serializers.SerializerMethodField()

    def get_proposal(self, obj):
        return _NestedProposalSerializer(obj.business_proposal).data
```

- [ ] **Step 4: Add the 4 views to `backend/accounts/views.py`**

Append to the auth section (or create a new "Project phases" section) near the other project views:

```python
from accounts.services.project_phases import (
    PhaseError,
    add_phase,
    list_phases,
    remove_phase,
    reorder_phases,
)
from accounts.serializers import ProjectPhaseSerializer


def _get_project_or_404(project_id, user):
    from accounts.models import Project
    qs = Project.objects.filter(id=project_id)
    profile = getattr(user, 'profile', None)
    if profile and profile.role != 'admin':
        qs = qs.filter(client=user)
    project = qs.first()
    if project is None:
        return None
    return project


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def project_phases_view(request, project_id):
    project = _get_project_or_404(project_id, request.user)
    if project is None:
        return Response({'detail': 'project_not_found'}, status=404)
    if request.method == 'GET':
        return Response(ProjectPhaseSerializer(list_phases(project), many=True).data)
    # POST
    proposal_id = request.data.get('proposal_id')
    if not proposal_id:
        return Response({'detail': 'proposal_id required'}, status=400)
    from content.models import BusinessProposal
    proposal = BusinessProposal.objects.filter(id=proposal_id).first()
    if proposal is None:
        return Response({'detail': 'proposal_not_found'}, status=404)
    try:
        phase = add_phase(project, proposal, order=request.data.get('order'))
    except PhaseError as exc:
        return Response({'detail': exc.code, **exc.extra}, status=exc.http_status)
    return Response(ProjectPhaseSerializer(phase).data, status=201)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminRole])
def project_phase_detail_view(request, project_id, phase_id):
    project = _get_project_or_404(project_id, request.user)
    if project is None:
        return Response({'detail': 'project_not_found'}, status=404)
    try:
        remove_phase(project, phase_id)
    except PhaseError as exc:
        return Response({'detail': exc.code, **exc.extra}, status=exc.http_status)
    return Response(status=204)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdminRole])
def project_phases_reorder_view(request, project_id):
    project = _get_project_or_404(project_id, request.user)
    if project is None:
        return Response({'detail': 'project_not_found'}, status=404)
    items = request.data
    if not isinstance(items, list):
        return Response({'detail': 'expected_list'}, status=400)
    try:
        reorder_phases(project, items)
    except PhaseError as exc:
        return Response({'detail': exc.code, **exc.extra}, status=exc.http_status)
    return Response(ProjectPhaseSerializer(list_phases(project), many=True).data)
```

- [ ] **Step 5: Wire URLs in `backend/accounts/urls.py`**

Add the imports next to the existing project view imports:

```python
from accounts.views import (
    # ... existing imports ...
    project_phases_view,
    project_phase_detail_view,
    project_phases_reorder_view,
)
```

And after the existing `path('projects/<int:project_id>/', ...)` add:

```python
    path('projects/<int:project_id>/phases/', project_phases_view, name='platform-project-phases'),
    path('projects/<int:project_id>/phases/reorder/', project_phases_reorder_view, name='platform-project-phases-reorder'),
    path('projects/<int:project_id>/phases/<int:phase_id>/', project_phase_detail_view, name='platform-project-phase-detail'),
```

(The `reorder/` path must come **before** `<int:phase_id>/` so Django matches it first.)

- [ ] **Step 6: Run all phase tests**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_project_phases.py -v 2>&1 | tail -8
```

Expected: 15 passed (5 model + 5 service + 5 endpoint).

- [ ] **Step 7: Commit**

```
git add backend/accounts/serializers.py backend/accounts/views.py backend/accounts/urls.py backend/accounts/tests/test_project_phases.py
git commit -m "FEAT: project phases REST endpoints (list/create/delete/reorder)"
```

---

## Task 4 — Eligible proposals endpoint

**Files:**
- Modify: `backend/accounts/views.py`
- Modify: `backend/accounts/urls.py`
- Create: `backend/accounts/tests/test_eligible_proposals.py`

- [ ] **Step 1: Write failing tests**

`backend/accounts/tests/test_eligible_proposals.py`:

```python
"""Tests for GET /api/accounts/clients/:id/eligible-proposals/."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Project, ProjectPhase, UserProfile
from accounts.services.project_phases import add_phase
from accounts.services.tokens import get_tokens_for_user

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(db):
    u = User.objects.create_user(username='a@e.co', email='a@e.co', password='x')
    UserProfile.objects.create(user=u, role='admin', is_onboarded=True, profile_completed=True)
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {get_tokens_for_user(u)["access"]}')
    return c


@pytest.fixture
def client_user(db):
    u = User.objects.create_user(username='c@e.co', email='c@e.co', password='x')
    UserProfile.objects.create(user=u, role='client', is_onboarded=True, profile_completed=True)
    return u


def _make_proposal(email, title='P', signed=True):
    from content.models import BusinessProposal
    return BusinessProposal.objects.create(
        title=title, client_email=email, client_name='X',
        signed_at='2026-01-01' if signed else None,
    )


def test_eligible_proposals_only_returns_clients_signed_unattached(admin_client, client_user):
    mine_signed_free = _make_proposal('c@e.co', 'A')
    mine_signed_attached = _make_proposal('c@e.co', 'B')
    mine_unsigned = _make_proposal('c@e.co', 'C', signed=False)
    other_signed = _make_proposal('other@e.co', 'D')

    project = Project.objects.create(name='P', client=client_user)
    add_phase(project, mine_signed_attached)

    resp = admin_client.get(f'/api/accounts/clients/{client_user.id}/eligible-proposals/')
    assert resp.status_code == 200
    titles = sorted(p['title'] for p in resp.json())
    assert titles == ['A']  # only the free, signed, client-matched one


def test_eligible_proposals_returns_empty_when_none(admin_client, client_user):
    resp = admin_client.get(f'/api/accounts/clients/{client_user.id}/eligible-proposals/')
    assert resp.status_code == 200
    assert resp.json() == []


def test_eligible_proposals_requires_admin(client_user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {get_tokens_for_user(client_user)["access"]}')
    resp = c.get(f'/api/accounts/clients/{client_user.id}/eligible-proposals/')
    assert resp.status_code in (403, 401)


def test_eligible_proposals_404_for_unknown_client(admin_client):
    resp = admin_client.get('/api/accounts/clients/9999999/eligible-proposals/')
    assert resp.status_code == 404
```

- [ ] **Step 2: Run — expect failure**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_eligible_proposals.py -v 2>&1 | tail -5
```

- [ ] **Step 3: Add view to `backend/accounts/views.py`**

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminRole])
def client_eligible_proposals_view(request, user_id):
    """Returns signed BusinessProposals for the client that are not already
    attached to any project as a phase."""
    user = User.objects.filter(id=user_id).first()
    if user is None:
        return Response({'detail': 'client_not_found'}, status=404)

    from content.models import BusinessProposal
    proposals = BusinessProposal.objects.filter(
        client_email__iexact=user.email,
        signed_at__isnull=False,
    ).exclude(
        project_phases__isnull=False,
    ).order_by('-signed_at')

    data = [
        {'id': p.id, 'title': p.title, 'signed_at': p.signed_at,
         'total_amount': getattr(p, 'total_investment', None) or 0}
        for p in proposals
    ]
    return Response(data)
```

- [ ] **Step 4: Wire URL**

In `backend/accounts/urls.py`, add the import:

```python
from accounts.views import (
    # ... existing imports ...
    client_eligible_proposals_view,
)
```

And append next to `clients/<int:user_id>/...`:

```python
    path('clients/<int:user_id>/eligible-proposals/', client_eligible_proposals_view, name='platform-client-eligible-proposals'),
```

- [ ] **Step 5: Run tests — expect pass**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_eligible_proposals.py -v 2>&1 | tail -8
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```
git add backend/accounts/views.py backend/accounts/urls.py backend/accounts/tests/test_eligible_proposals.py
git commit -m "FEAT: eligible-proposals endpoint for project phase wizard"
```

---

## Task 5 — Aggregated fields on `GET /projects/`

**Files:**
- Modify: `backend/accounts/serializers.py`
- Create: `backend/accounts/tests/test_project_list_aggregates.py`

- [ ] **Step 1: Write failing tests**

`backend/accounts/tests/test_project_list_aggregates.py`:

```python
"""Tests for the aggregated fields on GET /api/accounts/projects/."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import (
    BugReport, ChangeRequest, Deliverable, Project, UserProfile,
)
from accounts.services.tokens import get_tokens_for_user

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client_user(db):
    u = User.objects.create_user(username='a@e.co', email='a@e.co', password='x')
    UserProfile.objects.create(user=u, role='admin', is_onboarded=True, profile_completed=True)
    return u


@pytest.fixture
def client_user(db):
    u = User.objects.create_user(username='c@e.co', email='c@e.co', password='x')
    UserProfile.objects.create(user=u, role='client', is_onboarded=True, profile_completed=True)
    return u


@pytest.fixture
def authed(admin_client_user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {get_tokens_for_user(admin_client_user)["access"]}')
    return c


def test_project_list_includes_bugs_open_count(authed, client_user):
    p = Project.objects.create(name='P1', client=client_user)
    deliverable = Deliverable.objects.create(project=p, name='D1')
    BugReport.objects.create(deliverable=deliverable, reported_by=client_user, status=BugReport.STATUS_REPORTED, title='B1', description='x')
    BugReport.objects.create(deliverable=deliverable, reported_by=client_user, status=BugReport.STATUS_RESOLVED, title='B2', description='x')
    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)
    assert row['bugs_open_count'] == 1


def test_project_list_includes_changes_pending_count(authed, client_user):
    p = Project.objects.create(name='P1', client=client_user)
    ChangeRequest.objects.create(project=p, requested_by=client_user, title='C1', description='x', status=ChangeRequest.STATUS_PENDING)
    ChangeRequest.objects.create(project=p, requested_by=client_user, title='C2', description='x', status=ChangeRequest.STATUS_APPROVED)
    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)
    assert row['changes_pending_count'] == 1


def test_project_list_includes_next_deliverable(authed, client_user):
    p = Project.objects.create(name='P1', client=client_user)
    future = timezone.now().date() + timedelta(days=10)
    further = timezone.now().date() + timedelta(days=30)
    Deliverable.objects.create(project=p, name='Soon', due_date=future)
    Deliverable.objects.create(project=p, name='Later', due_date=further)
    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)
    assert row['next_deliverable']['name'] == 'Soon'


def test_project_list_includes_last_activity_at(authed, client_user):
    p = Project.objects.create(name='P1', client=client_user)
    p.updated_at = timezone.now() - timedelta(hours=2)
    p.save(update_fields=['updated_at'])
    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)
    assert row['last_activity_at'] is not None


def test_project_list_zero_counts_when_no_data(authed, client_user):
    p = Project.objects.create(name='P1', client=client_user)
    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)
    assert row['bugs_open_count'] == 0
    assert row['changes_pending_count'] == 0
    assert row['next_deliverable'] is None
```

- [ ] **Step 2: Run — expect failure (fields not in response yet)**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_project_list_aggregates.py -v 2>&1 | tail -5
```

- [ ] **Step 3: Augment `ProjectListSerializer` in `backend/accounts/serializers.py`**

Inside the class, add methods + register fields:

```python
class ProjectListSerializer(serializers.ModelSerializer):
    # ... existing fields ...

    bugs_open_count = serializers.SerializerMethodField()
    changes_pending_count = serializers.SerializerMethodField()
    next_deliverable = serializers.SerializerMethodField()
    last_activity_at = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status', 'progress',
            'start_date', 'estimated_end_date',
            'client_id', 'client_name', 'client_email', 'client_company',
            'proposal_id', 'proposal_title',
            'hosting_start_date',
            'bugs_open_count', 'changes_pending_count', 'next_deliverable',
            'last_activity_at',
            'created_at', 'updated_at',
        ]

    # ... existing methods ...

    def get_bugs_open_count(self, obj):
        from accounts.models import BugReport
        open_statuses = [
            BugReport.STATUS_REPORTED, BugReport.STATUS_CONFIRMED,
            BugReport.STATUS_FIXING, BugReport.STATUS_QA,
        ]
        return BugReport.objects.filter(
            deliverable__project=obj, status__in=open_statuses,
        ).count()

    def get_changes_pending_count(self, obj):
        from accounts.models import ChangeRequest
        return ChangeRequest.objects.filter(
            project=obj, status=ChangeRequest.STATUS_PENDING,
        ).count()

    def get_next_deliverable(self, obj):
        from django.utils import timezone
        from accounts.models import Deliverable
        nxt = Deliverable.objects.filter(
            project=obj, due_date__gte=timezone.now().date(),
        ).order_by('due_date').first()
        if nxt is None:
            return None
        return {'id': nxt.id, 'name': nxt.name, 'due_date': nxt.due_date}

    def get_last_activity_at(self, obj):
        # MVP: use project's updated_at. A future improvement aggregates across
        # bugs/changes/deliverables/payments; the field name is stable so we
        # can swap the implementation later without changing the contract.
        return obj.updated_at
```

- [ ] **Step 4: Run tests — expect pass**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_project_list_aggregates.py -v 2>&1 | tail -8
```

Expected: 5 passed.

- [ ] **Step 5: Regression — existing project tests still green**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_views_projects.py -v 2>&1 | tail -8
```

If that test file doesn't exist or has a different name, run a search:

```
cd backend && source venv/bin/activate && pytest accounts/tests/ -v -k 'project' 2>&1 | tail -10
```

Expected: all green; if anything fails because it expected the old serializer keys, update the assertion to accept the new keys without removing them.

- [ ] **Step 6: Commit**

```
git add backend/accounts/serializers.py backend/accounts/tests/test_project_list_aggregates.py
git commit -m "FEAT: projects list returns bugs/changes/next-deliverable/last-activity aggregates"
```

---

## Task 6 — Aggregated fields on `GET /clients/`

**Files:**
- Modify: `backend/accounts/serializers.py`
- Create: `backend/accounts/tests/test_client_list_aggregates.py`

- [ ] **Step 1: Write failing tests**

`backend/accounts/tests/test_client_list_aggregates.py`:

```python
"""Tests for the aggregated fields on GET /api/accounts/clients/."""
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import HostingSubscription, Project, UserProfile
from accounts.services.tokens import get_tokens_for_user

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_user(db):
    u = User.objects.create_user(username='a@e.co', email='a@e.co', password='x')
    UserProfile.objects.create(user=u, role='admin', is_onboarded=True, profile_completed=True)
    return u


@pytest.fixture
def authed(admin_user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {get_tokens_for_user(admin_user)["access"]}')
    return c


def _make_client(email='c@e.co'):
    u = User.objects.create_user(username=email, email=email, password='x')
    UserProfile.objects.create(user=u, role='client', is_onboarded=True, profile_completed=True)
    return u


def test_client_list_includes_hosting_summary(authed):
    client = _make_client()
    project = Project.objects.create(name='P', client=client)
    HostingSubscription.objects.create(
        project=project, plan=HostingSubscription.PLAN_QUARTERLY,
        next_renewal_at=date.today() + timedelta(days=20),
        renewal_amount=300, is_active=True,
    )
    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)
    assert row['hosting_plan'] == 'quarterly'
    assert row['hosting_renewal_value'] == '300.00'  # serialized as string by DRF default
    assert row['hosting_renewal_at']


def test_client_list_no_subscription_returns_nulls(authed):
    client = _make_client('no_sub@e.co')
    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)
    assert row['hosting_plan'] is None
    assert row['hosting_renewal_at'] is None


def test_client_list_project_counts(authed):
    client = _make_client('two_projects@e.co')
    Project.objects.create(name='Active', client=client, status=Project.STATUS_ACTIVE)
    Project.objects.create(name='Paused', client=client, status=Project.STATUS_PAUSED)
    Project.objects.create(name='Archived', client=client, status=Project.STATUS_ARCHIVED)
    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)
    assert row['active_projects_count'] == 1
    assert row['total_projects_count'] == 2  # archived excluded


def test_client_list_has_logged_in_once(authed):
    fresh = _make_client('never@e.co')
    visited = _make_client('visited@e.co')
    visited.last_login = timezone.now()
    visited.save(update_fields=['last_login'])
    resp = authed.get('/api/accounts/clients/')
    by_id = {r['user_id']: r for r in resp.json()}
    assert by_id[fresh.id]['has_logged_in_once'] is False
    assert by_id[visited.id]['has_logged_in_once'] is True


def test_client_list_last_activity_at(authed):
    client = _make_client('act@e.co')
    p = Project.objects.create(name='P', client=client)
    p.updated_at = timezone.now() - timedelta(days=3)
    p.save(update_fields=['updated_at'])
    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)
    assert row['last_activity_at'] is not None
```

- [ ] **Step 2: Run — expect failure**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_client_list_aggregates.py -v 2>&1 | tail -5
```

- [ ] **Step 3: Augment `ClientListSerializer` in `backend/accounts/serializers.py`**

```python
class ClientListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    user_id = serializers.IntegerField(source='user.id')
    is_active = serializers.BooleanField(source='user.is_active')
    avatar_display_url = serializers.SerializerMethodField()

    # New aggregated fields
    hosting_plan = serializers.SerializerMethodField()
    hosting_renewal_at = serializers.SerializerMethodField()
    hosting_renewal_value = serializers.SerializerMethodField()
    active_projects_count = serializers.SerializerMethodField()
    total_projects_count = serializers.SerializerMethodField()
    last_activity_at = serializers.SerializerMethodField()
    has_logged_in_once = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'email', 'first_name', 'last_name',
            'company_name', 'phone', 'is_onboarded', 'is_active',
            'profile_completed', 'avatar_display_url', 'created_at',
            'hosting_plan', 'hosting_renewal_at', 'hosting_renewal_value',
            'active_projects_count', 'total_projects_count',
            'last_activity_at', 'has_logged_in_once',
        ]

    # ... existing get_avatar_display_url ...

    def _active_subscription(self, obj):
        # Pick the active subscription across any of the user's projects.
        # Most clients have a single hosting subscription; if multiple, take
        # the one closest to renewing.
        from accounts.models import HostingSubscription
        return (
            HostingSubscription.objects
            .filter(project__client=obj.user, is_active=True)
            .order_by('next_renewal_at')
            .first()
        )

    def get_hosting_plan(self, obj):
        sub = self._active_subscription(obj)
        return sub.plan if sub else None

    def get_hosting_renewal_at(self, obj):
        sub = self._active_subscription(obj)
        return sub.next_renewal_at if sub else None

    def get_hosting_renewal_value(self, obj):
        sub = self._active_subscription(obj)
        return sub.renewal_amount if sub else None

    def get_active_projects_count(self, obj):
        from accounts.models import Project
        return Project.objects.filter(
            client=obj.user, status=Project.STATUS_ACTIVE,
        ).count()

    def get_total_projects_count(self, obj):
        from accounts.models import Project
        return Project.objects.filter(client=obj.user).exclude(
            status=Project.STATUS_ARCHIVED,
        ).count()

    def get_last_activity_at(self, obj):
        from django.db.models import Max
        from accounts.models import Project
        latest = Project.objects.filter(client=obj.user).aggregate(
            m=Max('updated_at'),
        )['m']
        login = obj.user.last_login
        if latest and login:
            return max(latest, login)
        return latest or login

    def get_has_logged_in_once(self, obj):
        return obj.user.last_login is not None
```

- [ ] **Step 4: Verify HostingSubscription field names**

```
cd backend && source venv/bin/activate && python -c "
import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','projectapp.settings')
import django; django.setup()
from accounts.models import HostingSubscription
print([f.name for f in HostingSubscription._meta.get_fields()])
"
```

If `renewal_amount` or `next_renewal_at` is named differently in the model, update the serializer field names in Step 3 to match. (The model exists per the spec §9; if names differ, the implementer adjusts.)

- [ ] **Step 5: Run tests — expect pass**

```
cd backend && source venv/bin/activate && pytest accounts/tests/test_client_list_aggregates.py -v 2>&1 | tail -8
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```
git add backend/accounts/serializers.py backend/accounts/tests/test_client_list_aggregates.py
git commit -m "FEAT: clients list returns hosting/projects/activity aggregates"
```

---

# PHASE B — Frontend tables and project shell

Goal of this phase: the new UI is in place but the sidebar is unchanged. New tables and the project shell coexist with the old global pages.

## Task 7 — Projects table component

**Files:**
- Create: `frontend/components/platform/projects/ProjectsTable.vue`
- Modify: `frontend/pages/platform/projects/index.vue`
- Create: `frontend/test/components/platform/projects/ProjectsTable.test.js`

- [ ] **Step 1: Write failing component test**

`frontend/test/components/platform/projects/ProjectsTable.test.js`:

```js
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import ProjectsTable from '../../../../components/platform/projects/ProjectsTable.vue'

describe('ProjectsTable', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  const rows = [
    {
      id: 1, name: 'Project A', status: 'active', progress: 40,
      client_name: 'Ada Lovelace', client_email: 'ada@e.co', client_id: 9,
      bugs_open_count: 3, changes_pending_count: 1,
      next_deliverable: { id: 7, name: 'Wireframes', due_date: '2026-06-01' },
      last_activity_at: '2026-05-15T10:00:00Z',
    },
  ]

  it('renders one row per project with the expected columns', () => {
    const w = mount(ProjectsTable, { props: { projects: rows, role: 'admin' } })
    expect(w.text()).toContain('Project A')
    expect(w.text()).toContain('Ada Lovelace')
    expect(w.text()).toContain('40')
    expect(w.text()).toContain('3') // bugs_open_count
    expect(w.text()).toContain('Wireframes')
  })

  it('emits navigate event on row click with the project id', async () => {
    const w = mount(ProjectsTable, { props: { projects: rows, role: 'admin' } })
    await w.find('[data-testid="project-row-1"]').trigger('click')
    expect(w.emitted('navigate')[0]).toEqual([1])
  })

  it('hides admin-only columns when role is client', () => {
    const w = mount(ProjectsTable, { props: { projects: rows, role: 'client' } })
    expect(w.text()).not.toContain('Ada Lovelace')
    expect(w.text()).not.toContain('1')  // changes_pending_count hidden for client
  })
})
```

- [ ] **Step 2: Run — expect module not found**

```
npm --prefix frontend test -- test/components/platform/projects/ProjectsTable.test.js 2>&1 | tail -5
```

- [ ] **Step 3: Implement the component**

`frontend/components/platform/projects/ProjectsTable.vue`:

```vue
<template>
  <div class="overflow-hidden rounded-2xl border border-border-default bg-surface">
    <table class="min-w-full text-left text-sm">
      <thead class="bg-surface-muted/40 text-xs font-medium uppercase tracking-wider text-green-light/70">
        <tr>
          <th class="px-4 py-3">Proyecto</th>
          <th v-if="isAdmin" class="px-4 py-3">Cliente</th>
          <th class="px-4 py-3">Progreso</th>
          <th class="px-4 py-3">Bugs abiertos</th>
          <th v-if="isAdmin" class="px-4 py-3">Solicitudes pendientes</th>
          <th class="px-4 py-3">Próximo entregable</th>
          <th class="px-4 py-3">Última actividad</th>
          <th class="w-10 px-2"></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="p in projects"
          :key="p.id"
          :data-testid="`project-row-${p.id}`"
          class="cursor-pointer border-t border-border-muted transition hover:bg-primary-soft/30"
          @click="$emit('navigate', p.id)"
        >
          <td class="px-4 py-3">
            <div class="font-medium text-text-default">{{ p.name }}</div>
            <span :class="statusChipClass(p.status)">{{ statusLabel(p.status) }}</span>
          </td>
          <td v-if="isAdmin" class="px-4 py-3 text-green-light">
            {{ p.client_name }}<br>
            <span class="text-xs text-green-light/60">{{ p.client_email }}</span>
          </td>
          <td class="px-4 py-3">
            <div class="flex items-center gap-2">
              <div class="h-1.5 w-20 overflow-hidden rounded-full bg-surface-muted">
                <div class="h-full bg-primary" :style="{ width: `${p.progress}%` }"></div>
              </div>
              <span class="text-xs">{{ p.progress }}%</span>
            </div>
          </td>
          <td class="px-4 py-3">
            <span :class="p.bugs_open_count > 0 ? 'rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700' : 'text-green-light/60'">
              {{ p.bugs_open_count }}
            </span>
          </td>
          <td v-if="isAdmin" class="px-4 py-3">
            <span :class="p.changes_pending_count > 0 ? 'rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700' : 'text-green-light/60'">
              {{ p.changes_pending_count }}
            </span>
          </td>
          <td class="px-4 py-3 text-sm">
            <template v-if="p.next_deliverable">
              {{ p.next_deliverable.name }}<br>
              <span class="text-xs text-green-light/60">{{ formatDate(p.next_deliverable.due_date) }}</span>
            </template>
            <span v-else class="text-green-light/60">—</span>
          </td>
          <td class="px-4 py-3 text-sm text-green-light/70">{{ relativeTime(p.last_activity_at) }}</td>
          <td class="px-2 py-3 text-right text-green-light/40">
            ›
          </td>
        </tr>
        <tr v-if="!projects.length">
          <td :colspan="isAdmin ? 8 : 6" class="px-4 py-12 text-center text-green-light/60">
            No hay proyectos para mostrar.
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  projects: { type: Array, required: true },
  role: { type: String, default: 'admin' },
})

defineEmits(['navigate'])

const isAdmin = computed(() => props.role === 'admin')

const STATUS_LABELS = {
  active: 'Activo', paused: 'Pausado',
  completed: 'Completado', archived: 'Archivado',
}
function statusLabel(s) { return STATUS_LABELS[s] || s }
function statusChipClass(s) {
  const base = 'mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium'
  const map = {
    active: 'bg-green-100 text-green-700',
    paused: 'bg-amber-100 text-amber-700',
    completed: 'bg-sky-100 text-sky-700',
    archived: 'bg-slate-100 text-slate-600',
  }
  return `${base} ${map[s] || map.archived}`
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })
}

function relativeTime(iso) {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days < 1) return 'Hoy'
  if (days === 1) return 'Ayer'
  if (days < 30) return `Hace ${days} días`
  if (days < 365) return `Hace ${Math.floor(days / 30)} meses`
  return `Hace ${Math.floor(days / 365)} años`
}
</script>
```

- [ ] **Step 4: Run tests — expect pass**

```
npm --prefix frontend test -- test/components/platform/projects/ProjectsTable.test.js 2>&1 | tail -8
```

Expected: 3 passed.

- [ ] **Step 5: Use the component in `frontend/pages/platform/projects/index.vue`**

Find the existing `<!-- Project cards grid -->` block (the `div.grid` with `v-for project in projectsStore.projects`) and replace it with:

```vue
<ProjectsTable
  :projects="projectsStore.projects"
  :role="authStore.isAdmin ? 'admin' : 'client'"
  @navigate="goToProject"
/>
```

Add at the top of `<script setup>`:

```js
import ProjectsTable from '~/components/platform/projects/ProjectsTable.vue'

function goToProject(id) {
  navigateTo(localePath(`/platform/projects/${id}`))
}
```

If `localePath` and `authStore` aren't already in scope, import/instantiate them (they are in the surrounding file already; verify before editing).

- [ ] **Step 6: Manual smoke test**

```
cd backend && source venv/bin/activate && python manage.py runserver 0.0.0.0:8000 &
npm --prefix frontend run dev &
```

Open `http://localhost:3000/es-co/platform/projects` (logged in as admin). Expected: see the table with the new columns. Click a row → navigates to detail.

- [ ] **Step 7: Commit**

```
git add frontend/components/platform/projects/ProjectsTable.vue frontend/pages/platform/projects/index.vue frontend/test/components/platform/projects/ProjectsTable.test.js
git commit -m "FEAT: Projects table with chevron drill-down (replaces card grid)"
```

---

## Task 8 — Clients table column refresh

**Files:**
- Modify: `frontend/pages/platform/clients/index.vue`

- [ ] **Step 1: Locate the existing `<table>` in `clients/index.vue`**

The current file already has a `<table>` with `tbody`. Identify the column headers and the row template; we'll replace them.

- [ ] **Step 2: Replace the columns**

Update the `<thead>`:

```html
<thead class="bg-surface-muted/40 text-xs font-medium uppercase tracking-wider text-green-light/70">
  <tr>
    <th class="px-4 py-3">Cliente</th>
    <th class="px-4 py-3">Empresa</th>
    <th class="px-4 py-3">Proyectos</th>
    <th class="px-4 py-3">Plan hosting</th>
    <th class="px-4 py-3">Próx. renovación</th>
    <th class="px-4 py-3">Valor renovación</th>
    <th class="px-4 py-3">Última actividad</th>
    <th class="w-10 px-2"></th>
  </tr>
</thead>
```

Update the row template:

```html
<tr
  v-for="client in filteredClients"
  :key="client.user_id"
  class="cursor-pointer border-b border-border-muted transition hover:bg-primary-soft/30 last:border-b-0"
  @click="goToClient(client.user_id)"
>
  <td class="px-4 py-3">
    <div class="flex items-center gap-2">
      <span class="font-medium text-text-default">{{ client.first_name }} {{ client.last_name }}</span>
      <span v-if="!client.is_active" class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">Inactivo</span>
    </div>
    <div class="flex items-center gap-1 text-xs text-green-light/60">
      {{ client.email }}
      <svg v-if="!client.has_logged_in_once" class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" :title="'Sin acceso aún'">
        <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />
      </svg>
    </div>
  </td>
  <td class="px-4 py-3">{{ client.company_name || '—' }}</td>
  <td class="px-4 py-3">{{ client.active_projects_count }} / {{ client.total_projects_count }}</td>
  <td class="px-4 py-3">
    <span v-if="client.hosting_plan" class="rounded-full bg-primary-soft px-2 py-0.5 text-xs font-medium text-text-brand">
      {{ planLabel(client.hosting_plan) }}
    </span>
    <span v-else class="text-green-light/60">—</span>
  </td>
  <td class="px-4 py-3" :class="renewalClass(client.hosting_renewal_at)">
    {{ formatDate(client.hosting_renewal_at) || '—' }}
  </td>
  <td class="px-4 py-3">{{ formatMoney(client.hosting_renewal_value) }}</td>
  <td class="px-4 py-3 text-sm text-green-light/70">{{ relativeTime(client.last_activity_at) }}</td>
  <td class="px-2 py-3 text-right text-green-light/40">›</td>
</tr>
```

- [ ] **Step 3: Add the helpers + handler to the script section**

```js
const PLAN_LABELS = {
  monthly: 'Mensual', quarterly: 'Trimestral', semiannual: 'Semestral',
}
function planLabel(p) { return PLAN_LABELS[p] || p }

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
function formatMoney(v) {
  if (v === null || v === undefined) return '—'
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}
function relativeTime(iso) {
  if (!iso) return '—'
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / (1000 * 60 * 60 * 24))
  if (days < 1) return 'Hoy'
  if (days === 1) return 'Ayer'
  if (days < 30) return `Hace ${days} días`
  if (days < 365) return `Hace ${Math.floor(days / 30)} meses`
  return `Hace ${Math.floor(days / 365)} años`
}
function renewalClass(iso) {
  if (!iso) return ''
  const days = Math.floor((new Date(iso).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  return days <= 30 ? 'text-amber-700 font-medium' : ''
}

function goToClient(id) {
  navigateTo(localePath(`/platform/clients/${id}`))
}
```

Update the status filter chip set to only **Activos / Inactivos / Todos** (remove "Pendientes onboarding" if present).

- [ ] **Step 4: Smoke test in the browser**

`http://localhost:3000/es-co/platform/clients` — verify columns render with backend data. If the backend hasn't propagated `has_logged_in_once`, the icon won't appear (fine).

- [ ] **Step 5: Commit**

```
git add frontend/pages/platform/clients/index.vue
git commit -m "FEAT: Clients table — hosting plan/renewal columns + Activo/Inactivo states"
```

---

## Task 9 — Project shell (header + secondary sidebar + breadcrumb)

**Files:**
- Create: `frontend/components/platform/projects/ProjectShell.vue`
- Create: `frontend/components/platform/projects/ProjectSecondarySidebar.vue`
- Create: `frontend/components/platform/projects/ProjectBreadcrumb.vue`

- [ ] **Step 1: Create the breadcrumb component**

`frontend/components/platform/projects/ProjectBreadcrumb.vue`:

```vue
<template>
  <nav class="flex items-center gap-2 text-sm text-green-light">
    <NuxtLink :to="localePath('/platform/projects')" class="hover:text-text-brand">Proyectos</NuxtLink>
    <span class="text-green-light/40">/</span>
    <span class="text-text-default">{{ projectName || '…' }}</span>
  </nav>
</template>

<script setup>
defineProps({ projectName: { type: String, default: '' } })
const localePath = useLocalePath()
</script>
```

- [ ] **Step 2: Create the secondary sidebar**

`frontend/components/platform/projects/ProjectSecondarySidebar.vue`:

```vue
<template>
  <aside class="w-56 shrink-0 border-r border-border-muted bg-surface px-3 py-4">
    <NuxtLink
      v-for="item in items"
      :key="item.href"
      :to="item.href"
      :class="[
        'flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition',
        isActive(item.href)
          ? 'bg-primary-soft text-text-brand'
          : 'text-green-light hover:bg-primary-soft/50 hover:text-text-brand',
      ]"
    >
      {{ item.label }}
    </NuxtLink>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  projectId: { type: [String, Number], required: true },
})

const localePath = useLocalePath()
const route = useRoute()

const items = computed(() => {
  const base = `/platform/projects/${props.projectId}`
  return [
    { label: 'Resumen',           href: localePath(base) },
    { label: 'Tablero',           href: localePath(`${base}/board`) },
    { label: 'Solicitudes',       href: localePath(`${base}/changes`) },
    { label: 'Bugs',              href: localePath(`${base}/bugs`) },
    { label: 'Entregables',       href: localePath(`${base}/deliverables`) },
    { label: 'Pagos',             href: localePath(`${base}/payments`) },
    { label: 'Cuentas de cobro',  href: localePath(`${base}/collection-accounts`) },
    { label: 'Modelo de datos',   href: localePath(`${base}/data-model`) },
    { label: 'Accesos',           href: localePath(`${base}/access`) },
  ]
})

function isActive(href) {
  const stripped = (p) => p.replace(/^\/[a-z]{2}-[a-z]{2}/, '')
  return stripped(route.path) === stripped(href)
}
</script>
```

- [ ] **Step 3: Create the shell**

`frontend/components/platform/projects/ProjectShell.vue`:

```vue
<template>
  <div>
    <header class="border-b border-border-muted bg-surface px-6 py-4">
      <ProjectBreadcrumb :project-name="project?.name" />
      <div class="mt-2 flex items-center gap-3">
        <h1 class="text-xl font-semibold text-text-default">{{ project?.name || 'Proyecto' }}</h1>
        <span v-if="project" :class="statusChipClass(project.status)">{{ statusLabel(project.status) }}</span>
      </div>
      <p v-if="project" class="mt-1 text-sm text-green-light">
        Cliente: {{ project.client_name }}
        <template v-if="project.start_date"> · Inició: {{ formatDate(project.start_date) }}</template>
        <template v-if="project.next_deliverable"> · Próx. entrega: {{ formatDate(project.next_deliverable.due_date) }}</template>
      </p>
    </header>
    <div class="flex">
      <ProjectSecondarySidebar :project-id="projectId" />
      <main class="flex-1 px-6 py-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import ProjectBreadcrumb from '~/components/platform/projects/ProjectBreadcrumb.vue'
import ProjectSecondarySidebar from '~/components/platform/projects/ProjectSecondarySidebar.vue'

const route = useRoute()
const store = usePlatformProjectsStore()

const projectId = computed(() => Number(route.params.id))
const project = computed(() => store.currentProject)

onMounted(() => { if (projectId.value) store.fetchProject(projectId.value) })
watch(projectId, (id) => { if (id) store.fetchProject(id) })

const STATUS_LABELS = { active: 'Activo', paused: 'Pausado', completed: 'Completado', archived: 'Archivado' }
function statusLabel(s) { return STATUS_LABELS[s] || s }
function statusChipClass(s) {
  const base = 'rounded-full px-2 py-0.5 text-xs font-medium'
  const map = {
    active: 'bg-green-100 text-green-700', paused: 'bg-amber-100 text-amber-700',
    completed: 'bg-sky-100 text-sky-700', archived: 'bg-slate-100 text-slate-600',
  }
  return `${base} ${map[s] || map.archived}`
}
function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>
```

Note: assumes `usePlatformProjectsStore` has a `fetchProject(id)` action and `currentProject` state. If not, this requires either (a) the store has them already, or (b) adding them in this task. Verify by reading the existing store before committing.

- [ ] **Step 4: Smoke test**

Open any `/platform/projects/:id` sub-route in the browser. The shell isn't wired yet, so this is just a visual check by importing `ProjectShell` ad-hoc in one page. Skip if there's nothing to check standalone.

- [ ] **Step 5: Commit**

```
git add frontend/components/platform/projects/ProjectShell.vue frontend/components/platform/projects/ProjectSecondarySidebar.vue frontend/components/platform/projects/ProjectBreadcrumb.vue
git commit -m "FEAT: ProjectShell with breadcrumb + secondary sidebar"
```

---

## Task 10 — Wrap project sub-routes with `ProjectShell`

**Files:**
- Modify: `frontend/pages/platform/projects/[id]/index.vue`
- Modify: `frontend/pages/platform/projects/[id]/board.vue`
- Modify: `frontend/pages/platform/projects/[id]/bugs.vue`
- Modify: `frontend/pages/platform/projects/[id]/changes.vue`
- Modify: `frontend/pages/platform/projects/[id]/payments.vue`
- Modify: `frontend/pages/platform/projects/[id]/collection-accounts.vue`
- Modify: `frontend/pages/platform/projects/[id]/data-model.vue`
- Modify: `frontend/pages/platform/projects/[id]/deliverables/index.vue`
- Modify: `frontend/pages/platform/projects/[id]/deliverables/[deliverableId]/index.vue`

For each file, the pattern is the same: wrap the existing `<template>` content in `<ProjectShell>` and import the component.

- [ ] **Step 1: Update each sub-route file**

In each file's `<template>`:

Before:
```vue
<template>
  <div class="...">
    <!-- existing content -->
  </div>
</template>
```

After:
```vue
<template>
  <ProjectShell>
    <div class="...">
      <!-- existing content -->
    </div>
  </ProjectShell>
</template>
```

In the `<script setup>` add:

```js
import ProjectShell from '~/components/platform/projects/ProjectShell.vue'
```

- [ ] **Step 2: Smoke test each sub-route**

Click through `/platform/projects/<id>/board`, `/bugs`, `/changes`, etc. Verify the shell header + secondary sidebar appear and the sub-content renders below.

- [ ] **Step 3: Commit**

```
git add frontend/pages/platform/projects/[id]/
git commit -m "REFACTOR: wrap project sub-routes with ProjectShell layout"
```

---

## Task 11 — Resumen page (KPIs + sections placeholder for Phases)

**Files:**
- Modify: `frontend/pages/platform/projects/[id]/index.vue`

This task refactors the project's root route to be the Resumen overview. The Phases section is rendered with a placeholder; the actual `PhaseList` component lands in Task 12.

- [ ] **Step 1: Rewrite `index.vue`**

`frontend/pages/platform/projects/[id]/index.vue`:

```vue
<template>
  <ProjectShell>
    <section v-if="project" class="space-y-8">
      <!-- KPIs -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Progreso</p>
          <p class="mt-2 text-2xl font-semibold text-text-default">{{ project.progress }}%</p>
        </div>
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Bugs abiertos</p>
          <p class="mt-2 text-2xl font-semibold" :class="project.bugs_open_count > 0 ? 'text-red-600' : 'text-text-default'">
            {{ project.bugs_open_count ?? 0 }}
          </p>
        </div>
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Solicitudes pendientes</p>
          <p class="mt-2 text-2xl font-semibold" :class="project.changes_pending_count > 0 ? 'text-amber-600' : 'text-text-default'">
            {{ project.changes_pending_count ?? 0 }}
          </p>
        </div>
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Próximo entregable</p>
          <p class="mt-2 text-sm text-text-default">{{ project.next_deliverable?.name || '—' }}</p>
          <p v-if="project.next_deliverable" class="text-xs text-green-light/60">{{ formatDate(project.next_deliverable.due_date) }}</p>
        </div>
      </div>

      <!-- Phases placeholder (PhaseList lands in Task 12) -->
      <div class="rounded-2xl border border-border-default bg-surface p-6">
        <h2 class="text-base font-medium text-text-default">Fases del proyecto</h2>
        <p class="mt-2 text-sm text-green-light">El componente de fases se renderiza aquí.</p>
      </div>

      <!-- Actions -->
      <div v-if="authStore.isAdmin" class="rounded-2xl border border-border-default bg-surface p-6">
        <h2 class="text-base font-medium text-text-default">Acciones</h2>
        <div class="mt-3 flex gap-2">
          <button class="rounded-xl border border-border-default px-3 py-2 text-sm" @click="onEdit">Editar</button>
          <button class="rounded-xl border border-border-default px-3 py-2 text-sm" @click="onArchive">Archivar</button>
          <button class="rounded-xl border border-red-500/30 px-3 py-2 text-sm text-red-600" @click="onDelete">Eliminar</button>
        </div>
      </div>
    </section>
    <div v-else class="px-6 py-12 text-center text-green-light/60">Cargando proyecto…</div>
  </ProjectShell>
</template>

<script setup>
import { computed } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import ProjectShell from '~/components/platform/projects/ProjectShell.vue'

definePageMeta({ middleware: ['platform-auth'] })

const authStore = usePlatformAuthStore()
const store = usePlatformProjectsStore()
const project = computed(() => store.currentProject)

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

function onEdit() { /* Modal hookup in a follow-up; out of scope for IA spec */ }
function onArchive() { /* Out of scope */ }
function onDelete() { /* Out of scope */ }
</script>
```

The edit/archive/delete handlers are stubbed for now. The spec keeps these "concentrated here" but the actual modals are out of scope for this IA round.

- [ ] **Step 2: Smoke test**

Open `/platform/projects/<id>` in the browser. Expected: KPIs render with real values; the Phases section shows a placeholder; the action buttons are visible but non-functional.

- [ ] **Step 3: Commit**

```
git add frontend/pages/platform/projects/[id]/index.vue
git commit -m "REFACTOR: project Resumen page with KPIs and action stubs"
```

---

## Task 12 — `PhaseList` component (drag-and-drop, render in Resumen)

**Files:**
- Create: `frontend/components/platform/projects/PhaseList.vue`
- Modify: `frontend/stores/platform-projects.js` (add phase actions)
- Modify: `frontend/pages/platform/projects/[id]/index.vue` (use the component)
- Create: `frontend/test/components/platform/projects/PhaseList.test.js`

- [ ] **Step 1: Write failing component test**

`frontend/test/components/platform/projects/PhaseList.test.js`:

```js
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import PhaseList from '../../../../components/platform/projects/PhaseList.vue'
import { usePlatformProjectsStore } from '../../../../stores/platform-projects'

jest.mock('vuedraggable', () => ({
  __esModule: true,
  default: {
    name: 'draggable',
    props: ['modelValue'],
    emits: ['update:modelValue', 'end'],
    template: '<div><slot v-for="el in modelValue" :element="el" /></div>',
  },
}))

describe('PhaseList', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  it('renders one entry per phase with the proposal title', () => {
    const w = mount(PhaseList, {
      props: {
        projectId: 1,
        phases: [
          { id: 10, order: 1, proposal: { id: 100, title: 'Discovery' } },
          { id: 11, order: 2, proposal: { id: 101, title: 'Build' } },
        ],
      },
    })
    expect(w.text()).toContain('1. Discovery')
    expect(w.text()).toContain('2. Build')
  })

  it('calls store.removePhase when × is clicked', async () => {
    const store = usePlatformProjectsStore()
    store.removePhase = jest.fn().mockResolvedValue({ success: true })
    global.confirm = () => true
    const w = mount(PhaseList, {
      props: {
        projectId: 5,
        phases: [{ id: 10, order: 1, proposal: { id: 100, title: 'X' } }],
      },
    })
    await w.find('[data-testid="remove-phase-10"]').trigger('click')
    await flushPromises()
    expect(store.removePhase).toHaveBeenCalledWith(5, 10)
  })
})
```

- [ ] **Step 2: Run — expect failure**

```
npm --prefix frontend test -- test/components/platform/projects/PhaseList.test.js 2>&1 | tail -5
```

- [ ] **Step 3: Add phase actions to the store**

In `frontend/stores/platform-projects.js`, append to `actions`:

```js
async loadPhases(projectId) {
  const { get } = usePlatformApi()
  const r = await get(`projects/${projectId}/phases/`)
  return r.data
},

async addPhase(projectId, proposalId, order = null) {
  const { post } = usePlatformApi()
  const body = { proposal_id: proposalId }
  if (order !== null) body.order = order
  const r = await post(`projects/${projectId}/phases/`, body)
  return { success: true, phase: r.data }
},

async removePhase(projectId, phaseId) {
  const { delete: del } = usePlatformApi()
  await del(`projects/${projectId}/phases/${phaseId}/`)
  return { success: true }
},

async reorderPhases(projectId, items) {
  const { patch } = usePlatformApi()
  const r = await patch(`projects/${projectId}/phases/reorder/`, items)
  return { success: true, phases: r.data }
},

async loadEligibleProposals(clientId) {
  const { get } = usePlatformApi()
  const r = await get(`clients/${clientId}/eligible-proposals/`)
  return r.data
},
```

If the store doesn't import `usePlatformApi` yet, add the import:

```js
import { usePlatformApi } from '~/composables/usePlatformApi'
```

- [ ] **Step 4: Implement the component**

`frontend/components/platform/projects/PhaseList.vue`:

```vue
<template>
  <div class="rounded-2xl border border-border-default bg-surface p-6">
    <h2 class="text-base font-medium text-text-default">Fases del proyecto</h2>
    <p v-if="phases.length === 0" class="mt-4 text-sm text-green-light/60">
      Este proyecto no tiene fases vinculadas todavía.
    </p>
    <draggable
      v-else
      :model-value="phases"
      handle=".drag-handle"
      item-key="id"
      class="mt-4 space-y-2"
      @end="onReorderEnd"
    >
      <template #item="{ element }">
        <div class="flex items-center gap-3 rounded-xl border border-border-muted bg-surface-muted/30 px-4 py-3">
          <span class="drag-handle cursor-grab text-green-light/40" aria-label="Arrastrar">⠿</span>
          <span class="font-medium text-text-default">{{ element.order }}. {{ element.proposal.title }}</span>
          <span class="ml-auto text-sm text-green-light/60">${{ element.proposal.total_amount }}</span>
          <button
            class="rounded-lg border border-border-default px-2 py-1 text-xs"
            @click="onEditProposal(element.proposal.id)"
          >Editar</button>
          <button
            :data-testid="`remove-phase-${element.id}`"
            class="rounded-lg border border-red-500/30 px-2 py-1 text-xs text-red-600"
            @click="onRemove(element.id)"
          >×</button>
        </div>
      </template>
    </draggable>
    <button
      class="mt-4 rounded-xl border border-dashed border-border-default px-3 py-2 text-sm text-text-default"
      @click="$emit('add-phase')"
    >+ Agregar fase desde propuesta del cliente</button>
  </div>
</template>

<script setup>
import draggable from 'vuedraggable'
import { usePlatformProjectsStore } from '~/stores/platform-projects'

const props = defineProps({
  projectId: { type: [String, Number], required: true },
  phases: { type: Array, required: true },
})
const emit = defineEmits(['add-phase', 'changed'])

const store = usePlatformProjectsStore()

async function onReorderEnd(evt) {
  // After drag completes, evt.from contains the new DOM order.
  // We rebuild the items array from the current `phases` order.
  const items = props.phases.map((p, idx) => ({ id: p.id, order: idx + 1 }))
  const r = await store.reorderPhases(props.projectId, items)
  if (r.success) emit('changed')
}

async function onRemove(phaseId) {
  if (!window.confirm('¿Quitar esta fase del proyecto?')) return
  const r = await store.removePhase(props.projectId, phaseId)
  if (r.success) emit('changed')
}

function onEditProposal(proposalId) {
  // Open the panel proposal editor in a new tab (per spec §7.4).
  window.open(`/panel/proposals/${proposalId}/edit`, '_blank')
}
</script>
```

- [ ] **Step 5: Run tests — expect pass**

```
npm --prefix frontend test -- test/components/platform/projects/PhaseList.test.js 2>&1 | tail -8
```

Expected: 2 passed.

- [ ] **Step 6: Replace the placeholder in `index.vue`**

In `frontend/pages/platform/projects/[id]/index.vue`, replace the placeholder block:

```vue
<!-- Phases placeholder (PhaseList lands in Task 12) -->
<div class="rounded-2xl border border-border-default bg-surface p-6">
  <h2 class="text-base font-medium text-text-default">Fases del proyecto</h2>
  <p class="mt-2 text-sm text-green-light">El componente de fases se renderiza aquí.</p>
</div>
```

with:

```vue
<PhaseList
  v-if="project"
  :project-id="project.id"
  :phases="phases"
  @add-phase="onAddPhase"
  @changed="loadPhases"
/>
```

Add to the `<script setup>`:

```js
import { ref, onMounted, watch } from 'vue'
import PhaseList from '~/components/platform/projects/PhaseList.vue'

const phases = ref([])

async function loadPhases() {
  if (!project.value) return
  phases.value = await store.loadPhases(project.value.id)
}

onMounted(loadPhases)
watch(() => project.value?.id, loadPhases)

function onAddPhase() { /* opens PhaseSelectorModal in add-mode — Task 13 */ }
```

- [ ] **Step 7: Commit**

```
git add frontend/components/platform/projects/PhaseList.vue frontend/stores/platform-projects.js frontend/pages/platform/projects/[id]/index.vue frontend/test/components/platform/projects/PhaseList.test.js
git commit -m "FEAT: PhaseList component (drag-and-drop reorder + remove) wired to Resumen"
```

---

## Task 13 — Create-project wizard (`PhaseSelectorModal`)

**Files:**
- Create: `frontend/components/platform/projects/PhaseSelectorModal.vue`
- Create: `frontend/test/components/platform/projects/PhaseSelectorModal.test.js`
- Modify: `frontend/pages/platform/projects/index.vue` (mount the modal, button)
- Modify: `frontend/pages/platform/projects/[id]/index.vue` (mount in "add mode" via `onAddPhase`)

- [ ] **Step 1: Write a focused failing test**

`frontend/test/components/platform/projects/PhaseSelectorModal.test.js`:

```js
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import PhaseSelectorModal from '../../../../components/platform/projects/PhaseSelectorModal.vue'
import { usePlatformProjectsStore } from '../../../../stores/platform-projects'

describe('PhaseSelectorModal (create flow)', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  it('cannot advance from step 1 without selecting a client', async () => {
    const w = mount(PhaseSelectorModal, { props: { mode: 'create' } })
    await w.find('[data-testid="next-step"]').trigger('click')
    expect(w.text()).toContain('Selecciona un cliente')
  })

  it('loads eligible proposals when client picked, allows multi-select', async () => {
    const store = usePlatformProjectsStore()
    store.loadEligibleProposals = jest.fn().mockResolvedValue([
      { id: 100, title: 'A', total_amount: 1000 },
      { id: 101, title: 'B', total_amount: 2000 },
    ])
    const w = mount(PhaseSelectorModal, {
      props: { mode: 'create', clients: [{ user_id: 9, email: 'a@b.co', first_name: 'A', last_name: 'B' }] },
    })
    await w.find('select[data-testid="client-select"]').setValue('9')
    await w.find('[data-testid="next-step"]').trigger('click')
    await flushPromises()
    expect(store.loadEligibleProposals).toHaveBeenCalledWith(9)
    expect(w.text()).toContain('A')
    expect(w.text()).toContain('B')
  })
})
```

- [ ] **Step 2: Run — expect failure**

```
npm --prefix frontend test -- test/components/platform/projects/PhaseSelectorModal.test.js 2>&1 | tail -5
```

- [ ] **Step 3: Implement the modal**

`frontend/components/platform/projects/PhaseSelectorModal.vue`:

```vue
<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
    <div class="w-full max-w-3xl rounded-3xl bg-surface p-6 shadow-2xl">
      <div class="mb-6 flex items-center justify-between">
        <h2 class="text-xl font-medium text-text-default">{{ mode === 'create' ? 'Nuevo proyecto' : 'Agregar fases' }}</h2>
        <button class="text-green-light/60" @click="$emit('close')">×</button>
      </div>

      <!-- Step 1 -->
      <section v-if="step === 1">
        <p class="mb-3 text-sm text-green-light">Selecciona el cliente.</p>
        <select
          data-testid="client-select"
          v-model.number="clientId"
          class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-3 py-2"
        >
          <option :value="0" disabled>Elegir…</option>
          <option v-for="c in clients" :key="c.user_id" :value="c.user_id">
            {{ c.first_name }} {{ c.last_name }} · {{ c.email }}
          </option>
        </select>
        <p v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</p>
      </section>

      <!-- Step 2 -->
      <section v-if="step === 2" class="grid gap-4 sm:grid-cols-2">
        <div>
          <p class="mb-2 text-xs uppercase tracking-wider text-green-light/70">Propuestas elegibles</p>
          <div v-if="eligibleProposals.length === 0" class="rounded-xl border border-border-default p-4 text-sm text-green-light/60">
            No hay propuestas elegibles para este cliente.
          </div>
          <label v-for="p in eligibleProposals" :key="p.id" class="flex items-center gap-2 rounded-xl border border-border-default px-3 py-2">
            <input type="checkbox" :value="p.id" v-model="selectedIds" />
            <span>{{ p.title }}</span>
            <span class="ml-auto text-xs text-green-light/60">${{ p.total_amount }}</span>
          </label>
        </div>
        <div>
          <p class="mb-2 text-xs uppercase tracking-wider text-green-light/70">Fases (en orden)</p>
          <div v-if="selectedProposals.length === 0" class="rounded-xl border border-dashed border-border-default p-4 text-sm text-green-light/60">
            Selecciona al menos una propuesta.
          </div>
          <div
            v-for="(p, idx) in selectedProposals" :key="p.id"
            class="mb-2 flex items-center gap-2 rounded-xl border border-border-muted bg-surface-muted/30 px-3 py-2"
          >
            <span class="font-medium">{{ idx + 1 }}. {{ p.title }}</span>
            <span class="ml-auto text-xs text-green-light/60">${{ p.total_amount }}</span>
            <button class="rounded-lg border border-red-500/30 px-2 py-1 text-xs text-red-600" @click="unselect(p.id)">×</button>
          </div>
        </div>
      </section>

      <!-- Step 3 -->
      <section v-if="step === 3">
        <p class="text-sm text-green-light">Confirmación</p>
        <p class="mt-2 text-base font-medium text-text-default">Cliente: {{ selectedClient?.email }}</p>
        <ol class="mt-3 space-y-1">
          <li v-for="(p, idx) in selectedProposals" :key="p.id" class="text-sm">
            {{ idx + 1 }}. {{ p.title }} — ${{ p.total_amount }}
          </li>
        </ol>
        <p class="mt-3 text-sm font-medium">Total: ${{ totalAmount }}</p>
      </section>

      <!-- Footer -->
      <div class="mt-6 flex justify-between">
        <button v-if="step > 1" class="rounded-xl border border-border-default px-3 py-2 text-sm" @click="step--">Atrás</button>
        <span v-else></span>
        <button
          v-if="step < 3"
          data-testid="next-step"
          class="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white"
          @click="nextStep"
        >Siguiente</button>
        <button
          v-else
          class="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white"
          :disabled="busy"
          @click="submit"
        >{{ mode === 'create' ? 'Crear proyecto' : 'Agregar fases' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { usePlatformProjectsStore } from '~/stores/platform-projects'

const props = defineProps({
  visible: { type: Boolean, default: false },
  mode: { type: String, default: 'create' },  // 'create' or 'add'
  clients: { type: Array, default: () => [] },
  projectId: { type: [Number, String], default: null },
  clientId: { type: Number, default: 0 },
})
const emit = defineEmits(['close', 'created', 'phases-added'])

const store = usePlatformProjectsStore()
const step = ref(1)
const clientId = ref(props.clientId || 0)
const eligibleProposals = ref([])
const selectedIds = ref([])
const error = ref('')
const busy = ref(false)

const selectedClient = computed(() => props.clients.find(c => c.user_id === clientId.value))
const selectedProposals = computed(() =>
  selectedIds.value.map(id => eligibleProposals.value.find(p => p.id === id)).filter(Boolean),
)
const totalAmount = computed(() => selectedProposals.value.reduce((acc, p) => acc + Number(p.total_amount || 0), 0))

watch(() => props.visible, (v) => {
  if (v) {
    step.value = props.mode === 'add' ? 2 : 1
    clientId.value = props.clientId || 0
    selectedIds.value = []
    eligibleProposals.value = []
    error.value = ''
    if (props.mode === 'add' && props.clientId) loadEligible()
  }
})

async function loadEligible() {
  if (!clientId.value) return
  eligibleProposals.value = await store.loadEligibleProposals(clientId.value)
}

async function nextStep() {
  error.value = ''
  if (step.value === 1) {
    if (!clientId.value) { error.value = 'Selecciona un cliente'; return }
    await loadEligible()
  }
  if (step.value === 2 && selectedIds.value.length === 0) {
    error.value = 'Selecciona al menos una propuesta'; return
  }
  step.value++
}

function unselect(id) {
  selectedIds.value = selectedIds.value.filter(x => x !== id)
}

async function submit() {
  busy.value = true
  try {
    if (props.mode === 'create') {
      // For MVP we hit POST /projects/ with phases inline. The serializer
      // change to accept `phases` is small; if it isn't deployed yet, fall
      // back to creating the project bare then adding phases.
      const project = await store.createProject({
        name: selectedProposals.value[0]?.title || 'Nuevo proyecto',
        client_id: clientId.value,
        phases: selectedProposals.value.map((p, i) => ({ proposal_id: p.id, order: i + 1 })),
      })
      // If the backend ignores `phases`, append them now (idempotent fallback):
      if (project && project.id && (project.phases_count ?? 0) === 0) {
        for (let i = 0; i < selectedProposals.value.length; i++) {
          await store.addPhase(project.id, selectedProposals.value[i].id, i + 1)
        }
      }
      emit('created', project)
    } else {
      for (let i = 0; i < selectedProposals.value.length; i++) {
        await store.addPhase(props.projectId, selectedProposals.value[i].id, null)
      }
      emit('phases-added')
    }
    emit('close')
  } finally {
    busy.value = false
  }
}
</script>
```

- [ ] **Step 4: Run tests**

```
npm --prefix frontend test -- test/components/platform/projects/PhaseSelectorModal.test.js 2>&1 | tail -8
```

Expected: 2 passed.

- [ ] **Step 5: Mount the modal in `frontend/pages/platform/projects/index.vue` (create mode)**

Add the button + modal in the template:

```vue
<div class="mb-4 flex items-center justify-between">
  <h1 class="text-xl font-semibold">Proyectos</h1>
  <button
    v-if="authStore.isAdmin"
    class="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white"
    @click="showCreate = true"
  >+ Nuevo proyecto</button>
</div>
<!-- existing filters + ProjectsTable here -->
<PhaseSelectorModal
  :visible="showCreate"
  mode="create"
  :clients="clientsStore.clients"
  @close="showCreate = false"
  @created="onProjectCreated"
/>
```

In `<script setup>`:

```js
import PhaseSelectorModal from '~/components/platform/projects/PhaseSelectorModal.vue'
import { usePlatformClientsStore } from '~/stores/platform-clients'

const clientsStore = usePlatformClientsStore()
const showCreate = ref(false)

onMounted(() => { clientsStore.fetchClients() })

async function onProjectCreated(project) {
  await projectsStore.fetchProjects()
  navigateTo(localePath(`/platform/projects/${project.id}`))
}
```

- [ ] **Step 6: Mount the modal in the Resumen (add-phase mode)**

In `frontend/pages/platform/projects/[id]/index.vue`, replace the empty `onAddPhase` stub:

```js
const showAddPhase = ref(false)

function onAddPhase() { showAddPhase.value = true }
async function onPhasesAdded() {
  await loadPhases()
  showAddPhase.value = false
}
```

And add the modal next to the `<PhaseList>`:

```vue
<PhaseSelectorModal
  :visible="showAddPhase"
  mode="add"
  :project-id="project?.id"
  :client-id="project?.client_id"
  @close="showAddPhase = false"
  @phases-added="onPhasesAdded"
/>
```

Import `PhaseSelectorModal` at the top.

- [ ] **Step 7: Smoke test the wizard**

Click "+ Nuevo proyecto" on `/platform/projects`. Verify all 3 steps render and the project gets created. From a project's Resumen, click "+ Agregar fase" and verify the add-mode flow appends phases.

- [ ] **Step 8: Commit**

```
git add frontend/components/platform/projects/PhaseSelectorModal.vue frontend/pages/platform/projects/index.vue frontend/pages/platform/projects/[id]/index.vue frontend/test/components/platform/projects/PhaseSelectorModal.test.js
git commit -m "FEAT: PhaseSelectorModal (3-step wizard) for project creation and phase add"
```

---

## Task 14 — Project-scoped `Accesos` page

**Files:**
- Create: `frontend/pages/platform/projects/[id]/access.vue`

The content is mostly migrated from the global `frontend/pages/platform/access.vue` but scoped to one project. Open the original file and adapt: keep the same layout and components, but drop the project-selection chrome (the project is fixed by the route).

- [ ] **Step 1: Open the existing global page**

Read `frontend/pages/platform/access.vue` to understand the layout (production / staging / Django admin / repo URL fields). Identify the parts that filter by project — those become hard-coded to `route.params.id`.

- [ ] **Step 2: Create the project-scoped page**

`frontend/pages/platform/projects/[id]/access.vue`:

```vue
<template>
  <ProjectShell>
    <section v-if="project" class="space-y-6">
      <h2 class="text-base font-medium text-text-default">Accesos del proyecto</h2>

      <div class="grid gap-4 sm:grid-cols-2">
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Producción</p>
          <a v-if="project.production_url" :href="project.production_url" target="_blank" class="mt-2 block text-sm text-text-default hover:underline">
            {{ project.production_url }}
          </a>
          <p v-else class="mt-2 text-sm text-green-light/60">—</p>
        </div>
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Staging</p>
          <a v-if="project.staging_url" :href="project.staging_url" target="_blank" class="mt-2 block text-sm text-text-default hover:underline">
            {{ project.staging_url }}
          </a>
          <p v-else class="mt-2 text-sm text-green-light/60">—</p>
        </div>
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Django admin</p>
          <a v-if="project.admin_url" :href="project.admin_url" target="_blank" class="block text-sm text-text-default hover:underline">
            {{ project.admin_url }}
          </a>
          <p v-if="project.admin_username" class="mt-2 text-sm">
            Usuario: <code class="rounded bg-surface-muted px-1">{{ project.admin_username }}</code>
          </p>
          <p v-if="project.admin_password" class="text-sm">
            Contraseña:
            <code class="rounded bg-surface-muted px-1" :class="{ 'blur-sm': !revealPassword }">{{ project.admin_password }}</code>
            <button class="ml-2 text-xs text-text-brand" @click="revealPassword = !revealPassword">{{ revealPassword ? 'Ocultar' : 'Mostrar' }}</button>
          </p>
        </div>
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Repositorio</p>
          <a v-if="project.repository_url" :href="project.repository_url" target="_blank" class="mt-2 block text-sm text-text-default hover:underline">
            {{ project.repository_url }}
          </a>
          <p v-else class="mt-2 text-sm text-green-light/60">—</p>
        </div>
      </div>
    </section>
    <div v-else class="px-6 py-12 text-center text-green-light/60">Cargando…</div>
  </ProjectShell>
</template>

<script setup>
import { computed, ref } from 'vue'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import ProjectShell from '~/components/platform/projects/ProjectShell.vue'

definePageMeta({ middleware: ['platform-auth'], platformRole: 'admin' })

const store = usePlatformProjectsStore()
const project = computed(() => store.currentProject)
const revealPassword = ref(false)
</script>
```

- [ ] **Step 3: Smoke test**

Navigate to `/platform/projects/<id>/access`. Verify the page renders with the same data as the old global page (filtered to the project).

- [ ] **Step 4: Commit**

```
git add frontend/pages/platform/projects/[id]/access.vue
git commit -m "FEAT: project-scoped Accesos page (replaces global /platform/access)"
```

---

# PHASE D — Sidebar cutover, middleware, view catalog

(Phase C is folded into Task 13 above — the wizard exists alongside the modal.)

## Task 15 — Rewrite `PlatformSidebar.vue`

**Files:**
- Modify: `frontend/components/platform/PlatformSidebar.vue`

- [ ] **Step 1: Replace the three computed nav lists**

In `<script setup>` of `PlatformSidebar.vue`, replace `primaryItems`, `projectItems`, `accountItems`, `adminItems`, and `projectSubModules` with:

```js
const primaryItems = computed(() => {
  const items = [
    { label: 'Notificaciones', href: lp('/platform/notifications'), icon: 'bell', badge: notifStore.unreadCount },
    { label: 'Proyectos',      href: lp('/platform/projects'),      icon: 'folder' },
  ]
  if (authStore.isAdmin) {
    items.push({ label: 'Clientes', href: lp('/platform/clients'), icon: 'users' })
  }
  return items
})

const accountItems = computed(() => [
  { label: 'Configuración', href: lp('/platform/profile'), icon: 'settings' },
])

const adminItems = computed(() => [
  { label: 'Panel admin', href: '/panel', icon: 'external', external: true },
])
```

- [ ] **Step 2: Remove the obsolete sections in the template**

In the `<template>`:

- Delete the entire `<!-- Projects section (placeholder) -->` block (it referenced `projectItems`).
- Update the "Principal" section to use the new `primaryItems` and rename the section header to `Navegación`.
- Keep the Cuenta and Administración sections; the Administración block now renders just `adminItems` (Panel admin).

The resulting template (relevant parts) looks like:

```vue
<nav class="flex-1 overflow-y-auto px-3 py-4">
  <div class="mb-5">
    <p v-if="!isCollapsed" class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-green-light/60">Navegación</p>
    <SidebarItem v-for="item in primaryItems" :key="item.href" :item="item" :is-collapsed="isCollapsed" :is-active="isActive(item.href)" :disabled="item.disabled" />
  </div>

  <div class="mb-5">
    <p v-if="!isCollapsed" class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-green-light/60">Cuenta</p>
    <SidebarItem v-for="item in accountItems" :key="item.href" :item="item" :is-collapsed="isCollapsed" :is-active="isActive(item.href)" :disabled="item.disabled" />
    <button type="button" :class="[...]" @click="showThemePicker = true">
      <!-- existing Personaliza button content -->
    </button>
  </div>

  <div v-if="authStore.isAdmin" class="mb-5">
    <p v-if="!isCollapsed" class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-green-light/60">Administración</p>
    <SidebarItem v-for="item in adminItems" :key="item.href" :item="item" :is-collapsed="isCollapsed" :is-active="isActive(item.href)" :disabled="item.disabled" />
  </div>
</nav>
```

- [ ] **Step 3: Simplify `isActive()`**

The current `isActive()` special-cases `projectSubModules`. With those gone, simplify to direct prefix matching:

```js
function isActive(href) {
  const cleanPath = route.path.replace(/^\/[a-z]{2}-[a-z]{2}/, '')
  const cleanHref = href.replace(/^\/[a-z]{2}-[a-z]{2}/, '')
  return cleanPath === cleanHref || cleanPath.startsWith(`${cleanHref}/`)
}
```

- [ ] **Step 4: Visual smoke test**

Reload the platform as admin. Sidebar shows Navegación (Notificaciones, Proyectos, Clientes) + Cuenta + Administración (Panel admin). As client, only Notificaciones + Proyectos + Cuenta.

- [ ] **Step 5: Commit**

```
git add frontend/components/platform/PlatformSidebar.vue
git commit -m "REFACTOR: PlatformSidebar — collapse to Navegación/Cuenta/Administración"
```

---

## Task 16 — Landing redirect + viewCatalog cleanup

**Files:**
- Modify: `frontend/pages/platform/index.vue`
- Modify: `frontend/config/viewCatalog.js`

- [ ] **Step 1: Update the redirect**

In `frontend/pages/platform/index.vue`:

```vue
<script setup>
definePageMeta({
  layout: false,
  middleware: ['platform-auth'],
})
await navigateTo('/platform/projects')
</script>
```

(Only the path changes from `/platform/dashboard` to `/platform/projects`.)

- [ ] **Step 2: Update `viewCatalog.js`**

Open `frontend/config/viewCatalog.js`. In the platform section:

- Remove entries pointing to `/platform/board`, `/platform/bugs`, `/platform/changes`, `/platform/deliverables`, `/platform/payments`, `/platform/collection-accounts`, `/platform/access`, `/platform/dashboard`.
- Update `/platform/clients` and `/platform/projects` entries to `audience: 'admin'` (they are admin-gated).
- Add a new entry for `/platform/projects/:id/access`:

```js
{
  label: 'Accesos del proyecto',
  url: '/platform/projects/:id/access',
  file: 'frontend/pages/platform/projects/[id]/access.vue',
  reference: 'credenciales por proyecto',
  audience: 'admin',
  viewType: 'readonly',
},
```

- [ ] **Step 3: Smoke test root redirect**

Open `http://localhost:3000/es-co/platform/`. Expected: redirected to `/es-co/platform/projects`.

- [ ] **Step 4: Commit**

```
git add frontend/pages/platform/index.vue frontend/config/viewCatalog.js
git commit -m "REFACTOR: platform landing redirects to /projects + viewCatalog updated"
```

---

# PHASE E — Cleanup

## Task 17 — Add 301 redirects, then delete obsolete pages

**Files:**
- Create: small redirect pages, then delete obsolete ones.

Strategy: replace each obsolete page's content with a `<script setup>` that navigates away. This keeps the route resolvable (no 404) while delivering an effective 301. After a few releases, the redirect pages themselves can be deleted.

- [ ] **Step 1: Replace each obsolete page with a redirect**

Apply this content to each file:

`frontend/pages/platform/dashboard.vue`:
```vue
<script setup>
definePageMeta({ layout: false, middleware: ['platform-auth'] })
await navigateTo('/platform/projects')
</script>
```

`frontend/pages/platform/board.vue`:
```vue
<script setup>
definePageMeta({ layout: false, middleware: ['platform-auth'] })
await navigateTo('/platform/projects')
</script>
```

Repeat the same content for: `bugs.vue`, `changes.vue`, `deliverables.vue`, `payments.vue`, `collection-accounts/index.vue`, `collection-accounts/[id].vue`, `access.vue`.

(All 9 files now collapse to a 4-line redirect stub.)

- [ ] **Step 2: Smoke test the redirects**

Hit each old URL manually (`/platform/board`, `/platform/bugs`, `/platform/dashboard`, etc.). Each should redirect to `/platform/projects` instantly.

- [ ] **Step 3: Commit**

```
git add frontend/pages/platform/dashboard.vue frontend/pages/platform/board.vue frontend/pages/platform/bugs.vue frontend/pages/platform/changes.vue frontend/pages/platform/deliverables.vue frontend/pages/platform/payments.vue frontend/pages/platform/collection-accounts/ frontend/pages/platform/access.vue
git commit -m "REFACTOR: replace deleted global pages with redirects to /platform/projects"
```

---

## Task 18 — Update or remove E2E specs targeting deleted pages

**Files:**
- Modify or delete: `frontend/e2e/platform/platform-dashboard.spec.js`
- Modify: `frontend/e2e/platform/platform-bug-reports.spec.js`
- Modify: `frontend/e2e/platform/platform-change-requests.spec.js`
- Modify: `frontend/e2e/platform/platform-deliverables.spec.js`
- Modify: `frontend/e2e/platform/platform-collection-accounts.spec.js`
- Modify: `frontend/e2e/platform/platform-access.spec.js` (if exists)
- Create: `frontend/e2e/platform/platform-projects-table.spec.js`
- Create: `frontend/e2e/platform/platform-project-creation.spec.js`
- Create: `frontend/e2e/platform/platform-project-phases.spec.js`

This task's scope is large enough that one engineer working through it carefully is fine. Treat each spec individually:

- [ ] **Step 1: For each existing spec that targets a deleted page**

If the spec only checks the deleted route, replace the navigation with a per-project navigation. E.g. for `platform-bug-reports.spec.js`:

Before:
```js
await page.goto('/es-co/platform/bugs')
```

After:
```js
// Bugs only exist inside a project now. Mock a project list and navigate into one.
await page.route('**/api/accounts/projects/', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, name: 'Test', /* … */ }]) }))
await page.goto('/es-co/platform/projects/1/bugs')
```

- [ ] **Step 2: For `platform-dashboard.spec.js`**

Either delete the file entirely or replace its content with a single smoke test for the redirect:

```js
import { test, expect } from '../helpers/test.js'

test('root /platform redirects to /platform/projects', async ({ page }) => {
  await page.goto('/es-co/platform/', { waitUntil: 'domcontentloaded' })
  await page.waitForURL(/\/platform\/projects/, { waitUntil: 'domcontentloaded' })
})
```

- [ ] **Step 3: Create the new E2E specs**

`platform-projects-table.spec.js` — happy path: page loads, table renders, chevron navigates. Use the existing `mockApi` helper.

```js
import { test, expect } from '../helpers/test.js'
import { mockApi } from '../helpers/api.js'

test('Projects table renders rows and chevron drills into detail', async ({ page }) => {
  await mockApi(page, async ({ apiPath, method }) => {
    if (method === 'GET' && apiPath === 'accounts/projects/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([
        { id: 1, name: 'P1', status: 'active', progress: 50,
          client_name: 'Ada', client_email: 'ada@e.co', client_id: 9,
          bugs_open_count: 2, changes_pending_count: 1,
          next_deliverable: null, last_activity_at: new Date().toISOString() },
      ]) }
    }
    if (method === 'GET' && apiPath === 'accounts/projects/1/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, name: 'P1' }) }
    }
    return null
  })
  // ... login mock + navigate ...
  await page.goto('/es-co/platform/projects', { waitUntil: 'domcontentloaded' })
  await expect(page.locator('[data-testid="project-row-1"]')).toBeVisible({ timeout: 10000 })
  await page.locator('[data-testid="project-row-1"]').click()
  await page.waitForURL(/\/platform\/projects\/1/, { waitUntil: 'domcontentloaded' })
})
```

`platform-project-creation.spec.js` — walk the 3-step wizard with mocked endpoints.

`platform-project-phases.spec.js` — load a project with phases, add a new phase, verify it appears.

Each spec follows the same mocking pattern as the existing platform specs (see `platform-login.spec.js` and the password-reset spec from the prior branch for examples).

- [ ] **Step 4: Run the affected specs**

```
npm --prefix frontend run e2e -- e2e/platform/platform-projects-table.spec.js
npm --prefix frontend run e2e -- e2e/platform/platform-project-creation.spec.js
npm --prefix frontend run e2e -- e2e/platform/platform-project-phases.spec.js
```

Expected: all passing.

- [ ] **Step 5: Commit**

```
git add frontend/e2e/platform/
git commit -m "FEAT: E2E coverage for projects table, creation wizard, and phases"
```

---

# Self-review

**Spec coverage:**

| Spec § | Covered by |
|---|---|
| §3 Sidebar | Task 15 |
| §4 Projects table (admin) | Task 7 |
| §4 Projects table (client subset) | Task 7 (`role` prop) |
| §5 Clients table | Task 8 |
| §5.3 Client detail summary | **Out of scope** (spec §5.3 deferred); leave existing `clients/[id].vue` |
| §6 Project shell | Tasks 9, 10 |
| §6.3 Resumen | Tasks 11, 12 |
| §6.2 New `/projects/:id/access` page | Task 14 |
| §7 ProjectPhase model + endpoints | Tasks 1, 2, 3 |
| §7 Eligible proposals endpoint | Task 4 |
| §7.3 Create wizard | Task 13 |
| §7.4 PhaseList on Resumen | Task 12 |
| §8 Migration order | Phases A → B → C (folded into 13) → D → E follow the spec order |
| §9 Backend aggregated fields | Tasks 5, 6 |
| §9.4 Hosting cycles support | Verified in research before plan writing — already supports the 3 cycles |
| §10 Frontend changes | Phases B, D, E |
| §11 Tests | Backend tests in Tasks 1-6; frontend unit in 7, 12, 13; E2E in 18 |
| §12 Out of scope | Respected — Client detail UI, hosting management UI, bulk ops, global search, mobile not in plan |
| §13 Risks | Addressed: 301 redirects in Task 17; backfill handles projects without proposal (Task 1 step 5); `linked_business_proposal()` keeps same return shape (Task 1 step 4) |
| §14 Open questions | Step 4 of Task 6 confirms HostingSubscription field names by introspection at runtime |

**Placeholder scan:** no `TBD` / `TODO` / "fill in details" markers in the plan. The wizard's edit/archive/delete action stubs in Task 11 are explicitly out-of-scope per spec §6.3, not placeholders.

**Type consistency:**
- `ProjectPhase` fields (`project`, `business_proposal`, `order`, `created_at`) are consistent across Tasks 1, 2, 3.
- Service errors share the same `PhaseError(code, http_status, extra)` shape.
- Store action names match across Tasks 12 and 13 (`loadPhases`, `addPhase`, `removePhase`, `reorderPhases`, `loadEligibleProposals`).
- API endpoint paths consistent: `/projects/:id/phases/`, `/projects/:id/phases/:phaseId/`, `/projects/:id/phases/reorder/`, `/clients/:id/eligible-proposals/`.
- Component event names match: `PhaseList` emits `add-phase` and `changed`; `PhaseSelectorModal` emits `close`, `created`, `phases-added`. Resumen page listens for all these correctly.
