/**
 * E2E tests for admin proposal zombie segment.
 *
 * Covers: zombie alerts section rendering, collapsible behavior,
 * zombie alert types (zombie_draft, zombie_sent_stale).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_ZOMBIE_SEGMENT } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockProposals = [
  { id: 1, uuid: 'aaa', title: 'Zombie Draft', client_name: 'Client A', status: 'draft', created_at: '2026-01-01' },
  { id: 2, uuid: 'bbb', title: 'Zombie Stale', client_name: 'Client B', status: 'sent', created_at: '2026-01-01' },
];

const mockAlerts = [
  { id: 1, alert_type: 'zombie_draft', title: 'Zombie Draft', client_name: 'Client A', message: 'Draft >5 days' },
  { id: 2, alert_type: 'zombie_sent_stale', title: 'Zombie Stale', client_name: 'Client B', message: 'Sent >10 days' },
  { id: 3, alert_type: 'not_viewed', title: 'Active Prop', client_name: 'Client C', message: 'Not viewed' },
];

function setupMock(page, alerts = mockAlerts) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
    if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: JSON.stringify(alerts) };
    if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify({}) };
    return null;
  });
}

test.describe('Admin Proposal Zombie Segment', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('renders zombie section with dark theme when zombie alerts exist', {
    tag: [...ADMIN_PROPOSAL_ZOMBIE_SEGMENT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/Propuestas zombie/)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('(2)')).toBeVisible();
  });

  test('zombie section is collapsed by default and expands on click', {
    tag: [...ADMIN_PROPOSAL_ZOMBIE_SEGMENT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    // Zombie alerts content should not be visible initially (collapsed)
    await expect(page.getByText(/Propuestas zombie/)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Draft >5 days')).not.toBeVisible();

    // Click to expand
    await page.getByText(/Propuestas zombie/).click();

    // Zombie alert messages should now be visible
    await expect(page.getByText('Draft >5 days')).toBeVisible();
    await expect(page.getByText('Sent >10 days')).toBeVisible();
  });

  test('zombie section is hidden when no zombie alerts exist', {
    tag: [...ADMIN_PROPOSAL_ZOMBIE_SEGMENT, '@role:admin'],
  }, async ({ page }) => {
    const noZombieAlerts = [
      { id: 3, alert_type: 'not_viewed', title: 'Active Prop', client_name: 'Client C', message: 'Not viewed' },
    ];
    await setupMock(page, noZombieAlerts);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    // Wait for proposals list to render
    await expect(page.getByText(/Propuestas que necesitan atención/)).toBeVisible({ timeout: 10000 });

    // Zombie section should not exist
    await expect(page.getByText(/Propuestas zombie/)).not.toBeVisible();
  });
});
