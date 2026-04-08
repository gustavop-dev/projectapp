/**
 * E2E tests for admin proposal dashboard rendering and manual refresh.
 *
 * Covers: dashboard toggle visibility, KPI cards render with data,
 * manual refresh button triggers API call and updates data.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_DASHBOARD_AUTO_REFRESH } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDashboardData = {
  total_proposals: 12,
  conversion_rate: 42,
  pct_revisit: 25,
  avg_time_to_first_view_hours: 3,
  avg_time_to_response: null,
  by_status: { draft: 3, sent: 5, accepted: 4 },
  top_rejection_reasons: [],
  monthly_trend: [],
  avg_value_by_status: {},
};

const mockProposals = [
  { id: 1, uuid: 'aaa', title: 'Test', client_name: 'Client', client_email: 'c@t.com', status: 'sent', total_investment: '5000000', currency: 'COP', view_count: 3, is_active: true, heat_score: 5, created_at: '2026-01-10T10:00:00Z', last_activity_at: '2026-01-10T10:00:00Z' },
];

test.describe('Admin Proposal Dashboard Auto-Refresh', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8700, role: 'admin', is_staff: true },
    });
  });

  test('dashboard toggle shows KPI cards with metrics', {
    tag: [...ADMIN_PROPOSAL_DASHBOARD_AUTO_REFRESH, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
      if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDashboardData) };
      if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });

    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    // Dashboard is open by default — KPI cards should render with data
    await expect(page.getByText('Total propuestas')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('12')).toBeVisible();
    await expect(page.getByText('Tasa conversión')).toBeVisible();
    await expect(page.getByText('42%')).toBeVisible();
  });

  test('clicking "Actualizar" refreshes dashboard data', {
    tag: [...ADMIN_PROPOSAL_DASHBOARD_AUTO_REFRESH, '@role:admin'],
  }, async ({ page }) => {
    let dashboardCalls = 0;

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
      if (apiPath === 'proposals/dashboard/') {
        dashboardCalls++;
        const data = dashboardCalls > 1
          ? { ...mockDashboardData, total_proposals: 15, conversion_rate: 50 }
          : mockDashboardData;
        return { status: 200, contentType: 'application/json', body: JSON.stringify(data) };
      }
      if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });

    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    // Dashboard is open by default
    await expect(page.getByText('Total propuestas')).toBeVisible({ timeout: 10000 });

    // Click refresh
    await page.getByRole('button', { name: 'Actualizar', exact: true }).click();

    // Updated data should appear
    await expect(page.getByText('15')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('50%')).toBeVisible();
    expect(dashboardCalls).toBeGreaterThan(1);
  });
});
