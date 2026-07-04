# LinkedIn Content Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeform LinkedIn posts (draft → schedule → publish) managed from a new `/panel/linkedin` page, plus renaming the sidebar section "Website content" to "ProjectApp content".

**Architecture:** New `LinkedInPost` model + function-based DRF views in the `content` app, reusing the existing encrypted-token OAuth service (`linkedin_service.py`) untouched except for one new `publish_post_to_linkedin` function. Scheduling mirrors the blog pattern exactly: per-post Huey ETA task + every-minute periodic sweep with atomic status-transition guards. Frontend: new Pinia store `stores/linkedin.js` (Options API, `request_http.js`), single page with a create/edit `BaseModal`, popup-OAuth + `postMessage` flow copied from the blog edit page.

**Tech Stack:** Django 5 + DRF (function-based `@api_view`), Huey, Nuxt 3 + Vue 3 + Pinia, Playwright.

**Spec:** `docs/superpowers/specs/2026-07-04-linkedin-content-module-design.md`
**Branch:** `feat/04072026-linkedin-content-module` (created from `origin/main`)

## Global Constraints

- DRF views are function-based with `@api_view` + `@permission_classes([IsAdminUser])`; business logic in services/serializers.
- Never run full test suites. Max 20 tests per batch, 3 test commands per cycle. Backend: `source .venv/bin/activate && cd backend && pytest <file> -v`.
- Frontend unit: `npm --prefix frontend test -- <file>`. E2E: `npm --prefix frontend run e2e -- <file>`.
- New UI uses semantic tokens (`bg-surface`, `text-text-default`, `border-input-border`…) and `frontend/components/base/` components. Check with `node frontend/scripts/check-design-tokens.mjs --files <file>`.
- Commit messages: `FEAT:`/`FIX:`/`DOCS:` voice, NO `Co-Authored-By` trailers, NO "Generated with Claude Code" footers.
- Do not modify existing migrations; do not touch existing `linkedin_service.py` functions.
- LinkedIn API facts (verified against official docs 2026-07): text-only post payload has NO `content` key; image post uses `content: {media: {id: '<urn:li:image:…>'}}`; post ID returned in `x-restli-id` header on 201; commentary limit 3000 chars; `w_member_social` scope covers member freeform posts. Headers already handled by `_api_headers`.
- LinkedIn store/blog store test warning: LinkedIn actions are mocked at the request layer — never add fixtures that store real tokens or call linkedin.com.

---

### Task 1: `LinkedInPost` model + migration + admin

**Files:**
- Create: `backend/content/models/linkedin_post.py`
- Modify: `backend/content/models/__init__.py` (export `LinkedInPost`)
- Modify: `backend/content/admin.py` (register)
- Create: `backend/content/migrations/` (auto-generated)
- Test: `backend/content/tests/models/test_linkedin_post.py`

**Interfaces:**
- Produces: `LinkedInPost` with fields `commentary`, `image`, `status` (choices `draft|scheduled|published|failed`, constants `LinkedInPost.STATUS_DRAFT` etc.), `scheduled_at`, `published_at`, `linkedin_post_id`, `error_message`, `created_at`, `updated_at`. Ordering `-created_at`.

- [ ] **Step 1: Write the failing test**

```python
# backend/content/tests/models/test_linkedin_post.py
"""LinkedInPost model: defaults and status choices."""
import pytest

from content.models import LinkedInPost

pytestmark = pytest.mark.django_db


def test_create_post_defaults_to_draft():
    post = LinkedInPost.objects.create(commentary='Hola LinkedIn')
    assert post.status == LinkedInPost.STATUS_DRAFT
    assert post.scheduled_at is None
    assert post.published_at is None
    assert post.linkedin_post_id == ''
    assert post.error_message == ''


def test_str_shows_truncated_commentary():
    post = LinkedInPost.objects.create(commentary='x' * 80)
    assert str(post).startswith('x' * 40)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/models/test_linkedin_post.py -v`
Expected: FAIL with `ImportError: cannot import name 'LinkedInPost'`

- [ ] **Step 3: Write the model**

```python
# backend/content/models/linkedin_post.py
"""
Freeform LinkedIn posts created from /panel/linkedin.

Independent from BlogPost: these posts have their own text (commentary),
optional image, and a draft -> scheduled -> published lifecycle handled
by Huey tasks (mirroring the blog scheduling pattern).
"""

from django.db import models

LINKEDIN_COMMENTARY_MAX_LENGTH = 3000  # LinkedIn Posts API commentary limit


class LinkedInPost(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_PUBLISHED = 'published'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_FAILED, 'Failed'),
    ]

    commentary = models.TextField(
        max_length=LINKEDIN_COMMENTARY_MAX_LENGTH,
        help_text='Post text (LinkedIn commentary, max 3000 chars).',
    )
    image = models.ImageField(
        upload_to='linkedin_posts/', blank=True, null=True,
        help_text='Optional image attached to the post.',
    )
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default=STATUS_DRAFT,
    )
    scheduled_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When set (and status=scheduled), Huey publishes at this time.',
    )
    published_at = models.DateTimeField(null=True, blank=True)
    linkedin_post_id = models.CharField(
        max_length=255, blank=True, default='',
        help_text='LinkedIn URN returned on publish (x-restli-id).',
    )
    error_message = models.TextField(
        blank=True, default='',
        help_text='Last publish failure detail.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'LinkedIn post'
        verbose_name_plural = 'LinkedIn posts'

    def __str__(self):
        return self.commentary[:40]
```

In `backend/content/models/__init__.py`, add (following the existing import/export style of the file):

```python
from .linkedin_post import LinkedInPost
```

and append `'LinkedInPost'` to `__all__` if the file defines one.

In `backend/content/admin.py`, register following the file's existing style:

```python
from content.models import LinkedInPost


@admin.register(LinkedInPost)
class LinkedInPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'scheduled_at', 'published_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('commentary',)
```

- [ ] **Step 4: Generate migration**

Run: `source .venv/bin/activate && cd backend && python manage.py makemigrations content && python manage.py check`
Expected: one new migration `content/migrations/00XX_linkedinpost.py`, check passes.

- [ ] **Step 5: Run tests to verify pass**

Run: `cd backend && pytest content/tests/models/test_linkedin_post.py -v`
Expected: 2 PASS

- [ ] **Step 6: Commit**

```bash
git add backend/content/models/ backend/content/admin.py backend/content/migrations/ backend/content/tests/models/test_linkedin_post.py
git commit -m "FEAT: LinkedInPost model for freeform panel posts"
```

---

### Task 2: `publish_post_to_linkedin` service function

**Files:**
- Modify: `backend/content/services/linkedin_service.py` (append in the "Publishing" section, after `publish_blog_to_linkedin`)
- Test: `backend/content/tests/services/test_linkedin_post_service.py`

**Interfaces:**
- Consumes: existing `get_access_token()`, `get_member_urn()`, `_upload_image_to_linkedin(image_url)`, `_api_headers(access_token)`, `LINKEDIN_POSTS_URL`.
- Produces: `publish_post_to_linkedin(commentary: str, image_url: str = '') -> dict` returning `{'success': bool, 'post_id': str, 'message': str}`; raises `ValueError` when not connected / no URN / empty commentary.

- [ ] **Step 1: Write the failing tests**

```python
# backend/content/tests/services/test_linkedin_post_service.py
"""publish_post_to_linkedin: payload shape and error paths (all HTTP mocked)."""
from unittest.mock import MagicMock, patch

import pytest

from content.services.linkedin_service import publish_post_to_linkedin

MOD = 'content.services.linkedin_service'


def _ok_response(post_id='urn:li:share:123'):
    resp = MagicMock()
    resp.status_code = 201
    resp.headers = {'x-restli-id': post_id}
    return resp


@patch(f'{MOD}.requests.post')
@patch(f'{MOD}.get_member_urn', return_value='urn:li:person:abc')
@patch(f'{MOD}.get_access_token', return_value='tok')
def test_text_only_post_omits_content_key(mock_tok, mock_urn, mock_post):
    mock_post.return_value = _ok_response()
    result = publish_post_to_linkedin('Hola mundo')
    assert result['success'] is True
    assert result['post_id'] == 'urn:li:share:123'
    payload = mock_post.call_args.kwargs['json']
    assert payload['author'] == 'urn:li:person:abc'
    assert payload['commentary'] == 'Hola mundo'
    assert payload['lifecycleState'] == 'PUBLISHED'
    assert 'content' not in payload


@patch(f'{MOD}._upload_image_to_linkedin', return_value='urn:li:image:img1')
@patch(f'{MOD}.requests.post')
@patch(f'{MOD}.get_member_urn', return_value='urn:li:person:abc')
@patch(f'{MOD}.get_access_token', return_value='tok')
def test_image_post_attaches_media_urn(mock_tok, mock_urn, mock_post, mock_upload):
    mock_post.return_value = _ok_response()
    result = publish_post_to_linkedin('Con imagen', image_url='https://projectapp.co/media/x.jpg')
    assert result['success'] is True
    payload = mock_post.call_args.kwargs['json']
    assert payload['content'] == {'media': {'id': 'urn:li:image:img1'}}


@patch(f'{MOD}._upload_image_to_linkedin', return_value=None)
@patch(f'{MOD}.requests.post')
@patch(f'{MOD}.get_member_urn', return_value='urn:li:person:abc')
@patch(f'{MOD}.get_access_token', return_value='tok')
def test_failed_image_upload_publishes_text_only(mock_tok, mock_urn, mock_post, mock_upload):
    mock_post.return_value = _ok_response()
    result = publish_post_to_linkedin('Texto', image_url='https://projectapp.co/media/x.jpg')
    assert result['success'] is True
    assert 'content' not in mock_post.call_args.kwargs['json']


@patch(f'{MOD}.get_access_token', return_value=None)
def test_not_connected_raises(mock_tok):
    with pytest.raises(ValueError):
        publish_post_to_linkedin('Hola')


@patch(f'{MOD}.get_member_urn', return_value='urn:li:person:abc')
@patch(f'{MOD}.get_access_token', return_value='tok')
def test_empty_commentary_raises(mock_tok, mock_urn):
    with pytest.raises(ValueError):
        publish_post_to_linkedin('')


@patch(f'{MOD}.requests.post')
@patch(f'{MOD}.get_member_urn', return_value='urn:li:person:abc')
@patch(f'{MOD}.get_access_token', return_value='tok')
def test_api_error_returns_failure_dict(mock_tok, mock_urn, mock_post):
    resp = MagicMock()
    resp.status_code = 422
    resp.text = 'UNPROCESSABLE_ENTITY'
    mock_post.return_value = resp
    result = publish_post_to_linkedin('Hola')
    assert result['success'] is False
    assert '422' in result['message']
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest content/tests/services/test_linkedin_post_service.py -v`
Expected: FAIL with `ImportError: cannot import name 'publish_post_to_linkedin'`

- [ ] **Step 3: Implement the service function**

Append to `backend/content/services/linkedin_service.py` right after `publish_blog_to_linkedin` (same section):

```python
def publish_post_to_linkedin(commentary: str, image_url: str = '') -> dict:
    """
    Publish a freeform post (text, optionally one image) to LinkedIn.

    Unlike publish_blog_to_linkedin there is no article preview: a
    text-only post sends no 'content' key; with an image the media URN
    from the Images API is attached as content.media.

    Returns dict with 'success', 'post_id' (LinkedIn URN) and 'message'.
    Raises ValueError if not connected or commentary is empty.
    """
    access_token = get_access_token()
    if not access_token:
        raise ValueError('LinkedIn not connected. Please authorize first.')

    member_urn = get_member_urn()
    if not member_urn:
        raise ValueError('Could not retrieve LinkedIn member URN.')

    if not commentary:
        raise ValueError('Commentary text is required for LinkedIn post.')

    image_urn = None
    if image_url:
        image_urn = _upload_image_to_linkedin(image_url)
        if not image_urn:
            logger.warning('Image upload failed, publishing text-only post.')

    commentary = commentary.replace('\\n', '\n')

    post_data = {
        'author': member_urn,
        'commentary': commentary,
        'visibility': 'PUBLIC',
        'distribution': {
            'feedDistribution': 'MAIN_FEED',
            'targetEntities': [],
            'thirdPartyDistributionChannels': [],
        },
        'lifecycleState': 'PUBLISHED',
        'isReshareDisabledByAuthor': False,
    }
    if image_urn:
        post_data['content'] = {'media': {'id': image_urn}}

    resp = requests.post(
        LINKEDIN_POSTS_URL,
        json=post_data,
        headers=_api_headers(access_token),
        timeout=15,
    )

    if resp.status_code in (200, 201):
        post_id = resp.headers.get('x-restli-id', '')
        logger.info('LinkedIn freeform post published: %s', post_id)
        return {
            'success': True,
            'post_id': post_id,
            'message': 'Post published to LinkedIn successfully.',
        }

    logger.error('LinkedIn freeform publish failed: %s %s', resp.status_code, resp.text)
    return {
        'success': False,
        'post_id': '',
        'message': f'LinkedIn API error ({resp.status_code}): {resp.text}',
    }
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd backend && pytest content/tests/services/test_linkedin_post_service.py -v`
Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/content/services/linkedin_service.py backend/content/tests/services/test_linkedin_post_service.py
git commit -m "FEAT: publish_post_to_linkedin service for freeform posts"
```

---

### Task 3: Serializer + CRUD views + URLs

**Files:**
- Create: `backend/content/serializers/linkedin_post.py`
- Modify: `backend/content/views/linkedin.py` (append CRUD views)
- Modify: `backend/content/urls.py` (new routes in the LinkedIn section)
- Test: `backend/content/tests/views/test_linkedin_post_views.py`

**Interfaces:**
- Consumes: `LinkedInPost` (Task 1).
- Produces:
  - `LinkedInPostSerializer` (ModelSerializer, fields: `id, commentary, image, status, scheduled_at, published_at, linkedin_post_id, error_message, created_at, updated_at`; read-only: `status, published_at, linkedin_post_id, error_message, created_at, updated_at`). Validation: `scheduled_at` must be in the future when provided.
  - Views: `list_linkedin_posts` (GET), `create_linkedin_post` (POST multipart/JSON), `update_linkedin_post` (PUT, 409 when published), `delete_linkedin_post` (DELETE).
  - URLs: `linkedin/posts/`, `linkedin/posts/create/`, `linkedin/posts/<int:post_id>/update/`, `linkedin/posts/<int:post_id>/delete/` (names: `list-linkedin-posts`, `create-linkedin-post`, `update-linkedin-post`, `delete-linkedin-post`).
  - Status/scheduling rule (in views, applied after serializer save): `scheduled_at` set → `status='scheduled'` + enqueue ETA via `schedule_linkedin_post_eta` (Task 4); `scheduled_at` cleared on a scheduled post → back to `draft`.

- [ ] **Step 1: Write the failing tests**

```python
# backend/content/tests/views/test_linkedin_post_views.py
"""CRUD views for freeform LinkedIn posts (session-auth admin API)."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from content.models import LinkedInPost

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client():
    user = get_user_model().objects.create_user(
        username='admin', password='x', is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_list_returns_posts_newest_first(admin_client):
    LinkedInPost.objects.create(commentary='uno')
    LinkedInPost.objects.create(commentary='dos')
    resp = admin_client.get('/api/linkedin/posts/')
    assert resp.status_code == 200
    assert [p['commentary'] for p in resp.data] == ['dos', 'uno']


def test_create_draft(admin_client):
    resp = admin_client.post('/api/linkedin/posts/create/', {'commentary': 'Hola'})
    assert resp.status_code == 201
    assert resp.data['status'] == 'draft'


@patch('content.views.linkedin.schedule_linkedin_post_eta')
def test_create_with_future_schedule_sets_scheduled(mock_eta, admin_client):
    eta = (timezone.now() + timedelta(hours=2)).isoformat()
    resp = admin_client.post(
        '/api/linkedin/posts/create/', {'commentary': 'Hola', 'scheduled_at': eta},
    )
    assert resp.status_code == 201
    assert resp.data['status'] == 'scheduled'
    mock_eta.assert_called_once()


def test_create_with_past_schedule_rejected(admin_client):
    eta = (timezone.now() - timedelta(hours=1)).isoformat()
    resp = admin_client.post(
        '/api/linkedin/posts/create/', {'commentary': 'Hola', 'scheduled_at': eta},
    )
    assert resp.status_code == 400


def test_update_published_post_conflict(admin_client):
    post = LinkedInPost.objects.create(
        commentary='ya salió', status=LinkedInPost.STATUS_PUBLISHED,
    )
    resp = admin_client.put(
        f'/api/linkedin/posts/{post.id}/update/', {'commentary': 'edit'},
    )
    assert resp.status_code == 409


def test_update_clearing_schedule_reverts_to_draft(admin_client):
    post = LinkedInPost.objects.create(
        commentary='prog', status=LinkedInPost.STATUS_SCHEDULED,
        scheduled_at=timezone.now() + timedelta(hours=1),
    )
    resp = admin_client.put(
        f'/api/linkedin/posts/{post.id}/update/',
        {'commentary': 'prog', 'scheduled_at': ''},
    )
    assert resp.status_code == 200
    assert resp.data['status'] == 'draft'


def test_delete_post(admin_client):
    post = LinkedInPost.objects.create(commentary='bye')
    resp = admin_client.delete(f'/api/linkedin/posts/{post.id}/delete/')
    assert resp.status_code == 204
    assert not LinkedInPost.objects.filter(pk=post.id).exists()


def test_requires_admin():
    resp = APIClient().get('/api/linkedin/posts/')
    assert resp.status_code in (401, 403)
```

Note: confirm the API prefix by checking how existing tests call `linkedin/status/` in `backend/content/tests/views/test_linkedin_views.py` — reuse the exact same prefix (adjust `/api/` if that file uses a different one, e.g. reverse() names).

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest content/tests/views/test_linkedin_post_views.py -v`
Expected: FAIL (404s — routes don't exist)

- [ ] **Step 3: Implement serializer**

```python
# backend/content/serializers/linkedin_post.py
"""Serializer for freeform LinkedIn posts."""
from django.utils import timezone
from rest_framework import serializers

from content.models import LinkedInPost


class LinkedInPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkedInPost
        fields = [
            'id', 'commentary', 'image', 'status', 'scheduled_at',
            'published_at', 'linkedin_post_id', 'error_message',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'status', 'published_at', 'linkedin_post_id',
            'error_message', 'created_at', 'updated_at',
        ]

    def validate_scheduled_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                'La fecha programada debe estar en el futuro.'
            )
        return value
```

If `backend/content/serializers/__init__.py` re-exports serializers, add `LinkedInPostSerializer` there following the existing style.

- [ ] **Step 4: Implement views + URLs**

Append to `backend/content/views/linkedin.py`:

```python
from content.models import LinkedInPost
from content.serializers.linkedin_post import LinkedInPostSerializer
from content.services.linkedin_post_service import schedule_linkedin_post_eta


def _apply_schedule_transition(post):
    """Sync status with scheduled_at after create/update and enqueue ETA."""
    if post.status == LinkedInPost.STATUS_PUBLISHED:
        return
    if post.scheduled_at:
        post.status = LinkedInPost.STATUS_SCHEDULED
        post.save(update_fields=['status', 'updated_at'])
        schedule_linkedin_post_eta(post)
    elif post.status == LinkedInPost.STATUS_SCHEDULED:
        post.status = LinkedInPost.STATUS_DRAFT
        post.save(update_fields=['status', 'updated_at'])


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_linkedin_posts(request):
    """List freeform LinkedIn posts, newest first."""
    posts = LinkedInPost.objects.all()
    return Response(LinkedInPostSerializer(posts, many=True).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_linkedin_post(request):
    """Create a freeform LinkedIn post (draft, or scheduled when scheduled_at set)."""
    serializer = LinkedInPostSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    post = serializer.save()
    _apply_schedule_transition(post)
    return Response(
        LinkedInPostSerializer(post).data, status=status.HTTP_201_CREATED,
    )


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_linkedin_post(request, post_id):
    """Update a draft/scheduled/failed post. Published posts are immutable."""
    post = LinkedInPost.objects.filter(pk=post_id).first()
    if not post:
        return Response({'error': 'Post no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    if post.status == LinkedInPost.STATUS_PUBLISHED:
        return Response(
            {'error': 'Un post ya publicado no se puede editar.'},
            status=status.HTTP_409_CONFLICT,
        )
    data = request.data.copy()
    if data.get('scheduled_at') == '':
        data['scheduled_at'] = None
    serializer = LinkedInPostSerializer(post, data=data, partial=True)
    serializer.is_valid(raise_exception=True)
    post = serializer.save()
    _apply_schedule_transition(post)
    return Response(LinkedInPostSerializer(post).data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_linkedin_post(request, post_id):
    """Delete a freeform LinkedIn post (local record only)."""
    post = LinkedInPost.objects.filter(pk=post_id).first()
    if not post:
        return Response({'error': 'Post no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    post.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
```

Create a minimal `backend/content/services/linkedin_post_service.py` stub now so imports resolve (full logic in Task 5):

```python
# backend/content/services/linkedin_post_service.py
"""Scheduling helpers for freeform LinkedIn posts (mirrors blog_service)."""
import logging

logger = logging.getLogger(__name__)


def schedule_linkedin_post_eta(post):
    """Enqueue the per-post ETA publish task (Huey)."""
    from content.tasks import publish_single_scheduled_linkedin_post
    publish_single_scheduled_linkedin_post.schedule(
        args=(post.id,), eta=post.scheduled_at,
    )
    logger.info(
        'Encolado publish_single_scheduled_linkedin_post para post %s a %s',
        post.id, post.scheduled_at,
    )
```

NOTE: this stub imports `publish_single_scheduled_linkedin_post` lazily; Task 5 defines it. For Task 3's tests the function is mocked (`@patch('content.views.linkedin.schedule_linkedin_post_eta')`), so tests pass before Task 5 exists.

In `backend/content/urls.py`, extend the imports from `content.views.linkedin` and add after the existing LinkedIn routes (`linkedin/status/`):

```python
    # Freeform LinkedIn posts (panel module)
    path('linkedin/posts/', list_linkedin_posts, name='list-linkedin-posts'),
    path('linkedin/posts/create/', create_linkedin_post, name='create-linkedin-post'),
    path('linkedin/posts/<int:post_id>/update/', update_linkedin_post, name='update-linkedin-post'),
    path('linkedin/posts/<int:post_id>/delete/', delete_linkedin_post, name='delete-linkedin-post'),
```

- [ ] **Step 5: Run tests to verify pass**

Run: `cd backend && pytest content/tests/views/test_linkedin_post_views.py -v`
Expected: 8 PASS

- [ ] **Step 6: Commit**

```bash
git add backend/content/serializers/ backend/content/views/linkedin.py backend/content/urls.py backend/content/services/linkedin_post_service.py backend/content/tests/views/test_linkedin_post_views.py
git commit -m "FEAT: LinkedIn posts CRUD API for panel module"
```

---

### Task 4: Publish-now endpoint with atomic guard

**Files:**
- Modify: `backend/content/views/linkedin.py`
- Modify: `backend/content/services/linkedin_post_service.py`
- Modify: `backend/content/urls.py`
- Test: `backend/content/tests/views/test_linkedin_post_publish.py`

**Interfaces:**
- Consumes: `publish_post_to_linkedin` (Task 2), `LinkedInPost` (Task 1).
- Produces:
  - Service: `publish_linkedin_post_now(post) -> dict` — atomic claim (`exclude(status='published').update(status='published')`; 0 rows → `{'success': False, 'message': 'already published', 'already': True}`), builds absolute image URL (`https://projectapp.co{post.image.url}` when `post.image`), calls `publish_post_to_linkedin`; on success stamps `linkedin_post_id` + `published_at`; on failure reverts `status='failed'` + `error_message`.
  - View: `publish_linkedin_post` (POST) → 200 on success, 409 when already published, 502 on LinkedIn API failure, 400 on `ValueError` (not connected).
  - URL: `linkedin/posts/<int:post_id>/publish/` (name `publish-linkedin-post`).

- [ ] **Step 1: Write the failing tests**

```python
# backend/content/tests/views/test_linkedin_post_publish.py
"""Publish-now endpoint: success, double-publish guard, failure persistence."""
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from content.models import LinkedInPost

pytestmark = pytest.mark.django_db

SVC = 'content.services.linkedin_post_service.publish_post_to_linkedin'


@pytest.fixture
def admin_client():
    user = get_user_model().objects.create_user(
        username='admin', password='x', is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@patch(SVC, return_value={'success': True, 'post_id': 'urn:li:share:9', 'message': 'ok'})
def test_publish_success_stamps_fields(mock_pub, admin_client):
    post = LinkedInPost.objects.create(commentary='Hola')
    resp = admin_client.post(f'/api/linkedin/posts/{post.id}/publish/')
    assert resp.status_code == 200
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_PUBLISHED
    assert post.linkedin_post_id == 'urn:li:share:9'
    assert post.published_at is not None


@patch(SVC)
def test_already_published_returns_409_and_skips_api(mock_pub, admin_client):
    post = LinkedInPost.objects.create(
        commentary='Hola', status=LinkedInPost.STATUS_PUBLISHED,
    )
    resp = admin_client.post(f'/api/linkedin/posts/{post.id}/publish/')
    assert resp.status_code == 409
    mock_pub.assert_not_called()


@patch(SVC, return_value={'success': False, 'post_id': '', 'message': 'LinkedIn API error (500): boom'})
def test_api_failure_sets_failed_status(mock_pub, admin_client):
    post = LinkedInPost.objects.create(commentary='Hola')
    resp = admin_client.post(f'/api/linkedin/posts/{post.id}/publish/')
    assert resp.status_code == 502
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_FAILED
    assert 'boom' in post.error_message


@patch(SVC, side_effect=ValueError('LinkedIn not connected. Please authorize first.'))
def test_not_connected_returns_400_and_reverts(mock_pub, admin_client):
    post = LinkedInPost.objects.create(commentary='Hola')
    resp = admin_client.post(f'/api/linkedin/posts/{post.id}/publish/')
    assert resp.status_code == 400
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_FAILED


@patch(SVC, return_value={'success': True, 'post_id': 'urn:li:share:9', 'message': 'ok'})
def test_failed_post_can_be_retried(mock_pub, admin_client):
    post = LinkedInPost.objects.create(
        commentary='Hola', status=LinkedInPost.STATUS_FAILED, error_message='old',
    )
    resp = admin_client.post(f'/api/linkedin/posts/{post.id}/publish/')
    assert resp.status_code == 200
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_PUBLISHED
    assert post.error_message == ''
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest content/tests/views/test_linkedin_post_publish.py -v`
Expected: FAIL (404 — route missing)

- [ ] **Step 3: Implement service + view + URL**

Extend `backend/content/services/linkedin_post_service.py`:

```python
from django.utils import timezone

from content.services.linkedin_service import publish_post_to_linkedin

LINKEDIN_MEDIA_BASE = 'https://projectapp.co'


def publish_linkedin_post_now(post) -> dict:
    """
    Publish a freeform post with an atomic double-publish guard.

    Claims the post by flipping status to 'published' first (0 rows updated
    means someone else already published it); on API failure reverts to
    'failed' and persists the error message.
    """
    from content.models import LinkedInPost

    claimed = LinkedInPost.objects.filter(pk=post.id).exclude(
        status=LinkedInPost.STATUS_PUBLISHED,
    ).update(status=LinkedInPost.STATUS_PUBLISHED)
    if not claimed:
        return {'success': False, 'already': True,
                'message': 'Este post ya fue publicado en LinkedIn.'}

    image_url = ''
    if post.image:
        image_url = f'{LINKEDIN_MEDIA_BASE}{post.image.url}'

    try:
        result = publish_post_to_linkedin(post.commentary, image_url=image_url)
    except ValueError as exc:
        LinkedInPost.objects.filter(pk=post.id).update(
            status=LinkedInPost.STATUS_FAILED, error_message=str(exc),
        )
        return {'success': False, 'not_connected': True, 'message': str(exc)}

    if result['success']:
        LinkedInPost.objects.filter(pk=post.id).update(
            status=LinkedInPost.STATUS_PUBLISHED,
            linkedin_post_id=result['post_id'],
            published_at=timezone.now(),
            error_message='',
        )
    else:
        LinkedInPost.objects.filter(pk=post.id).update(
            status=LinkedInPost.STATUS_FAILED,
            error_message=result['message'],
        )
    return result
```

Append the view to `backend/content/views/linkedin.py` (import `publish_linkedin_post_now` next to `schedule_linkedin_post_eta`):

```python
@api_view(['POST'])
@permission_classes([IsAdminUser])
def publish_linkedin_post(request, post_id):
    """Publish a freeform LinkedIn post immediately."""
    post = LinkedInPost.objects.filter(pk=post_id).first()
    if not post:
        return Response({'error': 'Post no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    result = publish_linkedin_post_now(post)

    if result.get('already'):
        return Response({'error': result['message']}, status=status.HTTP_409_CONFLICT)
    if result.get('not_connected'):
        return Response({'error': result['message']}, status=status.HTTP_400_BAD_REQUEST)

    post.refresh_from_db()
    payload = LinkedInPostSerializer(post).data
    payload['message'] = result['message']
    return Response(
        payload,
        status=status.HTTP_200_OK if result['success'] else status.HTTP_502_BAD_GATEWAY,
    )
```

URL in `backend/content/urls.py` (same block as Task 3):

```python
    path('linkedin/posts/<int:post_id>/publish/', publish_linkedin_post, name='publish-linkedin-post'),
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd backend && pytest content/tests/views/test_linkedin_post_publish.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/content/views/linkedin.py backend/content/services/linkedin_post_service.py backend/content/urls.py backend/content/tests/views/test_linkedin_post_publish.py
git commit -m "FEAT: publish-now endpoint with double-publish guard"
```

---

### Task 5: Huey scheduling tasks (ETA + sweep)

**Files:**
- Modify: `backend/content/tasks.py` (append after `publish_scheduled_blog_posts`)
- Test: `backend/content/tests/tasks/test_linkedin_post_publish_guards.py`

**Interfaces:**
- Consumes: `publish_linkedin_post_now(post)` (Task 4), `LinkedInPost` (Task 1).
- Produces: `publish_single_scheduled_linkedin_post(post_id)` (`@task()`) and `publish_scheduled_linkedin_posts()` (`@periodic_task(crontab(minute='*'))`). Both are re-entrant; `publish_linkedin_post_now`'s atomic claim is the double-publish guard.

- [ ] **Step 1: Write the failing tests** (mirror `test_blog_publish_guards.py` conventions: `call_local`, `freeze_time`)

```python
# backend/content/tests/tasks/test_linkedin_post_publish_guards.py
"""Guards on scheduled LinkedIn-post publishing (mirrors blog guards).

- L1: ETA task skips when scheduled_at is still in the future (reschedule race).
- L2: task is a no-op when the post was already published (atomic claim).
- L3: periodic sweep publishes due scheduled posts and skips drafts.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from content.models import LinkedInPost

pytestmark = pytest.mark.django_db

SVC = 'content.services.linkedin_post_service.publish_post_to_linkedin'


def _run_single(post_id):
    import content.tasks as tasks_module
    tasks_module.publish_single_scheduled_linkedin_post.call_local(post_id)


def _run_periodic():
    import content.tasks as tasks_module
    tasks_module.publish_scheduled_linkedin_posts.call_local()


@patch(SVC)
def test_eta_task_skips_future_schedule(mock_pub):
    post = LinkedInPost.objects.create(
        commentary='pronto', status=LinkedInPost.STATUS_SCHEDULED,
        scheduled_at=timezone.now() + timedelta(hours=3),
    )
    _run_single(post.id)
    mock_pub.assert_not_called()
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_SCHEDULED


@patch(SVC)
def test_eta_task_noop_when_already_published(mock_pub):
    post = LinkedInPost.objects.create(
        commentary='ya', status=LinkedInPost.STATUS_PUBLISHED,
        scheduled_at=timezone.now() - timedelta(minutes=5),
    )
    _run_single(post.id)
    mock_pub.assert_not_called()


@patch(SVC, return_value={'success': True, 'post_id': 'urn:li:share:7', 'message': 'ok'})
def test_eta_task_publishes_due_post(mock_pub):
    post = LinkedInPost.objects.create(
        commentary='ahora', status=LinkedInPost.STATUS_SCHEDULED,
        scheduled_at=timezone.now() - timedelta(minutes=1),
    )
    _run_single(post.id)
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_PUBLISHED
    assert post.linkedin_post_id == 'urn:li:share:7'


@patch(SVC, return_value={'success': True, 'post_id': 'urn:li:share:8', 'message': 'ok'})
def test_sweep_publishes_due_and_skips_drafts(mock_pub):
    due = LinkedInPost.objects.create(
        commentary='due', status=LinkedInPost.STATUS_SCHEDULED,
        scheduled_at=timezone.now() - timedelta(minutes=2),
    )
    draft = LinkedInPost.objects.create(commentary='draft')
    _run_periodic()
    due.refresh_from_db()
    draft.refresh_from_db()
    assert due.status == LinkedInPost.STATUS_PUBLISHED
    assert draft.status == LinkedInPost.STATUS_DRAFT
    assert mock_pub.call_count == 1


@patch(SVC, return_value={'success': False, 'post_id': '', 'message': 'err 500'})
def test_failed_publish_marks_failed_and_sweep_does_not_retry(mock_pub):
    post = LinkedInPost.objects.create(
        commentary='falla', status=LinkedInPost.STATUS_SCHEDULED,
        scheduled_at=timezone.now() - timedelta(minutes=2),
    )
    _run_periodic()
    post.refresh_from_db()
    assert post.status == LinkedInPost.STATUS_FAILED
    _run_periodic()
    assert mock_pub.call_count == 1  # failed posts require manual retry
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest content/tests/tasks/test_linkedin_post_publish_guards.py -v`
Expected: FAIL with `AttributeError` (tasks don't exist)

- [ ] **Step 3: Implement the tasks**

Append to `backend/content/tasks.py` after `publish_scheduled_blog_posts` (same imports style — `@task()` / `@periodic_task` are already imported at the top):

```python
@task()
def publish_single_scheduled_linkedin_post(post_id):
    """
    Publish a single scheduled freeform LinkedIn post by id.

    Enqueued with eta=scheduled_at on create/update. Re-entrant: the
    atomic claim inside publish_linkedin_post_now prevents doubles.
    """
    from content.models import LinkedInPost
    from content.services.linkedin_post_service import publish_linkedin_post_now

    now = timezone.now()
    post = LinkedInPost.objects.filter(pk=post_id).first()
    if not post:
        logger.warning('[LI-Sched-ETA] post %s no existe', post_id)
        return
    if post.status != LinkedInPost.STATUS_SCHEDULED:
        logger.info('[LI-Sched-ETA] post %s status=%s, skip', post_id, post.status)
        return
    if not post.scheduled_at or post.scheduled_at > now:
        logger.info('[LI-Sched-ETA] post %s aún no es hora, skip', post_id)
        return

    result = publish_linkedin_post_now(post)
    logger.info('[LI-Sched-ETA] post %s → success=%s', post_id, result.get('success'))


@periodic_task(crontab(minute='*'))
def publish_scheduled_linkedin_posts():
    """
    Periodic safety-net (every minute) for scheduled LinkedIn posts whose
    time has passed (Huey down at ETA, migrated data, etc.).
    """
    from content.models import LinkedInPost
    from content.services.linkedin_post_service import publish_linkedin_post_now

    now = timezone.now()
    due = list(LinkedInPost.objects.filter(
        status=LinkedInPost.STATUS_SCHEDULED,
        scheduled_at__isnull=False,
        scheduled_at__lte=now,
    ))
    if not due:
        return

    logger.info('[LI-Sched-Sweep] %d post(s) listos para publicar', len(due))
    for post in due:
        try:
            result = publish_linkedin_post_now(post)
            logger.info('[LI-Sched-Sweep] post %s → success=%s', post.id, result.get('success'))
        except Exception:
            logger.exception('[LI-Sched-Sweep] error publicando post %s', post.id)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd backend && pytest content/tests/tasks/test_linkedin_post_publish_guards.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/content/tasks.py backend/content/tests/tasks/test_linkedin_post_publish_guards.py
git commit -m "FEAT: Huey ETA + sweep tasks for scheduled LinkedIn posts"
```

---

### Task 5b: Token expiry visibility + email warning

**Context:** LinkedIn does not issue refresh tokens to non-MDP apps, so the access token hard-expires every 60 days and the operator must reconnect manually. This task makes the expiry visible in the API and warns by email ~7 days before, so scheduled posts don't silently fail on an expired token.

**Files:**
- Modify: `backend/content/services/linkedin_service.py` (`get_connection_status` gains `expires_at`)
- Create: `backend/content/services/linkedin_expiry_service.py`
- Modify: `backend/content/tasks.py` (daily periodic task)
- Test: `backend/content/tests/services/test_linkedin_expiry_service.py`

**Interfaces:**
- Consumes: `LinkedInToken.load()` (existing singleton), `EmailMultiAlternatives` pattern from `accounting_card_reminder_service.py`.
- Produces:
  - `get_connection_status()` connected responses include `'expires_at': token.expires_at.isoformat() if token.expires_at else None` (add to BOTH connected return branches — cached-profile and API-fallback).
  - `check_linkedin_token_expiry() -> str` in `linkedin_expiry_service.py`: returns `'not_connected' | 'ok' | 'warned' | 'already_warned'`.
  - Task `warn_linkedin_token_expiry` — `@periodic_task(crontab(hour='9', minute='30'))`, thin wrapper calling the service.

**Warning logic (implement exactly):**
- Not connected or no `expires_at` → `'not_connected'`.
- More than 7 days remaining → `'ok'`.
- ≤7 days remaining: build cache key `f'linkedin_expiry_warned:{token.expires_at.date().isoformat()}'`. If already set → `'already_warned'`. Otherwise send the email, `cache.set(key, True, timeout=60*60*24*10)` and return `'warned'`. (Key includes the expiry date, so reconnecting re-arms the warning for the new token.)
- Recipients: `get_user_model().objects.filter(is_staff=True, is_active=True).exclude(email='')` emails; if empty, log a warning and skip (mirror the card-reminder service's no-recipients behavior).
- Email (plain text is enough, Spanish): subject `'LinkedIn: la conexión expira pronto'`, body stating the expiry date and that reconnection is done from `/panel/linkedin`. `from_email=settings.DEFAULT_FROM_EMAIL`.

- [ ] **Step 1: Write the failing tests**

```python
# backend/content/tests/services/test_linkedin_expiry_service.py
"""Expiry warning service: threshold, dedup via cache, recipients."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.utils import timezone

from content.models import LinkedInToken
from content.services.linkedin_expiry_service import check_linkedin_token_expiry

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def staff_user():
    return get_user_model().objects.create_user(
        username='admin', password='x', is_staff=True, email='admin@projectapp.co',
    )


def _token_expiring_in(days):
    token = LinkedInToken.load()
    token.access_token_encrypted = 'x'  # non-empty → "connected" for this check
    token.expires_at = timezone.now() + timedelta(days=days)
    token.save()
    return token


def test_not_connected_returns_early(staff_user):
    assert check_linkedin_token_expiry() == 'not_connected'
    assert len(mail.outbox) == 0


def test_far_from_expiry_is_ok(staff_user):
    _token_expiring_in(30)
    assert check_linkedin_token_expiry() == 'ok'
    assert len(mail.outbox) == 0


def test_warns_once_within_seven_days(staff_user):
    _token_expiring_in(5)
    assert check_linkedin_token_expiry() == 'warned'
    assert len(mail.outbox) == 1
    assert 'admin@projectapp.co' in mail.outbox[0].to
    assert check_linkedin_token_expiry() == 'already_warned'
    assert len(mail.outbox) == 1


def test_no_staff_recipients_skips_email():
    _token_expiring_in(5)
    result = check_linkedin_token_expiry()
    assert result in ('warned', 'already_warned')
    assert len(mail.outbox) == 0
```

NOTE: the "connected" check must not depend on Fernet decryption succeeding — in the service use `token.expires_at` presence plus `token.access_token_encrypted` truthiness, NOT `get_access_token()` (which would attempt a refresh/clear). If `LinkedInToken` requires a valid encrypted payload for other reasons, adjust the fixture to use `token.set_access_token('fake')` with a test `LINKEDIN_ENCRYPTION_KEY` — check how `backend/content/tests/services/test_linkedin_service.py` builds tokens and copy that.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest content/tests/services/test_linkedin_expiry_service.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement service + expose expires_at + task**

```python
# backend/content/services/linkedin_expiry_service.py
"""
Daily check that warns staff by email when the LinkedIn access token is
about to expire (<=7 days). LinkedIn issues no refresh tokens to non-MDP
apps, so the operator must reconnect manually every ~60 days; this makes
that proactive instead of discovering it via a failed publish.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)

WARN_THRESHOLD_DAYS = 7
_CACHE_TIMEOUT = 60 * 60 * 24 * 10  # 10 days — outlives the warning window


def check_linkedin_token_expiry() -> str:
    from content.models import LinkedInToken

    token = LinkedInToken.load()
    if not token.access_token_encrypted or not token.expires_at:
        return 'not_connected'

    remaining = token.expires_at - timezone.now()
    if remaining.days >= WARN_THRESHOLD_DAYS:
        return 'ok'

    cache_key = f'linkedin_expiry_warned:{token.expires_at.date().isoformat()}'
    if cache.get(cache_key):
        return 'already_warned'
    cache.set(cache_key, True, timeout=_CACHE_TIMEOUT)

    recipients = list(
        get_user_model().objects.filter(is_staff=True, is_active=True)
        .exclude(email='').values_list('email', flat=True)
    )
    if not recipients:
        logger.warning('LinkedIn token expiry warning due but no staff recipients.')
        return 'warned'

    expiry_str = timezone.localtime(token.expires_at).strftime('%d/%m/%Y')
    body = (
        f'La conexión con LinkedIn expira el {expiry_str}.\n\n'
        'Para renovarla entra a /panel/linkedin y usa "Reconectar" '
        '(toma menos de un minuto). Los posts programados después de esa '
        'fecha fallarán si el token no se renueva.'
    )
    email = EmailMultiAlternatives(
        subject='LinkedIn: la conexión expira pronto',
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    email.send(fail_silently=True)
    logger.info('LinkedIn expiry warning sent to %s', ', '.join(recipients))
    return 'warned'
```

In `get_connection_status` (`linkedin_service.py`): add `'expires_at': token.expires_at.isoformat() if token.expires_at else None,` to both connected return dicts.

Append to `backend/content/tasks.py`:

```python
@periodic_task(crontab(hour='9', minute='30'))
def warn_linkedin_token_expiry():
    """Daily: email staff when the LinkedIn token expires in <=7 days."""
    from content.services.linkedin_expiry_service import check_linkedin_token_expiry
    return check_linkedin_token_expiry()
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd backend && pytest content/tests/services/test_linkedin_expiry_service.py -v`
Expected: 4 PASS. Also re-run `pytest content/tests/views/test_linkedin_views.py -v` (get_connection_status changed — existing status tests must still pass; if any asserts exact dict keys, update it to include `expires_at`).

- [ ] **Step 5: Commit**

```bash
git add backend/content/services/ backend/content/tasks.py backend/content/tests/services/test_linkedin_expiry_service.py
git commit -m "FEAT: LinkedIn token expiry surfaced in status + daily email warning"
```

---

### Task 6: Frontend store `stores/linkedin.js` + OAuth action move

**Files:**
- Create: `frontend/stores/linkedin.js`
- Modify: `frontend/stores/blog.js` (remove `fetchLinkedInStatus`, `fetchLinkedInAuthUrl`, `linkedinCallback`; keep `publishToLinkedIn`)
- Modify: `frontend/pages/auth/linkedin/callback.vue` (use new store)
- Modify: `frontend/pages/panel/blog/[id]/edit.vue` (use new store for status/auth)
- Create: `frontend/test/stores/linkedin.test.js` (move the 3 OAuth describe blocks from `blog.test.js` + new CRUD tests)
- Modify: `frontend/test/stores/blog.test.js` (remove moved tests; keep `publishToLinkedIn` tests)

**Interfaces:**
- Consumes: `get_request`, `create_request`, `put_request`, `delete_request` from `~/stores/services/request_http`.
- Produces: `useLinkedInStore` with state `{ posts: [], connectionStatus: { connected: false } }` and actions (all return `{ success, data }` or `{ success: false, error }` like the blog store):
  - `fetchLinkedInStatus()` → GET `linkedin/status/` (also sets `this.connectionStatus`)
  - `fetchLinkedInAuthUrl()` → GET `linkedin/auth-url/`
  - `linkedinCallback(code, state)` → POST `linkedin/callback/`
  - `fetchPosts()` → GET `linkedin/posts/` (sets `this.posts`)
  - `createPost(formData)` → POST `linkedin/posts/create/`
  - `updatePost(id, formData)` → PUT `linkedin/posts/${id}/update/`
  - `deletePost(id)` → DELETE `linkedin/posts/${id}/delete/`
  - `publishPost(id)` → POST `linkedin/posts/${id}/publish/`

- [ ] **Step 1: Write the store**

```javascript
// frontend/stores/linkedin.js
import { defineStore } from 'pinia';
import {
  get_request,
  create_request,
  put_request,
  delete_request,
} from '~/stores/services/request_http';

/**
 * LinkedIn integration store: OAuth connection + freeform posts
 * managed from /panel/linkedin. Blog-post publishing stays in the
 * blog store (it is a BlogPost-scoped endpoint).
 */
export const useLinkedInStore = defineStore('linkedin', {
  state: () => ({
    posts: [],
    connectionStatus: { connected: false },
  }),

  getters: {},

  actions: {
    /**
     * fetchLinkedInStatus: Check LinkedIn connection status.
     */
    async fetchLinkedInStatus() {
      try {
        const response = await get_request('linkedin/status/');
        this.connectionStatus = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching LinkedIn status:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * fetchLinkedInAuthUrl: Get the LinkedIn OAuth authorization URL.
     */
    async fetchLinkedInAuthUrl() {
      try {
        const response = await get_request('linkedin/auth-url/');
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching LinkedIn auth URL:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * linkedinCallback: Exchange authorization code for token.
     */
    async linkedinCallback(code, state) {
      try {
        const response = await create_request('linkedin/callback/', { code, state });
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error exchanging LinkedIn code:', error);
        return { success: false, error: error.response?.data?.error };
      }
    },

    /**
     * fetchPosts: List freeform LinkedIn posts.
     */
    async fetchPosts() {
      try {
        const response = await get_request('linkedin/posts/');
        this.posts = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching LinkedIn posts:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * createPost: Create a draft/scheduled post. Accepts FormData
     * (commentary, optional image file, optional scheduled_at ISO).
     */
    async createPost(formData) {
      try {
        const response = await create_request('linkedin/posts/create/', formData);
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error creating LinkedIn post:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * updatePost: Update a non-published post.
     */
    async updatePost(id, formData) {
      try {
        const response = await put_request(`linkedin/posts/${id}/update/`, formData);
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error updating LinkedIn post:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * deletePost: Delete a post (local record only).
     */
    async deletePost(id) {
      try {
        await delete_request(`linkedin/posts/${id}/delete/`);
        return { success: true };
      } catch (error) {
        console.error('Error deleting LinkedIn post:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * publishPost: Publish a post to LinkedIn immediately.
     */
    async publishPost(id) {
      try {
        const response = await create_request(`linkedin/posts/${id}/publish/`, {});
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error publishing LinkedIn post:', error);
        return { success: false, error: error.response?.data?.error };
      }
    },
  },
});
```

- [ ] **Step 2: Move OAuth actions out of the blog store**

In `frontend/stores/blog.js`: delete the `fetchLinkedInStatus`, `fetchLinkedInAuthUrl` and `linkedinCallback` actions (keep `publishToLinkedIn` — it calls the BlogPost endpoint `blog/admin/${postId}/publish-linkedin/`). Keep the `// LinkedIn integration` comment above `publishToLinkedIn`.

In `frontend/pages/auth/linkedin/callback.vue`: replace `useBlogStore` with `useLinkedInStore`:

```javascript
import { useLinkedInStore } from '~/stores/linkedin';
// ...
const linkedInStore = useLinkedInStore();
// ...
const result = await linkedInStore.linkedinCallback(code, state);
```

In `frontend/pages/panel/blog/[id]/edit.vue`: add `import { useLinkedInStore } from '~/stores/linkedin';` and `const linkedInStore = useLinkedInStore();`, then change the two call sites:
- in `reloadPost()`: `blogStore.fetchLinkedInStatus()` → `linkedInStore.fetchLinkedInStatus()`
- in `connectLinkedIn()`: `blogStore.fetchLinkedInAuthUrl()` → `linkedInStore.fetchLinkedInAuthUrl()`
(`blogStore.publishToLinkedIn(...)` stays as is.)

- [ ] **Step 3: Write the store unit tests**

Create `frontend/test/stores/linkedin.test.js`. Copy the mocking setup style from `frontend/test/stores/blog.test.js` (vi.mock of `~/stores/services/request_http`, `setActivePinia(createPinia())` in `beforeEach`). Move the existing `describe('LinkedIn actions', …)` tests for `fetchLinkedInStatus` / `fetchLinkedInAuthUrl` / `linkedinCallback` from `blog.test.js` into this file (changing `useBlogStore` to `useLinkedInStore`), keep the warning comment about never storing real tokens, and add:

```javascript
describe('posts CRUD', () => {
  it('fetchPosts stores the list', async () => {
    get_request.mockResolvedValue({ data: [{ id: 1, commentary: 'Hola', status: 'draft' }] });
    const result = await store.fetchPosts();
    expect(get_request).toHaveBeenCalledWith('linkedin/posts/');
    expect(result.success).toBe(true);
    expect(store.posts).toHaveLength(1);
  });

  it('createPost posts to the create endpoint', async () => {
    create_request.mockResolvedValue({ data: { id: 2, status: 'draft' } });
    const result = await store.createPost({ commentary: 'Nuevo' });
    expect(create_request).toHaveBeenCalledWith('linkedin/posts/create/', { commentary: 'Nuevo' });
    expect(result.success).toBe(true);
  });

  it('updatePost puts to the update endpoint', async () => {
    put_request.mockResolvedValue({ data: { id: 2, status: 'draft' } });
    await store.updatePost(2, { commentary: 'Edit' });
    expect(put_request).toHaveBeenCalledWith('linkedin/posts/2/update/', { commentary: 'Edit' });
  });

  it('deletePost calls the delete endpoint', async () => {
    delete_request.mockResolvedValue({});
    const result = await store.deletePost(3);
    expect(delete_request).toHaveBeenCalledWith('linkedin/posts/3/delete/');
    expect(result.success).toBe(true);
  });

  it('publishPost surfaces backend error message', async () => {
    create_request.mockRejectedValue({ response: { data: { error: 'ya publicado' } } });
    const result = await store.publishPost(4);
    expect(result.success).toBe(false);
    expect(result.error).toBe('ya publicado');
  });
});
```

In `frontend/test/stores/blog.test.js`: remove the moved OAuth tests, keep the `publishToLinkedIn` tests.

- [ ] **Step 4: Run the two store test files**

Run: `npm --prefix frontend test -- test/stores/linkedin.test.js test/stores/blog.test.js`
Expected: all PASS (blog suite unchanged except removed tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/stores/linkedin.js frontend/stores/blog.js frontend/pages/auth/linkedin/callback.vue "frontend/pages/panel/blog/[id]/edit.vue" frontend/test/stores/linkedin.test.js frontend/test/stores/blog.test.js
git commit -m "FEAT: linkedin Pinia store; move OAuth actions out of blog store"
```

---

### Task 7: Sidebar rename + LinkedIn nav item + icon + view catalog

**Files:**
- Modify: `frontend/config/panelNav.js:56-64`
- Modify: `frontend/components/panel/SidebarIcon.vue` (locate by `grep -rn "name === 'blog'" frontend/components` — add a `linkedin` template)
- Modify: `frontend/config/viewCatalog.js` (new entry near the blog entries)
- Test: `frontend/test/components/PanelSidebar.test.js` (assert new label + item)

**Interfaces:**
- Consumes: nothing new.
- Produces: section `site` labeled `'ProjectApp content'` with item `{ label: 'LinkedIn', href: lp('/panel/linkedin'), icon: 'linkedin' }`.

- [ ] **Step 1: Update `panelNav.js`**

```javascript
    {
      id: 'site',
      label: 'ProjectApp content',
      items: [
        { label: 'Blog', href: lp('/panel/blog'), icon: 'blog' },
        { label: 'Blog calendar', href: lp('/panel/blog/calendar'), icon: 'calendar' },
        { label: 'Portfolio', href: lp('/panel/portfolio'), icon: 'portfolio' },
        { label: 'LinkedIn', href: lp('/panel/linkedin'), icon: 'linkedin' },
      ],
    },
```

- [ ] **Step 2: Add the `linkedin` icon**

In the SidebarIcon component, add alongside the other templates (official LinkedIn glyph simplified, stroke style consistent with siblings — check a sibling template first and match its svg attribute pattern):

```html
    <template v-else-if="name === 'linkedin'">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
        d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-4 0v7h-4v-7a6 6 0 016-6zM6 9H2v12h4zM4 6a2 2 0 100-4 2 2 0 000 4z" />
    </template>
```

- [ ] **Step 3: Add view catalog entry**

In `frontend/config/viewCatalog.js`, after the blog panel entries (~line 290), following the exact object shape of neighbors:

```javascript
      {
        label: 'LinkedIn del panel',
        url: '/panel/linkedin',
        file: 'frontend/pages/panel/linkedin/index.vue',
        reference: 'módulo de posts de LinkedIn (crear, programar, publicar)',
        audience: 'admin',
        viewType: 'list',
      },
```

- [ ] **Step 4: Update sidebar unit test**

In `frontend/test/components/PanelSidebar.test.js`, add to the existing render assertions:

```javascript
  it('shows the ProjectApp content section with the LinkedIn item', () => {
    const wrapper = mountSidebar(); // reuse the file's existing mount helper
    expect(wrapper.text()).toContain('ProjectApp content');
    expect(wrapper.text()).toContain('LinkedIn');
    expect(wrapper.text()).not.toContain('Website content');
  });
```

(Adapt the mount call to the helper actually used in that file.)

- [ ] **Step 5: Run tests + token check**

Run: `npm --prefix frontend test -- test/components/PanelSidebar.test.js`
Expected: PASS
Run: `node frontend/scripts/check-design-tokens.mjs --files frontend/config/panelNav.js`
Expected: no violations

- [ ] **Step 6: Commit**

```bash
git add frontend/config/panelNav.js frontend/config/viewCatalog.js frontend/components/panel/SidebarIcon.vue frontend/test/components/PanelSidebar.test.js
git commit -m "FEAT: rename sidebar section to ProjectApp content and add LinkedIn item"
```

---

### Task 8: `/panel/linkedin` page

**Files:**
- Create: `frontend/pages/panel/linkedin/index.vue`
- Test: `frontend/test/pages/panel-linkedin.test.js` (only if `frontend/test/pages/` exists with similar page tests — check first; otherwise page behavior is covered by the E2E in Task 9)

**Interfaces:**
- Consumes: `useLinkedInStore` (Task 6), `BaseModal`, `BaseButton`, `BaseInput` from `frontend/components/base/`, `useIsMobile` composable, `admin` layout.
- Produces: page at `/panel/linkedin`.

**Behavior contract (build exactly this):**

1. `definePageMeta({ layout: 'admin', middleware: 'panel-auth' })` — first check the middleware name used by `frontend/pages/panel/blog/index.vue` and copy it verbatim (it may be `auth-admin` or similar; also copy its `layout`).
2. On mount: `Promise.all([store.fetchLinkedInStatus(), store.fetchPosts()])`; register a `window.addEventListener('message', handler)` that, on `event.data?.type === 'linkedin-connected'`, sets the connection status (same pattern as blog edit); remove the listener `onUnmounted`.
3. **Connection card** (top): when disconnected → "LinkedIn no conectado" + `Conectar LinkedIn` button (`bg-[#0A66C2]` like blog edit) that calls `fetchLinkedInAuthUrl()` and `window.open(url, '_blank', 'width=600,height=700')`. When connected → "Conectado como **{{ profile_name }}**" + a smaller "Reconectar" text button doing the same. When `connectionStatus.expires_at` is present, show "La conexión expira el {{ date }}" (`toLocaleDateString()`); if it expires within 7 days, render that line with `text-danger-strong` and prepend "⚠".
4. **Posts list**: desktop = table (columns: Texto (truncated 80 chars), Estado (chip), Programado, Publicado, Acciones); mobile (`useIsMobile`, `v-if` — NOT CSS hidden) = stacked cards with the same data. Status chips: draft `bg-surface-muted text-text-muted`, scheduled `bg-warning-soft text-warning-strong`, published `bg-primary-soft text-text-brand`, failed `bg-danger-soft text-danger-strong` (verify these token names exist in the styleguide/tailwind config; substitute the project's closest semantic tokens if any is missing). Published rows show a link `https://www.linkedin.com/feed/update/{{ linkedin_post_id }}/` (target `_blank`). Failed rows show `error_message` truncated with `title` attr.
5. **Actions per row**: Editar (draft/scheduled/failed only), Publicar ahora (draft/scheduled/failed), Eliminar (all — with `useConfirmModal` if that composable is the project pattern, otherwise a BaseModal confirm).
6. **Create/edit modal** (`BaseModal`): textarea bound to `form.commentary` with live counter `{{ form.commentary.length }} / 3000` and `maxlength="3000"`; `<input type="file" accept="image/*">` (show current image thumbnail when editing); `<input type="datetime-local">` bound to `form.scheduledLocal`. Footer buttons: `Guardar` (creates/updates: builds `FormData` with `commentary`, `image` only when a new file was picked, `scheduled_at` = ISO string from `scheduledLocal` or `''` to clear) and, when editing an existing non-published post, `Publicar ahora`. On success: close modal, `fetchPosts()`, show a transient success message (`text-text-brand`, 5s timeout — same pattern as blog edit `linkedinMsg`).
7. All copy in Spanish (user-facing), all styling with semantic tokens + base components.

- [ ] **Step 1: Check page-test conventions**

Run: `ls frontend/test/pages/ 2>/dev/null | head`
If page test files exist, mirror one for mount + "renders connection card and list" smoke assertions. If not, skip unit tests for the page (E2E covers it).

- [ ] **Step 2: Build the page per the behavior contract above**

Reference implementations to copy patterns from (read them first):
- popup + postMessage: `frontend/pages/panel/blog/[id]/edit.vue` (`connectLinkedIn`, `handleLinkedInMessage`)
- admin list page skeleton + mobile cards: `frontend/pages/panel/documents/index.vue` or `frontend/pages/panel/blog/index.vue`
- modal form: any `BaseModal` usage in `frontend/components/panel/documents/`

- [ ] **Step 3: Token check + dev smoke**

Run: `node frontend/scripts/check-design-tokens.mjs --files frontend/pages/panel/linkedin/index.vue`
Expected: no violations

- [ ] **Step 4: Run page unit test (if created)**

Run: `npm --prefix frontend test -- test/pages/panel-linkedin.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/pages/panel/linkedin/ frontend/test/pages/ 2>/dev/null || git add frontend/pages/panel/linkedin/
git commit -m "FEAT: /panel/linkedin page — connection card, posts list, create/edit modal"
```

---

### Task 9: E2E spec + flow definitions

**Files:**
- Create: `frontend/e2e/admin/admin-linkedin-module.spec.js`
- Modify: `frontend/e2e/helpers/flow-tags.js` (add `ADMIN_LINKEDIN_MODULE` tag following the existing export style)
- Modify: `frontend/e2e/flow-definitions.json` (add flow entry `admin-linkedin-module` describing: list + connection card + create draft + publish-now happy path, API mocked)

**Interfaces:**
- Consumes: `test`/`expect` from `../helpers/test.js`, `mockApi` from `../helpers/api.js`, `setAuthLocalStorage` from `../helpers/auth.js` — exactly like `admin-blog-linkedin.spec.js`.

- [ ] **Step 1: Write the spec** (mirror `admin-blog-linkedin.spec.js` structure: `test.setTimeout(60_000)`, mocked `authCheck`, mock `linkedin/status/`, `linkedin/posts/` fixtures)

Cover:
1. Disconnected state renders "Conectar LinkedIn" button.
2. Connected state renders profile name.
3. Posts list renders a draft row with status chip "Borrador" (or the chip label chosen in Task 8 — keep them consistent).
4. Create modal: open, type commentary, save → POST to `linkedin/posts/create/` mocked → list refreshes showing the new post.
5. Publish now: click → POST `linkedin/posts/1/publish/` mocked success → chip flips to published label.
6. Publish failure: mocked 502 → inline error message visible.

Use role-based locators (`getByRole('button', { name: 'Conectar LinkedIn' })`), `domcontentloaded` waits, no `networkidle`.

- [ ] **Step 2: Run the spec**

Run: `npm --prefix frontend run e2e -- e2e/admin/admin-linkedin-module.spec.js`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/admin/admin-linkedin-module.spec.js frontend/e2e/helpers/flow-tags.js frontend/e2e/flow-definitions.json
git commit -m "TEST: E2E coverage for LinkedIn panel module"
```

---

### Task 10: Final audit + push + PR

- [ ] **Step 1: Run the `e2e-user-flows-check` skill** (required by CLAUDE.md for new user flows) and address CRITICAL gaps it reports.

- [ ] **Step 2: Focused regression slice** (≤3 test commands): re-run `content/tests/views/test_linkedin_views.py` (existing blog-LinkedIn views must still pass) and `test/stores/blog.test.js`.

- [ ] **Step 3: Update memory bank** — `tasks/active_context.md` (module shipped) and `docs/USER_FLOW_MAP.md` if it exists.

- [ ] **Step 4: Push + PR**

```bash
git push -u origin feat/04072026-linkedin-content-module
```

PR body: plain summary + test plan, no AI attribution. Report the PR URL as the final line: `PR URL: <url>`.

---

## Self-Review Notes

- Spec coverage: rename (T7), model (T1), service (T2), CRUD (T3), publish guard (T4), Huey mirror (T5), store + OAuth move (T6), page (T8), viewCatalog (T7), E2E + flows-check (T9/T10). ✔
- Type consistency: `schedule_linkedin_post_eta(post)` defined T3-stub, used T3 views; `publish_linkedin_post_now(post)` defined T4, consumed T4 view + T5 tasks; store action names match page contract (T6 ↔ T8). ✔
- Known checks left to the implementer on purpose (marked inline): exact API URL prefix in backend tests (Task 3 note), middleware/layout names for the page (Task 8.1), status-chip token names (Task 8.4), SidebarIcon file location (Task 7).
