/**
 * E2E tests for admin proposal batch actions.
 *
 * @flow: admin-proposal-batch-actions
 *
 * Covers: selecting proposals via checkboxes, batch action bar visibility,
 * cancel clears selection, select-all toggle, batch delete/expire/resend buttons.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_BATCH_ACTIONS } from '../helpers/flow-tags.js';

const mockProposals = [
  { id: 1, title: 'Proposal Alpha', client_name: 'Client A', client_email: 'a@test.com', status: 'sent', total_investment: '5000000', currency: 'COP', view_count: 3, heat_score: 5, is_active: true },
  { id: 2, title: 'Proposal Beta', client_name: 'Client B', client_email: 'b@test.com', status: 'viewed', total_investment: '8000000', currency: 'COP', view_count: 7, heat_score: 8, is_active: true },
  { id: 3, title: 'Proposal Gamma', client_name: 'Client C', client_email: 'c@test.com', status: 'draft', total_investment: '3000000', currency: 'COP', view_count: 0, heat_score: 0, is_active: true },
];

function setupMock(page) {
  return mockApi(page, async ({ apiPath, route }) => {
    if (apiPath === 'auth/check/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
    }
    if (apiPath === 'proposals/' && route.request().method() === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
    }
    if (apiPath === 'proposals/dashboard/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ total: 3, by_status: {}, conversion_rate: 0, avg_close_days: 0 }) };
    }
    if (apiPath === 'proposals/alerts/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    if (apiPath === 'proposals/bulk-action/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ affected: 2, action: 'delete' }) };
    }
    return null;
  });
}

test.describe('Batch Actions on Proposals', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8000, role: 'admin', is_staff: true } });
  });

  test('action bar is hidden when no proposals selected', {
    tag: [...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');

    // Table should render
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    // Batch bar should NOT be visible (no selections)
    await expect(page.getByText(/seleccionada\(s\)/)).not.toBeVisible();
  });

  test('selecting a checkbox shows the bulk action bar', {
    tag: [...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    const checkboxes = page.locator('tbody input[type="checkbox"]');
    // quality: allow-fragile-selector (table row checkboxes have no testid, first row is the target)
    await checkboxes.first().check();

    // Batch bar should appear with count
    await expect(page.getByText('1 seleccionada(s)')).toBeVisible({ timeout: 5000 });
  });

  test('bulk action bar shows resend, expire, delete, and cancel buttons', {
    tag: [...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    const checkboxes = page.locator('tbody input[type="checkbox"]');
    // quality: allow-fragile-selector (table row checkboxes have no testid, first row is the target)
    await checkboxes.first().check();

    // Scope assertions to the sticky batch bar (bg-gray-900 container)
    const batchBar = page.locator('div.bg-gray-900.text-white');
    await expect(batchBar).toBeVisible({ timeout: 5000 });
    await expect(batchBar.getByRole('button', { name: /Re-enviar/ })).toBeVisible();
    await expect(batchBar.getByRole('button', { name: /Expirar/ })).toBeVisible();
    await expect(batchBar.getByRole('button', { name: /Eliminar/ })).toBeVisible();
    await expect(batchBar.getByRole('button', { name: /Cancelar/ })).toBeVisible();
  });

  test('cancel button clears selection and hides action bar', {
    tag: [...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    const checkboxes = page.locator('tbody input[type="checkbox"]');
    // quality: allow-fragile-selector (table row checkboxes have no testid, first row is the target)
    await checkboxes.first().check();
    await expect(page.getByText('1 seleccionada(s)')).toBeVisible({ timeout: 5000 });

    // Click cancel
    await page.getByRole('button', { name: /Cancelar/ }).click();

    // Bar should hide
    await expect(page.getByText(/seleccionada\(s\)/)).not.toBeVisible({ timeout: 5000 });
  });

  test('select-all header checkbox selects all visible rows', {
    tag: [...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    // Click header checkbox (select all)
    const headerCheckbox = page.locator('thead input[type="checkbox"]');
    await headerCheckbox.check();

    // Should show count matching total proposals
    await expect(page.getByText('3 seleccionada(s)')).toBeVisible({ timeout: 5000 });
  });
});
