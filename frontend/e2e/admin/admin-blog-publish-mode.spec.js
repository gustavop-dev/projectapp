/**
 * E2E tests for the blog publish-mode selector.
 *
 * @flow:admin-blog-publish-mode
 * Covers: the three-radio publish selector on the blog edit page —
 *         schedule mode revealing the datetime input with the overdue
 *         banner for past dates, hydration of a scheduled post, and the
 *         is_published/published_at payload for "Publicar ahora".
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_BLOG_PUBLISH_MODE } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const basePost = {
  id: 9,
  slug: 'post-de-prueba',
  title_es: 'Post de prueba',
  title_en: 'Test post',
  excerpt_es: 'Resumen ES',
  excerpt_en: 'Summary EN',
  content_es: 'Contenido',
  content_en: 'Content',
  category: '',
  read_time_minutes: 4,
  is_featured: false,
  is_published: false,
  published_at: null,
  author: 'projectapp-team',
  sources: [],
};

function baseRoutes(apiPath, post) {
  if (apiPath === 'auth/check/') return authCheck;
  if (apiPath === 'blog/admin/9/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify(post) };
  if (apiPath.startsWith('blog/categories')) return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  return null;
}

test.describe('Admin Blog Publish Mode', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('schedule mode reveals the datetime input hidden for drafts', {
    tag: [...ADMIN_BLOG_PUBLISH_MODE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => baseRoutes(apiPath, basePost));
    await page.goto('/panel/blog/9/edit', { waitUntil: 'domcontentloaded' });

    const draftRadio = page.locator('input[type="radio"][value="draft"]');
    await expect(draftRadio).toBeChecked();
    await expect(page.locator('input[type="datetime-local"]')).toBeHidden();

    await page.locator('input[type="radio"][value="schedule"]').check();
    await expect(page.locator('input[type="datetime-local"]')).toBeVisible();
  });

  test('shows the overdue banner for a post scheduled in the past', {
    tag: [...ADMIN_BLOG_PUBLISH_MODE, '@role:admin'],
  }, async ({ page }) => {
    // The banner reflects the STORED schedule at hydration time (a post
    // waiting for the Huey safety-net), not live input validation.
    const overduePost = { ...basePost, published_at: '2020-01-01T10:00:00Z' };
    await mockApi(page, async ({ apiPath }) => baseRoutes(apiPath, overduePost));
    await page.goto('/panel/blog/9/edit', { waitUntil: 'domcontentloaded' });

    await expect(page.locator('input[type="radio"][value="schedule"]')).toBeChecked();
    await expect(page.locator('[data-test="scheduled-overdue-banner"]')).toBeVisible();
  });

  test('hydrates a future-scheduled post into schedule mode', {
    tag: [...ADMIN_BLOG_PUBLISH_MODE, '@role:admin'],
  }, async ({ page }) => {
    const scheduled = { ...basePost, published_at: '2030-06-01T15:30:00Z' };
    await mockApi(page, async ({ apiPath }) => baseRoutes(apiPath, scheduled));
    await page.goto('/panel/blog/9/edit', { waitUntil: 'domcontentloaded' });

    await expect(page.locator('input[type="radio"][value="schedule"]')).toBeChecked();
    await expect(page.locator('input[type="datetime-local"]')).not.toHaveValue('');
    await expect(page.locator('[data-test="scheduled-overdue-banner"]')).toBeHidden();
  });

  test('saving in "Publicar ahora" submits is_published without a schedule', {
    tag: [...ADMIN_BLOG_PUBLISH_MODE, '@role:admin'],
  }, async ({ page }) => {
    let patchBody = null;
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'blog/admin/9/update/' && method === 'PATCH') {
        patchBody = route.request().postDataJSON();
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...basePost, is_published: true }) };
      }
      return baseRoutes(apiPath, basePost);
    });
    await page.goto('/panel/blog/9/edit', { waitUntil: 'domcontentloaded' });

    await page.locator('input[type="radio"][value="now"]').check();
    await page.getByRole('button', { name: 'Guardar Cambios' }).click();

    await expect.poll(() => patchBody).not.toBeNull();
    expect(patchBody.is_published).toBe(true);
    expect(patchBody.published_at).toBeNull();
  });
});
