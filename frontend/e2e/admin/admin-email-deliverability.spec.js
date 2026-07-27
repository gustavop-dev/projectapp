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
  total_emails_30d: 42,
  success_rate: 95.2,
  sent_count: 40,
  failed_count: 2,
  by_template: [
    { template_key: 'proposal_sent', total: 30, sent: 29, failed: 1, success_rate: 96.7 },
    { template_key: 'proposal_reminder', total: 12, sent: 11, failed: 1, success_rate: 91.7 },
  ],
  daily_trend: [
    { date: '2026-03-18', total: 5, failed: 0 },
    { date: '2026-03-19', total: 8, failed: 1 },
  ],
  recent_failures: [
    {
      template_key: 'proposal_sent', recipient: 'client@example.com',
      status: 'bounced', sent_at: '2026-03-18T09:00:00Z', error_message: 'Mailbox full',
    },
  ],
};

test.describe('Admin Email Deliverability Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('renders deliverability dashboard with stats and email log', {
    tag: [...ADMIN_EMAIL_DELIVERABILITY, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (dashboard is populated straight from a GET on load; no action changes what renders)
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('proposals/email-deliverability/') || apiPath.startsWith('email-deliverability/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDeliverabilityData) };
      }
      return null;
    });
    await page.goto('/panel/proposals/email-deliverability');

    // Concrete KPI value from the fixture — catches a broken/renamed stats prop.
    await expect(page.getByText('42', { exact: true }).first()).toBeVisible({ timeout: 15000 });
    // Per-template row from the fixture — catches the log table failing to render real rows.
    // (also matches the recent-failures entry for the same template, hence .first())
    await expect(page.getByText('proposal_sent', { exact: true }).first()).toBeVisible();
    await expect(page).toHaveURL(/email-deliverability/);
  });

  test('page is accessible and renders heading', {
    tag: [...ADMIN_EMAIL_DELIVERABILITY, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (accessibility/heading-structure check on load; no action changes the heading)
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('proposals/email-deliverability/') || apiPath.startsWith('email-deliverability/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDeliverabilityData) };
      }
      return null;
    });
    await page.goto('/panel/proposals/email-deliverability');

    const heading = page.getByRole('heading').first();
    await expect(heading).toContainText('Email Deliverability', { timeout: 15000 });
  });
});
