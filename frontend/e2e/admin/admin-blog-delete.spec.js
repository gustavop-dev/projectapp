/**
 * E2E tests for admin blog post deletion.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_BLOG_DELETE } from '../helpers/flow-tags.js';

test.describe('Admin Blog Delete', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 9000, role: 'admin', is_staff: true } });
  });

  test('deletes blog post from list', {
    tag: [...ADMIN_BLOG_DELETE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'blog/admin/') return { status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, title_es: 'Borrar', title_en: 'Delete', is_published: true }]) };
      if (apiPath === 'blog/admin/1/delete/') return { status: 204, contentType: 'application/json', body: '' };
      return null;
    });
    await page.goto('/panel/blog');
    await page.waitForLoadState('networkidle');
  });
});
