/**
 * E2E tests for admin proposal quick-log activity modal.
 *
 * @flow: admin-proposal-quick-log
 *
 * Covers: opening quick-log modal from actions menu, activity type select,
 * description input, submit button disabled state, successful submission.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_QUICK_LOG } from '../helpers/flow-tags.js';

const mockProposals = [
  { id: 1, title: 'Quick Log Proposal', client_name: 'Log Client', client_email: 'log@test.com', status: 'sent', total_investment: '5000000', currency: 'COP', view_count: 3, heat_score: 5, is_active: true },
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
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ total: 1, by_status: {}, conversion_rate: 0, avg_close_days: 0 }) };
    }
    if (apiPath === 'proposals/alerts/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    if (apiPath === 'proposals/1/log-activity/') {
      return { status: 201, contentType: 'application/json', body: JSON.stringify({ id: 99, change_type: 'call', description: 'Test call', created_at: new Date().toISOString() }) };
    }
    return null;
  });
}

async function openQuickLogModal(page) {
  await page.goto('/panel/proposals');
  await page.waitForLoadState('networkidle');
  await expect(page.getByText('Log Client')).toBeVisible({ timeout: 10000 });

  // Hide the floating "?" metrics button that overlaps the actions column
  await page.evaluate(() => {
    const floatingBtn = document.querySelector('button[title="Manual de métricas"]');
    if (floatingBtn) floatingBtn.style.display = 'none';
  });

  // quality: allow-fragile-selector (table row has no testid, first row is the target for actions)
  const firstRow = page.locator('tbody tr').first();
  // quality: allow-fragile-selector (table row actions button has no testid, last td + last button is the three-dots trigger)
  const dotsBtn = firstRow.locator('td').last().locator('button').last();
  await dotsBtn.click();

  // Actions modal should open showing the proposal title in the header
  await expect(page.locator('h3').filter({ hasText: 'Quick Log Proposal' })).toBeVisible({ timeout: 5000 });

  // Click "Registrar actividad" action button inside the actions modal
  const actionsModal = page.locator('div.fixed.inset-0').filter({ has: page.locator('h3').filter({ hasText: 'Quick Log Proposal' }) });
  const logAction = actionsModal.locator('button, a').filter({ hasText: 'Registrar actividad' });
  await logAction.click();

  // Quick-log modal should now be visible (different modal with form)
  // Scope to the quick-log modal to avoid matching the inline status <select> in the table
  const quickLogModal = page.locator('div.fixed.inset-0').filter({ has: page.getByText('Registrar') });
  await expect(quickLogModal.locator('select')).toBeVisible({ timeout: 5000 });
}

test.describe('Quick Log Activity from Proposals List', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8000, role: 'admin', is_staff: true } });
  });

  test('quick-log modal shows proposal context', {
    tag: [...ADMIN_PROPOSAL_QUICK_LOG, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await openQuickLogModal(page);

    // Should show client name and title
    await expect(page.getByText(/Log Client.*Quick Log Proposal/)).toBeVisible();
  });

  test('quick-log modal has activity type selector with 4 options', {
    tag: [...ADMIN_PROPOSAL_QUICK_LOG, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await openQuickLogModal(page);

    // Scope to the quick-log modal to avoid the inline status <select>
    const modal = page.locator('div.fixed.inset-0').filter({ has: page.getByText('Registrar') });
    const select = modal.locator('select');
    await expect(select).toBeVisible();

    // Verify 4 options
    const options = select.locator('option');
    await expect(options).toHaveCount(4);
  });

  test('submit button is disabled when description is empty', {
    tag: [...ADMIN_PROPOSAL_QUICK_LOG, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await openQuickLogModal(page);

    // Scope to the quick-log modal form area
    const modal = page.locator('div.fixed.inset-0').filter({ has: page.getByText('Registrar') });
    const submitBtn = modal.getByRole('button', { name: 'Registrar', exact: true });
    await expect(submitBtn).toBeDisabled();
  });

  test('submit button becomes enabled after typing description', {
    tag: [...ADMIN_PROPOSAL_QUICK_LOG, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await openQuickLogModal(page);

    // Type description
    const input = page.locator('input[placeholder*="Llamada de seguimiento"]');
    await input.fill('Llamada de seguimiento con el cliente');

    const modal = page.locator('div.fixed.inset-0').filter({ has: page.getByText('Registrar') });
    const submitBtn = modal.getByRole('button', { name: 'Registrar', exact: true });
    await expect(submitBtn).toBeEnabled();
  });

  test('submitting quick-log sends API request and closes modal', {
    tag: [...ADMIN_PROPOSAL_QUICK_LOG, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await openQuickLogModal(page);

    const input = page.locator('input[placeholder*="Llamada de seguimiento"]');
    await input.fill('Seguimiento telefónico exitoso');

    const modal = page.locator('div.fixed.inset-0').filter({ has: page.getByText('Registrar') });
    const submitBtn = modal.getByRole('button', { name: 'Registrar', exact: true });

    // Wait for API response before asserting modal closure
    await Promise.all([
      page.waitForResponse(r => r.url().includes('log-activity')),
      submitBtn.click(),
    ]);

    // Modal should close after successful submission
    await expect(modal).not.toBeVisible({ timeout: 5000 });
  });
});
