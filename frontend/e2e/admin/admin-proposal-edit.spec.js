/**
 * E2E tests for admin proposal edit flow.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_EDIT } from '../helpers/flow-tags.js';

test.describe('Admin Proposal Edit', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8200, role: 'admin', is_staff: true } });
  });

  test('renders proposal edit page with tabs', {
    tag: [...ADMIN_PROPOSAL_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'proposals/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, uuid: '11111111-1111-1111-1111-111111111111', title: 'Edit Test', client_name: 'Client', status: 'draft', sections: [], requirement_groups: [] }) };
      return null;
    });
    await page.goto('/panel/proposals/1/edit');
    await page.waitForLoadState('networkidle');
  });
});
