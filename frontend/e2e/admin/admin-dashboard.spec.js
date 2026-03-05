/**
 * E2E tests for admin dashboard.
 */
import { test } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DASHBOARD } from '../helpers/flow-tags.js';

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8400, role: 'admin', is_staff: true } });
  });

  test('renders dashboard page', {
    tag: [...ADMIN_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: '[]' };
      if (apiPath === 'blog/admin/') return { status: 200, contentType: 'application/json', body: '[]' };
      return null;
    });
    await page.goto('/panel');
    await page.waitForLoadState('networkidle');
  });
});
