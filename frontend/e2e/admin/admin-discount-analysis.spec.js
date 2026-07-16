/**
 * E2E tests for the discount analysis card in the proposal KPI dashboard.
 *
 * The card lives in the collapsible dashboard on /panel/proposals (it moved
 * out of the global /panel dashboard with the redesign). Covers: discount
 * vs no-discount close rates, sample sizes (n=X), average discount %, and
 * the warning when discount doesn't help.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DISCOUNT_ANALYSIS_ENHANCED } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDashboard = {
  total_proposals: 20,
  conversion_rate: 45,
  by_status: { draft: 3, sent: 5, accepted: 7, rejected: 5 },
  top_rejection_reasons: [],
  monthly_trend: [],
  avg_value_by_status: {},
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
    if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: '[]' };
    return null;
  });
}

async function openKpiDashboard(page) {
  await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: /Mostrar Dashboard KPI/ }).click();
  await expect(page.getByTestId('discount-analysis-card')).toBeVisible({ timeout: 15000 });
}

test.describe('Admin Discount Analysis Enhanced', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8400, role: 'admin', is_staff: true } });
  });

  test('renders discount card with sample sizes and average discount', {
    tag: [...ADMIN_DISCOUNT_ANALYSIS_ENHANCED, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await openKpiDashboard(page);

    const card = page.getByTestId('discount-analysis-card');
    await expect(card.getByText('Con descuento', { exact: true })).toBeVisible();
    await expect(card.getByText('Sin descuento', { exact: true })).toBeVisible();

    await expect(card.getByText('n=6')).toBeVisible();
    await expect(card.getByText('n=10')).toBeVisible();

    await expect(card.getByText(/Descuento promedio/)).toBeVisible();
    await expect(card.getByText('12%')).toBeVisible();
  });

  test('shows warning when discount does not improve close rate', {
    tag: [...ADMIN_DISCOUNT_ANALYSIS_ENHANCED, '@role:admin'],
  }, async ({ page }) => {
    // discount_close_rate (50) <= no_discount_close_rate (55) → delta <= 0
    await setupMock(page);
    await openKpiDashboard(page);

    await expect(page.getByText(/no está mejorando el cierre/)).toBeVisible();
  });
});
