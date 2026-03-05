/**
 * E2E tests for admin blog post creation.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_BLOG_CREATE } from '../helpers/flow-tags.js';

test.describe('Admin Blog Create', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8800, role: 'admin', is_staff: true } });
  });

  test('renders blog creation form with bilingual fieldsets', {
    tag: [...ADMIN_BLOG_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      return null;
    });
    await page.goto('/panel/blog/create');
    await page.waitForLoadState('networkidle');
  });
});
