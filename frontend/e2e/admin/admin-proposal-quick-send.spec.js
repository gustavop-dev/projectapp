/**
 * E2E tests for sending a proposal directly from the proposals listing page
 * via the actions modal, without entering the edit page.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_QUICK_SEND } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDraftProposal = {
  id: 1,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Quick Send Test',
  client_name: 'Test Client',
  client_email: 'client@test.com',
  status: 'draft',
  total_investment: '5000000',
  currency: 'COP',
  view_count: 0,
  heat_score: 5,
  is_active: true,
  created_at: '2026-03-01T12:00:00Z',
  last_activity_at: '2026-03-01T12:00:00Z',
};

const mockSentProposal = {
  ...mockDraftProposal,
  id: 2,
  uuid: '22222222-2222-2222-2222-222222222222',
  title: 'Sent Proposal',
  status: 'sent',
  sent_at: '2026-03-02T12:00:00Z',
  last_activity_at: '2026-03-02T12:00:00Z',
};

test.describe('Admin Proposal Quick Send', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8400, role: 'admin', is_staff: true },
    });
  });

  test('draft proposal shows "Enviar al cliente" in actions modal from listing', {
    tag: [...ADMIN_PROPOSAL_QUICK_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify([mockDraftProposal]) };
      if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify({}) };
      if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });

    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Test Client')).toBeVisible({ timeout: 10000 });

    // Hide the MetricsManual floating button that intercepts pointer events
    await page.evaluate(() => {
      const btn = document.querySelector('button[title="Manual de métricas"]');
      if (btn) btn.style.display = 'none';
    });

    // quality: allow-fragile-selector (table actions button has no testid)
    const actionsBtn = page.locator('table button').filter({ has: page.locator('svg') }).last();
    await actionsBtn.click();

    await expect(page.getByText('Enviar al cliente')).toBeVisible({ timeout: 3000 });
  });

  test('sent proposal shows "Re-enviar email" in actions modal from listing', {
    tag: [...ADMIN_PROPOSAL_QUICK_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify([mockSentProposal]) };
      if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify({}) };
      if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });

    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Test Client')).toBeVisible({ timeout: 10000 });

    // Hide the MetricsManual floating button that intercepts pointer events
    await page.evaluate(() => {
      const btn = document.querySelector('button[title="Manual de métricas"]');
      if (btn) btn.style.display = 'none';
    });

    // quality: allow-fragile-selector (table actions button has no testid)
    const actionsBtn = page.locator('table button').filter({ has: page.locator('svg') }).last();
    await actionsBtn.click();

    await expect(page.getByText('Re-enviar email')).toBeVisible({ timeout: 3000 });
  });
});
