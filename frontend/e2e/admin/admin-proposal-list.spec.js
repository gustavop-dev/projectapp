/**
 * E2E tests for admin proposal list view.
 */
import { test } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_LIST } from '../helpers/flow-tags.js';

test.describe('Admin Proposal List', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8000, role: 'admin', is_staff: true } });
  });

  test('renders proposal list page', {
    tag: [...ADMIN_PROPOSAL_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, title: 'Test', client_name: 'Client', status: 'draft' }]) };
      return null;
    });
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');
  });
});
