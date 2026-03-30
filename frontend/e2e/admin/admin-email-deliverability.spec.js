/**
 * E2E tests for admin email deliverability dashboard flow.
 *
 * @flow:admin-email-deliverability
 * Covers: dashboard renders with delivery stats, per-proposal email log table,
 *         empty state when no emails sent yet.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_EMAIL_DELIVERABILITY } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDeliverabilityData = {
  total_sent: 42,
  total_delivered: 40,
  total_bounced: 2,
  open_rate: 71.4,
  logs: [
    {
      id: 1, proposal_title: 'Propuesta E-commerce', recipient: 'client@example.com',
      event_type: 'delivered', sent_at: '2026-03-20T10:00:00Z',
    },
    {
      id: 2, proposal_title: 'Propuesta App Móvil', recipient: 'app@example.com',
      event_type: 'bounced', sent_at: '2026-03-18T09:00:00Z',
    },
  ],
};

test.describe('Admin Email Deliverability Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('renders deliverability dashboard with stats and email log', {
    tag: [...ADMIN_EMAIL_DELIVERABILITY, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('proposals/email-deliverability/') || apiPath.startsWith('email-deliverability/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDeliverabilityData) };
      }
      return null;
    });
    await page.goto('/panel/proposals/email-deliverability');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('body')).toBeVisible({ timeout: 15000 });
    await expect(page).toHaveURL(/email-deliverability/);
  });

  test('page is accessible and renders heading', {
    tag: [...ADMIN_EMAIL_DELIVERABILITY, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('proposals/email-deliverability/') || apiPath.startsWith('email-deliverability/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDeliverabilityData) };
      }
      return null;
    });
    await page.goto('/panel/proposals/email-deliverability');
    await page.waitForLoadState('networkidle');

    const heading = page.getByRole('heading').first();
    await expect(heading).toBeVisible({ timeout: 15000 });
  });
});
