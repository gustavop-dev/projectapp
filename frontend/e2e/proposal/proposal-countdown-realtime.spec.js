/**
 * E2E tests for proposal countdown realtime timer.
 *
 * Covers: HH:MM countdown when proposal expires within 48 hours,
 * ExpirationBadge visibility with countdown format.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_COUNTDOWN_REALTIME } from '../helpers/flow-tags.js';

const MOCK_UUID = 'countdown-uuid-1234-5678-abcdef';

function buildProposal(expiresAt) {
  return {
    id: 1,
    uuid: MOCK_UUID,
    title: 'Countdown Proposal',
    client_name: 'Timer Client',
    status: 'sent',
    language: 'es',
    total_investment: '10000000',
    currency: 'COP',
    expires_at: expiresAt,
    sections: [
      {
        id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
        content_json: { clientName: 'Timer Client', inspirationalQuote: 'Hello.' },
      },
    ],
    requirement_groups: [],
  };
}

test.describe('Proposal Countdown Realtime', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`proposal-${uuid}-viewMode`, 'detailed');
    }, MOCK_UUID);
  });

  test('shows HH:MM countdown when proposal expires within 48 hours', {
    tag: [...PROPOSAL_COUNTDOWN_REALTIME, '@role:client'],
  }, async ({ page }) => {
    // Set expiry 12 hours from now
    const expiresAt = new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString();
    const proposal = buildProposal(expiresAt);

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
      }
      return null;
    });

    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // ExpirationBadge should show with "Expira en" text and HH:MM format
    await expect(page.getByText(/Expira en \d+:\d+/)).toBeVisible({ timeout: 15000 });
  });

  test('does not show countdown when expiry is more than 48 hours away', {
    tag: [...PROPOSAL_COUNTDOWN_REALTIME, '@role:client'],
  }, async ({ page }) => {
    // Set expiry 5 days from now
    const expiresAt = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString();
    const proposal = buildProposal(expiresAt);

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
      }
      return null;
    });

    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Should show standard "Expira en X días" instead of HH:MM
    await expect(page.getByTestId('nav-next')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/Expira en \d+:\d+/)).not.toBeVisible();
    await expect(page.getByText(/Expira en/)).toBeVisible();
  });
});
