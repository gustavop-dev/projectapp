/**
 * E2E tests for admin impersonation ("Login with this user") flow.
 *
 * @flow:admin-impersonate-user
 * Covers: superuser clicks "Login with this user" on /panel/admins, backend
 *         issues a single-use exchange code, a new tab opens at
 *         /platform/admin-login and exchanges the code for session tokens,
 *         landing authenticated on /platform/dashboard.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_IMPERSONATE_USER } from '../helpers/flow-tags.js';
import { mockPlatformAdmin } from '../helpers/platform-auth.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockAdmins = [
  {
    user_id: 101, first_name: 'Carlos', last_name: 'López', email: 'carlos@example.com',
    role: 'admin', is_active: true, is_onboarded: true, created_at: '2026-01-15T10:00:00Z',
  },
];

test.describe('Admin Impersonate User', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('"Login with this user" opens the impersonation tab and lands on the platform dashboard', {
    tag: [...ADMIN_IMPERSONATE_USER, '@role:admin'],
  }, async ({ page, context }) => {
    // Routes registered on the context (not just `page`) so the popup tab
    // opened by window.open() is mocked too — context-level routes apply to
    // pages created after registration, avoiding a race with the popup nav.
    await mockApi(context, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('accounts/admins/') && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockAdmins) };
      }
      if (apiPath === 'accounts/admins/101/login-as/' && method === 'POST') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ redirect_url: '/platform/admin-login?code=mock-exchange-code' }) };
      }
      if (apiPath === 'accounts/impersonation/exchange/' && method === 'POST') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ access: 'mock-access', refresh: 'mock-refresh' }) };
      }
      if (apiPath === 'accounts/me/' && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockPlatformAdmin) };
      }
      return null;
    });

    await page.goto('/panel/admins');
    await expect(page.getByRole('button', { name: 'Login with this user' })).toBeVisible();

    const [popup] = await Promise.all([
      context.waitForEvent('page'),
      page.getByRole('button', { name: 'Login with this user' }).click(),
    ]);

    await popup.waitForURL('**/platform/dashboard', { timeout: 15000 });
    await expect(popup).toHaveURL(/\/platform\/dashboard/);
  });
});
