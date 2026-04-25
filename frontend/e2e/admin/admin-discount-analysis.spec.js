/**
 * E2E tests for admin discount analysis enhanced card.
 *
 * Covers: discount vs no-discount close rates, sample sizes (n=X),
 * average discount %, and warning when discount doesn't help.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DISCOUNT_ANALYSIS_ENHANCED } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDashboard = {
  total: 20,
  conversion_rate: 45,
  by_status: { draft: 3, sent: 5, accepted: 7, rejected: 5 },
  discount_close_rate: 50,
  no_discount_close_rate: 55,
  discount_analysis: {
    with_discount_count: 6,
    without_discount_count: 10,
    avg_discount_percent: 12,
    avg_discount_accepted: 8,
  },
};

function setupMock(page, dashboard = mockDashboard) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: '[]' };
    if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify(dashboard) };
    if (apiPath === 'blog/admin/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0, page: 1, page_size: 10, total_pages: 1 }) };
    return null;
  });
}

test.describe('Admin Discount Analysis Enhanced', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8400, role: 'admin', is_staff: true } });
  });

  test('renders discount card with sample sizes and average discount', {
    tag: [...ADMIN_DISCOUNT_ANALYSIS_ENHANCED, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel');

    // Discount card should show close rates
    await expect(page.getByText('Con descuento', { exact: true })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Sin descuento', { exact: true })).toBeVisible();

    // Sample sizes
    await expect(page.getByText('n=6')).toBeVisible();
    await expect(page.getByText('n=10')).toBeVisible();

    // Average discount percentage
    await expect(page.getByText(/Descuento promedio/)).toBeVisible();
    await expect(page.getByText('12%')).toBeVisible();
  });

  test('shows warning when discount does not improve close rate', {
    tag: [...ADMIN_DISCOUNT_ANALYSIS_ENHANCED, '@role:admin'],
  }, async ({ page }) => {
    // discount_close_rate (50) <= no_discount_close_rate (55) → delta <= 0
    await setupMock(page);
    await page.goto('/panel');

    await expect(page.getByText('Con descuento', { exact: true })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/no está mejorando el cierre/)).toBeVisible();
  });
});
