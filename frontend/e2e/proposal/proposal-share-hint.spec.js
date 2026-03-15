/**
 * E2E tests for proposal share button hint.
 *
 * Covers: persistent tooltip "Comparte con tu equipo" below share button,
 * auto-show behavior, and localStorage persistence.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_SHARE_HINT } from '../helpers/flow-tags.js';

const MOCK_UUID = 'share-hint-uuid-1234-5678-abcdef';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Share Hint Proposal',
  client_name: 'Hint Client',
  status: 'sent',
  language: 'es',
  total_investment: '10000000',
  currency: 'COP',
  sections: [
    {
      id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
      content_json: { clientName: 'Hint Client', inspirationalQuote: 'Hello.' },
    },
  ],
  requirement_groups: [],
};

function setupMock(page) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
    }
    return null;
  });
}

test.describe('Proposal Share Button Hint', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('share hint tooltip appears after delay', {
    tag: [...PROPOSAL_SHARE_HINT, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    // Wait for the hint to auto-show (2s delay)
    await expect(page.getByText('Comparte con tu equipo')).toBeVisible({ timeout: 10000 });
  });

  test('share hint does not appear when already dismissed via localStorage', {
    tag: [...PROPOSAL_SHARE_HINT, '@role:client'],
  }, async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem(`proposal-${uuid}-share-hint-seen`, '1');
    }, MOCK_UUID);

    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    // Wait for page to render, then verify hint is not shown
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 15000 });
    // The hint has a 2s auto-show delay; wait for that window to pass using condition-based wait
    await expect(page.getByText('Comparte con tu equipo')).not.toBeVisible({ timeout: 5000 });
  });
});
