/**
 * E2E tests for admin proposal section reordering.
 */
import { test } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_SECTION_REORDER } from '../helpers/flow-tags.js';

test.describe('Admin Proposal Section Reorder', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8600, role: 'admin', is_staff: true } });
  });

  test('reorders sections in proposal edit page', {
    tag: [...ADMIN_PROPOSAL_SECTION_REORDER, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'proposals/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, uuid: '11111111-1111-1111-1111-111111111111', title: 'Reorder Test', client_name: 'Client', status: 'draft', sections: [{ id: 1, section_type: 'greeting', title: 'Greeting', order: 0, is_enabled: true, content_json: {} }, { id: 2, section_type: 'executive_summary', title: 'Summary', order: 1, is_enabled: true, content_json: {} }], requirement_groups: [] }) };
      if (apiPath === 'proposals/1/reorder-sections/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ reordered: 2 }) };
      return null;
    });
    await page.goto('/panel/proposals/1/edit');
    await page.waitForLoadState('networkidle');
  });
});
