/**
 * E2E tests for admin proposal metrics manual.
 *
 * Covers: floating ? button, slide-over panel with searchable metric definitions.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_METRICS_MANUAL } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockProposals = [
  { id: 1, uuid: 'aaa', title: 'P1', client_name: 'C1', status: 'sent', created_at: '2026-01-01' },
];

function setupMock(page) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
    if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: '[]' };
    if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: '{}' };
    return null;
  });
}

test.describe('Admin Proposal Metrics Manual', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8400, role: 'admin', is_staff: true } });
  });

  test('floating ? button opens metrics manual slide-over', {
    tag: [...ADMIN_PROPOSAL_METRICS_MANUAL, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    // Click the floating ? button
    const triggerBtn = page.getByTitle('Manual de métricas');
    await expect(triggerBtn).toBeVisible({ timeout: 10000 });
    await triggerBtn.click();

    // Slide-over should open with title and search
    await expect(page.getByText('Manual de Métricas')).toBeVisible({ timeout: 5000 });
    await expect(page.getByPlaceholder('Buscar métrica...')).toBeVisible();

    // Should show metric entries
    await expect(page.getByText('Tasa de conversión')).toBeVisible();
    await expect(page.getByText('Engagement Score (0-100)')).toBeVisible();
  });

  test('search filters metric definitions', {
    tag: [...ADMIN_PROPOSAL_METRICS_MANUAL, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    await page.getByTitle('Manual de métricas').click();
    await expect(page.getByText('Manual de Métricas')).toBeVisible({ timeout: 5000 });

    // Search for "zombie"
    await page.getByPlaceholder('Buscar métrica...').fill('zombie');

    // Should show only zombie-related metric
    await expect(page.getByText('Propuestas zombie')).toBeVisible();
    await expect(page.getByText('1 resultado')).toBeVisible();
  });
});
