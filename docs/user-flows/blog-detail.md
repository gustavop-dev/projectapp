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
