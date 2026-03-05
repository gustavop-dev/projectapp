/**
 * E2E tests for admin proposal creation flow.
 */
import { test } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_CREATE } from '../helpers/flow-tags.js';

test.describe('Admin Proposal Create', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8100, role: 'admin', is_staff: true } });
  });

  test('renders proposal creation form', {
    tag: [...ADMIN_PROPOSAL_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      return null;
    });
    await page.goto('/panel/proposals/create');
    await page.waitForLoadState('networkidle');
  });
});
