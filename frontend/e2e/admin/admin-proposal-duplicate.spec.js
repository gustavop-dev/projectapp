/**
 * E2E tests for admin proposal duplicate flow.
 *
 * Covers: duplicate action from proposal list dropdown, redirect to
 * new duplicate's edit page.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_DUPLICATE } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockProposals = [
  { id: 1, uuid: 'aaa', title: 'Propuesta Original', client_name: 'Carlos', client_email: 'c@t.com', status: 'sent', total_investment: 5000, currency: 'COP', view_count: 3, is_active: true, created_at: '2026-01-10T10:00:00Z' },
];

const mockDuplicated = {
  id: 50,
  uuid: 'dup-uuid',
  title: 'Propuesta Original (copia)',
  client_name: 'Carlos',
  status: 'draft',
  sections: [],
  requirement_groups: [],
};

const dashboardData = { total_proposals: 1, conversion_rate: 0, avg_time_to_first_view: null, avg_time_to_response: null, by_status: {}, top_rejection_reasons: [], monthly_trend: [], avg_value_by_status: {} };

test.describe('Admin Proposal Duplicate', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('duplicating a proposal from the list redirects to new edit page', {
    tag: [...ADMIN_PROPOSAL_DUPLICATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'proposals/' && route.request().method() === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
      }
      if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify(dashboardData) };
      if (apiPath === 'proposals/1/duplicate/' && route.request().method() === 'POST') {
        return { status: 201, contentType: 'application/json', body: JSON.stringify(mockDuplicated) };
      }
      if (apiPath === 'proposals/50/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDuplicated) };
      }
      return null;
    });

    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    // Open the actions dropdown for the first proposal
    await page.locator('table tbody tr').first().locator('button').last().click();
    await expect(page.getByRole('button', { name: 'Duplicar' })).toBeVisible();

    // Use dispatchEvent with bubbles:false to avoid tr click propagation
    await page.getByRole('button', { name: 'Duplicar' }).evaluate(el => {
      el.dispatchEvent(new MouseEvent('click', { bubbles: false }));
    });

    // Should redirect to the duplicated proposal's edit page
    await expect(page).toHaveURL(/\/panel\/proposals\/50\/edit/, { timeout: 10000 });
  });
});
