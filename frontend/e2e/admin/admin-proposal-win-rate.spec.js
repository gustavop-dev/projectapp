/**
 * E2E tests for admin proposal win rate dashboard.
 *
 * Covers: win rate by project type, market type, and combination table.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_WIN_RATE_DASHBOARD } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDashboard = {
  total: 10,
  conversion_rate: 40,
  by_status: { draft: 2, sent: 3, accepted: 3, rejected: 2 },
  win_rate_by_project_type: [
    { type: 'web_app', win_rate: 60, accepted: 3, total: 5 },
    { type: 'landing', win_rate: 33, accepted: 1, total: 3 },
  ],
  win_rate_by_market_type: [
    { type: 'saas', win_rate: 75, accepted: 3, total: 4 },
    { type: 'ecommerce', win_rate: 25, accepted: 1, total: 4 },
  ],
  win_rate_by_combination: [
    { project_type: 'web_app', market_type: 'saas', win_rate: 80, accepted: 4, total: 5 },
  ],
};

const mockProposals = [
  { id: 1, uuid: 'aaa', title: 'P1', client_name: 'C1', status: 'sent', created_at: '2026-01-01' },
];

function setupMock(page, dashboard = mockDashboard) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
    if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: '[]' };
    if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify(dashboard) };
    return null;
  });
}

test.describe('Admin Proposal Win Rate Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8400, role: 'admin', is_staff: true } });
  });

  test('renders win rate bars by project type', {
    tag: [...ADMIN_PROPOSAL_WIN_RATE_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    // Expand dashboard if collapsed
    const toggleBtn = page.getByRole('button', { name: /Dashboard|KPI/i });
    if (await toggleBtn.isVisible()) await toggleBtn.click();

    await expect(page.getByText('Win rate por tipo de proyecto')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('60%')).toBeVisible();
  });

  test('renders win rate bars by market type', {
    tag: [...ADMIN_PROPOSAL_WIN_RATE_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    const toggleBtn = page.getByRole('button', { name: /Dashboard|KPI/i });
    if (await toggleBtn.isVisible()) await toggleBtn.click();

    await expect(page.getByText('Win rate por tipo de mercado')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('75%')).toBeVisible();
  });

  test('renders win rate combination table', {
    tag: [...ADMIN_PROPOSAL_WIN_RATE_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    const toggleBtn = page.getByRole('button', { name: /Dashboard|KPI/i });
    if (await toggleBtn.isVisible()) await toggleBtn.click();

    await expect(page.getByText('Mejor combinación proyecto × mercado')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('80%')).toBeVisible();
  });
});
