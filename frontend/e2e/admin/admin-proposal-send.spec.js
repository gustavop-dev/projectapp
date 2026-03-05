/**
 * E2E tests for admin sending a proposal to a client.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_SEND } from '../helpers/flow-tags.js';

test.describe('Admin Proposal Send', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8300, role: 'admin', is_staff: true } });
  });

  test('sends proposal from edit page', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'proposals/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, uuid: '11111111-1111-1111-1111-111111111111', title: 'Send Test', client_name: 'Client', client_email: 'client@test.com', status: 'draft', sections: [], requirement_groups: [] }) };
      if (apiPath === 'proposals/1/send/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, status: 'sent', sent_at: '2026-03-04T12:00:00Z' }) };
      return null;
    });
    await page.goto('/panel/proposals/1/edit');
    await page.waitForLoadState('networkidle');
  });
});
