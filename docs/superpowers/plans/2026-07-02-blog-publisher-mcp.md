# Blog Publisher MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Embed a remote MCP server in the Django backend so the owner's claude.ai account can create, schedule, edit, and inspect blog posts, with connector tokens managed from a new superuser-only `/panel/mcps` section.

**Architecture:** A minimal JSON-RPC 2.0 dispatcher (`content/mcp/protocol.py`) serves the MCP Streamable HTTP transport without SSE (plain JSON responses, WSGI-compatible) at `POST /api/mcp/blog/<token>/`. Six tools reuse the exact panel pipeline via logic extracted from `views/blog.py` into `services/blog_service.py`. A new `McpConnector` model stores hashed capability tokens generated/rotated from the panel.

**Tech Stack:** Django 5 + DRF (function-based `@api_view` views), pytest, Nuxt 3 + Pinia (Options API stores), Jest, Playwright.

**Spec:** `docs/superpowers/specs/2026-07-02-blog-publisher-mcp-design.md`

## Global Constraints

- Never run the full test suite. Max 20 tests per batch, max 3 test commands per cycle. Run only the slice named in each task.
- Backend test command prefix: `source .venv/bin/activate && cd backend && pytest ...` (run from repo root).
- Frontend unit tests: `npm --prefix frontend test -- path/to/file.test.js`.
- Do not modify existing migrations; add new ones.
- Commit messages: conventional prefix, no `Co-Authored-By` trailers, no AI attribution lines.
- Docs/comments/commits in English. User-facing UI strings in Spanish (panel copy follows accounting module style).
- DRF views stay function-based with `@api_view`. Business logic in services.
- Pinia stores: Options API shape `{ state, getters, actions }`, snake_case filename, `request_http.js` client (content/admin flow).
- Existing behavior of the blog panel flow must not change: `test_blog_views.py` is the regression net.

---

### Task 1: `McpConnector` model + seed migration

**Files:**
- Create: `backend/content/models/mcp_connector.py`
- Modify: `backend/content/models/__init__.py` (add import)
- Create: `backend/content/migrations/0128_mcpconnector.py` (via makemigrations — number may shift; use whatever makemigrations produces)
- Create: `backend/content/migrations/0129_seed_blog_mcp_connector.py` (manual data migration; renumber to follow the previous one)
- Test: `backend/content/tests/models/test_mcp_connector.py`

**Interfaces:**
- Produces: `McpConnector` model with fields `slug`, `name`, `description`, `token_hash`, `token_prefix`, `is_active`, `last_used_at`, `created_at`, `updated_at`; methods `generate_token() -> str`, `check_token(token: str) -> bool`, staticmethod `hash_token(token: str) -> str`. A `blog` connector row exists after migrations (inactive, empty token).

- [ ] **Step 1: Write the failing test**

```python
# backend/content/tests/models/test_mcp_connector.py
"""Tests for the McpConnector model (token lifecycle)."""
import pytest

from content.models import McpConnector


@pytest.mark.django_db
class TestMcpConnectorTokens:
    def _connector(self):
        connector, _ = McpConnector.objects.get_or_create(
            slug='blog',
            defaults={'name': 'Blog Publisher'},
        )
        return connector

    def test_blog_connector_is_seeded_inactive(self):
        connector = McpConnector.objects.get(slug='blog')
        assert connector.is_active is False
        assert connector.token_hash == ''

    def test_generate_token_returns_plaintext_and_stores_hash(self):
        connector = self._connector()
        token = connector.generate_token()
        connector.refresh_from_db()
        assert len(token) >= 40
        assert connector.token_hash != ''
        assert token not in connector.token_hash
        assert connector.token_prefix == token[:8]

    def test_check_token_accepts_current_token_only(self):
        connector = self._connector()
        token = connector.generate_token()
        assert connector.check_token(token) is True
        assert connector.check_token('wrong-token') is False
        assert connector.check_token('') is False

    def test_regenerating_invalidates_previous_token(self):
        connector = self._connector()
        old_token = connector.generate_token()
        new_token = connector.generate_token()
        assert connector.check_token(old_token) is False
        assert connector.check_token(new_token) is True

    def test_check_token_false_when_no_token_generated(self):
        connector = self._connector()
        connector.token_hash = ''
        assert connector.check_token('anything') is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/models/test_mcp_connector.py -v`
Expected: FAIL with `ImportError: cannot import name 'McpConnector'`

- [ ] **Step 3: Write the model**

```python
# backend/content/models/mcp_connector.py
import hashlib
import hmac
import secrets

from django.db import models


class McpConnector(models.Model):
    """
    A remote MCP connector exposed by this backend (e.g. the Blog Publisher).

    The token embedded in the connector URL is the credential (capability
    URL, webhook-secret style). Only its SHA-256 hash is stored; the
    plaintext is shown once at generation time in /panel/mcps.
    """

    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    token_hash = models.CharField(
        max_length=64, blank=True, default='',
        help_text='SHA-256 hex digest of the connector token. Plaintext is never stored.',
    )
    token_prefix = models.CharField(
        max_length=8, blank=True, default='',
        help_text='First 8 chars of the token, for masked display in the panel.',
    )
    is_active = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'MCP Connector'
        verbose_name_plural = 'MCP Connectors'

    def __str__(self):
        return self.name

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def generate_token(self):
        """Create a new token, persist only its hash, return the plaintext once."""
        token = secrets.token_urlsafe(36)
        self.token_hash = self.hash_token(token)
        self.token_prefix = token[:8]
        self.save(update_fields=['token_hash', 'token_prefix', 'updated_at'])
        return token

    def check_token(self, token):
        if not self.token_hash or not token:
            return False
        return hmac.compare_digest(self.token_hash, self.hash_token(token))
```

Add to `backend/content/models/__init__.py` (after the `LinkedInToken` import line):

```python
from .mcp_connector import McpConnector
```

- [ ] **Step 4: Create schema migration**

Run: `source .venv/bin/activate && cd backend && python manage.py makemigrations content --name mcpconnector`
Expected: creates `content/migrations/0128_mcpconnector.py` (number may differ — use what it generates).

- [ ] **Step 5: Write the seed data migration**

Create `backend/content/migrations/0129_seed_blog_mcp_connector.py` (replace `0128_mcpconnector` in dependencies with the actual filename from Step 4):

```python
from django.db import migrations


def seed_blog_connector(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.get_or_create(
        slug='blog',
        defaults={
            'name': 'Blog Publisher',
            'description': (
                'Permite a Claude (claude.ai) crear, programar, editar y '
                'consultar posts del blog directamente.'
            ),
            'is_active': False,
        },
    )


def unseed_blog_connector(apps, schema_editor):
    McpConnector = apps.get_model('content', 'McpConnector')
    McpConnector.objects.filter(slug='blog').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0128_mcpconnector'),
    ]
    operations = [
        migrations.RunPython(seed_blog_connector, unseed_blog_connector),
    ]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/models/test_mcp_connector.py -v`
Expected: 5 PASS

- [ ] **Step 7: Commit**

```bash
git add backend/content/models/ backend/content/migrations/ backend/content/tests/models/test_mcp_connector.py
git commit -m "feat: add McpConnector model with hashed token lifecycle"
```

---

### Task 2: Extract shared blog logic into `blog_service.py`

**Files:**
- Create: `backend/content/services/blog_service.py`
- Modify: `backend/content/views/blog.py` (delete moved code, rewire views)
- Test (regression, existing): `backend/content/tests/views/test_blog_views.py`, `backend/content/tests/tasks/test_blog_tasks.py`

**Interfaces:**
- Produces (all in `content.services.blog_service`):
  - `BASE_URL: str`, `BLOG_PUBLIC_BASE: str` (moved constants)
  - `auto_publish_blog_to_linkedin(post) -> None` (moved verbatim)
  - `enqueue_scheduled_publish_if_future(post) -> None` (moved; renamed from `_enqueue_scheduled_publish_if_future`)
  - `create_post_from_json(validated_data: dict) -> BlogPost`
  - `run_post_save_pipeline(post, was_published: bool = False) -> None`
  - `build_blog_json_template() -> dict`
  - `get_calendar_posts(start_dt, end_dt) -> list[dict]`
- Note: existing LinkedIn tests patch `content.services.linkedin_service.publish_blog_to_linkedin` (service layer), so moving these functions does not break patch targets. Verify with: `grep -rn "views.blog.auto_publish\|views.blog._enqueue" backend/content/tests/` → expect no hits.

- [ ] **Step 1: Write `blog_service.py`**

```python
# backend/content/services/blog_service.py
"""
Shared blog post logic used by the panel views (content.views.blog)
and the Blog Publisher MCP tools (content.mcp.tools).

Both entry points must go through the same pipeline so scheduled
publication (Huey), LinkedIn auto-post, and frontend rebuild never diverge.
"""
import copy as _copy
import logging

from django.utils import timezone as tz

from content.models import BlogPost
from content.services.frontend_build import schedule_rebuild_after_publish

logger = logging.getLogger(__name__)

BASE_URL = 'https://projectapp.co'
# Canonical public URL for posts (i18n strategy 'prefix': /blog/* only 301s here)
BLOG_PUBLIC_BASE = f'{BASE_URL}/es-co/blog'


def auto_publish_blog_to_linkedin(post):
    # (MOVED VERBATIM from content/views/blog.py — full body including all
    # logging, the internal `from content.services.linkedin_service import
    # publish_blog_to_linkedin`, and the try/except structure. Do not edit.)
    ...


def enqueue_scheduled_publish_if_future(post):
    # (MOVED VERBATIM from content/views/blog.py `_enqueue_scheduled_publish_if_future`,
    # only the leading underscore dropped from the name.)
    ...


def create_post_from_json(validated_data):
    """Create a BlogPost from BlogPostFromJSONSerializer.validated_data."""
    data = validated_data
    return BlogPost.objects.create(
        title_es=data['title_es'],
        title_en=data['title_en'],
        excerpt_es=data['excerpt_es'],
        excerpt_en=data['excerpt_en'],
        content_json_es=data['content_json_es'],
        content_json_en=data.get('content_json_en') or {},
        cover_image_url=data.get('cover_image_url', ''),
        sources=data.get('sources', []),
        category=data.get('category', ''),
        read_time_minutes=data.get('read_time_minutes', 0),
        is_featured=data.get('is_featured', False),
        is_published=data.get('is_published', False),
        published_at=data.get('published_at'),
        author=data.get('author', 'projectapp-team'),
        meta_title_es=data.get('meta_title_es', ''),
        meta_title_en=data.get('meta_title_en', ''),
        meta_description_es=data.get('meta_description_es', ''),
        meta_description_en=data.get('meta_description_en', ''),
        meta_keywords_es=data.get('meta_keywords_es', ''),
        meta_keywords_en=data.get('meta_keywords_en', ''),
        cover_image_credit=data.get('cover_image_credit', ''),
        cover_image_credit_url=data.get('cover_image_credit_url', ''),
        linkedin_summary_es=data.get('linkedin_summary_es', ''),
        linkedin_summary_en=data.get('linkedin_summary_en', ''),
    )


def run_post_save_pipeline(post, was_published=False):
    """
    Side effects shared by every create/update path.

    - LinkedIn auto-publish fires only on the transition to published
      (auto_publish_blog_to_linkedin also guards internally).
    - A draft with a future published_at gets a one-shot Huey task.
    - Any save touching a live post schedules a frontend rebuild.
    """
    if post.is_published and not was_published:
        auto_publish_blog_to_linkedin(post)
    enqueue_scheduled_publish_if_future(post)
    if post.is_published or was_published:
        schedule_rebuild_after_publish()


def build_blog_json_template():
    """Template payload for blog creation (panel download + MCP tool)."""
    from content.serializers.blog import AVAILABLE_CATEGORIES, BLOG_JSON_TEMPLATE
    return {
        'title_es': 'Título del artículo en español',
        'title_en': 'Article title in English',
        'excerpt_es': 'Resumen corto en español (1-2 oraciones).',
        'excerpt_en': 'Short summary in English (1-2 sentences).',
        'author': 'projectapp-team',
        'content_json_es': _copy.deepcopy(BLOG_JSON_TEMPLATE),
        'content_json_en': _copy.deepcopy(BLOG_JSON_TEMPLATE),
        'cover_image_url': '',
        'cover_image_credit': '',
        'cover_image_credit_url': '',
        'sources': [
            {'name': 'Source Name', 'url': 'https://example.com'},
        ],
        'category': 'technology',
        'read_time_minutes': 8,
        'is_featured': False,
        'is_published': False,
        'meta_title_es': '',
        'meta_title_en': '',
        'meta_description_es': '',
        'meta_description_en': '',
        'meta_keywords_es': '',
        'meta_keywords_en': '',
        'linkedin_summary_es': 'Resumen para LinkedIn en español (máx. ~1300 caracteres).',
        'linkedin_summary_en': 'LinkedIn summary in English (max ~1300 chars).',
        '_available_categories': AVAILABLE_CATEGORIES,
    }


def get_calendar_posts(start_dt, end_dt):
    """
    Posts with published_at in [start_dt, end_dt] plus drafts created in
    range, as calendar dicts. (MOVED from the body of views.blog.blog_calendar —
    everything after date parsing; keep the queryset logic and the dict
    shape identical, including 'calendar_status' and 'date'.)
    """
    published_qs = BlogPost.objects.filter(
        published_at__gte=start_dt,
        published_at__lte=end_dt,
    )
    draft_qs = BlogPost.objects.filter(
        is_published=False,
        published_at__isnull=True,
        created_at__gte=start_dt,
        created_at__lte=end_dt,
    )
    all_ids = set(published_qs.values_list('id', flat=True)) | set(
        draft_qs.values_list('id', flat=True)
    )
    posts = BlogPost.objects.filter(id__in=all_ids)

    data = []
    for p in posts:
        is_scheduled = (
            not p.is_published
            and p.published_at is not None
            and p.published_at > tz.now()
        )
        cal_status = 'published' if p.is_published else ('scheduled' if is_scheduled else 'draft')
        data.append({
            'id': p.id,
            'title_es': p.title_es,
            'title_en': p.title_en,
            'slug': p.slug,
            'category': p.category,
            'is_published': p.is_published,
            'published_at': p.published_at.isoformat() if p.published_at else None,
            'created_at': p.created_at.isoformat(),
            'calendar_status': cal_status,
            'date': (
                p.published_at.strftime('%Y-%m-%d') if p.published_at
                else p.created_at.strftime('%Y-%m-%d')
            ),
        })
    return data
```

The two `...` bodies above are literal moves — copy the exact function bodies from `backend/content/views/blog.py` lines 36-124 (current file), do not retype them.

- [ ] **Step 2: Rewire `views/blog.py`**

In `backend/content/views/blog.py`:

1. Delete the moved code: `BASE_URL`/`BLOG_PUBLIC_BASE` constants, `auto_publish_blog_to_linkedin`, `_enqueue_scheduled_publish_if_future`, and drop the now-unused `copy as _copy` import if nothing else uses it.
2. Add import:

```python
from content.services.blog_service import (
    BASE_URL,
    BLOG_PUBLIC_BASE,
    build_blog_json_template,
    create_post_from_json,
    get_calendar_posts,
    run_post_save_pipeline,
)
```

3. `create_blog_post`: replace the three side-effect lines (`auto_publish_blog_to_linkedin(post)`, `_enqueue_scheduled_publish_if_future(post)`, `if post.is_published: schedule_rebuild_after_publish()`) with `run_post_save_pipeline(post)`.
4. `update_blog_post`: replace the block from `if post.is_published and not was_published:` down to `schedule_rebuild_after_publish()` (keep the `[Blog] post updated` log line) with `run_post_save_pipeline(post, was_published=was_published)`. The `publish transition detected` log line moves into nothing — delete it (the service logs enough).
5. `create_blog_post_from_json`: replace the inline `BlogPost.objects.create(...)` with `post = create_post_from_json(serializer.validated_data)` and the three side-effect lines with `run_post_save_pipeline(post)`.
6. `get_blog_json_template`: body becomes `return Response(build_blog_json_template(), status=status.HTTP_200_OK)`.
7. `blog_calendar`: keep param parsing and the two 400 branches; replace everything from `published_qs = ...` to the end with:

```python
    data = get_calendar_posts(start_dt, end_dt)
    return Response(data, status=status.HTTP_200_OK)
```

8. `serve_sitemap_xml` keeps using `BASE_URL` (now imported). Remove the `from content.services.frontend_build import schedule_rebuild_after_publish` import if no view still calls it directly (the delete view does — keep it).

- [ ] **Step 3: Run the regression slice**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/views/test_blog_views.py -v -x`
Expected: all PASS (this suite covers create, create-from-json, update, template, calendar, LinkedIn transitions).

Run: `source .venv/bin/activate && cd backend && pytest content/tests/tasks/test_blog_tasks.py -v`
Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/content/services/blog_service.py backend/content/views/blog.py
git commit -m "refactor: extract shared blog publish logic into blog_service"
```

---

### Task 3: MCP JSON-RPC protocol dispatcher

**Files:**
- Create: `backend/content/mcp/__init__.py` (empty)
- Create: `backend/content/mcp/protocol.py`
- Test: `backend/content/tests/mcp/__init__.py` (empty), `backend/content/tests/mcp/test_protocol.py`

**Interfaces:**
- Produces (in `content.mcp.protocol`):
  - `handle_message(message: dict, tools: list[dict]) -> tuple[int, dict | None]` — returns `(http_status, jsonrpc_response_or_None)`; notifications return `(202, None)`.
  - `class ToolError(Exception)` — raised by tool handlers for business errors; becomes `result.isError = true`.
  - Tool registry entry shape consumed here and produced by Task 4: `{'name': str, 'description': str, 'input_schema': dict, 'handler': callable(dict) -> dict}`.

- [ ] **Step 1: Write the failing tests**

```python
# backend/content/tests/mcp/test_protocol.py
"""Tests for the minimal MCP JSON-RPC dispatcher."""
from content.mcp.protocol import ToolError, handle_message


def _echo_handler(arguments):
    return {'echo': arguments.get('value')}


def _failing_handler(arguments):
    raise ToolError('categoría inválida')


TOOLS = [
    {
        'name': 'echo',
        'description': 'Echo a value back.',
        'input_schema': {'type': 'object', 'properties': {'value': {'type': 'string'}}},
        'handler': _echo_handler,
    },
    {
        'name': 'always_fails',
        'description': 'Always raises a business error.',
        'input_schema': {'type': 'object', 'properties': {}},
        'handler': _failing_handler,
    },
]


def _rpc(method, params=None, msg_id=1):
    message = {'jsonrpc': '2.0', 'id': msg_id, 'method': method}
    if params is not None:
        message['params'] = params
    return message


class TestInitialize:
    def test_initialize_returns_capabilities_and_server_info(self):
        status, resp = handle_message(
            _rpc('initialize', {'protocolVersion': '2025-06-18'}), TOOLS,
        )
        assert status == 200
        assert resp['id'] == 1
        assert resp['result']['protocolVersion'] == '2025-06-18'
        assert resp['result']['capabilities'] == {'tools': {}}
        assert 'name' in resp['result']['serverInfo']

    def test_initialize_with_unknown_version_falls_back_to_supported(self):
        status, resp = handle_message(
            _rpc('initialize', {'protocolVersion': '1999-01-01'}), TOOLS,
        )
        assert status == 200
        assert resp['result']['protocolVersion'] == '2025-06-18'

    def test_initialized_notification_returns_202_no_body(self):
        status, resp = handle_message(
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'}, TOOLS,
        )
        assert status == 202
        assert resp is None


class TestToolsList:
    def test_lists_tools_with_schemas(self):
        status, resp = handle_message(_rpc('tools/list'), TOOLS)
        assert status == 200
        names = [t['name'] for t in resp['result']['tools']]
        assert names == ['echo', 'always_fails']
        assert resp['result']['tools'][0]['inputSchema']['type'] == 'object'


class TestToolsCall:
    def test_calls_handler_and_wraps_result_as_text_content(self):
        status, resp = handle_message(
            _rpc('tools/call', {'name': 'echo', 'arguments': {'value': 'hola'}}), TOOLS,
        )
        assert status == 200
        result = resp['result']
        assert result['isError'] is False
        assert result['content'][0]['type'] == 'text'
        assert 'hola' in result['content'][0]['text']

    def test_tool_error_becomes_is_error_result_not_protocol_error(self):
        status, resp = handle_message(
            _rpc('tools/call', {'name': 'always_fails', 'arguments': {}}), TOOLS,
        )
        assert status == 200
        assert resp['result']['isError'] is True
        assert 'categoría inválida' in resp['result']['content'][0]['text']

    def test_unknown_tool_returns_invalid_params_error(self):
        status, resp = handle_message(
            _rpc('tools/call', {'name': 'nope', 'arguments': {}}), TOOLS,
        )
        assert status == 200
        assert resp['error']['code'] == -32602


class TestProtocolErrors:
    def test_ping_returns_empty_result(self):
        status, resp = handle_message(_rpc('ping'), TOOLS)
        assert status == 200
        assert resp['result'] == {}

    def test_unknown_method_returns_method_not_found(self):
        status, resp = handle_message(_rpc('bogus/method'), TOOLS)
        assert status == 200
        assert resp['error']['code'] == -32601

    def test_non_dict_message_is_invalid_request(self):
        status, resp = handle_message(['not', 'a', 'dict'], TOOLS)
        assert status == 200
        assert resp['error']['code'] == -32600
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/mcp/test_protocol.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'content.mcp'`

- [ ] **Step 3: Implement `protocol.py`**

```python
# backend/content/mcp/protocol.py
"""
Minimal MCP (Model Context Protocol) JSON-RPC 2.0 dispatcher.

Implements the stateless subset of the Streamable HTTP transport that
claude.ai custom connectors need: initialize, notifications/*, tools/list,
tools/call, ping. Every response is plain JSON (the SSE mode of the
transport is optional per spec and deliberately unsupported — this must
run under gunicorn WSGI).
"""
import json
import logging

logger = logging.getLogger(__name__)

SUPPORTED_PROTOCOL_VERSIONS = ('2025-06-18', '2025-03-26')
DEFAULT_PROTOCOL_VERSION = '2025-06-18'
SERVER_INFO = {'name': 'projectapp-blog-mcp', 'version': '1.0.0'}

INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class ToolError(Exception):
    """Business/validation error inside a tool handler.

    Surfaces as result.isError=true with a readable message so the calling
    model can fix its arguments and retry.
    """


def _error(msg_id, code, message):
    return 200, {'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': code, 'message': message}}


def _result(msg_id, result):
    return 200, {'jsonrpc': '2.0', 'id': msg_id, 'result': result}


def _text_result(msg_id, payload, is_error=False):
    text = payload if isinstance(payload, str) else json.dumps(
        payload, ensure_ascii=False, default=str,
    )
    return _result(msg_id, {
        'content': [{'type': 'text', 'text': text}],
        'isError': is_error,
    })


def handle_message(message, tools):
    """
    Handle one JSON-RPC message. Returns (http_status, response_dict|None).
    Notifications (no 'id') return (202, None) per Streamable HTTP transport.
    """
    if not isinstance(message, dict):
        return _error(None, INVALID_REQUEST, 'Expected a single JSON-RPC request object.')

    method = message.get('method', '')
    msg_id = message.get('id')
    params = message.get('params') or {}

    if method.startswith('notifications/'):
        return 202, None

    if message.get('jsonrpc') != '2.0' or not method:
        return _error(msg_id, INVALID_REQUEST, 'Malformed JSON-RPC 2.0 request.')

    if method == 'initialize':
        requested = params.get('protocolVersion', '')
        version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION
        return _result(msg_id, {
            'protocolVersion': version,
            'capabilities': {'tools': {}},
            'serverInfo': SERVER_INFO,
        })

    if method == 'ping':
        return _result(msg_id, {})

    if method == 'tools/list':
        return _result(msg_id, {
            'tools': [
                {
                    'name': t['name'],
                    'description': t['description'],
                    'inputSchema': t['input_schema'],
                }
                for t in tools
            ],
        })

    if method == 'tools/call':
        name = params.get('name', '')
        arguments = params.get('arguments') or {}
        tool = next((t for t in tools if t['name'] == name), None)
        if tool is None:
            return _error(msg_id, INVALID_PARAMS, f'Unknown tool: {name}')
        try:
            payload = tool['handler'](arguments)
        except ToolError as exc:
            logger.info('[MCP] tool %s rejected: %s', name, exc)
            return _text_result(msg_id, str(exc), is_error=True)
        except Exception:
            logger.exception('[MCP] tool %s crashed', name)
            return _text_result(
                msg_id,
                'Error interno ejecutando la herramienta. Revisa los logs del servidor.',
                is_error=True,
            )
        logger.info('[MCP] tool %s executed ok', name)
        return _text_result(msg_id, payload)

    return _error(msg_id, METHOD_NOT_FOUND, f'Method not supported: {method}')
```

Also create empty `backend/content/mcp/__init__.py` and `backend/content/tests/mcp/__init__.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/mcp/test_protocol.py -v`
Expected: 11 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/content/mcp/ backend/content/tests/mcp/
git commit -m "feat: add minimal MCP JSON-RPC dispatcher (streamable HTTP, no SSE)"
```

---

### Task 4: Blog tool registry (6 tools)

**Files:**
- Create: `backend/content/mcp/tools.py`
- Test: `backend/content/tests/mcp/test_tools.py`

**Interfaces:**
- Consumes: `ToolError` from `content.mcp.protocol`; `create_post_from_json`, `run_post_save_pipeline`, `build_blog_json_template`, `get_calendar_posts`, `BLOG_PUBLIC_BASE` from `content.services.blog_service`; `BlogPostFromJSONSerializer`, `BlogPostCreateUpdateSerializer`, `BlogPostAdminListSerializer` from `content.serializers.blog`.
- Produces: `BLOG_TOOLS: list[dict]` — registry consumed by the endpoint view (Task 5) and by the panel connector list (Task 6).

- [ ] **Step 1: Write the failing tests**

```python
# backend/content/tests/mcp/test_tools.py
"""Tests for the Blog Publisher MCP tool handlers."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone as tz

from content.mcp.protocol import ToolError
from content.mcp.tools import BLOG_TOOLS
from content.models import BlogPost


def _tool(name):
    return next(t for t in BLOG_TOOLS if t['name'] == name)


VALID_POST = {
    'title_es': 'Cómo elegir tu stack',
    'title_en': 'How to choose your stack',
    'excerpt_es': 'Resumen corto.',
    'excerpt_en': 'Short summary.',
    'content_json_es': {
        'intro': 'Introducción.',
        'sections': [{'heading': 'Sección', 'content': 'Contenido.'}],
    },
}


class TestGetBlogTemplate:
    def test_returns_template_and_categories(self, db):
        result = _tool('get_blog_template')['handler']({})
        assert 'content_json_es' in result['template']
        assert any(c['slug'] == 'technology' for c in result['available_categories'])


@pytest.mark.django_db
class TestCreateBlogPost:
    def test_creates_draft_and_reports_status(self):
        result = _tool('create_blog_post')['handler'](dict(VALID_POST))
        assert result['status'] == 'draft'
        post = BlogPost.objects.get(pk=result['id'])
        assert post.is_published is False
        assert result['public_url'].endswith(f"/{post.slug}")

    def test_scheduled_create_enqueues_huey_task(self):
        future = (tz.now() + timedelta(days=2)).isoformat()
        args = dict(VALID_POST, is_published=False, published_at=future)
        with patch('content.tasks.publish_single_scheduled_blog') as mock_task:
            result = _tool('create_blog_post')['handler'](args)
        assert result['status'] == 'scheduled'
        assert mock_task.schedule.called

    def test_invalid_payload_raises_tool_error_with_field_names(self):
        with pytest.raises(ToolError) as exc:
            _tool('create_blog_post')['handler']({'title_es': 'solo esto'})
        assert 'title_en' in str(exc.value)


@pytest.mark.django_db
class TestUpdateBlogPost:
    def test_partial_update_changes_fields(self, draft_blog_post):
        result = _tool('update_blog_post')['handler']({
            'post_id': draft_blog_post.id,
            'title_es': 'Título corregido',
        })
        draft_blog_post.refresh_from_db()
        assert draft_blog_post.title_es == 'Título corregido'
        assert result['id'] == draft_blog_post.id

    def test_unknown_post_raises_tool_error(self):
        with pytest.raises(ToolError):
            _tool('update_blog_post')['handler']({'post_id': 99999, 'title_es': 'x'})


@pytest.mark.django_db
class TestDeleteBlogPost:
    def test_deletes_draft(self, draft_blog_post):
        result = _tool('delete_blog_post')['handler']({'post_id': draft_blog_post.id})
        assert result['deleted'] is True
        assert not BlogPost.objects.filter(pk=draft_blog_post.id).exists()

    def test_refuses_to_delete_published_post(self, blog_post):
        assert blog_post.is_published is True
        with pytest.raises(ToolError) as exc:
            _tool('delete_blog_post')['handler']({'post_id': blog_post.id})
        assert BlogPost.objects.filter(pk=blog_post.id).exists()
        assert 'publicado' in str(exc.value)


@pytest.mark.django_db
class TestListBlogPosts:
    def test_lists_with_status_and_pagination(self, blog_post, draft_blog_post):
        result = _tool('list_blog_posts')['handler']({'page': 1, 'page_size': 10})
        assert result['count'] == 2
        statuses = {p['id']: p['status'] for p in result['results']}
        assert statuses[blog_post.id] == 'published'
        assert statuses[draft_blog_post.id] == 'draft'


@pytest.mark.django_db
class TestGetBlogCalendar:
    def test_returns_posts_in_range(self, blog_post):
        today = tz.now().strftime('%Y-%m-%d')
        result = _tool('get_blog_calendar')['handler']({'start': today, 'end': today})
        assert any(p['id'] == blog_post.id for p in result['posts'])

    def test_invalid_dates_raise_tool_error(self):
        with pytest.raises(ToolError):
            _tool('get_blog_calendar')['handler']({'start': 'ayer', 'end': 'hoy'})
```

Note: `blog_post` (published, `published_at=now`) and `draft_blog_post` fixtures already exist in `backend/content/tests/conftest.py`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/mcp/test_tools.py -v`
Expected: FAIL with `ModuleNotFoundError`/`ImportError` for `content.mcp.tools`

- [ ] **Step 3: Implement `tools.py`**

```python
# backend/content/mcp/tools.py
"""
Tool registry for the Blog Publisher MCP.

Each entry: {'name', 'description', 'input_schema', 'handler'}.
Handlers receive the raw `arguments` dict from tools/call, return a
JSON-serializable dict, and raise ToolError for business errors.
They reuse the exact same serializers and service pipeline as the panel.
"""
import json
from datetime import datetime, time

from django.utils import timezone as tz
from django.utils.dateparse import parse_date

from content.mcp.protocol import ToolError
from content.models import BlogPost
from content.serializers.blog import (
    BlogPostAdminListSerializer,
    BlogPostCreateUpdateSerializer,
    BlogPostFromJSONSerializer,
)
from content.services import blog_service


def _post_status(post):
    if post.is_published:
        return 'published'
    if post.published_at and post.published_at > tz.now():
        return 'scheduled'
    return 'draft'


def _post_summary(post):
    return {
        'id': post.id,
        'slug': post.slug,
        'title_es': post.title_es,
        'status': _post_status(post),
        'published_at': post.published_at.isoformat() if post.published_at else None,
        'public_url': f'{blog_service.BLOG_PUBLIC_BASE}/{post.slug}',
    }


def _serializer_errors_to_message(errors):
    return 'JSON inválido para el blog: ' + json.dumps(errors, ensure_ascii=False, default=str)


def _get_post_or_error(post_id):
    try:
        return BlogPost.objects.get(pk=int(post_id))
    except (BlogPost.DoesNotExist, TypeError, ValueError):
        raise ToolError(f'No existe un blog post con id={post_id}.')


# ── Handlers ────────────────────────────────────────────────────────────────

def get_blog_template(arguments):
    template = blog_service.build_blog_json_template()
    categories = template.pop('_available_categories')
    return {
        'template': template,
        'available_categories': categories,
        'scheduling_notes': (
            'Para programar: is_published=false + published_at futuro (ISO 8601 '
            'con timezone, ej. 2026-07-10T09:00:00-05:00). El sistema publica '
            'automáticamente a esa hora, postea en LinkedIn si hay '
            'linkedin_summary, y reconstruye el sitio. Para publicar ya: '
            'is_published=true. Para borrador: is_published=false sin published_at.'
        ),
    }


def create_blog_post(arguments):
    serializer = BlogPostFromJSONSerializer(data=arguments)
    if not serializer.is_valid():
        raise ToolError(_serializer_errors_to_message(serializer.errors))
    post = blog_service.create_post_from_json(serializer.validated_data)
    blog_service.run_post_save_pipeline(post)
    return _post_summary(post)


def update_blog_post(arguments):
    args = dict(arguments)
    post = _get_post_or_error(args.pop('post_id', None))
    was_published = post.is_published
    serializer = BlogPostCreateUpdateSerializer(post, data=args, partial=True)
    if not serializer.is_valid():
        raise ToolError(_serializer_errors_to_message(serializer.errors))
    serializer.save()
    blog_service.run_post_save_pipeline(post, was_published=was_published)
    return _post_summary(post)


def delete_blog_post(arguments):
    post = _get_post_or_error(arguments.get('post_id'))
    if post.is_published:
        raise ToolError(
            'Este post está publicado. Despublícalo primero con update_blog_post '
            '(is_published=false) o elimínalo desde el panel.'
        )
    post_id = post.id
    post.delete()
    return {'deleted': True, 'id': post_id}


def list_blog_posts(arguments):
    page = max(1, int(arguments.get('page', 1) or 1))
    page_size = max(1, min(int(arguments.get('page_size', 15) or 15), 50))
    qs = BlogPost.objects.all()
    total = qs.count()
    start = (page - 1) * page_size
    rows = BlogPostAdminListSerializer(qs[start:start + page_size], many=True).data
    posts_by_id = {p.id: p for p in qs[start:start + page_size]}
    results = []
    for row in rows:
        post = posts_by_id[row['id']]
        results.append({**dict(row), 'status': _post_status(post)})
    return {'count': total, 'page': page, 'page_size': page_size, 'results': results}


def get_blog_calendar(arguments):
    start_date = parse_date(str(arguments.get('start', '')))
    end_date = parse_date(str(arguments.get('end', '')))
    if not start_date or not end_date:
        raise ToolError('Formato de fecha inválido: usa YYYY-MM-DD en start y end.')
    start_dt = tz.make_aware(datetime.combine(start_date, time.min))
    end_dt = tz.make_aware(datetime.combine(end_date, time.max))
    return {'posts': blog_service.get_calendar_posts(start_dt, end_dt)}


# ── Registry ────────────────────────────────────────────────────────────────

_POST_ID_PROP = {'post_id': {'type': 'integer', 'description': 'ID del blog post.'}}

BLOG_TOOLS = [
    {
        'name': 'get_blog_template',
        'description': (
            'Devuelve el template JSON bilingüe (ES/EN) para crear un blog post, '
            'las categorías disponibles y las reglas de programación. Llama esto '
            'antes de create_blog_post para conocer la estructura exacta.'
        ),
        'input_schema': {'type': 'object', 'properties': {}},
        'handler': get_blog_template,
    },
    {
        'name': 'create_blog_post',
        'description': (
            'Crea un blog post con el JSON completo (misma estructura que '
            'get_blog_template). Borrador: is_published=false. Publicar ya: '
            'is_published=true. Programar: is_published=false + published_at futuro.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'title_es': {'type': 'string'},
                'title_en': {'type': 'string'},
                'excerpt_es': {'type': 'string'},
                'excerpt_en': {'type': 'string'},
                'content_json_es': {'type': 'object'},
                'content_json_en': {'type': 'object'},
                'category': {'type': 'string'},
                'cover_image_url': {'type': 'string'},
                'sources': {'type': 'array', 'items': {'type': 'object'}},
                'read_time_minutes': {'type': 'integer'},
                'is_featured': {'type': 'boolean'},
                'is_published': {'type': 'boolean'},
                'published_at': {'type': 'string', 'description': 'ISO 8601 con timezone.'},
                'author': {'type': 'string'},
                'meta_title_es': {'type': 'string'},
                'meta_title_en': {'type': 'string'},
                'meta_description_es': {'type': 'string'},
                'meta_description_en': {'type': 'string'},
                'meta_keywords_es': {'type': 'string'},
                'meta_keywords_en': {'type': 'string'},
                'cover_image_credit': {'type': 'string'},
                'cover_image_credit_url': {'type': 'string'},
                'linkedin_summary_es': {'type': 'string'},
                'linkedin_summary_en': {'type': 'string'},
            },
            'required': ['title_es', 'title_en', 'excerpt_es', 'excerpt_en', 'content_json_es'],
        },
        'handler': create_blog_post,
    },
    {
        'name': 'update_blog_post',
        'description': (
            'Actualiza campos de un post existente (parcial). Acepta los mismos '
            'campos que create_blog_post más post_id. Para despublicar: '
            'is_published=false.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {**_POST_ID_PROP, 'title_es': {'type': 'string'}},
            'required': ['post_id'],
            'additionalProperties': True,
        },
        'handler': update_blog_post,
    },
    {
        'name': 'delete_blog_post',
        'description': (
            'Elimina un post NO publicado. Los posts publicados no se pueden '
            'borrar por MCP (guardrail SEO): despublícalos primero o usa el panel.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': _POST_ID_PROP,
            'required': ['post_id'],
        },
        'handler': delete_blog_post,
    },
    {
        'name': 'list_blog_posts',
        'description': 'Lista todos los posts (publicados, programados y borradores) con paginación.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'page': {'type': 'integer', 'default': 1},
                'page_size': {'type': 'integer', 'default': 15, 'maximum': 50},
            },
        },
        'handler': list_blog_posts,
    },
    {
        'name': 'get_blog_calendar',
        'description': (
            'Posts con published_at en un rango de fechas más borradores creados '
            'en el rango. Úsalo para revisar qué hay agendado antes de programar.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'start': {'type': 'string', 'description': 'YYYY-MM-DD'},
                'end': {'type': 'string', 'description': 'YYYY-MM-DD'},
            },
            'required': ['start', 'end'],
        },
        'handler': get_blog_calendar,
    },
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/mcp/test_tools.py -v`
Expected: 12 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/content/mcp/tools.py backend/content/tests/mcp/test_tools.py
git commit -m "feat: add blog publisher MCP tool registry (6 tools)"
```

---

### Task 5: MCP HTTP endpoint + throttle + URL

**Files:**
- Create: `backend/content/views/mcp_blog.py`
- Modify: `backend/projectapp/settings.py:341-346` (add throttle rates to `REST_FRAMEWORK`)
- Modify: `backend/content/urls.py` (import + route)
- Test: `backend/content/tests/views/test_mcp_blog.py`

**Interfaces:**
- Consumes: `handle_message` (Task 3), `BLOG_TOOLS` (Task 4), `McpConnector` (Task 1).
- Produces: route `POST /api/mcp/blog/<token>/` (name `mcp-blog-endpoint`). Panel management views land in this same file in Task 6.

- [ ] **Step 1: Write the failing tests**

```python
# backend/content/tests/views/test_mcp_blog.py
"""Tests for the Blog Publisher MCP HTTP endpoint."""
import pytest

from content.models import BlogPost, McpConnector


@pytest.fixture
def blog_connector(db):
    connector, _ = McpConnector.objects.get_or_create(
        slug='blog', defaults={'name': 'Blog Publisher'},
    )
    connector.is_active = True
    connector.save(update_fields=['is_active'])
    token = connector.generate_token()
    return connector, token


def _url(token):
    return f'/api/mcp/blog/{token}/'


def _rpc(method, params=None, msg_id=1):
    message = {'jsonrpc': '2.0', 'id': msg_id, 'method': method}
    if params is not None:
        message['params'] = params
    return message


VALID_POST = {
    'title_es': 'Post por MCP',
    'title_en': 'Post via MCP',
    'excerpt_es': 'Resumen.',
    'excerpt_en': 'Summary.',
    'content_json_es': {
        'intro': 'Intro.',
        'sections': [{'heading': 'Uno', 'content': 'Texto.'}],
    },
}


@pytest.mark.django_db
class TestMcpEndpointAuth:
    def test_wrong_token_is_404(self, api_client, blog_connector):
        response = api_client.post(_url('bad-token'), _rpc('ping'), format='json')
        assert response.status_code == 404

    def test_inactive_connector_is_404_even_with_valid_token(self, api_client, blog_connector):
        connector, token = blog_connector
        connector.is_active = False
        connector.save(update_fields=['is_active'])
        response = api_client.post(_url(token), _rpc('ping'), format='json')
        assert response.status_code == 404

    def test_get_is_not_allowed(self, api_client, blog_connector):
        _, token = blog_connector
        response = api_client.get(_url(token))
        assert response.status_code == 405


@pytest.mark.django_db
class TestMcpEndpointFlow:
    def test_initialize_handshake(self, api_client, blog_connector):
        _, token = blog_connector
        response = api_client.post(
            _url(token),
            _rpc('initialize', {'protocolVersion': '2025-06-18'}),
            format='json',
        )
        assert response.status_code == 200
        assert response.data['result']['serverInfo']['name'] == 'projectapp-blog-mcp'

    def test_initialized_notification_returns_202(self, api_client, blog_connector):
        _, token = blog_connector
        response = api_client.post(
            _url(token),
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            format='json',
        )
        assert response.status_code == 202

    def test_tools_list_exposes_six_tools(self, api_client, blog_connector):
        _, token = blog_connector
        response = api_client.post(_url(token), _rpc('tools/list'), format='json')
        names = [t['name'] for t in response.data['result']['tools']]
        assert names == [
            'get_blog_template', 'create_blog_post', 'update_blog_post',
            'delete_blog_post', 'list_blog_posts', 'get_blog_calendar',
        ]

    def test_tools_call_creates_post_and_touches_last_used(self, api_client, blog_connector):
        connector, token = blog_connector
        assert connector.last_used_at is None
        response = api_client.post(
            _url(token),
            _rpc('tools/call', {'name': 'create_blog_post', 'arguments': VALID_POST}),
            format='json',
        )
        assert response.status_code == 200
        assert response.data['result']['isError'] is False
        assert BlogPost.objects.filter(title_es='Post por MCP').exists()
        connector.refresh_from_db()
        assert connector.last_used_at is not None

    def test_validation_error_is_readable_tool_error(self, api_client, blog_connector):
        _, token = blog_connector
        response = api_client.post(
            _url(token),
            _rpc('tools/call', {'name': 'create_blog_post', 'arguments': {'title_es': 'x'}}),
            format='json',
        )
        assert response.status_code == 200
        assert response.data['result']['isError'] is True
        assert 'title_en' in response.data['result']['content'][0]['text']
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/views/test_mcp_blog.py -v`
Expected: FAIL — all 404 (route does not exist yet; the auth tests may pass vacuously, the flow tests must fail)

- [ ] **Step 3: Implement the endpoint view**

```python
# backend/content/views/mcp_blog.py
"""
Blog Publisher MCP: public JSON-RPC endpoint (token-authenticated) and,
from Task 6, the panel management endpoints for /panel/mcps.
"""
import logging

from django.http import Http404
from django.utils import timezone as tz
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from content.mcp.protocol import handle_message
from content.mcp.tools import BLOG_TOOLS
from content.models import McpConnector

logger = logging.getLogger(__name__)

LAST_USED_TOUCH_SECONDS = 60


class McpEndpointThrottle(AnonRateThrottle):
    scope = 'mcp'


def _touch_last_used(connector):
    now = tz.now()
    if connector.last_used_at and (now - connector.last_used_at).total_seconds() < LAST_USED_TOUCH_SECONDS:
        return
    McpConnector.objects.filter(pk=connector.pk).update(last_used_at=now)


@api_view(['POST'])
@authentication_classes([])  # token in URL is the credential; no session ⇒ no CSRF
@permission_classes([AllowAny])
@throttle_classes([McpEndpointThrottle])
def mcp_blog_endpoint(request, token):
    """
    MCP Streamable HTTP endpoint for the Blog Publisher connector.
    Plain-JSON responses only (no SSE) — WSGI-compatible by design.
    """
    connector = McpConnector.objects.filter(slug='blog', is_active=True).first()
    if connector is None or not connector.check_token(token):
        raise Http404

    message = request.data
    http_status, payload = handle_message(message, BLOG_TOOLS)

    if isinstance(message, dict) and message.get('method') == 'tools/call':
        _touch_last_used(connector)

    if payload is None:
        return Response(status=http_status)
    return Response(payload, status=http_status)
```

- [ ] **Step 4: Add throttle rate to settings**

In `backend/projectapp/settings.py`, extend the existing `REST_FRAMEWORK` dict (line ~341):

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'mcp': '60/min',
    },
}
```

- [ ] **Step 5: Add the URL**

In `backend/content/urls.py`, add to the imports block:

```python
from content.views.mcp_blog import mcp_blog_endpoint
```

and add the route next to the blog admin routes:

```python
    # MCP (Model Context Protocol) — token-authenticated remote connectors
    path('mcp/blog/<str:token>/', mcp_blog_endpoint, name='mcp-blog-endpoint'),
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/views/test_mcp_blog.py -v`
Expected: 8 PASS

- [ ] **Step 7: Commit**

```bash
git add backend/content/views/mcp_blog.py backend/content/urls.py backend/projectapp/settings.py backend/content/tests/views/test_mcp_blog.py
git commit -m "feat: expose blog publisher MCP endpoint at /api/mcp/blog/<token>/"
```

---

### Task 6: Panel connector management endpoints

**Files:**
- Modify: `backend/content/views/mcp_blog.py` (append panel views)
- Modify: `backend/content/urls.py` (import + 3 routes)
- Test: append to `backend/content/tests/views/test_mcp_blog.py`

**Interfaces:**
- Consumes: `IsSuperUser` from `content.permissions`; `BASE_URL` from `content.services.blog_service`; `BLOG_TOOLS`.
- Produces routes (all superuser, session + CSRF):
  - `GET /api/mcp-connectors/` → `[{slug, name, description, is_active, has_token, token_prefix, last_used_at, tools: [{name, description}]}]`
  - `POST /api/mcp-connectors/<slug>/generate-token/` → `{connector_url, token_prefix}`
  - `PATCH /api/mcp-connectors/<slug>/` (body `{is_active: bool}`) → connector row (same shape as list item)

- [ ] **Step 1: Write the failing tests (append to `test_mcp_blog.py`)**

```python
@pytest.fixture
def superuser_client(api_client, django_user_model):
    user = django_user_model.objects.create_user(
        username='root_test', password='x', is_staff=True, is_superuser=True,
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestMcpConnectorPanelEndpoints:
    def test_staff_non_superuser_gets_403(self, admin_client):
        assert admin_client.get('/api/mcp-connectors/').status_code == 403
        assert admin_client.post('/api/mcp-connectors/blog/generate-token/').status_code == 403

    def test_list_includes_blog_connector_with_tools(self, superuser_client):
        response = superuser_client.get('/api/mcp-connectors/')
        assert response.status_code == 200
        blog = next(c for c in response.data if c['slug'] == 'blog')
        assert blog['is_active'] is False
        assert blog['has_token'] is False
        tool_names = [t['name'] for t in blog['tools']]
        assert 'create_blog_post' in tool_names

    def test_generate_token_returns_full_url_once(self, superuser_client):
        response = superuser_client.post('/api/mcp-connectors/blog/generate-token/')
        assert response.status_code == 200
        url = response.data['connector_url']
        assert url.startswith('https://projectapp.co/api/mcp/blog/')
        token = url.rstrip('/').rsplit('/', 1)[-1]
        connector = McpConnector.objects.get(slug='blog')
        assert connector.check_token(token) is True
        assert response.data['token_prefix'] == token[:8]

    def test_toggle_is_active(self, superuser_client):
        response = superuser_client.patch(
            '/api/mcp-connectors/blog/', {'is_active': True}, format='json',
        )
        assert response.status_code == 200
        assert McpConnector.objects.get(slug='blog').is_active is True

    def test_unknown_slug_is_404(self, superuser_client):
        assert superuser_client.patch(
            '/api/mcp-connectors/nope/', {'is_active': True}, format='json',
        ).status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/views/test_mcp_blog.py::TestMcpConnectorPanelEndpoints -v`
Expected: FAIL with 404s (routes missing)

- [ ] **Step 3: Implement the panel views (append to `views/mcp_blog.py`)**

```python
from django.shortcuts import get_object_or_404

from content.permissions import IsSuperUser
from content.services.blog_service import BASE_URL

TOOLS_BY_SLUG = {
    'blog': BLOG_TOOLS,
}


def _connector_payload(connector):
    tools = TOOLS_BY_SLUG.get(connector.slug, [])
    return {
        'slug': connector.slug,
        'name': connector.name,
        'description': connector.description,
        'is_active': connector.is_active,
        'has_token': bool(connector.token_hash),
        'token_prefix': connector.token_prefix,
        'last_used_at': connector.last_used_at.isoformat() if connector.last_used_at else None,
        'tools': [{'name': t['name'], 'description': t['description']} for t in tools],
    }


@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_mcp_connectors(request):
    """List MCP connectors for /panel/mcps."""
    connectors = McpConnector.objects.all().order_by('slug')
    return Response([_connector_payload(c) for c in connectors], status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def generate_mcp_connector_token(request, slug):
    """Create/rotate the connector token. The full URL is returned ONCE."""
    connector = get_object_or_404(McpConnector, slug=slug)
    token = connector.generate_token()
    logger.info('[MCP] token rotated for connector %s by %s', slug, request.user.username)
    return Response({
        'connector_url': f'{BASE_URL}/api/mcp/{connector.slug}/{token}/',
        'token_prefix': connector.token_prefix,
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_mcp_connector(request, slug):
    """Toggle is_active."""
    connector = get_object_or_404(McpConnector, slug=slug)
    if 'is_active' in request.data:
        connector.is_active = bool(request.data['is_active'])
        connector.save(update_fields=['is_active', 'updated_at'])
        logger.info(
            '[MCP] connector %s %s by %s',
            slug, 'activated' if connector.is_active else 'deactivated',
            request.user.username,
        )
    return Response(_connector_payload(connector), status=status.HTTP_200_OK)
```

- [ ] **Step 4: Add the URLs**

In `backend/content/urls.py`, extend the mcp import and add:

```python
from content.views.mcp_blog import (
    generate_mcp_connector_token,
    list_mcp_connectors,
    mcp_blog_endpoint,
    update_mcp_connector,
)
```

```python
    path('mcp-connectors/', list_mcp_connectors, name='list-mcp-connectors'),
    path('mcp-connectors/<slug:slug>/', update_mcp_connector, name='update-mcp-connector'),
    path('mcp-connectors/<slug:slug>/generate-token/', generate_mcp_connector_token, name='generate-mcp-connector-token'),
```

Note: register `mcp-connectors/<slug>/generate-token/` BEFORE `mcp-connectors/<slug>/`? Not needed — Django matches the more specific path because `<slug:slug>/` requires the trailing segment to be the whole remainder; `blog/generate-token/` does not match `<slug:slug>/`. Order as listed is fine.

- [ ] **Step 5: Run tests to verify they pass**

Run: `source .venv/bin/activate && cd backend && pytest content/tests/views/test_mcp_blog.py -v`
Expected: 13 PASS (8 from Task 5 + 5 new)

- [ ] **Step 6: Commit**

```bash
git add backend/content/views/mcp_blog.py backend/content/urls.py backend/content/tests/views/test_mcp_blog.py
git commit -m "feat: add superuser panel endpoints to manage MCP connector tokens"
```

---

### Task 7: Pinia store `mcps.js`

**Files:**
- Create: `frontend/stores/mcps.js`
- Test: `frontend/test/stores/mcps.test.js`

**Interfaces:**
- Consumes: `get_request`, `create_request`, `patch_request` from `frontend/stores/services/request_http` (content/admin HTTP client).
- Produces: `useMcpsStore` with state `{connectors, loading, error}`, actions `fetchConnectors()`, `generateToken(slug) -> {success, data|error}` (data = `{connector_url, token_prefix}`), `toggleConnector(slug, isActive)`.

- [ ] **Step 1: Write the failing test**

```javascript
// frontend/test/stores/mcps.test.js
import { setActivePinia, createPinia } from 'pinia'
import { useMcpsStore } from '../../stores/mcps'

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
}))

const { get_request, create_request, patch_request } = require('../../stores/services/request_http')

const CONNECTOR = {
  slug: 'blog',
  name: 'Blog Publisher',
  description: 'Publica blogs desde Claude.',
  is_active: false,
  has_token: false,
  token_prefix: '',
  last_used_at: null,
  tools: [{ name: 'create_blog_post', description: 'Crea un post.' }],
}

describe('useMcpsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useMcpsStore()
    jest.clearAllMocks()
  })

  it('fetchConnectors loads the list', async () => {
    get_request.mockResolvedValue({ data: [CONNECTOR] })
    const result = await store.fetchConnectors()
    expect(result.success).toBe(true)
    expect(store.connectors).toHaveLength(1)
    expect(get_request).toHaveBeenCalledWith('mcp-connectors/')
  })

  it('fetchConnectors stores a readable error on failure', async () => {
    get_request.mockRejectedValue({ response: { data: { detail: 'nope' } } })
    const result = await store.fetchConnectors()
    expect(result.success).toBe(false)
    expect(store.error).toBe('nope')
  })

  it('generateToken returns the one-time connector URL', async () => {
    create_request.mockResolvedValue({
      data: { connector_url: 'https://projectapp.co/api/mcp/blog/abc123def/', token_prefix: 'abc123de' },
    })
    get_request.mockResolvedValue({ data: [{ ...CONNECTOR, has_token: true, token_prefix: 'abc123de' }] })
    const result = await store.generateToken('blog')
    expect(result.success).toBe(true)
    expect(result.data.connector_url).toContain('/api/mcp/blog/')
    expect(create_request).toHaveBeenCalledWith('mcp-connectors/blog/generate-token/', {})
  })

  it('toggleConnector patches is_active and updates local state', async () => {
    store.connectors = [{ ...CONNECTOR }]
    patch_request.mockResolvedValue({ data: { ...CONNECTOR, is_active: true } })
    const result = await store.toggleConnector('blog', true)
    expect(result.success).toBe(true)
    expect(store.connectors[0].is_active).toBe(true)
    expect(patch_request).toHaveBeenCalledWith('mcp-connectors/blog/', { is_active: true })
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix frontend test -- test/stores/mcps.test.js`
Expected: FAIL — cannot find module `../../stores/mcps`

- [ ] **Step 3: Implement the store**

```javascript
// frontend/stores/mcps.js
import { defineStore } from 'pinia';
import { get_request, create_request, patch_request } from './services/request_http';

export const useMcpsStore = defineStore('mcps', {
  state: () => ({
    connectors: [],
    loading: false,
    error: null,
  }),

  getters: {},

  actions: {
    async fetchConnectors() {
      this.loading = true;
      this.error = null;
      try {
        const response = await get_request('mcp-connectors/');
        this.connectors = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error.response?.data?.detail || 'Error al cargar los conectores MCP.';
        return { success: false, error: this.error };
      /* c8 ignore next 3 */
      } finally {
        this.loading = false;
      }
    },

    async generateToken(slug) {
      try {
        const response = await create_request(`mcp-connectors/${slug}/generate-token/`, {});
        await this.fetchConnectors();
        return { success: true, data: response.data };
      } catch (error) {
        const detail = error.response?.data?.detail || 'Error al generar el token.';
        return { success: false, error: detail };
      }
    },

    async toggleConnector(slug, isActive) {
      try {
        const response = await patch_request(`mcp-connectors/${slug}/`, { is_active: isActive });
        const index = this.connectors.findIndex((c) => c.slug === slug);
        if (index !== -1) this.connectors.splice(index, 1, response.data);
        return { success: true, data: response.data };
      } catch (error) {
        const detail = error.response?.data?.detail || 'Error al actualizar el conector.';
        return { success: false, error: detail };
      }
    },
  },
});
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix frontend test -- test/stores/mcps.test.js`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/stores/mcps.js frontend/test/stores/mcps.test.js
git commit -m "feat: add mcps store for panel MCP connector management"
```

---

### Task 8: Panel page `/panel/mcps` + nav + view catalog

**Files:**
- Create: `frontend/pages/panel/mcps/index.vue`
- Modify: `frontend/config/panelNav.js` (new superuser section before the closing `]` of `sections`, after the accounting section)
- Modify: `frontend/config/viewCatalog.js` (new section after `panel-accounting`)

**Interfaces:**
- Consumes: `useMcpsStore` (Task 7), `usePanelNotify` composable, base components `BaseToggle`, `BaseButton` (same imports as `frontend/pages/panel/accounting/settings.vue` — copy its import style), middleware `['admin-auth', 'superuser-only']`.
- Produces: superuser-only page listing connector cards with toggle, masked token, tools, and one-time token modal. `data-testid` hooks for E2E: `mcp-card-blog`, `mcp-toggle-blog`, `mcp-generate-token-blog`, `mcp-token-modal`, `mcp-token-url`, `mcp-token-copy`, `mcp-token-close`.

- [ ] **Step 1: Implement the page**

Before writing, open `frontend/pages/panel/accounting/settings.vue` and mirror its `<script setup>` conventions (definePageMeta, store usage, notify composable). Page content:

```vue
<!-- frontend/pages/panel/mcps/index.vue -->
<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-light text-text-default">MCPs</h1>
      <p class="text-sm text-text-subtle mt-1">
        Conectores MCP para usar los módulos del panel desde Claude (claude.ai).
      </p>
    </div>

    <div v-if="store.loading && store.connectors.length === 0" class="text-center py-16 text-text-subtle text-sm">
      Cargando conectores...
    </div>

    <div v-else class="max-w-2xl space-y-4">
      <div
        v-for="connector in store.connectors"
        :key="connector.slug"
        :data-testid="`mcp-card-${connector.slug}`"
        class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6"
      >
        <div class="flex items-start justify-between gap-3 mb-1">
          <h2 class="text-lg font-bold text-text-default">{{ connector.name }}</h2>
          <BaseToggle
            :model-value="connector.is_active"
            :aria-label="`Activar ${connector.name}`"
            :data-testid="`mcp-toggle-${connector.slug}`"
            @update:model-value="(value) => onToggle(connector, value)"
          />
        </div>
        <p class="text-sm text-text-muted mb-4">{{ connector.description }}</p>

        <div class="flex items-center gap-2 text-sm mb-4">
          <span class="text-text-subtle">Token:</span>
          <code v-if="connector.has_token" class="text-xs bg-surface-muted rounded px-2 py-1">
            {{ connector.token_prefix }}…
          </code>
          <span v-else class="text-text-subtle">sin generar</span>
          <span v-if="connector.last_used_at" class="text-xs text-text-subtle ml-auto">
            Último uso: {{ formatDate(connector.last_used_at) }}
          </span>
        </div>

        <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mb-2">
          Funciones disponibles
        </p>
        <ul class="space-y-1 mb-5">
          <li v-for="tool in connector.tools" :key="tool.name" class="text-sm">
            <code class="text-xs bg-surface-muted rounded px-1.5 py-0.5">{{ tool.name }}</code>
            <span class="text-text-muted ml-1">{{ tool.description }}</span>
          </li>
        </ul>

        <div class="flex items-center justify-end pt-4 border-t border-border-muted">
          <BaseButton
            variant="primary"
            size="sm"
            :data-testid="`mcp-generate-token-${connector.slug}`"
            @click="onGenerateToken(connector)"
          >
            {{ connector.has_token ? 'Regenerar token' : 'Generar token' }}
          </BaseButton>
        </div>
      </div>
    </div>

    <!-- One-time token modal -->
    <div
      v-if="tokenModal.open"
      data-testid="mcp-token-modal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    >
      <div class="bg-surface rounded-xl shadow-lg max-w-lg w-full p-6">
        <h3 class="text-lg font-bold text-text-default mb-2">URL del conector</h3>
        <p class="text-sm text-text-muted mb-4">
          Cópiala ahora: por seguridad no se volverá a mostrar. Pégala en
          claude.ai → Settings → Connectors → “Add custom connector”.
        </p>
        <code
          data-testid="mcp-token-url"
          class="block text-xs bg-surface-muted rounded p-3 break-all mb-4"
        >{{ tokenModal.url }}</code>
        <div class="flex items-center justify-end gap-2">
          <BaseButton variant="secondary" size="sm" data-testid="mcp-token-copy" @click="copyTokenUrl">
            {{ tokenModal.copied ? 'Copiada ✓' : 'Copiar URL' }}
          </BaseButton>
          <BaseButton variant="primary" size="sm" data-testid="mcp-token-close" @click="closeTokenModal">
            Listo, la guardé
          </BaseButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue';
import { useMcpsStore } from '~/stores/mcps';
import { usePanelNotify } from '~/composables/usePanelNotify';

definePageMeta({
  layout: 'admin',
  middleware: ['admin-auth', 'superuser-only'],
});

const store = useMcpsStore();
const notify = usePanelNotify();

const tokenModal = reactive({ open: false, url: '', copied: false });

onMounted(() => {
  store.fetchConnectors();
});

function formatDate(iso) {
  return new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
}

async function onToggle(connector, value) {
  const result = await store.toggleConnector(connector.slug, value);
  if (!result.success) notify.error(result.error);
}

async function onGenerateToken(connector) {
  const result = await store.generateToken(connector.slug);
  if (!result.success) {
    notify.error(result.error);
    return;
  }
  tokenModal.url = result.data.connector_url;
  tokenModal.copied = false;
  tokenModal.open = true;
}

async function copyTokenUrl() {
  try {
    await navigator.clipboard.writeText(tokenModal.url);
    tokenModal.copied = true;
  } catch {
    notify.error('No se pudo copiar. Selecciona la URL manualmente.');
  }
}

function closeTokenModal() {
  tokenModal.open = false;
  tokenModal.url = '';
}
</script>
```

Adjust component/composable import paths to match how `accounting/settings.vue` actually imports `BaseToggle`, `BaseButton`, and the notify composable (auto-import vs explicit) — mirror that file exactly.

- [ ] **Step 2: Add nav section**

In `frontend/config/panelNav.js`, after the accounting section object, add:

```javascript
    {
      id: 'integrations',
      label: 'Integrations',
      superuserOnly: true,
      items: [
        { label: 'MCPs', href: lp('/panel/mcps'), icon: 'settings' },
      ],
    },
```

- [ ] **Step 3: Add view catalog entry**

In `frontend/config/viewCatalog.js`, after the `panel-accounting` section, add:

```javascript
  {
    id: 'panel-mcps',
    label: 'MCPs (panel)',
    description: 'Gestion de conectores MCP para Claude, solo superusuarios.',
    views: [
      {
        label: 'MCPs — Conectores',
        url: '/panel/mcps',
        file: 'frontend/pages/panel/mcps/index.vue',
        reference: 'vista de gestion de conectores MCP del panel',
        audience: 'admin',
        viewType: 'settings',
      },
    ],
  },
```

Check the allowed `viewType` values used elsewhere in the file (`settings` appears for accounting settings; if not, use the closest existing value — do not invent a new one).

- [ ] **Step 4: Run the store test as smoke + build-level sanity**

Run: `npm --prefix frontend test -- test/stores/mcps.test.js`
Expected: PASS (page has no unit test; it is covered by E2E in Task 9)

- [ ] **Step 5: Commit**

```bash
git add frontend/pages/panel/mcps/ frontend/config/panelNav.js frontend/config/viewCatalog.js
git commit -m "feat: add /panel/mcps superuser page for MCP connector management"
```

---

### Task 9: E2E coverage + flow definitions + final audit

**Files:**
- Create: `frontend/e2e/admin/admin-mcps.spec.js`
- Modify: `frontend/e2e/helpers/flow-tags.js` (add `ADMIN_MCPS` tag following the existing export pattern)
- Modify: `frontend/e2e/flow-definitions.json` (add flow entry following the existing schema — copy an accounting entry and adapt)

**Interfaces:**
- Consumes: `test`/`expect` from `../helpers/test.js`, `mockApi` from `../helpers/api.js`, `setAuthLocalStorage` from `../helpers/auth.js` (same imports as `admin-accounting-dashboard.spec.js`).

- [ ] **Step 1: Write the E2E spec**

Open `frontend/e2e/admin/admin-accounting-dashboard.spec.js` first and mirror its setup (auth mock with superuser, `mockApi` usage, `domcontentloaded` + explicit waits — never `networkidle`). Spec:

```javascript
/**
 * E2E tests for the MCPs panel section (superuser-only).
 *
 * FLOW: admin-mcps
 * Covers: connector card rendering, token generation one-time modal,
 *         active toggle, and superuser gating redirect.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_MCPS } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const CONNECTOR = {
  slug: 'blog',
  name: 'Blog Publisher',
  description: 'Permite a Claude crear, programar, editar y consultar posts del blog.',
  is_active: false,
  has_token: false,
  token_prefix: '',
  last_used_at: null,
  tools: [
    { name: 'get_blog_template', description: 'Template JSON del blog.' },
    { name: 'create_blog_post', description: 'Crea un post.' },
  ],
};

const TOKEN_RESPONSE = {
  connector_url: 'https://projectapp.co/api/mcp/blog/e2e-token-abc123/',
  token_prefix: 'e2e-toke',
};

test.describe('Panel MCPs', () => {
  test(`muestra el conector y genera token una sola vez ${ADMIN_MCPS}`, async ({ page }) => {
    await setAuthLocalStorage(page, { superuser: true });
    await mockApi(page, {
      'mcp-connectors/': { GET: [CONNECTOR] },
      'mcp-connectors/blog/generate-token/': { POST: TOKEN_RESPONSE },
    });

    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('mcp-card-blog')).toBeVisible();
    await expect(page.getByText('Blog Publisher')).toBeVisible();
    await expect(page.getByText('create_blog_post')).toBeVisible();

    await page.getByTestId('mcp-generate-token-blog').click();
    await expect(page.getByTestId('mcp-token-modal')).toBeVisible();
    await expect(page.getByTestId('mcp-token-url')).toContainText('/api/mcp/blog/');

    await page.getByTestId('mcp-token-close').click();
    await expect(page.getByTestId('mcp-token-modal')).not.toBeVisible();
  });

  test(`staff no superusuario es redirigido ${ADMIN_MCPS}`, async ({ page }) => {
    await setAuthLocalStorage(page, { superuser: false });
    await mockApi(page, { 'mcp-connectors/': { GET: [CONNECTOR] } });

    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/panel', { waitUntil: 'domcontentloaded' });
    await expect(page).not.toHaveURL(/\/panel\/mcps/);
  });
});
```

Adapt the exact `setAuthLocalStorage`/`mockApi` call signatures to what the helpers actually expose (check `admin-accounting-dashboard.spec.js` and `helpers/auth.js` — the superuser flag name may differ). Add the `ADMIN_MCPS` tag to `flow-tags.js` and a matching entry in `flow-definitions.json` copying an accounting flow's schema.

- [ ] **Step 2: Run the E2E spec**

Run: `npm --prefix frontend run e2e -- e2e/admin/admin-mcps.spec.js`
Expected: 2 PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/
git commit -m "test: add E2E coverage for the panel MCPs section"
```

- [ ] **Step 4: Final audits (skills)**

1. Invoke the `e2e-user-flows-check` skill (required by CLAUDE.md: new panel route/flow).
2. Invoke `superpowers:requesting-code-review` / run `/code-review` per the executing workflow.
3. Push and update PR #69 (the spec PR) — implementation lands on the same branch `feat/02072026-blog-publisher-mcp`. Report the PR URL.

---

## Verification (manual, post-deploy)

1. `/panel/mcps` as superuser → generate token → copy connector URL.
2. claude.ai → Settings → Connectors → Add custom connector → paste URL.
3. In a chat: ask Claude to list blog posts → check the calendar → create a draft.
4. Verify the draft in `/panel` blog module.
5. Schedule a post 10 minutes out; verify Huey publishes it (site + LinkedIn + rebuild).
