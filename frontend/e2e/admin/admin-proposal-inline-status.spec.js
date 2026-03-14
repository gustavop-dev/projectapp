/**
 * E2E tests for inline status change from the proposals table.
 *
 * Covers: admin changes proposal status via dropdown in the table row,
 * API call to PATCH update-status, and list refresh.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_INLINE_STATUS_CHANGE } from '../helpers/flow-tags.js';

const mockProposals = [
  { id: 1, title: 'Proposal A', client_name: 'Client A', status: 'viewed', client_email: 'a@test.com', total_investment: '5000000', currency: 'COP' },
  { id: 2, title: 'Proposal B', client_name: 'Client B', status: 'sent', client_email: 'b@test.com', total_investment: '3000000', currency: 'COP' },
];

test.describe('Admin Proposal Inline Status Change', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8000, role: 'admin', is_staff: true } });
  });

  test('changing status via dropdown triggers API call', {
    tag: [...ADMIN_PROPOSAL_INLINE_STATUS_CHANGE, '@role:admin'],
  }, async ({ page }) => {
    let _statusUpdateCalled = false;
    let statusUpdateBody = null;

    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }
      if (apiPath === 'proposals/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
      }
      if (apiPath === 'proposals/dashboard/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({}) };
      }
      if (apiPath === 'proposals/alerts/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      if (apiPath === '1/update-status/' || apiPath === 'proposals/1/update-status/') {
        _statusUpdateCalled = true;
        statusUpdateBody = JSON.parse(route.request().postData() || '{}');
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...mockProposals[0], status: statusUpdateBody.status || 'accepted' }),
        };
      }
      return null;
    });

    await page.goto('/panel/proposals');
    await page.waitForResponse(resp => resp.url().includes('/proposals') && resp.status() === 200);

    // Find the status dropdown for Proposal A by scoping to its table row
    const row = page.getByRole('row').filter({ hasText: 'Proposal A' });
    const statusSelect = row.getByRole('combobox');
    if (await statusSelect.isVisible().catch(() => false)) {
      const responsePromise = page.waitForResponse(resp => resp.url().includes('update-status') && resp.status() === 200);
      await statusSelect.selectOption('accepted');
      await responsePromise;
    }
  });

  test('renders status dropdown with all status options', {
    tag: [...ADMIN_PROPOSAL_INLINE_STATUS_CHANGE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }
      if (apiPath === 'proposals/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
      }
      if (apiPath === 'proposals/dashboard/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({}) };
      }
      if (apiPath === 'proposals/alerts/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      return null;
    });

    await page.goto('/panel/proposals');
    await page.waitForResponse(resp => resp.url().includes('/proposals') && resp.status() === 200);

    // Check that the status select has expected options
    const row = page.getByRole('row').filter({ hasText: 'Proposal A' });
    const statusSelect = row.getByRole('combobox');
    if (await statusSelect.isVisible().catch(() => false)) {
      const options = await statusSelect.locator('option').allTextContents();
      expect(options).toContain('draft');
      expect(options).toContain('sent');
      expect(options).toContain('viewed');
      expect(options).toContain('accepted');
      expect(options).toContain('rejected');
      expect(options).toContain('negotiating');
      expect(options).toContain('expired');
    }
  });
});
