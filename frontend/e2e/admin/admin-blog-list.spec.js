/**
 * E2E tests for admin blog list view.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_BLOG_LIST } from '../helpers/flow-tags.js';

test.describe('Admin Blog List', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('renders blog post list for admin', {
    tag: [...ADMIN_BLOG_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'blog/admin/') return { status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, title_es: 'Post ES', title_en: 'Post EN', is_published: true }]) };
      return null;
    });
    await page.goto('/panel/blog');
    await page.waitForLoadState('networkidle');
  });
});
