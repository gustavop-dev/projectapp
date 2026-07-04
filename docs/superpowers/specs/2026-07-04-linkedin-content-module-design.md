# LinkedIn Content Module + Sidebar Section Rename — Design

**Date:** 2026-07-04
**Status:** Approved

## Goal

Promote the existing LinkedIn integration (today embedded in the blog edit
page) to a first-class panel module, so freeform LinkedIn posts can be
created, scheduled and published from `/panel`. Rename the sidebar section
"Website content" to "ProjectApp content" to reflect the broader scope.

## Context (current state)

- Sidebar section `site` ("Website content") lives in
  `frontend/config/panelNav.js` with Blog, Blog calendar and Portfolio.
  Section labels render uppercase via CSS (`PanelSidebar.vue`,
  `PanelMobileDrawer.vue`), so the label displays as "PROJECTAPP CONTENT".
- LinkedIn OAuth (auth-url, callback, status) and blog→LinkedIn publishing
  already exist: `backend/content/views/linkedin.py`,
  `backend/content/services/linkedin_service.py`, encrypted
  `LinkedInToken` singleton, `/auth/linkedin/callback` frontend page.
- Blog scheduling pattern: per-post Huey ETA task + every-minute periodic
  sweep with atomic double-publish guards (`backend/content/tasks.py`).

## Scope decisions (user-confirmed)

1. Full module: freeform LinkedIn posts (own text, optional image), not
   tied to blog posts. Blog→LinkedIn publishing keeps working unchanged.
2. Lifecycle: drafts + manual publish + scheduled publishing via Huey
   (mirroring the blog scheduling pattern).
3. UI: single page `/panel/linkedin` with create/edit in a `BaseModal`
   (no separate create/edit routes).

## Backend

### Model — `content/models/linkedin_post.py`

`LinkedInPost`:

| Field | Type | Notes |
|---|---|---|
| `commentary` | TextField, max_length 3000 | LinkedIn commentary limit |
| `image` | ImageField, `upload_to='linkedin_posts/'`, blank | optional |
| `status` | CharField choices | `draft` / `scheduled` / `published` / `failed` |
| `scheduled_at` | DateTimeField, null | set → eligible for scheduling |
| `published_at` | DateTimeField, null | stamped on successful publish |
| `linkedin_post_id` | CharField, blank | LinkedIn URN from API |
| `error_message` | TextField, blank | last publish failure detail |
| `created_at` / `updated_at` | auto | |

New migration; register in Django admin.

### Service — `content/services/linkedin_service.py`

New `publish_post_to_linkedin(commentary, image_url='') -> dict`:
same token/refresh handling and payload shape as
`publish_blog_to_linkedin`, but without `content.article`. If an image is
provided, upload via existing `_upload_image_to_linkedin` and attach as
`content.media`. No changes to existing functions.

### Views — `content/views/linkedin.py` (function-based, `@api_view`, `IsAdminUser`)

- `GET/POST linkedin/posts/` — list + create.
- `GET/PUT/DELETE linkedin/posts/<id>/` — detail + update + delete.
  Editing is blocked once `status == 'published'`.
- `POST linkedin/posts/<id>/publish/` — publish now, with an atomic guard
  (`filter(status__in=['draft','scheduled','failed']).update(...)`) so a
  post cannot be double-published.
- Serializer with validated inputs (commentary required and ≤3000 chars,
  `scheduled_at` must be in the future when provided).
- Saving a post with `scheduled_at` sets `status='scheduled'` and enqueues
  the ETA task; clearing it reverts to `draft`.

### Scheduling — `content/tasks.py`

- `publish_single_scheduled_linkedin_post(post_id)` — ETA task enqueued on
  save, re-entrant with the same guards as the blog equivalent.
- `publish_scheduled_linkedin_posts()` — every-minute periodic safety-net
  sweep for posts with `status='scheduled'` and `scheduled_at <= now`.
- Both use the atomic `status` transition as the double-publish guard; on
  API failure, set `status='failed'` + `error_message`.

## Frontend

### Navigation

- `panelNav.js`: section `site` label → `'ProjectApp content'`; add item
  `{ label: 'LinkedIn', href: lp('/panel/linkedin'), icon: 'linkedin' }`.
- Add a `linkedin` glyph to `SidebarIcon.vue`.
- Update sidebar/drawer unit tests that assert the old section label.

### Store — `frontend/stores/linkedin.js` (new, snake_case, Options API, `request_http.js`)

- State: `posts`, `connectionStatus`.
- Actions: `fetchStatus`, `fetchAuthUrl`, `callback`, `fetchPosts`,
  `createPost`, `updatePost`, `deletePost`, `publishPost`.
- The three OAuth actions (`fetchLinkedInStatus`, `fetchLinkedInAuthUrl`,
  `linkedinCallback`) **move** from `stores/blog.js` to this store;
  `/panel/blog/[id]/edit.vue` and `/auth/linkedin/callback.vue` switch to
  the new store. `publishToLinkedIn` (blog-post publishing) stays in the
  blog store. `frontend/test/stores/blog.test.js` adjusted accordingly.

### Page — `frontend/pages/panel/linkedin/index.vue`

- Connection card: status (profile name / expiry), connect/reconnect via
  the existing OAuth redirect flow.
- Posts list: status chips, scheduled datetime, published-at + link when
  available; mobile uses the card pattern with `useIsMobile` (v-if, not
  CSS hidden).
- Create/edit `BaseModal`: commentary textarea with 3000 counter, image
  upload, optional schedule datetime, save-as-draft / schedule / publish
  now actions. Semantic design tokens + base components throughout.
- `viewCatalog.js` entry for the new route.

### Unchanged

- Blog edit page keeps its LinkedIn summary fields and publish button.
- OAuth callback route `/auth/linkedin/callback` is reused as-is (only its
  store import changes).

## Error handling

- Publish failures surface the LinkedIn API message in the UI and persist
  it in `error_message` with `status='failed'`; a failed post can be
  retried (publish now) or rescheduled.
- OAuth state validation, token refresh and encryption remain untouched.

## Testing

- Backend (pytest, small slices): model constraints, serializer
  validation, CRUD + publish guard views, scheduling task guards
  (mirroring `test_blog_publish_guards.py`), `publish_post_to_linkedin`
  payload shape (mocked requests).
- Frontend unit: new store actions; adjusted blog store tests; sidebar
  label test update.
- E2E: one spec for the module flow (connection card render, create draft,
  list shows it) following `admin-blog-linkedin.spec.js` conventions.
- Final step: run the `e2e-user-flows-check` audit (new user flow).
