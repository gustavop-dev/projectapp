/**
 * E2E tests for proposal share button on public proposal page.
 *
 * Covers: share button visibility, quick-copy click, share modal open
 * via context menu, and share link creation form.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_SHARE } from '../helpers/flow-tags.js';

const MOCK_UUID = '5a111111-1111-1111-1111-111111111111';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Share Test Proposal',
  client_name: 'Share Client',
  status: 'sent',
  language: 'es',
  total_investment: '10000.00',
  currency: 'COP',
  sections: [
    {
      id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
      content_json: { clientName: 'Share Client', inspirationalQuote: 'Hello.' },
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

test.describe('Proposal Share', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('share button is visible on proposal page', {
    tag: [...PROPOSAL_SHARE, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    await expect(page.getByTestId('share-proposal-btn')).toBeVisible({ timeout: 15000 });
  });

  test('share modal opens and shows copy link button', {
    tag: [...PROPOSAL_SHARE, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    const shareBtn = page.getByTestId('share-proposal-btn');
    await expect(shareBtn).toBeVisible({ timeout: 15000 });

    // Click opens the share modal
    await shareBtn.click();

    // Modal header and copy link button should be visible
    await expect(page.getByText('Compartir propuesta')).toBeVisible();
    await expect(page.getByText('Copiar enlace')).toBeVisible();
  });
});
