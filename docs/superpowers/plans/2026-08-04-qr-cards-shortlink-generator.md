# Tarjetas QR — QR Code + Short-Link Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Tarjetas QR" panel module: admins create UUID-identified "cards", each with an editable destination URL; the UUID is reachable at a public short link (`/t/<uuid>/`) that 302-redirects to the destination, and each card's QR (always encoding the short link, never the destination) can be downloaded as a PNG with a customizable foreground/background color and optional transparency — all client-side.

**Architecture:** New Django model `QRCard` in the `content` app with function-based `@api_view` admin CRUD endpoints and a separate `AllowAny` public redirect view registered as a top-level Django route (outside `/api/`, before the Nuxt SPA catch-all). New Nuxt panel page with a Pinia store (Options API, same shape as `portfolio_works.js`) driving a listing table, a create/edit modal, and a dedicated `DownloadQrModal.vue` component that renders the QR client-side via the `qrcode` npm package (which natively supports 8-digit hex colors, so transparency is just an alpha channel — no server involvement, nothing persisted).

**Tech Stack:** Django 5 + DRF (backend), Nuxt 3 + Vue 3 + Pinia (frontend), `qrcode` npm package (new frontend dependency, client-side QR rendering), pytest (backend tests), Jest (frontend unit tests), Playwright (E2E).

**Full design spec:** `docs/superpowers/specs/2026-08-04-qr-cards-shortlink-generator-design.md`

## Global Constraints

- Backend views are function-based DRF views with `@api_view` — never CBVs.
- Business logic goes in serializers/model methods; views stay thin request/response wiring.
- Content/admin HTTP flows use `frontend/stores/services/request_http.js` — never `usePlatformApi.js`.
- Pinia stores use the Options API shape: `{ state, getters, actions }`.
- Never edit existing Django migrations — add a new one.
- New frontend views/components use semantic design tokens (`bg-surface`, `text-text-default`, etc.) and `frontend/components/base/*` components — never `bg-white dark:bg-gray-800` patterns.
- Never run the full backend or frontend test suite — run only the files this plan touches.
- No `Co-Authored-By: Claude` or "Generated with Claude Code" in any commit message.
- The sidebar label is **"Tarjetas QR"**, never bare "Tarjetas" — that label is already taken by `/panel/accounting/cards` (credit-card snapshots) and reusing it is ambiguous.
- The QR always encodes the short link (`{origin}/t/{uuid}/`), never the destination URL directly, and color/transparency choices are never persisted — ephemeral form state only.

---

### Task 1: `QRCard` model + migration

**Files:**
- Create: `backend/content/models/qr_cards.py`
- Modify: `backend/content/models/__init__.py` (add import, after line 32 `from .proposal_share_link import ProposalShareLink`)
- Test: `backend/content/tests/models/test_qr_cards.py`

**Interfaces:**
- Produces: `QRCard` model with fields `id` (UUID primary key), `name` (str), `destination_url` (str, blank-ok), `is_active` (bool, default `True`), `created_at`, `updated_at`. Exported from `content.models`.

- [ ] **Step 1: Write the failing test**

```python
# backend/content/tests/models/test_qr_cards.py
"""Tests for the QRCard model."""
import pytest

from content.models import QRCard

pytestmark = pytest.mark.django_db


class TestQRCardModel:
    def test_id_is_auto_generated(self):
        card = QRCard.objects.create(name='Tarjeta evento X')
        assert card.id is not None

    def test_ids_are_unique_across_cards(self):
        card_a = QRCard.objects.create(name='Tarjeta A')
        card_b = QRCard.objects.create(name='Tarjeta B')
        assert card_a.id != card_b.id

    def test_is_active_defaults_to_true(self):
        card = QRCard.objects.create(name='Tarjeta evento X')
        assert card.is_active is True

    def test_destination_url_defaults_to_empty_string(self):
        card = QRCard.objects.create(name='Tarjeta evento X')
        assert card.destination_url == ''

    def test_str_includes_name_and_id(self):
        card = QRCard.objects.create(name='Tarjeta evento X')
        assert 'Tarjeta evento X' in str(card)
        assert str(card.id) in str(card)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/models/test_qr_cards.py -v`
Expected: FAIL with `ImportError: cannot import name 'QRCard' from 'content.models'`

- [ ] **Step 3: Write the model**

```python
# backend/content/models/qr_cards.py
import uuid

from django.db import models


class QRCard(models.Model):
    """
    A QR-code + short-link card. The UUID is the permanent identifier
    printed/embedded in the QR; the destination it redirects to can be
    changed at any time without invalidating the printed code.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    destination_url = models.URLField(max_length=500, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'QR Card'
        verbose_name_plural = 'QR Cards'

    def __str__(self):
        return f'{self.name} ({self.id})'
```

- [ ] **Step 4: Register the model in `content/models/__init__.py`**

Add this line right after `from .proposal_share_link import ProposalShareLink` (line 32):

```python
from .qr_cards import QRCard
```

- [ ] **Step 5: Generate the migration**

Run: `source .venv/bin/activate && cd backend && python manage.py makemigrations content`
Expected: creates `backend/content/migrations/0174_qrcard.py` (next number after `0173_expense_source_income_and_regross.py` — confirm the actual generated filename/number and adjust later references if it differs).

- [ ] **Step 6: Run test to verify it passes**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/models/test_qr_cards.py -v`
Expected: PASS (5 tests)

- [ ] **Step 7: Commit**

```bash
git add backend/content/models/qr_cards.py backend/content/models/__init__.py backend/content/migrations/0174_qrcard.py backend/content/tests/models/test_qr_cards.py
git commit -m "feat: add QRCard model for the Tarjetas QR module"
```

---

### Task 2: Serializers

**Files:**
- Create: `backend/content/serializers/qr_cards.py`
- Test: `backend/content/tests/serializers/test_qr_cards_serializers.py`

**Interfaces:**
- Consumes: `QRCard` model from Task 1.
- Produces: `QRCardListSerializer` (fields: `id`, `name`, `destination_url`, `is_active`, `created_at`) and `QRCardCreateUpdateSerializer` (fields: `name` required, `destination_url` optional URL-validated, `is_active` optional).

- [ ] **Step 1: Write the failing test**

```python
# backend/content/tests/serializers/test_qr_cards_serializers.py
"""Tests for QRCard serializers."""
import pytest

from content.models import QRCard
from content.serializers.qr_cards import (
    QRCardListSerializer,
    QRCardCreateUpdateSerializer,
)

pytestmark = pytest.mark.django_db


class TestQRCardListSerializer:
    def test_serializes_expected_fields(self):
        card = QRCard.objects.create(name='Tarjeta evento X', destination_url='https://example.com')
        data = QRCardListSerializer(card).data
        assert data['name'] == 'Tarjeta evento X'
        assert data['destination_url'] == 'https://example.com'
        assert data['is_active'] is True
        assert 'id' in data
        assert 'created_at' in data


class TestQRCardCreateUpdateSerializer:
    def test_valid_with_only_name(self):
        serializer = QRCardCreateUpdateSerializer(data={'name': 'Tarjeta evento X'})
        assert serializer.is_valid(), serializer.errors

    def test_invalid_without_name(self):
        serializer = QRCardCreateUpdateSerializer(data={'destination_url': 'https://example.com'})
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

    def test_invalid_with_malformed_destination_url(self):
        serializer = QRCardCreateUpdateSerializer(data={'name': 'X', 'destination_url': 'not-a-url'})
        assert not serializer.is_valid()
        assert 'destination_url' in serializer.errors

    def test_valid_with_empty_destination_url(self):
        serializer = QRCardCreateUpdateSerializer(data={'name': 'X', 'destination_url': ''})
        assert serializer.is_valid(), serializer.errors
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/serializers/test_qr_cards_serializers.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'content.serializers.qr_cards'`

- [ ] **Step 3: Write the serializers**

```python
# backend/content/serializers/qr_cards.py
from rest_framework import serializers

from content.models import QRCard


class QRCardListSerializer(serializers.ModelSerializer):
    """Admin listing serializer — every field a listing row or edit form needs."""

    class Meta:
        model = QRCard
        fields = ('id', 'name', 'destination_url', 'is_active', 'created_at')


class QRCardCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating a QR card from the admin panel."""

    class Meta:
        model = QRCard
        fields = ('name', 'destination_url', 'is_active')
        extra_kwargs = {
            'destination_url': {'required': False, 'allow_blank': True},
            'is_active': {'required': False},
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/serializers/test_qr_cards_serializers.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/content/serializers/qr_cards.py backend/content/tests/serializers/test_qr_cards_serializers.py
git commit -m "feat: add QRCard serializers"
```

---

### Task 3: Admin CRUD views + URL registration

**Files:**
- Create: `backend/content/views/qr_cards.py` (admin CRUD functions only — the public redirect view is Task 4, in the same file)
- Modify: `backend/content/urls.py` (add import near line 48, add routes near the portfolio admin block, e.g. after line 456)
- Test: `backend/content/tests/views/test_qr_cards_views.py`

**Interfaces:**
- Consumes: `QRCard`, `QRCardListSerializer`, `QRCardCreateUpdateSerializer` from Tasks 1-2.
- Produces: URL names `list-admin-qr-cards`, `create-qr-card`, `update-qr-card`, `delete-qr-card` (all under `/api/qr-cards/admin/...`), used by the frontend store in Task 5.

- [ ] **Step 1: Write the failing tests**

```python
# backend/content/tests/views/test_qr_cards_views.py
"""Tests for QRCard admin CRUD views (the public redirect view is tested
in test_qr_card_redirect.py, since it lives outside /api/)."""
import pytest
from django.urls import reverse

from content.models import QRCard

pytestmark = pytest.mark.django_db


@pytest.fixture
def qr_card(db):
    return QRCard.objects.create(name='Tarjeta evento X', destination_url='https://example.com')


class TestAdminListQrCards:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('list-admin-qr-cards'))
        assert response.status_code in (401, 403)

    def test_returns_200_with_all_cards(self, admin_client, qr_card):
        response = admin_client.get(reverse('list-admin-qr-cards'))
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'Tarjeta evento X'


class TestAdminCreateQrCard:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.post(reverse('create-qr-card'), {}, format='json')
        assert response.status_code in (401, 403)

    def test_creates_card_returns_201(self, admin_client):
        payload = {'name': 'Tarjeta nueva'}
        response = admin_client.post(reverse('create-qr-card'), payload, format='json')
        assert response.status_code == 201
        assert QRCard.objects.count() == 1
        assert response.data['is_active'] is True

    def test_returns_400_without_name(self, admin_client):
        response = admin_client.post(reverse('create-qr-card'), {}, format='json')
        assert response.status_code == 400


class TestAdminUpdateQrCard:
    def test_returns_401_for_unauthenticated(self, api_client, qr_card):
        url = reverse('update-qr-card', kwargs={'card_id': qr_card.id})
        response = api_client.patch(url, {}, format='json')
        assert response.status_code in (401, 403)

    def test_updates_destination_url(self, admin_client, qr_card):
        url = reverse('update-qr-card', kwargs={'card_id': qr_card.id})
        response = admin_client.patch(url, {'destination_url': 'https://new-destination.com'}, format='json')
        assert response.status_code == 200
        qr_card.refresh_from_db()
        assert qr_card.destination_url == 'https://new-destination.com'

    def test_toggles_is_active(self, admin_client, qr_card):
        url = reverse('update-qr-card', kwargs={'card_id': qr_card.id})
        response = admin_client.patch(url, {'is_active': False}, format='json')
        assert response.status_code == 200
        qr_card.refresh_from_db()
        assert qr_card.is_active is False

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('update-qr-card', kwargs={'card_id': '11111111-1111-1111-1111-111111111111'})
        response = admin_client.patch(url, {'name': 'X'}, format='json')
        assert response.status_code == 404


class TestAdminDeleteQrCard:
    def test_returns_401_for_unauthenticated(self, api_client, qr_card):
        url = reverse('delete-qr-card', kwargs={'card_id': qr_card.id})
        response = api_client.delete(url)
        assert response.status_code in (401, 403)

    def test_deletes_card_returns_204(self, admin_client, qr_card):
        url = reverse('delete-qr-card', kwargs={'card_id': qr_card.id})
        response = admin_client.delete(url)
        assert response.status_code == 204
        assert QRCard.objects.count() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/views/test_qr_cards_views.py -v`
Expected: FAIL with `NoReverseMatch` (URL names don't exist yet)

- [ ] **Step 3: Write the admin CRUD views**

```python
# backend/content/views/qr_cards.py
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import QRCard
from content.serializers.qr_cards import QRCardListSerializer, QRCardCreateUpdateSerializer


# ---------------------------------------------------------------------------
# Admin endpoints (staff only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_admin_qr_cards(request):
    """List all QR cards for admin management."""
    qs = QRCard.objects.all()
    serializer = QRCardListSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_qr_card(request):
    """Create a new QR card."""
    serializer = QRCardCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    card = serializer.save()
    detail = QRCardListSerializer(card)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_qr_card(request, card_id):
    """Update a QR card's name, destination_url and/or is_active."""
    card = get_object_or_404(QRCard, pk=card_id)
    serializer = QRCardCreateUpdateSerializer(card, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    detail = QRCardListSerializer(card)
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_qr_card(request, card_id):
    """Delete a QR card."""
    card = get_object_or_404(QRCard, pk=card_id)
    card.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 4: Register the URLs**

In `backend/content/urls.py`, add this import after line 48 (the `upload_portfolio_cover_image,` import block):

```python
from content.views.qr_cards import (
    list_admin_qr_cards, create_qr_card, update_qr_card, delete_qr_card,
)
```

Add these routes after line 456 (`path('portfolio/admin/<int:work_id>/duplicate/', ...)`), before the `upload-cover` line:

```python
    # QR Cards — admin CRUD
    path('qr-cards/admin/', list_admin_qr_cards, name='list-admin-qr-cards'),
    path('qr-cards/admin/create/', create_qr_card, name='create-qr-card'),
    path('qr-cards/admin/<uuid:card_id>/update/', update_qr_card, name='update-qr-card'),
    path('qr-cards/admin/<uuid:card_id>/delete/', delete_qr_card, name='delete-qr-card'),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/views/test_qr_cards_views.py -v`
Expected: PASS (9 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/content/views/qr_cards.py backend/content/urls.py backend/content/tests/views/test_qr_cards_views.py
git commit -m "feat: add QRCard admin CRUD endpoints"
```

---

### Task 4: Public redirect view + top-level URL

**Files:**
- Modify: `backend/content/views/qr_cards.py` (append the redirect view)
- Modify: `backend/projectapp/urls.py` (add import + top-level route, before the catch-all)
- Test: `backend/content/tests/views/test_qr_card_redirect.py`

**Interfaces:**
- Consumes: `QRCard` from Task 1.
- Produces: URL name `qr-card-redirect` at `/t/<uuid:card_id>/`, a top-level (non-`/api/`) route — this is the short link the frontend's `DownloadQrModal` (Task 7) encodes into the QR.

- [ ] **Step 1: Write the failing tests**

```python
# backend/content/tests/views/test_qr_card_redirect.py
"""Tests for the public QR card redirect view (top-level /t/<uuid>/ route,
registered in projectapp/urls.py — NOT under /api/)."""
import pytest
from django.urls import reverse

from content.models import QRCard

pytestmark = pytest.mark.django_db


class TestQrCardRedirect:
    def test_returns_404_for_nonexistent_uuid(self, api_client):
        url = reverse('qr-card-redirect', kwargs={'card_id': '11111111-1111-1111-1111-111111111111'})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_redirects_to_destination_when_active_and_configured(self, api_client):
        card = QRCard.objects.create(name='X', destination_url='https://example.com/landing', is_active=True)
        url = reverse('qr-card-redirect', kwargs={'card_id': card.id})
        response = api_client.get(url)
        assert response.status_code == 302
        assert response.url == 'https://example.com/landing'

    def test_returns_200_with_message_when_inactive(self, api_client):
        card = QRCard.objects.create(name='X', destination_url='https://example.com/landing', is_active=False)
        url = reverse('qr-card-redirect', kwargs={'card_id': card.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'no está disponible' in response.content.decode()

    def test_returns_200_with_message_when_no_destination_configured(self, api_client):
        card = QRCard.objects.create(name='X', destination_url='', is_active=True)
        url = reverse('qr-card-redirect', kwargs={'card_id': card.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'aún no ha sido configurado' in response.content.decode()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/views/test_qr_card_redirect.py -v`
Expected: FAIL with `NoReverseMatch`

- [ ] **Step 3: Append the redirect view**

Add to the end of `backend/content/views/qr_cards.py`:

```python
from django.http import HttpResponse, HttpResponseRedirect
from rest_framework.permissions import AllowAny


# ---------------------------------------------------------------------------
# Public redirect endpoint (registered as a top-level route — see
# projectapp/urls.py — so the short link reads as /t/<uuid>/, not /api/t/<uuid>/)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def qr_card_redirect(request, card_id):
    """Resolve a QR card's UUID to its configured destination and redirect."""
    card = get_object_or_404(QRCard, pk=card_id)
    if not card.is_active:
        return HttpResponse(
            'Este enlace no está disponible.', content_type='text/plain; charset=utf-8'
        )
    if not card.destination_url:
        return HttpResponse(
            'Este enlace aún no ha sido configurado.', content_type='text/plain; charset=utf-8'
        )
    return HttpResponseRedirect(card.destination_url)
```

(Move the `from django.http import ...` and `AllowAny` import to the top of the file alongside the existing imports rather than inline — inline shown here only to make the diff obvious.)

- [ ] **Step 4: Register the top-level URL**

In `backend/projectapp/urls.py`, add this import after line 10 (`from content.views.blog import serve_sitemap_xml`):

```python
from content.views.qr_cards import qr_card_redirect
```

Add this line to the `urlpatterns` list right after line 40 (`path('sitemap.xml', serve_sitemap_xml, name='sitemap-xml'),`), still inside the initial list — i.e. before the `urlpatterns += static(...)` line:

```python
    path('t/<uuid:card_id>/', qr_card_redirect, name='qr-card-redirect'),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/views/test_qr_card_redirect.py -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/content/views/qr_cards.py backend/projectapp/urls.py backend/content/tests/views/test_qr_card_redirect.py
git commit -m "feat: add public short-link redirect for QR cards"
```

---

### Task 5: Pinia store (`qr_cards.js`)

**Files:**
- Create: `frontend/stores/qr_cards.js`
- Test: `frontend/test/stores/qr_cards.test.js`

**Interfaces:**
- Consumes: `get_request`, `create_request`, `patch_request`, `delete_request` from `frontend/stores/services/request_http.js`; backend endpoints from Task 3 (`qr-cards/admin/`, `qr-cards/admin/create/`, `qr-cards/admin/<id>/update/`, `qr-cards/admin/<id>/delete/`).
- Produces: `useQrCardsStore()` with `state.cards` (Array), `state.isLoading`, `state.isUpdating`, `state.error`; actions `fetchCards()`, `createCard(payload)`, `updateCard(id, payload)`, `deleteCard(id)` — each returning `{ success: boolean, data?, errors? }`. Consumed by the page in Task 8.

- [ ] **Step 1: Write the failing test**

```javascript
// frontend/test/stores/qr_cards.test.js
/**
 * Tests for the qr_cards store.
 * Covers: initial state, fetchCards, createCard, updateCard, deleteCard.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useQrCardsStore } from '../../stores/qr_cards';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const {
  get_request, create_request, patch_request, delete_request,
} = require('../../stores/services/request_http');

const mockCard = {
  id: '11111111-1111-1111-1111-111111111111',
  name: 'Tarjeta evento X',
  destination_url: '',
  is_active: true,
};

describe('useQrCardsStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useQrCardsStore();
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  describe('initial state', () => {
    it('has empty cards array', () => {
      expect(store.cards).toEqual([]);
    });

    it('has isLoading false', () => {
      expect(store.isLoading).toBe(false);
    });

    it('has null error', () => {
      expect(store.error).toBeNull();
    });
  });

  describe('fetchCards', () => {
    it('fetches cards and updates state', async () => {
      get_request.mockResolvedValue({ data: [mockCard] });

      const result = await store.fetchCards();

      expect(get_request).toHaveBeenCalledWith('qr-cards/admin/');
      expect(store.cards).toHaveLength(1);
      expect(result.success).toBe(true);
    });

    it('handles API error gracefully', async () => {
      get_request.mockRejectedValue(new Error('Network error'));

      const result = await store.fetchCards();

      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
    });
  });

  describe('createCard', () => {
    it('creates a card and prepends it to the list', async () => {
      create_request.mockResolvedValue({ data: mockCard });

      const result = await store.createCard({ name: 'Tarjeta evento X' });

      expect(create_request).toHaveBeenCalledWith('qr-cards/admin/create/', { name: 'Tarjeta evento X' });
      expect(store.cards[0]).toEqual(mockCard);
      expect(result.success).toBe(true);
    });

    it('returns validation errors on failure', async () => {
      const error = new Error('Bad request');
      error.response = { data: { name: ['This field is required.'] } };
      create_request.mockRejectedValue(error);

      const result = await store.createCard({});

      expect(result.success).toBe(false);
      expect(result.errors).toEqual({ name: ['This field is required.'] });
      expect(store.error).toBe('create_failed');
    });
  });

  describe('updateCard', () => {
    it('updates a card in place', async () => {
      store.cards = [mockCard];
      const updated = { ...mockCard, destination_url: 'https://example.com' };
      patch_request.mockResolvedValue({ data: updated });

      const result = await store.updateCard(mockCard.id, { destination_url: 'https://example.com' });

      expect(patch_request).toHaveBeenCalledWith(`qr-cards/admin/${mockCard.id}/update/`, { destination_url: 'https://example.com' });
      expect(store.cards[0].destination_url).toBe('https://example.com');
      expect(result.success).toBe(true);
    });

    it('handles API error gracefully', async () => {
      patch_request.mockRejectedValue(new Error('Network error'));

      const result = await store.updateCard(mockCard.id, {});

      expect(result.success).toBe(false);
      expect(store.error).toBe('update_failed');
    });
  });

  describe('deleteCard', () => {
    it('removes the card from the list', async () => {
      store.cards = [mockCard];
      delete_request.mockResolvedValue({});

      const result = await store.deleteCard(mockCard.id);

      expect(delete_request).toHaveBeenCalledWith(`qr-cards/admin/${mockCard.id}/delete/`);
      expect(store.cards).toHaveLength(0);
      expect(result.success).toBe(true);
    });

    it('handles API error gracefully', async () => {
      delete_request.mockRejectedValue(new Error('Network error'));

      const result = await store.deleteCard(mockCard.id);

      expect(result.success).toBe(false);
      expect(store.error).toBe('delete_failed');
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix frontend test -- test/stores/qr_cards.test.js`
Expected: FAIL — `Cannot find module '../../stores/qr_cards'`

- [ ] **Step 3: Write the store**

```javascript
// frontend/stores/qr_cards.js
import { defineStore } from 'pinia';
import { get_request, create_request, patch_request, delete_request } from './services/request_http';

export const useQrCardsStore = defineStore('qr_cards', {
  state: () => ({
    cards: [],
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    getCardById: (state) => (id) => state.cards.find((c) => c.id === id),
  },

  actions: {
    async fetchCards() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request('qr-cards/admin/');
        this.cards = response.data || [];
        return { success: true };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching QR cards:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    async createCard(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('qr-cards/admin/create/', payload);
        this.cards.unshift(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_failed';
        console.error('Error creating QR card:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async updateCard(id, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`qr-cards/admin/${id}/update/`, payload);
        const index = this.cards.findIndex((c) => c.id === id);
        if (index !== -1) this.cards[index] = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error('Error updating QR card:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async deleteCard(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`qr-cards/admin/${id}/delete/`);
        this.cards = this.cards.filter((c) => c.id !== id);
        return { success: true };
      } catch (error) {
        this.error = 'delete_failed';
        console.error('Error deleting QR card:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },
  },
});
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix frontend test -- test/stores/qr_cards.test.js`
Expected: PASS (11 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/stores/qr_cards.js frontend/test/stores/qr_cards.test.js
git commit -m "feat: add qr_cards Pinia store"
```

---

### Task 6: Sidebar icon + nav entry + view catalog entries

**Files:**
- Modify: `frontend/components/platform/SidebarIcon.vue` (add `'qrcode'` case before the fallback `v-else`)
- Modify: `frontend/config/panelNav.js` (add nav item to the `site` section, after line 63)
- Modify: `frontend/config/viewCatalog.js` (add one `list` entry after the portfolio block, i.e. after line 365)

**Interfaces:**
- Produces: sidebar entry "Tarjetas QR" → `/panel/qr-cards`; a `viewCatalog.js` entry so the `/panel/views` map audit doesn't flag the new page as orphaned once Task 8 creates it.

- [ ] **Step 1: Add the `qrcode` icon case**

In `frontend/components/platform/SidebarIcon.vue`, insert this right before the `<!-- Fallback: circle -->` template (the last one before `</svg>`):

```html
    <!-- QR code / Tarjetas QR -->
    <template v-else-if="name === 'qrcode'">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <path d="M14 14h3v3h-3zM19 14h2v2h-2zM14 19h2v2h-2zM19 19h2v2h-2z" />
    </template>
```

- [ ] **Step 2: Add the nav entry**

In `frontend/config/panelNav.js`, in the `site` section (`id: 'site'`), add a line right after line 63 (`{ label: 'Portafolio', href: lp('/panel/portfolio'), icon: 'portfolio' },`):

```javascript
        { label: 'Tarjetas QR', href: lp('/panel/qr-cards'), icon: 'qrcode' },
```

- [ ] **Step 3: Add the view catalog entry**

In `frontend/config/viewCatalog.js`, add this object right after the portfolio edit-view entry (after line 365, still inside the `admin-panel` section's `views` array):

```javascript
      {
        label: 'Tarjetas QR del panel',
        url: '/panel/qr-cards',
        group: 'Tarjetas QR',
        file: 'frontend/pages/panel/qr-cards/index.vue',
        reference: 'listado de tarjetas QR con generador de link corto y descarga de QR personalizable',
        audience: 'admin',
        viewType: 'list',
      },
```

- [ ] **Step 4: Run the existing SidebarIcon test to confirm no regression**

Run: `npm --prefix frontend test -- test/components/SidebarIcon.test.js`
Expected: PASS (existing tests unaffected — this only adds a new branch, changes nothing else)

- [ ] **Step 5: Commit**

```bash
git add frontend/components/platform/SidebarIcon.vue frontend/config/panelNav.js frontend/config/viewCatalog.js
git commit -m "feat: wire Tarjetas QR into sidebar nav and view catalog"
```

---

### Task 7: `qrcode` dependency + `DownloadQrModal.vue`

**Files:**
- Modify: `frontend/package.json` (add `qrcode` dependency)
- Create: `frontend/components/panel/qr-cards/DownloadQrModal.vue`
- Test: `frontend/test/components/DownloadQrModal.test.js`

**Interfaces:**
- Consumes: `BaseModal`, `BaseFormField`, `BaseButton`, `BaseCheckbox` from `frontend/components/base/`; the `qrcode` npm package's `QRCode.toCanvas(canvasEl, text, options)` (Promise-based when no callback is passed).
- Produces: `<DownloadQrModal v-model="open" :card="card" />` — a self-contained modal. `card` needs only `{ id, name }`. Consumed by the page in Task 8.

- [ ] **Step 1: Install the dependency**

Run: `npm --prefix frontend install qrcode@^1.5.4`
Expected: `frontend/package.json` gains `"qrcode": "^1.5.4"` under `dependencies`, and `frontend/package-lock.json` updates.

- [ ] **Step 2: Write the failing test**

```javascript
// frontend/test/components/DownloadQrModal.test.js
/**
 * Tests for DownloadQrModal.
 * Covers: renders when open, download button triggers a PNG download,
 * transparent-background checkbox disables the background color picker.
 */
import { mount } from '@vue/test-utils';
import DownloadQrModal from '../../components/panel/qr-cards/DownloadQrModal.vue';

jest.mock('qrcode', () => ({
  toCanvas: jest.fn().mockResolvedValue(undefined),
}));

const QRCode = require('qrcode');

const card = { id: '11111111-1111-1111-1111-111111111111', name: 'Tarjeta evento X' };

describe('DownloadQrModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the canvas and card name when open', async () => {
    const wrapper = mount(DownloadQrModal, {
      props: { modelValue: true, card },
    });
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="qr-canvas"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Tarjeta evento X');
  });

  it('renders the QR encoding the short link, not the destination', async () => {
    const wrapper = mount(DownloadQrModal, {
      props: { modelValue: true, card },
    });
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(QRCode.toCanvas).toHaveBeenCalled();
    const [, encodedText] = QRCode.toCanvas.mock.calls[0];
    expect(encodedText).toContain(`/t/${card.id}/`);
  });

  it('disables the background color picker when transparent is checked', async () => {
    const wrapper = mount(DownloadQrModal, {
      props: { modelValue: true, card },
    });
    await wrapper.vm.$nextTick();

    await wrapper.find('[data-testid="qr-transparent-toggle"] input').setValue(true);

    expect(wrapper.find('[data-testid="qr-background-color"]').attributes('disabled')).toBeDefined();
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `npm --prefix frontend test -- test/components/DownloadQrModal.test.js`
Expected: FAIL — `Cannot find module '../../components/panel/qr-cards/DownloadQrModal.vue'`

- [ ] **Step 4: Write the component**

```vue
<!-- frontend/components/panel/qr-cards/DownloadQrModal.vue -->
<template>
  <BaseModal v-model="open" size="md">
    <div data-testid="qr-download-modal">
      <h3 class="text-lg font-bold text-text-default mb-4">Descargar QR — {{ card?.name }}</h3>

      <div class="flex justify-center mb-4">
        <canvas ref="canvasRef" data-testid="qr-canvas" />
      </div>

      <div class="space-y-3 mb-4">
        <BaseFormField label="Color del QR" for="qr-color">
          <input
            id="qr-color"
            v-model="foregroundColor"
            type="color"
            data-testid="qr-foreground-color"
            class="h-10 w-16 rounded-md border border-input-border bg-input-bg cursor-pointer"
          />
        </BaseFormField>

        <BaseFormField label="Color de fondo" for="qr-bg-color">
          <input
            id="qr-bg-color"
            v-model="backgroundColor"
            type="color"
            :disabled="transparentBackground"
            data-testid="qr-background-color"
            class="h-10 w-16 rounded-md border border-input-border bg-input-bg cursor-pointer disabled:opacity-50"
          />
        </BaseFormField>

        <BaseCheckbox v-model="transparentBackground" data-testid="qr-transparent-toggle">
          Fondo transparente
        </BaseCheckbox>
      </div>

      <div class="flex items-center justify-end gap-2">
        <BaseButton variant="ghost" size="sm" @click="open = false">Cerrar</BaseButton>
        <BaseButton variant="primary" size="sm" data-testid="qr-download-button" @click="download">
          Descargar PNG
        </BaseButton>
      </div>
    </div>
  </BaseModal>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import QRCode from 'qrcode';
import BaseModal from '~/components/base/BaseModal.vue';
import BaseFormField from '~/components/base/BaseFormField.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseCheckbox from '~/components/base/BaseCheckbox.vue';

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  card: { type: Object, default: null },
});
const emit = defineEmits(['update:modelValue']);

const open = ref(props.modelValue);
watch(() => props.modelValue, (value) => { open.value = value; });
watch(open, (value) => emit('update:modelValue', value));

const canvasRef = ref(null);
const foregroundColor = ref('#000000');
const backgroundColor = ref('#ffffff');
const transparentBackground = ref(false);

function shortLinkFor(card) {
  return `${window.location.origin}/t/${card.id}/`;
}

async function renderQr() {
  if (!open.value || !props.card || !canvasRef.value) return;
  const lightColor = transparentBackground.value
    ? `${backgroundColor.value}00`
    : `${backgroundColor.value}ff`;
  await QRCode.toCanvas(canvasRef.value, shortLinkFor(props.card), {
    width: 240,
    margin: 2,
    color: {
      dark: `${foregroundColor.value}ff`,
      light: lightColor,
    },
  });
}

watch(
  [open, foregroundColor, backgroundColor, transparentBackground, () => props.card],
  async () => {
    await nextTick();
    await renderQr();
  },
);

function download() {
  if (!canvasRef.value || !props.card) return;
  const link = document.createElement('a');
  link.download = `qr-${props.card.name.replace(/\s+/g, '-').toLowerCase()}.png`;
  link.href = canvasRef.value.toDataURL('image/png');
  link.click();
}
</script>
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npm --prefix frontend test -- test/components/DownloadQrModal.test.js`
Expected: PASS (3 tests)

- [ ] **Step 6: Check design tokens on the new file**

Run: `node frontend/scripts/check-design-tokens.mjs --files frontend/components/panel/qr-cards/DownloadQrModal.vue`
Expected: no offenses reported (the raw `<input type="color">` elements use `border-input-border`/`bg-input-bg` tokens already, not raw hex/gray classes).

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/components/panel/qr-cards/DownloadQrModal.vue frontend/test/components/DownloadQrModal.test.js
git commit -m "feat: add DownloadQrModal with color/transparency customization"
```

---

### Task 8: `index.vue` page — listing + create/edit modal

**Files:**
- Create: `frontend/pages/panel/qr-cards/index.vue`

**Interfaces:**
- Consumes: `useQrCardsStore` (Task 5), `DownloadQrModal` (Task 7), `usePanelNotify`, base components (`BaseButton`, `BaseModal`, `BaseInput`, `BaseFormField`, `BaseToggle`, `BaseEmptyState`).
- Produces: the `/panel/qr-cards` route referenced by Task 6's nav entry and view catalog entry, and by Task 9's E2E spec.

- [ ] **Step 1: Write the page**

```vue
<!-- frontend/pages/panel/qr-cards/index.vue -->
<template>
  <div>
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-light text-text-default">Tarjetas QR</h1>
        <p class="text-sm text-text-subtle mt-1">
          Generá códigos QR con un link corto y cambiá su destino cuando quieras, sin reimprimir nada.
        </p>
      </div>
      <BaseButton variant="primary" size="sm" data-testid="qr-card-new" @click="openCreateModal">
        Nueva tarjeta
      </BaseButton>
    </div>

    <div v-if="store.isLoading && store.cards.length === 0" class="text-center py-16 text-text-subtle text-sm">
      Cargando tarjetas...
    </div>

    <BaseEmptyState
      v-else-if="store.cards.length === 0"
      title="Sin tarjetas todavía"
      description="Creá tu primera tarjeta QR para generar un link corto."
    />

    <div v-else class="bg-surface border border-border-default rounded-xl shadow-card overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-surface-raised">
          <tr>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Nombre</th>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Link corto</th>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Destino</th>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Activa</th>
            <th class="text-right px-4 py-3 font-semibold text-text-muted">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border-muted">
          <tr v-for="card in store.cards" :key="card.id" :data-testid="`qr-card-row-${card.id}`">
            <td class="px-4 py-3 text-text-default">{{ card.name }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <code class="text-xs bg-surface-muted rounded px-2 py-1">{{ shortLinkFor(card) }}</code>
                <BaseButton variant="ghost" size="sm" icon-only aria-label="Copiar link" @click="copyLink(card)">
                  <ClipboardIcon class="h-4 w-4" />
                </BaseButton>
              </div>
            </td>
            <td class="px-4 py-3 text-text-muted">
              <span v-if="card.destination_url">{{ card.destination_url }}</span>
              <span v-else class="text-text-subtle italic">Sin configurar</span>
            </td>
            <td class="px-4 py-3">
              <BaseToggle
                :model-value="card.is_active"
                :aria-label="`Activar ${card.name}`"
                :data-testid="`qr-card-toggle-${card.id}`"
                @update:model-value="(value) => onToggleActive(card, value)"
              />
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-end gap-2">
                <BaseButton variant="secondary" size="sm" :data-testid="`qr-card-download-${card.id}`" @click="openDownloadModal(card)">
                  Descargar QR
                </BaseButton>
                <BaseButton variant="ghost" size="sm" :data-testid="`qr-card-edit-${card.id}`" @click="openEditModal(card)">
                  Editar
                </BaseButton>
                <BaseButton
                  variant="danger-ghost"
                  size="sm"
                  icon-only
                  aria-label="Eliminar tarjeta"
                  :data-testid="`qr-card-delete-${card.id}`"
                  @click="onDelete(card)"
                >
                  <TrashIcon class="h-4 w-4" />
                </BaseButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / edit modal -->
    <BaseModal v-model="formModal.open" size="md">
      <form data-testid="qr-card-form" @submit.prevent="onSubmit">
        <h3 class="text-lg font-bold text-text-default mb-4">
          {{ formModal.editingId ? 'Editar tarjeta' : 'Nueva tarjeta' }}
        </h3>

        <div class="space-y-4">
          <BaseFormField label="Nombre" for="qr-card-name" required :error="formErrors.name">
            <BaseInput id="qr-card-name" v-model="formModal.name" data-testid="qr-card-name-input" />
          </BaseFormField>

          <BaseFormField
            label="Link de destino"
            for="qr-card-destination"
            hint="Opcional — podés dejarlo vacío y completarlo después."
            :error="formErrors.destination_url"
          >
            <BaseInput
              id="qr-card-destination"
              v-model="formModal.destinationUrl"
              placeholder="https://..."
              data-testid="qr-card-destination-input"
            />
          </BaseFormField>
        </div>

        <div class="flex items-center justify-end gap-2 mt-6">
          <BaseButton type="button" variant="ghost" size="sm" @click="formModal.open = false">Cancelar</BaseButton>
          <BaseButton type="submit" variant="primary" size="sm" :loading="store.isUpdating" data-testid="qr-card-save">
            Guardar
          </BaseButton>
        </div>
      </form>
    </BaseModal>

    <DownloadQrModal v-model="downloadModal.open" :card="downloadModal.card" />
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue';
import { ClipboardIcon, TrashIcon } from '@heroicons/vue/24/outline';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseModal from '~/components/base/BaseModal.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BaseFormField from '~/components/base/BaseFormField.vue';
import BaseToggle from '~/components/base/BaseToggle.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import DownloadQrModal from '~/components/panel/qr-cards/DownloadQrModal.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useQrCardsStore } from '~/stores/qr_cards';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const store = useQrCardsStore();
const notify = usePanelNotify();

const formModal = reactive({ open: false, editingId: null, name: '', destinationUrl: '' });
const formErrors = reactive({ name: '', destination_url: '' });
const downloadModal = reactive({ open: false, card: null });

onMounted(() => {
  store.fetchCards();
});

function shortLinkFor(card) {
  return `${window.location.origin}/t/${card.id}/`;
}

async function copyLink(card) {
  try {
    await navigator.clipboard.writeText(shortLinkFor(card));
    notify.success({ title: 'Link copiado' });
  } catch {
    notify.error({ title: 'No se pudo copiar', detail: 'Copiá el link manualmente.' });
  }
}

function openCreateModal() {
  formModal.editingId = null;
  formModal.name = '';
  formModal.destinationUrl = '';
  formErrors.name = '';
  formErrors.destination_url = '';
  formModal.open = true;
}

function openEditModal(card) {
  formModal.editingId = card.id;
  formModal.name = card.name;
  formModal.destinationUrl = card.destination_url;
  formErrors.name = '';
  formErrors.destination_url = '';
  formModal.open = true;
}

function openDownloadModal(card) {
  downloadModal.card = card;
  downloadModal.open = true;
}

async function onToggleActive(card, value) {
  const result = await store.updateCard(card.id, { is_active: value });
  if (!result.success) {
    notify.error({ title: 'No se pudo actualizar la tarjeta' });
  }
}

async function onSubmit() {
  formErrors.name = '';
  formErrors.destination_url = '';
  const payload = { name: formModal.name, destination_url: formModal.destinationUrl };
  const result = formModal.editingId
    ? await store.updateCard(formModal.editingId, payload)
    : await store.createCard(payload);

  if (!result.success) {
    formErrors.name = result.errors?.name?.[0] || '';
    formErrors.destination_url = result.errors?.destination_url?.[0] || '';
    if (!result.errors) {
      notify.error({ title: 'No se pudo guardar la tarjeta' });
    }
    return;
  }
  formModal.open = false;
}

async function onDelete(card) {
  const result = await store.deleteCard(card.id);
  if (!result.success) {
    notify.error({ title: 'No se pudo eliminar la tarjeta' });
  }
}
</script>
```

- [ ] **Step 2: Check design tokens on the new file**

Run: `node frontend/scripts/check-design-tokens.mjs --files frontend/pages/panel/qr-cards/index.vue`
Expected: no offenses (page uses only semantic tokens and base components).

- [ ] **Step 3: Manual smoke check**

Run: `npm --prefix frontend run dev` (if not already running), then in a browser log into `/panel` and open `/panel/qr-cards`. Confirm: the empty state renders, "Nueva tarjeta" opens the modal, creating a card with just a name works, editing adds a destination, the active toggle flips, "Descargar QR" opens the QR modal and the PNG downloads with the chosen colors/transparency.

- [ ] **Step 4: Commit**

```bash
git add frontend/pages/panel/qr-cards/index.vue
git commit -m "feat: add Tarjetas QR panel page"
```

---

### Task 9: E2E coverage + flow map

**Files:**
- Modify: `frontend/e2e/helpers/flow-tags.js` (add `ADMIN_QR_CARDS` tag constant)
- Create: `frontend/e2e/admin/admin-qr-cards.spec.js`
- Modify: `docs/USER_FLOW_MAP.md` (add a `FLOW: admin-qr-cards` entry + coverage index row)
- Modify: `frontend/e2e/flow-definitions.json` (add the matching flow definition entry)

**Interfaces:**
- Consumes: the page from Task 8, the mock helpers `mockApi`/`setAuthLocalStorage` from `frontend/e2e/helpers/`.
- Produces: E2E coverage for the create/edit/toggle flows, satisfying the project's mandatory `e2e-user-flows-check` requirement for new panel views.

- [ ] **Step 1: Add the flow tag**

In `frontend/e2e/helpers/flow-tags.js`, add near the other `ADMIN_*` constants:

```javascript
export const ADMIN_QR_CARDS = ['@flow:admin-qr-cards', '@module:admin', '@priority:P2'];
```

- [ ] **Step 2: Write the E2E spec**

```javascript
// frontend/e2e/admin/admin-qr-cards.spec.js
/**
 * E2E tests for the Tarjetas QR panel module.
 *
 * Covers flow: admin-qr-cards
 *   - Creating a card with only a name (destination left empty).
 *   - Editing a card's destination_url.
 *   - Toggling a card's active state.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_QR_CARDS } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const existingCard = {
  id: '11111111-1111-1111-1111-111111111111',
  name: 'Tarjeta evento X',
  destination_url: '',
  is_active: true,
  created_at: '2026-08-01T10:00:00Z',
};

function setupQrCardsMock(page, { cards = [] } = {}) {
  let store = [...cards];
  return mockApi(page, async ({ apiPath, route }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'qr-cards/admin/' && route.request().method() === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(store) };
    }
    if (apiPath === 'qr-cards/admin/create/' && route.request().method() === 'POST') {
      const payload = route.request().postDataJSON();
      const created = {
        id: '22222222-2222-2222-2222-222222222222',
        is_active: true,
        destination_url: '',
        created_at: '2026-08-02T10:00:00Z',
        ...payload,
      };
      store = [created, ...store];
      return { status: 201, contentType: 'application/json', body: JSON.stringify(created) };
    }
    if (apiPath.match(/^qr-cards\/admin\/[^/]+\/update\/$/) && route.request().method() === 'PATCH') {
      const payload = route.request().postDataJSON();
      const id = apiPath.split('/')[2];
      store = store.map((c) => (c.id === id ? { ...c, ...payload } : c));
      const updated = store.find((c) => c.id === id);
      return { status: 200, contentType: 'application/json', body: JSON.stringify(updated) };
    }
    return null;
  });
}

test.describe('Admin QR Cards', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8900, role: 'admin', is_staff: true } });
  });

  test('creates a new card with only a name', {
    tag: [...ADMIN_QR_CARDS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await setupQrCardsMock(page, { cards: [] });
    await page.goto('/panel/qr-cards');
    await page.waitForLoadState('domcontentloaded');

    await page.getByTestId('qr-card-new').click();
    await page.getByTestId('qr-card-name-input').fill('Tarjeta evento X');
    await page.getByTestId('qr-card-save').click();

    await expect(page.getByText('Tarjeta evento X')).toBeVisible();
  });

  test('editing destination_url updates the row', {
    tag: [...ADMIN_QR_CARDS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await setupQrCardsMock(page, { cards: [existingCard] });
    await page.goto('/panel/qr-cards');
    await page.waitForLoadState('domcontentloaded');

    await page.getByTestId(`qr-card-edit-${existingCard.id}`).click();
    await page.getByTestId('qr-card-destination-input').fill('https://example.com/landing');
    await page.getByTestId('qr-card-save').click();

    await expect(page.getByText('https://example.com/landing')).toBeVisible();
  });

  test('toggling active state calls the update endpoint', {
    tag: [...ADMIN_QR_CARDS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await setupQrCardsMock(page, { cards: [existingCard] });
    await page.goto('/panel/qr-cards');
    await page.waitForLoadState('domcontentloaded');

    await page.getByTestId(`qr-card-toggle-${existingCard.id}`).click();

    await expect(page.getByTestId(`qr-card-toggle-${existingCard.id}`)).toHaveAttribute('aria-checked', 'false');
  });
});
```

- [ ] **Step 3: Run the E2E spec**

Run: `npm --prefix frontend run e2e -- e2e/admin/admin-qr-cards.spec.js`
Expected: PASS (3 tests)

- [ ] **Step 4: Update `docs/USER_FLOW_MAP.md`**

Add this entry right after the existing `#### FLOW: \`admin-blog-linkedin-publish\`` block (after line 4258, before `### 11.2 New Flows Coverage Index`):

```markdown
#### FLOW: `admin-qr-cards`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/qr-cards`
- **API:** `GET/POST /api/qr-cards/admin/`, `PATCH /api/qr-cards/admin/:id/update/`, `DELETE /api/qr-cards/admin/:id/delete/`; public redirect at `GET /t/:uuid/` (outside `/api/`).
- **Description:** Admin creates a "tarjeta" (name required, destination URL optional) which gets a UUID and a short public link (`/t/:uuid/`). The QR always encodes the short link, never the destination, so changing the destination later never requires reprinting. Admin can edit the destination, toggle active/inactive, and download a PNG QR with custom foreground/background colors or a transparent background — generated entirely client-side, never persisted.
- **Steps:**
  1. Admin opens `/panel/qr-cards`.
  2. Clicks "Nueva tarjeta", fills a name (destination optional), saves.
  3. Row appears with its short link, "Sin configurar" if no destination was set.
  4. Admin edits the card to set/change `destination_url`.
  5. Admin toggles the row's active switch.
  6. Admin clicks "Descargar QR", adjusts foreground/background color or checks "Fondo transparente", downloads the PNG.
- **Branches:**
  - [Branch A — no destination configured] Scanning the short link shows "Este enlace aún no ha sido configurado." instead of redirecting.
  - [Branch B — inactive card] Scanning the short link shows "Este enlace no está disponible." instead of redirecting.
  - [Branch C — active + configured] Scanning the short link 302-redirects to `destination_url`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-qr-cards.spec.js`
```

Add this row to the `### 11.2 New Flows Coverage Index` table:

```markdown
| `admin-qr-cards` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-qr-cards.spec.js` |
```

- [ ] **Step 5: Update `frontend/e2e/flow-definitions.json`**

Add this entry alongside the other `admin-blog-*` entries (matching the shape used by `admin-blog-linkedin-publish`):

```json
    "admin-qr-cards": {
      "name": "Admin QR Cards",
      "module": "admin",
      "roles": [
        "admin"
      ],
      "priority": "P2",
      "description": "Admin creates QR cards (name required, destination URL optional) that get a UUID short link (/t/:uuid/) redirecting to the configurable destination. QR always encodes the short link, never the destination. Download modal customizes foreground/background color and transparency client-side, without persisting the choice.",
      "expectedSpecs": 1,
      "outcomes": [
        "success"
      ]
    },
```

- [ ] **Step 6: Commit**

```bash
git add frontend/e2e/helpers/flow-tags.js frontend/e2e/admin/admin-qr-cards.spec.js docs/USER_FLOW_MAP.md frontend/e2e/flow-definitions.json
git commit -m "test: add E2E coverage and flow map entry for Tarjetas QR"
```

---

## Post-implementation checklist

- [ ] All 9 tasks committed as separate commits on `feat/04082026-qr-cards-shortlink-generator`.
- [ ] Push the branch and open a PR (per the repo's git workflow — this branch has no existing PR yet, so the first push creates one).
- [ ] Confirm `node frontend/scripts/check-design-tokens.mjs --scope=panel --quiet` shows no new offenses.
