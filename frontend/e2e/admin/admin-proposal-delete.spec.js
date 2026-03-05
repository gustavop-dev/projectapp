/**
 * E2E tests for admin proposal deletion.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_DELETE } from '../helpers/flow-tags.js';

test.describe('Admin Proposal Delete', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8500, role: 'admin', is_staff: true } });
  });

  test('deletes proposal from list', {
    tag: [...ADMIN_PROPOSAL_DELETE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, title: 'Delete Me', client_name: 'Client', status: 'draft' }]) };
      if (apiPath === 'proposals/1/delete/') return { status: 204, contentType: 'application/json', body: '' };
      return null;
    });
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');
  });
});
