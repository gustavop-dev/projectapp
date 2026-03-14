/**
 * E2E tests for admin proposal KPI dashboard.
 *
 * Covers: toggle visibility, KPI cards rendering, status distribution,
 * and rejection reasons display.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_DASHBOARD } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockProposals = [
  { id: 1, uuid: 'aaa', title: 'Prop A', client_name: 'Carlos', status: 'sent', total_investment: 5000, currency: 'COP', view_count: 0, is_active: true },
];

const mockDashboard = {
  total_proposals: 12,
  conversion_rate: 25,
  avg_time_to_first_view_hours: 4.5,
  avg_time_to_response_hours: 48,
  by_status: { draft: 3, sent: 4, viewed: 2, accepted: 3 },
  top_rejection_reasons: [
    { rejection_reason: 'Precio alto', count: 3 },
    { rejection_reason: 'Sin presupuesto', count: 1 },
  ],
  monthly_trend: [],
  avg_value_by_status: { draft: 3000000, sent: 5000000, accepted: 8000000 },
};

const mockAlerts = [];

function setupMock(page) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
    if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockAlerts) };
    if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDashboard) };
    return null;
  });
}

test.describe('Admin Proposal Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('renders KPI cards with dashboard metrics', {
    tag: [...ADMIN_PROPOSAL_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');

    await expect(page.getByText('Total propuestas')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('12')).toBeVisible();
    await expect(page.getByText('25%')).toBeVisible();
    await expect(page.getByText('Tasa conversión')).toBeVisible();
  });

  test('displays status distribution bars', {
    tag: [...ADMIN_PROPOSAL_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');

    await expect(page.getByText('Total propuestas')).toBeVisible({ timeout: 15000 });
    const distSection = page.locator('text=Distribución por estado').locator('..');
    await expect(distSection).toBeVisible();
    await expect(distSection.getByText('draft').first()).toBeVisible();
    await expect(distSection.getByText('sent').first()).toBeVisible();
    await expect(distSection.getByText('accepted').first()).toBeVisible();
  });

  test('displays top rejection reasons', {
    tag: [...ADMIN_PROPOSAL_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');

    // Wait for KPI cards to render first to confirm dashboard data loaded
    await expect(page.getByText('Total propuestas')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Top motivos de rechazo')).toBeVisible();
    await expect(page.getByText('Precio alto')).toBeVisible();
    await expect(page.getByText('Sin presupuesto')).toBeVisible();
  });

  test('toggle button hides and shows dashboard', {
    tag: [...ADMIN_PROPOSAL_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');

    await expect(page.getByText('Total propuestas')).toBeVisible({ timeout: 15000 });

    // Hide dashboard
    const hideBtn = page.getByText('Ocultar Dashboard');
    await hideBtn.waitFor({ state: 'visible', timeout: 5000 });
    await hideBtn.click();
    await expect(page.getByText('Total propuestas')).not.toBeVisible();

    // Show dashboard
    const showBtn = page.getByText('Mostrar Dashboard KPI');
    await showBtn.waitFor({ state: 'visible', timeout: 5000 });
    await showBtn.click();
    await expect(page.getByText('Total propuestas')).toBeVisible({ timeout: 10000 });
  });
});
