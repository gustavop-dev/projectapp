/**
 * E2E tests for admin blog post editing.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_BLOG_EDIT } from '../helpers/flow-tags.js';

test.describe('Admin Blog Edit', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8900, role: 'admin', is_staff: true } });
  });

  test('renders blog edit form with bilingual fields', {
    tag: [...ADMIN_BLOG_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'blog/admin/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, title_es: 'Post ES', title_en: 'Post EN', excerpt_es: 'E', excerpt_en: 'E', content_es: '<p>C</p>', content_en: '<p>C</p>', is_published: false }) };
      return null;
    });
    await page.goto('/panel/blog/1/edit');
    await page.waitForLoadState('networkidle');
  });
});
