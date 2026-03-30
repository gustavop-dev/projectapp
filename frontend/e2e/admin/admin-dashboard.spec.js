/**
 * E2E tests for admin dashboard.
 *
 * Covers: dashboard render, Pipeline Value KPI card.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DASHBOARD, ADMIN_DASHBOARD_PIPELINE_VALUE } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDashboardWithPipeline = {
  total: 10,
  conversion_rate: 40,
  avg_time_to_first_view_hours: 12,
  avg_time_to_response_hours: 48,
  pipeline_value: 45000000,
  pipeline_count: 3,
  by_status: { draft: 2, sent: 3, viewed: 2, accepted: 2, rejected: 1 },
};

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8400, role: 'admin', is_staff: true } });
  });

  test('renders dashboard page', {
    tag: [...ADMIN_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: '[]' };
      if (apiPath === 'blog/admin/') return { status: 200, contentType: 'application/json', body: '[]' };
      return null;
    });
    await page.goto('/panel');
    await page.waitForLoadState('networkidle');
  });

  test('renders Pipeline Value KPI card with value and count', {
    tag: [...ADMIN_DASHBOARD_PIPELINE_VALUE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: '[]' };
      if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDashboardWithPipeline) };
      if (apiPath === 'blog/admin/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0, page: 1, page_size: 10, total_pages: 1 }) };
      return null;
    });
    await page.goto('/panel');
    await page.waitForResponse(res => res.url().includes('/api/proposals/dashboard/'));

    await expect(page.getByText('Pipeline activo')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/3 propuestas en curso/)).toBeVisible();
  });

  test('Pipeline Value card is hidden when pipeline_value is null', {
    tag: [...ADMIN_DASHBOARD_PIPELINE_VALUE, '@role:admin'],
  }, async ({ page }) => {
    const noPipeline = { ...mockDashboardWithPipeline, pipeline_value: null };
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: '[]' };
      if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify(noPipeline) };
      if (apiPath === 'blog/admin/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0, page: 1, page_size: 10, total_pages: 1 }) };
      return null;
    });
    await page.goto('/panel');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Tasa de cierre')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Pipeline activo')).not.toBeVisible();
  });
});
